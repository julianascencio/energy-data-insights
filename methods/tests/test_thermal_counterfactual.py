"""Independent event calculations and censoring rules."""

import numpy as np
import pytest

from energy_methods.thermal_counterfactual import comfort_time, paired_shift_error


def test_crossing_and_isolated_spike():
    assert comfort_time([0, 15, 30], [20, 21, 21], threshold_c=20.5) == 7.5
    assert comfort_time([0, 15, 30, 45, 60], [19, 21, 19, 21, 22], threshold_c=20) == 37.5
    assert comfort_time([0, 15], [19, 21]) is None
    assert comfort_time([0, 15], [21, 21]) == 0


def test_gated_crossing_is_explicit():
    assert comfort_time([0, 15, 30], [20, 21, 21], not_before_min=15) == 15
    assert comfort_time([0, 15], [21, 21], not_before_min=30) is None


def test_intervention_sign_and_censoring():
    assert paired_shift_error(75, 60, 120, 60) == -45
    assert paired_shift_error(None, 60, 120, 60) is None
    with pytest.raises(ValueError):
        paired_shift_error(np.inf, 0, 0, 0)


@pytest.mark.parametrize(
    "x,y", [([], []), ([0, 0], [20, 21]), ([0, 15], [20, np.nan]), ([0, 15], [20])]
)
def test_invalid_arrays(x, y):
    with pytest.raises(ValueError):
        comfort_time(x, y)
