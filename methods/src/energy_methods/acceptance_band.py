"""Publication-based two-stage acceptance bands, DOI 10.3390/en13092166.

This is a maintained reimplementation of the previous ASVA method, not original
author software. The paper's inconsistent printed distance/roughness expressions
are resolved explicitly in README.md. Fit receives training data only. Bounds
depend on irradiance alone and never inspect the observations being evaluated.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import NormalDist
from typing import Literal

import numpy as np
from numpy.typing import ArrayLike

from energy_methods._arrays import BoolArray, FloatArray, IntArray, aligned, immutable, vector


class BandFitUnavailable(ValueError):
    """Insufficient scientific support; callers must not silently skip the filter."""


@dataclass(frozen=True, slots=True)
class AcceptanceBandConfig:
    """Numerical conventions that were not fully specified in the publication."""

    bin_width_wm2: float = 50.0
    irradiance_max_wm2: float = 1300.0
    min_samples_per_bin: int = 10
    min_supported_bins: int = 7
    accuracy_level: Literal["low", "medium", "high"] = "low"

    def __post_init__(self) -> None:
        if not 0 < self.bin_width_wm2 <= self.irradiance_max_wm2 < np.inf:
            raise ValueError("Finite positive bin width and irradiance maximum are required")
        if self.min_samples_per_bin < 2 or self.min_supported_bins < 5:
            raise ValueError("At least two samples per bin and five supported bins are required")
        if self.accuracy_level not in {"low", "medium", "high"}:
            raise ValueError("Unknown accuracy level")


DEFAULT_CONFIG = AcceptanceBandConfig()


def _bin_ids(irradiance: FloatArray, config: AcceptanceBandConfig) -> IntArray:
    valid = np.isfinite(irradiance) & (irradiance >= 0) & (irradiance <= config.irradiance_max_wm2)
    ids = np.floor(np.where(valid, irradiance, -config.bin_width_wm2) / config.bin_width_wm2)
    result = ids.astype(np.int64)
    result[irradiance == config.irradiance_max_wm2] = (
        int(np.ceil(config.irradiance_max_wm2 / config.bin_width_wm2)) - 1
    )
    return result


def _quartic(x: FloatArray, y: FloatArray) -> FloatArray:
    if len(x) < 5 or len(np.unique(x)) < 5:
        raise BandFitUnavailable("A quartic needs at least five distinct retained bins")
    design = np.polynomial.polynomial.polyvander(x, 4)
    coefficients, _, rank, _ = np.linalg.lstsq(design, y, rcond=None)
    if rank < 5 or not np.isfinite(coefficients).all():
        raise BandFitUnavailable("Rank-deficient or nonfinite quartic fit")
    return immutable(coefficients)


@dataclass(frozen=True, slots=True)
class FittedAcceptanceBand:
    """Frozen curves with an explicit populated-bin and joint-curve support domain."""

    config: AcceptanceBandConfig
    lower_coefficients: FloatArray
    center_coefficients: FloatArray
    upper_coefficients: FloatArray
    power_scale_mwh: float
    support_wm2: tuple[float, float]
    populated_bin_ids: tuple[int, ...]
    training_rows: int
    fitted_bins: int

    def to_dict(self) -> dict[str, object]:
        """Export portable coefficients with source and support provenance."""
        return {
            "method": "ascencio_vasquez_2020_two_stage_band",
            "source_doi": "10.3390/en13092166",
            "config": asdict(self.config),
            "lower_coefficients": self.lower_coefficients.tolist(),
            "center_coefficients": self.center_coefficients.tolist(),
            "upper_coefficients": self.upper_coefficients.tolist(),
            "coefficient_order": "ascending",
            "power_scale_mwh": self.power_scale_mwh,
            "support_wm2": list(self.support_wm2),
            "populated_bin_ids": list(self.populated_bin_ids),
            "training_rows": self.training_rows,
            "fitted_bins": self.fitted_bins,
            "original_author_code": False,
        }

    def bounds(self, poa_wm2: ArrayLike) -> tuple[FloatArray, FloatArray]:
        """NaN outside fitted bins or for crossing bounds; never extrapolate or swap."""
        irradiance = vector(poa_wm2, "poa_wm2")
        lower, upper = np.full(len(irradiance), np.nan), np.full(len(irradiance), np.nan)
        valid = np.isfinite(irradiance) & (irradiance > 0)
        valid &= (irradiance >= self.support_wm2[0]) & (irradiance <= self.support_wm2[1])
        valid &= np.isin(_bin_ids(irradiance, self.config), self.populated_bin_ids)
        index = np.flatnonzero(valid)
        x = irradiance[index] / 1000.0
        low = np.polynomial.polynomial.polyval(x, self.lower_coefficients) * self.power_scale_mwh
        high = np.polynomial.polynomial.polyval(x, self.upper_coefficients) * self.power_scale_mwh
        ordered = np.isfinite(low) & np.isfinite(high) & (low <= high)
        lower[index[ordered]], upper[index[ordered]] = low[ordered], high[ordered]
        return lower, upper

    def mask(self, poa_wm2: ArrayLike, actual_mwh: ArrayLike) -> BoolArray:
        """Inclusive physical and band boundaries; unsupported observations fail."""
        irradiance, actual = aligned(poa_wm2, actual_mwh)
        lower, upper = self.bounds(irradiance)
        return np.isfinite(actual) & (actual >= 0) & (actual >= lower) & (actual <= upper)


def fit_acceptance_band(
    poa_wm2: ArrayLike,
    actual_mwh: ArrayLike,
    config: AcceptanceBandConfig = DEFAULT_CONFIG,
) -> FittedAcceptanceBand:
    """Fit Gaussian within-bin percentiles and separately trimmed quartic curves.

    Supply only the chronological training partition. POA is the published
    independent variable; substituting GHI is a separate, explicitly labelled
    scientific adaptation and is not performed here. Hourly interval energy
    equals mean MW numerically only for one elapsed hour.
    """
    irradiance, actual = aligned(poa_wm2, actual_mwh)
    valid = np.isfinite(irradiance) & np.isfinite(actual) & (irradiance > 0) & (actual >= 0)
    valid &= irradiance <= config.irradiance_max_wm2
    positive = actual[valid & (actual > 0)]
    if not len(positive):
        raise BandFitUnavailable("Positive training generation is required")
    scale = float(np.quantile(positive, 0.95, method="linear"))
    normalized = actual / scale
    ids = _bin_ids(irradiance, config)
    count = int(np.ceil(config.irradiance_max_wm2 / config.bin_width_wm2))
    probability = 0.2 if config.accuracy_level == "low" else 0.05
    z = NormalDist().inv_cdf(1.0 - probability)
    populated, centers, lows, medians, highs = [], [], [], [], []
    for bin_id in range(count):
        values = normalized[valid & (ids == bin_id)]
        if len(values) < config.min_samples_per_bin:
            continue
        mu, sigma = float(np.mean(values)), float(np.std(values, ddof=0))
        right = min((bin_id + 1) * config.bin_width_wm2, config.irradiance_max_wm2)
        populated.append(bin_id)
        centers.append((bin_id * config.bin_width_wm2 + right) / 2000.0)
        lows.append(mu - z * sigma)
        medians.append(mu)
        highs.append(mu + z * sigma)
    if len(populated) < config.min_supported_bins:
        raise BandFitUnavailable("Too few populated irradiance bins")
    x, ql, qm, qu = (np.asarray(v, dtype=np.float64) for v in (centers, lows, medians, highs))
    lookup = {key: index for index, key in enumerate(populated)}
    roughness = np.full(len(populated), np.nan)
    for i, bin_id in enumerate(populated):
        terms = []
        for offset in (-2, -1, 1, 2):
            if bin_id + offset in lookup:
                delta = abs(float(qm[i] - qm[lookup[bin_id + offset]]))
                terms.append(delta**2 if abs(offset) == 2 else delta)
        if terms:
            roughness[i] = sum(terms)
    finite = np.isfinite(roughness)
    if int(finite.sum()) < 5:
        raise BandFitUnavailable("Too few observed neighboring bins for roughness screening")
    center_keep = finite & (roughness <= np.quantile(roughness[finite], 0.9, method="linear"))
    center = _quartic(x[center_keep], qm[center_keep])
    center_values = np.polynomial.polynomial.polyval(x, center)
    domain = (float(x[center_keep].min()), float(x[center_keep].max()))
    eligible = (x >= domain[0]) & (x <= domain[1])
    low_distance, high_distance = ql - center_values, qu - center_values
    low_threshold = float(np.mean(low_distance[eligible])) + NormalDist().inv_cdf(0.25) * float(
        np.std(low_distance[eligible], ddof=0)
    )
    high_threshold = float(np.mean(high_distance[eligible])) + NormalDist().inv_cdf(0.75) * float(
        np.std(high_distance[eligible], ddof=0)
    )
    low_keep, high_keep = (
        eligible & (low_distance >= low_threshold),
        eligible & (high_distance <= high_threshold),
    )
    lower, upper = _quartic(x[low_keep], ql[low_keep]), _quartic(x[high_keep], qu[high_keep])
    support = (
        1000.0 * max(domain[0], float(x[low_keep].min()), float(x[high_keep].min())),
        1000.0 * min(domain[1], float(x[low_keep].max()), float(x[high_keep].max())),
    )
    if support[0] >= support[1]:
        raise BandFitUnavailable("The three curves have no common fitted domain")
    fitted = FittedAcceptanceBand(
        config,
        lower,
        center,
        upper,
        scale,
        support,
        tuple(populated),
        int(valid.sum()),
        len(populated),
    )
    low, high = fitted.bounds(irradiance)
    if not np.any(np.isfinite(low) & np.isfinite(high)):
        raise BandFitUnavailable("No finite ordered bounds on the training observations")
    return fitted


def performance_ratio(
    actual_mwh: ArrayLike,
    poa_wm2: ArrayLike,
    dc_capacity_mw: ArrayLike,
    interval_hours: ArrayLike = 1.0,
) -> FloatArray:
    """E_AC / (P_DC,STC * POA/1000 * hours); caller must qualify DC provenance.

    Missing, nonpositive irradiance/capacity/duration or negative energy gives
    NaN. AC capacity and GHI are not silently substituted.
    """
    actual, poa, capacity, hours = np.broadcast_arrays(
        *[
            np.asarray(a, dtype=np.float64)
            for a in (
                actual_mwh,
                poa_wm2,
                dc_capacity_mw,
                interval_hours,
            )
        ]
    )
    valid = np.isfinite(actual) & np.isfinite(poa) & np.isfinite(capacity) & np.isfinite(hours)
    valid &= (actual >= 0) & (poa > 0) & (capacity > 0) & (hours > 0)
    result = np.full(actual.shape, np.nan)
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        denominator = capacity * poa / 1000.0 * hours
        np.divide(actual, denominator, out=result, where=valid & np.isfinite(denominator))
    result[~np.isfinite(result)] = np.nan
    return result


def pr_acceptance_mask(pr: ArrayLike, lower: float = 0.5, upper: float = 1.0) -> BoolArray:
    """Inclusive 50-100% gate by default; missing PR is unknown, not accepted."""
    if not np.isfinite(lower) or not np.isfinite(upper) or lower > upper:
        raise ValueError("PR bounds must be finite and ordered")
    values = np.asarray(pr, dtype=np.float64)
    return np.isfinite(values) & (values >= lower) & (values <= upper)
