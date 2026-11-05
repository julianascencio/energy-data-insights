"""
India's 2026 storage VGF: battery LCOS under explicit funding scenarios
=======================================================================

**News trigger (4-5 November 2026):** India's Union Cabinet approved
Rs 14,500 crore of support for **92 GWh across storage technologies**:
30 GWh batteries, 60 GWh pumped hydro and 2 GWh other technology. The
announced budget **does not imply** any published BESS-specific subsidy.

Official announcement (4 November 2026):
https://www.pmindia.gov.in/en/news_updates/cabinet-approves-rs-14500-crore-viability-gap-funding-scheme-for-development-of-92-gwh-grid-scale-energy-storage-systems/

The published government announcement is evidence for technology capacity
allocations and aggregate scheme funding only. Battery CAPEX, O&M, cycle
rates, fade, discount rate and **budget share** are clearly labelled
ILLUSTRATIVE / hypothetical values; no site or tariff is measured. This
example evaluates financing sensitivities rather than predicting awards.

Business question: under what cycling intensity and *hypothetical*
allocation of programme funds would a battery be competitive on a
levelized storage cost basis, excluding charging-energy purchase costs?
"""

# %%
from dataclasses import replace

import matplotlib.pyplot as plt

from energy_methods.storage_viability import (
    INDIA_2026_BESS_GWH,
    INDIA_2026_OTHER_STORAGE_GWH,
    INDIA_2026_PUMPED_STORAGE_GWH,
    BatteryLcosAssumptions,
    battery_lcos,
    hypothetical_bess_vgf_inr_per_kwh,
)

# Published aggregate policy figures: 30 GWh BESS + 60 GWh pumped + 2 GWh other.
capacities = [INDIA_2026_BESS_GWH, INDIA_2026_PUMPED_STORAGE_GWH, INDIA_2026_OTHER_STORAGE_GWH]

# ILLUSTRATIVE battery economics: not Indian tender prices or measured output.
base_case = BatteryLcosAssumptions(
    capex_inr_per_kwh=18_000,
    fixed_om_inr_per_kwh_year=200,
    cycles_per_year=300,
    lifetime_years=15,
    discount_rate=0.085,
    round_trip_efficiency=0.86,
    depth_of_discharge=0.90,
    annual_capacity_fade=0.02,
)
shares = [0, 0.10, 0.20, 0.30, 0.40]
cycles = [200, 250, 300, 365]

# %%
print("Official: total support Rs 14,500 crore for 92 GWh across all technologies.")
print("India BESS allocation: 30 GWh, *not* 92 GWh.")
for share in shares:
    grant = hypothetical_bess_vgf_inr_per_kwh(share)
    result = battery_lcos(base_case, hypothetical_grant_inr_per_kwh=grant)
    print(
        f"ILLUSTRATIVE BESS VGF budget share {share:4.0%}; "
        f"assumed upfront grant Rs {grant:,.0f}/kWh; "
        f"LCOS Rs {result.lcos_inr_per_kwh:.2f}/delivered kWh"
    )

# %%
fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(12, 4))
ax0.bar(["Battery", "Pumped hydro", "Other"], capacities)
ax0.set(ylabel="GWh", title="Published scheme mix (Nov 2026)")
for count in cycles:
    case = replace(base_case, cycles_per_year=count)
    cost = [
        battery_lcos(
            case, hypothetical_grant_inr_per_kwh=hypothetical_bess_vgf_inr_per_kwh(share)
        ).lcos_inr_per_kwh
        for share in shares
    ]
    ax1.plot([100 * share for share in shares], cost, marker="o", label=f"{count} cycles/year")
ax1.set(
    xlabel="Hypothetical share of all-technology VGF budget (%)",
    ylabel="Battery LCOS (INR / delivered kWh)",
    title="ILLUSTRATIVE economics (charging cost excluded)",
)
ax1.legend()
fig.tight_layout()
plt.show()

# %%
# This is NOT an official incentive tariff, an LCOS estimate for Indian assets,
# or a comparison to pumped-storage economics; the government has not specified
# grants by technology. Reproduce with:
# uv run --no-sync python examples/analysis/plot_india_storage_vgf_lcos.py
