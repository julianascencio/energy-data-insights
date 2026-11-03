"""Long-horizon PV power retention, following selected MAPLE equations (2026).

These deterministic power fractions are not survival probabilities. Equations
8, 10 and 13 are implemented independently; this is not the full MAPLE package.
Rates and time steps must use reciprocal units (here years and 1/year).
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

REFERENCE_IDS = ("ravindrababu_2026_maple",)


def _finite(values: ArrayLike, name: str) -> NDArray[np.float64]:
    array = np.asarray(values, dtype=float)
    if not array.size or not np.isfinite(array).all():
        raise ValueError(f"{name} must be nonempty and finite")
    return array


def sigmoid_power(exposure: ArrayLike, *, shape: float) -> NDArray[np.float64]:
    """Eq. 10: (1+exp(-B))/(1+exp(exposure-B)), with dimensionless B=shape.

    For constant stress, exposure = rate * age. For varying rates and constant
    B, exposure is the accumulated rate*time, not the latest rate*total age.
    The log-domain evaluation avoids exponential overflow and gives P(0)=1.
    """
    dose = _finite(exposure, "exposure")
    if np.any(dose < 0) or not np.isfinite(shape) or shape < 0:
        raise ValueError("Exposure and shape must be nonnegative; shape must be finite")
    return np.exp(np.logaddexp(0, -shape) - np.logaddexp(0, dose - shape))


def sigmoid_exposure(retained_power: float, *, shape: float) -> float:
    """Inverse of Eq. 10; exposure required to reach a given power fraction."""
    if not np.isfinite(retained_power) or not 0 < retained_power <= 1:
        raise ValueError("retained_power must be in (0, 1]")
    sigmoid_power(0, shape=shape)
    if retained_power == 1:
        return 0.0
    return float(np.logaddexp(0, shape + np.log1p(-retained_power)) - np.log(retained_power))


def equivalent_time_power(
    step_years: ArrayLike, rate_per_year: ArrayLike, *, shape: ArrayLike
) -> NDArray[np.float64]:
    """Eqs. 10/13: preserve prior damage across piecewise-constant stresses.

    Return initial power 1 followed by the power at every interval end. Time
    steps are a positive 1-D array; rate and B are scalars or arrays of exactly
    that shape. At each step, invert the CURRENT sigmoid at the PREVIOUS power,
    then advance by rate*step. This permits B to change as well as the rate.
    A zero rate pauses damage. No healing, replacement or interaction is assumed.
    Log power is carried internally to avoid losing history to underflow.
    """
    dt = _finite(step_years, "step_years")
    if dt.ndim != 1 or np.any(dt <= 0):
        raise ValueError("step_years must be a positive 1-D array")
    parameters = []
    for value, name in ((rate_per_year, "rate_per_year"), (shape, "shape")):
        array = _finite(value, name)
        if array.ndim != 0 and array.shape != dt.shape:
            raise ValueError(f"{name} must be scalar or match step_years")
        if np.any(array < 0):
            raise ValueError(f"{name} must be nonnegative")
        parameters.append(np.broadcast_to(array, dt.shape))
    rates, shapes = parameters
    with np.errstate(over="ignore"):
        increments = rates * dt
        total = np.sum(increments)
    if not np.isfinite(total):
        raise ValueError("Accumulated exposure exceeds the finite numerical range")
    power = np.ones(len(dt) + 1)
    log_power = 0.0
    dose = 0.0
    previous_shape = shapes[0]
    for i, (increment, b) in enumerate(zip(increments, shapes, strict=True), 1):
        if increment > 0:
            # Algebraic inverse avoids log(expm1(0)) when P=1 and B is large.
            # Carry exposure directly for unchanged B, including an induction
            # period whose power loss is smaller than floating-point precision.
            if b != previous_shape:
                dose = (
                    0.0
                    if log_power == 0
                    else np.logaddexp(0, b + np.log(-np.expm1(log_power))) - log_power
                )
            dose += increment
            log_power = np.logaddexp(0, -b) - np.logaddexp(0, dose - b)
            previous_shape = b
        power[i] = np.exp(log_power)
    return power


def independent_mode_power(mode_power: ArrayLike) -> NDArray[np.float64]:
    """Eq. 8: product across rows of a (modes, times) power-fraction matrix.

    Assumes independent mode effects. Do not multiply a system-level total loss
    curve by its constituent modes: that would count the same damage twice.
    """
    values = _finite(mode_power, "mode_power")
    if values.ndim != 2 or np.any((values < 0) | (values > 1)):
        raise ValueError("mode_power must be a 2-D matrix with entries in [0, 1]")
    return np.prod(values, axis=0)


def threshold_crossing(
    age_years: ArrayLike, power: ArrayLike, *, threshold: float = 0.8
) -> float | None:
    """First threshold crossing by linear interpolation of monotone samples.

    Return None when the threshold is not reached inside the supplied horizon.
    That is a censored projection, not an infinite lifetime. A first point at or
    below threshold returns its age; the actual earlier crossing is unknown.
    """
    age, retained = _finite(age_years, "age_years"), _finite(power, "power")
    if age.ndim != 1 or age.shape != retained.shape:
        raise ValueError("Age and power must be matching 1-D arrays")
    if np.any(age < 0) or np.any(np.diff(age) <= 0):
        raise ValueError("Ages must be nonnegative and strictly increasing")
    if np.any((retained < 0) | (retained > 1)) or np.any(np.diff(retained) > 1e-12):
        raise ValueError("Power must be nonincreasing and in [0, 1]")
    if not np.isfinite(threshold) or not 0 < threshold < 1:
        raise ValueError("threshold must be in (0, 1)")
    hit = np.flatnonzero(retained <= threshold)
    if not hit.size:
        return None
    i = int(hit[0])
    if i == 0:
        return float(age[0])
    fraction = (retained[i - 1] - threshold) / (retained[i - 1] - retained[i])
    return float(age[i - 1] + fraction * (age[i] - age[i - 1]))
