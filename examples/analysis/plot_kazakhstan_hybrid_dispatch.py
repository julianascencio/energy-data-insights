"""
Kazakhstan wind-solar-battery hybrid: reproducible dispatch sensitivity
======================================================================

**News trigger:** Ember, 3 November 2026, reports that a Kazakhstan
wind-solar-battery hybrid could cover 70-90% of a typical demand profile
at a delivered cost below $60/MWh.

This gallery example does **not** reproduce that cost or coverage claim.
It uses explicitly SYNTHETIC 14-day hourly profiles to illustrate how
battery energy capacity changes renewable demand coverage. There is no
assumption that these profiles represent Kazakhstan measurements.

Original source: https://ember-energy.org/latest-insights/kazakhstan-has-the-wind-to-power-its-demand-growth

Business question: how much does storage increase the share of a demand
profile served by co-located renewables? The method is a deterministic
hourly energy balance with charge/discharge power limits, storage energy
capacity and round-trip efficiency. It excludes network congestion,
electricity prices, battery aging, reserve constraints and financing.
"""

# %%
import math

import matplotlib.pyplot as plt

from energy_methods.hybrid_dispatch import simulate_hybrid

hours = range(14 * 24)
# SYNTHETIC, deterministic shapes. Not calibrated to Kazakhstan.
wind = [48 + 25 * math.sin(2 * math.pi * h / 79) for h in hours]
solar = [75 * max(0, math.sin(math.pi * ((h % 24) - 6) / 12)) for h in hours]
demand = [90 + 12 * math.sin(2 * math.pi * ((h % 24) - 17) / 24) for h in hours]

capacities = [0, 50, 100, 200, 400, 800]
results = [simulate_hybrid(wind, solar, demand, battery_mwh=e, battery_mw=50) for e in capacities]
baseline = results[0]
for capacity, result in zip(capacities, results, strict=True):
    print(
        f"Synthetic battery {capacity:3d} MWh: "
        f"coverage {result.coverage:.1%}; "
        f"curtailment {result.curtailed_mwh:.0f} MWh; "
        f"unserved {result.unserved_mwh:.0f} MWh"
    )

# %%
fig, ax = plt.subplots()
ax.plot(capacities, [100 * r.coverage for r in results], marker="o")
ax.axhline(100 * baseline.coverage, linestyle="--", label="No storage baseline")
ax.set(
    xlabel="Battery energy capacity (MWh)",
    ylabel="Demand served (%)",
    title="Illustrative hybrid dispatch — SYNTHETIC inputs",
)
ax.set_ylim(0, 100)
ax.legend()
fig.tight_layout()
plt.show()

# %%
# Interpretation: differences here are scenario sensitivities, not observed
# Kazakhstan performance. The dispatch is greedy, not globally optimal.
# Reproduction: uv run python examples/analysis/plot_kazakhstan_hybrid_dispatch.py
