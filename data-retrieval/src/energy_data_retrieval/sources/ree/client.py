"""Actual system energy from the REData generation-structure widget.

This is aggregate generation by technology, not individual plant telemetry.
The widget's API energy values are MWh, even when the website scales its chart
to GWh. Source offset-bearing period labels and last-update metadata are retained.
No demand, installed capacity or forecast is substituted for generation.
"""

from __future__ import annotations

import calendar
import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from types import MappingProxyType

import pandas as pd

from energy_data_retrieval.transport import (
    HTTPClient,
    JSONValue,
    RequestRecord,
    RetrievalError,
    array_value,
    object_value,
)

REE_HOSTS = frozenset({"apidatos.ree.es"})
GENERATION_ENDPOINT = "https://apidatos.ree.es/es/datos/generacion/estructura-generacion"
REE_SYSTEMS = MappingProxyType(
    {
        "national": None,
        "peninsular": "8741",
        "canarias": "8742",
        "baleares": "8743",
        "ceuta": "8744",
        "melilla": "8745",
    }
)
REFERENCE_IDS = ("ree_redata_api", "ree_generation_structure")
_COLUMNS = [
    "timestamp",
    "source_datetime",
    "period",
    "source",
    "area",
    "technology_id",
    "technology",
    "value",
    "unit",
    "aggregation",
    "percentage",
    "source_type",
    "is_total",
    "source_last_update",
]


@dataclass(frozen=True, slots=True)
class REEGeneration:
    """Normalized observations and non-secret provenance for every response."""

    frame: pd.DataFrame
    requests: tuple[RequestRecord, ...]


def _limit(value: int, name: str, upper: int) -> None:
    if type(value) is not int or not 1 <= value <= upper:
        raise ValueError(f"{name} must be an integer in 1..{upper}")


def _number(value: JSONValue, name: str) -> float:
    if value is None:
        return float("nan")
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise RetrievalError(f"REE {name} must be numeric or null")
    try:
        number = float(value)
    except ValueError:
        raise RetrievalError(f"REE {name} is not a number") from None
    if not math.isfinite(number):
        raise RetrievalError(f"REE {name} contains a non-finite value")
    return number


