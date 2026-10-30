"""NIST native CSV/TOA5 import, after download through the public PV portal."""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from itertools import islice
from pathlib import Path

import pandas as pd

from energy_data_retrieval.generation import GenerationResult
from energy_data_retrieval.sources._generation_utils import (
    bounded_csv,
    local_export,
    numeric,
    unique_observations,
    utc_labels,
)
from energy_data_retrieval.transport import RetrievalError

PORTAL_URL = "https://pvdata.nist.gov/"
REFERENCE_IDS = ("nist_pv_testbeds", "nist_pv_dictionary", "nist_pv_measurements_paper")


def parse_generation_csv(
    content: str | bytes,
    *,
    array: str,
    power_column: str = "InvPAC_kW_Avg",
    timestamp_column: str = "TIMESTAMP",
    source_timezone: str = "-05:00",
    resolution: str = "one-minute",
    maximum_rows: int = 1_000_000,
) -> pd.DataFrame:
    """Read an inverter/meter AC power channel from a NIST native export.

    NIST labels TIMESTAMP as local standard time (LST); Gaithersburg is fixed
    UTC-05:00. An explicit override supports exports that document another clock.
    One-minute averages and one-second samples remain distinct. Timestamp labels
    are retained without guessing which edge of the averaging interval they mark.
    """
    if array.lower() not in {"ground", "roof", "canopy"}:
        raise ValueError("array must be Ground, Roof, or Canopy")
    if not re.fullmatch(r"(?:InvPAC_kW|PwrMtrP_kW)(?:_Avg)?(?:\(\d+\))?", power_column):
        raise ValueError("Select an AC real-power channel InvPAC_kW or PwrMtrP_kW")
    if resolution not in {"one-minute", "one-second"}:
        raise ValueError("resolution must be one-minute or one-second")
    try:
        text = (
            content.decode("utf-8-sig") if isinstance(content, bytes) else content.lstrip("\ufeff")
        )
    except UnicodeDecodeError:
        raise RetrievalError("NIST export must be UTF-8 CSV") from None
    header_rows = list(islice(csv.reader(io.StringIO(text)), 4))
    toa5 = bool(header_rows and header_rows[0] and header_rows[0][0] == "TOA5")
    if resolution == "one-minute" and "_Avg" not in power_column and not toa5:
        raise ValueError("NIST one-minute exports use the _Avg channel suffix")
    if resolution == "one-second" and "_Avg" in power_column:
        raise ValueError("Use an instantaneous channel for one-second samples")
    if toa5:
        if len(header_rows) < 4 or power_column not in header_rows[1]:
            raise RetrievalError("Incomplete NIST TOA5 header or missing power channel")
        index = header_rows[1].index(power_column)
        if len(header_rows[2]) <= index or header_rows[2][index].lower() != "kw":
            raise RetrievalError("NIST TOA5 power channel must declare kW units")
        aggregation = "Avg" if resolution == "one-minute" else "Smp"
        if len(header_rows[3]) <= index or header_rows[3][index].lower() != aggregation.lower():
            raise RetrievalError(f"NIST {resolution} power must declare {aggregation} aggregation")
    frame = bounded_csv(text, maximum_rows=maximum_rows, skiprows=[0, 2, 3] if toa5 else None)
    if not {timestamp_column, power_column}.issubset(frame.columns):
        raise RetrievalError("NIST export lacks the selected timestamp or AC power channel")
    frame["timestamp"] = utc_labels(
        frame[timestamp_column], source_timezone=source_timezone, timestamp_format="ISO8601"
    )
    measurements = frame[power_column]
    frame["value"] = numeric(measurements.where(measurements.ne("NAN")), power_column)
    frame["unit"] = "kW"
    frame["source"] = "nist"
    frame["system_id"] = array.lower()
    frame["technology"] = "solar_pv"
    frame["channel"] = power_column
    frame["measurement_kind"] = (
        "interval_average_power" if resolution == "one-minute" else "instantaneous_power"
    )
    frame["sampling_seconds"] = 60 if resolution == "one-minute" else 1
    frame = unique_observations(frame, ["system_id", "timestamp", "channel"])
    frame.attrs.update(
        source_url=PORTAL_URL,
        source_timezone=source_timezone,
        resolution=resolution,
        timestamp_semantics="Native logger label; NIST dictionary specifies local standard time",
        units_basis="NIST InvPAC_kW/PwrMtrP_kW AC real-power dictionary, kW",
        reference_ids=list(REFERENCE_IDS),
    )
    return frame


@dataclass(frozen=True, slots=True)
class NISTClient:
    """Import a user-downloaded export; no account, portal token or form submission."""

    maximum_rows: int = 1_000_000

    def read_export(
        self,
        path: Path,
        *,
        array: str,
        power_column: str = "InvPAC_kW_Avg",
        timestamp_column: str = "TIMESTAMP",
        source_timezone: str = "-05:00",
        resolution: str = "one-minute",
    ) -> GenerationResult:
        """Normalize a downloaded CSV and record the exact input file's SHA-256."""
        content, provenance = local_export(path)
        frame = parse_generation_csv(
            content,
            array=array,
            power_column=power_column,
            timestamp_column=timestamp_column,
            source_timezone=source_timezone,
            resolution=resolution,
            maximum_rows=self.maximum_rows,
        )
        frame.attrs.update(provenance)
        return GenerationResult(frame, ())
