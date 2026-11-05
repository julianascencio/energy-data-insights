# India’s November 2026 storage VGF: battery cost sensitivity

## News and evidence

On **4 November 2026**, India’s Union Cabinet announced an all-technology viability-gap-funding (VGF) scheme for grid-scale energy storage ([official announcement](https://www.pmindia.gov.in/en/news_updates/cabinet-approves-rs-14500-crore-viability-gap-funding-scheme-for-development-of-92-gwh-grid-scale-energy-storage-systems/)). The public facts used are **₹14,500 crore** across FY 2026–27 to 2030–31, to enable **92 GWh**: **30 GWh BESS**, **60 GWh pumped hydro**, **2 GWh emerging storage**. Total estimated investment is **₹97,600 crore**, batteries face **at least 40% domestic-content requirement**, and awards will be through tariff-based competitive bidding. India’s government also projects **411 GWh** grid-scale storage need by FY 2031–32. These are **published goals/announcements, not measured operating output or awarded grants**.

On **5 November**, Reuters [reported](https://www.reuters.com/business/energy/india-mandate-energy-storage-state-power-utilities-power-secretary-says-2026-11-05/) a proposed storage obligation for state utilities; its required volume had **not** been specified. This proposal must not be represented as an enacted or quantified mandate.

**Important allocation caveat:** the ₹14,500 crore fund is for *all three* technologies. The 92 GWh is **not** an amount of battery storage. In particular, dividing the full support envelope by 30 GWh of BESS would **not** be an official BESS subsidy per kWh. The implementation instead makes the assumed allocation to BESS an explicit parameter, from 0–40% in the gallery.

## Inputs, method and outputs

1. **Published quantitative policy data**: support envelope, technology mix, period, domestic-content rule; source links above (accessed 2026-11-05). Source license for reusing article text/data not asserted; only attributed facts are retained.
2. **ILLUSTRATIVE battery assumptions**: installed CAPEX ₹18,000 per nominal kWh, O&M ₹200 per nominal kWh annually, 15-year life, 8.5% real discount rate, 86% round-trip energy efficiency, 90% usable depth of discharge, 2% annual loss of usable capacity, and 200/250/300/365 full-equivalent charging cycles annually. These are **scenario knobs**, not sourced Indian tender data, measured battery degradation or certified performance.
3. **Financial model**: calculate the grant per nominal BESS kWh if an assumed fraction *f* of the aggregate support envelope were allocated to 30 GWh batteries: 

   `grant_INR_per_kWh = f * 14500 * 1e7 / (30 * 1e6)`.

   Assume the grant is received upfront. Per nominal battery kWh, the annual *discharged* energy in year *y* is `cycles * DoD * RTE * (1 - annual_fade)^(y-1)` kWh; discount at `(1+r)^y`. Discount annual fixed O&M similarly. **LCOS** is `(CAPEX - upfront grant + discounted O&M) / discounted discharged kWh`. A **zero-grant baseline** is mandatory. Energy purchase cost is excluded; this is not the delivered tariff, discharge price, net present value of a real project or a bankability assessment.
4. **Outputs**: published capacity mix, chart of hypothetical grant-budget share versus LCOS for four cycle-rate assumptions, console report of baseline and grant scenarios.

## Reproduce

```bash
uv sync --locked --all-packages --group docs --python 3.13
uv run --no-sync python examples/analysis/plot_india_storage_vgf_lcos.py
uv run --no-sync pytest methods/tests/test_storage_viability.py
uv run --no-sync sphinx-build -W --keep-going -b html docs docs/_build/html
```

## Limitations and next analysis

No BESS-specific grant split, award rates, timing or final tender terms have been published here. The scenario cannot support claims about the exact payback, required investor tariffs, actual cost of energy-storage in India, physical performance, economic merit relative to pumped hydro, or state-by-state mandates. The up-front grant assumption is a modelling choice. Capacity cycling and degradation are deterministic and no replacements are assumed. No weather or grid-dispatch observations enter the model; there are therefore no empirical uncertainty bars to report. The four-cycle intensity curves are **sensitivity uncertainty**, not probabilistic confidence intervals.

Next, ingest awarded BESS tender documents and measured dispatch and prices, quantify the charging-energy cost and dispatch value, incorporate actual capital/grant disbursement dates and replacement costs, then validate the calculation against actual winning bids.
