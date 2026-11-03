"""Independent arithmetic and boundary checks for repairable PV scenarios."""

import numpy as np
import pytest

from energy_methods.pv_operation import ComponentScenario, simulate_operation
from energy_methods.pv_reliability import ReliabilityCurve


def test_certain_failure_and_outage_cap():
    result = simulate_operation(
        curve=ReliabilityCurve("exponential", 0),
        initial_annual_energy_mwh=100,
        components=(ComponentScenario("a", 1, 0.7, 5), ComponentScenario("b", 1, 0.6, 3)),
        years=2,
        trials=2,
    )
    assert (result.energy_mwh == 0).all()
    assert result.cumulative_replacement_cost.tolist() == [8, 16, 8, 16]
    assert not result.original_components_survive.any()


def test_no_failures_and_midpoint_energy():
    result = simulate_operation(
        curve=ReliabilityCurve("linear", 0.01),
        initial_annual_energy_mwh=100,
        components=(),
        years=2,
        trials=1,
    )
    np.testing.assert_allclose(result.energy_mwh, [99.5, 98.5])
    assert result.cumulative_energy_mwh.iloc[-1] == 198
    assert result.original_components_survive.all()


def test_replay_and_survival():
    kwargs = dict(
        curve=ReliabilityCurve("exponential", 0.005),
        initial_annual_energy_mwh=100,
        years=10,
        trials=10000,
        components=(ComponentScenario("a", 0.1, 0.01, 5),),
        seed=42,
    )
    result = simulate_operation(**kwargs)
    assert result.equals(simulate_operation(**kwargs))
    survival = result[result.year == 10].original_components_survive.mean()
    assert abs(survival - 0.9**10) < 0.02


@pytest.mark.parametrize("probability", [-1, 1.1, float("nan")])
def test_invalid_probability(probability):
    with pytest.raises(ValueError):
        ComponentScenario("a", probability, 0, 0)


def test_negative_retention_rejected():
    with pytest.raises(ValueError, match="retention"):
        simulate_operation(
            curve=ReliabilityCurve("linear", 0.1), initial_annual_energy_mwh=100, components=()
        )
