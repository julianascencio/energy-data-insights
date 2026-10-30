"""SMARD's published German solar and wind generation, in quarter-hour MWh.

These chart series are verified Bundesnetzagentur publications originating from
ENTSO-E, not independent plant observations. SMARD already converts the upstream
average MW to quarter-hour MWh. No additional division or power-to-energy
conversion belongs in this parser.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from types import MappingProxyType
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

SMARD_HOSTS = frozenset({"www.smard.de"})
CHART_ROOT = "https://www.smard.de/app/chart_data"
SMARD_TECHNOLOGIES = MappingProxyType(
    {"solar": "4068", "wind_onshore": "4067", "wind_offshore": "1225"}
)
REFERENCE_IDS = ("smard_generation_user_guide", "smard_data_use")
_BERLIN = ZoneInfo("Europe/Berlin")
_COLUMNS = [
    "timestamp",
    "interval_start",
    "interval_end",
    "source",
    "area",
    "technology",
    "value",
    "unit",
    "aggregation",
    "source_timestamp_ms",
]


def normalize_generation(
    payload: JSONValue,
    *,
    technology: str,
    region: str = "DE",
    maximum_rows: int = 1_000_000,
) -> pd.DataFrame:
    """Read one native weekly SMARD ``quarterhour`` series as interval MWh.

    Epoch millisecond labels identify UTC interval starts and therefore preserve
    both occurrences of a repeated autumn civil hour. Nulls remain missing and
    reported zero/negative values are retained. Exact duplicates collapse;
    conflicting observations for the same interval raise.
    """
    if technology not in SMARD_TECHNOLOGIES or region != "DE":
        raise ValueError("Select a documented solar/wind technology for SMARD region='DE'")
    if type(maximum_rows) is not int or not 1 <= maximum_rows <= 10_000_000:
        raise ValueError("maximum_rows must be in 1..10000000")
    root = object_value(payload)
    metadata = object_value(root.get("meta_data"))
    if type(metadata.get("version")) is not int or metadata["version"] != 1:
        raise RetrievalError("Unsupported SMARD chart schema version")
    points = array_value(root.get("series"))
    if len(points) > maximum_rows:
        raise RetrievalError("SMARD response exceeds maximum_rows")
    rows: list[dict[str, object]] = []
    for raw in points:
        point = array_value(raw)
        if len(point) != 2:
            raise RetrievalError("SMARD series point must contain timestamp and value")
        epoch, value = point
        if type(epoch) is not int or epoch % 900_000:
            raise RetrievalError("SMARD timestamp must be quarter-hour epoch milliseconds")
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise RetrievalError("SMARD generation must be finite numeric MWh or null")
        try:
            stamp = pd.Timestamp(epoch, unit="ms", tz="UTC")
        except (ValueError, OverflowError):
            raise RetrievalError("SMARD timestamp is outside the supported range") from None
        rows.append(
            {
                "timestamp": stamp,
                "interval_start": stamp,
                "interval_end": stamp + pd.Timedelta(minutes=15),
                "source": "smard",
                "area": region,
                "technology": technology,
                "value": float("nan") if value is None else float(value),
                "unit": "MWh",
                "aggregation": "quarter_hour_energy",
                "source_timestamp_ms": epoch,
            }
        )
    frame = pd.DataFrame(rows, columns=_COLUMNS)
    for column in ("timestamp", "interval_start", "interval_end"):
        frame[column] = pd.to_datetime(frame[column], utc=True)
    frame = frame.astype({"value": "float64"}).drop_duplicates()
    if frame.duplicated(["timestamp"]).any():
        raise RetrievalError("Conflicting SMARD values for one quarter hour")
    frame = frame.sort_values("timestamp").reset_index(drop=True)
    frame.attrs.update(
        source="Bundesnetzagentur SMARD",
        upstream_source="ENTSO-E",
        unit="MWh",
        interval_minutes=15,
        chart_id=SMARD_TECHNOLOGIES[technology],
        region=region,
        timestamp_semantics="UTC start of quarter-hour energy interval",
        source_created_ms=metadata.get("created"),
        scope="German national net grid-feed generation by selected solar/wind technology",
        missing_policy="Null remains missing; absent quarters are not inferred",
        licence="CC BY 4.0; attribution Bundesnetzagentur | SMARD.de",
        reference_ids=list(REFERENCE_IDS),
    )
    return frame


@dataclass(slots=True)
class SMARDClient:
    """Bounded index and weekly-series retrieval from the public chart downloads."""

    http: HTTPClient
    maximum_requests: int = 64
    maximum_rows: int = 1_000_000

    def __post_init__(self) -> None:
        if type(self.maximum_requests) is not int or not 1 <= self.maximum_requests <= 1000:
            raise ValueError("maximum_requests must be in 1..1000")
        if type(self.maximum_rows) is not int or not 1 <= self.maximum_rows <= 10_000_000:
            raise ValueError("maximum_rows must be in 1..10000000")

    def generation(
        self,
        start: date,
        end: date,
        *,
        technologies: Sequence[str] = ("solar", "wind_onshore", "wind_offshore"),
        region: str = "DE",
    ) -> GenerationResult:
        """Fetch inclusive German civil dates, preserving the source's MWh values.

        Index requests discover actual week boundaries rather than assuming
        every local week is 168 hours. Each downloaded week is filtered to the
        requested half-open UTC interval. Solar, onshore and offshore wind are
        separate non-overlapping series, not a complete national energy mix.
        """
        if type(start) is not date or type(end) is not date or start > end or end.year > 9998:
            raise ValueError("Use ordered inclusive dates with end year <= 9998")
        if (
            region != "DE"
            or isinstance(technologies, str)
            or not technologies
            or any(
                not isinstance(item, str) or item not in SMARD_TECHNOLOGIES for item in technologies
            )
            or len(set(technologies)) != len(technologies)
        ):
            raise ValueError("Select unique documented solar/wind technologies for region='DE'")
        begin = datetime.combine(start, time(), _BERLIN).astimezone(UTC)
        until = datetime.combine(end + timedelta(days=1), time(), _BERLIN).astimezone(UTC)
        begin_ms, until_ms = int(begin.timestamp() * 1000), int(until.timestamp() * 1000)
        if len(technologies) > self.maximum_requests:
            raise ValueError("SMARD technology selection exceeds maximum_requests")
        records: list[RequestRecord] = []
        plan: list[tuple[str, str, int]] = []
        for technology in technologies:
            identifier = SMARD_TECHNOLOGIES[technology]
            response = self.http.get_json(
                f"{CHART_ROOT}/{identifier}/{region}/index_quarterhour.json"
            )
            records.append(response.record)
            raw_index = array_value(object_value(response.value).get("timestamps"))
            if any(type(value) is not int or value < 0 for value in raw_index):
                raise RetrievalError("SMARD index contains invalid epoch milliseconds")
            timestamps = [int(value) for value in raw_index if isinstance(value, int)]
            if timestamps != sorted(set(timestamps)):
                raise RetrievalError("SMARD index must contain ordered unique week boundaries")
            for position, week in enumerate(timestamps):
                next_week = timestamps[position + 1] if position + 1 < len(timestamps) else math.inf
                if week < until_ms and next_week > begin_ms:
                    plan.append((technology, identifier, week))
        if len(records) + len(plan) > self.maximum_requests:
            raise ValueError("SMARD selected weeks exceed maximum_requests")
        frames: list[pd.DataFrame] = []
        count = 0
        for technology, identifier, week in plan:
            response = self.http.get_json(
                f"{CHART_ROOT}/{identifier}/{region}/{identifier}_{region}_quarterhour_{week}.json"
            )
            frame = normalize_generation(
                response.value, technology=technology, region=region, maximum_rows=self.maximum_rows
            )
            frame = frame.loc[frame["timestamp"].between(begin, until, inclusive="left")].copy()
            count += len(frame)
            if count > self.maximum_rows:
                raise RetrievalError("SMARD retrieval exceeds maximum_rows")
            frames.append(frame)
            records.append(response.record)
        if not frames:
            empty = normalize_generation(
                {"meta_data": {"version": 1}, "series": []},
                technology=technologies[0],
                region=region,
            )
            return GenerationResult(empty, tuple(records))
        combined = pd.concat(frames, ignore_index=True).drop_duplicates()
        if combined.duplicated(["timestamp", "technology"]).any():
            raise RetrievalError("Conflicting SMARD observations across weekly files")
        combined = combined.sort_values(["timestamp", "technology"]).reset_index(drop=True)
        combined.attrs.update(
            source="Bundesnetzagentur SMARD",
            upstream_source="ENTSO-E",
            unit="MWh",
            interval_minutes=15,
            scope="German net grid-feed generation by selected solar/wind technology",
            timestamp_semantics="UTC start of quarter-hour energy interval",
            missing_policy="Null remains missing; absent quarters are not inferred",
            licence="CC BY 4.0; attribution Bundesnetzagentur | SMARD.de",
            region=region,
            technologies=list(technologies),
            reference_ids=list(REFERENCE_IDS),
        )
        return GenerationResult(combined, tuple(records))
