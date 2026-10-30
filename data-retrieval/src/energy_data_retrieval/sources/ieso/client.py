"""Ontario's public hourly generator output, distinct from capability/forecasts."""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta, timezone

import pandas as pd

from energy_data_retrieval.generation import GenerationResult
from energy_data_retrieval.transport import HTTPClient, RequestRecord, RetrievalError

IESO_HOSTS = frozenset({"reports-public.ieso.ca"})
REPORT_ROOT = "https://reports-public.ieso.ca/public/GenOutputCapability"
REFERENCE_IDS = ("ieso_generator_output", "ieso_report_directory")
_EST = timezone(timedelta(hours=-5))
_NS = {"i": "http://www.theIMO.com/schema"}
_COLUMNS = [
    "timestamp",
    "interval_end",
    "source",
    "area",
    "unit_id",
    "technology",
    "value",
    "unit",
    "source_date",
    "hour_ending",
    "source_created_at",
    "quality",
    "aggregation",
]


def _limit(value: int, name: str, upper: int) -> None:
    if type(value) is not int or not 1 <= value <= upper:
        raise ValueError(f"{name} must be an integer in 1..{upper}")


def _text(parent: ET.Element, path: str) -> str:
    value = parent.findtext(path, namespaces=_NS)
    if value is None or not value.strip():
        raise RetrievalError(f"IESO report omitted {path}")
    return value.strip()


def parse_generation_xml(payload: str, *, maximum_rows: int = 1_000_000) -> pd.DataFrame:
    """Parse only ``Outputs/Output/EnergyMW`` from a native IESO daily XML report.

    Source Hour 1 covers 00:00-01:00 and Hour 24 covers 23:00-24:00, in fixed
    Eastern Standard Time (UTC-05), including summer. ``timestamp`` is the UTC
    interval start. Published values are hourly averages of operational MW
    telemetry, not settlement-meter MWh. Missing telemetry remains NaN.
    """
    _limit(maximum_rows, "maximum_rows", 10_000_000)
    if "<!DOCTYPE" in payload.upper() or "<!ENTITY" in payload.upper():
        raise RetrievalError("IESO XML declarations/entities are not accepted")
    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        raise RetrievalError("IESO returned malformed XML") from None
    if root.get("docID") != "GenOutputCapability":
        raise RetrievalError("Expected IESO GenOutputCapability report")
    body = root.find("i:IMODocBody", _NS)
    if body is None:
        raise RetrievalError("IESO report has no body")
    label = _text(body, "i:Date")
    try:
        day = date.fromisoformat(label)
    except ValueError:
        raise RetrievalError("IESO report has an invalid date") from None
    origin = datetime.combine(day, datetime.min.time(), _EST)
    created = root.findtext("i:IMODocHeader/i:CreatedAt", default="", namespaces=_NS)
    generators = body.find("i:Generators", _NS)
    if generators is None:
        raise RetrievalError("IESO report omitted Generators")
    rows: list[dict[str, object]] = []
    for generator in generators.findall("i:Generator", _NS):
        identifier = _text(generator, "i:GeneratorName")
        technology = _text(generator, "i:FuelType")
        outputs = generator.find("i:Outputs", _NS)
        if outputs is None:
            raise RetrievalError("IESO generator omitted actual Outputs")
        for output in outputs.findall("i:Output", _NS):
            if len(rows) >= maximum_rows:
                raise RetrievalError("IESO response exceeds maximum_rows")
            try:
                hour = int(_text(output, "i:Hour"))
            except ValueError:
                raise RetrievalError("IESO hour must be 1..24") from None
            if not 1 <= hour <= 24:
                raise RetrievalError("IESO hour must be 1..24")
            node = output.find("i:EnergyMW", _NS)
            # IESO publishes Hour-only Output elements for unavailable telemetry.
            # Their absence is distinct from an omitted Outputs container.
            raw = "" if node is None else (node.text or "").strip()
            if raw in {"", "N/A"}:
                value = float("nan")
            else:
                try:
                    value = float(raw)
                except ValueError:
                    raise RetrievalError("IESO EnergyMW must be numeric or N/A") from None
                if not math.isfinite(value):
                    raise RetrievalError("IESO EnergyMW must be finite")
            rows.append(
                {
                    "timestamp": (origin + timedelta(hours=hour - 1)).astimezone(UTC),
                    "interval_end": (origin + timedelta(hours=hour)).astimezone(UTC),
                    "source": "ieso",
                    "area": "Ontario",
                    "unit_id": identifier,
                    "technology": technology,
                    "value": value,
                    "unit": "MW",
                    "source_date": label,
                    "hour_ending": hour,
                    "source_created_at": created,
                    "quality": "missing" if math.isnan(value) else "operational_telemetry",
                    "aggregation": "hourly_mean",
                }
            )
    frame = pd.DataFrame(rows, columns=_COLUMNS)
    for column in ("timestamp", "interval_end"):
        frame[column] = pd.to_datetime(frame[column], utc=True)
    frame["value"] = frame["value"].astype(float)
    frame = frame.drop_duplicates()
    if frame.duplicated(["unit_id", "timestamp"]).any():
        raise RetrievalError("IESO returned conflicting unit/hour observations")
    frame = frame.sort_values(["timestamp", "unit_id"]).reset_index(drop=True)
    frame.attrs.update(
        source_timezone="UTC-05:00 (IESO fixed EST)",
        timestamp_semantics="UTC interval start derived from source hour ending",
        coverage="IESO participating facilities with maximum capability of at least 20 MW",
        missing_policy="N/A and empty telemetry remain missing; no gap filling",
        source_report_date=label,
        reference_ids=list(REFERENCE_IDS),
    )
    return frame


