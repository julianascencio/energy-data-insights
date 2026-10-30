"""New Zealand EMI plant-associated metered injections, in half-hour kWh."""

from __future__ import annotations

import csv
import io
import math
import re
from collections.abc import Sequence
from datetime import date, timedelta

import pandas as pd

from energy_data_retrieval.generation import GenerationResult
from energy_data_retrieval.transport import HTTPClient, RetrievalError

EMI_HOSTS = frozenset({"emidatasets.blob.core.windows.net"})
GENERATION_BASE = (
    "https://emidatasets.blob.core.windows.net/publicdata/"
    "Datasets/Wholesale/Generation/Generation_MD"
)
REFERENCE_IDS = ("nz_emi_generation", "nz_emi_license")
_COLUMNS = [
    "timestamp",
    "interval_end",
    "source",
    "area",
    "plant_id",
    "connection_id",
    "network_id",
    "technology",
    "fuel",
    "value",
    "unit",
    "aggregation",
    "source_date",
    "trading_period",
    "measurement_kind",
]


def _limit(value: int, name: str) -> None:
    if type(value) is not int or value < 1:
        raise ValueError(f"{name} must be a positive integer")


def generation_urls(start: date, end: date, *, maximum_requests: int = 24) -> tuple[str, ...]:
    """Plan inclusive civil-date retrieval as bounded monthly CSV requests."""
    _limit(maximum_requests, "maximum_requests")
    if type(start) is not date or type(end) is not date or end < start:
        raise ValueError("start and end must be ordered calendar dates")
    if start < date(1997, 8, 1):
        raise ValueError("The EMI generation archive starts in August 1997")
    count = (end.year - start.year) * 12 + end.month - start.month + 1
    if count > maximum_requests:
        raise ValueError("EMI interval exceeds maximum_requests")
    first = start.year * 12 + start.month - 1
    return tuple(
        f"{GENERATION_BASE}/{(first + n) // 12:04d}{(first + n) % 12 + 1:02d}_Generation_MD.csv"
        for n in range(count)
    )


