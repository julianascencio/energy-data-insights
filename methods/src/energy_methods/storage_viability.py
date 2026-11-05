"""Transparent discounted battery storage cost under a *scenario* grant allocation.

Policy values (4 November 2026) refer to an all-technology Indian scheme:
https://www.pmindia.gov.in/en/news_updates/cabinet-approves-rs-14500-crore-viability-gap-funding-scheme-for-development-of-92-gwh-grid-scale-energy-storage-systems/

No technology-specific allocation has been announced. Policy totals are
published facts; developer-selected battery capital costs, operating costs,
cycling and hypothetical grant shares are assumptions, never measured data.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Official policy, announced 2026-11-04; rupee crore = 10**7 INR.
INDIA_2026_VGF_INR_CRORE = 14_500.0
INDIA_2026_SCHEME_GWH = 92.0
INDIA_2026_BESS_GWH = 30.0
INDIA_2026_PUMPED_STORAGE_GWH = 60.0
INDIA_2026_OTHER_STORAGE_GWH = 2.0
INDIA_2026_SCHEME_INVESTMENT_INR_CRORE = 97_600.0
INDIA_2026_BESS_MIN_DOMESTIC_CONTENT_FRACTION = 0.40


@dataclass(frozen=True, slots=True)
class BatteryLcosAssumptions:
    """Illustrative battery costs per *nominal* kWh of AC charging capacity.

    The ``cycles_per_year`` parameter counts full-equivalent annual charging
    cycles of nominal energy; annual delivered energy applies depth of
    discharge, round-trip efficiency and capacity fade. Purchase price of
    charging energy, replacements, taxes and residual value are excluded.
    """

    capex_inr_per_kwh: float
    fixed_om_inr_per_kwh_year: float
    cycles_per_year: float
    lifetime_years: int
    discount_rate: float
    round_trip_efficiency: float
    depth_of_discharge: float
    annual_capacity_fade: float

    def __post_init__(self) -> None:
        values = (
            self.capex_inr_per_kwh,
            self.fixed_om_inr_per_kwh_year,
            self.cycles_per_year,
            self.discount_rate,
            self.round_trip_efficiency,
            self.depth_of_discharge,
            self.annual_capacity_fade,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError("All financial and performance inputs must be finite")
        if self.capex_inr_per_kwh <= 0 or self.fixed_om_inr_per_kwh_year < 0:
            raise ValueError("CAPEX must be positive and fixed O&M nonnegative")
        if self.cycles_per_year <= 0 or self.cycles_per_year > 366:
            raise ValueError("Cycles per year must be in (0,366]")
        if type(self.lifetime_years) is not int or self.lifetime_years < 1:
            raise ValueError("Lifetime must be a positive integer")
        if self.discount_rate < 0:
            raise ValueError("Discount rate must be nonnegative")
        if not 0 < self.round_trip_efficiency <= 1:
            raise ValueError("Round-trip efficiency must be in (0,1]")
        if not 0 < self.depth_of_discharge <= 1:
            raise ValueError("Depth of discharge must be in (0,1]")
        if not 0 <= self.annual_capacity_fade < 1:
            raise ValueError("Annual capacity fade must be in [0,1)")


@dataclass(frozen=True, slots=True)
class BatteryLcosResult:
    """Present-value costs and energy per nominal kWh, and LCOS in INR/kWh."""

    net_capex_inr_per_kwh: float
    discounted_om_inr_per_kwh: float
    discounted_delivered_kwh_per_kwh: float
    lcos_inr_per_kwh: float


def hypothetical_bess_vgf_inr_per_kwh(budget_share: float) -> float:
    """Allocate a chosen share of the *all-technology* VGF envelope to BESS.

    ``budget_share`` is a **hypothesis**, not an announced disbursement,
    eligibility rule or awarded subsidy. Returns INR per nominal BESS kWh.
    """
    if not math.isfinite(budget_share) or not 0 <= budget_share <= 1:
        raise ValueError("Hypothetical budget share must be finite and in [0,1]")
    allocation_inr = INDIA_2026_VGF_INR_CRORE * 10_000_000 * budget_share
    capacity_kwh = INDIA_2026_BESS_GWH * 1_000_000
    return allocation_inr / capacity_kwh


def battery_lcos(
    assumptions: BatteryLcosAssumptions,
    *,
    hypothetical_grant_inr_per_kwh: float = 0.0,
) -> BatteryLcosResult:
    """Discount costs / discharged energy from a per-nominal-kWh model.

    The grant is modelled as paid up front. This timing has **not** been
    published for the India scheme and is strictly a financing sensitivity.
    Charging energy is free/excluded, so this is not an all-in delivered tariff.
    """
    grant = hypothetical_grant_inr_per_kwh
    if not math.isfinite(grant) or not 0 <= grant <= assumptions.capex_inr_per_kwh:
        raise ValueError("Hypothetical grant must be between zero and CAPEX")
    delivered_pv = 0.0
    om_pv = 0.0
    for year in range(1, assumptions.lifetime_years + 1):
        discount = (1 + assumptions.discount_rate) ** year
        delivered_pv += (
            assumptions.cycles_per_year
            * assumptions.depth_of_discharge
            * assumptions.round_trip_efficiency
            * (1 - assumptions.annual_capacity_fade) ** (year - 1)
            / discount
        )
        om_pv += assumptions.fixed_om_inr_per_kwh_year / discount
    net_capex = assumptions.capex_inr_per_kwh - grant
    return BatteryLcosResult(
        net_capex_inr_per_kwh=net_capex,
        discounted_om_inr_per_kwh=om_pv,
        discounted_delivered_kwh_per_kwh=delivered_pv,
        lcos_inr_per_kwh=(net_capex + om_pv) / delivered_pv,
    )
