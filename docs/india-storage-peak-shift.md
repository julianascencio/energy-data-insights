# India November 2026 BESS policy: evening-peak-shifting screening example

## Dated reporting and official data context

On **5 November 2026**, Reuters reported that India's power secretary Pankaj Agarwal said energy-storage requirements would be introduced for licensed entities purchasing electricity, including state utilities. **No minimum MW, MWh or percentage requirement was stated.** The [4 November Reuters report](https://www.reuters.com/world/india/india-cabinet-clears-153-billion-programme-energy-storage-projects-2026-11-04/) described a ₹145 billion storage-development programme. [5 November report](https://www.reuters.com/business/energy/india-mandate-energy-storage-state-power-utilities-power-secretary-says-2026-11-05/).

The official [Central Electricity Authority data API](https://cea.nic.in/api-for-central-electricity-authority-data/?lang=en) publishes electricity-sector capacity, generation and supply indicators. They **do not supply the matched hourly local surplus and evening peak-deficit profiles used by this example**. This case intentionally does not claim a measured Indian time series or manufacture one from aggregate capacity statistics.

## Method and quantitative KPI

The reproducible [gallery example](../examples/analysis/plot_india_storage_mandate.py) illustrates utility procurement **screening**, not legal compliance or economic optimization. Its deterministic **SYNTHETIC** seven-day profiles include daytime PV surplus **after local contemporaneous use** and evening residual shortfall. The method `energy_methods.storage_peak_shift.simulate_storage_peak_shift` dispatches available surplus into a battery and discharges into residual peak demand. Each hour enforces usable battery energy (MWh), charge/discharge power (MW), and symmetric square-root round-trip efficiency (default 90%). No grid charging. It returns auditable hourly stored, delivered, curtailed and unserved energy.

- **Baseline:** no battery, peak shortfall wholly unserved by shifted PV.
- **KPI:** fraction of remaining peak demand served by the battery = discharged MWh / original shortfall MWh, plus curtailed MWh and hourly SOC.
- **Sensitivity:** energy capacities 0–240 MWh; battery powers 0/20/40 MW; solar availability multipliers 0.7/1.0/1.3. These are **stress scenarios, not confidence limits**.
- **Interpretation:** whether MW charge/discharge limits or usable MWh constrain solar-to-evening shifting. It does **not** identify an India-wide storage mandate, operational requirement, optimal CAPEX, annual firm capacity, or real grid integration benefit.

## Reproduction

From the project root, using Python 3.12 or 3.13 and `uv`:

```bash
uv sync --locked --all-packages
uv run --no-sync pytest methods/tests/test_storage_peak_shift.py
uv run --no-sync python examples/analysis/plot_india_storage_mandate.py
```

The example is also executed by Sphinx-Gallery during the documentation build. No live credentials, paid APIs, or external files are required.

## Scientific limits and next data connector

Hourly inputs are **constructed examples**, not sampled weather or dispatch history. The output is not calibrated to India, and the solar multipliers are not statistical uncertainty intervals. Neither an 8760-hour weather chronology nor battery wear, price-based dispatch, export curtailment limits, network congestion, state-of-charge reserves, outages, multiple renewables, tariffs or inverter losses is represented. A seven-day trace is insufficient for resource adequacy or financing decisions.

For a real India business case, obtain jurisdiction-specific time-aligned renewable *available and curtailed power*, utility load/peak demand, weather, and dispatch constraints with documented licensing. Compare multiple years and a 15-minute baseline, then size MW/MWh using weather uncertainty, availability, degradation, dispatch scheduling and economic objectives. Verify data units, timezone and provenance before comparing outputs with public policy or tender figures.
