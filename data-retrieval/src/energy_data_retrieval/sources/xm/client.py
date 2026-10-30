"""Colombia's SIMEM hourly actual-generation settlement dataset (055A4D)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd

from energy_data_retrieval.generation import GenerationResult
from energy_data_retrieval.transport import (
    HTTPClient,
    JSONValue,
    RequestRecord,
    RetrievalError,
    array_value,
    object_value,
)

XM_HOSTS = frozenset({"www.simem.co"})
GENERATION_ENDPOINT = "https://www.simem.co/backend-files/api/PublicData"
DATASET_ID = "055A4D"
REFERENCE_IDS = ("xm_simem_actual_generation", "xm_api_documentation")
_VERSIONS = frozenset({"TX1", "TX2", "TX3", "TX4", "TX5", "TXF", "TXR"})
_COLUMNS = [
    "timestamp",
    "source_datetime",
    "source",
    "area",
    "unit_id",
    "agent_id",
    "value",
    "unit",
    "source_value",
    "source_unit",
    "version",
    "aggregation",
    "quality",
    "source_last_update",
]


def _limit(value: int, name: str, upper: int) -> None:
    if type(value) is not int or not 1 <= value <= upper:
        raise ValueError(f"{name} must be an integer in 1..{upper}")


def _text(value: JSONValue, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RetrievalError(f"SIMEM omitted {label}")
    return value.strip()


def parse_generation(
    payload: JSONValue, *, version: str = "TXF", maximum_rows: int = 1_000_000
) -> pd.DataFrame:
    """Select one explicit settlement revision, retaining source kWh alongside MWh.

    This dataset is hourly actual generation at generation boundaries. It is
    distinct from E17D25, which contains daily estimated SCADA and schedules.
    ``timestamp`` converts the source ``FechaHora`` label from Colombia UTC-05;
    the label is not shifted. No revision is substituted for the selected one.
    """
    _limit(maximum_rows, "maximum_rows", 10_000_000)
    if version not in _VERSIONS:
        raise ValueError("Select one explicit SIMEM revision TX1..TX5, TXF or TXR")
    root = object_value(payload)
    if root.get("success") is not True:
        raise RetrievalError("SIMEM returned an error document")
    result = object_value(root.get("result"))
    if str(result.get("idDataset", "")).upper() != DATASET_ID:
        raise RetrievalError("Expected SIMEM actual-generation dataset 055A4D")
    metadata = object_value(result.get("metadata"))
    if metadata.get("granularity") != "Horaria":
        raise RetrievalError("SIMEM actual generation must have hourly granularity")
    records = array_value(result.get("records"))
    if len(records) > maximum_rows:
        raise RetrievalError("SIMEM response exceeds maximum_rows")
    rows: list[dict[str, object]] = []
    available: set[str] = set()
    for item in records:
        record = object_value(item)
        revision = _text(record.get("Version"), "settlement version")
        available.add(revision)
        if revision != version:
            continue
        if (
            record.get("CodigoVariable") != "GReal"
            or record.get("UnidadMedida") != "kWh"
            or record.get("CodigoDuracion") != "PT1H"
        ):
            raise RetrievalError("SIMEM row is not hourly actual GReal energy in kWh")
        label = _text(record.get("FechaHora"), "FechaHora")
        try:
            stamp = datetime.strptime(label, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise RetrievalError("SIMEM returned an invalid hourly timestamp") from None
        if stamp.minute or stamp.second:
            raise RetrievalError("SIMEM generation labels must be aligned to the hour")
        if "Valor" not in record:
            raise RetrievalError("SIMEM observation omitted Valor")
        raw = record["Valor"]
        if raw is None:
            value = float("nan")
        elif isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(raw):
            raise RetrievalError("SIMEM Valor must be a finite number or null")
        else:
            value = float(raw)
        rows.append(
            {
                "timestamp": stamp.replace(tzinfo=ZoneInfo("America/Bogota")),
                "source_datetime": label,
                "source": "xm",
                "area": "Colombia SIN",
                "unit_id": _text(record.get("CodigoPlanta"), "plant code"),
                "agent_id": _text(record.get("CodigoSICAgente"), "agent code"),
                "value": value / 1000,
                "unit": "MWh",
                "source_value": value,
                "source_unit": "kWh",
                "version": revision,
                "aggregation": "hourly_energy",
                "quality": "settlement_actual",
                "source_last_update": metadata.get("lastUpdate"),
            }
        )
    if records and version not in available:
        raise RetrievalError("Requested SIMEM settlement version is unavailable; select explicitly")
    frame = pd.DataFrame(rows, columns=_COLUMNS)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame = frame.astype({"value": float, "source_value": float}).drop_duplicates()
    if frame.duplicated(["unit_id", "timestamp", "version"]).any():
        raise RetrievalError("SIMEM conflicting plant/hour observations within one revision")
    frame = frame.sort_values(["timestamp", "unit_id"]).reset_index(drop=True)
    frame.attrs.update(
        dataset_id=DATASET_ID,
        selected_version=version,
        available_versions=sorted(available),
        source_timezone="America/Bogota",
        timestamp_semantics="Source FechaHora label converted to UTC without shifting",
        missing_policy="Null remains missing; absent records do not imply zero energy",
        reference_ids=list(REFERENCE_IDS),
    )
    return frame


@dataclass(slots=True)
class XMClient:
    """Public credential-free SIMEM GET requests, bounded to one civil day each."""

    http: HTTPClient
    maximum_requests: int = 31
    maximum_rows: int = 1_000_000

    def __post_init__(self) -> None:
        _limit(self.maximum_requests, "maximum_requests", 1000)
        _limit(self.maximum_rows, "maximum_rows", 10_000_000)

    def generation(
        self, start: date, end: date, *, version: str = "TXF", resource_ids: list[str] | None = None
    ) -> GenerationResult:
        """Retrieve inclusive Colombia dates and one caller-visible settlement revision."""
        if (
            type(start) is not date
            or type(end) is not date
            or not date(2013, 1, 1) <= start <= end < date(9999, 1, 1)
        ):
            raise ValueError("SIMEM requires ordered inclusive dates from 2013-01-01")
        days = (end - start).days + 1
        if days > self.maximum_requests:
            raise ValueError("SIMEM date range exceeds maximum_requests")
        if version not in _VERSIONS:
            raise ValueError("Select one explicit SIMEM revision TX1..TX5, TXF or TXR")
        if resource_ids is not None and (
            not resource_ids or any(not isinstance(x, str) or not x for x in resource_ids)
        ):
            raise ValueError("resource_ids must be nonempty plant codes")
        frames: list[pd.DataFrame] = []
        records: list[RequestRecord] = []
        total = 0
        for offset in range(days):
            day = start + timedelta(days=offset)
            response = self.http.get_json(
                GENERATION_ENDPOINT,
                {
                    "datasetId": DATASET_ID,
                    "startDate": day.isoformat(),
                    "endDate": day.isoformat(),
                    "columnDestinyName": "Version",
                    "values": version,
                },
            )
            frame = parse_generation(
                response.value, version=version, maximum_rows=self.maximum_rows
            )
            if not frame["timestamp"].dt.tz_convert("America/Bogota").dt.date.eq(day).all():
                raise RetrievalError("SIMEM returned observations outside the requested date")
            total += len(frame)
            if total > self.maximum_rows:
                raise RetrievalError("SIMEM query exceeds maximum_rows")
            frames.append(frame)
            records.append(response.record)
        result = pd.concat(frames, ignore_index=True)
        result.attrs.update(frames[0].attrs)
        if resource_ids is not None:
            if set(resource_ids) - set(result["unit_id"]):
                raise RetrievalError("SIMEM requested resource_ids absent from returned generation")
            result = result.loc[result["unit_id"].isin(resource_ids)].reset_index(drop=True)
        return GenerationResult(result, tuple(records))
