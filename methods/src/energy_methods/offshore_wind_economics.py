"""Discounted offshore-wind energy costs with explicit physical and financial units.

Pure engineering-economics calculation; not a project valuation or price forecast.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

HOURS_PER_YEAR = 8760.0


@dataclass(frozen=True)
class OffshoreWindScenario:
    """Simplified annual-average scenario; costs and tariff use constant real JPY.

    ``net_capacity_factor`` includes availability, wake and electrical losses.
    Commissioning occurs at year zero; energy and O&M occur at year end.
    Degradation is applied from the second operating year onward.
    """

    capacity_mw: float
    capex_jpy_per_kw: float
    opex_jpy_per_kw_year: float
    net_capacity_factor: float
    lifetime_years: int
    discount_rate: float
    annual_degradation: float = 0.0


@dataclass(frozen=True)
class OffshoreWindEconomics:
    """Present-value accounting result, with monetary values in real JPY."""

    lcoe_jpy_per_kwh: float
    lifetime_energy_mwh: float
    discounted_energy_kwh: float
    discounted_cost_jpy: float
    upfront_cost_jpy: float
    discounted_opex_jpy: float


def evaluate_offshore_wind(scenario: OffshoreWindScenario) -> OffshoreWindEconomics:
    """Compute discounted LCOE from annual net energy, investment and fixed O&M.

    ``LCOE = (CAPEX + sum(OPEX_t / (1 + r)^t)) /
    sum(E_t / (1 + r)^t)``. Capacity factor, degradation and real WACC
    are *assumptions*, not observations or inferred likelihood distributions.
    There is no replacement CAPEX, revenue stacking, tax, salvage or debt model.
    """
    fields = (
        scenario.capacity_mw,
        scenario.capex_jpy_per_kw,
        scenario.opex_jpy_per_kw_year,
        scenario.net_capacity_factor,
        scenario.discount_rate,
        scenario.annual_degradation,
    )
    if not all(math.isfinite(value) for value in fields):
        raise ValueError("All scenario quantities must be finite")
    if scenario.capacity_mw <= 0 or scenario.capex_jpy_per_kw < 0:
        raise ValueError("Capacity must be positive and CAPEX nonnegative")
    if scenario.opex_jpy_per_kw_year < 0:
        raise ValueError("OPEX must be nonnegative")
    if not 0 < scenario.net_capacity_factor <= 1:
        raise ValueError("Net capacity factor must be in (0, 1]")
    if (
        not isinstance(scenario.lifetime_years, int)
        or isinstance(scenario.lifetime_years, bool)
        or scenario.lifetime_years < 1
    ):
        raise ValueError("Lifetime must be a positive whole number of years")
    if not 0 <= scenario.discount_rate < 1:
        raise ValueError("Real discount rate must be in [0, 1)")
    if not 0 <= scenario.annual_degradation < 1:
        raise ValueError("Annual degradation must be in [0, 1)")
    capacity_kw = scenario.capacity_mw * 1000.0
    annual_energy_kwh = capacity_kw * HOURS_PER_YEAR * scenario.net_capacity_factor
    annual_opex = capacity_kw * scenario.opex_jpy_per_kw_year
    discounted_energy = 0.0
    lifetime_energy = 0.0
    discounted_opex = 0.0
    for year in range(1, scenario.lifetime_years + 1):
        generated = annual_energy_kwh * (1 - scenario.annual_degradation) ** (year - 1)
        discount = (1 + scenario.discount_rate) ** year
        lifetime_energy += generated
        discounted_energy += generated / discount
        discounted_opex += annual_opex / discount
    upfront = capacity_kw * scenario.capex_jpy_per_kw
    total_cost = upfront + discounted_opex
    return OffshoreWindEconomics(
        lcoe_jpy_per_kwh=total_cost / discounted_energy,
        lifetime_energy_mwh=lifetime_energy / 1000.0,
        discounted_energy_kwh=discounted_energy,
        discounted_cost_jpy=total_cost,
        upfront_cost_jpy=upfront,
        discounted_opex_jpy=discounted_opex,
    )


def tariff_npv_jpy(scenario: OffshoreWindScenario, tariff_jpy_per_kwh: float) -> float:
    """NPV of a flat *real* tariff, ignoring subsidies, contracts and taxes."""
    if not math.isfinite(tariff_jpy_per_kwh) or tariff_jpy_per_kwh < 0:
        raise ValueError("Tariff must be finite and nonnegative")
    result = evaluate_offshore_wind(scenario)
    return tariff_jpy_per_kwh * result.discounted_energy_kwh - result.discounted_cost_jpy
