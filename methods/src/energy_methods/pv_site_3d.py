"""Reproducible 2.5D PV scenes from geographic footprints and declared terrain.

XY comes from footprints; Z combines sampled elevation with explicit mounting
assumptions. This is not photogrammetry, an as-built survey or a shading model.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cached_property

import numpy as np
from numpy.typing import ArrayLike, NDArray
from pyproj import CRS, Transformer
from shapely.geometry import Polygon

REFERENCE_IDS = ("proj_aeqd", "copernicus_dem")
type FloatArray = NDArray[np.float64]
type IntArray = NDArray[np.int64]


def _coordinates(values: ArrayLike, dimensions: int) -> FloatArray:
    points = np.asarray(values, dtype=float)
    if points.ndim != 2 or points.shape[1] != dimensions or not np.isfinite(points).all():
        raise ValueError(f"Coordinates must be a finite N x {dimensions} array")
    return points


def _wgs84(values: ArrayLike) -> FloatArray:
    xy = _coordinates(values, 2)
    if np.any(np.abs(xy[:, 0]) > 180) or np.any(np.abs(xy[:, 1]) >= 90):
        raise ValueError("Coordinates must be valid WGS84 longitude, latitude")
    return xy


@dataclass(frozen=True)
class LocalSiteFrame:
    """Local azimuthal-equidistant XY metres, Z relative to a declared height.

    X is east and Y north at the origin. Mounting azimuths use these local grid
    axes. The height offset does not convert the input terrain's vertical datum.
    Keep the scene local; the default radius guard is 20 km.
    """

    longitude: float
    latitude: float
    elevation_origin_m: float = 0.0
    maximum_radius_m: float = 20_000.0

    def __post_init__(self) -> None:
        _wgs84([[self.longitude, self.latitude]])
        if not np.isfinite(self.elevation_origin_m):
            raise ValueError("elevation_origin_m must be finite")
        if not np.isfinite(self.maximum_radius_m) or not 1 <= self.maximum_radius_m <= 100_000:
            raise ValueError("maximum_radius_m must be in 1..100000")

    @cached_property
    def crs(self) -> CRS:
        return CRS.from_proj4(
            f"+proj=aeqd +lat_0={self.latitude} +lon_0={self.longitude} "
            "+datum=WGS84 +units=m +no_defs"
        )

    @cached_property
    def _forward(self) -> Transformer:
        return Transformer.from_crs("EPSG:4326", self.crs, always_xy=True)

    @cached_property
    def _inverse(self) -> Transformer:
        return Transformer.from_crs(self.crs, "EPSG:4326", always_xy=True)

    def project(self, longitude_latitude: ArrayLike) -> FloatArray:
        """Project longitude/latitude to local XY, enforcing the radius guard."""
        ll = _wgs84(longitude_latitude)
        xy = np.column_stack(self._forward.transform(ll[:, 0], ll[:, 1]))
        if not np.isfinite(xy).all() or np.any(np.linalg.norm(xy, axis=1) > self.maximum_radius_m):
            raise ValueError("Geometry exceeds the local frame radius")
        return xy

    def unproject(self, xy_m: ArrayLike) -> FloatArray:
        """Convert local XY metres back to WGS84 longitude/latitude."""
        xy = _coordinates(xy_m, 2)
        if np.any(np.linalg.norm(xy, axis=1) > self.maximum_radius_m):
            raise ValueError("Geometry exceeds the local frame radius")
        return np.column_stack(self._inverse.transform(xy[:, 0], xy[:, 1]))


@dataclass(frozen=True)
class ElevationGrid:
    """North-up native metre heights, with CRS and vertical datum kept separately.

    ``transform`` is (a,b,c,d,e,f): x=a*column+b*row+c, y=d*column+e*row+f
    at pixel edges. Sampling uses pixel centres. NaN means missing, never zero.
    The source can be geographic or projected, but must have north-up pixels.
    """

    values_m: FloatArray
    transform: tuple[float, float, float, float, float, float]
    crs: str
    vertical_datum: str

    def __post_init__(self) -> None:
        values = np.asarray(self.values_m, dtype=float).copy()
        if values.ndim != 2 or min(values.shape) < 2 or values.size > 4_000_000:
            raise ValueError("Elevation grid must be at least 2 x 2 and at most 4 million cells")
        if np.isinf(values).any():
            raise ValueError("Infinite terrain heights are invalid; use NaN for nodata")
        if len(self.transform) != 6 or not np.isfinite(self.transform).all():
            raise ValueError("transform must contain six finite affine coefficients")
        a, b, _, d, e, _ = self.transform
        if a <= 0 or e >= 0 or b != 0 or d != 0:
            raise ValueError("Elevation grid must be north-up with positive X spacing")
        CRS.from_user_input(self.crs)
        if not self.vertical_datum.strip():
            raise ValueError("A vertical datum or explicit unknown label is required")
        values.setflags(write=False)
        object.__setattr__(self, "values_m", values)

    @cached_property
    def _transformer(self) -> Transformer:
        return Transformer.from_crs("EPSG:4326", self.crs, always_xy=True)

    def sample(self, longitude_latitude: ArrayLike) -> FloatArray:
        """Bilinear heights; unsupported/outside samples return NaN without extrapolation.

        Every neighbour with nonzero weight must be finite. Exact native centres
        remain valid even beside nodata. Interpolation adds no source resolution.
        """
        ll = _wgs84(longitude_latitude)
        x, y = self._transformer.transform(ll[:, 0], ll[:, 1])
        a, _, c, _, e, f = self.transform
        col, row = (np.asarray(x) - c) / a - 0.5, (np.asarray(y) - f) / e - 0.5
        h, w = self.values_m.shape
        inside = (
            np.isfinite(col)
            & np.isfinite(row)
            & (col >= -1e-8)
            & (row >= -1e-8)
            & (col <= w - 1 + 1e-8)
            & (row <= h - 1 + 1e-8)
        )
        output = np.full(len(ll), np.nan)
        cc, rr = np.clip(col[inside], 0, w - 1), np.clip(row[inside], 0, h - 1)
        # Projection round-off must not turn an exact native centre into a
        # tiny nonzero weight on an adjacent missing pixel. The tolerance is
        # in native pixels, not geographic degrees or terrain height units.
        cc = np.where(np.abs(cc - np.rint(cc)) <= 1e-8, np.rint(cc), cc)
        rr = np.where(np.abs(rr - np.rint(rr)) <= 1e-8, np.rint(rr), rr)
        j, i = (
            np.minimum(np.floor(cc).astype(int), w - 2),
            np.minimum(np.floor(rr).astype(int), h - 2),
        )
        u, v = cc - j, rr - i
        weights = np.column_stack([(1 - u) * (1 - v), u * (1 - v), (1 - u) * v, u * v])
        heights = np.column_stack(
            [
                self.values_m[i, j],
                self.values_m[i, j + 1],
                self.values_m[i + 1, j],
                self.values_m[i + 1, j + 1],
            ]
        )
        used = weights > 1e-12
        valid = np.all(~used | np.isfinite(heights), axis=1)
        sampled = np.sum(weights * np.where(used, heights, 0), axis=1)
        output[np.flatnonzero(inside)[valid]] = sampled[valid]
        return output


@dataclass(frozen=True)
class ModuleFootprint:
    """One convex quadrilateral in longitude/latitude, grouped into a mounting table."""

    id: str
    table_id: str
    vertices_wgs84: FloatArray

    def __post_init__(self) -> None:
        vertices = _wgs84(self.vertices_wgs84).copy()
        if vertices.shape != (4, 2):
            raise ValueError("A module footprint must have four vertices, without a closing repeat")
        if not self.id.strip() or not self.table_id.strip():
            raise ValueError("Module and table IDs must be nonempty strings")
        polygon = Polygon(vertices)
        if (
            not polygon.is_valid
            or polygon.area <= 0
            or not np.isclose(polygon.area, polygon.convex_hull.area, rtol=1e-6, atol=0)
        ):
            raise ValueError("Module footprint must be a valid convex quadrilateral")
        vertices.setflags(write=False)
        object.__setattr__(self, "vertices_wgs84", vertices)


@dataclass(frozen=True)
class MountingParameters:
    """Assumed common table plane, preserving the supplied horizontal footprint.

    Azimuth is clockwise from local north, towards the module's facing direction.
    A table is raised until all corner, edge-midpoint and centre samples clear
    the terrain by ``minimum_clearance_m``. This is a sampling rule, not a
    continuous-clearance guarantee or a structural design. Tilt is absolute to
    horizontal, not added to the terrain slope. Zero is a flat-plane scenario.
    """

    tilt_degrees: float = 20.0
    azimuth_degrees: float = 0.0
    minimum_clearance_m: float = 0.8

    def __post_init__(self) -> None:
        for name, low, high in (
            ("tilt_degrees", 0, 80),
            ("azimuth_degrees", 0, 360),
            ("minimum_clearance_m", 0, 100),
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not np.isfinite(value) or not low <= value <= high:
                raise ValueError(f"{name} must be finite and in {low}..{high}")

    @property
    def gradient(self) -> FloatArray:
        azimuth = np.radians(self.azimuth_degrees)
        return -np.tan(np.radians(self.tilt_degrees)) * np.array([np.sin(azimuth), np.cos(azimuth)])


@dataclass(frozen=True)
class TriangleMesh:
    """Indexed triangles in local east, north, relative-up metres."""

    vertices_m: FloatArray
    triangles: IntArray


@dataclass(frozen=True)
class ModuleSurface:
    """A modelled plane, not an elevation inferred from imagery."""

    id: str
    table_id: str
    vertices_m: FloatArray
    terrain_at_vertices_m: FloatArray


@dataclass(frozen=True)
class PVSiteScene:
    """Terrain, supported module surfaces and explicit assumptions/rejections."""

    frame: LocalSiteFrame
    terrain: TriangleMesh
    vertical_datum: str
    modules: tuple[ModuleSurface, ...]
    table_mounting: dict[str, MountingParameters]
    rejected_modules: tuple[dict[str, str], ...]
    input_module_count: int
    bounds_wgs84: tuple[float, float, float, float]
    display_grid_shape: tuple[int, int]

    @property
    def module_mesh(self) -> TriangleMesh:
        vertices = np.concatenate([m.vertices_m for m in self.modules])
        triangles = np.array([[0, 1, 2], [0, 2, 3]], dtype=np.int64)[None, :, :]
        triangles = (triangles + 4 * np.arange(len(self.modules))[:, None, None]).reshape(-1, 3)
        return TriangleMesh(vertices, triangles)


def _terrain_mesh(
    terrain: ElevationGrid,
    frame: LocalSiteFrame,
    bounds: tuple[float, float, float, float],
    grid_shape: tuple[int, int],
) -> TriangleMesh:
    h, w = grid_shape
    if any(type(n) is not int or n < 2 for n in grid_shape) or h * w > 250_000:
        raise ValueError("Display grid must have 2+ rows/columns and at most 250000 vertices")
    west, south, east, north = bounds
    if (
        not np.isfinite(bounds).all()
        or not -180 <= west < east <= 180
        or not -90 < south < north < 90
    ):
        raise ValueError("Invalid geographic bounds; split antimeridian scenes")
    lon, lat = np.meshgrid(np.linspace(west, east, w), np.linspace(north, south, h))
    ll = np.column_stack([lon.ravel(), lat.ravel()])
    xy = frame.project(ll)
    z = terrain.sample(ll) - frame.elevation_origin_m
    grid = np.arange(h * w).reshape(h, w)
    tl, tr, bl, br = (
        grid[:-1, :-1].ravel(),
        grid[:-1, 1:].ravel(),
        grid[1:, :-1].ravel(),
        grid[1:, 1:].ravel(),
    )
    faces = np.concatenate([np.column_stack([tl, bl, tr]), np.column_stack([tr, bl, br])])
    valid = np.isfinite(z)
    faces = faces[valid[faces].all(axis=1)]
    if not len(faces):
        raise ValueError("No supported terrain triangles in the display bounds")
    remap = np.full(len(z), -1, dtype=np.int64)
    remap[valid] = np.arange(valid.sum())
    return TriangleMesh(np.column_stack([xy[valid], z[valid]]), remap[faces])


def build_pv_site_scene(
    footprints: Sequence[ModuleFootprint],
    terrain: ElevationGrid,
    *,
    frame: LocalSiteFrame,
    bounds_wgs84: tuple[float, float, float, float],
    mounting: MountingParameters | None = None,
    table_mounting: Mapping[str, MountingParameters] | None = None,
    display_grid_shape: tuple[int, int] = (60, 90),
    maximum_modules: int = 100_000,
) -> PVSiteScene:
    """Lift geographic candidates into common table planes above a real elevation grid.

    Original XY footprints are preserved. Slant dimensions change with assumed
    tilt; they are not inferred physical module dimensions. No modules, terrain
    gaps, structural details or additional site blocks are invented. Different
    table assumptions can be provided with ``table_mounting``. Missing terrain
    rejects individual footprints with reasons. All other invalid input fails.
    """
    if type(maximum_modules) is not int or maximum_modules < 1:
        raise ValueError("maximum_modules must be a positive integer")
    if not footprints or len(footprints) > maximum_modules:
        raise ValueError("Require 1..maximum_modules footprints")
    if len({f.id for f in footprints}) != len(footprints):
        raise ValueError("Module IDs must be unique")
    overrides = dict(table_mounting or {})
    if set(overrides) - {f.table_id for f in footprints}:
        raise ValueError("Unknown table IDs in mounting overrides")
    parameters = {
        f.table_id: overrides.get(f.table_id, mounting or MountingParameters()) for f in footprints
    }
    terrain_mesh = _terrain_mesh(terrain, frame, bounds_wgs84, display_grid_shape)
    groups: dict[str, list[tuple[ModuleFootprint, FloatArray, FloatArray, FloatArray]]] = {}
    rejected = []
    west, south, east, north = bounds_wgs84
    for footprint in footprints:
        ll = footprint.vertices_wgs84
        if np.any((ll[:, 0] < west) | (ll[:, 0] > east) | (ll[:, 1] < south) | (ll[:, 1] > north)):
            raise ValueError(f"Module {footprint.id} extends outside the display bounds")
        xy = frame.project(ll)
        area = np.sum(xy[:, 0] * np.roll(xy[:, 1], -1) - xy[:, 1] * np.roll(xy[:, 0], -1)) / 2
        if abs(area) < 1e-4:
            raise ValueError("Module footprint is degenerate in metric coordinates")
        if area < 0:
            xy = xy[::-1]
        samples = np.vstack([xy, (xy + np.roll(xy, -1, axis=0)) / 2, xy.mean(axis=0)])
        ground = terrain.sample(frame.unproject(samples))
        if not np.isfinite(ground).all():
            rejected.append(
                {
                    "id": footprint.id,
                    "table_id": footprint.table_id,
                    "reason": "missing_terrain_samples",
                }
            )
            continue
        groups.setdefault(footprint.table_id, []).append((footprint, xy, samples, ground))
    modules = []
    for table_id, items in groups.items():
        params = parameters[table_id]
        # A shared intercept keeps all cells in a table coplanar, rather than
        # resetting the assumed height independently for every module.
        intercept = (
            max(
                float(np.max(ground - samples @ params.gradient)) for _, _, samples, ground in items
            )
            + params.minimum_clearance_m
        )
        for footprint, xy, _, ground in items:
            z = xy @ params.gradient + intercept - frame.elevation_origin_m
            modules.append(
                ModuleSurface(
                    footprint.id,
                    table_id,
                    np.column_stack([xy, z]),
                    ground[:4] - frame.elevation_origin_m,
                )
            )
    if not modules:
        raise ValueError("No module footprints have supported terrain samples")
    return PVSiteScene(
        frame,
        terrain_mesh,
        terrain.vertical_datum,
        tuple(modules),
        parameters,
        tuple(rejected),
        len(footprints),
        bounds_wgs84,
        display_grid_shape,
    )
