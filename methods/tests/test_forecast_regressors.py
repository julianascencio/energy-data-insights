"""Reusable regression contracts; synthetic fixtures are only numerical tests."""

import json

import numpy as np
import pytest
from xgboost import XGBRegressor

from energy_methods.lightgbm import fit_lightgbm_features
from energy_methods.wind_physics import WindPhysicsConfig, fit_wind_physics, wind_power_fraction
from energy_methods.xgboost import XGBoostConfig, fit_xgboost


@pytest.mark.parametrize("fit", [fit_xgboost, fit_lightgbm_features])
def test_tabular_determinism_feature_contract_and_target_units(fit) -> None:
    x = np.column_stack((np.linspace(0, 10, 100), np.cos(np.arange(100))))
    y = -20 + 0.5 * x[:, 0]  # Generic regressors must not silently clip targets.
    model = fit(x, y, feature_names=("speed", "clock"))
    second = fit(x, y, feature_names=("speed", "clock"))
    np.testing.assert_array_equal(model.predict(x), second.predict(x))
    assert (model.predict(x) < 0).all()
    assert np.mean(np.abs(model.predict(x) - y)) < 0.5
    assert model.training_rows == 100
    assert model.to_dict()["feature_names"] == ["speed", "clock"]
    json.dumps(model.to_dict(), allow_nan=False)
    for invalid in [x[:, :1], x[:, 0], np.full_like(x, np.nan), np.empty((0, 2))]:
        with pytest.raises(ValueError, match=r"Features|feature count"):
            model.predict(invalid)
    with pytest.raises(ValueError, match="Feature names"):
        fit(x, y, feature_names=("speed", "speed"))
    for target in [y[:-1], y * np.nan, y[:, None]]:
        with pytest.raises(ValueError):
            fit(x, target)
    with pytest.raises(ValueError, match="min_samples"):
        fit(x[:5], y[:5])


def test_xgboost_native_json_roundtrip() -> None:
    x = np.arange(100, dtype=float).reshape(50, 2)
    model = fit_xgboost(x, x[:, 0])
    restored = XGBRegressor()
    restored.load_model(bytearray(json.dumps(model.to_dict()["model_json"]).encode()))
    np.testing.assert_allclose(restored.predict(x), model.predict(x))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"n_jobs": 0},
        {"min_samples": True},
        {"n_estimators": 0},
        {"learning_rate": np.nan},
        {"reg_lambda": -1},
        {"max_depth": 0},
        {"min_child_weight": np.inf},
        {"random_state": -1},
    ],
)
def test_invalid_xgboost_settings(kwargs) -> None:
    with pytest.raises(ValueError):
        XGBoostConfig(**kwargs)


def test_wind_curve_boundaries_and_scale_recovery() -> None:
    speed = np.array([0, 3, 7, 11.4, 24.99, 25, -1, np.nan])
    curve = wind_power_fraction(speed)
    np.testing.assert_allclose(curve[:6], [0, 0, (7**3 - 3**3) / (11.4**3 - 3**3), 1, 1, 0])
    assert np.isnan(curve[-2:]).all()
    training = np.linspace(0, 28, 200)
    model = fit_wind_physics(training, 30 * wind_power_fraction(training))
    assert model.scale_mw == pytest.approx(30)
    assert model.to_dict()["scale_is_installed_capacity"] is False
    np.testing.assert_allclose(model.predict(training), 30 * wind_power_fraction(training))
    with pytest.raises(ValueError, match="identify"):
        fit_wind_physics(np.zeros(100), np.ones(100))
    with pytest.raises(ValueError, match="Insufficient"):
        fit_wind_physics([np.nan] * 100, np.ones(100))
    with pytest.raises(ValueError, match="ordered"):
        WindPhysicsConfig(cut_in_ms=12)
