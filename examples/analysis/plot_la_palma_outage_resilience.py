"""
La Palma 2026 blackout: synthetic critical-load BESS resilience
===============================================================

**Observed event** (Red Electrica, 2 November 2026): La Palma's electricity
supply was lost at 06:38 local time and fully restored by 10:26, a **228-minute
restoration interval**. Individual customers may have experienced shorter
interruptions. No load/generation timeseries is provided by the incident report.

Primary source: https://www.ree.es/en/news/press-release/2026/11/electricity-supply-restored-in-la-palma

**Business question:** How much usable battery energy would an *appropriately
islanded* critical facility need for a 228-minute outage? All modeled load,
PV and wind profiles and storage ratings below are **SYNTHETIC SCENARIOS**.
They are not observations of La Palma or evidence that a BESS could restart the
island system. Grid-forming, black start, protection and switching are not
modeled; normal grid-following PV cannot be assumed to remain online.
"""

# %%
from datetime import datetime

import matplotlib.pyplot as plt

from energy_methods.hybrid_dispatch import simulate_hybrid
from energy_methods.outage_resilience import minimum_islanded_capacity

start = datetime.fromisoformat("2026-11-02T06:38:00+00:00")
restored = datetime.fromisoformat("2026-11-02T10:26:00+00:00")
duration_minutes = int((restored - start).total_seconds() / 60)
assert duration_minutes == 228

# Synthetic 0.5-MW critical load, three-minute steps (exactly 76 samples).
timestep_hours = 3.0 / 60.0
intervals = duration_minutes // 3
load_mw = [0.5] * intervals
no_generation = [0.0] * intervals

# Illustrative *conditional* island-capable renewables: no historical data.
wind_scenario_mw = [0.04] * intervals
pv_scenario_mw = [0.12 * min(1.0, max(0.0, ((i * 3) - 60) / 160)) for i in range(intervals)]
rated_power_mw = 0.65
start_soc = 0.80
roundtrip_efficiency = 0.95**2

cases = {
    "No renewable generation (conservative)": (no_generation, no_generation),
    "Synthetic available PV + wind": (wind_scenario_mw, pv_scenario_mw),
}
capacities_mwh = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0]

# %%
fig, ax = plt.subplots()
for label, (wind_mw, solar_mw) in cases.items():
    required = minimum_islanded_capacity(
        wind_mw,
        solar_mw,
        load_mw,
        inverter_mw=rated_power_mw,
        initial_soc_fraction=start_soc,
        roundtrip_efficiency=roundtrip_efficiency,
        timestep_hours=timestep_hours,
    )
    coverage = [
        simulate_hybrid(
            wind_mw,
            solar_mw,
            load_mw,
            battery_mwh=capacity,
            battery_mw=rated_power_mw,
            initial_soc_mwh=capacity * start_soc,
            efficiency=roundtrip_efficiency,
            timestep_hours=timestep_hours,
        ).coverage
        * 100
        for capacity in capacities_mwh
    ]
    print(f"{label}: {required:.3f} usable MWh required")
    ax.plot(capacities_mwh, coverage, marker="o", label=label)

ax.set(
    xlabel="Modeled usable battery energy (MWh)",
    ylabel="Synthetic critical-load energy served (%)",
    title="La Palma incident duration; SYNTHETIC facility assumptions",
    ylim=(0, 101),
)
ax.legend()
fig.tight_layout()
plt.show()

# %%
# 100% energy coverage is conditional on islanding/black-start capabilities,
# controls and protection; it does not establish reliability or feasibility.
# Run offline: uv run python examples/analysis/plot_la_palma_outage_resilience.py
