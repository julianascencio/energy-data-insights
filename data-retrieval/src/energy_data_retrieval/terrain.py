"""Read native elevation grids without resampling or inventing missing heights."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import rasterio
from affine import Affine
from numpy.typing import NDArray
from rasterio.io import MemoryFile
from rasterio.warp import transform, transform_bounds
from rasterio.windows import Window, from_bounds
from rasterio.windows import bounds as window_bounds

from energy_data_retrieval.transport import atomic_bytes

type Bounds = tuple[float, float, float, float]


@dataclass(frozen=True, slots=True)
class TerrainSource:
    """Product identity; vertical datum is independent of horizontal CRS."""

    id: str
    name: str
    surface: str
    vertical_datum: str
    reference_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TerrainMetadata:
    """Native spacing uses CRS units, not a claimed positional accuracy."""

    source: TerrainSource
    crs: str
    shape: tuple[int, int]
    bounds: Bounds
    pixel_spacing: tuple[float, float]
    horizontal_unit: str
    nodata: float | str | None
    scale: float
    offset: float
    elevation_unit: str = "m"


@dataclass(frozen=True, slots=True)
class TerrainWindow:
    """Decoded metres; nodata/masked/nonfinite cells are NaN, zero is valid."""

    elevation_m: NDArray[np.float64]
    transform: Affine
    metadata: TerrainMetadata

    def sample(self, latitude: float, longitude: float) -> float | None:
        """Nearest native cell, with no interpolation; None means missing data."""
        validate_point(latitude, longitude)
        xs, ys = transform("EPSG:4326", self.metadata.crs, [longitude], [latitude])
        inverse = ~self.transform
        column = inverse.a * xs[0] + inverse.b * ys[0] + inverse.c
        row = inverse.d * xs[0] + inverse.e * ys[0] + inverse.f
        i, j = math.floor(row), math.floor(column)
        if not (0 <= i < self.elevation_m.shape[0] and 0 <= j < self.elevation_m.shape[1]):
            raise ValueError("Site is outside the loaded terrain window")
        value = float(self.elevation_m[i, j])
        return value if math.isfinite(value) else None


def validate_point(latitude: float, longitude: float) -> None:
    """Validate WGS84 coordinates; +180 and +90 are excluded tile origins."""
    if (
        isinstance(latitude, bool)
        or isinstance(longitude, bool)
        or not math.isfinite(latitude)
        or not math.isfinite(longitude)
        or not -90 <= latitude < 90
        or not -180 <= longitude < 180
    ):
        raise ValueError("Require finite latitude in [-90,90) and longitude in [-180,180)")


def validate_bounds(bounds: Bounds) -> None:
    """Require west, south, east, north; split antimeridian requests explicitly."""
    if len(bounds) != 4 or any(isinstance(x, bool) or not math.isfinite(x) for x in bounds):
        raise ValueError("Bounds must contain four finite numbers")
    west, south, east, north = bounds
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError("Require west < east and south < north in WGS84; split the antimeridian")


def degree_tiles(bounds: Bounds, *, maximum_tiles: int = 16) -> tuple[tuple[int, int], ...]:
    """Southwest (latitude, longitude) origins of intersecting 1-degree tiles."""
    validate_bounds(bounds)
    if type(maximum_tiles) is not int or maximum_tiles < 1:
        raise ValueError("maximum_tiles must be a positive integer")
    west, south, east, north = bounds
    count = (math.ceil(east) - math.floor(west)) * (math.ceil(north) - math.floor(south))
    if count > maximum_tiles:
        raise ValueError("Requested area exceeds maximum_tiles")
    return tuple(
        (lat, lon)
        for lat in range(math.floor(south), math.ceil(north))
        for lon in range(math.floor(west), math.ceil(east))
    )


def _check_grid(dataset: rasterio.io.DatasetReader) -> None:
    t = dataset.transform
    if dataset.count != 1 or dataset.crs is None:
        raise ValueError("Terrain must have one elevation band and a horizontal CRS")
    if not all(math.isfinite(v) for v in t) or t.b != 0 or t.d != 0 or t.a <= 0 or t.e >= 0:
        raise ValueError("Terrain must be a finite, north-up grid")
    if not all(math.isfinite(v) for v in (dataset.scales[0], dataset.offsets[0])):
        raise ValueError("Invalid elevation scale or offset")


def describe_terrain(path: Path, source: TerrainSource) -> TerrainMetadata:
    """Inspect a local file without loading its elevation array.

    Source descriptors declare metre-valued products. Retain the descriptor,
    request record and project metadata with the file; a CRS alone does not
    establish a vertical datum or distinguish a DSM from bare-earth terrain.
    """
    with rasterio.open(Path(path)) as dataset:
        _check_grid(dataset)
        nodata = dataset.nodata
        if nodata is not None and not math.isfinite(nodata):
            nodata = "NaN" if math.isnan(nodata) else str(nodata)
        return TerrainMetadata(
            source,
            str(dataset.crs),
            (dataset.height, dataset.width),
            tuple(dataset.bounds),
            dataset.res,
            "degree" if dataset.crs.is_geographic else dataset.crs.linear_units,
            nodata,
            dataset.scales[0],
            dataset.offsets[0],
        )


def read_terrain(
    path: Path,
    source: TerrainSource,
    *,
    bounds_wgs84: Bounds | None = None,
    maximum_pixels: int = 4_000_000,
) -> TerrainWindow:
    """Read an enclosing native-pixel window, retaining its exact grid.

    The requested bounding box must fit within this file. Obtain all intersecting
    tiles separately for larger areas. No reprojection, merging, hole filling,
    vertical conversion, overview selection or elevation interpolation occurs.
    """
    if type(maximum_pixels) is not int or maximum_pixels < 1:
        raise ValueError("maximum_pixels must be a positive integer")
    metadata = describe_terrain(path, source)
    with rasterio.open(Path(path)) as dataset:
        window = Window.from_slices((0, dataset.height), (0, dataset.width))
        if bounds_wgs84 is not None:
            validate_bounds(bounds_wgs84)
            native = transform_bounds("EPSG:4326", dataset.crs, *bounds_wgs84, densify_pts=21)
            raw = from_bounds(*native, transform=dataset.transform)
            left, top = math.floor(raw.col_off), math.floor(raw.row_off)
            right, bottom = math.ceil(raw.col_off + raw.width), math.ceil(raw.row_off + raw.height)
            if left < 0 or top < 0 or right > dataset.width or bottom > dataset.height:
                raise ValueError("Requested bounds extend outside this terrain file")
            window = Window.from_slices((top, bottom), (left, right))
        if window.width * window.height > maximum_pixels:
            raise ValueError("Terrain window exceeds maximum_pixels; request a smaller area")
        raw_values = dataset.read(1, window=window, masked=True).astype("float64")
        values = raw_values.filled(np.nan) * metadata.scale + metadata.offset
        values[~np.isfinite(values)] = np.nan
        affine = dataset.window_transform(window)
        bounds = tuple(window_bounds(window, dataset.transform))
    info = TerrainMetadata(
        source,
        metadata.crs,
        values.shape,
        bounds,
        metadata.pixel_spacing,
        metadata.horizontal_unit,
        "NaN",
        1.0,
        0.0,
    )
    return TerrainWindow(values, affine, info)


def write_terrain_window(window: TerrainWindow, path: Path) -> Path:
    """Save decoded metre elevations and source/datum tags, without resampling."""
    values = window.elevation_m
    with MemoryFile() as memory:
        with memory.open(
            driver="GTiff",
            height=values.shape[0],
            width=values.shape[1],
            count=1,
            dtype="float64",
            crs=window.metadata.crs,
            transform=window.transform,
            nodata=float("nan"),
            compress="deflate",
            predictor=3,
        ) as dataset:
            dataset.write(values, 1)
            dataset.set_band_unit(1, "m")
            dataset.update_tags(
                **{key: str(value) for key, value in asdict(window.metadata.source).items()}
            )
        atomic_bytes(Path(path), memory.read())
    return Path(path)
