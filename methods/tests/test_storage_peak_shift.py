"""Analytical balance checks for grid-free renewable-to-evening storage shift."""

import pytest

from energy_methods.storage_peak_shift import simulate_storage_peak_shift


def test_no_storage_and_energy_accounting() -> None:
    result = simulate_storage_peak_shift(
        [10, 0], [0, 5], battery_power_mw=0, battery_energy_mwh=0
    )
    assert result.peak_coverage == 0
    assert result.curtailed_mwh == 10
    assert result.steps[-1].unmet_peak_mwh == 5


def test_perfect_round_trip_and_power_limit() -> None:
    result = simulate_storage_peak_shift(
        [8, 0, 0],
        [0, 4, 4],
        battery_power_mw=4,
        battery_energy_mwh=8,
        round_trip_efficiency=1,
    )
    assert result.peak_delivered_mwh == pytest.approx(4)
    assert result.steps[0].charged_input_mwh == 4
    assert result.steps[0].soc_mwh == 4
    assert result.final_soc_mwh == 0
    assert result.peak_coverage == 0.5


def test_round_trip_efficiency() -> None:
    result = simulate_storage_peak_shift(
        [10, 0],
        [0, 10],
        battery_power_mw=10,
        battery_energy_mwh=10,
        round_trip_efficiency=0.81,
    )
    assert result.peak_delivered_mwh == pytest.approx(8.1)
    assert result.peak_coverage == pytest.approx(0.81)
    assert result.final_soc_mwh == pytest.approx(0)


def test_energy_capacity_and_demand_cap() -> None:
    result = simulate_storage_peak_shift(
        [100, 0], [0, 1], battery_power_mw=20, battery_energy_mwh=2,
        round_trip_efficiency=1,
    )
    assert result.peak_delivered_mwh == 1
    assert result.final_soc_mwh == 1
    assert result.curtailed_mwh == 98


def test_zero_peak_shortfall_is_covered() -> None:
    result = simulate_storage_peak_shift(
        [0, 0], [0, 0], battery_power_mw=2, battery_energy_mwh=2
    )
    assert result.peak_coverage == 1.0
    assert result.peak_shortfall_mwh == 0


@pytest.mark.parametrize(
    "surplus,shortfall,power,energy,efficiency,dt,soc",
    [
        ([], [], 1, 1, 0.9, 1, 0),
        ([1], [1], 1, 1, 0.9, 1, 0),
        ([1], [], 1, 1, 0.9, 1, 0),
        ([-1], [0], 1, 1, 0.9, 1, 0),
        ([float("nan")], [0], 1, 1, 0.9, 1, 0),
        ([1], [0], -1, 1, 0.9, 1, 0),
        ([1], [0], 1, 1, 1.1, 1, 0),
        ([1], [0], 1, 1, 0.9, 0, 0),
        ([1], [0], 1, 1, 0.9, 1, 2),
    ],
)
def test_invalid_inputs(
    surplus: list[float],
    shortfall: list[float],
    power: float,
    energy: float,
    efficiency: float,
    dt: float,
    soc: float,
) -> None:
    with pytest.raises(ValueError):
        simulate_storage_peak_shift(
            surplus,
            shortfall,
            battery_power_mw=power,
            battery_energy_mwh=energy,
            round_trip_efficiency=efficiency,
            timestep_hours=dt,
            initial_soc_mwh=soc,
        )
