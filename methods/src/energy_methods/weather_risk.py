"""Soiling and snow shading indicators from Ascencio Vasquez (2021).

Thesis equations 3.2-3.4 and Tables 6.6-6.7. These are empirical screening
indicators, not event probabilities, structural snow loads or measured losses.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

REFERENCE_IDS = (
    "ascencio_vasquez_2021_thesis",
    "cordero_2018_soiling",
    "ryberg_freeman_2017_snow",
)
RISK_LABELS = ("No data", "Very Low", "Low", "Medium", "High", "Very High")
SOILING_EDGES = (0.05, 0.10, 0.20, 0.40)
SNOW_EDGES = (2.0, 4.0, 7.0, 10.0)


def _nonnegative(value: ArrayLike, name: str) -> NDArray[np.float64]:
    result = np.asarray(value, dtype=float)
    if np.isinf(result).any() or np.any(result < 0):
        raise ValueError(f"{name} must be nonnegative and finite, or NaN for missing data")
    return result


def soiling_rate_from_aod(aod550: ArrayLike) -> NDArray[np.float64]:
    """Thesis Eq. 3.2: daily soiling-rate indicator in numerical %/day.

    Use dimensionless, annual-mean total AOD at 550 nm. The underlying Chilean
    study relates annual averages, not individual dust events. For AOD <= 0.106
    use 0.648*AOD; above it use 6.63*AOD-0.63. Zero and exact equality close gaps
    left in the printed inequalities. The small branch discontinuity is retained.
    This does not include rain/manual cleaning or estimate annual energy loss.
    """
    aod = _nonnegative(aod550, "AOD550")
    with np.errstate(over="raise"):
        try:
            result = np.where(aod <= 0.106, 0.648 * aod, 6.63 * aod - 0.63)
        except FloatingPointError as error:
            raise ValueError("AOD exceeds the numerical range of the soiling equation") from error
    return np.asarray(result, dtype=float)


def snow_loss_from_exposure(snow_depth_sum_cm_hours: ArrayLike) -> NDArray[np.float64]:
    """Thesis Eqs. 3.3-3.4: annual snow energy-loss indicator, numerical percent.

    Input is the annual sum of hourly PHYSICAL ground snow depths in cm, with
    each sample weighted by one hour (cm h). This is not snowfall, maximum depth,
    or snow water equivalent. Figure 3.4 supplies the cm convention and describes
    fixed modules at tilt equal to latitude. The log uses the numerical value
    relative to 1 cm h. For exposure <= 1 cm h return zero, an explicit extension
    of the unspecified low domain; log=5 belongs to the lower branch. Retain the
    published discontinuity and unbounded polynomial rather than silently clip
    extrapolations to 100%. NaN stays missing. No mounting-specific SAM simulation
    or independent global validation is implied.
    """
    exposure = _nonnegative(snow_depth_sum_cm_hours, "Annual snow exposure")
    log_depth = np.log(np.maximum(exposure, 1.0))
    loss = np.where(
        log_depth <= 5,
        0.0263 * log_depth,
        0.25 * log_depth**2 - 2.41 * log_depth + 6,
    )
    return np.asarray(loss, dtype=float)


def _classes(values: ArrayLike, edges: tuple[float, ...]) -> NDArray[np.uint8]:
    values = _nonnegative(values, "Risk indicator")
    return np.asarray(
        np.where(np.isnan(values), 0, np.searchsorted(edges, values, side="left") + 1),
        dtype=np.uint8,
    )


def soiling_risk_classes(rate_percent_day: ArrayLike) -> NDArray[np.uint8]:
    """Table 6.7 classes 1-5 at 0.05, 0.10, 0.20, 0.40 %/day; 0 is missing.

    Upper edges are inclusive, explicitly resolving omitted equalities.
    """
    return _classes(rate_percent_day, SOILING_EDGES)


def snow_risk_classes(annual_loss_percent: ArrayLike) -> NDArray[np.uint8]:
    """Table 6.6 classes 1-5 at 2, 4, 7, 10 percent; 0 is missing.

    Upper edges are inclusive. Class 1 includes zero AND small nonzero loss.
    """
    return _classes(annual_loss_percent, SNOW_EDGES)
