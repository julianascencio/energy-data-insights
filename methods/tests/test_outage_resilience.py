"""Independent physics and edge tests for islanded critical-load storage sizing."""

from datetime import datetime

import pytest

from energy_methods.hybrid_dispatch import simulate_hybrid
from energy_methods.outage_resilience import minimum_islanded_capacity


def test_blackout_timeline_primary_source() -> None:
    # Red Electrica, 2026-11-02, La Palma restoration: 06:38 to 10:26 local.
    start = datetime.fromisoformat("2026-11-02T06:38:00+00:00")
    restored = datetime.fromisoformat("2026-11-02T10:26:00+00:00")
    assert (restored - start).total_seconds() == 228 * 60


def test_no_generation_matches_hand_balance() -> None:
    # 0.5 MW x 3.8 h / (80% SOC x 95% discharge efficiency) = 2.5 MWh.
    intervals = 76
    result = minimum_islanded_capacity(
        [0.0] * intervals,
        [0.0] * intervals,
        [0.5] * intervals,
        inverter_mw=0.65,
        timestep_hours=0.05,
        roundtrip_efficiency=0.95**2,
    )
    assert result == pytest.approx(2.5, abs=1e-6)
    check = simulate_hybrid(
        [0.0] * intervals, [0.0] * intervals, [0.5] * intervals,
        battery_mwh=result + 1e-6, battery_mw=0.65,
        initial_soc_mwh=(result + 1e-6) * 0.8, efficiency=0.95**2,
        timestep_hours=0.05,
    )
    assert check.unserved_mwh <= 1e-6


def test_renewables_reduce_required_energy() -> None:
    windy = minimum_islanded_capacity(
        [0.1] * 10, [0.0] * 10, [0.5] * 10,
        inverter_mw=0.5, timestep_hours=0.5, roundtrip_efficiency=1,
    )
    still = minimum_islanded_capacity(
        [0.0] * 10, [0.0] * 10, [0.5] * 10,
        inverter_mw=0.5, timestep_hours=0.5, roundtrip_efficiency=1,
    )
    assert windy == pytest.approx(2.5)
    assert still == pytest.approx(3.125)


def test_renewables_alone_need_no_battery() -> None:
    assert minimum_islanded_capacity(
        [0.5], [0.0], [0.5], inverter_mw=0.0,
    ) == 0.0


def test_inverter_power_infeasible() -> None:
    with pytest.raises(ValueError, match="No feasible capacity"):
        minimum_islanded_capacity(
            [0.0], [0.0], [1.0], inverter_mw=0.5,
        max_capacity_mwh=100,
    )


@pytest.mark.parametrize(
    "keyword,value",
    [
        ("initial_soc_fraction", -0.1),
        ("initial_soc_fraction", 1.1),
        ("roundtrip_efficiency", 0.0),
        ("inverter_mw", float("nan")),
        ("max_capacity_mwh", 0),
        ("timestep_hours", 0),
    ],
)
def test_invalid_settings(keyword: str, value: float) -> None:
    options = {keyword: value}
    with pytest.raises(ValueError):
        minimum_islanded_capacity([0.0], [0.0], [1.0], inverter_mw=1.0,
                                  **{key: val for key, val in options.items()
                                     if key != "inverter_mw"})
