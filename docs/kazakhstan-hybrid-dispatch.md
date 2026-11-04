# News-to-example: Kazakhstan hybrid wind–solar–BESS dispatch

**Source:** Ember, 3 November 2026, [Kazakhstan has the wind to power its demand growth](https://ember-energy.org/latest-insights/kazakhstan-has-the-wind-to-power-its-demand-growth).

Ember reports a hybrid portfolio may cover 70–90% of a typical Kazakhstan demand profile for less than $60/MWh. **This contribution does not validate or reproduce those findings.** It provides a small, inspectable hourly dispatch baseline as a foundation for a later measured-data and cost-calibrated study.

## Input, method, analysis

- **Input:** deterministic **synthetic** hourly wind, solar and demand profiles (14 days). No data provider, credentials or live API required. No claims of measured Kazakhstan generation.
- **Method:** `energy_methods.hybrid_dispatch.simulate_hybrid`, direct renewable supply followed by renewable-only battery charging and demand-serving discharging; MW/MWh power and energy limits, symmetric charge/discharge losses, no grid import. Greedy dispatch, not economic optimization.
- **Analysis:** compare demand coverage, curtailment and unmet demand over storage energy capacities from 0 to 800 MWh with fixed 50 MW battery power. Baseline is zero storage.
- **Reproduce:** `uv sync --locked --all-packages`, then `uv run python examples/analysis/plot_kazakhstan_hybrid_dispatch.py`; tests: `uv run pytest methods/tests/test_hybrid_dispatch.py`.
- **Scientific limitations:** illustrative profiles are not measured or meteorologically calibrated; 14 days are not representative of annual variability; no capital/operating costs, storage degradation, dispatch prices, reserves, transmission, reliability stress test, or optimal capacity sizing. Never interpret its coverage numbers as an independent estimate for Kazakhstan.
- **Next research step:** connect licensed hourly Kazakhstan load and renewable weather/generation records, optimize dispatch against an explicit economic objective and benchmark against Ember's assumptions with a documented input reconciliation.
