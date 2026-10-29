"""Measured hourly station data with explicit units, identity and interval labels."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd

from energy_data_retrieval.storage import (
    Artifact,
    existing_artifact,
    fingerprint,
    sha256_file,
    write_parquet,
)
from energy_data_retrieval.tabular import (
    identity_mapping,
    numeric_values,
    read_export,
    utc_intervals,
)
from energy_data_retrieval.transport import JSONValue


@dataclass(frozen=True, slots=True)
class StationSchema:
    station_column: str
    timestamp_column: str
    timezone: str
    timestamp_label: str
    ghi_column: str
    ghi_unit: str
    temperature_column: str | None = None
    temperature_unit: str = "degC"
    wind_speed_column: str | None = None
    wind_speed_unit: str = "m/s"
    gust_column: str | None = None
    gust_unit: str = "m/s"
    gust_statistic: str = "hourly_maximum"
    sampling: str = "hourly_mean"
    irradiance_kind: str = "GHI"
    decimal_separator: str = "."
    source_label: str = "measured-station"
    sheet: str | None = None
    skiprows: int = 0
    delimiter: str = ","

    def __post_init__(self) -> None:
        if self.sampling != "hourly_mean":
            raise ValueError("Station observations require hourly means; resample explicitly first")
        if self.irradiance_kind != "GHI":
            raise ValueError("POA or unknown irradiance cannot be relabeled as GHI")
        if self.ghi_unit not in {"W/m2", "kW/m2", "Wh/m2", "kWh/m2"}:
            raise ValueError("Unsupported hourly GHI unit")
        if self.temperature_unit not in {"degC", "K", "degF"}:
            raise ValueError("Temperature unit must be degC, K, or degF")
        if self.wind_speed_unit not in {"m/s", "km/h"} or self.gust_unit not in {"m/s", "km/h"}:
            raise ValueError("Wind and gust units must be m/s or km/h")
        if self.gust_statistic not in {"hourly_maximum", "instantaneous_end"}:
            raise ValueError("Declare the measured gust statistic explicitly")
        if not self.source_label.strip():
            raise ValueError("Station source label must be nonempty")


def normalize_station(
    frame: pd.DataFrame, mapping: pd.DataFrame, schema: StationSchema
) -> pd.DataFrame:
    """Produce hourly weather without interpolation or inferred station suitability.

    A station may serve several explicitly mapped sites, but each site may use
    only one station within this import. No nearest-station selection is guessed.
    Missing optional observations stay null, and negatives are retained for QA.
    """
    columns = {
        schema.station_column,
        schema.timestamp_column,
        schema.ghi_column,
        *[
            value
            for value in (schema.temperature_column, schema.wind_speed_column, schema.gust_column)
            if value is not None
        ],
    }
    if not columns.issubset(frame.columns):
        raise ValueError(f"Station export is missing columns: {sorted(columns - set(frame))}")
    if frame.empty:
        raise ValueError("Station export has no observations")
    if (
        not {"station_id", "site_id"}.issubset(mapping.columns)
        or mapping.empty
        or mapping["site_id"].duplicated().any()
        or mapping[["station_id", "site_id"]].isna().any().any()
    ):
        raise ValueError("Station mapping requires exactly one station_id per site_id")
    stations = frame[schema.station_column].astype(str)
    if set(stations) - set(mapping["station_id"]):
        raise ValueError("Station observations contain unmapped station identities")
    out = pd.DataFrame(
        {
            "station_id": stations,
            "timestamp": utc_intervals(
                frame[schema.timestamp_column],
                timezone=schema.timezone,
                label=schema.timestamp_label,
            ),
        }
    )

    def values(column: str | None) -> pd.Series:
        if column is None:
            return pd.Series(np.nan, index=frame.index, dtype="float64")
        return numeric_values(frame[column], decimal=schema.decimal_separator)

    out["ghi_wm2"] = values(schema.ghi_column) * (1000 if schema.ghi_unit.startswith("k") else 1)
    temperature = values(schema.temperature_column)
    if schema.temperature_unit == "K":
        temperature -= 273.15
    elif schema.temperature_unit == "degF":
        temperature = (temperature - 32) * 5 / 9
    out["temperature_c"] = temperature
    out["wind_speed_ms"] = values(schema.wind_speed_column) / (
        3.6 if schema.wind_speed_unit == "km/h" else 1
    )
    out["gust_ms"] = values(schema.gust_column) / (3.6 if schema.gust_unit == "km/h" else 1)
    keys = ["station_id", "timestamp"]
    weather = ["ghi_wm2", "temperature_c", "wind_speed_ms", "gust_ms"]
    if (out.groupby(keys)[weather].nunique(dropna=False) > 1).any().any():
        raise ValueError("Conflicting station-hour measurements require explicit reconciliation")
    duplicates = int(out.duplicated(keys).sum())
    out = out.drop_duplicates(keys).merge(
        mapping, how="left", on="station_id", validate="many_to_many"
    )
    out["duration_hours"] = 1.0
    out["weather_source"] = schema.source_label
    out = out.sort_values(["site_id", "timestamp"]).reset_index(drop=True)
    out.attrs.update(
        source=schema.source_label,
        station_observations=True,
        sensor_quality_confirmed=False,
        spatial_representativeness_confirmed=False,
        schema=asdict(schema),
        timestamp_convention="UTC interval start; one elapsed hour",
        duplicate_equal_rows_removed=duplicates,
        missing_rule="no interpolation, modeled replacement, or forward filling",
        units={
            "ghi_wm2": "W/m2",
            "temperature_c": "degC",
            "wind_speed_ms": "m/s",
            "gust_ms": "m/s",
        },
    )
    return out


def import_station(
    path: Path,
    mapping_path: Path,
    output: Path,
    schema: StationSchema,
    *,
    member: str | None = None,
) -> Artifact:
    source_hash = sha256_file(path)
    mapping_hash = sha256_file(mapping_path)
    request = cast(
        dict[str, JSONValue],
        {
            "source": schema.source_label,
            "source_filename": path.name,
            "source_sha256": source_hash,
            "mapping_filename": mapping_path.name,
            "mapping_sha256": mapping_hash,
            "zip_member": member,
            "schema": asdict(schema),
        },
    )
    previous = existing_artifact(output, fingerprint(request))
    if previous is not None:
        return previous
    frame = read_export(
        path,
        member=member,
        sheet=schema.sheet,
        skiprows=schema.skiprows,
        delimiter=schema.delimiter,
    )
    mapping = identity_mapping(mapping_path, ("station_id", "site_id"))
    normalized = normalize_station(frame, mapping, schema)
    if source_hash != sha256_file(path) or mapping_hash != sha256_file(mapping_path):
        raise ValueError("Source or station mapping changed during import")
    return write_parquet(
        normalized,
        output,
        request=request,
        provenance=cast(dict[str, JSONValue], normalized.attrs),
    )
