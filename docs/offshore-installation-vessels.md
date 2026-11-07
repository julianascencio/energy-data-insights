# Dogger Bank C: vessel installation and commissioning sensitivity

**Primary evidence (4 November 2026):** [Dogger Bank Wind Farm's announcement](https://doggerbank.com/news/) states that the Dogger Bank C phase is **1.2 GW with 87 turbines** and the new vessel *Wind Apex* will join *Seaway Ventus* in **Q3 2027**. It does **not** establish the exact joining date, site installation rates, weather, grid-ready day, turbines already installed, production, vessel charter costs or power prices. The small set of published facts is manually transcribed into the gallery script, not fetched or redistributed from a third-party dataset.

**Independent industry context:** Reuters, 6 November 2026, [Germany's onshore wind logistical bottlenecks](https://www.reuters.com/business/energy/germanys-onshore-wind-boom-faces-logistical-hurdles-turbine-orders-surge-2026-11-06/). German onshore transport conditions are **not** numerical inputs to this UK offshore case.

## Business problem and method

How could a second turbine installation vessel shorten the construction critical path, and how would grid-connection readiness affect the opportunity to export earlier generation?

`energy_methods.wind_installation.simulate_installation` takes a phase turbine count, vessel starting offsets, site-wide daily workable-day flags and a minimum workload of workable vessel-days per turbine. Each active vessel accumulates installation progress separately, holding it across weather delays; installation timestamps and charter exposure days are returned. This is a constrained daily project-planning model, not an offshore construction digital twin.

`energy_methods.wind_installation.commissioning_opportunity_mwh` then computes a conditional **gross potential-energy envelope** under progressive per-turbine commissioning, assuming equal-rated turbines. With project capacity P (MW), net capacity factor CF, N installed turbines, common export-ready day g, commissioning lag L, installation completion day t_i, and fixed horizon T (days):

$$
E_{\mathrm{opportunity}} = 24 P CF \frac{1}{N}
\sum_{i=1}^{N} \max(0,T-\max(g, t_i+1+L)).
$$

Units are MWh. This is **not actual generation, energy loss, expected revenue, or energy-not-served**.

## Input provenance and assumptions

Only **87 turbines**, **1,200 MW**, and **two named vessels with Q3 2027 as the advertised second-vessel arrival window** are public source-reported facts. Everything else is **invented scenario input**: an arbitrary day-zero campaign origin; joining after 90 campaign days, with no inference to a calendar date; 70% independently sampled workability per day (not metocean calibrated); three workable vessel-days per turbine; 200 fixed-seed independent weather scenarios (20261107); study horizon 560 days; net capacity factor 48%; three assumed grid-ready offsets (0, 350, 500 days); and €65/MWh as a purely hypothetical gross energy-value multiplier.

Paired scenarios use identical synthetic weather to isolate vessel count. Duration and modeled opportunity percentiles are conditional simulation variation under the assumed weather process, **not confidence intervals for Dogger Bank or validation of its likely completion date**.

## Reproduce offline

From the locked repository workspace (Python 3.12 or 3.13):

```bash
uv sync --locked --all-packages --group docs
uv run --no-sync pytest methods/tests/test_wind_installation.py -q
MPLBACKEND=Agg uv run --no-sync python examples/analysis/plot_dogger_bank_vessel_installation.py
uv run --no-sync sphinx-build -W --keep-going -b html docs docs/_build/html
```

The Sphinx-Gallery build executes the example offline and includes plots of synthetic campaign durations and grid-limited energy opportunity. No credentials, API calls or live network are needed for this specific example.

## Limitations, interpretation and research extensions

The model excludes actual work-package dependencies, foundations, port loading, shared weather windows, metocean persistence, vessel transit, equipment/crew mobilization, vessel performance specifications, permits, cables, grid synchronization and commissioning regimes. It assumes each turbine can export from the day after installation (or after an explicit lag), subject to a common export gate; this is **not verified** for Dogger Bank. The equal rating simplification is derived from aggregate nameplate, not turbine equipment telemetry. The 48% net CF and €65/MWh are deliberately hypothetical, not published actual plant performance or contract prices. Do not infer real energy lost or actual financial benefit from the scenario charts.

The next scientifically useful step would join licensed metocean time series, vessel logbooks and observed work-package completion, contract terms and public grid energization milestones, then compare progressively energized and full-phase commissioning and optimize vessel commitments under credible downtime covariance.