def parse_generation_csv(data: bytes | str, *, maximum_rows: int = 2_000_000) -> pd.DataFrame:
    """Normalize native TP columns to UTC interval-start kWh observations.

    EMI maps metered grid injections to plants and sometimes apportions a shared
    injection point. This is not direct SCADA for every unit. Local trading days
    have 46, 48 or 50 actual half hours; invalid extra TP values fail rather than
    shifting subsequent days. Missing intervals remain NaN, never zero.
    """
    _limit(maximum_rows, "maximum_rows")
    try:
        text = data.decode("utf-8-sig") if isinstance(data, bytes) else data.lstrip("\ufeff")
    except UnicodeDecodeError:
        raise RetrievalError("EMI CSV must be UTF-8") from None
    reader = csv.DictReader(io.StringIO(text))
    fields = reader.fieldnames or []
    required = {"POC_Code", "Nwk_Code", "Gen_Code", "Fuel_Code", "Tech_Code", "Trading_Date"}
    if not required <= set(fields) or len(fields) != len(set(fields)):
        raise RetrievalError("EMI CSV has missing or duplicate column names")
    tp_fields = [name for name in fields if re.fullmatch(r"TP\d+", name)]
    if not tp_fields or any(not 1 <= int(name[2:]) <= 50 for name in tp_fields):
        raise RetrievalError("EMI CSV has invalid trading-period columns")
    rows: list[dict[str, object]] = []
    for item in reader:
        if None in item or any(value is None for value in item.values()):
            raise RetrievalError("EMI CSV row width differs from its header")
        if not all(item[name].strip() for name in required):
            raise RetrievalError("EMI row omitted plant, metadata or trading date")
        try:
            day = date.fromisoformat(item["Trading_Date"])
            start = pd.Timestamp(day, tz="Pacific/Auckland").tz_convert("UTC")
            stop = pd.Timestamp(day + timedelta(days=1), tz="Pacific/Auckland").tz_convert("UTC")
        except (ValueError, TypeError):
            raise RetrievalError("EMI row has an invalid trading date") from None
        periods = int((stop - start) / pd.Timedelta(minutes=30))
        if not all(f"TP{n}" in fields for n in range(1, periods + 1)):
            raise RetrievalError("EMI CSV omits a required trading-period column")
        for name in tp_fields:
            if int(name[2:]) > periods and item[name].strip():
                raise RetrievalError("EMI has a value outside this civil day's trading periods")
        if len(rows) + periods > maximum_rows:
            raise RetrievalError("EMI response exceeds maximum_rows")
        for period in range(1, periods + 1):
            raw = item[f"TP{period}"].strip()
            try:
                value = float(raw) if raw else float("nan")
            except ValueError:
                raise RetrievalError("EMI generation is not numeric") from None
            if raw and not math.isfinite(value):
                raise RetrievalError("EMI generation contains a non-finite value")
            stamp = start + pd.Timedelta(minutes=30 * (period - 1))
            rows.append(
                {
                    "timestamp": stamp,
                    "interval_end": stamp + pd.Timedelta(minutes=30),
                    "source": "emi",
                    "area": "NZ",
                    "plant_id": item["Gen_Code"],
                    "connection_id": item["POC_Code"],
                    "network_id": item["Nwk_Code"],
                    "technology": item["Tech_Code"],
                    "fuel": item["Fuel_Code"],
                    "value": value,
                    "unit": "kWh",
                    "aggregation": "plant_connection",
                    "source_date": day.isoformat(),
                    "trading_period": period,
                    "measurement_kind": "metered_injection_mapped_to_plant",
                }
            )
    frame = pd.DataFrame(rows, columns=_COLUMNS)
    for name in ("timestamp", "interval_end"):
        frame[name] = pd.to_datetime(frame[name], utc=True)
    if frame.duplicated(["timestamp", "plant_id", "connection_id", "network_id"]).any():
        raise RetrievalError("EMI has duplicate plant/connection interval observations")
    return frame.sort_values(["timestamp", "plant_id", "connection_id"]).reset_index(drop=True)


class EMIClient:
    """Read public monthly exports without credentials; retain each response hash."""

    def __init__(
        self, http: HTTPClient, *, maximum_requests: int = 24, maximum_rows: int = 2_000_000
    ) -> None:
        _limit(maximum_requests, "maximum_requests")
        _limit(maximum_rows, "maximum_rows")
        self.http, self.maximum_requests, self.maximum_rows = http, maximum_requests, maximum_rows

    def generation(
        self, start: date, end: date, *, plants: Sequence[str] | None = None
    ) -> GenerationResult:
        """Fetch inclusive New Zealand dates, optionally selecting plant codes."""
        urls = generation_urls(start, end, maximum_requests=self.maximum_requests)
        if plants is not None and (
            isinstance(plants, str)
            or not plants
            or any(not isinstance(p, str) or not p for p in plants)
        ):
            raise ValueError("plants must be a nonempty sequence of plant codes")
        frames, records = [], []
        total = 0
        for url in urls:
            if total >= self.maximum_rows:
                raise RetrievalError("EMI response exceeds maximum_rows")
            response = self.http.get_text(url)
            frame = parse_generation_csv(response.value, maximum_rows=self.maximum_rows - total)
            total += len(frame)
            frames.append(frame)
            records.append(response.record)
        frame = pd.concat(frames, ignore_index=True)
        frame = frame.loc[frame.source_date.between(start.isoformat(), end.isoformat())]
        if plants is not None:
            missing = set(plants) - set(frame.plant_id)
            if missing:
                raise RetrievalError("Requested EMI plant codes are absent from the interval")
            frame = frame.loc[frame.plant_id.isin(plants)]
        return GenerationResult(frame.reset_index(drop=True), tuple(records))
