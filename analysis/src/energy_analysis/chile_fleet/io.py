"""Strict hourly schema validation and bounded, per-site Arrow scans."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterator, Mapping
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

VALUE_COLUMNS = (
    "actual_mwh",
    "ghi_wm2",
    "temperature_c",
    "wind_speed_ms",
    "gust_ms",
    "duration_hours",
    "expected_mwh",
    "expected_final_mwh",
    "expected_heldout_mwh",
)
OPTIONAL_WEATHER = ("ghi_wm2", "temperature_c", "wind_speed_ms", "gust_ms")


def read_table(path: Path) -> pd.DataFrame:
    """Read a small registry or CSV; production hourly inputs should be Parquet."""
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, dtype={"site_id": "string"})
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    raise ValueError(f"Expected a CSV or Parquet table: {path.name}")


def normalize_ids(values: pd.Series) -> pd.Series:
    """Keep stable string identifiers; reject missing and whitespace-only IDs."""
    result = values.astype("string").str.strip()
    if result.isna().any() or result.eq("").any():
        raise ValueError("site_id cannot be missing or empty")
    return result


def parse_utc(values: pd.Series) -> pd.DatetimeIndex:
    """Reject naive civil times, then normalize explicit offsets to UTC."""
    if isinstance(values.dtype, pd.DatetimeTZDtype):
        return pd.DatetimeIndex(values).tz_convert("UTC")
    text = values.astype("string")
    offset_present = text.str.contains(r"(?:Z|[+-]\d{2}:?\d{2})$", regex=True, na=False)
    if not offset_present.all():
        raise ValueError(
            "Every timestamp must include an explicit timezone offset; naive times are rejected"
        )
    return pd.DatetimeIndex(pd.to_datetime(text, utc=True, errors="raise", format="ISO8601"))


def validate_hourly(frame: pd.DataFrame, *, require_actual: bool = True) -> pd.DataFrame:
    """Validate site-hour keys without replacing zero, missing or negative values."""
    required = {"site_id", "timestamp"} | ({"actual_mwh"} if require_actual else set())
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing hourly columns: {', '.join(sorted(missing))}")
    if "unit_id" in frame.columns:
        raise ValueError(
            "Unit-level CEN data must be aggregated using a trusted unit roster before analysis"
        )
    result = frame.copy()
    result["site_id"] = normalize_ids(result["site_id"])
    result["timestamp"] = parse_utc(result["timestamp"])
    if result["timestamp"].isna().any():
        raise ValueError("Missing timestamps are not valid site-hour observations")
    if result.duplicated(["site_id", "timestamp"]).any():
        raise ValueError(
            "Duplicate site_id/timestamp keys; resolve source conflicts before analysis"
        )
    if not result["timestamp"].eq(result["timestamp"].dt.floor("h")).all():
        raise ValueError("Only hourly interval-start timestamps are supported")
    for name in VALUE_COLUMNS:
        if name in result:
            result[name] = pd.to_numeric(result[name], errors="raise").astype("float64")
    if "duration_hours" in result and not result["duration_hours"].eq(1.0).all():
        raise ValueError("This workflow requires one elapsed hour per energy observation")
    if "generation_complete" in result:
        complete = boolean_values(result["generation_complete"], "generation_complete")
        if "actual_mwh" in result:
            result.loc[~complete, "actual_mwh"] = np.nan
    for name in OPTIONAL_WEATHER:
        if name not in result:
            result[name] = np.nan
    return result.sort_values(["site_id", "timestamp"], kind="stable").reset_index(drop=True)


def boolean_values(values: pd.Series, label: str) -> pd.Series:
    """Decode bool/0/1/string booleans without Python's truthy-string trap."""
    mapped = (
        values.astype("string")
        .str.lower()
        .map({"true": True, "false": False, "1": True, "0": False})
    )
    if mapped.isna().any():
        raise ValueError(f"{label} must contain explicit true/false values")
    return mapped.astype(bool)


def load_sites(path: Path) -> pd.DataFrame:
    """Preserve every registry row, including sites lacking coordinates or data."""
    sites = read_table(path)
    if "site_id" not in sites:
        raise ValueError("Site registry requires site_id")
    sites["site_id"] = normalize_ids(sites["site_id"])
    if sites["site_id"].duplicated().any():
        raise ValueError("Duplicate site_id in registry")
    for name in (
        "latitude",
        "longitude",
        "dc_capacity_mw",
        "ac_capacity_mw",
        "tilt_deg",
        "azimuth_deg",
    ):
        if name not in sites:
            sites[name] = np.nan
        sites[name] = pd.to_numeric(sites[name], errors="raise").astype("float64")
    for name in ("name", "region", "racking_type"):
        if name not in sites:
            sites[name] = ""
        sites[name] = sites[name].fillna("").astype("string")
    if "dc_capacity_qualified" not in sites:
        sites["dc_capacity_qualified"] = False
    sites["dc_capacity_qualified"] = boolean_values(
        sites["dc_capacity_qualified"], "dc_capacity_qualified"
    )
    qualified = sites["dc_capacity_qualified"]
    if (qualified & (~np.isfinite(sites["dc_capacity_mw"]) | sites["dc_capacity_mw"].le(0))).any():
        raise ValueError("Qualified DC capacity must be finite and strictly positive")
    return sites.sort_values("site_id", kind="stable").reset_index(drop=True)


