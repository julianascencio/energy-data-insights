"""Consolidated half-hourly French production by technology from ODRÉ.

The dataset also has quarter-hour forecasts. Their empty generation fields
are not actual observations and are excluded without filling them with zero.
Only the eight mutually exclusive top-level production categories are used;
subcategories, pumping, consumption and imports are never double-counted.
"""

from __future__ import annotations

import math
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

RTE_HOSTS = frozenset({"odre.opendatasoft.com"})
DATASET = "eco2mix-national-cons-def"
GENERATION_ENDPOINT = (
    f"https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/{DATASET}/records"
)
REFERENCE_IDS = ("rte_eco2mix_consolidated", "rte_eco2mix_api")
TECHNOLOGIES = (
    "fioul",
    "charbon",
    "gaz",
    "nucleaire",
    "eolien",
    "solaire",
    "hydraulique",
    "bioenergies",
)
_PARIS = ZoneInfo("Europe/Paris")
_COLUMNS = [
    "timestamp",
    "source",
    "area",
    "technology",
    "value",
    "unit",
    "aggregation",
    "nature",
    "source_datetime",
]


def normalize_generation(payload: JSONValue, *, maximum_rows: int = 1_000_000) -> pd.DataFrame:
    """Parse an Explore API 2.1 page of actual half-hourly generation in MW.

    Source ``date_heure`` has an explicit UTC offset. Forecast-only quarter-hour
    rows are counted in metadata and omitted; null generation in a genuine
    half-hour row stays missing. Source nature distinguishes consolidated and
    definitive observations. Neither the technology detail nor a national total
    is summed into the top-level production categories.
    """
    if type(maximum_rows) is not int or not 1 <= maximum_rows <= 10_000_000:
        raise ValueError("maximum_rows must be in 1..10000000")
    root = object_value(payload)
    if "error" in root or "errors" in root:
        raise RetrievalError("RTE returned an API error document")
    raw_rows = array_value(root.get("results"))
    if len(raw_rows) * len(TECHNOLOGIES) > maximum_rows:
        raise RetrievalError("RTE page exceeds maximum_rows")
    rows: list[dict[str, object]] = []
    skipped = 0
    for raw in raw_rows:
        item = object_value(raw)
        label = item.get("date_heure")
        if not isinstance(label, str):
            raise RetrievalError("RTE omitted its offset-bearing timestamp")
        try:
            stamp = datetime.fromisoformat(label)
        except ValueError:
            raise RetrievalError("Invalid RTE date_heure") from None
        if stamp.tzinfo is None or stamp.utcoffset() is None:
            raise RetrievalError("RTE timestamps must include a UTC offset")
        if item.get("perimetre") != "France":
            raise RetrievalError("Expected France's national RTE generation dataset")
        if stamp.second or stamp.microsecond or stamp.minute not in {0, 15, 30, 45}:
            raise RetrievalError("RTE timestamp is not on the published quarter-hour grid")
        if any(key not in item for key in TECHNOLOGIES):
            raise RetrievalError("RTE omitted a top-level generation field")
        if stamp.minute in {15, 45}:
            if any(item[key] is not None for key in TECHNOLOGIES):
                raise RetrievalError(
                    "Unexpected actual generation on an RTE quarter-hour forecast row"
                )
            skipped += 1
            continue
        nature = item.get("nature")
        if nature not in {"Données consolidées", "Données définitives"}:
            raise RetrievalError("Expected consolidated or definitive RTE observations")
        for technology in TECHNOLOGIES:
            raw_value = item[technology]
            if isinstance(raw_value, bool) or not isinstance(
                raw_value, (int, float, str, type(None))
            ):
                raise RetrievalError("RTE generation must be numeric or null")
            try:
                value = float("nan") if raw_value is None else float(raw_value)
            except ValueError:
                raise RetrievalError("RTE generation is not numeric") from None
            if raw_value is not None and not math.isfinite(value):
                raise RetrievalError("RTE generation contains a non-finite value")
            rows.append(
                {
                    "timestamp": stamp,
                    "source": "rte",
                    "area": "FR",
                    "technology": technology,
                    "value": value,
                    "unit": "MW",
                    "aggregation": "half_hourly_reported_power",
                    "nature": nature,
                    "source_datetime": label,
                }
            )
    frame = pd.DataFrame(rows, columns=_COLUMNS)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame = frame.astype({"value": "float64"}).drop_duplicates()
    if frame.duplicated(["timestamp", "technology"]).any():
        raise RetrievalError("Conflicting RTE generation observations")
    frame = frame.sort_values(["timestamp", "technology"]).reset_index(drop=True)
    frame.attrs.update(
        source="RTE ODRÉ éCO2mix national consolidated/definitive",
        unit="MW",
        interval_minutes=30,
        dataset=DATASET,
        excluded_forecast_only_rows=skipped,
        scope="National generation by top-level technology; not plant telemetry",
        missing_policy="Null remains missing; forecast-only quarter-hours excluded; no filling",
        timestamp_semantics="Provider's offset-bearing half-hour label converted to UTC",
        reference_ids=list(REFERENCE_IDS),
    )
    return frame


