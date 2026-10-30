"""Scientific invariants, frozen prediction and source-independent hand calculations."""

import json
from dataclasses import replace

import numpy as np
import pytest

from energy_methods.climate_zones import ClimateClusterModel, ClimateProvenance, class_target_rmse
from energy_methods.jrc_climate import fit_jrc_climate, performance_features
from energy_methods.ml21 import fit_ml21
from energy_methods.pvcz import classify_pvcz, equivalent_temperature

P = ClimateProvenance("test observations", "2001-2020", "point samples")


def test_pvcz_thresholds_missing_and_upstream_numbering():
    result = classify_pvcz([13.99, 14, 54, np.nan], [2.99, 3, 10.5, 7], provenance=P)
    assert result.zone.tolist() == ["T1:H1", "T2:H2", "T10:H5", ""]
    assert result.class_id.tolist() == [1, 12, 50, 0]
    assert result.provenance == P
    with pytest.raises(ValueError):
        result.class_id[0] = 2
    for t, h in [(np.inf, 3), (-273.15, 2), (20, -1)]:
        with pytest.raises(ValueError):
            classify_pvcz(t, h, provenance=P)


def test_arrhenius_equivalent_temperature_against_direct_equation():
    t = np.array([[40.0, 50.0], [20.0, 20.0]])
    dt = np.array([1.0, 3.0])
    a = 1.1 / 8.617333262145e-5
    expected = -a / np.log(np.average(np.exp(-a / (t + 273.15)), weights=dt, axis=1)) - 273.15
    np.testing.assert_allclose(equivalent_temperature(t, duration_hours=dt), expected)
    assert equivalent_temperature(t)[0] > t[0].mean()
    assert equivalent_temperature(t)[1] == pytest.approx(20.0)
    assert np.isnan(equivalent_temperature([20.0, np.nan]))
    with pytest.raises(ValueError):
        equivalent_temperature([20.0, 30.0], duration_hours=[1.0, 0.0])


def test_performance_features_use_poa_and_duration_not_simple_temperature_mean():
    actual = performance_features([0, 200, 800], [10, 20, 40], duration_hours=[1, 2, 1])
    np.testing.assert_allclose(actual, [1.2, (200 * 20 * 2 + 800 * 40) / 1200])
    assert np.isnan(performance_features([0, 0], [20, 30])[1])
    assert np.isnan(performance_features([10, np.nan], [20, 30])).all()
    with pytest.raises(ValueError):
        performance_features([-10], [20])


def test_jrc_cosine_area_weighting_and_frozen_json_prediction():
    x = np.array([[100, 10], [120, 12], [1000, 30], [1100, 32]], dtype=float)
    lat = np.array([0, 60, 0, 60])
    model = fit_jrc_climate(x, latitude=lat, provenance=P, n_clusters=2, n_init=3)
    expected = np.stack(
        [np.average(x[:2], axis=0, weights=[1, 0.5]), np.average(x[2:], axis=0, weights=[1, 0.5])]
    )
    np.testing.assert_allclose(model.centers * model.scale, expected)
    restored = ClimateClusterModel.from_dict(json.loads(json.dumps(model.to_dict())))
    test = np.vstack([x, [np.nan, 20], [2000, 50]])
    result = restored.predict(test, batch_size=1)
    np.testing.assert_array_equal(result.class_id, model.predict(test).class_id)
    assert result.class_id.tolist() == [1, 1, 2, 2, 0, 2]
    assert result.outside_training_range is not None
    assert result.outside_training_range.tolist() == [False] * 5 + [True]
    with pytest.raises(ValueError):
        replace(model, scale=np.array([0.0, 1.0]))
    with pytest.raises(ValueError):
        model.predict([[np.inf, 20.0]])


def test_ml_fit_retains_training_scaler_weights_and_does_not_refit_new_regions():
    rng = np.random.default_rng(8)
    x = rng.uniform(1, 30, (200, 7))
    coefficients = np.array([1.0, -2.0, 3.0, 4.0, 5.0, 6.0, 7.0])
    y = 1000 + x @ coefficients
    model = fit_ml21(x, y, provenance=P, feature_convention="synthetic fixture", n_clusters=4)
    np.testing.assert_allclose(model.offset, x.mean(axis=0))
    expected = np.abs(coefficients * x.std(axis=0))
    np.testing.assert_allclose(model.weights, expected / expected.max())
    before = model.to_dict()
    model.predict(x * 2)
    assert model.to_dict() == before
    restored = ClimateClusterModel.from_dict(before)
    np.testing.assert_array_equal(restored.predict(x).class_id, model.predict(x).class_id)
    with pytest.raises(ValueError, match="full-rank"):
        fit_ml21(np.repeat(x[:, :1], 7, axis=1), y, provenance=P, feature_convention="fixture")


def test_class_target_dispersion_excludes_missing_and_uses_weighted_class_means():
    zones = classify_pvcz([10, 10, 30, np.nan], [2, 2, 2, 2], provenance=P)
    assert class_target_rmse(zones, [0, 4, 100, 999], [1, 3, 2, 1]) == pytest.approx(np.sqrt(2))
    with pytest.raises(ValueError):
        class_target_rmse(zones, [1, 2])
