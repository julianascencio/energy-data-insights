"""Independent arithmetic checks for the PV press-release claim audit."""

import pytest

from energy_methods.pv_news_claims import audit_pv_news_claims

BASE = {
    "capacity_mwp": 20,
    "homes_equivalent": 8500,
    "annual_household_kwh": 2500,
    "avoided_co2_floor_tonnes": 6200,
    "grid_average_kgco2e_per_kwh": 0.13096,
}


def test_court_barton_benchmark_algebra() -> None:
    result = audit_pv_news_claims(**BASE)
    assert result.equivalent_generation_mwh == pytest.approx(21250)
    assert result.dc_equivalent_full_load_hours == pytest.approx(1062.5)
    assert result.dc_equivalent_capacity_factor == pytest.approx(21250 / (20 * 8760))
    assert result.co2_floor_kg_per_kwh == pytest.approx(6200 / 21250)
    assert result.grid_average_tonnes_co2e == pytest.approx(2782.9)


def test_household_sensitivity_is_not_measured_generation() -> None:
    low = audit_pv_news_claims(**{**BASE, "annual_household_kwh": 1600})
    high = audit_pv_news_claims(**{**BASE, "annual_household_kwh": 3800})
    assert low.equivalent_generation_mwh < high.equivalent_generation_mwh
    assert low.dc_equivalent_capacity_factor < high.dc_equivalent_capacity_factor
    assert low.co2_floor_kg_per_kwh > high.co2_floor_kg_per_kwh


def test_zero_grid_factor_is_valid_without_impact_claim() -> None:
    result = audit_pv_news_claims(**{**BASE, "grid_average_kgco2e_per_kwh": 0})
    assert result.grid_average_tonnes_co2e == 0
    assert result.co2_floor_kg_per_kwh > 0


@pytest.mark.parametrize(
    "field,value",
    [
        ("capacity_mwp", 0),
        ("homes_equivalent", -2),
        ("annual_household_kwh", float("nan")),
        ("avoided_co2_floor_tonnes", float("inf")),
        ("grid_average_kgco2e_per_kwh", -0.1),
        ("hours_per_year", 0),
    ],
)
def test_invalid_inputs_raise(field: str, value: float) -> None:
    with pytest.raises(ValueError):
        audit_pv_news_claims(**{**BASE, field: value})


def test_physical_infeasibility_is_exposed_not_hidden() -> None:
    result = audit_pv_news_claims(**{**BASE, "annual_household_kwh": 30_000})
    assert result.dc_equivalent_capacity_factor > 1
