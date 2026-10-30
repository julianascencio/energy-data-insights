# Energy methods

## PV climate classifications

[Compare KGPV, JRC parametric climates, ML21 and PVCZ](../docs/climate-comparison.md).
The implementation includes validated source readers, fixed PVCZ thresholds,
frozen JSON cluster models, and offline global/Chile/Canary reference maps.
Source periods, input units, published labels and documented refits stay explicit.

## Main reference and method attribution

The main scientific reference is **Julián Andrés Ascencio Vásquez (2021),
_Modelling and worldwide assessment of performance and aging of photovoltaic
modules and systems_, University of Ljubljana**. The [full catalogue](../docs/references.md)
contains the original method papers, data sources, software and standards;
[references.bib](../references.bib) provides BibTeX. Each method exposes
`REFERENCE_IDS`; portable fitted-state exports retain those IDs.

Cite the thesis together with each method actually used. The published TDP and
acceptance-band methods are adapted explicitly below. The shape-constrained PV
basis is repository-specific and uses the Stark–Parker BVLS algorithm through
SciPy. Operational screening is informed by IEC TS 63019 and does not establish
IEC conformity, verified causes or certified availability.


Country-neutral, typed Python methods for photovoltaic performance assessment.
Install as `energy-methods` and import `energy_methods`. The workspace root
documents installation and quality checks.

## Scientific scope

- Climate Change Yield Assessment (CCYA) follows thesis sections 7.5.1-7.5.3:
  historical monthly calibration, future irradiance/temperature/degradation
  components and annual/cumulative comparisons. The [CCYA guide](../docs/ccya.md)
  maps equations and explicitly documents fitting and normalization choices.
