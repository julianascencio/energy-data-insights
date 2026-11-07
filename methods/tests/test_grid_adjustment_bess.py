"""Independent numerical and boundary tests of non-market BESS screening."""

import math

import pytest

from energy_methods.grid_adjustment_bess import (
    infer_aggregate_unit_cost_growth,
    screen_complete_bess_cycle,
)


def test_reported_growth_decomposition() -> None:
    result = infer_aggregate_unit_cost_growth(26.4, 43.4)
    assert result.energy_index == pytest.approx(1.264)
    assert result.cost_index == pytest.approx(1.434)
    assert result.implied_unit_cost_index == pytest.approx(1.434 / 1.264)
    assert result.implied_unit_cost_growth_pct == pytest.approx(13.449367088607599)


def test_one_cycle_cash_and_energy_balance() -> None:
    r = screen_complete_bess_cycle(
        charge_price_eur_mwh=60,
        sale_price_eur_mwh=120,
        battery_power_mw=1,
        usable_energy_mwh=2,
        charging_hours=2,
        discharging_hours=2,
        round_trip_efficiency=0.9,
        wear_eur_per_delivered_mwh=10,
    )
    assert r.charged_mwh == pytest.approx(2)
    assert r.delivered_mwh == pytest.approx(1.8)
    assert r.peak_soc_mwh == pytest.approx(2 * math.sqrt(0.9))
    assert r.conversion_loss_mwh == pytest.approx(0.2)
    assert r.purchase_cost_eur == pytest.approx(120)
    assert r.sale_revenue_eur == pytest.approx(216)
    assert r.wear_cost_eur == pytest.approx(18)
    assert r.contribution_eur == pytest.approx(78)
    assert r.break_even_sale_price_eur_mwh == pytest.approx(60 / 0.9 + 10)


def test_baseline_zero_battery() -> None:
    r = screen_complete_bess_cycle(
        charge_price_eur_mwh=50,
        sale_price_eur_mwh=200,
        battery_power_mw=0,
        usable_energy_mwh=0,
        charging_hours=2,
        discharging_hours=2,
    )
    assert r.charged_mwh == r.delivered_mwh == r.contribution_eur == 0


def test_usable_capacity_is_stored_energy_not_grid_input() -> None:
    r = screen_complete_bess_cycle(
        charge_price_eur_mwh=10,
        sale_price_eur_mwh=100,
        battery_power_mw=10,
        usable_energy_mwh=1,
        charging_hours=1,
        discharging_hours=1,
        round_trip_efficiency=0.81,
    )
    assert r.peak_soc_mwh == pytest.approx(1)
    assert r.charged_mwh == pytest.approx(1 / 0.9)
    assert r.delivered_mwh == pytest.approx(0.9)


def test_discharge_window_limits_complete_cycle() -> None:
    r = screen_complete_bess_cycle(
        charge_price_eur_mwh=20,
        sale_price_eur_mwh=80,
        battery_power_mw=1,
        usable_energy_mwh=10,
        charging_hours=5,
        discharging_hours=1,
        round_trip_efficiency=0.8,
    )
    assert r.delivered_mwh == pytest.approx(1)
    assert r.charged_mwh == pytest.approx(1 / 0.8)


def test_negative_market_prices_are_valid() -> None:
    r = screen_complete_bess_cycle(
        charge_price_eur_mwh=-10,
        sale_price_eur_mwh=20,
        battery_power_mw=1,
        usable_energy_mwh=2,
        charging_hours=2,
        discharging_hours=2,
    )
    assert r.contribution_eur > 0


def test_equal_prices_cause_loss_below_unity_efficiency() -> None:
    r = screen_complete_bess_cycle(
        charge_price_eur_mwh=100,
        sale_price_eur_mwh=100,
        battery_power_mw=1,
        usable_energy_mwh=2,
        charging_hours=2,
        discharging_hours=2,
    )
    assert r.contribution_eur < 0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"charge_price_eur_mwh": float("nan")},
        {"battery_power_mw": -1},
        {"usable_energy_mwh": -1},
        {"charging_hours": 0},
        {"discharging_hours": 0},
        {"round_trip_efficiency": 0},
        {"round_trip_efficiency": 1.1},
        {"wear_eur_per_delivered_mwh": -2},
    ],
)
def test_invalid_cycle_inputs(kwargs: dict[str, float]) -> None:
    params = dict(
        charge_price_eur_mwh=30.0,
        sale_price_eur_mwh=100.0,
        battery_power_mw=1.0,
        usable_energy_mwh=2.0,
        charging_hours=2.0,
        discharging_hours=2.0,
    )
    params.update(kwargs)
    with pytest.raises(ValueError):
        screen_complete_bess_cycle(**params)


@pytest.mark.parametrize("energy,cost", [(float("inf"), 5), (-100, 0), (1, -101)])
def test_invalid_growth_values(energy: float, cost: float) -> None:
    with pytest.raises(ValueError):
        infer_aggregate_unit_cost_growth(energy, cost)
