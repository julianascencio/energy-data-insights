"""TEPCO Tokyo-area actual/estimated generation mix, in half-hour average MW."""

from __future__ import annotations

import csv
import io
import math
import tempfile
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from energy_data_retrieval.generation import GenerationResult
from energy_data_retrieval.transport import HTTPClient, RetrievalError

TEPCO_HOSTS = frozenset({"www.tepco.co.jp"})
GENERATION_BASE = "https://www.tepco.co.jp/forecast/html/images"
REFERENCE_IDS = ("tepco_generation", "tepco_generation_definitions")
_SERIES = {
    "原子力": ("nuclear", "generation"),
    "火力(LNG)": ("lng", "generation"),
    "火力(石炭)": ("coal", "generation"),
    "火力(石油)": ("oil", "generation"),
    "火力(その他)": ("other_thermal", "generation"),
    "水力": ("hydro", "generation"),
    "地熱": ("geothermal", "generation"),
    "バイオマス": ("biomass", "generation"),
    "太陽光発電実績": ("solar", "generation"),
    "風力発電実績": ("wind", "generation"),
    "その他": ("other", "generation"),
    "太陽光出力制御量": ("solar", "curtailment"),
    "風力出力制御量": ("wind", "curtailment"),
    "揚水": ("pumped_storage", "storage_net"),
    "蓄電池": ("battery", "storage_net"),
    "連系線": ("interconnector", "net_import"),
}
_COLUMNS = [
    "timestamp",
    "interval_end",
    "source",
    "area",
    "technology",
    "value",
    "unit",
    "source_unit",
    "source_value",
    "source_series",
    "flow",
    "aggregation",
    "source_datetime",
    "may_include_estimates",
]


def generation_urls(start: date, end: date, *, maximum_requests: int = 24) -> tuple[str, ...]:
    """Plan the current TEPCO monthly export format (February 2024 onward)."""
    if type(maximum_requests) is not int or maximum_requests < 1:
        raise ValueError("maximum_requests must be a positive integer")
    if type(start) is not date or type(end) is not date or end < start:
        raise ValueError("start and end must be ordered calendar dates")
    if start < date(2024, 2, 1):
        raise ValueError("This TEPCO connector supports the February 2024 onward CSV format")
    count = (end.year - start.year) * 12 + end.month - start.month + 1
    if count > maximum_requests:
        raise ValueError("TEPCO interval exceeds maximum_requests")
    first = start.year * 12 + start.month - 1
    return tuple(
        f"{GENERATION_BASE}/eria_jukyu_{(first + n) // 12:04d}{(first + n) % 12 + 1:02d}_03.csv"
        for n in range(count)
    )


