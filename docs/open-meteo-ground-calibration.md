# Open-Meteo ground calibration — Canary Islands

Reusable API: `energy_methods.open_meteo_ground_calibration`.

## Inputs

Use the existing `energy_data_retrieval.sources.open_meteo` historical ERA5
adapter and `energy_data_retrieval.sources.aemet` station observations.
Pair station observations with the **same variable, compatible temporal
aggregation and units**. Preserve station IDs, coordinates, elevations,
model choice, retrieval dates, source hashes, and observation quality flags.
AEMET daily `tmed` is compared with daily (Tmin+Tmax)/2, not a claimed
hourly mean. Do not mix forecast products with historical reanalysis.

## Method

`fit_monthly_bias(pairs, year=2022)` fits 12 station-specific monthly
parameters with at least 20 paired days per month. Temperature and humidity
use additive corrections; wind uses multiplicative correction. Humidity
is bounded to 0–100%. `evaluate_station_holdout(pairs, parameters,
validation_year=2023)` computes held-out daily RMSE and bias for each
month and **reports deteriorations**. No validation-year observations
may be used to fit coefficients.

Use existing `weather_calibration.spatial_weights` and
`weather_calibration.correct_hourly` for supported spatial transfer
and application. Station-to-grid transfer requires independent
leave-one-station-out evaluation; do not label a high-resolution map
as high-resolution meteorological observations.

## Real Canary dataset and gallery

The existing AEMET/Open-Meteo ERA5 capture and island-wide analysis is in
[the Canary study](aemet-era5-canary.md), with runnable
[`plot_aemet_era5_canary.py`](../examples/analysis/plot_aemet_era5_canary.py).
It contains captured daily ground observations and 2022/2023 weather
inputs. The new API adds a standalone, reproducible held-out evaluation
for any station dataset with the required schema.

**Observed result from the existing study:** independent spatial transfer
improved humidity and wind but worsened temperature RMSE. Do not
automatically apply temperature correction to every island.

## Limitations

Ground solar irradiance is **not** calibrated by this implementation:
AEMET stations without a verified radiometer cannot validate GHI.
AEMET daily data also cannot validate hourly extremes or solar irradiance.
Island elevation, trade-wind inversions, coastlines and exposure require
separate representativeness checks. This is weather calibration, not
calibration of PV degradation rates.
