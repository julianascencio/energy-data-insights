"""Power-versus-age models and variation metrics from Kaaya et al. (2021).

These are deterministic extrapolations, not survival probabilities or warranties.
The stretched-exponential coefficient has units year**(-beta); coefficients
from different curve families are not interchangeable annual loss percentages.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.optimize import least_squares

REFERENCE_IDS = ("ascencio_vasquez_2021_thesis", "kaaya_2021_uncertainties")
ReliabilityKind = Literal["linear", "exponential", "stretched_exponential", "wear_out"]
KINDS: tuple[ReliabilityKind, ...] = ("linear", "exponential", "stretched_exponential", "wear_out")


def _finite(value: ArrayLike, name: str) -> NDArray[np.float64]:
    result = np.asarray(value, dtype=float)
    if not result.size or not np.isfinite(result).all():
        raise ValueError(f"{name} must be nonempty and finite")
    return result


def _paired(measured: ArrayLike, predicted: ArrayLike) -> tuple[NDArray, NDArray]:
    m, p = _finite(measured, "measured"), _finite(predicted, "predicted")
    if m.shape != p.shape:
        raise ValueError("Measured and predicted shapes must match; align observations first")
    return m, p


def normalized_rmse(measured: ArrayLike, predicted: ArrayLike) -> float:
    """Equation 19, percent: RMSE/mean, or RMSE/range for exactly zero mean.

    The paper concerns positive quantities. Negative means are rejected rather
    than producing negative errors. A constant zero reference is defined only
    for an exact match (zero error); otherwise its normalization is undefined.
    """
    m, p = _paired(measured, predicted)
    mean = float(m.mean())
    if mean < 0:
        raise ValueError("Equation 19 requires a nonnegative measured mean")
    scale = mean if mean != 0 else float(np.ptp(m))
    rmse = float(np.sqrt(np.mean((p - m) ** 2)))
    if scale == 0:
        if rmse == 0:
            return 0.0
        raise ValueError("NRMSE normalization is undefined for an all-zero reference")
    return 100 * rmse / scale


def relative_difference(measured: ArrayLike, predicted: ArrayLike) -> NDArray[np.float64]:
    """Equation 20: 100*abs(p-m)/max(abs(p),abs(m)); (0,0) is defined as 0.

    This symmetric difference is not percentage error relative to the reference.
    Equal shapes are required; no implicit broadcasting or missing-value removal.
    """
    m, p = _paired(measured, predicted)
    scale = np.maximum(np.abs(m), np.abs(p))
    return 100 * np.divide(np.abs(p - m), scale, out=np.zeros_like(scale), where=scale > 0)


@dataclass(frozen=True, slots=True)
class ReliabilityCurve:
    """Table 2 curve with time in years and power normalized to initial power.

    ``k`` is fractional, never a numerical percent. ``beta`` belongs to the
    stretched exponential (Pan); ``gamma`` and ``mu`` to wear-out (Kaaya).
    Gamma and k are inseparable through their ratio and cannot both be fitted.
    """

    kind: ReliabilityKind
    k: float
    beta: float = 1.0
    gamma: float = 1.0
    mu: float = 1.0

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"Unknown reliability kind: {self.kind}")
        if not np.isfinite([self.k, self.beta, self.gamma, self.mu]).all():
            raise ValueError("Curve parameters must be finite")
        if self.k < 0 or min(self.beta, self.gamma, self.mu) <= 0:
            raise ValueError("k must be nonnegative and shape parameters positive")

    @property
    def k_units(self) -> str:
        """Dimensional coefficient units, with gamma treated as dimensionless."""
        return "year**(-beta)" if self.kind == "stretched_exponential" else "year**(-1)"

    def power(self, age_years: ArrayLike) -> NDArray[np.float64]:
        """Evaluate Table 2; linear predictions are not clipped below zero."""
        t = _finite(age_years, "age_years")
        if np.any(t < 0):
            raise ValueError("Age must be nonnegative")
        if self.k == 0:
            return np.ones_like(t)
        with np.errstate(over="ignore", under="ignore"):
            if self.kind == "linear":
                return 1 - self.k * t
            if self.kind == "exponential":
                return np.exp(-self.k * t)
            if self.kind == "stretched_exponential":
                return np.exp(-self.k * t**self.beta)
            # The analytic limit at t=0 is one, without divide-by-zero warnings.
            ratio = np.divide(self.gamma, self.k * t, out=np.full_like(t, np.inf), where=t > 0)
            return -np.expm1(-(ratio**self.mu))

    def failure_time(self, retained_power: float = 0.8) -> float:
        """Analytic crossing time, years, for a retained-power threshold in (0,1)."""
        if not np.isfinite(retained_power) or not 0 < retained_power < 1:
            raise ValueError("retained_power must lie strictly between zero and one")
        if self.k == 0:
            return float("inf")
        if self.kind == "linear":
            return (1 - retained_power) / self.k
        if self.kind == "exponential":
            return -float(np.log(retained_power)) / self.k
        if self.kind == "stretched_exponential":
            return float((-np.log(retained_power) / self.k) ** (1 / self.beta))
        return float(self.gamma / (self.k * (-np.log1p(-retained_power)) ** (1 / self.mu)))


@dataclass(frozen=True, slots=True)
class ReliabilityFit:
    """Calibration result; residual error is not a prediction confidence interval."""

    curve: ReliabilityCurve
    nrmse_percent: float
    observations: int
    calibration_end_year: float
    jacobian_condition: float


def fit_reliability(
    age_years: ArrayLike,
    normalized_power: ArrayLike,
    *,
    kind: ReliabilityKind,
    gamma: float = 1.0,
) -> ReliabilityFit:
    """Fit Table 2 with bounded, deterministic multistart least squares.

    Fit k and (for nonlinear families) beta or mu. Wear-out gamma is FIXED to
    the caller's value to avoid the exact k/gamma degeneracy. Ages must be
    distinct, increasing, measured from a declared origin. The normalization
    must be supplied; no hidden intercept, temperature correction or filtering.
    Shape bounds [0.05, 10] and k bounds [1e-10, 10] are numerical choices.
    Report the family and shape alongside k; do not rank lifetimes by fit alone.
    """
    t, y = _paired(age_years, normalized_power)
    if t.ndim != 1 or len(t) < 4 or np.any(t < 0) or np.any(np.diff(t) <= 0):
        raise ValueError("At least four increasing, distinct, nonnegative ages are required")
    if np.any(y <= 0) or np.any(y > 1.5):
        raise ValueError("Normalized power must be positive and at most 1.5")
    if np.ptp(y) <= 1e-12:
        raise ValueError("A flat series cannot identify a degradation curve and its lifetime")
    ReliabilityCurve(kind, 0.01, gamma=gamma)
    nonlinear = kind in {"stretched_exponential", "wear_out"}

    def curve_for(log_parameters: NDArray) -> ReliabilityCurve:
        values = np.exp(log_parameters)
        return ReliabilityCurve(
            kind,
            float(values[0]),
            gamma=gamma,
            beta=float(values[1]) if kind == "stretched_exponential" else 1,
            mu=float(values[1]) if kind == "wear_out" else 1,
        )

    lower = np.log([1e-10, 0.05] if nonlinear else [1e-10])
    upper = np.log([10, 10] if nonlinear else [10])
    fits = [
        least_squares(
            lambda x: curve_for(x).power(t) - y,
            np.log([k, shape] if nonlinear else [k]),
            bounds=(lower, upper),
            ftol=1e-12,
            xtol=1e-12,
            gtol=1e-12,
            max_nfev=3000,
        )
        for k in (0.001, 0.01, 0.1)
        for shape in ((0.3, 1.0, 2.0) if nonlinear else (1.0,))
    ]
    successful = [fit for fit in fits if fit.success]
    if not successful:
        raise ValueError("Reliability calibration did not converge")
    best = min(successful, key=lambda fit: fit.cost)
    curve = curve_for(best.x)
    return ReliabilityFit(
        curve,
        normalized_rmse(y, curve.power(t)),
        len(t),
        float(t[-1]),
        float(np.linalg.cond(best.jac)),
    )
