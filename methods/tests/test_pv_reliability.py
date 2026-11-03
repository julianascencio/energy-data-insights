"""Analytic crossings, parameter identifiability and metric edge cases."""

import numpy as np
import pytest

from energy_methods.pv_reliability import (
    KINDS,
    ReliabilityCurve,
    fit_reliability,
    normalized_rmse,
    relative_difference,
)


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("threshold", [0.2, 0.8, 0.95])
def test_analytic_failure_time_inverts_each_curve(kind, threshold):
    curve = ReliabilityCurve(kind, 0.007, beta=1.6, gamma=0.43, mu=0.52)
    assert curve.power(curve.failure_time(threshold)) == pytest.approx(threshold)
    assert curve.power(0) == 1
    assert np.all(np.diff(curve.power(np.linspace(0, 40, 100))) <= 0)
    assert ReliabilityCurve(kind, 0).failure_time() == np.inf
    np.testing.assert_array_equal(ReliabilityCurve(kind, 0).power([0, 1, 10]), [1, 1, 1])


@pytest.mark.parametrize("kind", KINDS)
def test_fit_recovers_known_curve_and_threshold(kind):
    curve = ReliabilityCurve(kind, 0.008, beta=1.6, gamma=0.43, mu=0.52)
    t = np.linspace(0, 18, 150)
    fit = fit_reliability(t, curve.power(t), kind=kind, gamma=0.43)
    assert fit.curve.k == pytest.approx(curve.k, rel=1e-5)
    assert fit.curve.failure_time() == pytest.approx(curve.failure_time(), rel=1e-5)
    assert fit.nrmse_percent < 1e-5
    assert fit.observations == 150


def test_wear_out_only_identifies_gamma_over_k():
    t = np.linspace(0, 30, 100)
    a = ReliabilityCurve("wear_out", 0.008, gamma=0.4, mu=0.5)
    b = ReliabilityCurve("wear_out", 0.016, gamma=0.8, mu=0.5)
    np.testing.assert_array_equal(a.power(t), b.power(t))
    assert a.failure_time() == b.failure_time()


def test_published_uncertainty_metrics_and_zero_conventions():
    assert normalized_rmse([1, 3], [2, 4]) == 50
    assert normalized_rmse([-1, 1], [0, 2]) == 50
    assert normalized_rmse([0, 0], [0, 0]) == 0
    assert relative_difference(8, 10) == 20
    assert relative_difference(-2, 2) == 200
    np.testing.assert_array_equal(relative_difference([0, 10], [0, 0]), [0, 100])
    for m, p in [([0, 0], [1, 1]), ([-2], [-1]), ([1], [1, 2]), ([np.nan], [1])]:
        with pytest.raises(ValueError):
            normalized_rmse(m, p)


@pytest.mark.parametrize(
    "kwargs", [{"k": -1}, {"k": np.nan}, {"k": 1, "mu": 0}, {"k": 1, "beta": np.inf}]
)
def test_invalid_curves_fail(kwargs):
    with pytest.raises(ValueError):
        ReliabilityCurve("linear", **kwargs)


def test_invalid_times_and_thresholds_fail():
    curve = ReliabilityCurve("wear_out", 0.01)
    for t in [[-1], [np.nan], []]:
        with pytest.raises(ValueError):
            curve.power(t)
    for threshold in [0, 1, np.nan]:
        with pytest.raises(ValueError):
            curve.failure_time(threshold)
    for t in [[0, 1, 1, 2], [0, 2, 1, 3]]:
        with pytest.raises(ValueError):
            fit_reliability(t, [1, 0.99, 0.98, 0.97], kind="linear")


def test_flat_observations_do_not_produce_a_spurious_finite_lifetime():
    for kind in KINDS:
        with pytest.raises(ValueError, match="flat series"):
            fit_reliability([0, 1, 2, 3], [1, 1, 1, 1], kind=kind)
