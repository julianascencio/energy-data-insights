"""DKASC five-minute AC power CSV import with provider-specific data terms."""

from __future__ import annotations

from dataclasses import dataclass
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

PORTAL_URL = "https://dkasolarcentre.com.au/download?location=alice-springs"
TERMS_URL = "https://dkasolarcentre.com.au/download/terms-conditions"
REFERENCE_IDS = ("dkasc_download", "dkasc_data_parameters", "dkasc_data_terms")


def parse_generation_csv(
    content: str | bytes,
    *,
    system_id: str,
    timestamp_column: str,
    timestamp_format: str,
    power_column: str,
    maximum_rows: int = 1_000_000,
) -> pd.DataFrame:
    """Read one documented five-minute average AC power channel, in native kW.

    Select its exact exported column (which may contain the array name) and date
    format explicitly. Local civil time in Alice Springs is Australia/Darwin,
    UTC+09:30 throughout the year. Cumulative kWh registers are not power channels.
    """
    if not isinstance(system_id, str) or not system_id.strip():
        raise ValueError("system_id must identify the downloaded PV array")
    if not timestamp_column or not timestamp_format or not power_column:
        raise ValueError("Select exact timestamp/power columns and an explicit timestamp_format")
    suffix = power_column.rsplit(" - ", maxsplit=1)[-1]
    if suffix not in {
        "5-Min-Avg kW",
        "5-Min-Avg kWtot",
        "5-Min-Avg kWa",
        "5-Min-Avg kWb",
        "5-Min-Avg kWc",
    }:
        raise ValueError(
            "Choose a documented 5-Min-Avg kW power channel, not a cumulative kWh meter"
        )
    frame = bounded_csv(content, maximum_rows=maximum_rows)
    if not {timestamp_column, power_column}.issubset(frame.columns):
        raise RetrievalError("DKASC export lacks the selected timestamp or power column")
    frame["timestamp"] = utc_labels(
        frame[timestamp_column],
        source_timezone="Australia/Darwin",
        timestamp_format=timestamp_format,
    )
    frame["value"] = numeric(frame[power_column], power_column)
    frame["unit"] = "kW"
    frame["source"] = "dkasc"
    frame["system_id"] = system_id
    frame["technology"] = "solar_pv"
    frame["channel"] = power_column
    frame["measurement_kind"] = "interval_average_power"
    frame["interval_minutes"] = 5
    frame = unique_observations(frame, ["system_id", "timestamp", "channel"])
    frame.attrs.update(
        source_url=PORTAL_URL,
        terms_url=TERMS_URL,
        source_timezone="Australia/Darwin",
        timestamp_semantics="Native five-minute label; interval alignment not inferred",
        scope="Selected PV array and meter/phase channel, not total Australian generation",
        units_basis="DKASC glossary: 5-Min-Avg kW is average AC power in kW",
        reference_ids=list(REFERENCE_IDS),
    )
    return frame


@dataclass(frozen=True, slots=True)
class DKASCClient:
    """Use the provider's download form, then import the export locally.

    The form requires identifying details and acceptance of data terms. The
    connector does not fabricate those details or bypass that download workflow.
    """

    maximum_rows: int = 1_000_000

    def read_export(
        self,
        path: Path,
        *,
        system_id: str,
        timestamp_column: str,
        timestamp_format: str,
        power_column: str,
    ) -> GenerationResult:
        """Normalize an existing CSV and record its exact input SHA-256."""
        content, provenance = local_export(path)
        frame = parse_generation_csv(
            content,
            system_id=system_id,
            timestamp_column=timestamp_column,
            timestamp_format=timestamp_format,
            power_column=power_column,
            maximum_rows=self.maximum_rows,
        )
        frame.attrs.update(provenance)
        return GenerationResult(frame, ())
