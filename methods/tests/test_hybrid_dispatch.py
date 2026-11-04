"""Energy-balance and edge-case checks for the illustrative hybrid dispatcher."""

import pytest

from energy_methods.hybrid_dispatch import simulate_hybrid


def test_no_storage_baseline() -> None:
    result = simulate_hybrid([0, 10], [0, 0], [5, 5], battery_mwh=0, battery_mw=0)
    assert result.coverage == pytest.approx(0.5)
    assert result.curtailed_mwh == pytest.approx(5)
    assert result.unserved_mwh == pytest.approx(5)


def test_storage_shifts_surplus() -> None:
    result = simulate_hybrid([10, 0], [0, 0], [5, 5], battery_mwh=5, battery_mw=5, efficiency=1)
    assert result.coverage == pytest.approx(1)
    assert result.discharged_mwh == pytest.approx(5)
    assert result.unserved_mwh == pytest.approx(0)


def test_round_trip_loss() -> None:
    result = simulate_hybrid([10, 0], [0, 0], [5, 5], battery_mwh=5, battery_mw=5, efficiency=0.81)
    assert result.discharged_mwh == pytest.approx(4.05)
    assert result.coverage == pytest.approx(0.905)


@pytest.mark.parametrize(
    "wind,solar,demand",
    [
        ([], [], []),
        ([1], [], [1]),
        ([-1], [0], [1]),
        ([float("nan")], [0], [1]),
    ],
)
def test_invalid_profiles(wind: list[float], solar: list[float], demand: list[float]) -> None:
    with pytest.raises(ValueError):
        simulate_hybrid(wind, solar, demand, battery_mwh=1, battery_mw=1)