class SiteDataSource:
    """Read one site at a time, using Arrow predicate pushdown for Parquet.

    CSV is a convenience for small files (at most one million rows). Partition
    production datasets by site_id to avoid scanning unrelated row groups.
    """

    def __init__(self, path: Path, *, require_actual: bool = True) -> None:
        self.path = path
        self.require_actual = require_actual
        self._csv: pd.DataFrame | None = None
        self._dataset: ds.Dataset | None = None
        if path.suffix.lower() == ".csv":
            frame = pd.read_csv(path, dtype={"site_id": "string"}, nrows=1_000_001)
            if len(frame) > 1_000_000:
                raise ValueError(
                    "CSV input exceeds one million rows; convert to site-partitioned Parquet"
                )
            self._csv = validate_hourly(frame, require_actual=require_actual)
        else:
            self._dataset = ds.dataset(
                str(path), format="parquet", partitioning="hive", exclude_invalid_files=True
            )
            fields = set(self._dataset.schema.names)
            required = {"site_id", "timestamp"} | ({"actual_mwh"} if require_actual else set())
            if not required <= fields:
                raise ValueError(
                    "Hourly Parquet dataset requires site_id, timestamp and actual_mwh"
                )

    def site(self, site_id: str) -> pd.DataFrame:
        if self._csv is not None:
            return self._csv.loc[self._csv["site_id"].eq(site_id)].copy()
        assert self._dataset is not None
        field_type = self._dataset.schema.field("site_id").type
        value: str | int = int(site_id) if str(field_type).startswith(("int", "uint")) else site_id
        columns = [
            name
            for name in self._dataset.schema.names
            if name
            in {
                "site_id",
                "timestamp",
                "generation_complete",
                "unit_id",
                *VALUE_COLUMNS,
            }
        ]
        table = self._dataset.scanner(
            columns=columns, filter=ds.field("site_id") == value, use_threads=True
        ).to_table()
        return validate_hourly(table.to_pandas(), require_actual=self.require_actual)


def input_files(path: Path) -> Iterator[Path]:
    if path.is_file():
        yield path
    elif path.is_dir():
        yield from sorted(path.rglob("*.parquet"))
    else:
        raise FileNotFoundError(path)


def fingerprint(path: Path, *, contents: bool = True) -> dict[str, object]:
    """Hash all source files once; no tokens or request URLs enter provenance."""
    files: list[dict[str, object]] = []
    for file in input_files(path):
        entry: dict[str, object] = {
            "path": str(file.relative_to(path)) if path.is_dir() else file.name,
            "bytes": file.stat().st_size,
        }
        if contents:
            with file.open("rb") as stream:
                entry["sha256"] = hashlib.file_digest(stream, "sha256").hexdigest()
        files.append(entry)
    return {"name": path.name, "content_hashed": contents, "files": files}


def json_safe(value: object) -> object:
    """JSON serialization with explicit nulls for nonfinite scientific values."""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, (Path, datetime, date)):
        return str(value)
    if isinstance(value, np.ndarray):
        return json_safe(value.tolist())
    if isinstance(value, Mapping):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [json_safe(v) for v in value]
    if is_dataclass(value) and not isinstance(value, type):
        return json_safe(asdict(value))
    raise TypeError(f"Unsupported provenance value: {type(value).__name__}")


def write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(json_safe(value), ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def row_mapping(frame: pd.DataFrame) -> Iterator[dict[str, object]]:
    for row in frame.to_dict(orient="records"):
        yield cast("dict[str, object]", row)


def write_fleet_csv(frame: pd.DataFrame, path: Path) -> None:
    """Escape spreadsheet formula prefixes in labels; Parquet preserves exact IDs."""
    exported = frame.copy()
    for name in ("site_id", "name", "region"):
        if name in exported:
            values = exported[name].astype("string")
            suspicious = values.str.match(r"^(?:[\s]*[=+@-]|[\t\r\n])", na=False)
            exported[name] = values.where(~suspicious, "'" + values)
    exported.to_csv(path, index=False)


def validate_output_location(output: Path, *inputs: Path) -> None:
    """Keep generated Parquet out of a directory scanned as an input dataset."""
    destination = output.resolve()
    for source in inputs:
        if source.is_dir() and destination.is_relative_to(source.resolve()):
            raise ValueError("Output must be outside all input Parquet dataset directories")
