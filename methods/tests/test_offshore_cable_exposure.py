"""Independent energy-balance checks for hypothetical cable capacity outages."""

import math
from typing import Any

import pytest

from energy_methods.offshore_cable_exposure import calculate_cable_exposure


def test_hand_computed_full_export_outage() -> None:
    result = calculate_cable_exposure(
        [5, 10, 6, 2],
        export_capacity_mw=8,
        outage_start_interval=1,
        outage_intervals=2,
        outage_export_capacity_mw=0,
    )
    assert result.available_wind_mwh == pytest.approx(23)
    assert result.baseline_export_mwh == pytest.approx(21)
    assert result.outage_export_mwh == pytest.approx(7)
    assert result.incremental_lost_export_mwh == pytest.approx(14)
    assert result.baseline_curtailed_mwh == pytest.approx(2)
    assert result.outage_curtailed_mwh == pytest.approx(16)


def test_partial_transfer_and_existing_curtailment() -> None:
    result = calculate_cable_exposure(
        [9, 2, 8],
        export_capacity_mw=7,
        outage_start_interval=0,
        outage_intervals=3,
        outage_export_capacity_mw=4,
    )
    assert result.baseline_export_mwh == pytest.approx(16)
    assert result.outage_export_mwh == pytest.approx(10)
    assert result.incremental_lost_export_mwh == pytest.approx(6)
    assert result.outage_curtailed_mwh - result.baseline_curtailed_mwh == pytest.approx(6)


def test_zero_duration_and_full_redundancy() -> None:
    for duration, remaining in ((0, 0), (3, 10)):
        result = calculate_cable_exposure(
            [5, 7, 8],
            export_capacity_mw=10,
            outage_start_interval=0,
            outage_intervals=duration,
            outage_export_capacity_mw=remaining,
        )
        assert result.incremental_lost_export_mwh == pytest.approx(0)


def test_subhourly_energy_units_and_residual_limit() -> None:
    result = calculate_cable_exposure(
        [2, 4],
        export_capacity_mw=4,
        outage_start_interval=0,
        outage_intervals=2,
        outage_export_capacity_mw=1,
        timestep_hours=0.5,
    )
    assert result.incremental_lost_export_mwh == pytest.approx(2)
    assert result.outage_hours == pytest.approx(1)
    assert result.incremental_lost_export_mwh <= 3 * result.outage_hours


def test_loss_monotonic_with_reduced_transfer_capacity() -> None:
    generation = [2, 5, 8, 4, 9]
    losses = [
        calculate_cable_exposure(
            generation,
            export_capacity_mw=8,
            outage_start_interval=0,
            outage_intervals=5,
            outage_export_capacity_mw=cap,
        ).incremental_lost_export_mwh
        for cap in (0, 2, 4, 8)
    ]
    assert losses == sorted(losses, reverse=True)


@pytest.mark.parametrize(
    "generation,options",
    [
        ([], {}),
        ([-1], {}),
        ([math.nan], {}),
        ([float("inf")], {}),
        ([1], {"export_capacity_mw": -1}),
        ([1], {"outage_export_capacity_mw": 11}),
        ([1], {"outage_start_interval": -1}),
        ([1], {"outage_start_interval": 1}),
        ([1], {"outage_intervals": 2}),
        ([1], {"outage_intervals": -1}),
        ([1], {"outage_intervals": 1.5}),
        ([1], {"outage_start_interval": True}),
        ([1], {"timestep_hours": 0}),
    ],
)
def test_invalid_inputs(generation: list[float], options: dict[str, Any]) -> None:
    kwargs = dict(
        export_capacity_mw=10,
        outage_start_interval=0,
        outage_intervals=1,
        outage_export_capacity_mw=0,
        timestep_hours=1,
    )
    kwargs.update(options)
    with pytest.raises(ValueError):
        calculate_cable_exposure(generation, **kwargs)
