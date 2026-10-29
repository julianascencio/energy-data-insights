"""CEN generation is reported by operating unit; aggregation requires a roster."""

from __future__ import annotations

import math
import os
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from energy_data_retrieval.transport import (
    HTTPClient,
    JSONValue,
    RequestRecord,
    RetrievalError,
    array_value,
    object_value,
)

GENERATION_ENDPOINT = "https://sipub.api.coordinador.cl/generacion-real/v3/findByDate"
REGISTRY_ENDPOINT = "https://api-infotecnica.coordinador.cl/v1/centrales-sin-filtrar/extended/"
CEN_HOSTS = frozenset({"sipub.api.coordinador.cl", "api-infotecnica.coordinador.cl"})


@dataclass(frozen=True, slots=True)
class GenerationDay:
    day: date
    units: pd.DataFrame
    exclusions: pd.DataFrame
    requests: tuple[RequestRecord, ...]


@dataclass(slots=True)
class CENClient:
    http: HTTPClient
    user_key: str = field(default="", repr=False)
    page_size: int = 5000
    maximum_pages: int = 200

    def __post_init__(self) -> None:
        if not 1 <= self.page_size <= 20000 or not 1 <= self.maximum_pages <= 1000:
            raise ValueError("Invalid bounded CEN pagination settings")

    @classmethod
    def from_environment(cls, http: HTTPClient) -> CENClient:
        return cls(http=http, user_key=os.environ.get("CEN_USER_KEY", ""))

    def registry(self) -> tuple[pd.DataFrame, RequestRecord]:
        response = self.http.get_json(REGISTRY_ENDPOINT)
        return normalize_registry(array_value(response.value)), response.record

    def generation_day(self, day: date, *, technology: str = "Solar") -> GenerationDay:
        """Retrieve every advertised page for one civil day, validating a stable envelope.

        An API's pagination can change during a live query. This adapter fails on
        any envelope change instead of claiming an atomic or complete snapshot.
        Requests are sequential and are bounded independently of the date range.
        """
        if not self.user_key:
            raise ValueError("CEN_USER_KEY must contain an authorized CEN API user key")
        rows: list[JSONValue] = []
        provenance: list[RequestRecord] = []
        total_pages: int | None = None
        effective_size: int | None = None
        page = 1
        while total_pages is None or page <= total_pages:
            parameters = {
                "startDate": day.isoformat(),
                "endDate": day.isoformat(),
                "page": str(page),
                "pageSize": str(self.page_size),
                "tipoTecnologia": technology,
            }
            response = self.http.get_json(
                GENERATION_ENDPOINT,
                parameters,
                secrets={"user_key": self.user_key},
            )
            payload = object_value(response.value)
            returned_page = _positive_int(payload.get("page"))
            returned_size = _positive_int(payload.get("pageSize"))
            advertised = _positive_int(payload.get("totalPages"))
            if (
                returned_page != page
                or payload.get("startDate") != day.isoformat()
                or payload.get("endDate") != day.isoformat()
                or advertised > self.maximum_pages
                or returned_size > 20000
            ):
                raise RetrievalError("CEN returned a mismatched date or pagination envelope")
            if total_pages is not None and (
                advertised != total_pages or returned_size != effective_size
            ):
                raise RetrievalError(
                    "CEN pagination changed during retrieval; snapshot is incomplete"
                )
            total_pages, effective_size = advertised, returned_size
            page_rows = array_value(payload.get("data"))
            if len(page_rows) > returned_size:
                raise RetrievalError("CEN page exceeds its advertised page size")
            for raw in page_rows:
                row = object_value(raw)
                if row.get("tipo_tecnologia") != technology:
                    raise RetrievalError("CEN did not honor the requested technology filter")
                stamp = row.get("fecha_hora")
                if not isinstance(stamp, str) or stamp[:10] != day.isoformat():
                    raise RetrievalError("CEN row falls outside the requested civil date")
            rows.extend(page_rows)
            provenance.append(response.record)
            page += 1
        units, exclusions = normalize_generation(rows)
        return GenerationDay(day, units, exclusions, tuple(provenance))

    def iter_generation_days(
        self,
        start: date,
        end: date,
        *,
        technology: str = "Solar",
    ) -> Iterator[GenerationDay]:
        if start > end:
            raise ValueError("start must be on or before end")
        current = start
        while current <= end:
            yield self.generation_day(current, technology=technology)
            current += timedelta(days=1)


