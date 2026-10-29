"""Bounded decoding of monthly provider NetCDF archives (no climate algorithms)."""

from __future__ import annotations

import gzip
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from energy_data_retrieval.transport import RetrievalError


@contextmanager
def open_netcdf(
    path: Path, *, maximum_uncompressed_bytes: int = 2 * 1024**3
) -> Generator[xr.Dataset, None, None]:
    """Decode CF fill values/scales; expand gzip on disk with a hard byte limit."""
    if maximum_uncompressed_bytes < 1:
        raise ValueError("maximum_uncompressed_bytes must be positive")
    with tempfile.TemporaryDirectory(prefix="energy-climate-") as temporary:
        source = path
        if path.suffix == ".gz":
            source = Path(temporary) / "data.nc"
            size = 0
            with gzip.open(path, "rb") as reader, source.open("wb") as writer:
                while chunk := reader.read(1024**2):
                    size += len(chunk)
                    if size > maximum_uncompressed_bytes:
                        raise RetrievalError("Expanded NetCDF exceeds the configured byte limit")
                    writer.write(chunk)
        elif path.stat().st_size > maximum_uncompressed_bytes:
            raise RetrievalError("NetCDF exceeds the configured byte limit")
        with xr.open_dataset(source, decode_cf=True, decode_timedelta=False) as dataset:
            yield dataset


def normalize_monthly(
    dataset: xr.Dataset,
    variables: dict[str, tuple[str, str]],
    *,
    start_year: int,
    end_year: int,
    bbox: tuple[float, float, float, float] | None = None,
    maximum_values: int = 20_000_000,
) -> xr.Dataset:
    """Select before loading. Output time is a calendar-month label, not UTC telemetry.

    ``variables`` maps native names to (output name, canonical unit). Native units
    are checked by the source adapter. Spatial bounds are inclusive cell centres;
    west > east selects across the antimeridian. No resampling or gap filling.
    """
    if not 1 <= start_year <= end_year <= 9998 or maximum_values < 1:
        raise ValueError("Use ordered years and a positive maximum_values")
    rename = {
        name: target
        for name, target in (("latitude", "lat"), ("longitude", "lon"))
        if name in dataset.dims
    }
    ds = dataset.rename(rename)
    for axis, limit in (("lat", 90), ("lon", 360)):
        if axis not in ds.coords or ds[axis].dims != (axis,):
            raise ValueError("Expected one-dimensional latitude/longitude coordinates")
        values = ds[axis].values
        if not np.isfinite(values).all() or np.any(np.abs(values) > limit):
            raise ValueError(f"Invalid {axis} coordinates")
    ds = ds.assign_coords(lon=(ds.lon + 180) % 360 - 180).sortby(["lat", "lon"])
    if not ds.indexes["lat"].is_unique or not ds.indexes["lon"].is_unique:
        raise ValueError("Duplicate spatial coordinates")
    times = pd.DatetimeIndex(ds.time.values)
    months = times.to_period("M")
    if times.hasnans or months.has_duplicates or not months.is_monotonic_increasing:
        raise ValueError("Expected unique increasing calendar months")
    ds = ds.assign_coords(time=months.to_timestamp()).sel(
        time=slice(f"{start_year:04d}-01-01", f"{end_year:04d}-12-31")
    )
    if bbox is not None:
        west, south, east, north = bbox
        if not (
            np.isfinite(bbox).all()
            and -180 <= west <= 180
            and -180 <= east <= 180
            and -90 <= south <= north <= 90
        ):
            raise ValueError("bbox must be WEST SOUTH EAST NORTH in geographic degrees")
        longitude = (
            (ds.lon >= west) & (ds.lon <= east)
            if west <= east
            else (ds.lon >= west) | (ds.lon <= east)
        )
        ds = ds.sel(lat=slice(south, north)).isel(lon=np.flatnonzero(longitude.values))
    if not ds.sizes["lat"] or not ds.sizes["lon"]:
        raise ValueError("No grid cell centres fall inside bbox")
    selected = ds[list(variables)]
    if any(set(selected[name].dims) != {"time", "lat", "lon"} for name in variables):
        raise ValueError("Monthly variables must have time, lat and lon dimensions only")
    if sum(v.size for v in selected.data_vars.values()) > maximum_values:
        raise ValueError("Selected data exceeds maximum_values; select a smaller bbox or archive")
    result = selected.rename({key: value[0] for key, value in variables.items()}).load()
    for native, (name, unit) in variables.items():
        result[name].attrs.update(units=unit, native_variable=native)
    result.time.attrs.update(long_name="calendar month", interval="monthly")
    return result
