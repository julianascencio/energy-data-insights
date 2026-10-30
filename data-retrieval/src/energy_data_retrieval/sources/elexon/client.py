"""Half-hourly BM-unit metered energy from Elexon Insights B1610.

B1610 quantity is MWh, including negative demand and zero. It is published
through settlement, not live SCADA. Dates and settlement periods identify
46/48/50 half-hour civil days in Great Britain; source end labels are UTC.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
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

ELEXON_HOSTS = frozenset({"data.elexon.co.uk"})
GENERATION_ENDPOINT = "https://data.elexon.co.uk/bmrs/api/v1/datasets/B1610/stream"
REFERENCE_IDS = ("elexon_insights_api", "elexon_b1610_metered_volumes")
_LONDON = ZoneInfo("Europe/London")
_COLUMNS = [
    "timestamp",
    "interval_start",
    "interval_end",
    "source",
    "area",
    "unit_id",
    "national_grid_bm_unit_id",
    "value",
    "unit",
    "flow",
    "aggregation",
    "settlement_date",
    "settlement_period",
    "settlement_run",
    "source_end_time",
    "source_type",
]


def _midnight(day: date) -> datetime:
    return datetime.combine(day, time(), _LONDON).astimezone(UTC)


def normalize_generation(payload: JSONValue, *, maximum_rows: int = 1_000_000) -> pd.DataFrame:
    """Normalize a native B1610 stream without guessing away settlement revisions.

    One row identifies a BM unit and settlement interval. Exact duplicate rows
    collapse, but conflicting values or different runs for that same key raise:
    the endpoint normally returns the latest available run. All quantities are
    signed metered MWh; the API's generic ``psrType`` is not a fuel classification.
    """
    if type(maximum_rows) is not int or not 1 <= maximum_rows <= 10_000_000:
        raise ValueError("maximum_rows must be in 1..10000000")
    observations = array_value(payload)
    if len(observations) > maximum_rows:
        raise RetrievalError("Elexon response exceeds maximum_rows")
    rows: list[dict[str, object]] = []
    for raw in observations:
        item = object_value(raw)
        if item.get("dataset") != "B1610":
            raise RetrievalError("Expected Elexon B1610 actual metered volumes")
        label, identifier = item.get("settlementDate"), item.get("bmUnit")
        if not isinstance(label, str) or not isinstance(identifier, str) or not identifier:
            raise RetrievalError("Elexon omitted settlement date or BM unit")
        try:
            day = date.fromisoformat(label)
            start = _midnight(day)
            next_day = _midnight(day + timedelta(days=1))
        except (ValueError, OverflowError):
            raise RetrievalError("Elexon returned an invalid settlement date") from None
        period = item.get("settlementPeriod")
        count = int((next_day - start).total_seconds() / 1800)
        if type(period) is not int or not 1 <= period <= count:
            raise RetrievalError("Elexon settlement period is invalid for the UK civil day")
        interval_start = start + timedelta(minutes=30 * (period - 1))
        interval_end = interval_start + timedelta(minutes=30)
        end_label = item.get("halfHourEndTime")
        if not isinstance(end_label, str):
            raise RetrievalError("Elexon omitted halfHourEndTime")
        try:
            end_time = datetime.fromisoformat(end_label)
        except ValueError:
            raise RetrievalError("Elexon returned an invalid halfHourEndTime") from None
        # The native B1610 schema labels this UTC field without a trailing Z.
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=UTC)
        if end_time.astimezone(UTC) != interval_end:
            raise RetrievalError("Elexon end label disagrees with the settlement period")
        if "quantity" not in item:
            raise RetrievalError("Elexon omitted quantity")
        value = item["quantity"]
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise RetrievalError("Elexon quantity must be finite numeric MWh or null")
        run = item.get("settlementRunType")
        if not isinstance(run, str) or not run:
            raise RetrievalError("Elexon omitted settlement run")
        rows.append(
            {
                "timestamp": interval_start,
                "interval_start": interval_start,
                "interval_end": interval_end,
                "source": "elexon",
                "area": "GB",
                "unit_id": identifier,
                "national_grid_bm_unit_id": item.get("nationalGridBmUnitId"),
                "value": float("nan") if value is None else float(value),
                "unit": "MWh",
                "flow": "net_generation_or_demand",
                "aggregation": "settlement_interval_energy",
                "settlement_date": label,
                "settlement_period": period,
                "settlement_run": run,
                "source_end_time": end_label,
                "source_type": item.get("psrType"),
            }
        )
    frame = pd.DataFrame(rows, columns=_COLUMNS)
    for column in ("timestamp", "interval_start", "interval_end"):
        frame[column] = pd.to_datetime(frame[column], utc=True)
    frame = frame.astype({"value": "float64"}).drop_duplicates()
    if frame.duplicated(["unit_id", "timestamp"]).any():
        raise RetrievalError("Conflicting Elexon observations or settlement revisions for one key")
    frame = frame.sort_values(["timestamp", "unit_id"]).reset_index(drop=True)
    frame.attrs.update(
        source="Elexon Insights B1610",
        unit="MWh",
        interval_minutes=30,
        scope="BM-unit signed metered energy, including consuming BM units; not live SCADA",
        timestamp_semantics="UTC interval start derived from UK settlement date and period",
        revision_policy="Latest available API settlement run retained; conflicting keys rejected",
        missing_policy="Null remains missing; no absent interval is filled",
        reference_ids=list(REFERENCE_IDS),
    )
    return frame


@dataclass(slots=True)
class ElexonClient:
    """No-key B1610 retrieval, bounded to six-hour UTC request chunks."""

    http: HTTPClient
    maximum_requests: int = 64
    maximum_rows: int = 1_000_000

    def __post_init__(self) -> None:
        if type(self.maximum_requests) is not int or not 1 <= self.maximum_requests <= 1000:
            raise ValueError("maximum_requests must be in 1..1000")
        if type(self.maximum_rows) is not int or not 1 <= self.maximum_rows <= 10_000_000:
            raise ValueError("maximum_rows must be in 1..10000000")

    def generation(self, start: date, end: date, *, bm_unit: str | None = None) -> GenerationResult:
        """Fetch inclusive UK settlement dates, optionally selecting one exact BM unit.

        The API uses inclusive interval-start bounds. Six-hour requests avoid
        one unbounded all-unit response; maximum_rows also limits the combined
        result. No BM-unit registry or generation technology is inferred.
        """
        if type(start) is not date or type(end) is not date or start > end or end.year > 9998:
            raise ValueError("Use ordered inclusive dates with end year <= 9998")
        if bm_unit is not None and not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", bm_unit):
            raise ValueError("bm_unit must be an exact Elexon BM-unit identifier")
        first, until = _midnight(start), _midnight(end + timedelta(days=1))
        chunks = math.ceil((until - first).total_seconds() / 21600)
        if chunks > self.maximum_requests:
            raise ValueError("Elexon date range exceeds maximum_requests")
        frames: list[pd.DataFrame] = []
        records: list[RequestRecord] = []
        count = 0
        current = first
        while current < until:
            stop = min(current + timedelta(hours=6), until)
            query = {"from": current.isoformat(), "to": (stop - timedelta(minutes=30)).isoformat()}
            if bm_unit is not None:
                query["bmUnit"] = bm_unit
            response = self.http.get_json(GENERATION_ENDPOINT, query)
            frame = normalize_generation(response.value, maximum_rows=self.maximum_rows)
            if not frame.empty and (
                not frame["timestamp"].between(current, stop, inclusive="left").all()
                or (bm_unit is not None and not frame["unit_id"].eq(bm_unit).all())
            ):
                raise RetrievalError("Elexon returned observations outside the requested selection")
            count += len(frame)
            if count > self.maximum_rows:
                raise RetrievalError("Elexon retrieval exceeds maximum_rows")
            frames.append(frame)
            records.append(response.record)
            current = stop
        metadata = frames[0].attrs.copy()
        combined = pd.concat(frames, ignore_index=True).sort_values(["timestamp", "unit_id"])
        if combined.duplicated(["timestamp", "unit_id"]).any():
            raise RetrievalError("Elexon returned overlapping chunk observations")
        combined = combined.reset_index(drop=True)
        combined.attrs.update(metadata)
        return GenerationResult(combined, tuple(records))