def _positive_int(value: JSONValue) -> int:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise RetrievalError("CEN omitted an integer pagination field")
    try:
        integer = int(value)
    except ValueError:
        raise RetrievalError("CEN returned an invalid pagination integer") from None
    if integer < 1:
        raise RetrievalError("CEN pagination fields must be positive")
    return integer


def _source_timestamp(label: str, source_timezone: str) -> datetime | None:
    try:
        stamp = datetime.fromisoformat(label)
    except ValueError:
        raise RetrievalError("CEN returned a malformed source timestamp") from None
    if stamp.minute or stamp.second or stamp.microsecond:
        raise RetrievalError("CEN hourly timestamp is not on an hour boundary")
    if stamp.tzinfo is not None:
        return stamp.astimezone(UTC)
    zone = ZoneInfo(source_timezone)
    candidates = {
        candidate.astimezone(UTC)
        for fold in (0, 1)
        if (candidate := stamp.replace(tzinfo=zone, fold=fold))
        .astimezone(UTC)
        .astimezone(zone)
        .replace(tzinfo=None)
        == stamp
    }
    if len(candidates) > 1:
        raise RetrievalError(
            "Ambiguous CEN civil-clock label requires explicit source fold evidence"
        )
    return next(iter(candidates)) if candidates else None


