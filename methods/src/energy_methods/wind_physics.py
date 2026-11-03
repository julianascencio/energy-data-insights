"""Transparent cubic wind-power surrogate with training-only scale calibration.

The default cut-in/rated/cut-out speeds follow the NREL 5-MW reference turbine.
The interpolating cubic and fitted farm scale are repository approximations,
not that turbine's aerodynamic power curve or evidence of installed equipment.
Air density, wakes, availability and curtailment are not modelled.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
from numpy.typing import ArrayLike

from energy_methods._arrays import FloatArray, aligned, vector

REFERENCE_IDS = ("jonkman_2009_nrel_5mw",)


@dataclass(frozen=True, slots=True)
class WindPhysicsConfig:
    cut_in_ms: float = 3.0
    rated_ms: float = 11.4
    cut_out_ms: float = 25.0
    min_samples: int = 48

    def __post_init__(self) -> None:
        speeds = [self.cut_in_ms, self.rated_ms, self.cut_out_ms]
        if not np.isfinite(speeds).all() or not 0 <= speeds[0] < speeds[1] < speeds[2]:
            raise ValueError("Wind speed thresholds must be finite, nonnegative and ordered")
        if type(self.min_samples) is not int or self.min_samples < 1:
            raise ValueError("min_samples must be a positive integer")


DEFAULT_CONFIG = WindPhysicsConfig()


def wind_power_fraction(
    speed_ms: ArrayLike, *, config: WindPhysicsConfig = DEFAULT_CONFIG
) -> FloatArray:
    """Piecewise zero / cubic ramp / rated plateau / cut-out, with NaN for bad speeds."""
    speed = vector(speed_ms, "speed_ms")
    fraction = np.full(speed.shape, np.nan)
    valid = np.isfinite(speed) & (speed >= 0)
    fraction[valid] = 0.0
    ramp = valid & (speed >= config.cut_in_ms) & (speed < config.rated_ms)
    fraction[ramp] = (speed[ramp] ** 3 - config.cut_in_ms**3) / (
        config.rated_ms**3 - config.cut_in_ms**3
    )
    fraction[valid & (speed >= config.rated_ms) & (speed < config.cut_out_ms)] = 1.0
    return fraction


@dataclass(frozen=True, slots=True)
class WindPhysicsModel:
    config: WindPhysicsConfig
    scale_mw: float
    training_rows: int

    def predict(self, speed_ms: ArrayLike) -> FloatArray:
        return self.scale_mw * wind_power_fraction(speed_ms, config=self.config)

    def to_dict(self) -> dict[str, object]:
        return {
            "method": "calibrated_cubic_wind_surrogate",
            "config": asdict(self.config),
            "scale_mw": self.scale_mw,
            "training_rows": self.training_rows,
            "reference_ids": list(REFERENCE_IDS),
            "scale_is_installed_capacity": False,
        }


def fit_wind_physics(
    speed_ms: ArrayLike,
    power_mw: ArrayLike,
    *,
    config: WindPhysicsConfig = DEFAULT_CONFIG,
) -> WindPhysicsModel:
    """Calibrate a nonnegative response scale on supplied historical observations."""
    speed, power = aligned(speed_ms, power_mw)
    fraction = wind_power_fraction(speed, config=config)
    valid = np.isfinite(fraction) & np.isfinite(power) & (power >= 0)
    if valid.sum() < config.min_samples:
        raise ValueError("Insufficient finite wind-physics training observations")
    x, y = fraction[valid], power[valid]
    denominator = float(x @ x)
    if denominator <= 0 or not (y > 0).any():
        raise ValueError("Wind training data do not identify a positive power response")
    return WindPhysicsModel(config, max(0.0, float(x @ y) / denominator), len(y))
