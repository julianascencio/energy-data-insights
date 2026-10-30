# Soiling and snow risk maps

`energy_methods.weather_risk` implements the empirical indicators in
**Ascencio Vásquez (2021), thesis §§3.1.1–3.1.2 and §§6.5.2–6.5.3**.
`energy_methods.weather_risk_mapping` applies them to labelled grids and assigns
the five risk levels in Tables 6.6–6.7. The
[worldwide gallery example](https://julianascencio.github.io/energy-data-insights/auto_examples/plot_soiling_snow_risk.html)
uses real, attributed 2023 inputs and runs offline.

These categories describe empirical soiling-rate and snow-shading indicators.
They are not event probabilities, structural snow loads or independently
validated estimates of site losses. The thesis is the primary reference;
the original soiling study, snow report and data products are cited separately
in the [bibliography](references.md).

## Equations and units

### Soiling: thesis Eq. 3.2, printed page 49

Let $A$ be **annual-mean total aerosol optical depth at 550 nm**, dimensionless.
The daily soiling-rate indicator, in numerical **%/day**, is

$$
SR(A) =
\begin{cases}
0.648 A, & 0 \leq A \leq 0.106,\\
6.63 A - 0.63, & A > 0.106.
\end{cases}
$$

The underlying Cordero et al. (2018) correlation relates annual averages from
Chilean sites. Applying it to daily dust events or a different aerosol type
does not inherit that validation. The repository computes the annual mean
**before** applying the equation. It does not add rain/manual cleaning or
multiply the daily rate by 365 to estimate annual energy loss.

The printed strict inequalities leave zero and 0.106 unspecified. The
implementation assigns both to the lower branch and preserves the small
published discontinuity instead of smoothing it.

### Snow: thesis Eqs. 3.3–3.4, printed pages 50–51

For each complete year, sum **hourly physical ground snow depth in centimetres**:

$$
SD_y = \sum_{t\in y} d_t\,(1\ \mathrm{h}), \qquad
x = \ln\left(\frac{SD_y}{1\ \mathrm{cm\,h}}\right).
$$

The numerical sum follows the centimetre convention on the x-axis of thesis
Figure 3.4. Using metres without conversion changes the logarithm and loss.
The annual snow energy-loss indicator, in numerical **percent**, is

$$
SL =
\begin{cases}
0, & SD_y \leq 1\ \mathrm{cm\,h},\\
0.0263 x, & 0 < x \leq 5,\\
0.25x^2 - 2.41x + 6, & x > 5.
\end{cases}
$$

The zero result for exposure at or below 1 cm h and lower-branch ownership at
$x=5$ are explicit repository extensions of the unspecified printed boundaries.
The branch discontinuity is retained. The polynomial is not clipped at 100%;
implausible extrapolations remain visible and require review.

This is the **thesis's fit**, adapted from Ryberg & Freeman (2017), for fixed
modules at a tilt equal to latitude. It does not run the full SAM snow model or
resolve mounting height, snow sliding, tracking or site-specific clearing.

**Snow depth is not snowfall or snow water equivalent.** Native
[ERA5 parameter `sd`](https://codes.ecmwf.int/grib/param-db/?id=141) is in metres
of water equivalent. Multiplying it by 100 does not produce the physical-depth
input required here; conversion requires appropriate snow-density/cover
information and documented semantics. The supplied adapter instead requests
Open-Meteo's explicitly defined physical `snow_depth` for **ERA5-Land**, in
metres, and converts that to centimetres.

## Five risk levels

The following closes the omitted equalities in thesis Tables 6.7 and 6.6 by
making every upper threshold inclusive. Class 0 is unavailable data, separate
from Very Low. In particular, snow class 1 includes small nonzero losses.

| Class | Label | Soiling rate (%/day), Table 6.7 | Annual snow loss (%), Table 6.6 |
| --- | --- | --- | --- |
| 1 | Very Low | 0 ≤ SR ≤ 0.05 | 0 ≤ SL ≤ 2 |
| 2 | Low | 0.05 < SR ≤ 0.10 | 2 < SL ≤ 4 |
| 3 | Medium | 0.10 < SR ≤ 0.20 | 4 < SL ≤ 7 |
| 4 | High | 0.20 < SR ≤ 0.40 | 7 < SL ≤ 10 |
| 5 | Very High | SR > 0.40 | SL > 10 |

## Array and map interfaces

```python
from energy_methods.weather_risk import (
    snow_loss_from_exposure,
    snow_risk_classes,
    soiling_rate_from_aod,
    soiling_risk_classes,
)

rate = soiling_rate_from_aod([0.05, 0.20])  # [0.0324, 0.696] %/day
soiling_class = soiling_risk_classes(rate)  # [1, 5]
loss = snow_loss_from_exposure([0, 22026.465794806718])  # [0, 6.9] %
snow_class = snow_risk_classes(loss)  # [1, 3]
```

`annual_risk_inputs(daily_aod550, hourly_snow_depth, year=2023)` requires
`xarray.DataArray` inputs on `(time, lat, lon)` with these attributes:

| Input | Required attributes | Time axis |
| --- | --- | --- |
| Daily AOD550 | `units="1"`, `wavelength_nm=550`, `time_zone="UTC"` | Every daily UTC date in the year |
| Hourly ground snow | `units="cm"`, `snow_depth_kind="physical_ground"`, `time_zone="UTC"` | Every UTC hour in the year |

Use timezone-naive `datetime64` labels representing UTC, with the explicit
attribute above. Leap years need 366 days and 8,784 hours. Missing timestamps,
duplicate/reversed dates, incompatible grids, infinities and negative inputs
raise errors. NaN values mask only the affected indicator/cell/year. Valid-day
and valid-hour counts are retained; there is no partial-year annualization.

`map_weather_risks(annual_inputs)` consumes `aod550_mean` and `snow_depth_sum`
on `(year, lat, lon)`, with the units/physical-depth metadata above (`cm h` for
the annual snow sum). Years must be consecutive and increasing. Apply equations
**to each year**, average the annual rates/losses, then classify the means.
This nonlinear multi-year aggregation is an explicit repository convention;
the thesis does not specify every global-map processing detail. Missing years
or values are not silently dropped. The result retains each annual estimate,
mean indicators, classes, bin metadata and scientific reference IDs.

Normalize/regrid continuous input fields before classification, using
`energy_methods.mapping` if necessary. The caller must supply an ocean mask;
these methods do not infer land from zero snow. The gallery demonstrates
NetCDF, GeoJSON and area-weighted class summaries using the existing mapping
utilities.

## Reproduce the real-data example

The checked-in CSV contains **2023** annual inputs at **15° worldwide cell
centres**, with a coarse land mask inherited from the reviewed NOAA KGPV
fixture. It samples source cells rather than averaging all weather within
each 15° square. Small islands/coastlines are not resolved. The acquisition
manifest records every public request, response checksum, access time,
source-grid coordinates where supplied, input units and preprocessing.

| Input | Actual example source | Difference from the thesis |
| --- | --- | --- |
| AOD550 | NASA POWER `AOD_55`, unadjusted total AOD; CERES SYN1deg/MATCH, daily UTC | Alternative to the ECMWF/CAMS aerosol inputs |
| Physical ground snow | Open-Meteo, explicit `era5_land`, hourly `snow_depth` in m | ERA5-Land wrapper, not native ERA5 water-equivalent `sd` |
| Land mask | NOAA PSL NCEP/NCAR mask from the existing KGPV fixture | Coarse nearest-sampled illustration |

To refresh the inputs from the repository root (network required):

```bash
uv sync --locked --all-packages --group docs
uv run python scripts/prepare_weather_risk_example.py --year 2023
```

Use `--use-environment-proxy` only when your environment requires its configured
HTTPS proxy. Public responses are cached under ignored `artifacts/`. Requests
are paced and use two bounded workers. Provider usage limits still apply;
do not use the public wrapper for an unrestricted high-resolution global run.
`--region europe --output artifacts/europe-risk` prepares a smaller 5° example
for Europe. Place the downloaded gallery script alongside those output files
to plot it. The default gallery build only reads the checked-in fixtures.

For a climatological assessment, acquire and validate multiple complete years,
keep source/model vintages consistent, concatenate annual inputs on `year`,
and use the documented aggregation. A single year must remain labelled as
such. NASA POWER's [aerosol source documentation](https://power.larc.nasa.gov/docs/methodology/data/sources_clds_aerosols/)
and Open-Meteo's [historical API](https://open-meteo.com/en/docs/historical-weather-api)
define their variables and limitations. Open-Meteo warns that snow depth can
be overestimated. Aerosol composition, source resolution, snow-depth bias and
local conditions can all affect these empirical indicators.

Credit NASA POWER/CERES, Open-Meteo (CC BY 4.0), Copernicus/ERA5-Land,
Muñoz-Sabater et al. (2021) and NOAA PSL for the example data, in addition to
the thesis and method references. The derived example is this repository's
illustration and has not been independently validated against field losses.
