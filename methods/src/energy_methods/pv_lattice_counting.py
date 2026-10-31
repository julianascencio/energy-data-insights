"""Orientation-aware counting of optically resolved PV frame lattices.

PCA rectification, autocorrelation and local contrast checks extend the original
horizontal-table counter. This is an experimental image method, not a trained
model, super-resolution procedure or verified engineering inventory.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from scipy import ndimage, signal

from energy_methods.pv_module_counting import ModuleCandidate

REFERENCE_IDS = ("cardoso_2024_pv_modules", "scipy_find_peaks")
type FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class LatticeCountingConfig:
    """Screening thresholds, not calibrated probabilities or known module counts.

    ``source_pixel_ratio`` is effective source sampling / finest delivered pixel
    sampling, at least one. It stops oversampled imagery passing the pitch gate.
    Colour is (B - R) / (R + G + B); contrast uses 0..1 RGB intensity.
    """

    minimum_chroma: float = 0.018
    minimum_component_pixels: int = 300
    minimum_aspect: float = 3.0
    frame_prominence: float = 0.015
    minimum_autocorrelation: float = 0.30
    minimum_source_pitch: float = 3.0
    maximum_pitch_pixels: int = 30
    source_pixel_ratio: float = 1.0
    spacing_tolerance: float = 0.30
    minimum_panel_fraction: float = 0.55
    minimum_cell_contrast: float = 0.003

    def __post_init__(self) -> None:
        for name in (
            "minimum_chroma",
            "frame_prominence",
            "minimum_autocorrelation",
            "spacing_tolerance",
            "minimum_panel_fraction",
            "minimum_cell_contrast",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not np.isfinite(value) or not 0 < value < 1:
                raise ValueError(f"{name} must be finite and between 0 and 1")
        for name, low, high in (
            ("minimum_component_pixels", 25, 4_000_000),
            ("maximum_pitch_pixels", 4, 100),
        ):
            value = getattr(self, name)
            if type(value) is not int or not low <= value <= high:
                raise ValueError(f"{name} must be an integer in {low}..{high}")
        for name, low, high in (
            ("minimum_aspect", 1.5, 100),
            ("minimum_source_pitch", 3, 30),
            ("source_pixel_ratio", 1, 100),
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not np.isfinite(value) or not low <= value <= high:
                raise ValueError(f"{name} must be finite and in {low}..{high}")


@dataclass(frozen=True)
class LatticeTable:
    """Image evidence for a rectified table, including all observed frame lines."""

    id: int
    bounds_xyxy: tuple[int, int, int, int]
    centre_xy: tuple[float, float]
    angle_degrees: float
    column_pitch_pixels: float
    row_pitch_pixels: float
    autocorrelation: float
    column_lines: tuple[float, ...]
    row_lines: tuple[float, ...]


@dataclass(frozen=True)
class LatticeCount:
    """Candidates and explicit rejected cells/tables; None means unresolved."""

    image_shape: tuple[int, int]
    config: LatticeCountingConfig
    tables: tuple[LatticeTable, ...]
    cells: tuple[ModuleCandidate, ...]
    rejected_tables: tuple[dict[str, Any], ...]

    @property
    def estimated_modules(self) -> int | None:
        return sum(c.status != "excluded" for c in self.cells) if self.tables else None

    def to_frame(self) -> pd.DataFrame:
        """Export accepted and rejected grid cells in original-image coordinates."""
        return pd.DataFrame(
            [
                {
                    "id": c.id,
                    "table": c.table,
                    "row": c.row,
                    "column": c.column,
                    "x_pixel": float(np.mean([p[0] for p in c.vertices_xy])),
                    "y_pixel": float(np.mean([p[1] for p in c.vertices_xy])),
                    "status": c.status,
                    "reasons": ";".join(c.reasons),
                    "panel_fraction": c.blue_fraction,
                }
                for c in self.cells
            ],
            columns=[
                "id",
                "table",
                "row",
                "column",
                "x_pixel",
                "y_pixel",
                "status",
                "reasons",
                "panel_fraction",
            ],
        )


def _observed_lines(profile: FloatArray, prominence: float) -> FloatArray:
    """Locate actual bright maxima, with quadratic subpixel refinement; never infill."""
    smooth = ndimage.gaussian_filter1d(profile, 0.7)
    peaks, _ = signal.find_peaks(smooth, prominence=prominence, distance=3)
    denominator = smooth[peaks - 1] - 2 * smooth[peaks] + smooth[peaks + 1]
    delta = np.divide(
        0.5 * (smooth[peaks - 1] - smooth[peaks + 1]),
        denominator,
        out=np.zeros(len(peaks)),
        where=np.abs(denominator) > 1e-12,
    )
    return peaks.astype(float) + np.clip(delta, -0.5, 0.5)


def _period(profile: FloatArray, cfg: LatticeCountingConfig) -> tuple[float, float]:
    """First supported autocorrelation maximum, rather than a multiple/harmonic."""
    residual = profile - ndimage.gaussian_filter1d(profile, cfg.maximum_pitch_pixels / 2)
    corr = signal.correlate(residual, residual, mode="full", method="fft")[len(profile) - 1 :]
    if corr[0] <= np.finfo(float).eps:
        raise ValueError("no_periodic_contrast")
    corr /= corr[0]
    peaks, _ = signal.find_peaks(corr, height=cfg.minimum_autocorrelation, prominence=0.05)
    peaks = peaks[(peaks >= 3) & (peaks <= min(cfg.maximum_pitch_pixels, len(profile) // 4))]
    if not len(peaks):
        raise ValueError("no_supported_period")
    peak = peaks[0]
    d = 0.5 * (corr[peak - 1] - corr[peak + 1]) / (corr[peak - 1] - 2 * corr[peak] + corr[peak + 1])
    return float(peak + np.clip(d, -0.5, 0.5)), float(corr[peak])


def count_lattice_pv_modules(
    rgb: NDArray[Any],
    site_mask: NDArray[np.bool_] | None = None,
    *,
    config: LatticeCountingConfig | None = None,
    maximum_pixels: int = 4_000_000,
    maximum_cells: int = 100_000,
) -> LatticeCount:
    """Find rotated blue/grey tables and count cells bounded by observed frame lines.

    The long-axis period is checked independently with autocorrelation. At least
    three transverse lines (two module rows) must be visible. Missing lines and
    irregular gaps are excluded; no lattice positions or table edges are invented.
    Interpolation only rectifies the input: it adds no optical information.

    Table ends, mounting hardware, glare and faint frames can reduce recall.
    A lattice can still be a cell pattern or another repeated structure: evaluate
    against image annotations and independent records before interpreting modules.
    """
    cfg = config or LatticeCountingConfig()
    for name, value in (("maximum_pixels", maximum_pixels), ("maximum_cells", maximum_cells)):
        if type(value) is not int or value < 1:
            raise ValueError(f"{name} must be a positive integer")
    image = np.asarray(rgb)
    if image.ndim != 3 or image.shape[2] != 3 or min(image.shape[:2]) < 16:
        raise ValueError("rgb must have shape H x W x 3 with H,W >= 16")
    if np.prod(image.shape[:2]) > maximum_pixels:
        raise ValueError("Image exceeds maximum_pixels")
    if image.dtype == np.uint8:
        image = image.astype(float) / 255
    elif np.issubdtype(image.dtype, np.floating):
        image = image.astype(float)
    else:
        raise ValueError("rgb must be uint8 or floating point in 0..1")
    if not np.isfinite(image).all() or image.min() < 0 or image.max() > 1:
        raise ValueError("rgb must be finite and in 0..1")
    h, w = image.shape[:2]
    scope = np.ones((h, w), dtype=bool) if site_mask is None else np.asarray(site_mask)
    if scope.dtype != np.bool_ or scope.shape != (h, w) or not scope.any():
        raise ValueError("site_mask must be nonempty boolean with matching image shape")
    grey = image.mean(axis=2)
    chroma = (image[..., 2] - image[..., 0]) / np.maximum(image.sum(axis=2), 1e-8)
    colour = (chroma > cfg.minimum_chroma) & scope
    segmented = ndimage.binary_closing(colour, iterations=2)
    segmented = ndimage.binary_opening(segmented) & scope
    labels, _ = ndimage.label(segmented)
    tables: list[LatticeTable] = []
    cells: list[ModuleCandidate] = []
    rejected: list[dict[str, Any]] = []
    for label, slices in enumerate(ndimage.find_objects(labels), 1):
        if slices is None:
            continue
        ys, xs = slices
        y, x = np.nonzero(labels[slices] == label)
        if len(x) < cfg.minimum_component_pixels:
            continue
        xy = np.column_stack([x + xs.start, y + ys.start]).astype(float)
        centre = xy.mean(axis=0)
        bounds = (xs.start, ys.start, xs.stop, ys.stop)
        try:
            if min(xs.start, ys.start, w - xs.stop, h - ys.stop) < 6:
                raise ValueError("clipped_image_edge")
            _, eigenvectors = np.linalg.eigh(np.cov(xy.T))
            along = eigenvectors[:, -1]
            if along[0] < 0:
                along = -along
            basis = np.column_stack([along, [-along[1], along[0]]])
            uv = (xy - centre) @ basis
            low, high = uv.min(axis=0), uv.max(axis=0)
            if (high[0] - low[0]) / max(high[1] - low[1], 1) < cfg.minimum_aspect:
                raise ValueError("unsupported_table_shape")
            a = np.arange(np.floor(low[0]) - 6, np.ceil(high[0]) + 7)
            b = np.arange(np.floor(low[1]) - 6, np.ceil(high[1]) + 7)
            uu, vv = np.meshgrid(a, b)
            source = np.stack([uu, vv], axis=-1) @ basis.T + centre
            if (
                source[..., 0].min() < 0
                or source[..., 0].max() >= w - 1
                or source[..., 1].min() < 0
                or source[..., 1].max() >= h - 1
            ):
                raise ValueError("clipped_rectified_patch")
            patch = ndimage.map_coordinates(grey, [source[..., 1], source[..., 0]], order=1)
            longitudinal = patch[8:-8].mean(axis=0)
            transverse = patch[:, 10:-10].mean(axis=1)
            px = _observed_lines(longitudinal, cfg.frame_prominence) + a[0]
            py = _observed_lines(transverse, cfg.frame_prominence) + b[0]
            if len(px) < 6 or len(py) < 3:
                raise ValueError("unresolved_frame_lines")
            dx, correlation = _period(longitudinal[6:-6], cfg)
            dy = float(np.median(np.diff(py)))
            if min(dx, dy) / cfg.source_pixel_ratio < cfg.minimum_source_pitch:
                raise ValueError("insufficient_source_pitch")
            if np.mean(np.abs(np.diff(px) / dx - 1) <= cfg.spacing_tolerance) < 0.6:
                raise ValueError("inconsistent_frame_period")
            if len(cells) + (len(px) - 1) * (len(py) - 1) > maximum_cells:
                raise OverflowError("Detected lattice exceeds maximum_cells")
        except ValueError as error:
            rejected.append({"bounds_xyxy": bounds, "reason": str(error)})
            continue
        table_id = len(tables) + 1
        tables.append(
            LatticeTable(
                table_id,
                bounds,
                (float(centre[0]), float(centre[1])),
                float(np.degrees(np.arctan2(along[1], along[0]))),
                dx,
                dy,
                correlation,
                tuple(px.tolist()),
                tuple(py.tolist()),
            )
        )
        for row, (v0, v1) in enumerate(pairwise(py), 1):
            for col, (u0, u1) in enumerate(pairwise(px), 1):
                local = np.array([[u0, v0], [u1, v0], [u1, v1], [u0, v1]])
                vertices = local @ basis.T + centre
                su, sv = np.meshgrid(np.linspace(u0, u1, 7), np.linspace(v0, v1, 7))
                samples = np.stack([su, sv], axis=-1) @ basis.T + centre
                coordinates = [samples[..., 1], samples[..., 0]]
                inside = ndimage.map_coordinates(scope, coordinates, order=0, mode="constant")
                colour_samples = ndimage.map_coordinates(chroma, coordinates, order=1)
                fraction = float((colour_samples[2:-2, 2:-2] > cfg.minimum_chroma / 2).mean())
                light = ndimage.map_coordinates(grey, coordinates, order=1)
                interior = light[2:-2, 2:-2].mean()
                contrast_x = light[2:-2, [0, -1]].mean() - interior
                contrast_y = light[[0, -1], 2:-2].mean() - interior
                reasons = []
                if not inside.all():
                    reasons.append("outside_site_mask")
                if abs((u1 - u0) / dx - 1) > cfg.spacing_tolerance:
                    reasons.append("unresolved_column_gap")
                if abs((v1 - v0) / dy - 1) > cfg.spacing_tolerance:
                    reasons.append("unresolved_row_gap")
                if min(u1 - u0, v1 - v0) / cfg.source_pixel_ratio < cfg.minimum_source_pitch:
                    reasons.append("insufficient_source_pitch")
                if fraction < cfg.minimum_panel_fraction:
                    reasons.append("insufficient_panel_colour")
                if min(contrast_x, contrast_y) < cfg.minimum_cell_contrast:
                    reasons.append("weak_local_frame_contrast")
                p0, p1, p2, p3 = ((float(p[0]), float(p[1])) for p in vertices)
                cells.append(
                    ModuleCandidate(
                        table_id,
                        row,
                        col,
                        (p0, p1, p2, p3),
                        "excluded" if reasons else "regular_candidate",
                        tuple(reasons),
                        fraction,
                    )
                )
    return LatticeCount((h, w), cfg, tuple(tables), tuple(cells), tuple(rejected))
