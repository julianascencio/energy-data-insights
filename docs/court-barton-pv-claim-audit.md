# Court Barton PV: news-claim consistency and due-diligence screen

**Event:** 5 November 2026, Recurrent Energy / Canadian Solar announces commercial operation of Court Barton Solar Farm in South Devon, UK.

**Business question:** For an investor or technical advisor, what implied electricity generation and avoided-CO2 intensity are needed to justify developer marketing claims? What assumptions must be reconciled before financing or verifying them?

## Evidence and provenance

| Input | Value | Evidence class | Source | Interpretation |
| --- | ---: | --- | --- | --- |
| Court Barton solar DC nameplate | 20 MWp | Developer-reported project specification | [Canadian Solar investor release, 5 Nov 2026](https://investors.canadiansolar.com/news-releases/news-release-details/recurrent-energy-brings-court-barton-solar-farm-uk-commercial) | Not AC export power or measured yield |
| Homes-powered equivalent | Approximately 8,500/year | Developer-reported expected annual equivalent | Same developer release | Household consumption assumption is unstated |
| Avoided CO2 | **More than** 6,200 tonnes CO2/year | Developer-reported annual expectation, *lower bound* | Same developer release | Not verified avoided emissions; counterfactual not provided |
| Typical single-rate household annual demand | low 1,600; medium 2,500; high 3,800 kWh/household/year | Official representative *scenario* inputs | [Ofgem 2026 TDCV review, 27 May decision, effective 1 July](https://www.ofgem.gov.uk/consultation/review-typical-domestic-consumption-values) | Not actual household demand or uncertainty intervals |
| UK average electricity generation factor | 0.13096 kgCO2e/kWh | Official corporate reporting factor | [DESNZ 2026 factors](https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026); [government's worked example](https://www.gov.uk/government/publications/streamlined-energy-and-carbon-reporting-secr-for-academy-trusts/streamlined-energy-and-carbon-reporting-secr-for-academy-trusts) | Average location-based Scope 2, not marginal avoided CO2 |
| 8,760 calendar hours | 365 days | Model convention | Fixed nonleap-year physical baseline | DC full-load equivalence only |

**There are no Court Barton production measurements, weather time series, dispatch data or verified avoided emissions in this case.** Developer claims are kept distinct from official reference benchmarks and derived algebraic scenarios.

## Calculation

Reusable function: `energy_methods.pv_news_claims.audit_pv_news_claims`.

- Electricity *equivalent* (MWh/y) = homes × assumed household kWh/y ÷ 1000.
- DC-equivalent full-load hours = electricity-equivalent MWh/y ÷ peak MWp. DC-equivalent full-load fraction = hours ÷ 8,760; the absolute no-downtime physical ceiling is 100%.
- Lower bound of claim-implied avoided **CO2** intensity (kgCO2/kWh) = 1,000 × reported avoided tonnes CO2 floor ÷ assumed electricity-equivalent kWh.
- Separately, an **average-grid CO2e accounting benchmark** (tonnes CO2e/year) = equivalent electricity kWh × UK 2026 DESNZ average generation factor ÷ 1000.

For the official **medium** 2,500 kWh/home/year reference, the 8,500 homes claim corresponds to **21.25 GWh/year** of electricity equivalence, **1,062.5 DC-equivalent full-load hours**, or **12.13%**. The developer's **more-than-6,200-tonne CO2** claim implies **more than 0.292 kgCO2/kWh** *conditional on that consumption assumption*. The separate DESNZ average-factor benchmark is **2,782.9 tonnes CO2e/year** for 21.25 GWh. **This last result is not actual avoided emissions and does not refute the claim:** the released CO2 displacement claim and average-grid CO2e factor have different accounting and counterfactual boundaries.

Ofgem low/medium/high usage scenarios span 13.6, 21.25 and 32.3 GWh/year and 7.76%, 12.13% and 18.44% DC-equivalent full-load fractions. These are scenarios, **not a P50/P90 range, confidence interval or forecast**.

## Reproduction and verification

```bash
uv sync --locked --all-packages --python 3.13
uv run --no-sync pytest methods/tests/test_pv_news_claims.py
MPLBACKEND=Agg uv run --no-sync python examples/analysis/plot_court_barton_pv_claims.py
uv run --no-sync ruff format --check .
uv run --no-sync ruff check .
uv run --no-sync ty check
uv run --no-sync sphinx-build -W --keep-going -b html docs docs/_build/html
```

## Scientific limits and next evidence

No project-specific PVGIS/P50/P90 yield, DC-to-AC ratio, inverter clipping, grid export/curtailment, energy settlement data, generation observations or life-cycle analysis is included. The exact consumption basis behind the developer's "homes powered" is unknown; this news release does not document its avoided-emissions calculation. A location-based **annual average CO2e** factor is not a **marginal hourly counterfactual CO2** factor. This tool cannot validate actual generation, carbon savings, additionality, ESG claims, or financing. Next, acquire independent site weather, an audited yield study, actual metering and the developer's emissions counterfactual, then quantify uncertainty and financial outcomes.
