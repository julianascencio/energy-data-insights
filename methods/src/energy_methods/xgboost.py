"""Deterministic CPU XGBoost regression for explicitly prepared forecast features.

This module neither creates lags nor splits time series. Fit only on information
available before the issue time. References: Chen and Guestrin (2016), and the
official XGBoost Python API. JSON model state is exported instead of pickle.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

import numpy as np
from numpy.typing import ArrayLike
from xgboost import XGBRegressor

from energy_methods._arrays import FloatArray
from energy_methods._regression import feature_labels, feature_matrix, training_arrays

REFERENCE_IDS = ("chen_guestrin_2016_xgboost", "xgboost_python_api")


@dataclass(frozen=True, slots=True)
class XGBoostConfig:
    n_estimators: int = 200
    learning_rate: float = 0.04
    max_depth: int = 4
    min_child_weight: float = 10.0
    reg_lambda: float = 1.0
    min_samples: int = 48
    n_jobs: int = 1
    random_state: int = 42

    def __post_init__(self) -> None:
        for name in ("n_estimators", "max_depth", "min_samples", "n_jobs"):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError("Tree, sample and worker counts must be positive integers")
        if not 0 < self.learning_rate <= 1:
            raise ValueError("learning_rate must be in (0, 1]")
        if (
            not np.isfinite([self.min_child_weight, self.reg_lambda]).all()
            or min(self.min_child_weight, self.reg_lambda) < 0
        ):
            raise ValueError("Regularization must be finite and nonnegative")
        if type(self.random_state) is not int or self.random_state < 0:
            raise ValueError("random_state must be a nonnegative integer")


@dataclass(slots=True)
class XGBoostModel:
    """Fitted regressor, with explicit feature order and training-row count."""

    estimator: XGBRegressor
    config: XGBoostConfig
    feature_names: tuple[str, ...]
    training_rows: int

    def predict(self, features: ArrayLike) -> FloatArray:
        """Return predictions in the target unit, without implicit physical clipping."""
        x = feature_matrix(features, len(self.feature_names))
        return np.asarray(self.estimator.predict(x), dtype=np.float64)

    def to_dict(self) -> dict[str, object]:
        """Export native JSON model state and the exact feature contract."""
        return {
            "method": "xgboost_hist_regression",
            "reference_ids": list(REFERENCE_IDS),
            "config": asdict(self.config),
            "feature_names": list(self.feature_names),
            "training_rows": self.training_rows,
            "model_json": json.loads(self.estimator.get_booster().save_raw(raw_format="json")),
        }


DEFAULT_CONFIG = XGBoostConfig()


def fit_xgboost(
    features: ArrayLike,
    target: ArrayLike,
    *,
    feature_names: tuple[str, ...] | None = None,
    config: XGBoostConfig = DEFAULT_CONFIG,
) -> XGBoostModel:
    """Fit supplied training rows only; no random split or holdout-based early stopping."""
    x, y = training_arrays(features, target, config.min_samples)
    names = feature_labels(feature_names, x.shape[1])
    estimator = XGBRegressor(
        objective="reg:squarederror",
        tree_method="hist",
        device="cpu",
        n_estimators=config.n_estimators,
        learning_rate=config.learning_rate,
        max_depth=config.max_depth,
        min_child_weight=config.min_child_weight,
        reg_lambda=config.reg_lambda,
        random_state=config.random_state,
        n_jobs=config.n_jobs,
        subsample=1.0,
        colsample_bytree=1.0,
        verbosity=0,
    )
    estimator.fit(x, y)
    return XGBoostModel(estimator, config, names, len(y))
