# Climate degradation mapping

The **2021 doctoral thesis by Julián Andrés Ascencio Vásquez** is the primary
scientific reference: Section 3.4.3, equations 3.14–3.17, and Section 6.4,
Figures 6.7–6.9 ([institutional full text](https://repozitorij.uni-lj.si/Dokument.php?id=148326&lang=eng)).
The original mechanism equations are credited to
[Kaaya et al. (2019)](https://doi.org/10.1109/JPHOTOV.2019.2916197), and their global
mapping to [Ascencio-Vásquez et al. (2019)](https://doi.org/10.3390/en12244749).
Full bibliographic records are in [references.md](references.md).

`energy_methods.degradation` implements hydrolysis, photo-degradation,
thermomechanical degradation and the combined rate. `degradation_mapping`
processes annual stresses and returns geographic layers, rate categories and
optional area-weighted summaries by KGPV zone. Data providers remain in
`data-retrieval`; these methods accept prepared weather or annual stress grids.

## Scientific contract

With module temperature in kelvin **inside the exponential terms**, the equations are:

```text
k_H  = A_H * RH**n * exp(-E_H / (k_B * T_mean))
k_P  = A_P * UV_dose**X * (1 + RH**n) * exp(-E_P / (k_B * T_mean))
k_Tm = A_Tm * (T_upper - T_lower)**theta * C_N * exp(-E_Tm / (k_B * T_upper))
k_T  = A_N * (1 + k_H) * (1 + k_P) * (1 + k_Tm) - 1
```

The publication's `k_B = 8.62e-5 eV/K` is retained. A temperature **difference**
does not receive a 273.15 offset. The subtraction in the total stays outside
`A_N`, exactly as printed. Mechanisms are not added and their shares need not
sum to the total. All rates follow the mapping paper's numerical **%/year**
convention: `0.5` means `0.5%/year`, not `50%/year`. The multiplicative equation
is calibration-dependent; rescaling its component rates changes the model.
`log1p`/`expm1` evaluate the combined expression without losing tiny rates.

Every call requires `DegradationParameters`: `a_h`, `a_p`, `a_tm`, `e_h`, `e_p`,
`e_tm`, `n`, `x`, `theta`, `a_n`, `calibration_id`, and `calibration_source`.
No default calibration is provided. Fit prefactors and normalization consistently
with the documented units and stress processing for the intended module.
Activation energies are in eV. Prefactors and energies must be nonnegative;
exponents and normalization must be positive. A calibration yielding a negative
total or overflow raises instead of producing a clipped, plausible-looking map.

The thesis's Table 4.6 is a **different calibration**, fitted to a polycrystalline
module in Ljubljana for the uncertainty study. It must not silently become the
monocrystalline module calibration used in Chapter 6. The mapping chapter does
not provide a complete executable calibration and stress-processing specification.
This PR implements the equations and mapping workflow; it does not claim an
exact reproduction of the original 2016–2018 rasters. The committed example
uses explicitly synthetic coefficients, not that table or a generic c-Si model.

These outputs are module-specific **climate degradation indicators**, not measured
performance loss rates, warranted service life or a diagnosis of failure modes.
As in Section 6.4, LID, LeTID, PID, wind/snow mechanical damage, soiling and snow
cover losses are outside this model. It does not infer a power-versus-age curve.

## Input grids and processing

`map_degradation` consumes an xarray Dataset with each field on `(year, lat, lon)`:

| Variable | Required `units` attribute | Meaning |
| --- | --- | --- |
| `module_temperature_mean_c` | `degC` | Representative annual mean module temperature |
| `module_temperature_upper_c` | `degC` | Annual upper temperature under the selected convention |
| `module_temperature_lower_c` | `degC` | Annual lower temperature under the selected convention |
| `relative_humidity_percent` | `%` | RH in 0–100, with effective/ambient interpretation documented |
| `uv_dose_kwh_m2` | `kWh m-2 year-1` | Annual integrated UV dose, not irradiance |
| `cycles_per_year` | `year-1` | Explicit thermal cycling frequency, not inferred from sample count |

`year` contains sorted, unique, consecutive integers. The dataset must have a
nonempty `stress_convention` attribute describing temperature limits, humidity
processing and UV band; add `source` for provenance. Lower/mean/upper temperatures
must be ordered and above absolute zero. UV and cycle frequency may be zero.
A missing stress masks all outputs for that cell-year, and every year must be
complete at a mapped cell. `valid_year_count` records joint annual coverage.
NaN is never converted to dry weather, no UV, or zero degradation.

Latitude and longitude must be one-dimensional geographic coordinates. They are
sorted, with longitude normalized to `[-180, 180)`. Duplicate cyclic seams fail.
No land mask is guessed: ocean and other excluded locations must be masked in
the inputs. Spatial interpolation is never implicit. If needed, use the existing
`mapping.regrid` on continuous stresses **before** applying the nonlinear model.

The mandatory `aggregation` argument makes two distinct calculations explicit:

- `mean_stress`: equal-year average of the annual stresses, then one evaluation
  of the degradation model; consistent with the climate-average mapping workflow.
- `mean_rate`: evaluate each year's stresses and average the rates; a separate
  sensitivity scenario, not interchangeable with evaluating mean stresses.

The optional `annual_stresses(weather, year=..., cycles_per_year=...)` helper
accepts one complete UTC calendar year of hourly **interval-start labels** with
`module_temperature_c` (`degC`), `relative_humidity_percent` (`%`) and
`uv_irradiance_w_m2` (`W m-2`) on `(time, lat, lon)`. Time must be datetime64 UTC,
encoded without a timezone offset, and dataset `time_zone` must be `UTC`.
It computes the arithmetic annual module temperature and RH means, the annual
means of daily temperature maxima/minima, and the sum of hourly UV divided by
1000. Leap years have 8784 hours. Any missing hourly input masks the whole
cell-year; `valid_hour_count` is retained. Missing/duplicate timestamps, incomplete
years, wrong units and infinities fail.

**Those daily extrema and arithmetic ambient RH are documented repository
choices**, not a reconstruction of effective module humidity or unspecified
published temperature bins. Use prepared annual grids for other calibrations.
Supply cycle frequency explicitly; one cycle per day is an assumption to assess,
not a property established by these data. Process hourly weather in spatial tiles
and one year at a time. The map command loads annual grids, not global hourly data.

ERA5 ambient air temperature is not module temperature. ERA5 accumulated solar
energy in J/m² is not W/m². Native ERA5 UV extends to 440 nm, while the mapping
study models UV below 400 nm; do not pass it unchanged. Appropriate upstream
module-temperature, dewpoint/RH and 280–400 nm UV processing is required.
GPCC/CRU TS monthly inputs alone do not supply these degradation stresses.

## Reproducible example and CLI

Run from the repository root. This creates only a small **synthetic** regional
fixture; it downloads nothing and makes no scientific forecast:

```bash
uv sync --locked --all-packages
uv run python methods/examples/degradation_mapping.py \
  --output artifacts/degradation-input
uv run energy-degradation \
  --stresses artifacts/degradation-input/annual_stresses.nc \
  --parameters artifacts/degradation-input/parameters.json \
  --aggregation mean_stress --region global --geojson \
  --output artifacts/degradation-map
```

Use the same command with your calibrated parameter JSON and prepared annual
files. Multiple `--stresses` files must have identical grids and the same stress
convention. Years are sorted, then checked for duplicates and gaps. Optional
`--kgpv /path/to/kgpv.nc` summarizes all four rates by the existing twelve KGPV
zones. The class grid must align exactly; use nearest-neighbour explicitly if
it needs regridding. Different KGPV and degradation baselines can be compared,
but their metadata remain separate. The summary covers the valid intersection,
uses spherical cell areas, and returns NaN means and zero covered area for an
empty zone. It is not a capacity-weighted PV fleet degradation estimate.

Outputs:

- `degradation.nc`: four continuous rates, `rate_class`, `valid_year_count`,
  baseline, full calibration, processing assumptions and reference IDs.
- `manifest.json`: input SHA-256 hashes (including calibration/KGPV), full
  bibliography with the thesis first, parameters and class areas in km².
- `degradation_by_kgpv.nc` when requested: weighted means, valid cell counts and
  valid area for every KGPV zone, plus both layers' metadata.
- Five GeoJSON files with `--geojson`: four continuous layers and the classified
  total. Each is limited to 100,000 polygons. Exports and area summaries require
  at least two regularly spaced centres per axis. Use NetCDF for global layers.

Thesis Section 6.4 uses 0.2%/year categories. `--region global` has upper edges
0.2, 0.4, 0.6, 0.8, 1.0, 1.2 and 1.4; `europe` ends at 0.8. An overflow class
retains higher values. Upper edges are inclusive, an explicit edge-ownership
convention. ID 0 is missing; ID 1 includes true zero. The region switch selects
the **bin scheme** and does not crop the geographic grid. Class labels and edge
metadata are retained in NetCDF and GeoJSON.

## Verification

Offline tests use analytically selected Arrhenius factors, non-unit normalization,
percent-versus-fraction checks, temperature differences, zero/tiny rates, missing
inputs, invalid calibrations and overflow. They also cover leap-year integration,
complete-hour coverage, both aggregation orders, map categories and edges,
latitude-dependent area weights, exact grid alignment and a CLI NetCDF/GeoJSON
round trip with provenance. Synthetic tests establish implementation behavior;
they are not validation against field observations or the published global maps.
