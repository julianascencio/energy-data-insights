"""Deterministic monotone LightGBM alternative; concavity is not guaranteed.

Irradiance is constrained increasing and temperature decreasing. Tree-based
monotonicity is weaker than the analytic concavity of the physics model. Fit
only the accepted training partition and evaluate later chronological data.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
from lightgbm import LGBMRegressor
from numpy.typing import ArrayLike

from energy_methods._arrays import BoolArray, FloatArray, aligned


@dataclass(frozen=True, slots=True)
class LightGBMConfig:
    n_estimators: int = 200
    learning_rate: float = 0.04
    num_leaves: int = 15
    min_child_samples: int = 20
    min_samples: int = 48
    n_jobs: int = 1
    random_state: int = 42

    def __post_init__(self) -> None:
        if min(self.n_estimators, self.min_child_samples, self.min_samples, self.n_jobs) < 1:
            raise ValueError(
                "Training and worker counts must be positive; unlimited threads forbidden"
            )
        if not 0 < self.learning_rate <= 1 or self.num_leaves < 2:
            raise ValueError("Invalid learning rate or tree size")


@dataclass(slots=True)
class LightGBMModel:
    estimator: LGBMRegressor
    config: LightGBMConfig
    training_scale_mwh: float
    training_rows: int
    poa_support_wm2: tuple[float, float]
    temperature_support_c: tuple[float, float]

    def to_dict(self) -> dict[str, object]:
        """Export LightGBM's text model rather than unsafe pickle objects."""
        return {
            "method": "monotone_lightgbm",
            "config": asdict(self.config),
            "model_text": self.estimator.booster_.model_to_string(),
            "feature_order": ["poa_wm2", "temperature_c"],
            "training_scale_mwh": self.training_scale_mwh,
            "training_rows": self.training_rows,
            "poa_support_wm2": list(self.poa_support_wm2),
            "temperature_support_c": list(self.temperature_support_c),
            "monotone_constraints": [1, -1],
            "irradiance_concavity": "not_guaranteed",
        }

    def predict(self, poa_wm2: ArrayLike, temperature_c: ArrayLike) -> FloatArray:
        """Mask invalid/out-of-domain weather and enforce the declared startup zero."""
        poa, temperature = aligned(poa_wm2, temperature_c)
        valid = np.isfinite(poa) & np.isfinite(temperature)
        valid &= (poa >= 0) & (poa <= 1300) & (temperature >= -20) & (temperature <= 60)
        result = np.full(len(poa), np.nan)
        if valid.any():
            prediction = np.asarray(
                self.estimator.booster_.predict(
                    np.column_stack((poa[valid], temperature[valid])),
                    num_threads=self.config.n_jobs,
                ),
                dtype=np.float64,
            )
            result[valid] = np.maximum(prediction, 0.0)
        result[valid & (poa <= 1)] = 0.0
        return result

    def weather_support(self, poa_wm2: ArrayLike, temperature_c: ArrayLike) -> BoolArray:
        poa, temperature = aligned(poa_wm2, temperature_c)
        return (
            np.isfinite(poa)
            & np.isfinite(temperature)
            & (poa >= self.poa_support_wm2[0])
            & (poa <= self.poa_support_wm2[1])
            & (temperature >= self.temperature_support_c[0])
            & (temperature <= self.temperature_support_c[1])
        )


DEFAULT_CONFIG = LightGBMConfig()


def fit_lightgbm(
    poa_wm2: ArrayLike,
    temperature_c: ArrayLike,
    actual_mwh: ArrayLike,
    *,
    config: LightGBMConfig = DEFAULT_CONFIG,
) -> LightGBMModel:
    """Fit without random train/test splitting, early stopping or test-label access."""
    poa, temperature, actual = aligned(poa_wm2, temperature_c, actual_mwh)
    valid = np.isfinite(poa) & np.isfinite(temperature) & np.isfinite(actual) & (actual >= 0)
    valid &= (poa >= 0) & (poa <= 1300) & (temperature >= -20) & (temperature <= 60)
    if int(valid.sum()) < config.min_samples:
        raise ValueError("Insufficient accepted finite LightGBM training rows")
    poa, temperature, actual = poa[valid], temperature[valid], actual[valid]
    scale = float(np.quantile(actual, 0.95, method="linear"))
    if scale <= 0:
        raise ValueError("Accepted-training Q95 energy must be positive")
    estimator = LGBMRegressor(
        objective="regression",
        n_estimators=config.n_estimators,
        learning_rate=config.learning_rate,
        num_leaves=config.num_leaves,
        min_child_samples=config.min_child_samples,
        random_state=config.random_state,
        n_jobs=config.n_jobs,
        deterministic=True,
        force_col_wise=True,
        monotone_constraints=[1, -1],
        monotone_constraints_method="advanced",
        verbosity=-1,
    )
    estimator.fit(np.column_stack((poa, temperature)), actual)
    return LightGBMModel(
        estimator,
        config,
        scale,
        len(actual),
        (float(poa.min()), float(poa.max())),
        (float(temperature.min()), float(temperature.max())),
    )