def _text(value: JSONValue, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise RetrievalError(f"REE omitted {name}")
    return value


def _deduplicate(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.drop_duplicates()
    if frame.duplicated(["area", "technology_id", "timestamp"]).any():
        raise RetrievalError("REE returned conflicting observations for a technology and period")
    return frame.sort_values(["timestamp", "technology_id"]).reset_index(drop=True)


def normalize_generation(
    payload: JSONValue,
    *,
    area: str = "national",
    time_trunc: str = "day",
    include_total: bool = False,
    maximum_rows: int = 1_000_000,
) -> pd.DataFrame:
    """Parse one ``estructura-generacion`` JSON response into long MWh rows.

    ``timestamp`` is the source period-start label converted to UTC. ``period``
    and ``source_datetime`` preserve the provider's civil date and offset. A
    daily, monthly or yearly energy value is never treated as instantaneous MW.
    Null observations remain NaN; reported zeros and negative values remain.
    The source's total series is excluded by default to prevent double counting.
    Empty ``included`` means no observations, without inferring zero generation.
    """
    _limit(maximum_rows, "maximum_rows", 10_000_000)
    if time_trunc not in {"day", "month", "year"}:
        raise ValueError("REE generation supports day, month or year aggregation")
    if not isinstance(area, str) or not area:
        raise ValueError("area must identify the requested REE electrical system")
    root = object_value(payload)
    if root.get("errors"):
        raise RetrievalError("REE returned an API error document")
    widget = object_value(root.get("data"))
    if widget.get("id") != "gen1":
        raise RetrievalError("Expected the REE generation-structure widget (gen1)")
    rows: list[dict[str, object]] = []
    observed_rows = 0
    excluded_total_rows = 0
    for raw in array_value(root.get("included")):
        series = object_value(raw)
        attrs = object_value(series.get("attributes"))
        identifier = _text(series.get("id"), "technology identifier")
        title = _text(attrs.get("title"), "technology name")
        source_type = _text(attrs.get("type"), "series type")
        is_total = source_type.lower() == "total"
        if attrs.get("composite"):
            raise RetrievalError("Composite REE generation series require explicit interpretation")
        if attrs.get("magnitude") not in (None, "MWh"):
            raise RetrievalError("REE generation widget has an unexpected energy magnitude")
        for point in array_value(attrs.get("values")):
            observed_rows += 1
            if observed_rows > maximum_rows:
                raise RetrievalError("REE response exceeds maximum_rows")
            observation = object_value(point)
            label = _text(observation.get("datetime"), "offset-bearing timestamp")
            try:
                stamp = datetime.fromisoformat(label)
            except ValueError:
                raise RetrievalError("REE returned an invalid timestamp") from None
            if stamp.tzinfo is None or stamp.utcoffset() is None:
                raise RetrievalError("REE timestamp must carry an explicit UTC offset")
            if stamp.hour or stamp.minute or stamp.second or stamp.microsecond:
                raise RetrievalError("REE period label does not match the requested aggregation")
            if (time_trunc in {"month", "year"} and stamp.day != 1) or (
                time_trunc == "year" and stamp.month != 1
            ):
                raise RetrievalError("REE period label does not match the requested aggregation")
            if "value" not in observation:
                raise RetrievalError("REE observation omitted its value field")
            value = _number(observation["value"], "generation")
            percentage = _number(observation.get("percentage"), "percentage")
            if is_total and not include_total:
                excluded_total_rows += 1
                continue
            rows.append(
                {
                    "timestamp": stamp,
                    "source_datetime": label,
                    "period": stamp.date().isoformat(),
                    "source": "ree",
                    "area": area,
                    "technology_id": identifier,
                    "technology": title,
                    "value": value,
                    "unit": "MWh",
                    "aggregation": time_trunc,
                    "percentage": percentage,
                    "source_type": source_type,
                    "is_total": is_total,
                    "source_last_update": attrs.get("last-update"),
                }
            )
    frame = pd.DataFrame(rows, columns=_COLUMNS)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame = frame.astype({"value": "float64", "percentage": "float64", "is_total": "bool"})
    frame = _deduplicate(frame)
    frame.attrs.update(
        source="Red Eléctrica REData",
        endpoint=GENERATION_ENDPOINT,
        unit="MWh",
        timestamp_semantics="UTC conversion of the source's offset-bearing period-start label",
        aggregation=time_trunc,
        area=area,
        scope="System generation by technology; no individual plant identifiers",
        missing_policy="Null remains missing; absent periods are not imputed or filled with zero",
        total_series_included=include_total,
        excluded_total_rows=excluded_total_rows,
        reference_ids=list(REFERENCE_IDS),
    )
    return frame


@dataclass(slots=True)
class REEClient:
    """Unauthenticated REData access with bounded calendar-year request chunks."""

    http: HTTPClient
    maximum_requests: int = 32
    maximum_rows: int = 1_000_000

    def __post_init__(self) -> None:
        _limit(self.maximum_requests, "maximum_requests", 1000)
        _limit(self.maximum_rows, "maximum_rows", 10_000_000)

    def generation(
        self,
        start: date,
        end: date,
        *,
        time_trunc: str = "day",
        system: str = "national",
        geo_id: str | None = None,
        include_total: bool = False,
    ) -> REEGeneration:
        """Retrieve inclusive provider civil dates, preserving MWh and period labels.

        Use ``system='ccaa', geo_id='7'`` for an explicit autonomous-community
        identifier from REE's catalogue. National uses the widget's documented
        default; named island/peninsular systems send all three geo parameters.
        Monthly and yearly queries must cover complete calendar periods. No
        completeness claim is made for provider omissions or provisional data.
        """
        if type(start) is not date or type(end) is not date or start > end or end.year > 9998:
            raise ValueError("REE requires ordered inclusive date objects (end year <= 9998)")
        if time_trunc not in {"day", "month", "year"}:
            raise ValueError("REE generation supports day, month or year aggregation")
        if time_trunc in {"month", "year"} and (
            start.day != 1 or end.day != calendar.monthrange(end.year, end.month)[1]
        ):
            raise ValueError("Monthly/yearly retrieval requires complete calendar periods")
        if time_trunc == "year" and (start.month != 1 or end.month != 12):
            raise ValueError("Yearly retrieval requires complete calendar years")
        parameters: dict[str, str] = {"time_trunc": time_trunc}
        if system == "ccaa":
            if not isinstance(geo_id, str) or not geo_id.isascii() or not geo_id.isdecimal():
                raise ValueError("ccaa requires an exact numeric geo_id from the REE catalogue")
            area = f"ccaa:{geo_id}"
            parameters.update(geo_trunc="electric_system", geo_limit="ccaa", geo_ids=geo_id)
        elif system in REE_SYSTEMS:
            if geo_id is not None:
                raise ValueError("geo_id is only accepted with system='ccaa'")
            area = system
            selected_id = REE_SYSTEMS[system]
            if selected_id is not None:
                parameters.update(
                    geo_trunc="electric_system", geo_limit=system, geo_ids=selected_id
                )
        else:
            raise ValueError("Choose a documented REE system or ccaa with an explicit geo_id")
        if end.year - start.year + 1 > self.maximum_requests:
            raise ValueError("REE date range exceeds maximum_requests")
        frames: list[pd.DataFrame] = []
        provenance: list[RequestRecord] = []
        current = start
        excluded = 0
        count = 0
        while current <= end:
            until = min(date(current.year, 12, 31), end)
            query = parameters | {
                "start_date": current.isoformat() + "T00:00",
                "end_date": until.isoformat() + "T23:59",
            }
            response = self.http.get_json(GENERATION_ENDPOINT, query)
            frame = normalize_generation(
                response.value,
                area=area,
                time_trunc=time_trunc,
                include_total=include_total,
                maximum_rows=self.maximum_rows,
            )
            if (
                not frame.empty
                and not frame["period"].between(current.isoformat(), until.isoformat()).all()
            ):
                raise RetrievalError("REE returned observations outside the requested civil dates")
            count += len(frame)
            if count > self.maximum_rows:
                raise RetrievalError("REE retrieval exceeds maximum_rows")
            excluded += int(frame.attrs["excluded_total_rows"])
            frames.append(frame)
            provenance.append(response.record)
            current = until + timedelta(days=1)
        metadata = frames[0].attrs.copy()
        combined = _deduplicate(pd.concat(frames, ignore_index=True))
        combined.attrs.update(metadata)
        combined.attrs["excluded_total_rows"] = excluded
        return REEGeneration(combined, tuple(provenance))
