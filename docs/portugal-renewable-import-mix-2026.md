# Portugal's October 2026 import exposure: reconcile rounded REN statistics

**Primary data provenance (Portuguese transmission-system operator REN):**

- [2 October 2026, first nine months](https://www.ren.pt/en-gb/media/news/portugal-breaks-electricity-consumption-record-in-the-first-nine-months): demand **40.5 TWh** (rounded), renewable electricity **64%**, natural gas **14%**, net imports **22%** of consumption.
- [3 November 2026, first ten months](https://www.ren.pt/en-gb/media/news/renewables-account-for-62-per-cent-of-electricity-consumption-after-10-months): renewables **62%**, natural gas **14%**, net imports **24%** of consumption; October alone renewables **47%**, all non-renewables **13%**, net imports **40%**. October hydro, wind and solar PV productivity indices were **0.58**, **0.61** and **1.05**, respectively (historical reference **1**).

These are actual **published rounded percentages of electricity consumption**, not percentages of domestic generation, hourly records or measured plant performance. The **13% solar contribution** belongs to the first ten months, **not** to October alone. Gas in cumulative reports must not automatically be equated to all non-renewable generation in October.

## Decision problem and method

Before a PV developer, wind investor or BESS owner contracts firm electricity or sizes flexibility, they need to distinguish genuine weather exposure from rounding/reporting effects. Using preceding demand `P`, subsequent month demand `M`, preceding percentage `p` and new cumulative percentage `c`, the implied month percentage is

```text
monthly_pct = c + (P / M) * (c - p)
```

`energy_methods.mix_rounding.infer_incremental_month_share` propagates integer reporting precision (plus/minus **0.5 percentage points**) and REN's January-September 40.5 TWh demand rounded to one decimal (plus/minus **0.05 TWh**) by evaluating all parameter corners. Output is an *envelope from rounding*, **not** a statistical confidence interval. Marginal extremes across different generation categories need not be jointly achievable.

**Explicit synthetic scenario:** October demand is taken as **4.50 TWh** for this reproducible sensitivity calculation. REN's cited press release does not state this monthly demand total; it is NOT a measured input and no resulting conditional October TWh volume is reported as fact.

For this scenario the central derived October shares are **44% renewables** and **42% net imports**. Rounding envelopes are approximately **34-54%** and **32-52%**, respectively. The independently reported October shares **47%** and **40%** lie within these conservative intervals: rounded cumulative figures do **not** contradict REN's October press figures. The reported October aggregate non-renewable value 13% is not used to infer monthly gas output, since those are different reporting labels.

The runnable Sphinx-Gallery example plots the actual reported cumulative and monthly categories, rounding envelopes from the illustrative demand scenario, and REN's reported hydro/wind/solar productivity indices. It performs no inference about the renewable/carbon content of imports.

## Reproduce

```bash
uv sync --locked --all-packages
uv run --no-sync python examples/analysis/plot_portugal_mix_rounding.py
uv run --no-sync pytest methods/tests/test_mix_rounding.py
```

It is listed under **Analysis -> Electricity mix and imports**. No keys, paid APIs, live downloads or unlicensed copied datasets are required. Sources are directly attributed. The input percentages are frozen extracts of the public dated primary statements, not a private data connector.

## Limitations and next step

No time-matched hourly generation, imports, market prices, curtailment, system losses, weather model, storage state-of-charge, degradation, arbitrage optimization or emissions are derived. A productivity index cannot be used to causally attribute import exposure to a particular renewable technology. The input consumption assumption is NOT verified. Do not infer a reliable BESS MW/MWh rating or wind/PV PPA revenue from these statistics alone.

A later study should retrieve official REN Data Hub/ENTSO-E hourly demand, generation by source, interchange and day-ahead prices (after checking licensing, revisions and time zones), reconcile the energy balance and only then run a physical/economic flexibility optimization with uncertainty.
