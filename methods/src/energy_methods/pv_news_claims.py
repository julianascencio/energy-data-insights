"""Audit aggregate PV news claims against explicit physical and accounting baselines.

News release claims are inputs, not observed generation or verified emissions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class PVClaimAudit:
    """Derived energy and carbon quantities, with the distinct boundaries retained.

    ``co2_floor_kg_per_kwh`` is a *lower bound* on the CO2 displacement
    factor implied by the release's avoided-CO2 claim, not a grid observation.
    ``grid_average_tonnes_co2e`` is an illustrative location-average accounting
    benchmark and is NOT a statement of avoided emissions or consequential impact.
    """

    equivalent_generation_mwh: float
    dc_equivalent_full_load_hours: float
    dc_equivalent_capacity_factor: float
    co2_floor_kg_per_kwh: float
    grid_average_tonnes_co2e: float


def audit_pv_news_claims(
    *,
    capacity_mwp: float,
    homes_equivalent: float,
    annual_household_kwh: float,
    avoided_co2_floor_tonnes: float,
    grid_average_kgco2e_per_kwh: float,
    hours_per_year: float = 8760.0,
) -> PVClaimAudit:
    """Infer energy-equivalence and emissions-intensity bounds from a PV news release.

    Parameters
    ----------
    capacity_mwp : float
        Published DC peak capacity in MWp; not an AC export rating.
    homes_equivalent : float
        Published approximate annual number of households supplied (not metered).
    annual_household_kwh : float
        Explicit household electricity-consumption benchmark (kWh/home/year).
    avoided_co2_floor_tonnes : float
        Lower bound for developer's claimed annual avoided tonnes of *CO2*.
    grid_average_kgco2e_per_kwh : float
        Independent *average* grid emission-factor reference (kg *CO2e*/kWh).
    hours_per_year : float
        Calendar hours in the reference year; default is a non-leap 365-day year.

    Notes
    -----
    This is an algebraic screening tool, not a PV yield, marginal-emissions,
    additionality or lifecycle-assessment model. Numerical results are conditional
    on the representative household demand assumed by the caller. The distinct
    CO2 and CO2e boundaries must NOT be silently compared as equivalent.
    """
    positives = (
        capacity_mwp,
        homes_equivalent,
        annual_household_kwh,
        avoided_co2_floor_tonnes,
        hours_per_year,
    )
    if any(not math.isfinite(x) or x <= 0 for x in positives):
        raise ValueError("PV capacity, homes, usage, CO2 bound and year hours must be positive")
    if not math.isfinite(grid_average_kgco2e_per_kwh) or grid_average_kgco2e_per_kwh < 0:
        raise ValueError("Grid-average emissions factor must be finite and nonnegative")

    equivalent_kwh = homes_equivalent * annual_household_kwh
    if not math.isfinite(equivalent_kwh):
        raise ValueError("Equivalent generation overflows finite arithmetic")
    equivalent_mwh = equivalent_kwh / 1000
    dc_full_load_hours = equivalent_mwh / capacity_mwp
    equivalent_factor = dc_full_load_hours / hours_per_year
    implied_co2_lower_bound = avoided_co2_floor_tonnes * 1000 / equivalent_kwh
    average_tonnes_co2e = equivalent_kwh * grid_average_kgco2e_per_kwh / 1000

    result = PVClaimAudit(
        equivalent_generation_mwh=equivalent_mwh,
        dc_equivalent_full_load_hours=dc_full_load_hours,
        dc_equivalent_capacity_factor=equivalent_factor,
        co2_floor_kg_per_kwh=implied_co2_lower_bound,
        grid_average_tonnes_co2e=average_tonnes_co2e,
    )
    if any(
        not math.isfinite(x)
        for x in (
            result.dc_equivalent_full_load_hours,
            result.dc_equivalent_capacity_factor,
            result.co2_floor_kg_per_kwh,
            result.grid_average_tonnes_co2e,
        )
    ):
        raise ValueError("Claim audit outputs overflow finite arithmetic")
    return result
