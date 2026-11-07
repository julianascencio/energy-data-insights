"""Reported adjustment-cost decomposition and hypothetical BESS spread screening.

Not a BESS revenue forecast or a model of technical-constraint settlements.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class CostGrowth:
    """Index-based year-on-year decomposition of reported aggregate costs."""

    energy_index: float
    cost_index: float
    implied_unit_cost_index: float
    implied_unit_cost_growth_pct: float


@dataclass(frozen=True)
class BessCycleScreen:
    """One complete price-taking cycle, with energy and cash in MWh and EUR."""

    charged_mwh: float
    delivered_mwh: float
    conversion_loss_mwh: float
    peak_soc_mwh: float
    purchase_cost_eur: float
    sale_revenue_eur: float
    wear_cost_eur: float
    contribution_eur: float
    break_even_sale_price_eur_mwh: float


def infer_aggregate_unit_cost_growth(
    energy_growth_pct: float, cost_growth_pct: float
) -> CostGrowth:
    """Separate volume and implied average-unit-cost effects of aggregate growth.

    Indices use an arbitrary previous-period reference of 1. The reported
    aggregates must refer to the same accounting boundary and compared periods.
    These are *not* merchant energy prices or a causal price decomposition.
    """
    if (
        not math.isfinite(energy_growth_pct)
        or not math.isfinite(cost_growth_pct)
        or energy_growth_pct <= -100
        or cost_growth_pct <= -100
    ):
        raise ValueError("Both growth percentages must be finite and greater than -100")
    energy_index = 1 + energy_growth_pct / 100
    cost_index = 1 + cost_growth_pct / 100
    unit_index = cost_index / energy_index
    return CostGrowth(energy_index, cost_index, unit_index, 100 * (unit_index - 1))


def screen_complete_bess_cycle(
    *,
    charge_price_eur_mwh: float,
    sale_price_eur_mwh: float,
    battery_power_mw: float,
    usable_energy_mwh: float,
    charging_hours: float,
    discharging_hours: float,
    round_trip_efficiency: float = 0.9,
    wear_eur_per_delivered_mwh: float = 0.0,
) -> BessCycleScreen:
    """Evaluate a *prescribed*, complete charge/discharge cycle at flat prices.

    Prices may be negative. Charging/discharging windows cannot overlap;
    durations and prices are assumed exogenous. Charge/discharge efficiencies
    each equal sqrt(round_trip_efficiency). The algorithm limits charge energy
    by battery MW, usable stored MWh, and later discharge MW; the whole charge
    is discharged, returning to the starting SOC (zero). No hourly optimizer,
    market access rights, auxiliary demand, fixed costs, reserves or taxes.
    The maximum physical cycle is evaluated even when its margin is negative.
    """
    vals = (
        charge_price_eur_mwh,
        sale_price_eur_mwh,
        battery_power_mw,
        usable_energy_mwh,
        charging_hours,
        discharging_hours,
        round_trip_efficiency,
        wear_eur_per_delivered_mwh,
    )
    if not all(math.isfinite(x) for x in vals):
        raise ValueError("All inputs must be finite")
    if (
        battery_power_mw < 0
        or usable_energy_mwh < 0
        or charging_hours <= 0
        or discharging_hours <= 0
        or not 0 < round_trip_efficiency <= 1
        or wear_eur_per_delivered_mwh < 0
    ):
        raise ValueError("Invalid MW, MWh, window duration, efficiency, or wear cost")
    eta = math.sqrt(round_trip_efficiency)
    charge_mwh = min(
        battery_power_mw * charging_hours,
        usable_energy_mwh / eta,
        battery_power_mw * discharging_hours / round_trip_efficiency,
    )
    delivered = charge_mwh * round_trip_efficiency
    purchase = charge_mwh * charge_price_eur_mwh
    revenue = delivered * sale_price_eur_mwh
    wear = delivered * wear_eur_per_delivered_mwh
    return BessCycleScreen(
        charged_mwh=charge_mwh,
        delivered_mwh=delivered,
        conversion_loss_mwh=charge_mwh - delivered,
        peak_soc_mwh=charge_mwh * eta,
        purchase_cost_eur=purchase,
        sale_revenue_eur=revenue,
        wear_cost_eur=wear,
        contribution_eur=revenue - purchase - wear,
        break_even_sale_price_eur_mwh=(
            charge_price_eur_mwh / round_trip_efficiency + wear_eur_per_delivered_mwh
        ),
    )