def normalize_generation(
    rows: Sequence[JSONValue],
    *,
    source_timezone: str = "America/Santiago",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Normalize unit rows; quarantine missing identities and nonexistent DST labels.

    Source ``gen_real_mw`` is interpreted as mean MW for one real hourly interval,
    so ``actual_mwh = gen_real_mw * 1 hour``. NaN remains missing and zero remains
    reported zero. Negative source observations are retained for downstream QA.
    No site or unit is guessed from a name. Conflicting duplicates fail loudly.
    """
    accepted: list[dict[str, object]] = []
    rejected: list[dict[str, object]] = []
    time_cache: dict[str, datetime | None] = {}
    for value in rows:
        row = object_value(value)
        site, unit, label = row.get("id_central"), row.get("id_opreal"), row.get("fecha_hora")
        if site is None or unit is None:
            rejected.append({"reason": "missing_site_or_unit_identity", "source_row": row})
            continue
        if (
            isinstance(site, bool)
            or isinstance(unit, bool)
            or not isinstance(site, (int, str))
            or not isinstance(unit, (int, str))
        ):
            raise RetrievalError("CEN site and unit identities must be integers or strings")
        if not isinstance(label, str):
            raise RetrievalError("CEN source timestamp is missing")
        if label not in time_cache:
            time_cache[label] = _source_timestamp(label, source_timezone)
        timestamp = time_cache[label]
        if timestamp is None:
            rejected.append({"reason": "nonexistent_civil_clock_label", "source_row": row})
            continue
        if (
            row.get("hora") is not None
            and _positive_int(row["hora"]) != datetime.fromisoformat(label).hour + 1
        ):
            raise RetrievalError("CEN hour label conflicts with its source timestamp")
        power = row.get("gen_real_mw")
        if power is not None and (
            isinstance(power, bool)
            or not isinstance(power, (int, float))
            or not math.isfinite(power)
        ):
            raise RetrievalError("CEN returned nonnumeric or non-finite generation")
        accepted.append(
            {
                "site_id": str(site),
                "unit_id": str(unit),
                "timestamp": timestamp,
                "actual_mwh": np.nan if power is None else float(power),
                "duration_hours": 1.0,
                "source_timestamp": label,
            }
        )
    columns = [
        "site_id",
        "unit_id",
        "timestamp",
        "actual_mwh",
        "duration_hours",
        "source_timestamp",
    ]
    frame = pd.DataFrame(accepted, columns=columns)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame["actual_mwh"] = frame["actual_mwh"].astype("float64")
    keys = ["site_id", "unit_id", "timestamp"]
    if not frame.empty:
        conflicts = frame.groupby(keys, dropna=False)["actual_mwh"].nunique(dropna=False)
        if bool((conflicts > 1).any()):
            raise RetrievalError(
                "Conflicting CEN unit-hour observations require source reconciliation"
            )
        frame = frame.drop_duplicates(keys).sort_values(keys).reset_index(drop=True)
    frame.attrs.update(
        source="CEN actual generation",
        source_timezone=source_timezone,
        timestamp_convention="UTC interval start",
        interval_hours=1,
        aggregation_level="operating_unit",
        excluded_rows=len(rejected),
    )
    return frame, pd.DataFrame(rejected, columns=["reason", "source_row"])


def aggregate_units(
    units: pd.DataFrame,
    expected_units: Mapping[str, frozenset[str]],
) -> pd.DataFrame:
    """Aggregate using an externally verified roster valid for this time period.

    Every expected unit must report a non-null observation. Partial totals are
    retained as ``reported_mwh`` while ``actual_mwh`` is null for incomplete hours.
    Unexpected units are rejected, rather than expanding a roster after the fact.
    """
    required = {"site_id", "unit_id", "timestamp", "actual_mwh"}
    if not required.issubset(units.columns):
        raise ValueError(f"Missing unit columns: {sorted(required - set(units.columns))}")
    if units.duplicated(["site_id", "unit_id", "timestamp"]).any():
        raise ValueError("Duplicate unit-hour rows must be reconciled before aggregation")
    if any(not roster for roster in expected_units.values()):
        raise ValueError("Every expected site roster must be nonempty")
    for site, block in units.groupby("site_id", sort=False):
        roster = expected_units.get(str(site))
        if roster is None or not set(block["unit_id"].astype(str)).issubset(roster):
            raise ValueError("Observed unit is not in the verified site roster")
    grouped = units.groupby(["site_id", "timestamp"], observed=True, sort=True)
    output = grouped.agg(
        unit_count=("unit_id", "nunique"), valid_unit_count=("actual_mwh", "count")
    )
    output["reported_mwh"] = grouped["actual_mwh"].sum(min_count=1)
    output = output.reset_index()
    output["expected_unit_count"] = output["site_id"].map(
        {site: len(roster) for site, roster in expected_units.items()}
    )
    output["generation_complete"] = output["valid_unit_count"] == output["expected_unit_count"]
    output["actual_mwh"] = output["reported_mwh"].where(output["generation_complete"])
    output["duration_hours"] = 1.0
    return output


def normalize_registry(rows: Sequence[JSONValue]) -> pd.DataFrame:
    """Normalize registry identity and coordinates without inventing DC capacity."""
    output: list[dict[str, object]] = []
    for value in rows:
        row = object_value(value)
        if row.get("id") is None:
            raise RetrievalError("Registry row has no stable CEN identity")
        output.append(
            {
                "site_id": str(row["id"]),
                "name": row.get("nombre"),
                "region": row.get("region_nombre"),
                "latitude": row.get("latitud"),
                "longitude": row.get("longitud"),
                "technology": row.get("tipo_central_nombre"),
                "reported_maximum_power_mw": row.get("potencia_maxima"),
                "ac_capacity_mw": np.nan,
                "dc_capacity_mw": np.nan,
                "dc_capacity_qualified": False,
                "status": row.get("estado"),
            }
        )
    frame = pd.DataFrame(output)
    if not frame.empty and frame["site_id"].duplicated().any():
        raise RetrievalError("Registry contains duplicate CEN identities")
    return frame
