# Applied CCYA: the Bolzano thesis workflow

This example applies Climate Change Yield Assessment (CCYA) following the study
design in Ascencio Vásquez's PhD thesis, §§7.5.2–7.5.3, Figures 7.10–7.21:
monthly site adaptation, a seasonal irradiance-to-DC-yield relation, historical
yield quantiles, and separate and combined irradiance, temperature and degradation
effects over a 50-year operating period.

**The runnable example uses synthetic data.** Eurac's original ABD plant
production/weather database is access-restricted. No original plant measurements
or CMIP6 series are bundled. Paths A–G are artificial sensitivity paths, **not the
seven SSP projections from the thesis**. This reproduces the analysis structure,
not the thesis's numerical results or a forecast for the actual Bolzano plant.

## Run the complete example

From the repository root:

```bash
uv sync --locked --all-packages
uv run energy-ccya demo --output artifacts/ccya-demo
```

Open `artifacts/ccya-demo/results/reports/index.html`. It is an offline,
self-contained report with seven figures, a 25/50-year comparison table, embedded
CSV download and input provenance. PNG and SVG versions accompany the report.
Use a new output directory for each run; existing results are never overwritten.
No network connection or provider credentials are needed after installation.

The generated `case.toml` and monthly CSVs make the study inspectable and reusable.
To rerun them, copy the config, give it a new `output_path`, and execute:

```bash
uv run energy-ccya run --config artifacts/ccya-demo/case-rerun.toml
```

The deterministic default seed is `202110` (`--seed` selects another seed).
There are ten calibration years (2010–2019), 50 projection years (2020–2069),
seven artificial paths and four linear degradation assumptions: 0, 0.25, 0.5 and
1%/year. Each path is fitted to its own historical model series. The exact imposed
GHI trends and warming are recorded in its config source field. They are illustrative
inputs, not estimates taken from the thesis or a climate model.

## What is applied from the thesis

| Stage | Thesis connection | Example output |
|---|---|---|
| Monthly weather adaptation | Figures 7.11–7.12 | Raw model/site pairs and fitted weather regressions |
| Irradiance-to-yield relation | Figure 7.13 | Twelve monthly centroids of raw model GHI and mean daily DC yield |
| Historical and future annual yield | Figures 7.14–7.15 | Annual values, ten-year trailing means, historical P10/P50/P90 |
| Irradiance change | Figure 7.16 | Cumulative gain/loss against each historical quantile |
| Incremental temperature effect | Figures 7.17–7.18 | Energy-weighted temperature factor and adjusted cumulative yield |
| Linear degradation | Figures 7.19–7.20 | Power retention and degradation-adjusted yield |
| Combined assessment | Figure 7.21 | Separate and combined effects at operating years 25 and 50 |

The example calls the reusable [`energy_methods.ccya`](../../../methods/src/energy_methods/ccya.py)
implementation rather than duplicating its equations. See the
[method specification](../../../docs/ccya.md) for equations and explicit choices:

- The daily-yield response is a through-origin slope for each calendar month,
  fitted from raw model GHI and measured monthly DC yield divided by measured days.
- Temperature uses the method defaults: coefficient −0.0045/°C and Ross constant
  0.03 °C m²/W. The multiplier is normalized against the adapted historical model
  monthly reference, so historical thermal losses already present in measured
  yield are not counted again.
- Linear degradation begins at zero age in the first operating year; a 0.5%/year
  case retains 75.5% in year 50. It is an assumption, not a degradation fit.
- P10/P50/P90 mean **nonexceedance** quantiles Q10/Q50/Q90 of measured annual yields.
  They are not finance-style exceedance probabilities, scenario probabilities,
  prediction intervals, or a guarantee. The ten-year sample is illustrative.
- Signed cumulative gain is `100 × (cumulative energy / (annual baseline ×
  operating years) − 1)`. Zero means equal energy. Saved annual tables also retain
  the ratio convention where equality is 100%. Multiplicative component effects
  must not be added as percentages.

## Use qualified plant and climate data

Copy [`real-data.toml`](real-data.toml), supply monthly files, and replace every
source placeholder with actual dataset, model, experiment, member, location,
calendar and preprocessing identifiers. Add one `[[scenarios]]` block for each
model/member/SSP combination. Keep the scenario label separate from its probability;
the analysis assigns no scenario probabilities.

CSV column order is arbitrary; the following names and units are required:

| Column | Plant observations | Historical and future climate |
|---|---|---|
| `month` | `YYYY-MM`, unique, ordered, complete calendar years | Same format |
| `ghi_wm2` | All-hours monthly mean GHI, W/m² | All-hours monthly mean surface downwelling shortwave radiation, W/m² |
| `temperature_c` | Monthly mean ambient temperature, °C | Monthly mean near-surface air temperature, °C |
| `days` | Gregorian number of days in that month | Explicit native month length |
| `dc_yield_kwh_kwp` | Monthly DC energy / qualified DC nameplate capacity, kWh/kWp | Omit this column |
| `data_kind` | `observations` | `climate_model` |

The synthetic generator uses `synthetic` in **all** input rows. Changing the config
to `observed_and_projected` alone cannot relabel those files as measured data.
Labels are declarations, not independent verification of data authenticity.

At least two complete calibration years are required; more years are needed for
credible historical quantiles. Every model's historical months must exactly match
the plant calibration months. Future months must follow calibration, cover every
requested report horizon, and have the same monthly index and calendar across
cases. This analysis accepts Gregorian or noleap future calendars. Annual totals
retain their native durations; leap days can cause small annual differences.
360-day and fixed-leap calendars require an explicit, documented upstream choice
before comparison with observed annual energy. No conversion, interpolation,
spatial extraction, quality screening or retrieval is silently performed here.

Prepare the inputs upstream: verify DC capacity and stable system configuration,
exclude or explicitly account for outages and missing data, aggregate to complete
months, select the correct climate cell or interpolation, convert kelvin to °C,
and retain retrieval provenance. An AC production series is not interchangeable
with the thesis's DC specific yield. Regressions are in-sample calibration; the
report's support flags identify extrapolation but do not establish predictive
validity. Historical losses are embedded in the fitted reference. The uncertainty
shown excludes regression, model-ensemble and future operational uncertainty.

## Reproducible outputs

| Path below `results/` | Contents |
|---|---|
| `inputs/` | Exact input CSV snapshots |
| `scenarios/<id>/model.json` | Frozen fitted model and method parameters |
| `scenarios/<id>/rate-NN/` | Monthly components, annual/rolling/cumulative metrics and metadata |
| `summary.csv` | All components against P10/P50/P90 for each requested horizon and degradation rate |
| `manifest.json` | Complete configuration, source statements, versions, Git revision and input/output SHA-256 hashes |
| `references.bib`, `references.md` | Thesis and supporting scientific/software sources |
| `reports/index.html`, `reports/figures/` | Self-contained report and seven PNG/SVG figures |

All result files are published together only after the run and report succeed.
Failures remove the temporary result directory. The demo's generated inputs remain
available if a later analysis step fails. Results are ignored by Git; regenerate
them instead of committing downloaded data or generated figures. Report code lives
in [`ccya_case/reports/`](../../src/energy_analysis/ccya_case/reports/).

References are maintained centrally in [`references.json`](../../../methods/src/energy_methods/references.json):
`ascencio_vasquez_2021_thesis` (primary), `polo_2020_site_adaptation`,
`skoplaki_palyvos_2009_temperature`, `hunter_2007_matplotlib` (plotting), and
`eurac_abd_data_access` (access limitations only).
