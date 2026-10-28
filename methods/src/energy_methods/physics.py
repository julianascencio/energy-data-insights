"""Shape-constrained PV regression on POA and ambient temperature.

Nonnegative coefficients analytically enforce a nondecreasing, concave response
to irradiance and a nonincreasing response to temperature on the declared domain.
These are empirical response constraints, not identified module thermal physics.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

import numpy as np
from numpy.typing import ArrayLike
from scipy.optimize import lsq_linear

from energy_methods._arrays import BoolArray, FloatArray, aligned, immutable


@dataclass(frozen=True, slots=True)
class PhysicsConfig:
    family: Literal["thermal_quadratic", "concave_spline"] = "concave_spline"
    alpha: float = 0.1
    min_samples: int = 24
    poa_max_wm2: float = 1300.0
    temperature_min_c: float = -20.0
    temperature_max_c: float = 60.0
    operational_zero_poa_wm2: float = 1.0
    knots_wm2: tuple[float, ...] = (200.0, 400.0, 600.0, 800.0, 1000.0, 1200.0)

    def __post_init__(self) -> None:
        if self.family not in {"thermal_quadratic", "concave_spline"}:
            raise ValueError("Unknown physical response family")
        values = [
            self.alpha,
            self.poa_max_wm2,
            self.temperature_min_c,
            self.temperature_max_c,
            self.operational_zero_poa_wm2,
            *self.knots_wm2,
        ]
        if not np.isfinite(values).all() or self.alpha < 0 or self.min_samples < 3:
            raise ValueError(
                "Finite model settings, nonnegative alpha and >=3 samples are required"
            )
        if not 0 <= self.operational_zero_poa_wm2 < self.poa_max_wm2:
            raise ValueError("Invalid POA domain or startup cutoff")
        if self.temperature_min_c >= self.temperature_max_c:
            raise ValueError("Temperature bounds must be ordered")
        if any(not 0 < knot < self.poa_max_wm2 for knot in self.knots_wm2):
            raise ValueError("Spline knots must be strictly inside the irradiance domain")
        if tuple(sorted(set(self.knots_wm2))) != self.knots_wm2:
            raise ValueError("Spline knots must be unique and increasing")


DEFAULT_CONFIG = PhysicsConfig()


def _design(poa: FloatArray, temperature: FloatArray, config: PhysicsConfig) -> FloatArray:
    g, t = poa / 1000.0, (temperature - 25.0) / 25.0
    tmax = (config.temperature_max_c - 25.0) / 25.0
    if config.family == "thermal_quadratic":
        gmax = config.poa_max_wm2 / 1000.0
        return np.column_stack((g, g * (2 * gmax - g), g * (tmax - t)))
    return np.column_stack(
        (g, *[np.minimum(g, k / 1000.0) for k in config.knots_wm2], g * (tmax - t))
    )


@dataclass(frozen=True, slots=True)
class PhysicsModel:
    config: PhysicsConfig
    coefficients: FloatArray
    training_scale_mwh: float
    training_rows: int
    poa_support_wm2: tuple[float, float]
    temperature_support_c: tuple[float, float]

    def to_dict(self) -> dict[str, object]:
        """Portable fitted state; no opaque estimator or executable serialization."""
        return {
            "method": "shape_constrained_physical_response",
            "config": asdict(self.config),
            "coefficients": self.coefficients.tolist(),
            "training_scale_mwh": self.training_scale_mwh,
            "training_rows": self.training_rows,
            "poa_support_wm2": list(self.poa_support_wm2),
            "temperature_support_c": list(self.temperature_support_c),
            "parameterization": "nonnegative_transformed_basis",
            "irradiance_concavity": "analytic_on_declared_domain_before_startup_cutoff",
            "identified_thermal_parameters": False,
        }

    def predict(self, poa_wm2: ArrayLike, temperature_c: ArrayLike) -> FloatArray:
        """Return NaN outside the declared domain; startup cutoff is separate."""
        poa, temperature = aligned(poa_wm2, temperature_c)
        result = np.full(len(poa), np.nan)
        valid = np.isfinite(poa) & np.isfinite(temperature) & (poa >= 0)
        valid &= poa <= self.config.poa_max_wm2
        valid &= temperature >= self.config.temperature_min_c
        valid &= temperature <= self.config.temperature_max_c
        result[valid] = np.maximum(
            _design(poa[valid], temperature[valid], self.config)
            @ self.coefficients
            * self.training_scale_mwh,
            0.0,
        )
        result[valid & (poa <= self.config.operational_zero_poa_wm2)] = 0.0
        return result

    def weather_support(self, poa_wm2: ArrayLike, temperature_c: ArrayLike) -> BoolArray:
        """Training-observed rectangular support, separate from physical domain."""
        poa, temperature = aligned(poa_wm2, temperature_c)
        return (
            np.isfinite(poa)
            & np.isfinite(temperature)
            & (poa >= self.poa_support_wm2[0])
            & (poa <= self.poa_support_wm2[1])
            & (temperature >= self.temperature_support_c[0])
            & (temperature <= self.temperature_support_c[1])
        )


def fit_physics_model(
    poa_wm2: ArrayLike,
    temperature_c: ArrayLike,
    actual_mwh: ArrayLike,
    *,
    config: PhysicsConfig = DEFAULT_CONFIG,
) -> PhysicsModel:
    """Fit only supplied accepted training rows using nonnegative least squares."""
    poa, temperature, actual = aligned(poa_wm2, temperature_c, actual_mwh)
    valid = np.isfinite(poa) & np.isfinite(temperature) & np.isfinite(actual) & (actual >= 0)
    valid &= (poa >= 0) & (poa <= config.poa_max_wm2)
    valid &= (temperature >= config.temperature_min_c) & (temperature <= config.temperature_max_c)
    if int(valid.sum()) < config.min_samples:
        raise ValueError("Insufficient accepted finite training rows for the physical model")
    poa, temperature, actual = poa[valid], temperature[valid], actual[valid]
    scale = float(np.quantile(actual, 0.95, method="linear"))
    if scale <= 0:
        raise ValueError("Accepted-training Q95 energy must be positive")
    design = _design(poa, temperature, config)
    if config.family == "thermal_quadratic":
        penalty = np.asarray(
            [
                [1.0, 2 * config.poa_max_wm2 / 1000.0, (config.temperature_max_c - 25) / 25],
                [0.0, -1.0, 0.0],
                [0.0, 0.0, -1.0],
            ]
        )
    else:
        penalty = np.eye(design.shape[1])
    augmented = np.vstack((design, np.sqrt(config.alpha) * penalty))
    target = np.concatenate((actual / scale, np.zeros(penalty.shape[0])))
    solved = lsq_linear(
        augmented, target, bounds=(0.0, np.inf), method="bvls", tol=1e-12, max_iter=1000
    )
    if not solved.success or not np.isfinite(solved.x).all():
        raise RuntimeError(f"Constrained least squares failed: {solved.message}")
    return PhysicsModel(
        config,
        immutable(np.maximum(solved.x, 0.0)),
        scale,
        len(actual),
        (float(poa.min()), float(poa.max())),
        (float(temperature.min()), float(temperature.max())),
    )
