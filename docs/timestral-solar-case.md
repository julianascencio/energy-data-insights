# Timestral for solar: a real win with a strong baseline check

The [runnable gallery example](https://julianascencio.github.io/energy-data-insights/auto_examples/analysis/plot_timestral_solar_case.html)
forecasts **Mendubim VI solar generation in Brazil, 24 hours ahead**, using real
ONS observations. Timestral-28M reads the preceding 14 days of generation without
weather forecasts or fine tuning. It beats the fixed LightGBM, XGBoost and
physical-surrogate comparators on August 2024 MAE and RMSE.

It does **not** establish meaningful superiority over every model. Its August
MAE advantage over a 14-day same-clock median is just **0.0048%**, a practical tie.
A same-clock mean has better RMSE. Those baselines are included prominently.

## Held-out August results

Every row below covers the same **31 daily origins and 1,488 half-hour targets**.
Lower errors are better; units are mean MW over each half-hour, not MWh.

| Model | MAE (MW) | RMSE (MW) | Timestral MAE reduction |
| --- | ---: | ---: | ---: |
| Timestral-28M | 2.809545 | 5.154373 | — |
| Daily median, preceding 14 days | 2.809680 | 5.193739 | 0.0048%, practical tie |
| Daily mean, preceding 14 days | 2.817207 | **5.107030** | 0.2720% |
| Physical surrogate | 2.900642 | 5.177469 | 3.1406% |
| LightGBM | 3.028465 | 5.598410 | 7.2287% |
| XGBoost | 3.042184 | 5.694536 | 7.6471% |
| Previous day | 3.590715 | 7.187679 | 21.7553% |

Timestral has lower daily MAE than the physical model on 19/31 days and than
Daily median on 16/31. Monthly ranking is not a claim of winning every day.
These are descriptive results from one site and month, without a statistical
significance or operational-savings claim. Small dependency/platform changes may
reverse the near tie. See `solar_case_scores.csv` for full-precision scores.

## What was selected, and when

The search was requested specifically to find a Timestral success case. Its
selection bias is therefore part of the result, not hidden from the reader.

1. **June plant search.** Take the first 20 plants in native June export order
   passing qualification on June 1–14 only: 672 records, at least 650 valid
   irradiance flags, at least 150 valid readings above 100 W/m², and complete,
   nonnegative measured generation. Run Timestral-5M with all four benchmark
   covariates and six comparators on June 15–30. Choose the largest relative MAE
   gain against the best comparator. Mendubim VI (`RNMB06`) is the only winner,
   ahead by 8.66%. All 140 candidate/model scores are in `plant_search.csv`.
2. **Failed July validation.** That selected 5M configuration loses in July:
   3.586077 MW MAE versus 3.032351 MW for Daily mean. The seven scores remain in
   `first_validation_scores.csv`; July was then reclassified as development.
3. **Configuration search on June/July.** At the selected plant, compare 5M and
   28M, each with generation only, calendar covariates, or all four covariates.
   Select the smallest MAE across all 47 June 15–July 31 origins. Generation-only
   28M wins at 3.136869 MW. The six results are in `variant_search.csv`. No tree or
   physical hyperparameters were tuned; they retain the existing benchmark defaults.
4. **Final August evaluation.** Freeze plant, model size, generation context,
   covariate choice and the full August period before scoring it. Do not search
   for favorable August days, filter curtailment, or remove nights. The pipeline
   needed the input-availability repairs described below, before the complete
   August score could be calculated. This is a transparent retrospective study,
   not a preregistered untouched-pipeline trial.

`selection_audit.json` retains the two selection timestamps, failed attempt,
model configurations and availability repairs. The research command below reruns
the fixed search using June/July only and refuses August development inputs.

## Information and model boundaries

The existing [forecast benchmark](forecast-benchmark.md) documents the fitted
methods: 200-tree LightGBM/XGBoost defaults, the nonnegative concave PV response,
UTC clock sine/cosine, previous-day power and persistence irradiance forecasts.
Every issue refits on the preceding 672 half-hour records, subject to the
explicit availability fallbacks below. Future measured irradiance and future
restriction flags never enter a prediction.

Timestral uses **generation only**, with the same 672-step context. Its checkpoint
is `mistralai/Timestral-28M` at
`49b26409ac87b5935539a5d8ffe7f397b720db47`; the optional inference code is pinned
through the existing connector. It never receives the deliberately noisy
persistence-weather forecast selected against on development data. The other
models retain that weather information. This compares the declared workflows;
it does not isolate architecture quality under identical feature representations.

Daily mean and Daily median calculate, for each half-hour offset, the mean or
median of its 14 preceding daily values. Previous day repeats yesterday. No
baseline uses future data. All predictions have the same nonnegative clipping,
and missing, duplicate or incomplete forecast coverage raises an error.

## Irradiance-data gap and causal fallbacks

The August export contains flagged resource readings. Near the end of the month,
some clock offsets have no valid reading in the preceding 14 days. Those readings
remain missing in calibration. For the two final forecast issues, resource
persistence searches farther back in the already observed history when needed.
Only the weather-dependent models benefit from this additional resource history.

At the final issue, accepted resource-valid calibration rows have zero generation
Q95, making the physical fit unidentifiable. All three fitted comparators retain
their most recent informative calibration window, while predicting with the
current pre-issue future features. The exported `calibration_issue_time` records
that choice. The zero-shot model and seasonal baselines continue to use current
generation history. No August forecast label is excluded.

These safeguards followed execution failures, before the complete August metrics
were available. They are disclosed implementation adaptations, not evidence that
sensor failure caused Timestral's advantage. The study does not identify the
cause of flagged readings or isolate a sensor-gap treatment effect.

## Observations, provenance and inspiration

The fixture preserves **all 18 native fields** from the ONS solar restriction-detail
exports for June–August 2024, 4,416 records. It never substitutes estimated or
reference generation for measured generation. Full monthly-download hashes,
request metadata, the subset checksum, original columns, source URLs and CC-BY
attribution are in `forecast_ons_provenance.json`.

Native `America/Sao_Paulo` timestamp reference labels are converted to UTC without
asserting interval-start or interval-end semantics. The issue is the last
historical reference label. Revised ONS historical values are assumed available
at those labels; this is not an as-issued operational backtest. No archived NWP
is available here. Irradiance is a proxy with an undocumented sensor plane, and
temperature is held at 25°C for the physical surrogate. Unknown Timestral
pretraining overlap and uncalibrated P10/P90 intervals are further limits.

**Ascencio-Vásquez, J., Bevc, J., Reba, K., Brecl, K., Jankovec, M. and Topič, M.
(2020). Advanced PV Performance Modelling Based on Different Levels of Irradiance
Data Accuracy. *Energies*, 13(9), 2166.
[doi:10.3390/en13092166](https://doi.org/10.3390/en13092166).**
The paper motivates attention to irradiance quality and comparisons between
empirical and machine-learning PV models. This example uses different data and
forecasting methods; it does not reproduce its Ljubljana experiment, accuracy
tiers, filtering or numerical results.

## Run it

```bash
uv sync --locked --all-packages
MPLBACKEND=Agg uv run --no-sync python examples/analysis/plot_timestral_solar_case.py
uv run --no-sync python scripts/prepare_timestral_solar_case.py
```

The default fits all non-neural methods again and verifies the saved real
Timestral forecasts against their checksum and every fold's exact inputs.
It works without network access or PyTorch. The preparation command exports
predictions and daily errors under `artifacts/timestral-solar`.

For the downloadable ZIP, install this repository's three workspace packages
(or their built wheels), extract the ZIP and run `python plot_timestral_solar_case.py`.
Keep `data/timestral_solar` next to the example. Set
`ENERGY_TIMESTRAL_CASE_OUTPUT=/path/to/results` to save figures and result CSVs.

For actual live inference, follow the [optional Timestral installation](timestral.md):

```bash
ENERGY_TIMESTRAL_CASE_LIVE=1 ENERGY_TIMESTRAL_LOCAL_ONLY=1 \
  uv run --no-sync python examples/analysis/plot_timestral_solar_case.py
```

Omit `ENERGY_TIMESTRAL_LOCAL_ONLY=1` to permit the pinned checkpoint download.
No API key is needed. Captures used deterministic CPU inference, one thread and
seed 0; the manifest records package versions, source/checkpoint hashes and inputs.

Maintainers can reacquire inputs, rerun the disclosed development search and
recapture the actual model outputs:

```bash
uv run --no-sync python scripts/prepare_timestral_solar_case.py \
  --download --research --capture-timestral
```

`--research` writes its audit under `artifacts/timestral-solar` and does not change
the frozen plant or select a model on August. It needs the optional Timestral
runtime and both pinned 5M/28M checkpoints. `--use-env-proxy` explicitly opts
into the environment proxy when required for downloads.
