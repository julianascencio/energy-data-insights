"""ADME raw SCADA: measured generation and dispatch limits remain distinct."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from html.parser import HTMLParser

import pandas as pd

from energy_data_retrieval.generation import GenerationResult
from energy_data_retrieval.transport import HTTPClient, RequestRecord, RetrievalError

ADME_HOSTS = frozenset({"pronos.adme.com.uy"})
SCADA_ROOT = "https://pronos.adme.com.uy/svg/pronos/cache_series_scada/"
REFERENCE_IDS = ("adme_open_data", "adme_scada_archive")
_FILE = re.compile(r"scada_central_(\d+)_(\d{10})\.sas")


def _limit(value: int, name: str, upper: int) -> None:
    if type(value) is not int or not 1 <= value <= upper:
        raise ValueError(f"{name} must be an integer in 1..{upper}")


def parse_scada_sas(
    payload: str,
    *,
    central_id: int,
    power_series: str | None = None,
    source_timezone: str = "America/Montevideo",
    maximum_rows: int = 100_000,
) -> pd.DataFrame:
    """Read ADME's tab-separated native six-line-header SAS time series.

    The source's Excel/LibreOffice serial date is treated as a local clock
    label, converted to UTC without interval shifting. A fixed-offset override
    may be supplied for exports with a different clock convention. Ambiguous or
    nonexistent local times fail. Values below -10000 are ADME missing sentinels.
    Only the actual ``GETOTMEDP.AV`` channel is selected automatically; dispatch
    limits (``CONSIGNAP``) and forecasts cannot become measured generation.
    """
    _limit(central_id, "central_id", 1_000_000)
    _limit(maximum_rows, "maximum_rows", 1_000_000)
    lines = payload.splitlines()
    if len(lines) < 7 or "<html" in payload[:200].lower() or "<?php" in payload[:200].lower():
        raise RetrievalError("ADME response is not a native SCADA SAS file")
    try:
        count = int(lines[0].split("\t")[0])
        fields = lines[1].split("\t")[:6]
        year, month, day, hour, minute, second = (int(x) for x in fields)
        first = datetime(year, month, day, hour, minute, second)
        period_hours = float(lines[2].split("\t")[0])
        samples = int(lines[3].split("\t")[0])
        int(lines[4].split("\t")[0])
    except (ValueError, TypeError):
        raise RetrievalError("ADME SAS has an invalid native header") from None
    if not 1 <= count <= 1000 or not 1 <= samples <= maximum_rows:
        raise RetrievalError("ADME SAS series/sample count is invalid or exceeds maximum_rows")
    if not math.isfinite(period_hours) or not 0 < period_hours <= 24:
        raise RetrievalError("ADME SAS has an invalid sampling period")
    seconds = round(period_hours * 3600)
    if seconds < 1 or abs(period_hours * 3600 - seconds) > 0.01:
        raise RetrievalError("ADME SAS sampling period must resolve to whole seconds")
    labels = lines[5].split("\t")
    if len(labels) != count + 1 or labels[0].strip():
        raise RetrievalError("ADME SAS names do not match the declared series count")
    names = [name.strip() for name in labels[1:]]
    if len([x for x in names if x]) != len(set(x for x in names if x)):
        raise RetrievalError("ADME SAS contains duplicate named series")
    actual = [name for name in names if name.endswith("GETOTMEDP.AV")]
    if power_series is None:
        if len(actual) != 1:
            raise RetrievalError(
                "ADME actual power channel is ambiguous; supply its documented power_series"
            )
        power_series = actual[0]
    if power_series not in actual:
        raise RetrievalError(
            "ADME power_series must identify a GETOTMEDP.AV power channel, not a limit/forecast"
        )
    data_lines = [line for line in lines[6:] if line.strip()]
    if len(data_lines) != samples:
        raise RetrievalError("ADME SAS sample count does not match its native header")
    rows: list[list[float]] = []
    for line in data_lines:
        values = line.split("\t")
        if len(values) != count + 1:
            raise RetrievalError("ADME SAS row has an unexpected number of columns")
        try:
            row = [float(value) for value in values]
        except ValueError:
            raise RetrievalError("ADME SAS observations must be numeric") from None
        if not all(math.isfinite(value) for value in row):
            raise RetrievalError(
                "ADME SAS observations must be finite or use the documented missing sentinel"
            )
        rows.append(row)
    native_names = [name or f"unnamed_series_{i + 1}" for i, name in enumerate(names)]
    frame = pd.DataFrame(rows, columns=["source_serial_datetime", *native_names])
    try:
        local = pd.to_datetime(
            frame["source_serial_datetime"], unit="D", origin="1899-12-30"
        ).dt.round("s")
        if local.iloc[0] != first:
            raise ValueError("Header start does not match data")
        expected = pd.date_range(first, periods=samples, freq=pd.Timedelta(seconds=seconds))
        if not local.eq(pd.Series(expected, index=local.index)).all():
            raise ValueError("Irregular source clock labels")
        frame["timestamp"] = local.dt.tz_localize(
            source_timezone, ambiguous="raise", nonexistent="raise"
        ).dt.tz_convert("UTC")
    except Exception as exc:
        raise RetrievalError(
            "ADME SAS has invalid, irregular or ambiguous source clock labels"
        ) from exc
    for column in native_names:
        frame[column] = frame[column].mask(frame[column] < -10000)
    frame["source_datetime"] = local
    frame["source"] = "adme"
    frame["area"] = "Uruguay"
    frame["unit_id"] = str(central_id)
    frame["value"] = frame[power_series]
    frame["unit"] = "MW"
    frame["power_series"] = power_series
    frame["sampling_seconds"] = seconds
    frame["aggregation"] = "sampled_scada"
    frame["quality"] = frame["value"].map(
        lambda value: "missing" if pd.isna(value) else "operational_scada"
    )
    limits = [name for name in names if name.endswith("CONSIGNAP.AV")]
    if len(limits) == 1:
        frame["dispatch_limit_mw"] = frame[limits[0]]
        frame["dispatch_limit_series"] = limits[0]
    if frame.duplicated(["unit_id", "timestamp"]).any():
        raise RetrievalError("ADME SAS contains duplicate unit/time observations")
    frame.attrs.update(
        source_timezone=source_timezone,
        source_start=first.isoformat(),
        source_series=names,
        reference_ids=list(REFERENCE_IDS),
        timestamp_semantics=(
            "Native local SCADA sample label converted to UTC; interval boundaries are not inferred"
        ),
        missing_policy=(
            "Source values below -10000 are missing; other negatives and zero are retained"
        ),
        dispatch_limits="CONSIGNAP is a control limit, not generation or measured lost energy",
    )
    return frame


class _Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.files: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if isinstance(href, str) and _FILE.fullmatch(href):
            self.files.add(href)


@dataclass(slots=True)
class ADMEClient:
    """Discover official SCADA archive files, with one six-day chunk per file."""

    http: HTTPClient
    maximum_requests: int = 32
    maximum_rows: int = 100_000

    def __post_init__(self) -> None:
        _limit(self.maximum_requests, "maximum_requests", 1000)
        _limit(self.maximum_rows, "maximum_rows", 1_000_000)

    def generation(
        self,
        start: date,
        end: date,
        *,
        central_id: int,
        power_series: str | None = None,
        source_timezone: str = "America/Montevideo",
    ) -> GenerationResult:
        """Retrieve inclusive local dates for one plant from raw measured SCADA.

        The archive exposes rolling seven-day files. The latest file starting
        before each requested six-day chunk is selected, and actual file coverage
        is checked. Archive gaps fail explicitly; no forecast archive is used.
        """
        _limit(central_id, "central_id", 1_000_000)
        if (
            type(start) is not date
            or type(end) is not date
            or not date(2016, 1, 2) <= start <= end < date(9999, 1, 1)
        ):
            raise ValueError("ADME requires ordered inclusive dates from 2016-01-02")
        chunks = math.ceil(((end - start).days + 1) / 6)
        if chunks + 1 > self.maximum_requests:
            raise ValueError("ADME date range exceeds maximum_requests including archive discovery")
        listing = self.http.get_text(SCADA_ROOT)
        parser = _Links()
        parser.feed(listing.value)
        candidates: list[tuple[datetime, str]] = []
        for filename in parser.files:
            match = _FILE.fullmatch(filename)
            if match is None or int(match[1]) != central_id:
                continue
            try:
                stamp = datetime.strptime(match[2], "%Y%m%d%H")
            except ValueError:
                continue
            candidates.append((stamp, filename))
        records: list[RequestRecord] = [listing.record]
        frames: list[pd.DataFrame] = []
        total = 0
        for offset in range(chunks):
            chunk_start = start + timedelta(days=offset * 6)
            chunk_end = min(end, chunk_start + timedelta(days=5))
            origin = datetime.combine(chunk_start, datetime.min.time())
            eligible = [
                item for item in candidates if origin - timedelta(days=1) <= item[0] <= origin
            ]
            if not eligible:
                raise RetrievalError(
                    "ADME has no SCADA archive file covering the requested plant/date"
                )
            stamp, filename = max(eligible)
            response = self.http.get_text(SCADA_ROOT + filename)
            frame = parse_scada_sas(
                response.value,
                central_id=central_id,
                power_series=power_series,
                source_timezone=source_timezone,
                maximum_rows=self.maximum_rows,
            )
            if frame.attrs["source_start"] != stamp.isoformat():
                raise RetrievalError("ADME file start differs from its discovered filename")
            exclusive_end = datetime.combine(chunk_end + timedelta(days=1), datetime.min.time())
            step = timedelta(seconds=int(frame["sampling_seconds"].iloc[0]))
            if (
                frame["source_datetime"].min() > origin
                or frame["source_datetime"].max() + step < exclusive_end
            ):
                raise RetrievalError("ADME archive file does not cover all requested local dates")
            selected = frame.loc[
                frame["source_datetime"].between(origin, exclusive_end, inclusive="left")
            ].reset_index(drop=True)
            total += len(frame)
            if total > self.maximum_rows:
                raise RetrievalError("ADME query exceeds maximum_rows")
            frames.append(selected)
            records.append(response.record)
        result = pd.concat(frames, ignore_index=True)
        result.attrs.update(frames[0].attrs)
        if result.duplicated(["unit_id", "timestamp"]).any():
            raise RetrievalError("ADME archive produced overlapping observations")
        return GenerationResult(result, tuple(records))
