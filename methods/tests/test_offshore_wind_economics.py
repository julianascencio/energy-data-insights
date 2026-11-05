"""Independent energy and present-value checks for offshore wind economics."""

from dataclasses import replace

import pytest

from energy_methods.offshore_wind_economics import (
    OffshoreWindScenario,
    evaluate_offshore_wind,
    tariff_npv_jpy,
)


@pytest.fixture
def scenario() -> OffshoreWindScenario:
    return OffshoreWindScenario(
        capacity_mw=1,
        capex_jpy_per_kw=1000,
        opex_jpy_per_kw_year=100,
        net_capacity_factor=0.5,
        lifetime_years=2,
        discount_rate=0,
    )


def test_manual_zero_discount_energy_cost(scenario: OffshoreWindScenario) -> None:
    result = evaluate_offshore_wind(scenario)
    assert result.lifetime_energy_mwh == pytest.approx(8760)
    assert result.discounted_energy_kwh == pytest.approx(8_760_000)
    assert result.upfront_cost_jpy == pytest.approx(1_000_000)
    assert result.discounted_opex_jpy == pytest.approx(200_000)
    assert result.lcoe_jpy_per_kwh == pytest.approx(1_200_000 / 8_760_000)


def test_breakeven_tariff_zero_npv(scenario: OffshoreWindScenario) -> None:
    result = evaluate_offshore_wind(scenario)
    assert tariff_npv_jpy(scenario, result.lcoe_jpy_per_kwh) == pytest.approx(0, abs=1e-8)


def test_discount_rate_increases_lcoe(scenario: OffshoreWindScenario) -> None:
    base = evaluate_offshore_wind(scenario).lcoe_jpy_per_kwh
    financed = evaluate_offshore_wind(replace(scenario, discount_rate=0.08))
    assert financed.lcoe_jpy_per_kwh > base


def test_degradation_reduces_energy(scenario: OffshoreWindScenario) -> None:
    degraded = evaluate_offshore_wind(replace(scenario, annual_degradation=0.1))
    assert degraded.lifetime_energy_mwh == pytest.approx(4380 * 1.9)
    assert degraded.lcoe_jpy_per_kwh > evaluate_offshore_wind(scenario).lcoe_jpy_per_kwh


def test_mw_scale_does_not_change_lcoe(scenario: OffshoreWindScenario) -> None:
    enlarged = evaluate_offshore_wind(replace(scenario, capacity_mw=500))
    baseline = evaluate_offshore_wind(scenario)
    assert enlarged.lcoe_jpy_per_kwh == pytest.approx(baseline.lcoe_jpy_per_kwh)
    assert enlarged.lifetime_energy_mwh == pytest.approx(500 * baseline.lifetime_energy_mwh)


@pytest.mark.parametrize(
    "attribute,value",
    [
        ("capacity_mw", 0),
        ("capex_jpy_per_kw", -1),
        ("opex_jpy_per_kw_year", -1),
        ("net_capacity_factor", 0),
        ("net_capacity_factor", 1.01),
        ("lifetime_years", 0),
        ("lifetime_years", 2.5),
        ("discount_rate", -0.01),
        ("discount_rate", float("nan")),
        ("annual_degradation", 1),
    ],
)
def test_reject_invalid_inputs(scenario: OffshoreWindScenario, attribute: str, value: float) -> None:
    with pytest.raises(ValueError):
        evaluate_offshore_wind(replace(scenario, **{attribute: value}))


def test_reject_invalid_tariff(scenario: OffshoreWindScenario) -> None:
    with pytest.raises(ValueError):
        tariff_npv_jpy(scenario, -1)
