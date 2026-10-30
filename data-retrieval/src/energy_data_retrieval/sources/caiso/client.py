"""CAISO Today's Outlook fuel-source CSV: five-minute average power in MW.

Imports, net battery output and mixed Other supply are separate flows, never
silently included in a generation total. These operational displays are not
settlement-quality data.
Native CSV clock labels omit UTC offsets; ambiguous/nonexistent DST labels are
rejected rather than guessed, interpolated or shifted to another interval.
"""

from __future__ import annotations

import csv
import io
import math
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd

from energy_data_retrieval.generation import GenerationResult
from energy_data_retrieval.transport import HTTPClient, RequestRecord, RetrievalError

CAISO_HOSTS = frozenset({"www.caiso.com"})
HISTORY_ROOT = "https://www.caiso.com/outlook/history"
REFERENCE_IDS = ("caiso_todays_outlook_supply",)
_PACIFIC = ZoneInfo("America/Los_Angeles")
_TECHNOLOGIES = {
    "Solar": "solar",
    "Wind": "wind",
    "Geothermal": "geothermal",
    "Biomass": "biomass",
    "Biogas": "biogas",
    "Small hydro": "small_hydro",
    "Coal": "coal",
    "Nuclear": "nuclear",
    "Natural Gas": "natural_gas",
    "Large Hydro": "large_hydro",
    "Batteries": "batteries",
    "Imports": "imports",
    "Other": "other",
}
_FLOW_TYPES = {
    "Imports": "net_import",
    "Batteries": "net_storage",
    "Other": "other_supply",
}
_COLUMNS = [
    "timestamp",
    "source",
    "area",
    "technology",
    "flow",
    "value",
    "unit",
    "aggregation",
    "source_date",
    "source_time",
]


def _timestamp(day: date, label: str) -> datetime:
    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", label):
        raise RetrievalError("Invalid CAISO clock label")
    hour, minute = map(int, label.split(":"))
    if minute % 5:
        raise RetrievalError("CAISO clock label is not on a five-minute grid")
    native = datetime(day.year, day.month, day.day, hour, minute)
    candidates = {
        native.replace(tzinfo=_PACIFIC, fold=fold).astimezone(UTC)
        for fold in (0, 1)
        if native.replace(tzinfo=_PACIFIC, fold=fold)
        .astimezone(UTC)
        .astimezone(_PACIFIC)
        .replace(tzinfo=None)
        == native
    }
    if len(candidates) != 1:
        raise RetrievalError("CAISO CSV has an ambiguous or nonexistent Pacific DST clock label")
    return candidates.pop()


def parse_fuel_mix(text: str, *, day: date, maximum_rows: int = 1_000_000) -> pd.DataFrame:
    """Parse one source-calendar day's native ``fuelsource.csv`` without gap filling.

    ``timestamp`` is the published clock label converted to UTC, not an asserted
    interval-start or interval-end convention. Each source value is a five-minute
    average MW. Missing numeric cells stay missing; signed values stay signed.
    The CSV cannot disambiguate the repeated fall-back hour or represent a
    nonexistent spring-forward hour, so those labels fail explicitly.
    """
    if type(day) is not date:
        raise ValueError("day must be the CAISO source calendar date")
    if type(maximum_rows) is not int or not 1 <= maximum_rows <= 10_000_000:
        raise ValueError("maximum_rows must be in 1..10000000")
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff"), newline=""))
    fields = reader.fieldnames
    if (
        not fields
        or fields[0] != "Time"
        or len(fields) < 2
        or len(fields) != len(set(fields))
        or any(name not in _TECHNOLOGIES for name in fields[1:])
    ):
        raise RetrievalError("Expected CAISO fuel-source CSV with known resource columns")
    rows: list[dict[str, object]] = []
    previous: datetime | None = None
    for item in reader:
        if None in item or any(value is None for value in item.values()):
            raise RetrievalError("CAISO CSV row does not match its header")
        label = item["Time"]
        stamp = _timestamp(day, label)
        if previous is not None and stamp <= previous:
            raise RetrievalError("CAISO clock labels are duplicated or out of order")
        previous = stamp
        for field in fields[1:]:
            if len(rows) >= maximum_rows:
                raise RetrievalError("CAISO response exceeds maximum_rows")
            raw_value = item[field].strip()
            try:
                value = float("nan") if raw_value == "" else float(raw_value)
            except ValueError:
                raise RetrievalError("CAISO generation is not numeric") from None
            if raw_value and not math.isfinite(value):
                raise RetrievalError("CAISO generation contains a non-finite value")
            flow = _FLOW_TYPES.get(field, "generation")
            rows.append(
                {
                    "timestamp": stamp,
                    "source": "caiso",
                    "area": "CAISO",
                    "technology": _TECHNOLOGIES[field],
                    "flow": flow,
                    "value": value,
                    "unit": "MW",
                    "aggregation": "five_minute_average_power",
                    "source_date": day.isoformat(),
                    "source_time": label,
                }
            )
    frame = pd.DataFrame(rows, columns=_COLUMNS)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame = frame.astype({"value": "float64"})
    frame.attrs.update(
        source="CAISO Today's Outlook fuel source",
        unit="MW",
        interval_minutes=5,
        scope="CAISO operational fuel mix; imports, storage and Other supply remain distinct flows",
        timestamp_semantics="Pacific clock label converted to UTC; interval edge not inferred",
        dst_policy="Ambiguous or nonexistent native clock labels rejected; no offset guessed",
        missing_policy="Blank cells remain missing; no absent intervals are filled",
        quality="Informational operational display; not settlement or billing data",
        reference_ids=list(REFERENCE_IDS),
    )
    return frame


@dataclass(slots=True)
class CAISOClient:
    """Bounded public daily CSV retrieval, with no API key."""

    http: HTTPClient
    maximum_requests: int = 31
    maximum_rows: int = 1_000_000

    def __post_init__(self) -> None:
        if type(self.maximum_requests) is not int or not 1 <= self.maximum_requests <= 1000:
            raise ValueError("maximum_requests must be in 1..1000")
        if type(self.maximum_rows) is not int or not 1 <= self.maximum_rows <= 10_000_000:
            raise ValueError("maximum_rows must be in 1..10000000")

    def generation(self, start: date, end: date) -> GenerationResult:
        """Retrieve inclusive Pacific source dates; retain imports and net storage separately."""
        if type(start) is not date or type(end) is not date or start > end or end.year > 9998:
            raise ValueError("Use ordered inclusive dates with end year <= 9998")
        if (end - start).days + 1 > self.maximum_requests:
            raise ValueError("CAISO date range exceeds maximum_requests")
        frames: list[pd.DataFrame] = []
        provenance: list[RequestRecord] = []
        day = start
        count = 0
        while day <= end:
            endpoint = f"{HISTORY_ROOT}/{day:%Y%m%d}/fuelsource.csv"
            response = self.http.get_text(endpoint)
            frame = parse_fuel_mix(response.value, day=day, maximum_rows=self.maximum_rows)
            count += len(frame)
            if count > self.maximum_rows:
                raise RetrievalError("CAISO retrieval exceeds maximum_rows")
            frames.append(frame)
            provenance.append(response.record)
            day += timedelta(days=1)
        metadata = frames[0].attrs.copy()
        combined = pd.concat(frames, ignore_index=True)
        combined.attrs.update(metadata)
        return GenerationResult(combined, tuple(provenance))
