"""Independent analytic checks of equivalent time and horizon censoring."""

import numpy as np
import pytest

from energy_methods.pv_lifetime import (
    equivalent_time_power,
    independent_mode_power,
    sigmoid_exposure,
    sigmoid_power,
    threshold_crossing,
)


@pytest.mark.parametrize("shape", [0, 2, 8, 1000])
def test_sigmoid_inverse_and_constant_stress(shape):
    dose = sigmoid_exposure(0.8, shape=shape)
    assert sigmoid_power(dose, shape=shape) == pytest.approx(0.8)
    assert sigmoid_power(0, shape=shape) == 1
    assert sigmoid_exposure(1, shape=shape) == 0
    result = equivalent_time_power(np.ones(1000), dose / 1000, shape=shape)
    assert result[-1] == pytest.approx(0.8)
    np.testing.assert_allclose(
        result, sigmoid_power(np.arange(1001) * dose / 1000, shape=shape), atol=1e-12
    )


def test_variable_stress_is_cumulative_not_current_rate_times_total_age():
    dt, rates = np.array([10, 20, 10, 10]), np.array([0.05, 0.15, 0, 0.02])
    result = equivalent_time_power(dt, rates, shape=4)
    expected = (1 + np.exp(-4)) / (1 + np.exp(np.r_[0, np.cumsum(dt * rates)] - 4))
    np.testing.assert_allclose(result, expected)
    assert result[3] == result[2]
    assert np.all(np.diff(result) <= 0)
    # Subdividing constant-stress intervals does not change their endpoints.
    fine = equivalent_time_power(np.repeat(dt / 10, 10), np.repeat(rates, 10), shape=4)
    np.testing.assert_allclose(fine[::10], result, atol=1e-13)


def test_changing_shape_preserves_previous_damage():
    p1 = (1 + np.exp(-2)) / (1 + np.exp(0.1 * 20 - 2))
    equivalent_age = (7 + np.log((1 + np.exp(-7)) / p1 - 1)) / 0.03
    p2 = (1 + np.exp(-7)) / (1 + np.exp(0.03 * (equivalent_age + 10) - 7))
    result = equivalent_time_power([20, 10], [0.1, 0.03], shape=[2, 7])
    np.testing.assert_allclose(result, [1, p1, p2])
    assert result[-1] < result[-2]


def test_mode_product_and_horizon_censoring():
    np.testing.assert_allclose(independent_mode_power([[1, 0.9], [1, 0.8]]), [1, 0.72])
    assert threshold_crossing([0, 30, 50], [1, 0.9, 0.7]) == pytest.approx(40)
    assert threshold_crossing([0, 30, 50], [1, 0.9, 0.85]) is None
    assert threshold_crossing([0, 30, 50], [1, 0.9, 0.8]) == 50
    assert threshold_crossing([37, 50], [0.55, 0.4]) == 37


@pytest.mark.parametrize(
    "steps,rate,shape",
    [
        ([], 1, 1),
        ([0], 1, 1),
        ([-1], 1, 1),
        ([1, 1], [1], 1),
        ([1], -1, 1),
        ([1], 1, np.nan),
        ([1], 1, -1),
        ([[1]], 1, 1),
        ([1e308], 1e308, 1),
    ],
)
def test_invalid_stress_histories(steps, rate, shape):
    with pytest.raises(ValueError):
        equivalent_time_power(steps, rate, shape=shape)


@pytest.mark.parametrize("power", [0, -1, 1.01, np.nan])
def test_invalid_inverse(power):
    with pytest.raises(ValueError):
        sigmoid_exposure(power, shape=4)


@pytest.mark.parametrize(
    "age,power",
    [
        ([0, 0], [1, 0.9]),
        ([0, 1], [0.8, 0.9]),
        ([0, 1], [1]),
        ([0, 1], [1, np.nan]),
        ([-1, 1], [1, 0.9]),
    ],
)
def test_invalid_crossings(age, power):
    with pytest.raises(ValueError):
        threshold_crossing(age, power)


def test_invalid_power_and_mode_matrices():
    for values in ([1, 0.9], [[1.01]], [[-0.1]], [[np.nan]], []):
        with pytest.raises(ValueError):
            independent_mode_power(values)
    with pytest.raises(ValueError):
        sigmoid_power(-1, shape=4)
    with pytest.raises(ValueError):
        threshold_crossing([0, 1], [1, 0.9], threshold=1)
