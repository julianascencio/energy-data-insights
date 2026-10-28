"""Shape, determinism, serialization and prediction-score tests."""

import json

import numpy as np
import pytest
from lightgbm import Booster

from energy_methods.lightgbm import LightGBMConfig, fit_lightgbm
from energy_methods.metrics import energy_metrics
from energy_methods.physics import PhysicsConfig, fit_physics_model


@pytest.mark.parametrize("family", ["thermal_quadratic", "concave_spline"])
def test_physical_shapes_across_declared_domain(family: str) -> None:
    rng = np.random.default_rng(8)
    poa = rng.uniform(30, 1250, 700)
    temperature = rng.uniform(-15, 55, 700)
    actual = (0.01 * poa - 0.000002 * poa**2) * (1 - 0.002 * temperature)
    config = PhysicsConfig(
        family="thermal_quadratic" if family == "thermal_quadratic" else "concave_spline"
    )
    model = fit_physics_model(poa, temperature, actual, config=config)
    probe = np.linspace(10, 1300, 260)
    for degrees in [-20, 25, 60]:
        prediction = model.predict(probe, np.full(len(probe), degrees))
        assert np.all(prediction >= 0)
        assert np.min(np.diff(prediction)) >= -1e-10
        assert np.max(np.diff(prediction, n=2)) <= 1e-10
    hot = np.linspace(-20, 60, 100)
    assert np.max(np.diff(model.predict(np.full(len(hot), 700), hot))) <= 1e-10
    assert model.predict([0, 1400, 100], [25, 25, 70])[0] == 0
    assert np.isnan(model.predict([1400, 100], [25, 70])).all()
    assert not model.weather_support([1400], [25])[0]
    json.dumps(model.to_dict(), allow_nan=False)


def test_monotone_lightgbm_determinism_and_portable_model() -> None:
    rng = np.random.default_rng(2)
    poa, temperature = rng.uniform(50, 1200, 400), rng.uniform(-10, 50, 400)
    actual = 0.009 * poa * (1 - 0.002 * temperature)
    config = LightGBMConfig(n_estimators=35, min_child_samples=8)
    first = fit_lightgbm(poa, temperature, actual, config=config)
    second = fit_lightgbm(poa, temperature, actual, config=config)
    probe = np.linspace(30, 1250, 70)
    predictions = first.predict(probe, np.full(len(probe), 25))
    np.testing.assert_array_equal(predictions, second.predict(probe, np.full(len(probe), 25)))
    assert np.min(np.diff(predictions)) >= -1e-10
    hot = np.linspace(-20, 60, 70)
    assert np.max(np.diff(first.predict(np.full(len(hot), 700), hot))) <= 1e-10
    state = first.to_dict()
    json.dumps(state, allow_nan=False)
    booster = Booster(model_str=str(state["model_text"]))
    replay = booster.predict(np.column_stack((probe, np.full(len(probe), 25))), num_threads=1)
    np.testing.assert_allclose(predictions, np.asarray(replay, dtype=np.float64), atol=0, rtol=0)
    assert state["irradiance_concavity"] == "not_guaranteed"


def test_metrics_report_zero_and_unknown_denominators_honestly() -> None:
    result = energy_metrics([10, 0, np.nan, -1], [8, 2, 100, 2])
    assert result.matched_hours == 2
    assert result.actual_mwh == result.expected_mwh == 10
    assert result.wape == 0.4
    assert result.score_pct == 60
    assert energy_metrics([0, 0], [0, 1]).score_pct is None
    assert energy_metrics([np.nan], [1]).mae_mwh is None


def test_all_zero_training_does_not_create_a_fake_reference() -> None:
    with pytest.raises(ValueError, match="Q95"):
        fit_physics_model(np.arange(50, 150), np.full(100, 25), np.zeros(100))
    with pytest.raises(ValueError, match="Q95"):
        fit_lightgbm(np.arange(50, 150), np.full(100, 25), np.zeros(100))
    with pytest.raises(ValueError, match="unlimited"):
        LightGBMConfig(n_jobs=-1)
