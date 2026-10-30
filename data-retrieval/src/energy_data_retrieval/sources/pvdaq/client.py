"""Bounded daily CSV reads from PVDAQ's public, anonymous OEDI S3 archive."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import pyarrow.parquet as pq

from energy_data_retrieval.generation import GenerationResult
from energy_data_retrieval.sources._generation_utils import (
    bounded_csv,
    numeric,
    unique_observations,
    utc_labels,
)
from energy_data_retrieval.transport import HTTPClient, JSONResponse, RetrievalError

PVDAQ_HOSTS = frozenset({"oedi-data-lake.s3.amazonaws.com"})
BASE_URL = "https://oedi-data-lake.s3.amazonaws.com/pvdaq"
REFERENCE_IDS = ("pvdaq_public_archive", "pvdaq_data_dictionary")


def _system_id(value: int) -> int:
    if type(value) is not int or not 1 <= value <= 10_000_000:
        raise ValueError("system_id must be a positive integer")
    return value


def daily_url(system_id: int, day: date) -> str:
    """Return the provider's partitioned daily CSV path (source calendar date)."""
    _system_id(system_id)
    if type(day) is not date:
        raise ValueError("day must be a date")
    return (
        f"{BASE_URL}/csv/pvdata/system_id={system_id}/year={day.year}/"
        f"month={day.month}/day={day.day}/system_{system_id}__date_{day:%Y_%m_%d}.csv"
    )


def parse_generation_csv(
    content: str | bytes,
    *,
    system_id: int,
    power_column: str,
    unit: str,
    source_timezone: str,
    maximum_rows: int = 1_000_000,
) -> pd.DataFrame:
    """Select one measured power channel, retaining every native CSV column.

    Units and local-clock convention must be selected from the system/channel
    documentation. CSV exports do not contain these fields, and catalogue offset
    numbers are not guessed. Values are unchanged; no calibration is reapplied.
    """
    _system_id(system_id)
    if unit not in {"W", "kW", "MW"}:
        raise ValueError("Select a power channel with unit W, kW, or MW")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*__\d+", power_column):
        raise ValueError("Use an exact PVDAQ channel name, such as ac_power__315")
    if not source_timezone:
        raise ValueError("source_timezone must explicitly describe the source clock")
    frame = bounded_csv(content, maximum_rows=maximum_rows)
    if not {"measured_on", "system_id", power_column}.issubset(frame.columns):
        raise RetrievalError("PVDAQ CSV lacks the selected system, time, or power column")
    ids = numeric(frame["system_id"], "system_id")
    if ids.isna().any() or not ids.eq(system_id).all():
        raise RetrievalError("PVDAQ CSV contains a different or missing system_id")
    frame["timestamp"] = utc_labels(
        frame["measured_on"], source_timezone=source_timezone, timestamp_format="ISO8601"
    )
    frame["source"] = "pvdaq"
    frame["technology"] = "solar_pv"
    frame["channel"] = power_column
    frame["value"] = numeric(frame[power_column], power_column)
    frame["unit"] = unit
    frame["measurement_kind"] = "measured_power_channel"
    frame = unique_observations(frame, ["system_id", "timestamp", "channel"])
    frame.attrs.update(
        source_timezone=source_timezone,
        timestamp_semantics="Provider measured_on label; interval alignment not inferred",
        units_basis="Explicit selection from provider channel metadata; original values retained",
        power_column=power_column,
        reference_ids=list(REFERENCE_IDS),
    )
    return frame


@dataclass(frozen=True, slots=True)
class PVDAQClient:
    """Download selected daily files, never an unbounded archive or bulk bucket."""

    http: HTTPClient
    maximum_requests: int = 31
    maximum_rows: int = 1_000_000

    def __post_init__(self) -> None:
        if type(self.maximum_rows) is not int or not 1 <= self.maximum_rows <= 10_000_000:
            raise ValueError("maximum_rows must be an integer in 1..10,000,000")

    def system_metadata(self, system_id: int) -> JSONResponse:
        """Read public system/site/module metadata with request provenance."""
        _system_id(system_id)
        return self.http.get_json(
            f"{BASE_URL}/csv/system_metadata/{system_id}_system_metadata.json"
        )

    def metrics(self, system_id: int) -> GenerationResult:
        """Read channel names, units, scaling and aggregation metadata for a system.

        This is metadata, not generation. The provider's current per-system
        metadata partition is a small Parquet file; the HTTP byte limit applies.
        """
        _system_id(system_id)
        url = f"{BASE_URL}/parquet/metrics/metrics__system_{system_id}__part000.parquet"
        with TemporaryDirectory(prefix="pvdaq-metrics-") as directory:
            path = Path(directory) / "metrics.parquet"
            response = self.http.download_file(url, path)
            try:
                with pq.ParquetFile(path) as parquet:
                    if parquet.metadata.num_rows > self.maximum_rows:
                        raise RetrievalError("PVDAQ metadata exceeds maximum_rows")
                frame = pd.read_parquet(path)
            except (ValueError, OSError):
                raise RetrievalError("Invalid PVDAQ channel metadata Parquet") from None
        required = {"system_id", "standard_name", "units", "aggregation_type"}
        if not required.issubset(frame.columns) or not frame.system_id.eq(system_id).all():
            raise RetrievalError("Unexpected PVDAQ channel metadata schema or system")
        if len(frame) > self.maximum_rows:
            raise RetrievalError("PVDAQ metadata exceeds maximum_rows")
        frame.attrs.update(
            source="pvdaq", product="channel_metadata", reference_ids=list(REFERENCE_IDS)
        )
        return GenerationResult(frame, (response,))

    def generation(
        self,
        system_id: int,
        start: date,
        end: date,
        *,
        power_column: str,
        unit: str,
        source_timezone: str,
    ) -> GenerationResult:
        """Fetch inclusive source dates with explicit channel/clock semantics.

        Some catalogue date ranges contain gaps. Missing files raise the normal
        retrieval error rather than creating zeros or quietly returning a partial
        request. A new output path can preserve a later provider revision.
        """
        _system_id(system_id)
        if type(start) is not date or type(end) is not date or start > end:
            raise ValueError("Use inclusive dates with start <= end")
        days = (end - start).days + 1
        if type(self.maximum_requests) is not int or not 1 <= self.maximum_requests <= 366:
            raise ValueError("maximum_requests must be in 1..366")
        if days > self.maximum_requests:
            raise ValueError("Date range exceeds maximum_requests; request smaller snapshots")
        frames, records = [], []
        rows = 0
        for offset in range(days):
            day = start + timedelta(days=offset)
            response = self.http.get_text(daily_url(system_id, day))
            frame = parse_generation_csv(
                response.value,
                system_id=system_id,
                power_column=power_column,
                unit=unit,
                source_timezone=source_timezone,
                maximum_rows=self.maximum_rows,
            )
            # Keep each original calendar date, including explicit offsets on
            # either side of a clock change; UTC dates can differ near midnight.
            source_dates = frame["measured_on"].map(lambda value: pd.Timestamp(value).date())
            if not source_dates.eq(day).all():
                raise RetrievalError("PVDAQ file contains measurements outside its requested date")
            rows += len(frame)
            if rows > self.maximum_rows:
                raise RetrievalError("PVDAQ request exceeds maximum_rows")
            frames.append(frame)
            records.append(response.record)
        result = unique_observations(pd.concat(frames, ignore_index=True), ["timestamp", "channel"])
        result.attrs.update(requested_start=start.isoformat(), requested_end=end.isoformat())
        return GenerationResult(result, tuple(records))
