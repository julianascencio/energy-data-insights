# Offshore wind bankability: Japanese industry-cost sensitivity (November 2026)

## News trigger and business question

On **5 November 2026**, [Reuters reported Tokyo Gas's withdrawal from the Kashima Bay offshore wind project](https://www.reuters.com/business/energy/tokyo-gas-withdraws-ibaraki-offshore-wind-project-2026-11-05/), citing rising costs. The report disclosed **no project-level CAPEX, OPEX, financing or generation**; no financial conclusions about that project can be drawn from this model.

**Question:** how do construction-cost escalation, real financing costs and the net capacity factor affect the levelized cost and flat real electricity price needed to break even?

## Evidence and provenance

- [Japan METI, 111th Procurement Price Calculation Committee, January 8, 2026](https://www.meti.go.jp/shingikai/santeii/111.html) lists the Japan Wind Power Association (JWPA) presentation on offshore-wind investment and cost reduction.
- An [independent summary of that presentation](https://www.gridwatch.jp/policy/offshore-wind-industrial-base-cost-roadmap-january-2026) reports planning-model inputs of **JPY 900,000/kW CAPEX**, **JPY 12,300/kW-year OPEX** and **36.6% net capacity factor** for fixed-bottom offshore wind.
- The [offline JSON input and provenance](../examples/analysis/data/jwpa_offshore_cost_2026.json) classify these figures as `published_industry_assumption`, **not** measured site performance or invoices. The source PDF could not be independently retrieved in this run; numerical values were checked only against the secondary synthesis. Verify the original presentation before investment use.
- Full-source licensing is unverified; only three attributed numerical facts are transcribed, not original text, graphics or bulk data. All assumptions beyond those three quantities are expressly illustrative.

## Input → method → analysis

The versioned input loader `energy_data_retrieval.cost_inputs.load_offshore_cost_snapshot` validates evidence classification, values and source metadata. No live API, secret or data download is needed.

The reusable `energy_methods.offshore_wind_economics.evaluate_offshore_wind` computes

```text
E_year_kWh = capacity_kW * 8760 * net_CF * (1 - annual_degradation) ** (year - 1)
LCOE_real = (CAPEX_year_0 + sum(OPEX_year / (1+r)**year)) /
            sum(E_year_kWh / (1+r)**year)
NPV_real_tariff = real_tariff_per_kWh * discounted_energy_kWh - discounted_cost
```

CAPEX occurs at year zero; generation and fixed OPEX occur at year end. A real discount rate is applied to constant real JPY costs. The capacity factor includes wake, electrical and availability losses; degradation is an additional scenario assumption. This is not a price-capture or debt-financing optimizer.

The reproducible [gallery example](../examples/analysis/plot_japan_offshore_wind_cost.py) plots CAPEX multipliers (0.7–1.5) under three illustrative real discount rates (3%, 6%, 9%) and capacity-factor (26%–46%) sensitivity under different construction cost multipliers. Ranges are **scenarios, not confidence intervals**. It also checks that NPV is approximately zero at its computed flat-tariff break-even price.

**Illustrative example only:** 100 MW, 25 operating years, real 6% discount rate, 36.6% net capacity factor and 0% degradation yield approximately **JPY 25.8/kWh** simplified LCOE; a purely hypothetical JPY 30/kWh fixed tariff implies approximately **JPY 17.2 billion** NPV. These outputs **do not reproduce JWPA's reported LCOE and do not describe Kashima Bay**.

## Reproduce offline

```bash
uv sync --locked --all-packages
uv run --no-sync python examples/analysis/plot_japan_offshore_wind_cost.py
uv run --no-sync pytest methods/tests/test_offshore_wind_economics.py data-retrieval/tests/test_jwpa_cost.py
```

The example appears under **Analysis → Offshore wind economics** in the two-level gallery.

## Decision limits and next research

This screening model omits measured hourly wind/generation, turbine power curves, installation delays, location-specific EPC/O&M quotes, volatile or inflation-linked contracts, replacement CAPEX, degradation calibration, curtailment, taxes, subsidies, dynamic prices, debt structures, transmission, and project-specific site risks. Do **not** use it to determine whether any named project should proceed or withdraw.

Next: connect licensable hourly Japanese offshore resource and project bid data, model net production with turbine-specific power curves, and compare calibrated P50/P90 scenarios to published actual costs and contract terms.
