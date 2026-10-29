# Climate Change Yield Assessment (CCYA)

CCYA estimates how a PV system's specific DC yield changes under supplied
climate projections, separating irradiance, temperature and power degradation.
The implementation is `energy_methods.ccya` in the reusable `methods` package.
It fits historical monthly observations to a climate model and projects future
months for **one site, climate model, ensemble member and scenario at a time**.
It makes no network requests and requires no new dependencies.

## Scientific source and implementation boundary

Primary source: **Julián Andrés Ascencio Vásquez (2021), _Modelling and worldwide
assessment of performance and aging of photovoltaic modules and systems_,
University of Ljubljana**, Chapter 7, sections 7.5.1-7.5.3, printed pp. 150-164.
The CCYA definition is on p. 156, Figure 7.10. Its Bolzano application is on
pp. 157-164. Thermal expressions appear in equations 3.6 and 3.8, p. 52.

- [Institutional record](https://repozitorij.uni-lj.si/IzpisGradiva.php?id=131079&lang=eng)
- [Full thesis PDF](https://repozitorij.uni-lj.si/Dokument.php?id=148326&lang=eng)
- [Permanent national-library citation](https://www.dlib.si/details/URN:NBN:SI:DOC-TMG3QFI9)
- PDF retrieved 2026-10-29; SHA-256:
  `9ab0f6ecaecda9880b75ea68ead2184f0a1dcff630064d966f1a4f93e28dd2ec`.
  Printed page 156 is PDF page 204. The source PDF is not redistributed here.

The thesis cites a CCYA manuscript as **to be submitted**, bibliography [8].
This implementation cites the thesis; it does not invent a published CCYA
article or DOI. The Ross temperature relation is also credited through
Skoplaki and Palyvos (2009), thesis reference [154]. Polo et al. (2020), thesis
reference [287], is credited as background for site adaptation, without claiming
to reproduce all techniques benchmarked in that paper. See the
[reference catalogue](references.md) and the module's `REFERENCE_IDS`.

This is a documented implementation of the CCYA workflow, **not a numerical
reproduction of the Bolzano results**. Original author code, plant measurements,
selected climate files and all fitting settings were not supplied. The thesis
does not fully specify the seasonal fitting rule, percentile convention,
temperature normalization or rolling-window alignment. The choices below are
part of this implementation and must be retained when reporting results.

| Thesis element | Implementation |
| --- | --- |
| Section 7.5.1: linear site adaptation | Ordinary least squares `measured = slope * modelled + intercept` on the explicitly supplied monthly overlap, separately for GHI and ambient temperature. |
| Figure 7.13: monthly centers of modelled GHI and measured mean daily DC yield | Twelve through-origin proportional responses, one for each calendar month, passing through that month's centroid. This fitting rule is an explicit project choice. |
| Figures 7.14-7.15: annual yield and 10-year mean | Sum native-calendar monthly yields; trailing 10 **complete** years, including the reported year. Shorter windows stay missing. |
| Equation 7.1: rolling change relative to measured long-term mean | `100 * (rolling annual mean / mean measured annual yield - 1)`. This generalizes the solar-resource expression to DC yield. |
| Equations 7.2-7.4: cumulative comparisons | Sum annual projected yield and divide by `historical annual baseline * operating-year count`. Export both ratio (%) and signed gain/loss (%). |
| Equations 3.6, 3.8; Figure 7.17 | Ross module temperature with GHI, then an **incremental** multiplier relative to the historical calendar-month temperature. Defaults: gamma = -0.0045 /°C, Ross = 0.03 °C m²/W. |
| Figure 7.19: power retention | Linear degradation sampled at the start of each operating year; year 1 has age zero by default. Explicit aligned monthly factors support nonlinear paths. Rates are supplied, not inferred. |

## Input contract

Pass pandas DataFrames with a **monthly `PeriodIndex(freq="M")`**. The index is
a year/month label, not a UTC timestamp. Every table must contain consecutive,
complete January-December years, in order, with unique months and finite values.
Measured and historical-climate tables must cover the exact same selected years.
The default minimum calibration is two years; that is an execution guard, **not
a claim that two years suffice for a reliable climate or financial assessment**.
Use longer qualified records and chronological holdout evaluation in real studies.

| Column | Required in | Definition |
| --- | --- | --- |
| `ghi_wm2` | All tables | Monthly time-weighted **all-hours** mean GHI in W/m², including nights. Not daylight-only GHI, POA, or irradiation in kWh/m². |
| `temperature_c` | All tables | Monthly time-weighted mean ambient temperature in °C. Convert CMIP6 `tas` from kelvin before use. |
| `days` | All tables | Actual integer days in each native-calendar month. Gregorian, noleap, all_leap and 360_day year patterns are supported explicitly. |
| `dc_yield_kwh_kwp` | Measured only | Monthly **total DC** energy divided by qualified DC STC capacity, in kWh/kWp. Not mean daily yield, AC output, or energy in MWh. |

For regular interval inputs, integrate power over actual elapsed interval hours
to obtain energy, and use time-weighted means for weather. Check complete
interval coverage **before** monthly aggregation: a monthly sum from a partial
month is not a qualified monthly total. This API cannot detect missing hours
hidden inside a caller's finite aggregate. It does not fill gaps or scale partial
months to full months. Valid zero-yield months remain zero. Zero annual measured
yield and zero model-GHI monthly centroids are rejected because normalization is
undefined.

The existing station connectors can supply measured weather; actual DC energy
must come from qualified plant measurements. The existing CMIP6 connector
retrieves native files and provenance. **This PR does not add a NetCDF parser,
spatial interpolation, automatic station selection or hourly disaggregation.**
Reduce native model calendars to year/month labels and keep their `days`
explicitly. Never coerce a 360_day model into Gregorian timestamps.

Use the same climate model, member, variable definitions, grid/location and
preprocessing for historical calibration and its future scenario. Keep each
model/member separate, and preserve acquired dataset identifiers, versions,
coordinates, hashes, calendar and source citations alongside `model.to_dict()`.
The method cannot verify provider lineage from a numeric table.

## Calculations and conventions

For calendar month `m`, calculate a mean daily yield from each measured month's
total divided by **its measured-calendar** days. With bars denoting the average
across calibration years, the invariant response is:

```text
c[m] = mean(measured monthly DC yield / measured days)[m]
       / mean(raw historical model GHI)[m]
Y_irr[t] = c[month(t)] * raw scenario GHI[t] * scenario days[t]
```

This captures the plant's seasonal response while retaining climate-model GHI
variability. The raw model GHI is intentionally used here: its baseline bias is
already absorbed in `c`. Applying GHI site adaptation again to this yield
response would correct that bias twice. The separate GHI adaptation supplies
the Ross temperature model instead.

```text
G_site[t] = a_G * G_model[t] + b_G
T_site[t] = a_T * T_model[t] + b_T
T_module[t] = T_site[t] + ross * G_site[t]
T_reference[m] = mean(measured ambient T)[m] + ross * mean(measured GHI)[m]
f_temperature[t] = 1 + gamma * (T_module[t] - T_reference[month(t)])
f_power[t] = 1 - degradation_per_year * (age_at_start_years + operating_year[t] - 1)
```

The temperature multiplier is an incremental, first-order adaptation: the
measured yield calibration already includes historical thermal losses. It is
not an additional absolute STC loss, nor a claimed exact reproduction of the
unpublished normalization behind Figure 7.17. Unchanged reference weather gives
a multiplier of one. Monthly averages and GHI reproduce the chapter's coarse
approach; this is not an irradiance-weighted hourly module-temperature model.

An existing plant's historical aging and operating losses remain embedded in
its measured yield. Supply an explicitly justified `age_at_start_years` **relative
to the calibrated yield reference**, or a relative power-retention curve, to avoid
applying losses already present in the baseline twice. There is no automatic
weather-driven acceleration of degradation, replacement policy or rejuvenation.

Four outputs keep independent and combined effects distinguishable:

| Output | Monthly specific DC yield |
| --- | --- |
| `irradiance_kwh_kwp` | `Y_irr` |
| `irradiance_temperature_kwh_kwp` | `Y_irr * f_temperature` |
| `irradiance_power_kwh_kwp` | `Y_irr * f_power` |
| `combined_kwh_kwp` | `Y_irr * f_temperature * f_power` |

The printed equations 7.2-7.4 omit a clear `-1` for signed gain/loss and put an
integral together with a year count in the denominator. The surrounding text
describes total energy compared with an annual P-value times years, and the
figures show zero-centered signed percentages. Therefore this implementation
exports **both** `100 * cumulative_yield / (annual_baseline * years)` and
`100 * (cumulative_yield / (annual_baseline * years) - 1)`. The denominator is
not multiplied by years twice. A constant baseline yields 100% ratio and 0% gain.

P10/P50/P90 are **empirical nonexceedance** quantiles (Q0.10/Q0.50/Q0.90,
linear interpolation) of complete measured annual DC yields. This choice agrees
with the ordering of the thesis's comparisons; it is explicitly **not** the
finance convention in which P90 is a low energy yield exceeded 90% of the time.
These quantiles describe historical interannual variation only. They do not
combine model spread, scenario likelihood, regression uncertainty or outages,
and are not bankable P90 guarantees. Different SSPs are never pooled or assigned
probabilities.

The method allows future climate outside historical support, flags it by month
and counts flagged months per year. The GHI check uses calendar-month bounds;
temperature uses the overall adaptation range. These are diagnostic ranges, not
proof of future accuracy. Negative adapted irradiance, nonpositive thermal
multipliers, invalid power retention and incomplete inputs raise errors instead
of being silently clipped or replaced. There are no random seeds because all
calculations are deterministic.

## Usage

```python
from energy_methods.ccya import fit_ccya

# Tables follow the schema above; select the calibration overlap explicitly.
model = fit_ccya(measured_monthly, historical_model_monthly)
result = model.project(
    future_model_monthly,
    scenario="model/member/ssp245/grid/version",
    degradation_per_year=0.005,  # 0.5%/year, not 0.5
)
monthly = result.monthly
annual = result.annual
provenance = result.metadata  # Includes the fitted model and REFERENCE_IDS.
```

For a nonlinear path, pass `power_factors=pd.Series(...)` with exactly the
projection's monthly index and values in `[0, 1]`; leave the linear rate and age
at zero. For a scenario ensemble, call `project` separately for each scenario
and each member. Use the matching fitted historical model for each member.

Run the deterministic synthetic example, which prints model provenance and
25/50-year comparisons for two artificial climate paths and the four degradation
rates illustrated in the thesis:

```bash
uv run --no-sync python methods/examples/ccya_synthetic.py
uv run --no-sync pytest methods/tests/test_ccya.py
```

The example makes no real-site or real-SSP claim and downloads no data. Tests
independently check affine bias correction, a known warming response,
irradiance-induced Ross heating, constant-baseline identity, cumulative linear
degradation, nonlinear power factors, percentile direction, complete rolling
windows, calendar handling and invalid-input rejection.