@dataclass(slots=True)
class IESOClient:
    """Fetch bounded daily reports from IESO's public recent XML archive."""

    http: HTTPClient
    maximum_requests: int = 31
    maximum_rows: int = 1_000_000

    def __post_init__(self) -> None:
        _limit(self.maximum_requests, "maximum_requests", 1000)
        _limit(self.maximum_rows, "maximum_rows", 10_000_000)

    def generation(
        self, start: date, end: date, *, unit_ids: list[str] | None = None
    ) -> GenerationResult:
        """Retrieve inclusive EST report dates; archive retention is provider-limited.

        The public XML archive normally covers 90 days. Older monthly CSV files
        are a separate product and are not silently substituted. A missing report
        raises a retrieval error instead of manufacturing zero output.
        """
        if type(start) is not date or type(end) is not date or not start <= end < date(9999, 1, 1):
            raise ValueError("IESO requires ordered inclusive date objects")
        days = (end - start).days + 1
        if days > self.maximum_requests:
            raise ValueError("IESO date range exceeds maximum_requests")
        if unit_ids is not None and (
            not unit_ids or any(not isinstance(item, str) or not item for item in unit_ids)
        ):
            raise ValueError("unit_ids must be nonempty identifiers")
        frames: list[pd.DataFrame] = []
        records: list[RequestRecord] = []
        total = 0
        for offset in range(days):
            day = start + timedelta(days=offset)
            response = self.http.get_text(f"{REPORT_ROOT}/PUB_GenOutputCapability_{day:%Y%m%d}.xml")
            frame = parse_generation_xml(response.value, maximum_rows=self.maximum_rows)
            if frame.attrs["source_report_date"] != day.isoformat():
                raise RetrievalError("IESO returned a report outside the requested date")
            total += len(frame)
            if total > self.maximum_rows:
                raise RetrievalError("IESO query exceeds maximum_rows")
            frames.append(frame)
            records.append(response.record)
        result = pd.concat(frames, ignore_index=True)
        result.attrs.update(frames[0].attrs)
        if unit_ids is not None:
            if set(unit_ids) - set(result["unit_id"]):
                raise RetrievalError(
                    "IESO requested unit_ids were absent from the returned reports"
                )
            result = result.loc[result["unit_id"].isin(unit_ids)].reset_index(drop=True)
        return GenerationResult(result, tuple(records))
