# Spain's 2026 technical-restriction costs: BESS economics screening

## Dated trigger and primary-source evidence

[Red Eléctrica, 3 November 2026](https://www.ree.es/es/actualidad/nota-de-prensa/2026/11/servicios-ajuste-elevan-4350-millones-euros-ingresos-generadoras-octubre), reports that in **January–October 2026** the energy needed to resolve technical restrictions was **26.4%** higher than in the corresponding 2025 period, while the **cost to demand** was **43.4%** higher. It reports **€4.35 billion** in generators' revenue associated with technical restrictions and secondary regulation. The combined principal adjustment-service costs exceeded **€4.688 billion**. These totals describe different accounting boundaries, not interchangeable estimates of a battery market.

The release also gives **€214.73/MWh**, a *volume-weighted average* remuneration for upward technical constraints, and **€82.10/MWh**, the *arithmetic average* day-ahead price. The difference **must not be used as an investable BESS trading spread**: the two values relate to different services, settlement rules, participants and weighting. The article does not establish battery access to technical-restriction dispatch.

A small, source-attributed, manually transcribed [JSON numeric snapshot](../examples/analysis/ree_adjustment_20261103.json) is included; it contains official **reported aggregates**, not independently measured hourly data. No source document is reproduced or bulk data licence implied. News background includes [Spain's recent renewable curtailment coverage](https://www.elespanol.com/invertia/empresas/energia/20261025/segunda-edad-oro-renovables-sector-revitaliza-baterias-demanda-crece-ano/1003744432678_0.html) (25 October 2026), which is *not* used as model input.

## Question and two distinct evidence classes

1. **Official reported aggregate:** What change in average unit cost is implied by the simultaneous energy and cost growth? With indices of 1.264 for energy and 1.434 for cost, the implied average cost per unit changes by `1.434 / 1.264 - 1` = **+13.45%**. This describes the reported aggregate and is **not** an hourly price trend or a causal decomposition.
2. **Illustrative engineering/financial sensitivity:** For an assumed price-taking **1 MW / 2 MWh** BESS and *separate* two-hour charge and discharge windows, how much charge energy and delivery are physically feasible, and what buy/sell prices cover conversion losses plus an illustrative **€12 per delivered MWh** variable wear allowance? All charge and sale prices are **hypothetical**, including negative buy prices. This screen does **not** optimize an hourly price series or value ancillary services.

The reusable `energy_methods.grid_adjustment_bess` method computes the aggregate unit-cost index and one complete BESS cycle. Symmetric square-root conversion efficiency, usable SOC energy, charge/discharge power, and the duration of both periods constrain the traded energy. It enforces a return to zero SOC, preventing free energy at period boundaries. Baseline is **no storage**, with zero added revenue. Cash contribution subtracts energy purchase and wear allowance from sales; it excludes network fees, taxes, CAPEX, fixed O&M, ancillary-market participation, losses outside the cell and calendar aging. A negative contribution describes a loss-making **forced cycle**, not an optimizer that would rationally choose to remain idle.

## Gallery / reproduction

[Run the gallery script](../examples/analysis/plot_ree_adjustment_bess.py):

```bash
uv sync --locked --all-packages
uv run --no-sync pytest methods/tests/test_grid_adjustment_bess.py
uv run --no-sync python examples/analysis/plot_ree_adjustment_bess.py
```

It outputs one **reported-cost-growth index** chart and one **synthetic price-pair BESS contribution** heatmap, with warnings on their distinct evidence classifications. Sphinx-Gallery executes the example offline, resolving the attributed JSON fixture from the source tree during documentation builds. The JSON is committed in the repository and linked above; it is not advertised as a downloadable bundled observation file.

## Limitations and next data work

The REE announcement is a published aggregate, not a timestamped dataset. Neither the index ratio nor the €4.35 billion recipient revenue quantifies a battery's accessible revenue pool. The battery prices, calendar cycle count, efficiency and wear are assumptions, not calibrated observations, confidence bounds, annual merchant earnings or financing forecasts. Arbitrage trades require time-aligned prices and permitted market access; onsite charging, demand charges, operational dispatch rules, asymmetric efficiency, SOC constraints across days, network/export constraints and actual technical-restriction eligibility are unknown. There is **no valid conversion from the REE €214.73/MWh constraint figure to a battery discharge price**.

Next: obtain licensed hourly or 15-minute OMIE prices and compatible actual technical-service participation/settlement data, align Spanish time zones and daylight-saving hours, validate a battery-eligible product, and implement an optimization with conservative baseline and fees. The present case is an auditable **screen**, not a revenue forecast or regulation-compliance study.
