"""Independent checks for vessel construction schedule and grid commissioning."""

import pytest

from energy_methods.wind_installation import (
    InstallationSchedule,
    commissioning_opportunity_mwh,
    simulate_installation,
)


def test_single_vessel_manual_count() -> None:
    schedule = simulate_installation(
        2,
        vessel_start_days=(0,),
        workable_days=(True, False, True, True, True),
        workable_days_per_turbine=2,
    )
    assert schedule.completion_days == (2, 4)
    assert schedule.duration_days == 5
    assert schedule.charter_vessel_days == 5


def test_second_vessel_shortens_campaign() -> None:
    one = simulate_installation(
        4,
        vessel_start_days=(0,),
        workable_days=[True] * 20,
        workable_days_per_turbine=2,
    )
    two = simulate_installation(
        4,
        vessel_start_days=(0, 2),
        workable_days=[True] * 20,
        workable_days_per_turbine=2,
    )
    assert one.duration_days == 8
    assert two.duration_days == 6
    assert two.completion_days == (1, 3, 3, 5)
    assert two.charter_vessel_days == 10


def test_bad_weather_halts_both_vessels() -> None:
    schedule = simulate_installation(
        2,
        vessel_start_days=(0, 0),
        workable_days=[False, True],
        workable_days_per_turbine=1,
    )
    assert schedule.completion_days == (1, 1)


def test_grid_ready_is_critical_path() -> None:
    early = simulate_installation(
        2,
        vessel_start_days=(0,),
        workable_days=[True] * 8,
        workable_days_per_turbine=2,
    )
    late = simulate_installation(
        2,
        vessel_start_days=(0, 0),
        workable_days=[True] * 8,
        workable_days_per_turbine=2,
    )

    def energy(schedule: InstallationSchedule, grid_day: int = 0) -> float:
        return commissioning_opportunity_mwh(
            schedule,
            project_capacity_mw=20,
            net_capacity_factor=0.5,
            horizon_days=10,
            grid_ready_day=grid_day,
        )

    assert energy(early) == pytest.approx(1680)
    assert energy(late) == pytest.approx(1920)
    assert energy(early, grid_day=8) == pytest.approx(480)
    assert energy(late, grid_day=8) == pytest.approx(480)


def test_zero_incremental_value_beyond_horizon() -> None:
    schedule = simulate_installation(
        1, vessel_start_days=(0,), workable_days=(True,), workable_days_per_turbine=1
    )
    result = commissioning_opportunity_mwh(
        schedule,
        project_capacity_mw=10,
        net_capacity_factor=0.4,
        horizon_days=10,
        grid_ready_day=20,
    )
    assert result == pytest.approx(0)


@pytest.mark.parametrize(
    "changes",
    [
        {"turbines": 0},
        {"vessel_start_days": ()},
        {"vessel_start_days": (-1,)},
        {"workable_days": ()},
        {"workable_days": (1,)},
        {"workable_days_per_turbine": 0.5},
        {"workable_days_per_turbine": float("nan")},
    ],
)
def test_invalid_installation_inputs(changes: dict[str, object]) -> None:
    parameters: dict[str, object] = {
        "turbines": 1,
        "vessel_start_days": (0,),
        "workable_days": (True,),
        "workable_days_per_turbine": 1,
    }
    parameters.update(changes)
    with pytest.raises(ValueError):
        simulate_installation(**parameters)


def test_insufficient_horizon_rejected() -> None:
    with pytest.raises(ValueError, match="weather horizon"):
        simulate_installation(
            2,
            vessel_start_days=(0,),
            workable_days=(False, True),
            workable_days_per_turbine=1,
        )


@pytest.mark.parametrize(
    "capacity,cf,days",
    [(0, 0.5, 8), (10, 0, 8), (10, 1.1, 8), (10, 0.5, 0), (10, 0.5, True)],
)
def test_invalid_energy_inputs(capacity: float, cf: float, days: int) -> None:
    schedule = simulate_installation(
        1,
        vessel_start_days=(0,),
        workable_days=(True,),
        workable_days_per_turbine=1,
    )
    with pytest.raises(ValueError):
        commissioning_opportunity_mwh(
            schedule,
            project_capacity_mw=capacity,
            net_capacity_factor=cf,
            horizon_days=days,
        )
