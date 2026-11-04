"""Independent calculations check integration and missing-cell semantics."""

import numpy as np
import pytest

from energy_methods.pvdeg import thermal_stress_index


def test_constant_and_weighted_exposure():
    temperature = np.array([[25.0, 35.0], [25.0, 45.0]])
    result = thermal_stress_index(temperature, np.array([1.0, 3.0]))
    expected = np.exp(60000 / 8.31446261815324 * (1 / 298.15 - 1 / (temperature + 273.15)))
    np.testing.assert_allclose(result, np.average(expected, axis=0, weights=[1, 3]))
    assert result[0] == pytest.approx(1)
    assert result[1] > result[0]


def test_missing_period_invalidates_cell():
    result = thermal_stress_index(np.array([[25.0, np.nan], [25.0, 20.0]]), np.ones(2))
    assert result[0] == pytest.approx(1)
    assert np.isnan(result[1])


@pytest.mark.parametrize(
    "temperature,hours", [([20], [0]), ([-274], [1]), ([np.inf], [1]), ([], [])]
)
def test_invalid_inputs(temperature, hours):
    with pytest.raises(ValueError):
        thermal_stress_index(np.array(temperature), np.array(hours))
