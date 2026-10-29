"""Reusable rectilinear geographic mapping, alignment, area and GeoJSON utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import numpy as np
import xarray as xr
from numpy.typing import ArrayLike, NDArray

REFERENCE_IDS = (
    "ascencio_vasquez_2021_thesis",
    "ascencio_vasquez_2019_kgpv",
    "xarray_documentation",
)


def normalize_grid(data: xr.DataArray) -> xr.DataArray:
    """Return sorted lat/lon coordinates, lon in [-180,180), rejecting duplicate seams."""
    for axis, limit in (("lat", 90), ("lon", 360)):
        if axis not in data.coords or data[axis].dims != (axis,):
            raise ValueError("Mapping requires one-dimensional lat/lon coordinates")
        if not np.isfinite(data[axis]).all() or (np.abs(data[axis]) > limit).any():
            raise ValueError(f"Invalid {axis} coordinates")
    result = data.assign_coords(lon=(data.lon + 180) % 360 - 180).sortby(["lat", "lon"])
    if not result.indexes["lat"].is_unique or not result.indexes["lon"].is_unique:
        raise ValueError("Duplicate grid coordinates (including cyclic seam)")
    return result


def regrid(
    data: xr.DataArray,
    latitude: ArrayLike,
    longitude: ArrayLike,
    *,
    method: Literal["linear", "nearest"] = "linear",
    categorical: bool = False,
) -> xr.DataArray:
    """Bilinear/nearest interpolation of a rectilinear grid; no extrapolation.

    Categorical layers require nearest neighbour. Missing source cells are not
    filled. There is no cyclic seam interpolation; targets outside the source
    centre extent remain NaN. Regrid climate inputs before classification.
    """
    if method not in {"linear", "nearest"} or (categorical and method != "nearest"):
        raise ValueError("Categorical layers require nearest; continuous use linear or nearest")
    source = normalize_grid(data)
    lat = np.asarray(latitude, dtype=float)
    lon = np.asarray(longitude, dtype=float)
    for values, limit in ((lat, 90), (lon, 180)):
        if (
            values.ndim != 1
            or not len(values)
            or not np.isfinite(values).all()
            or np.any(np.abs(values) > limit)
            or np.any(np.diff(values) <= 0)
        ):
            raise ValueError("Target coordinates must be finite, unique, increasing and geographic")
    if np.array_equal(lat, source.lat.values) and np.array_equal(lon, source.lon.values):
        return source.copy()
    if source.sizes["lat"] < 2 or source.sizes["lon"] < 2:
        raise ValueError("Interpolation requires at least two source centres per axis")
    result = source.interp(lat=lat, lon=lon, method=method)
    result.attrs.update(source.attrs, regridding=method)
    return result


def _edges(centres: NDArray[np.float64], limit: float) -> NDArray[np.float64]:
    if (
        len(centres) < 2
        or not np.isfinite(centres).all()
        or np.any(np.diff(centres) <= 0)
        or not np.allclose(np.diff(centres), np.diff(centres)[0])
    ):
        raise ValueError("Cell export requires a regular grid with at least two centres per axis")
    edges = np.r_[
        centres[0] - (centres[1] - centres[0]) / 2,
        (centres[1:] + centres[:-1]) / 2,
        centres[-1] + (centres[-1] - centres[-2]) / 2,
    ]
    return np.clip(edges, -limit, limit)


def cell_areas_km2(data: xr.DataArray) -> xr.DataArray:
    """Spherical cell areas from regular centre coordinates; Earth radius 6371.0088 km."""
    source = normalize_grid(data)
    lat = _edges(np.asarray(source.lat.values, dtype=float), 90)
    lon = _edges(np.asarray(source.lon.values, dtype=float), 180)
    areas = 6371.0088**2 * np.diff(np.sin(np.deg2rad(lat)))[:, None] * np.deg2rad(np.diff(lon))
    return xr.DataArray(
        areas,
        dims=("lat", "lon"),
        coords={"lat": source.lat, "lon": source.lon},
        name="cell_area_km2",
        attrs={"units": "km2"},
    )


def class_area_summary(data: xr.DataArray, *, nodata: int = 0) -> dict[int, float]:
    """Area by numeric class, excluding nodata/NaN; not a count of equally sized cells."""
    source = normalize_grid(data)
    if set(source.dims) != {"lat", "lon"}:
        raise ValueError("Area summaries require a two-dimensional class map")
    areas = cell_areas_km2(source)
    values = source.values
    valid = values[np.isfinite(values) & (values != nodata)]
    if np.any(valid != np.floor(valid)):
        raise ValueError("Class IDs must be integers")
    return {int(value): float(areas.where(source == value, 0).sum()) for value in np.unique(valid)}


def write_geojson(
    data: xr.DataArray,
    path: Path,
    *,
    nodata: float | None = None,
    labels: dict[int, str] | None = None,
    maximum_features: int = 100_000,
) -> Path:
    """Export bounded regular grid cell polygons in EPSG:4326 for GIS/web maps.

    Missing cells are omitted; boundaries are cell midpoints clipped at the poles
    and antimeridian. Use NetCDF for large global layers; GeoJSON is for subsets.
    """
    source = normalize_grid(data).transpose("lat", "lon")
    values = np.asarray(source.values, dtype=float)
    valid = np.isfinite(values)
    if nodata is not None:
        valid &= values != nodata
    if maximum_features < 1 or np.count_nonzero(valid) > maximum_features:
        raise ValueError("GeoJSON exceeds maximum_features; subset the grid or use NetCDF")
    lat = _edges(np.asarray(source.lat.values, dtype=float), 90)
    lon = _edges(np.asarray(source.lon.values, dtype=float), 180)
    features = []
    for row, col in zip(*np.nonzero(valid), strict=True):
        west, east = float(lon[col]), float(lon[col + 1])
        south, north = float(lat[row]), float(lat[row + 1])
        value = float(values[row, col])
        properties: dict[str, object] = {"value": value}
        if labels is not None:
            if not value.is_integer() or int(value) not in labels:
                raise ValueError("Every exported class must have a label")
            properties["label"] = labels[int(value)]
        features.append(
            {
                "type": "Feature",
                "properties": properties,
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[west, south], [east, south], [east, north], [west, north], [west, south]]
                    ],
                },
            }
        )
    document = {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "name": str(source.name),
            "units": source.attrs.get("units", ""),
            "coordinate_reference_system": "EPSG:4326",
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, allow_nan=False, separators=(",", ":")), encoding="utf-8")
    return path
