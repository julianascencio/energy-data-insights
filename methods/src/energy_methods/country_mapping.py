"""Country grids, polygon masks, clipped plots and clipped cell exports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import numpy as np
import xarray as xr
from matplotlib.axes import Axes
from matplotlib.collections import QuadMesh
from matplotlib.colors import Colormap, Normalize
from matplotlib.patches import PathPatch
from matplotlib.path import Path as PlotPath
from shapely import box, intersection, intersects, intersects_xy
from shapely.geometry import MultiPolygon, Polygon, mapping
from shapely.geometry.polygon import orient

from energy_methods.country_boundaries import CountrySelection, polygons
from energy_methods.mapping import _edges, normalize_grid

REFERENCE_IDS = ("natural_earth_countries", "shapely_documentation", "pyproj_documentation")
type Bounds = tuple[float, float, float, float]


def _bounds(bounds: Bounds) -> Bounds:
    west, south, east, north = bounds
    if not np.isfinite(bounds).all() or not (
        -180 <= west < east <= 180 and -90 <= south < north <= 90
    ):
        raise ValueError("bounds must be (west, south, east, north) in EPSG:4326")
    return bounds


def country_grid(
    selection: CountrySelection,
    *,
    resolution: float = 0.5,
    bounds: Bounds | None = None,
    maximum_cells: int = 250_000,
) -> xr.Dataset:
    """Build a regular lon/lat grid and an intersecting-cell country mask.

    Resolution is degrees, not new source information. Cell edges align to
    -180/-90. The spacing must divide 180 degrees; e.g. 1, .5, .25 or .1.
    All country parts determine default bounds. Explicit bounds select an area
    of interest (useful for overseas territories/insets). At least two centres
    per axis support cell edges and export. Allocation is bounded in advance.
    """
    if (
        isinstance(resolution, bool)
        or not np.isfinite(resolution)
        or not 1e-6 <= resolution <= 30
        or not np.isclose(180 / resolution, round(180 / resolution), rtol=0, atol=1e-7)
    ):
        raise ValueError("resolution must be 1e-6..30 degrees and divide 180")
    if type(maximum_cells) is not int or maximum_cells < 1:
        raise ValueError("maximum_cells must be a positive integer")
    west, south, east, north = _bounds(bounds or selection.geometry.bounds)
    axes = []
    for low, high, origin in ((south, north, -90), (west, east, -180)):
        first = int(np.floor((low - origin) / resolution))
        last = int(np.ceil((high - origin) / resolution))
        total = round(-2 * origin / resolution)
        if last - first < 2:
            first = max(0, min(first, total - 2))
            last = first + 2
        axes.append((first, last, origin))
    if np.prod([last - first for first, last, _ in axes]) > maximum_cells:
        raise ValueError("Country grid exceeds maximum_cells; reduce extent or use a coarser grid")
    lat, lon = [
        origin + (np.arange(first, last) + 0.5) * resolution for first, last, origin in axes
    ]
    template = xr.DataArray(
        np.zeros((len(lat), len(lon))), dims=("lat", "lon"), coords={"lat": lat, "lon": lon}
    )
    mask = country_mask(template, selection, mode="intersects", maximum_cells=maximum_cells)
    if not mask.any():
        raise ValueError("Selected bounds/grid do not intersect the selected countries")
    result = mask.to_dataset(name="country_mask")
    result.attrs = {
        "country_codes": " ".join(selection.codes),
        "grid_degrees": resolution,
        "coordinate_reference_system": "EPSG:4326",
        "boundary_source": selection.source,
    }
    return result


def country_mask(
    data: xr.DataArray,
    selection: CountrySelection,
    *,
    mode: Literal["center", "intersects"] = "intersects",
    maximum_cells: int = 250_000,
) -> xr.DataArray:
    """Boolean mask on normalized lat/lon coordinates; no interpolation.

    'center' includes centres on country boundaries, excludes interior holes.
    'intersects' includes cells touching any polygon; this supports retrieval
    for partial coastal cells. It is not a fractional-area mask. Both modes keep
    islands. Antimeridian-split countries work on a conventional -180..180 grid;
    default extents can therefore span the world. Use separate views to zoom.
    """
    source = normalize_grid(data)
    size = source.sizes["lat"] * source.sizes["lon"]
    if type(maximum_cells) is not int or not 0 < size <= maximum_cells:
        raise ValueError("Country mask exceeds maximum_cells or has an empty grid")
    if mode == "center":
        values = intersects_xy(
            selection.geometry, source.lon.values[None, :], source.lat.values[:, None]
        )
    elif mode == "intersects":
        lat = _edges(source.lat.values.astype(float), 90)
        lon = _edges(source.lon.values.astype(float), 180)
        cells = box(lon[:-1][None, :], lat[:-1][:, None], lon[1:][None, :], lat[1:][:, None])
        values = intersects(selection.geometry, cells)
    else:
        raise ValueError("Mask mode must be center or intersects")
    return xr.DataArray(
        values,
        dims=("lat", "lon"),
        coords={"lat": source.lat, "lon": source.lon},
        attrs={"mask_mode": mode, "country_codes": " ".join(selection.codes)},
    )


def clip_country_grid(
    data: xr.DataArray,
    selection: CountrySelection,
    *,
    nodata: float = np.nan,
    mode: Literal["center", "intersects"] = "intersects",
    crop: bool = True,
) -> xr.DataArray:
    """Mask outside countries and optionally trim outer empty rows/columns.

    Partial cells retain their original numerical value; the plotting/export
    functions clip their polygon footprint. Existing NaN/nodata values stay
    missing. For integer class maps pass nodata=0 to preserve integer dtype.
    Supports additional dimensions such as year/month; never resamples classes.
    """
    source = normalize_grid(data)
    mask = country_mask(source, selection, mode=mode)
    result = source.where(mask, other=nodata)
    if crop:
        rows, cols = np.nonzero(mask.values)
        if not len(rows):
            raise ValueError("No selected country cells on this grid; check extent/resolution")
        slices = {}
        for axis, indices in (("lat", rows), ("lon", cols)):
            first, last = int(indices.min()), int(indices.max()) + 1
            if last - first == 1 and source.sizes[axis] >= 2:
                first = max(0, min(first, source.sizes[axis] - 2))
                last = first + 2
            slices[axis] = slice(first, last)
        result = result.isel(slices)
    result.attrs.update(country_codes=" ".join(selection.codes), country_mask_mode=mode)
    return result


def _plot_path(geometry: Polygon | MultiPolygon) -> PlotPath:
    paths = []
    for polygon in polygons(geometry):
        polygon = orient(polygon, sign=1.0)  # CCW shells / CW holes for nonzero fill.
        for ring in (polygon.exterior, *polygon.interiors):
            vertices = np.asarray(ring.coords)[:, :2]
            codes = np.full(len(vertices), PlotPath.LINETO, dtype=np.uint8)
            codes[0], codes[-1] = PlotPath.MOVETO, PlotPath.CLOSEPOLY
            paths.append(PlotPath(vertices, codes))
    return PlotPath.make_compound_path(*paths)


def plot_country_map(
    data: xr.DataArray,
    selection: CountrySelection,
    *,
    ax: Axes,
    bounds: Bounds | None = None,
    cmap: str | Colormap = "viridis",
    norm: Normalize | None = None,
    vmin: float | None = None,
    vmax: float | None = None,
    nodata: float | None = None,
) -> QuadMesh:
    """Draw unsmoothed values clipped to exact country contours and draw borders.

    Returns a QuadMesh for fig.colorbar. Geographic axes are longitude/latitude,
    not a metric/equal-area projection. Gray denotes missing data within the
    supplied boundaries; white/background is outside. Use explicit bounds for
    mainland/island views. Boundary detail does not change source resolution.
    """
    source = normalize_grid(data).transpose("lat", "lon")
    lat, lon = (
        _edges(source.lat.values.astype(float), 90),
        _edges(source.lon.values.astype(float), 180),
    )
    values = np.asarray(source.values, dtype=float)
    values = np.ma.masked_invalid(values)
    if nodata is not None:
        values = np.ma.masked_equal(values, nodata)
    clip = PathPatch(
        _plot_path(selection.geometry),
        transform=ax.transData,
        facecolor="#d9dfe3",
        edgecolor="none",
    )
    ax.add_patch(clip)
    mesh = ax.pcolormesh(
        lon,
        lat,
        values,
        cmap=cmap,
        norm=norm,
        vmin=vmin,
        vmax=vmax,
        shading="flat",
        rasterized=True,
    )
    mesh.set_clip_path(clip)
    for country in selection.countries:
        ax.add_patch(
            PathPatch(
                _plot_path(country.geometry),
                transform=ax.transData,
                facecolor="none",
                edgecolor="#34444f",
                linewidth=0.65,
            )
        )
    west, south, east, north = _bounds(bounds or selection.geometry.bounds)
    ax.set(xlim=(west, east), ylim=(south, north), xlabel="Longitude (°)", ylabel="Latitude (°)")
    ax.set_aspect(1 / max(np.cos(np.deg2rad((south + north) / 2)), 0.1))
    ax.grid(alpha=0.15, linewidth=0.5)
    return mesh


def write_country_geojson(
    data: xr.DataArray,
    selection: CountrySelection,
    path: Path,
    *,
    nodata: float | None = None,
    labels: dict[int, str] | None = None,
    maximum_features: int = 100_000,
) -> Path:
    """Export cell-country polygon intersections, retaining each cell's value.

    Empty/line-only intersections and missing values are omitted. Holes/islands
    remain in the output. Polygon clipping is planar lon/lat and adds no data
    resolution. Use geodesic/equal-area calculations for fractional-area totals.
    """
    source = normalize_grid(data).transpose("lat", "lon")
    mask = country_mask(source, selection).values
    values = np.asarray(source.values, dtype=float)
    valid = mask & np.isfinite(values)
    if nodata is not None:
        valid &= values != nodata
    if (
        type(maximum_features) is not int
        or not maximum_features > 0
        or valid.sum() > maximum_features
    ):
        raise ValueError("Country GeoJSON exceeds maximum_features")
    lat, lon = (
        _edges(source.lat.values.astype(float), 90),
        _edges(source.lon.values.astype(float), 180),
    )
    features = []
    for row, col in zip(*np.nonzero(valid), strict=True):
        geometry = intersection(
            box(lon[col], lat[row], lon[col + 1], lat[row + 1]), selection.geometry
        )
        if geometry.is_empty or geometry.area == 0:
            continue
        if geometry.geom_type == "GeometryCollection":
            geometry = MultiPolygon(
                [
                    p
                    for g in geometry.geoms
                    if isinstance(g, (Polygon, MultiPolygon))
                    for p in polygons(g)
                ]
            )
        value = float(values[row, col])
        properties: dict[str, object] = {"value": value}
        if labels is not None:
            if not value.is_integer() or int(value) not in labels:
                raise ValueError("Every exported class must have a label")
            properties["label"] = labels[int(value)]
        features.append(
            {"type": "Feature", "properties": properties, "geometry": mapping(geometry)}
        )
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": features,
                "metadata": {
                    "name": str(source.name),
                    "units": source.attrs.get("units", ""),
                    "country_codes": list(selection.codes),
                    "boundary_source": selection.source,
                    "coordinate_reference_system": "EPSG:4326",
                    "clipping": "cell-country intersection",
                },
            },
            allow_nan=False,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    return path