def parse_generation_csv(
    data: bytes | str, *, include_flows: bool = False, maximum_rows: int = 1_000_000
) -> pd.DataFrame:
    """Parse the declared CSV units, preserving half-hour average power.

    CSV starts with a physical-unit row and a Japanese header. Raw bytes may be
    CP932; no lossy replacement is used. MW averages are not interval MWh. Signed
    storage, net imports and curtailment are available only with include_flows;
    they retain explicit flow types. Demand and the supplied total are excluded.
    """
    if type(maximum_rows) is not int or maximum_rows < 1:
        raise ValueError("maximum_rows must be a positive integer")
    if isinstance(data, bytes):
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                text = data.decode("cp932")
            except UnicodeDecodeError:
                raise RetrievalError("TEPCO CSV is neither UTF-8 nor CP932") from None
    else:
        text = data.lstrip("\ufeff")
    lines = csv.reader(io.StringIO(text))
    units = next(lines, [])
    scales = {"単位[MW平均]": ("MW", 1.0), "単位[万kW平均]": ("10000kW", 10.0)}
    if not units or units[0].strip() not in scales:
        raise RetrievalError("TEPCO CSV omitted a supported average-power unit declaration")
    source_unit, scale = scales[units[0].strip()]
    header = next(lines, [])
    required = {"DATE", "TIME", "エリア需要", "合計", *_SERIES}
    if set(header) != required or len(header) != len(required):
        raise RetrievalError("TEPCO CSV has an unexpected generation-mix header")
    rows: list[dict[str, object]] = []
    seen: set[pd.Timestamp] = set()
    for values in lines:
        if not values:
            continue
        if len(values) != len(header):
            raise RetrievalError("TEPCO CSV row width differs from its header")
        item = dict(zip(header, values, strict=True))
        label = f"{item['DATE']} {item['TIME']}"
        try:
            parsed = datetime.strptime(label, "%Y/%m/%d %H:%M")
            if parsed.minute not in (0, 30):
                raise ValueError
            stamp = pd.Timestamp(parsed, tz="Asia/Tokyo").tz_convert("UTC")
        except (ValueError, TypeError):
            raise RetrievalError("TEPCO returned an invalid half-hour start label") from None
        if stamp in seen:
            raise RetrievalError("TEPCO returned duplicate half-hour observations")
        seen.add(stamp)
        for source_series, (technology, flow) in _SERIES.items():
            if flow != "generation" and not include_flows:
                continue
            raw = item[source_series].strip()
            try:
                value = float(raw) if raw not in ("", "-", "―") else float("nan")
            except ValueError:
                raise RetrievalError("TEPCO generation is not numeric") from None
            if raw not in ("", "-", "―") and not math.isfinite(value):
                raise RetrievalError("TEPCO generation contains a non-finite value")
            if len(rows) >= maximum_rows:
                raise RetrievalError("TEPCO response exceeds maximum_rows")
            rows.append(
                {
                    "timestamp": stamp,
                    "interval_end": stamp + pd.Timedelta(minutes=30),
                    "source": "tepco",
                    "area": "JP-Tokyo",
                    "technology": technology,
                    "value": value * scale,
                    "unit": "MW",
                    "source_unit": source_unit,
                    "source_value": value,
                    "source_series": source_series,
                    "flow": flow,
                    "aggregation": "area_technology",
                    "source_datetime": label,
                    "may_include_estimates": True,
                }
            )
    frame = pd.DataFrame(rows, columns=_COLUMNS)
    for name in ("timestamp", "interval_end"):
        frame[name] = pd.to_datetime(frame[name], utc=True)
    return frame.sort_values(["timestamp", "flow", "technology"]).reset_index(drop=True)


class TEPCOClient:
    """Download bounded monthly native-encoding CSV files with byte provenance."""

    def __init__(
        self, http: HTTPClient, *, maximum_requests: int = 24, maximum_rows: int = 1_000_000
    ) -> None:
        if type(maximum_requests) is not int or maximum_requests < 1:
            raise ValueError("maximum_requests must be a positive integer")
        if type(maximum_rows) is not int or maximum_rows < 1:
            raise ValueError("maximum_rows must be a positive integer")
        self.http, self.maximum_requests, self.maximum_rows = http, maximum_requests, maximum_rows

    def generation(
        self, start: date, end: date, *, include_flows: bool = False
    ) -> GenerationResult:
        """Fetch inclusive Japanese calendar dates; timestamps are interval starts."""
        urls = generation_urls(start, end, maximum_requests=self.maximum_requests)
        frames, records = [], []
        total = 0
        with tempfile.TemporaryDirectory(prefix="tepco-generation-") as folder:
            for index, url in enumerate(urls):
                if total >= self.maximum_rows:
                    raise RetrievalError("TEPCO response exceeds maximum_rows")
                target = Path(folder) / f"{index}.csv"
                record = self.http.download_file(url, target)
                frame = parse_generation_csv(
                    target.read_bytes(),
                    include_flows=include_flows,
                    maximum_rows=self.maximum_rows - total,
                )
                total += len(frame)
                frames.append(frame)
                records.append(record)
        frame = pd.concat(frames, ignore_index=True)
        lower = pd.Timestamp(start, tz="Asia/Tokyo").tz_convert("UTC")
        upper = pd.Timestamp(end, tz="Asia/Tokyo").tz_convert("UTC") + pd.Timedelta(days=1)
        frame = frame.loc[(frame.timestamp >= lower) & (frame.timestamp < upper)]
        return GenerationResult(frame.reset_index(drop=True), tuple(records))
