"""Independent cash-flow and policy-allocation tests for battery LCOS."""

from dataclasses import replace

import pytest

from energy_methods.storage_viability import (
    INDIA_2026_BESS_GWH,
    INDIA_2026_OTHER_STORAGE_GWH,
    INDIA_2026_PUMPED_STORAGE_GWH,
    INDIA_2026_SCHEME_GWH,
    BatteryLcosAssumptions,
    battery_lcos,
    hypothetical_bess_vgf_inr_per_kwh,
)


@pytest.fixture
def case() -> BatteryLcosAssumptions:
    return BatteryLcosAssumptions(
        capex_inr_per_kwh=1_000,
        fixed_om_inr_per_kwh_year=0,
        cycles_per_year=100,
        lifetime_years=1,
        discount_rate=0,
        round_trip_efficiency=1,
        depth_of_discharge=1,
        annual_capacity_fade=0,
    )


def test_published_total_capacity_mix() -> None:
    assert (
        INDIA_2026_BESS_GWH + INDIA_2026_PUMPED_STORAGE_GWH + INDIA_2026_OTHER_STORAGE_GWH
        == INDIA_2026_SCHEME_GWH
    )


def test_zero_grant_zero_budget_share() -> None:
    assert hypothetical_bess_vgf_inr_per_kwh(0) == pytest.approx(0)


def test_budget_share_unit_conversion() -> None:
    # 20% of 14,500 crore = 29 billion INR / (30 million kWh).
    assert hypothetical_bess_vgf_inr_per_kwh(0.2) == pytest.approx(966.6666666666666)


def test_battery_lcos_one_year_exact(case: BatteryLcosAssumptions) -> None:
    result = battery_lcos(case)
    assert result.discounted_delivered_kwh_per_kwh == pytest.approx(100)
    assert result.lcos_inr_per_kwh == pytest.approx(10)


def test_grant_reduces_lcos(case: BatteryLcosAssumptions) -> None:
    assert battery_lcos(case, hypothetical_grant_inr_per_kwh=200).lcos_inr_per_kwh == pytest.approx(
        8
    )


def test_discount_and_om(case: BatteryLcosAssumptions) -> None:
    result = battery_lcos(replace(case, discount_rate=0.1, fixed_om_inr_per_kwh_year=100))
    assert result.discounted_delivered_kwh_per_kwh == pytest.approx(100 / 1.1)
    assert result.discounted_om_inr_per_kwh == pytest.approx(100 / 1.1)
    assert result.lcos_inr_per_kwh == pytest.approx(12)


def test_fade_and_efficiency(case: BatteryLcosAssumptions) -> None:
    result = battery_lcos(
        replace(case, lifetime_years=2, round_trip_efficiency=0.8, annual_capacity_fade=0.25)
    )
    assert result.discounted_delivered_kwh_per_kwh == pytest.approx(140)


def test_more_cycles_lowers_lcos(case: BatteryLcosAssumptions) -> None:
    assert (
        battery_lcos(replace(case, cycles_per_year=200)).lcos_inr_per_kwh
        < battery_lcos(case).lcos_inr_per_kwh
    )


@pytest.mark.parametrize("share", [-0.1, 1.1, float("nan"), float("inf")])
def test_invalid_budget_shares(share: float) -> None:
    with pytest.raises(ValueError, match="budget share"):
        hypothetical_bess_vgf_inr_per_kwh(share)


@pytest.mark.parametrize(
    "updates",
    [
        {"capex_inr_per_kwh": 0},
        {"fixed_om_inr_per_kwh_year": -1},
        {"cycles_per_year": 0},
        {"cycles_per_year": 400},
        {"lifetime_years": 0},
        {"lifetime_years": 2.0},
        {"discount_rate": -0.01},
        {"round_trip_efficiency": 0},
        {"depth_of_discharge": 1.1},
        {"annual_capacity_fade": 1},
        {"capex_inr_per_kwh": float("nan")},
    ],
)
def test_invalid_cases(case: BatteryLcosAssumptions, updates: dict[str, float]) -> None:
    with pytest.raises(ValueError):
        replace(case, **updates)


@pytest.mark.parametrize("grant", [-1, 1_001, float("inf"), float("nan")])
def test_invalid_grants(case: BatteryLcosAssumptions, grant: float) -> None:
    with pytest.raises(ValueError, match="grant"):
        battery_lcos(case, hypothetical_grant_inr_per_kwh=grant)
