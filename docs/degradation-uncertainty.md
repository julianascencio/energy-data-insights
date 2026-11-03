# PV degradation uncertainty and lifetime

Implements the methodology in **Kaaya, Ascencio-Vásquez, Weiss and Topič (2021),
Assessment of uncertainties and variations in PV modules degradation rates and
lifetime predictions using physical models**, *Solar Energy* 218, 354–367,
[DOI: 10.1016/j.solener.2021.01.071](https://doi.org/10.1016/j.solener.2021.01.071).
The supplied paper is the source; its original field time series are unavailable.

The implementation separates reusable methods from an offline analysis and
[executable gallery example](../examples/analysis/plot_degradation_uncertainty.py).
It does not replace the existing [2019 climate degradation mapping](degradation.md).

## Method and input contracts

| Module | Paper coverage | Inputs and outputs |
| --- | --- | --- |
| `energy_methods.pv_reliability` | Table 2, Eqs. 19–20 | Four power-versus-age curves, analytic threshold crossing, curve fitting, NRMSE and symmetric relative difference |
| `energy_methods.degradation_uncertainty` | Eqs. 1, 3–6 | Daily stress-product rate and combined hydrolysis/photo/thermal rates, explicit native-to-fractional/year scale |
| `energy_methods.pv_stress_weather` | Eqs. 7–17 | Ross/Faiman temperature and fitting; linear, original/modified Wald and air-mass polynomial UV; Buck RH |
| `energy_methods.degradation_preprocessing` | Sections 2.5 and 3.4 | Power screening/normalization and complete-year hourly weather to annual stresses |
| `energy_analysis.degradation_uncertainty` | Tables 3–6, 8, 10–11 | Rounded-table checks, one-at-a-time climate scenarios, synthetic calibration and weather-model comparisons |

Models accept prepared inputs; acquisition stays in `data-retrieval`. Use the
existing ERA5/PVGIS connectors as appropriate, retaining native measurement
height, spectral band, POA geometry, units, source dates and quality flags.
Do not substitute ambient temperature for module temperature, GHI for POA, or
annual UV dose for daily irradiance. ERA5 UV through 440 nm is not the study's
280–400 nm UV band. No new remote connector is needed for this implementation.

## Reliability and coefficient units

With age `t` in years and power normalized to initial power:

| API kind | Normalized power | Time to retained fraction `q` |
| --- | --- | --- |
| `linear` | `1 - k*t` | `(1-q)/k` |
| `exponential` | `exp(-k*t)` | `-ln(q)/k` |
| `stretched_exponential` | `exp(-k*t**beta)` | `(-ln(q)/k)**(1/beta)` |
| `wear_out` | `1-exp(-(gamma/(k*t))**mu)` | `gamma/(k*(-ln(1-q))**(1/mu))` |

`k` is fractional, not a numerical percentage: Table 3's 0.83 is entered as
0.0083. Stretched-exponential `k` has units `year**(-beta)`, despite the paper's
common percent/year label. Comparing the four coefficients as if they were
identical annual loss rates is misleading. Report the complete curve and shape.
Threshold crossing is a deterministic extrapolation, not a survival distribution,
confidence interval, field-validated service life or warranty.

At age zero, all curves return one. Zero rate gives infinite threshold time.
Linear curves are not clipped after zero power. `fit_reliability` fits `k`, and
`beta` or `mu` where appropriate, using deterministic multistart bounded least
squares. Wear-out `gamma` is fixed by the caller: only `gamma/k` is identifiable,
so fitting both would produce an underdetermined model. The returned Jacobian
condition number exposes poor conditioning; it is not parameter uncertainty.
Shapes are bounded to 0.05–10 and `k` to 1e-10–10 as numerical fitting choices.

```python
from energy_methods.pv_reliability import ReliabilityCurve, fit_reliability

curve = ReliabilityCurve("stretched_exponential", k=0.003, beta=1.59)
print(curve.failure_time(retained_power=0.8))
print(curve.power([0, 5, 10, 20]))
# Supply measured ages and normalized power, after independent quality screening:
# fit = fit_reliability(ages, power, kind="wear_out", gamma=0.43)
```

The rounded published coefficients give approximately **24.1, 26.3, 15.0 and
19.8 years**. Small differences from the printed 24.0, 26.2, 15.1 and 19.7 are
retained, not tuned away. These are checks of published parameter arithmetic;
no original observations have been refitted.

## Physical-rate conventions and unresolved source details

The new combined model preserves the **printed** thermal factor
`(273 + upper_c - lower_c)**theta` in Eq. 6. This differs from the existing 2019
mapping function's `(upper_c - lower_c)**theta`. A temperature difference does
not physically require a kelvin offset. The new function deliberately implements
the printed empirical form without silently declaring it a typographical error.
Both paths share validated Arrhenius/combination algebra; existing API behavior
and tests remain unchanged. Arrhenius temperatures use Celsius + 273.15.

The combination is `A_N * product(1 + k_i) - 1`, with subtraction **outside**
normalization. Mechanism outputs are not additive shares. Table 5 gives nine
coefficients but omits `A_N` and cycling frequency `C_N`; the paper's dimensional
labels also do not fully settle the calibration's numerical rate convention.
The implementation therefore requires all these choices. No generic module
calibration is silently introduced.

`rate_scale_to_year_inverse` is mandatory: 0.01 means the native number has a
percent/year convention, 1 means fractional/year, and a genuine per-second
calibration would require its declared seconds/year conversion. This conversion
is applied **after** the combined expression; rescaling components before the
multiplicative combination changes the model.

The daily stress-product equation uses daily maximum module temperature,
temperature range, daytime UV **irradiance in W/m²**, and mean RH in percent.
Its `beta0` includes calibration-dependent units. The annual dose in Table 6
cannot replace that irradiance. The example exercises both physical equations
with synthetic hourly weather and discloses different aggregation paths and
assumed scales. It does not claim a fair ranking or reproduce Figure 3.
Physical-rate coefficient refitting across sites is not provided: the original
matched performance/weather records and complete calibration conventions are
needed for credible calibration and independent-location validation.

## Weather, filtering and uncertainty

Temperature coefficients are explicit; Faiman wind is supplied at the height
used in calibration, without a hidden height correction. Calibration uses one
year and the synthetic demonstration evaluates on another. UV polynomial
coefficients must be supplied; the code implements prediction, not a new UV
coefficient optimizer. Modified Wald preserves the `a-b*kt` sign convention,
including negative `b` values printed in Table 9. Invalid UV fractions fail
instead of clipping silently. The Buck prefactors are in kPa, despite the
paper's nomenclature saying Pa; the ratio for RH is unchanged. The accepted
Buck domain is -80 to 60 °C; dewpoint above ambient fails.

Power preprocessing keeps 800–1200 W/m² inclusive, scales power to 1000 W/m²,
and applies a mean ± 2 population-SD filter. It does **not** correct temperature
to 25 °C. Monthly means, centered rolling windows (default 12 months), mid-month
age labels and max-trend normalization are documented repository choices where
the paper does not specify an executable configuration. Centering uses future
data: use for retrospective trend analysis, and prepare calibration and holdout
intervals separately. Missing months remain gaps. A UTC age origin is required;
removing early observations does not reset module age. Filters cannot establish
that soiling, snow, outages or sensor changes have been removed.

Annual processing requires an entire UTC hourly calendar year (including leap
day) and finite values. It uses POA>0 daytime temperature/RH means and the 5th/95th
temperature percentiles; UV integrates every hourly interval. Cycling frequency
is independent of the number of hours. This is different from the existing
mapping helper's averages of daily extrema. Multi-year/TMY assessment and
independent module/site validation remain necessary for deployment.

NRMSE follows Eq. 19 using the measured mean, or measured range when the mean
is exactly zero. Negative measured means fail; the all-zero reference is defined
only for an exact match. Eq. 20 uses `100*abs(p-m)/max(abs(p),abs(m))`; a zero/zero
pair is defined as zero. These are error/variation metrics, **not probabilistic
uncertainty intervals**. Inputs must align; missing pairs are not silently dropped.

## Run the reproducible analysis

```bash
uv sync --locked --all-packages
uv run python -m energy_analysis.degradation_uncertainty \
  --output artifacts/degradation-uncertainty
uv run python examples/analysis/plot_degradation_uncertainty.py
```

The study writes six CSVs, two PNGs and a manifest with input/output SHA-256,
source metadata, numerical assumptions and software versions. Published-table
facts, `SCENARIO` outputs and `SYNTHETIC` results are identified separately.
The JSON table fixture is packaged in the wheel, so both commands run offline
outside the checkout after installation. No article PDF or original figures
are redistributed.

The default climate scenario declares `A_N=1`, 365 cycles/year and a 0.01
conversion factor. These are **unvalidated example assumptions**. Temperature,
RH or UV inputs are replaced one at a time; other inputs and curve shape stay
fixed. They do not reproduce the paper's stated 1.7–14.5% variations. The
synthetic weather generator uses Faiman/Wald/Buck, so their low errors are true
by construction, not field evidence for their superiority.

Source inconsistencies stay visible: Negev's UV is 96.7 kWh/m² in Table 6 and
96.9 in Table 10. Each comparison uses its own table's reference. Some printed
relative differences also disagree with Eq. 20 on the rounded inputs: for
Table 10's 96.9 versus 96.5, the implementation returns about 0.413%, not the
printed 0.2%. The raw time series would be required to investigate further.

Validation covers analytic inverse crossings, identifiable calibration recovery,
unit scaling, the two thermal conventions, normalization placement, weather
calibration, source-table checks, leap years, missing intervals, trend gaps and
byte-identical CSV replay. It verifies software behavior, not field prediction
accuracy or all numerical claims in the publication.
