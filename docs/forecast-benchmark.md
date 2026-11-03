# Solar and wind forecasting benchmark

The [runnable gallery example](https://julianascencio.github.io/energy-data-insights/auto_examples/analysis/plot_forecast_model_benchmark.html)
compares LightGBM, XGBoost, Mistral Timestral-5M and physical surrogates against
a previous-day baseline on **real ONS observations**. The downloadable ZIP includes
the Python example, native CSV subsets, input/model provenance and score tables.
The default run is offline: tree and physical models are fitted again, while
verified saved predictions from actual Timestral inference are replayed.

## Research inspiration and differences

**Ascencio-Vásquez, J., Bevc, J., Reba, K., Brecl, K., Jankovec, M. and Topič, M.
(2020). Advanced PV Performance Modelling Based on Different Levels of Irradiance
Data Accuracy. *Energies*, 13(9), 2166.
[doi:10.3390/en13092166](https://doi.org/10.3390/en13092166).**

The paper motivates attention to irradiance quality and comparisons between
empirical and machine-learning PV models. This example extends those ideas to
forecasting with different observations and model families. It does not reproduce
the Ljubljana experiment, its three irradiance-accuracy tiers, filtering algorithm,
or reported accuracy. Wind, XGBoost, Timestral and the rolling protocol are additions.

| Design choice | This forecasting example |
| --- | --- |
| Resource quality | Preserve ONS flags, qualify the initial solar resource record, disclose sensor-plane and wind-unit uncertainties. |
| Validation | Chronological daily origins; only earlier observations construct features. |
| Test population | Keep every test label, including nights and curtailment; no acceptance-band or test-outlier removal. |
| Error normalization | Raw MAE/RMSE in MW; normalized MAE uses historical Q95 power, not the paper's nominal-capacity denominator. |

## Real observations and time semantics

The June 2024 ONS monthly solar/wind restriction-detail exports contain measured
generation, measured resources, quality indicators and restriction flags. The
example retains **all native columns** for Coremas IV (`PBFCM4`, solar) and Delta
3 I (`MAEDT1`, wind), 1,440 half-hour records each. No estimated or reference
generation replaces measured generation. ONS attribution, URLs, retrieval times,
full-file/subset hashes and exact transformations are saved in
`forecast_ons_provenance.json`.

Solar selection uses only the first 14 days: the first plant in native source
order with 672 records, at least 650 valid resource flags and 150 valid readings
above 100 W/m². This excludes an all-zero irradiance sensor even when its flags
say valid. Wind is the first plant in its native export. Neither selection uses
test-period quality or forecast errors.

Generation is **MWmed**, mean MW over each half-hour, not MWh. Native timestamp
reference labels are localized with `America/Sao_Paulo` and converted to UTC,
without asserting whether the provider labels interval starts or ends. The issue
label is the last historical timestamp; targets are 0.5–24 hours after it.
Historical observations are assumed available at their labels. ONS exports may
contain post-operation revisions, so this is a retrospective experiment rather
than a verified as-issued operational backtest.

## Forecast protocol and available information

Each model uses the preceding 14 days (672 steps); it is refitted or reconditioned
at 16 daily origins. Each origin predicts the next 48 steps, giving **768 scored
points per plant and model**. No shuffled split, test-based early stopping or
test-set hyperparameter tuning is used. Predictions are clipped at zero for all
models; no future actuals determine a cap. Failures or incomplete model coverage
raise an error rather than silently dropping difficult points.

Solar resource forecasts use the most recent valid same-clock irradiance, normally
the previous day. Wind resource forecasts hold the last valid speed constant.
Flagged historical resources remain missing; solar fallback searches earlier days,
never later measurements. These are **weather-persistence forecasts, not NWP**.
Trees share four features: resource, UTC daily sine/cosine and previous-day power.
Their historical fit uses measured past resource; future inference uses its
persistence forecast, so resource-forecast error contributes to model error.
Both trees use the same finite rows (initial unavailable lags are omitted).
Timestral gets the full generation context and the same four history/future
covariates; missing historical covariates remain NaN. Physical surrogates fit on
the same finite rows as the trees but use only the resource column. All models
use the same allowed information set, with architecture-specific representations.
Restriction flags annotate results only; they are never forecast features or
reasons to exclude test observations.

| Model | Implementation |
| --- | --- |
| LightGBM | `fit_lightgbm_features`; 200 trees, learning rate 0.04, 15 leaves, minimum 20 child samples, seed 42, one CPU thread. Unconstrained generic feature regression; existing monotone PV API is preserved. |
| XGBoost | `fit_xgboost`; CPU histogram squared-error regression, 200 trees, learning rate 0.04, depth 4, minimum child weight 10, L2 1, seed 42, one thread. Full row/column sampling. |
| Timestral | Pinned `mistralai/Timestral-5M`, zero-shot median forecast; P10/P90 retained. No fitting or fine tuning on this benchmark. |
| Solar physical | Existing nonnegative, concave irradiance response. ONS irradiance is treated as a POA proxy with undocumented sensor orientation. Constant 25°C because temperature is absent: an isothermal empirical surrogate, not identified module thermal physics. Convert MW to half-hour MWh for the existing API, then back. |
| Wind physical | Generic cubic ramp between 3 and 11.4 m/s, rated plateau until 25 m/s, zero outside operating range. One nonnegative scale fitted from historical power. No wakes, density, outages or curtailment model. |
| Previous day | Reuse generation from the same 48 offsets of the preceding day. |

The wind reference speeds come from Jonkman et al. (2009),
[*Definition of a 5-MW Reference Wind Turbine for Offshore System Development*](https://www.nrel.gov/docs/fy09osti/38060.pdf),
NREL/TP-500-38060. The interpolating curve is a repository approximation, not that
turbine's aerodynamic curve or the actual farm equipment. Its fitted scale is
not installed capacity. The ONS wind dictionary calls `val_ventoverificado` speed
but prints **m³/s**, a dimensional inconsistency. We explicitly assume its native
numerical readings represent m/s; no volumetric-flow conversion is performed.
These assumptions limit interpretation of the physical-model result.

## Scores and interpretation

The example prints MAE, RMSE, mean signed error (prediction minus observation),
WAPE, normalized MAE, baseline skill and Timestral P10–P90 coverage. WAPE is total
absolute error divided by total absolute observed power; it is undefined when
that denominator is zero. Normalized MAE divides each absolute error by its
origin's training-power Q95, then averages. MAE skill is
`1 - model_MAE / previous_day_MAE`; positive values beat the daily baseline.
Each forecast lead has 16 observations. Lead and clock time are coupled by the
fixed daily issue time, especially for solar. No significance claim is made.

The plots show all models' MAE, the final three test days selected by date, and
MAE by forecast lead. Saved score tables are reproduced from the declared
software/data versions; small numerical differences across dependency versions
are possible. Ranking applies only to these plants, dates, features and defaults.
It cannot establish a best model across climates or seasons. Unknown Timestral
pretraining overlap and uncalibrated prediction intervals are additional limits.

## Run from the repository

```bash
uv sync --locked --all-packages
MPLBACKEND=Agg uv run --no-sync python examples/analysis/plot_forecast_model_benchmark.py
uv run --no-sync python scripts/prepare_forecast_benchmark.py
```

For the downloaded ZIP, install this repository's `energy-analysis` package and
its workspace dependencies (or the three built wheels), extract the ZIP and run
`python plot_forecast_model_benchmark.py` from any directory. Keep `data/forecast`
next to the script. Set `ENERGY_FORECAST_OUTPUT=/path/to/results` to save prediction
and score CSVs. No credentials or model downloads are required in replay mode.

For **live Timestral**, follow [the optional installation guide](timestral.md), then:

```bash
ENERGY_FORECAST_TIMESTRAL_LIVE=1 ENERGY_TIMESTRAL_LOCAL_ONLY=1 \
  uv run --no-sync python examples/analysis/plot_forecast_model_benchmark.py
```

The manifest pins the exact checkpoint. Omit `ENERGY_TIMESTRAL_LOCAL_ONLY=1` to
allow downloading it. Optional `ENERGY_TIMESTRAL_DEVICE=cuda` selects a GPU;
the captured results used deterministic CPU inference. Model loading/inference
errors fail explicitly; a baseline is never substituted for Timestral.

Maintainers can reacquire inputs and capture all actual model predictions:

```bash
uv run --no-sync python scripts/prepare_forecast_benchmark.py --download --capture-timestral
```

The capture command requires the optional runtime and public network access;
`--use-env-proxy` explicitly opts into `HTTPS_PROXY` when needed. It records
checkpoint/source hashes, model revision, package versions, all fold-input hashes
and prediction checksums. Model snapshots become invalid if any inputs change.
Large source downloads and full per-model predictions stay under `artifacts/`;
small attributed native subsets, Timestral captures and scores belong to the
example. The source/model manifests contain the authoritative acquisition and
inference details.

## Reusable methods and sources

`energy_methods.xgboost.fit_xgboost(X, y, feature_names=...)` accepts finite
two-dimensional feature arrays and aligned targets in any declared unit. Its
model validates prediction width and exports native JSON state, feature order,
configuration and training-row count. Feature construction and chronological
splitting remain the caller's responsibility. `fit_lightgbm_features` provides
the corresponding generic LightGBM contract; the existing `fit_lightgbm` PV API
continues to enforce its own physical feature assumptions.

XGBoost attribution: Chen and Guestrin (2016),
[*XGBoost: A Scalable Tree Boosting System*](https://doi.org/10.1145/2939672.2939785).
The central [reference catalogue](references.md) also links the official
LightGBM/Timestral software, ONS solar/wind data and physical-method sources.