@dataclass(slots=True)
class RTEClient:
    """Public Explore API retrieval, paginated separately for each French civil day."""

    http: HTTPClient
    maximum_requests: int = 64
    maximum_rows: int = 1_000_000
    page_size: int = 100

    def __post_init__(self) -> None:
        for value, name, upper in (
            (self.maximum_requests, "maximum_requests", 1000),
            (self.maximum_rows, "maximum_rows", 10_000_000),
            (self.page_size, "page_size", 100),
        ):
            if type(value) is not int or not 1 <= value <= upper:
                raise ValueError(f"{name} must be in 1..{upper}")

    def generation(
        self, start: date, end: date, *, dataset: str = "consolidated"
    ) -> GenerationResult:
        """Fetch inclusive French civil dates from the consolidated national dataset.

        Live telemetry is a different product and is deliberately not aliased
        to consolidated generation. Pagination must account for all advertised
        records; short, repeated or changing pages fail rather than truncate.
        """
        if type(start) is not date or type(end) is not date or start > end or end.year > 9998:
            raise ValueError("Use ordered inclusive dates with end year <= 9998")
        if dataset != "consolidated":
            raise ValueError("This connector supports dataset='consolidated' only")
        if (end - start).days + 1 > self.maximum_requests:
            raise ValueError("RTE date range exceeds maximum_requests")
        frames: list[pd.DataFrame] = []
        provenance: list[RequestRecord] = []
        day = start
        count = 0
        skipped = 0
        while day <= end:
            begin = datetime.combine(day, time(), _PARIS).astimezone(UTC)
            until = datetime.combine(day + timedelta(days=1), time(), _PARIS).astimezone(UTC)
            where = (
                f"date_heure >= date'{begin.isoformat()}' "
                f"and date_heure < date'{until.isoformat()}'"
            )
            offset = 0
            expected: int | None = None
            seen: set[str] = set()
            while True:
                if len(provenance) >= self.maximum_requests:
                    raise RetrievalError("RTE pagination exceeds maximum_requests")
                response = self.http.get_json(
                    GENERATION_ENDPOINT,
                    {
                        "where": where,
                        "order_by": "date_heure",
                        "limit": str(self.page_size),
                        "offset": str(offset),
                    },
                )
                root = object_value(response.value)
                total = root.get("total_count")
                if (
                    type(total) is not int
                    or total < 0
                    or (expected is not None and total != expected)
                ):
                    raise RetrievalError("RTE pagination total_count is missing or changed")
                expected = total
                entries = array_value(root.get("results"))
                if len(entries) > self.page_size or offset + len(entries) > total:
                    raise RetrievalError("RTE pagination returned an invalid page length")
                if not entries and offset < total:
                    raise RetrievalError("RTE pagination ended before total_count")
                for raw in entries:
                    item = object_value(raw)
                    stamp = item.get("date_heure")
                    if not isinstance(stamp, str) or stamp in seen:
                        raise RetrievalError("RTE pagination repeated an observation")
                    seen.add(stamp)
                    try:
                        parsed = datetime.fromisoformat(stamp)
                        valid = parsed.tzinfo is not None and begin <= parsed < until
                    except ValueError:
                        valid = False
                    if not valid:
                        raise RetrievalError("RTE observation outside the requested civil day")
                frame = normalize_generation(response.value, maximum_rows=self.maximum_rows)
                count += len(frame)
                if count > self.maximum_rows:
                    raise RetrievalError("RTE retrieval exceeds maximum_rows")
                skipped += int(frame.attrs["excluded_forecast_only_rows"])
                frames.append(frame)
                provenance.append(response.record)
                offset += len(entries)
                if offset == total:
                    break
            day += timedelta(days=1)
        metadata = frames[0].attrs.copy()
        combined = pd.concat(frames, ignore_index=True).sort_values(["timestamp", "technology"])
        if combined.duplicated(["timestamp", "technology"]).any():
            raise RetrievalError("RTE returned duplicate observations across pages")
        combined = combined.reset_index(drop=True)
        combined.attrs.update(metadata)
        combined.attrs["excluded_forecast_only_rows"] = skipped
        return GenerationResult(combined, tuple(provenance))
