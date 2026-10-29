"""Explicit historical bulk and preserved Qlik exports of CEN hourly generation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd

from energy_data_retrieval.sources.cen.client import aggregate_units
from energy_data_retrieval.storage import (
    Artifact,
    existing_artifact,
    fingerprint,
    sha256_file,
    write_parquet,
)
from energy_data_retrieval.tabular import (
    MAX_EXPORT_ROWS,
    identity_mapping,
    numeric_values,
    read_export,
    utc_intervals,
)
from energy_data_retrieval.transport import JSONValue

# User supplies the observed public download URL. There is no invented bulk API.
CEN_EXPORT_HOSTS = frozenset({"www.coordinador.cl", "coordinador.cl", "sic.coordinador.cl"})


@dataclass(frozen=True, slots=True)
class HistorySchema:
    """A source-specific contract; hourly and daily products cannot be conflated.

    Use timestamp_column, or date_column with hour_column/hour_columns. Hour origin
    1 means labels 1..24; origin 0 means 0..23. ``timestamp_label`` independently
    states whether each resulting civil-clock label begins or ends its interval.
    """

    identity_column: str
    value_column: str
    timezone: str
    timestamp_label: str
    energy_unit: str
    timestamp_column: str | None = None
    date_column: str | None = None
    hour_column: str | None = None
    hour_columns: tuple[str, ...] = ()
    hour_origin: int = 1
    date_format: str = "%Y-%m-%d"
    source: str = "cen-bulk"
    measurement_basis: str = "unspecified"
    decimal_places: int | None = None
    temporal_resolution: str = "hourly"
    decimal_separator: str = "."
    sheet: str | None = None
    skiprows: int = 0
    delimiter: str = ","
    technology_column: str | None = None
    pv_technology_values: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.source not in {"cen-bulk", "cen-qlik"}:
            raise ValueError("Historical source must be cen-bulk or cen-qlik")
        if self.temporal_resolution != "hourly":
            raise ValueError("Daily CEN records must stay separate; hourly values are not invented")
        if self.energy_unit not in {"MW", "MWh", "kW", "kWh"}:
            raise ValueError("Declare MW, MWh, kW, or kWh for one-hour intervals")
        if self.measurement_basis not in {"gross", "net", "unspecified"}:
            raise ValueError("Generation measurement basis must be gross, net or unspecified")
        if self.decimal_places is not None and not 0 <= self.decimal_places <= 12:
            raise ValueError("Declared source precision must be between 0 and 12 decimal places")
        if self.hour_origin not in {0, 1}:
            raise ValueError("Hour origin must be 0 or 1")
        if self.timestamp_column:
            if self.date_column or self.hour_column or self.hour_columns:
                raise ValueError("Choose timestamp labels or date/hour labels, not both")
        elif not self.date_column or bool(self.hour_column) == bool(self.hour_columns):
            raise ValueError("Date/hour input needs a date column and exactly one hour layout")
        if self.hour_columns and (
            len(self.hour_columns) != 24 or len(set(self.hour_columns)) != 24
        ):
            raise ValueError("Wide hourly input requires 24 unique columns in chronological order")
        if self.technology_column and not self.pv_technology_values:
            raise ValueError("Technology filtering requires explicit photovoltaic source labels")


def _hourly_table(frame: pd.DataFrame, schema: HistorySchema) -> pd.DataFrame:
    required = {schema.identity_column}
    if schema.timestamp_column:
        required.update({schema.timestamp_column, schema.value_column})
    else:
        required.add(str(schema.date_column))
        required.update(schema.hour_columns or (str(schema.hour_column), schema.value_column))
    if schema.technology_column:
        required.add(schema.technology_column)
    if not required.issubset(frame.columns):
        raise ValueError(f"Historical export is missing columns: {sorted(required - set(frame))}")
    if schema.technology_column:
        frame = frame.loc[
            frame[schema.technology_column].astype(str).isin(schema.pv_technology_values)
        ].copy()
    if frame.empty:
        raise ValueError("Historical export has no selected hourly records")
    if schema.hour_columns:
        if len(frame) * 24 > MAX_EXPORT_ROWS:
            raise ValueError("Reshaped hourly export exceeds the configured row limit")
        frame = frame.melt(
            id_vars=[schema.identity_column, str(schema.date_column)],
            value_vars=list(schema.hour_columns),
            var_name="_source_hour_column",
            value_name=schema.value_column,
        )
        hour_numbers = {
            name: index + schema.hour_origin for index, name in enumerate(schema.hour_columns)
        }
        frame["_source_hour"] = frame["_source_hour_column"].map(hour_numbers)
    else:
        frame = frame.copy()
    if schema.timestamp_column:
        frame["_source_timestamp"] = frame[schema.timestamp_column].astype(str)
    else:
        dates = pd.to_datetime(
            frame[str(schema.date_column)], format=schema.date_format, errors="raise"
        )
        if dates.isna().any() or not (dates == dates.dt.normalize()).all():
            raise ValueError("Date/hour exports require date-only civil labels")
        hours = numeric_values(
            frame["_source_hour" if schema.hour_columns else str(schema.hour_column)]
        )
        if (
            hours.isna().any()
            or (hours != np.floor(hours)).any()
            or not hours.between(schema.hour_origin, schema.hour_origin + 23).all()
        ):
            raise ValueError("Source hour labels do not match the declared 24-hour numbering")
        # The first numbered interval spans civil 00:00-01:00. Its end label is
        # 01:00, and the final interval ends at next-day 00:00.
        offsets = hours - schema.hour_origin + int(schema.timestamp_label == "end")
        frame["_source_timestamp"] = (dates + pd.to_timedelta(offsets, unit="h")).astype(str)
    return frame


def normalize_history(
    frame: pd.DataFrame, mapping: pd.DataFrame, schema: HistorySchema
) -> pd.DataFrame:
    """Map verified aliases to operating units, resolve duplicates, then aggregate.

    Mapping columns are source_id, unit_id, site_id. All mapped units constitute
    the verified roster for this import's period. Equal aliases are counted once;
    a conflict (including null versus a reported value) fails for reconciliation.
    """
    if not {"source_id", "unit_id", "site_id"}.issubset(mapping.columns):
        raise ValueError("Historical mapping requires source_id, unit_id and site_id")
    if mapping.empty or mapping["source_id"].duplicated().any():
        raise ValueError("Each historical source identity must have exactly one mapping")
    if mapping[["source_id", "unit_id", "site_id"]].isna().any().any():
        raise ValueError("Historical identity mapping cannot contain nulls")
    if (mapping.groupby("unit_id")["site_id"].nunique() > 1).any():
        raise ValueError("Each operating unit must belong to exactly one site in this import")
    prepared = _hourly_table(frame, schema)
    table = pd.DataFrame(
        {
            "source_id": prepared[schema.identity_column].astype(str),
            "_source_timestamp": prepared["_source_timestamp"],
            "_generation_value": prepared[schema.value_column],
        }
    )
    unknown = set(table["source_id"]) - set(mapping["source_id"])
    if unknown:
        raise ValueError(f"Historical export contains {len(unknown)} unmapped source identities")
    table = table.merge(mapping, on="source_id", validate="many_to_one", how="left")
    table["timestamp"] = utc_intervals(
        table["_source_timestamp"], timezone=schema.timezone, label=schema.timestamp_label
    )
    scale = 0.001 if schema.energy_unit.startswith("k") else 1.0
    table["actual_mwh"] = (
        numeric_values(table["_generation_value"], decimal=schema.decimal_separator) * scale
    )
    keys = ["site_id", "unit_id", "timestamp"]
    if (table.groupby(keys)["actual_mwh"].nunique(dropna=False) > 1).any():
        raise ValueError("Conflicting historical unit-hours require explicit reconciliation")
    duplicate_rows = int(table.duplicated(keys).sum())
    units = table.drop_duplicates(keys)[[*keys, "actual_mwh"]]
    roster = {
        str(site): frozenset(group["unit_id"].astype(str))
        for site, group in mapping.groupby("site_id", sort=False)
    }
    output = aggregate_units(units, roster)
    output["source"] = schema.source
    output["measurement_basis"] = schema.measurement_basis
    output.attrs.update(
        source=schema.source,
        timestamp_convention="UTC interval start; one elapsed hour",
        schema=asdict(schema),
        duplicate_equal_rows_removed=duplicate_rows,
        generation_rule="mean source power times one hour, or reported one-hour energy",
        missing_rule="missing stays null; partial site total is not actual_mwh",
        roster_scope="mapping valid only for the imported historical period",
        source_conflicts="rejected; no automatic precedence across source regimes",
    )
    return output


def import_history(
    path: Path,
    mapping_path: Path,
    output: Path,
    schema: HistorySchema,
    *,
    member: str | None = None,
) -> Artifact:
    """Import preserved exports with exact input/mapping/schema hashes and provenance."""
    source_hash = sha256_file(path)
    mapping_hash = sha256_file(mapping_path)
    request = cast(
        dict[str, JSONValue],
        {
            "source": schema.source,
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
    mapping = identity_mapping(mapping_path, ("source_id", "unit_id", "site_id"))
    normalized = normalize_history(frame, mapping, schema)
    if source_hash != sha256_file(path) or mapping_hash != sha256_file(mapping_path):
        raise ValueError("Source or identity mapping changed during import")
    return write_parquet(
        normalized,
        output,
        request=request,
        provenance=cast(dict[str, JSONValue], normalized.attrs),
    )
