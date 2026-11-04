# HVAC forecasting and counterfactual scheduling

The runnable gallery under **Analysis & case studies → Building thermal control**
replicates the two use cases in Antoine Galataud's [Foobot article, 2 November 2026](https://techblog.foobot.io/ai/hvac/control/tsfm-counterfactual-thermal-dynamics.html):

1. **T1, usual schedule:** temperature MAE versus comfort-time accuracy over 30 mornings.
2. **T2, changed action:** start shifts of −60, −30, +30 and +60 minutes, paired
   with each day's zero-offset T2 forecast from the same issue time.

These examples reanalyse **published EnergyPlus simulation outputs and published
Timestral-209M forecasts**. They are not measured building data, new Timestral
inference, or an independent reproduction of the EnergyPlus experiment. The
source does not provide its complete IDF/EPW, ten-day contexts, checkpoint
revision or inference configuration. Those are required before claiming an
end-to-end model reproduction. No generated surrogate is labelled Timestral.

## Input, method, analysis

- `energy_data_retrieval.foobot`: bounded public download and safe JSON-wrapper
  parsing, shape/finite-value/quantile checks, complete schedules, duplicate
  rejection, identical T2 grids and setpoints. Never executes JavaScript.
- `energy_methods.thermal_counterfactual`: sustained heating-threshold crossing
  with linear interpolation and paired intervention error. Units are degrees C
  and minutes relative to each morning's baseline start; timezone is unknown.
- `energy_analysis.thermal_counterfactual`: per-panel scores and per-day response
  slopes. T1 cannot substitute for the T2 baseline. Complete five-schedule days
  are required for sensitivity ratios; zero reference slopes are excluded.

The target is 21°C with 0.25°C tolerance and two consecutive samples. Inspection
of published event times reveals a start-gating convention: comfort is not
scored before candidate HVAC enablement. We implement this explicitly using
`not_before_min=offset`, and retain `unrestricted_prediction_met_min` to expose
pre-enable warming. On January 12, the +60-minute forecast crosses at about
46.1 minutes unrestricted, but the published convention reports 60 minutes.
This detail is inferred from the numerical asset, not stated explicitly in the
article. Missing events remain missing, with valid-pair counts displayed; they
are never replaced with the horizon. Initial comfort is left-censored.

The published summary is recovered to rounding: 0.552°C T1 MAE, 107.8-minute
mean absolute comfort error, 15/30 mornings within ±15 minutes, approximately
24.4-minute mean absolute T2 shift error, three censored comparisons. Our stricter complete-day slope calculation
returns 0.231 (27 days), versus the article's reported 0.25. We retain this
difference rather than claim exact reproduction of an unspecified slope filter. The source's rounded curves may differ slightly
from full-precision results. Pointwise q10–q90 temperature bands are not 80%
confidence intervals for comfort time.

## Reproduce

```bash
uv sync --locked --all-packages --group docs
uv run python scripts/prepare_thermal_counterfactual.py --output artifacts/thermal
# Or reanalyse a previously downloaded public data.js without network access:
uv run python scripts/prepare_thermal_counterfactual.py --source /path/to/data.js --output artifacts/thermal
uv run python examples/analysis/plot_thermal_forecast.py
uv run python examples/analysis/plot_thermal_counterfactual.py
```

The preparation command writes derived scores, sensitivities, two January 12
numerical trajectories, and an acquisition manifest with SHA-256 source/output
hashes. Gallery examples use committed numerical summaries and run offline.
The original JavaScript, article prose, chart artwork and interactive interface
are not bundled. Public availability does not establish a licence for source
assets; retain attribution and review terms for broader redistribution.

For new inference, reuse `energy_methods.timestral.TimestralConnector` with a
pinned local Timestral-209M checkpoint, temperature context and known covariates
(outdoor temperature, fixed setpoint, candidate availability). Set
`clip_nonnegative=False` for temperatures. Use the same pre-intervention issue
time and historical context for every candidate, never feed future indoor
measurements as context. Actual simulation weather is an oracle input in this
experiment; operational forecasts add weather uncertainty. A separate simulator
rerun for each candidate is needed for intervention ground truth.

## Scope and limitations

This implements the article's T1/T2 evaluation, not the cited papers' excitation,
physics-structured adaptation or model-distillation algorithms. Demand response
and equipment optimisation are motivations, not validated savings use cases.
No heating-power series or tariffs are supplied, so neither energy nor monetary
savings can be computed. A forecast benchmark alone does not validate a control
policy, causal identification in real buildings, or safe deployment. The
results concern one simulated zone and do not establish a general model ranking.