- Acceptance bands follow the two-stage bin/curve method in
  [Ascencio-Vásquez et al. (2020)](https://doi.org/10.3390/en13092166).
- Typical Daily Profiles pool original hourly observations by calendar month and
  hour, with separate year-to-year profiles, following
  [Ascencio-Vásquez et al. (2021)](https://doi.org/10.1016/j.solener.2021.07.007).
- Effective POA uses pvlib solar position, Erbs decomposition and Hay-Davies
  transposition. Inferred geometry is a model hypothesis, not verified as-built
  configuration.
- The physical response is analytically concave and nondecreasing in irradiance,
  and nonincreasing in ambient temperature within its declared domain.
- Monotone LightGBM is a separate trainable alternative. Monotonicity does **not**
  guarantee concavity. No accuracy target is guaranteed.
- The IEC-informed screen preserves observable states and leaves operational
  causes unconfirmed. It does not establish IEC availability or storm damage.

All fitting receives the chronological training partition only. Test generation
must never be used for filtering, geometry selection or model selection. Reported
zeros remain observations; missing values are never filled with zero.

## Public interfaces

| Module | Entry points | Units and behavior |
| --- | --- | --- |
| `acceptance_band` | `fit_acceptance_band`, `performance_ratio`, `pr_acceptance_mask` | POA in W/m²; interval energy in MWh; DC STC rating in MW. Unsupported bands raise `BandFitUnavailable`. |
| `poa` | `transpose_ghi`, `fit_effective_poa`, `solar_elevation_midpoint`, `shift_weather` | Timezone-aware UTC hourly interval starts, WGS84 coordinates. Geometry and lag fitting reads training labels only. |
| `physics` | `fit_physics_model` | Accepted POA, ambient °C and hourly MWh. Two analytically constrained model families. |
| `lightgbm` | `fit_lightgbm` | Separate monotone tree model; explicitly bounded threads and deterministic configuration. |
| `metrics` | `energy_metrics` | Matching nonnegative actual/expected pairs, including reported zeros. |
| `status` | `classify_status` | Ten observable hourly states plus envelope, band disagreement, near-zero and persistence evidence. |
| `tdp` | `analyze_tdp` | Country-neutral DataFrame interface; configurable fixed profile clock, default UTC. |
| `ccya` | `fit_ccya`, `CCYAModel.project`, `fit_site_adaptation` | Monthly GHI in W/m², ambient °C, native-calendar days and measured DC yield in kWh/kWp; complete years and separate scenario/member projections. |

Fitted bands and models expose `to_dict()` with portable numerical state. LightGBM
exports its text booster representation, not a pickle. Physical models and tree
models expose `weather_support()` independently of their broader prediction
domain. This prevents an in-domain numerical value from silently becoming an
independently supported operating reference.

## Training and evaluation order

1. Establish a chronological training cutoff in UTC and keep later observations
   for evaluation. Never use a random row split for the time-series result.
2. Infer geometry/clock lag only from that training partition, or use qualified
   as-built metadata. `fit_effective_poa` treats `training_end` as inclusive; an
   exclusive cutoff can be represented as `cutoff - pd.Timedelta(1, 'ns')`.
3. Fit the acceptance band on training POA/energy. Apply the frozen band to the
   training rows used for model fitting. Do not remove poor holdout observations
   to inflate validation scores.
4. Where independently qualified DC STC capacity exists, apply the separate
   inclusive `0.50 <= PR <= 1.00` training gate. An absent DC rating makes this
   gate unavailable; AC capacity is not a substitute. PR is
   `E_AC / (P_DC_STC * POA/1000 * elapsed_hours)`.
5. Fit the physical or LightGBM response to accepted training rows. Evaluate later
   observations on matching actual/expected intervals, retaining zeros.
6. Refit a separate final model only after the evaluation choices are frozen.
   Keep the held-out reference and the final in-sample reference labelled
   separately. New training does not reproduce an older frozen model by identity.

`EnergyMetrics.score_pct` is `100*(1-WAPE)`, where WAPE uses the sum of measured
energy as denominator. It may be negative. It is undefined when the measured
energy denominator is zero. It is not classification accuracy, R² or a promise
of 75% performance. Actual/expected energy bias and errors are also reported.

## Acceptance-band interpretation

The implementation preserves the previously documented interpretation of the
2020 paper, rather than claiming the printed pseudocode is internally consistent:

- Gaussian within-bin means/population standard deviations define the percentile
  ordinates. Low accuracy uses 20/50/80%; medium and high use 5/50/95%.
- The bin width (50 W/m²), maximum irradiance (1,300 W/m²), minimum ten observations
  per bin and seven populated bins are explicit project settings.
- The power normalization is the positive training-energy Q95, **not** capacity.
  Quartic fits use irradiance/1,000 and normalized energy for conditioning.
- Mixed-order roughness uses squared differences at offsets ±2 and absolute
  differences at offsets ±1. Only observed neighboring bin IDs contribute. The
  roughness itself is compared with its empirical 90th percentile; the printed
  comparison of a power ordinate with a roughness threshold is not used.
- Lower and upper signed distances use their respective percentile curves minus
  the fitted center. Outward residuals are trimmed at Gaussian 25/75% distance
  thresholds before separate quartic side fitting.
- Bounds require populated bins within the intersection of the three retained
  fitting domains. Unsupported or crossing bounds return NaN. They are never
  extrapolated, swapped or replaced with a different filter on failure.

The published independent variable is POA. Calling a GHI-based envelope a direct
implementation would be misleading; the application must explicitly document
such an adaptation. The standard workflow uses transposed effective POA.

## Effective POA and time alignment

Solar position is calculated at twelve equal midpoint substeps per hour. Hourly
GHI is distributed in proportion to positive cosine of true zenith, preserving
the hourly mean when the sun is above the horizon. Erbs decomposition and
Hay-Davies transposition follow. Applying an hourly empirical decomposition at
these synthetic substeps is a declared integration approximation. There is no
claim to reconstruct clouds or infer a surveyed array orientation.

The geometry bank is finite and supplied by the caller. Fixed and single-axis
configurations are supported. A positive lag of one means the feature at hour
`t` uses source weather at `t-1`; missing edges remain missing. Lag selection
requires a regular UTC hourly grid and no circular wrapping. Training objective
rows cannot use generation or shifted source weather after the cutoff. Original
solar elevation remains unshifted for operating-state evidence.

Solar position, decomposition and GHI disaggregation are prepared **once per
geometry-bank fit**, then reused. There is no unbounded global cache. The bank
does not require a candidate-by-hour-by-substep tensor, limiting peak memory.

References: [Erbs](https://pvlib-python.readthedocs.io/en/stable/reference/generated/pvlib.irradiance.erbs.html),
[Hay-Davies](https://pvlib-python.readthedocs.io/en/stable/reference/generated/pvlib.irradiance.haydavies.html),
[interval transposition](https://pvlib-python.readthedocs.io/en/stable/gallery/irradiance-transposition/plot_interval_transposition_error.html).

## Physical response versus LightGBM

The concave-spline raw response is

`Q * (r*g + sum(d_k*min(g,k)) + c*g*(tmax-t))`,

with nonnegative `r`, `d_k`, `c`, `g=POA/1000`, `t=(Tamb-25)/25` and training
normalization `Q`. Successive irradiance slopes cannot increase; the temperature
derivative cannot be positive. The thermal-quadratic alternative uses an
equivalent nonnegative transformed basis that constrains the hottest/brightest
irradiance slope to remain nonnegative. Both use constrained least squares with
explicit regularization. The shape domain defaults to POA 0–1,300 W/m² and
ambient temperature −20–60 °C. The POA ≤1 W/m² zero-output convention is a separate
startup cutoff, so the raw shape guarantee excludes that discontinuity.

These parameters are empirical; they do not establish module temperature,
thermal coefficients, shading, bifacial gain or recoverable losses.

LightGBM uses the squared-error `regression` objective with `[+1,-1]` feature
monotonicity, deterministic CPU mode, forced column histograms and bounded worker
counts. Monotonic constraints are not compatible with LightGBM's `regression_l1`
objective. Tree monotonicity alone cannot guarantee a concave irradiance response.
Training and prediction thread limits are both explicit to prevent nested fleet
parallelism from oversubscribing the machine.

[LightGBM parameters](https://lightgbm.readthedocs.io/en/stable/Parameters.html)
document the underlying constraints and deterministic-mode limitations across
different versions/platforms.

## Typical Daily Profiles

`analyze_tdp` receives `site_id`, timezone-aware `timestamp`, and a configured value
column (default `actual_mwh`). By default a useful day has 24 finite nonnegative
hourly observations and a year-month needs at least 15 useful days. Each reported
quantile needs at least ten observations. These project conventions are explicit
configuration, not implied publication constants. The Chile workflow uses fixed
UTC−04; the core default is UTC. Fixed-clock TDPs and civil-time DST reporting
must remain distinct.

Positive flat generation days are excluded only when complete solar elevation
is available and at least four observed daylight hours cover 75% of expected
daylight hours. Values must agree within the configured tolerance and at least
one must be positive. Reported zero days are retained, including zero-only sites.
Without solar elevation the flat-day screen is marked unavailable. Weather
profiles should disable the positive-flat screen; ambient temperature should
also set `nonnegative=False`.

Year-month qualification happens **before** AVG pooling. AVG combines original
hourly observations from eligible year-months; it does not average annual
percentiles. Raw profiles retain all physically valid observed values before
these day/month gates. Every hour retains its own observation count.

The paper's historical net-capacity normalized-yield and net-PR gates require
independently verified capacity effective dates and supported historical POA.
This implementation does not infer those from undated registry MW or substitute
DC capacity. The output explicitly reports that limitation. The earlier DC-PR
training gate and acceptance band are separate from TDP input qualification.

## Operating-state evidence

The ten states preserve the recovered ASVA decision order: missing generation,
invalid generation, night without generation, low resource without generation,
generation at low resource, no generation with adequate resource, reference
unavailable, below reference, within tolerance and above reference. Missing
resource inputs remain unavailable, even when output is zero.

Resource-present trace output is identified before model-support gates. Positive
output comparisons require the matching stage's training-weather support and
accepted-training Q95 (including accepted zeros). The envelope is
`expected ± max(20%*expected, 5%*training_Q95)`, with an expected-output floor of
5% Q95. These are engineering thresholds, not IEC thresholds or calibrated
prediction intervals. Band-inside plus below/above-model output is not, by itself,
the recovered asymmetric model/band disagreement flag.

Persistence requires at least two consecutive elapsed hours with the **same**
no-generation-with-resource or below-reference state. Timestamp gaps and changes
between those states break a run. These runs do not establish verified outage
duration. Solar elevation outside physical ±90° is treated as unavailable.

The information category remains **Information unavailable (§5.18)**; causes and
capability are unconfirmed. Positive hourly energy only establishes generation
during some part of that interval. No dispatch/curtailment, equipment fault,
maintenance, storm-damage diagnosis or IEC availability percentage is inferred.
See the [IEC TS 63019:2019 scope](https://webstore.iec.ch/en/publication/27253).

## Verification and performance

```bash
uv run ruff check methods
uv run ty check methods
uv run pytest methods/tests
uv run python methods/benchmarks/benchmark_poa.py --hours 2160
```

Tests cover physical shape constraints, training/test isolation, POA horizontal
closure, exact lag edges, band support, PR units/boundaries, all ten statuses,
state precedence, timestamp-gap persistence, TDP pooling, missingness and zero
retention, and LightGBM determinism/portable inference. Benchmark inputs are
synthetic and labelled; its measured timing is machine-specific.

## Climate classification and mapping

`energy_methods.kgpv` implements the KGPV temperature/precipitation rules,
fixed irradiation thresholds and published 24-to-12 zone merging.
`energy_methods.climatology` builds monthly climatologies from bounded batches.
`energy_methods.mapping` provides coordinate normalization, explicit regridding,
cell areas, class summaries and bounded GeoJSON export.
Run `energy-kgpv --help`; see [the complete workflow and assumptions](../docs/kgpv.md).
The primary thesis citation and the specific 2019 KGPV paper are both retained.

## Soiling and snow risk mapping

`country_boundaries` selects and exports country shapefiles/GeoJSON;
`country_mapping` builds finer regional grids, masks by polygons, plots clipped
maps and exports clipped cells. These helpers also work with KGPV and degradation.
See [country selection, CRS handling and examples](../docs/country-mapping.md).

`energy_methods.weather_risk` implements thesis Eqs. 3.2–3.4 and the five
classes in Tables 6.6–6.7. `weather_risk_mapping` validates complete-year AOD550
and physical ground snow-depth inputs and maps the resulting indicators.
See [equations, units and conventions](../docs/soiling-snow.md) and the offline
worldwide gallery example. Soiling rate is in %/day; snow energy loss is in %/year.
These are empirical screening indicators, with explicit missingness and
threshold boundaries, rather than independently validated site losses.

## Climate degradation mapping

`energy_methods.degradation` implements the thesis's hydrolysis,
photo-degradation, thermomechanical and combined-rate equations, with an explicit
module calibration. `degradation_mapping` processes annual stresses, classifies
total rates in 0.2%/year bins and summarizes mapped mechanisms by KGPV zone.
Run `energy-degradation --help`; see [inputs, scientific assumptions and the
synthetic example](../docs/degradation.md). The thesis remains the primary
citation alongside the Kaaya model and the 2019 degradation mapping paper.

`energy_methods.degradation_weather` supplies the published GHI-Faiman temperature
and Wald UVA/UVB transformations used by the [applied map analysis](../analysis/src/energy_analysis/degradation/README.md).
