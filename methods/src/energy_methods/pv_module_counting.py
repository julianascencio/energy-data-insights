"""Experimental counting of resolved, regular PV module grids in RGB orthophotos.

Colour segmentation finds candidate tables; brightness profiles find frame lines.
Every returned cell is an image-derived candidate, never a verified module or a
capacity measurement. The detector is intended for approximately horizontal,
blue/grey, regularly framed arrays. Unresolved grids return no estimate, not zero.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import pairwise
from typing import Any, Literal

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from scipy import ndimage, signal

REFERENCE_IDS = ("grimaccia_2017_pv_mapping", "scipy_find_peaks")
type FloatArray = NDArray[np.float64]
type XY = tuple[float, float]


@dataclass(frozen=True)
class ModuleCountingConfig:
    """Explicit image-space screening parameters, not trained/calibrated probabilities.

    RGB thresholds use 0..1 intensity; lengths/areas use delivered image pixels.
    Parameters need reassessment for different colours, rendering and resolution.
    """

    blue_excess: float = 0.025
    minimum_brightness: float = 0.25
    minimum_table_pixels: int = 500
    minimum_table_aspect: float = 2.0
    maximum_slope: float = 0.12
    column_prominence: float = 0.025
    row_prominence: float = 0.015
    minimum_pitch_pixels: float = 3.0
    spacing_tolerance: float = 0.30
    minimum_blue_fraction: float = 0.45

    def __post_init__(self) -> None:
        for name in (
            "blue_excess",
            "minimum_brightness",
            "column_prominence",
            "row_prominence",
            "spacing_tolerance",
            "minimum_blue_fraction",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not np.isfinite(value) or not 0 < value < 1:
                raise ValueError(f"{name} must be finite and between 0 and 1")
        if type(self.minimum_table_pixels) is not int or self.minimum_table_pixels < 25:
            raise ValueError("minimum_table_pixels must be an integer >= 25")
        for name, low, high in (
            ("minimum_table_aspect", 1, 100),
            ("maximum_slope", 0, 0.3),
            ("minimum_pitch_pixels", 2.5, 100),
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not np.isfinite(value) or not low <= value <= high:
                raise ValueError(f"{name} must be finite and in {low}..{high}")


@dataclass(frozen=True)
class ModuleCandidate:
    """A quadrilateral in pixel-centre coordinates (x right, y down).

    IDs describe this image/grid run, not persistent engineering asset IDs.
    Review flags express screening decisions, not detection confidence scores.
    """

    table: int
    row: int
    column: int
    vertices_xy: tuple[XY, XY, XY, XY]
    status: Literal["regular_candidate", "review_candidate", "excluded"]
    reasons: tuple[str, ...]
    blue_fraction: float

    @property
    def id(self) -> str:
        return f"t{self.table:02d}-r{self.row:02d}-c{self.column:03d}"


@dataclass(frozen=True)
class TableGrid:
    """Detected table geometry and frame pitch, in delivered image pixels."""

    id: int
    bounds_xyxy: tuple[int, int, int, int]
    slope: float
    rows: int
    columns: int
    column_pitch_pixels: float
    row_pitch_pixels: float


@dataclass(frozen=True)
class ModuleCount:
    """Candidate inventory with explicit unresolved/excluded areas.

    ``estimated_modules`` includes review candidates. It is not a validated
    inventory. A missing estimate means no grid resolved, not an empty PV site.
    """

    image_shape: tuple[int, int]
    config: ModuleCountingConfig
    tables: tuple[TableGrid, ...]
    cells: tuple[ModuleCandidate, ...]
    rejected_tables: tuple[dict[str, Any], ...]

    @property
    def estimated_modules(self) -> int | None:
        return sum(cell.status != "excluded" for cell in self.cells) if self.tables else None

    @property
    def review_candidates(self) -> int:
        return sum(cell.status == "review_candidate" for cell in self.cells)

    @property
    def regular_candidates(self) -> int:
        return sum(cell.status == "regular_candidate" for cell in self.cells)

    def to_frame(self) -> pd.DataFrame:
        """Return cells, including exclusions and their reasons, for CSV review."""
        rows = []
        for cell in self.cells:
            xy = np.asarray(cell.vertices_xy)
            rows.append(
                {
                    "id": cell.id,
                    "table": cell.table,
                    "row": cell.row,
                    "column": cell.column,
                    "x_pixel": float(xy[:, 0].mean()),
                    "y_pixel": float(xy[:, 1].mean()),
                    "status": cell.status,
                    "reasons": ";".join(cell.reasons),
                    "blue_fraction": cell.blue_fraction,
                }
            )
        return pd.DataFrame(
            rows,
            columns=[
                "id",
                "table",
                "row",
                "column",
                "x_pixel",
                "y_pixel",
                "status",
                "reasons",
                "blue_fraction",
            ],
        )


def _robust_edge(x: FloatArray, y: FloatArray) -> FloatArray:
    use = np.ones(len(x), dtype=bool)
    trim = max(2, len(x) // 20)
    use[:trim] = use[-trim:] = False
    if use.sum() < 5:
        raise ValueError("too_few_edge_pixels")
    for _ in range(5):
        coefficients = np.polyfit(x[use], y[use], 1)
        residual = y - np.polyval(coefficients, x)
        keep = use & (np.abs(residual) < max(1.5, 3 * np.median(np.abs(residual[use]))))
        if keep.sum() < 5:
            break
        use = keep
    return coefficients


def _frame_lines(profile: FloatArray, prominence: float, distance: int) -> NDArray[np.intp]:
    detrended = profile - ndimage.gaussian_filter1d(profile, 5)
    peaks, _ = signal.find_peaks(detrended, distance=distance, prominence=prominence, height=0.005)
    return peaks


def count_regular_pv_modules(
    rgb: NDArray[Any],
    site_mask: NDArray[np.bool_] | None = None,
    *,
    config: ModuleCountingConfig | None = None,
    maximum_pixels: int = 4_000_000,
    maximum_cells: int = 100_000,
) -> ModuleCount:
    """Detect tables and count visible grid cells with no hand-entered row counts.

    Input is H x W x 3 uint8 RGB or finite float RGB in 0..1. A boolean mask defines
    the scope; cells crossing it are excluded. No image rescaling is performed.
    Per-table shear correction samples original intensities for frame profiles;
    it adds no optical detail. Narrow seams/irregular pitches and weak colour
    support are flagged for review; unsupported and clipped tables are recorded.

    The method cannot distinguish module frames from cell patterns in arbitrary
    imagery. Check ground scale, imagery and independent plant records. It does
    not infer missing modules, purchase imagery, train a model or prove absence.
    """
    cfg = config or ModuleCountingConfig()
    for name, value in (("maximum_pixels", maximum_pixels), ("maximum_cells", maximum_cells)):
        if type(value) is not int or value < 1:
            raise ValueError(f"{name} must be a positive integer")
    image = np.asarray(rgb)
    if image.ndim != 3 or image.shape[2] != 3 or min(image.shape[:2]) < 8:
        raise ValueError("rgb must have shape H x W x 3 with H,W >= 8")
    if image.shape[0] * image.shape[1] > maximum_pixels:
        raise ValueError("Image exceeds maximum_pixels")
    if image.dtype == np.uint8:
        image = image.astype(np.float64) / 255
    elif not np.issubdtype(image.dtype, np.floating):
        raise ValueError("rgb must be uint8 or floating point in 0..1")
    else:
        image = image.astype(np.float64)
    if not np.isfinite(image).all() or image.min() < 0 or image.max() > 1:
        raise ValueError("rgb must be finite and in 0..1")
    h, w = image.shape[:2]
    scope = np.ones((h, w), dtype=bool) if site_mask is None else np.asarray(site_mask)
    if scope.dtype != np.bool_ or scope.shape != (h, w):
        raise ValueError("site_mask must be boolean with the same height and width")
    if not scope.any():
        raise ValueError("site_mask is empty")
    grey = image.mean(axis=2)
    blue = (
        (image[..., 2] - image[..., 0] > cfg.blue_excess)
        & (image[..., 1] > image[..., 0])
        & (grey > cfg.minimum_brightness)
    )
    # Presence screening is looser than table segmentation: bright frames and
    # dark module interiors must not become invented missing modules.
    presence = (
        (image[..., 2] - image[..., 0] > cfg.blue_excess / 3)
        & (image[..., 1] >= image[..., 0])
        & (grey > cfg.minimum_brightness / 2)
    )
    segmented = ndimage.binary_closing(blue & scope, structure=np.ones((3, 7)))
    segmented = ndimage.binary_opening(segmented, structure=np.ones((3, 3)))
    segmented = ndimage.binary_fill_holes(segmented) & scope
    labels, _ = ndimage.label(segmented)
    tables: list[TableGrid] = []
    cells: list[ModuleCandidate] = []
    rejected: list[dict[str, Any]] = []
    for label, slices in enumerate(ndimage.find_objects(labels), start=1):
        if slices is None:
            continue
        ys, xs = slices
        component = labels[slices] == label
        if int(component.sum()) < cfg.minimum_table_pixels:
            continue
        bounds = (xs.start, ys.start, xs.stop, ys.stop)
        try:
            if (xs.stop - xs.start) / (ys.stop - ys.start) < cfg.minimum_table_aspect:
                raise ValueError("unsupported_table_shape")
            if not (xs.start >= 5 and xs.stop + 6 < w and ys.start >= 5 and ys.stop + 8 < h):
                raise ValueError("clipped_image_edge")
            x = np.arange(xs.start, xs.stop, dtype=float)
            tops = np.argmax(component, axis=0).astype(float) + ys.start
            bottoms = component.shape[0] - 1 - np.argmax(component[::-1], axis=0) + ys.start
            edge = _robust_edge(x, tops)
            if abs(edge[0]) > cfg.maximum_slope + 1e-10:
                raise ValueError("unsupported_orientation")
            x = np.arange(xs.start - 5, xs.stop + 6, dtype=float)
            offsets = np.arange(-5, round(float(np.median(bottoms - tops))) + 8, dtype=float)
            y = np.polyval(edge, x)[None, :] + offsets[:, None]
            if y.min() < 0 or y.max() >= h:
                raise ValueError("clipped_profile")
            patch = ndimage.map_coordinates(grey, [y, np.broadcast_to(x, y.shape)], order=1)
            px = _frame_lines(patch[5:-5].mean(axis=0), cfg.column_prominence, 3)
            py = _frame_lines(patch[:, 10:-10].mean(axis=1), cfg.row_prominence, 2)
            if min(len(px), len(py)) < 4:
                raise ValueError("unresolved_frame_lines")
            dx, dy = float(np.median(np.diff(x[px]))), float(np.median(np.diff(offsets[py])))
            if min(dx, dy) < cfg.minimum_pitch_pixels:
                raise ValueError("insufficient_pixel_pitch")
            if len(cells) + (len(px) - 1) * (len(py) - 1) > maximum_cells:
                raise OverflowError("Detected grid exceeds maximum_cells")
        except ValueError as error:
            rejected.append({"bounds_xyxy": bounds, "reason": str(error)})
            continue
        table_id = len(tables) + 1
        tables.append(TableGrid(table_id, bounds, float(edge[0]), len(py) - 1, len(px) - 1, dx, dy))
        for row, (iy0, iy1) in enumerate(pairwise(py), 1):
            y0, y1 = offsets[iy0], offsets[iy1]
            for col, (ix0, ix1) in enumerate(pairwise(px), 1):
                x0, x1 = x[ix0], x[ix1]
                vertices = (
                    (float(x0), float(np.polyval(edge, x0) + y0)),
                    (float(x1), float(np.polyval(edge, x1) + y0)),
                    (float(x1), float(np.polyval(edge, x1) + y1)),
                    (float(x0), float(np.polyval(edge, x0) + y1)),
                )
                sx, sy = np.meshgrid(np.linspace(x0, x1, 5), np.linspace(y0, y1, 5))
                sy = sy + np.polyval(edge, sx)
                scope_values = ndimage.map_coordinates(scope, [sy, sx], order=0, mode="constant")
                blue_values = ndimage.map_coordinates(
                    presence, [sy[1:-1, 1:-1], sx[1:-1, 1:-1]], order=0, mode="constant"
                )
                fraction = float(blue_values.mean())
                reasons = []
                status: Literal["regular_candidate", "review_candidate", "excluded"]
                status = "regular_candidate"
                if not scope_values.all():
                    status = "excluded"
                    reasons.append("outside_site_mask")
                elif fraction < cfg.minimum_blue_fraction / 2:
                    status = "excluded"
                    reasons.append("insufficient_panel_colour")
                else:
                    if fraction < cfg.minimum_blue_fraction:
                        reasons.append("weak_panel_colour")
                    if abs((x1 - x0) / dx - 1) > cfg.spacing_tolerance:
                        reasons.append("irregular_column_spacing")
                    if abs((y1 - y0) / dy - 1) > cfg.spacing_tolerance:
                        reasons.append("irregular_row_spacing")
                    if reasons:
                        status = "review_candidate"
                cells.append(
                    ModuleCandidate(table_id, row, col, vertices, status, tuple(reasons), fraction)
                )
    return ModuleCount((h, w), cfg, tuple(tables), tuple(cells), tuple(rejected))


def module_candidates_geojson(
    result: ModuleCount, bounds_wgs84: tuple[float, float, float, float]
) -> dict[str, Any]:
    """Export all cells and review/exclusion flags from a north-up EPSG:4326 image.

    Bounds are outer image edges, west/south/east/north. Pixel centres use a
    half-pixel offset. These are image georeferences, not surveyed asset positions.
    """
    west, south, east, north = bounds_wgs84
    if not np.isfinite(bounds_wgs84).all() or not (
        -180 <= west < east <= 180 and -90 <= south < north <= 90
    ):
        raise ValueError("bounds_wgs84 must be valid west,south,east,north coordinates")
    h, w = result.image_shape
    features = []
    for cell in result.cells:
        ring = [
            [west + (x + 0.5) / w * (east - west), north - (y + 0.5) / h * (north - south)]
            for x, y in cell.vertices_xy
        ]
        features.append(
            {
                "type": "Feature",
                "id": cell.id,
                "geometry": {"type": "Polygon", "coordinates": [[*ring, ring[0]]]},
                "properties": {
                    "table": cell.table,
                    "row": cell.row,
                    "column": cell.column,
                    "status": cell.status,
                    "reasons": list(cell.reasons),
                    "blue_fraction": cell.blue_fraction,
                },
            }
        )
    return {
        "type": "FeatureCollection",
        "features": features,
        "properties": {
            "estimated_modules": result.estimated_modules,
            "interpretation": "Unvalidated image-grid candidates; not surveyed modules",
            "parameters": asdict(result.config),
        },
    }
