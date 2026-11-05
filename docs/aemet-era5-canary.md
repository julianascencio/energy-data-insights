# Canary Islands: AEMET-adjusted ERA5 degradation-rate maps

The gallery produces continuous, land-clipped raster surfaces for hydrolysis,
photodegradation, thermomechanical degradation and the model's combined rate.
Each mechanism has original, adjusted and difference maps. Station points are
an overlay; they are not the only calculated locations.

## Captured study results

The completed capture contains 54,500 AEMET daily observations from a 77-station
inventory and two full hourly years at 41 requested ERA5 nodes. Seventy-three
stations contribute fitted coefficients: 72 for temperature, 69 for RH and 70
for wind. All 441 land display cells have support for all three variables.

| Modeled mechanism | 2023 range (%/year) |
| --- | ---: |
| Hydrolysis | 0.0066–0.0760 |
| Photodegradation | 0.0205–0.1454 |
| Thermomechanical | 0.0309–0.2139 |
| Combined | 0.0837–0.4316 |

These ranges describe the recorded mono-Si scenario, not measured PV losses.
Spatial and temporal holdout results below average station monthly RMSE:

| Variable | Original ERA5 | AEMET-adjusted |
| --- | ---: | ---: |
| Temperature (°C) | 2.602 | 2.661 |
| Relative humidity (percentage points) | 14.266 | 10.879 |
| Wind speed (m/s) | 2.231 | 1.279 |

**Temperature transfer did not improve this independent spatial evaluation.**
The adjustment improves temporal validation at the measured stations, but that
does not establish accuracy between stations or across mountain/coastal
transitions. Treat the spatial rate maps as provisional modeled scenarios.
The full station-level results, including deteriorations, are downloadable
from the gallery alongside fitted parameters and four-band GeoTIFFs.

## What is calibrated

AEMET OpenData daily measurements from 2022 fit one correction per station,
variable and month. **2023 is withheld** for validation and is the map year.
Temperature uses an additive correction to daily min/max midpoint; humidity
uses an additive correction to daily mean RH; wind uses a ratio of daily means.
At least 20 finite paired days in **every month** are required for a station's
variable to participate. Missing pairs are excluded, never filled from ERA5.
The complete original daily table and provider field metadata are retained.
AEMET date labels are matched to UTC-day model aggregates as an explicit study
convention; undocumented observation-window differences are not resolved.
Consequently the reported evaluation is monthly-mean skill, not hourly skill.

ERA5 is requested explicitly through Open-Meteo with `models=era5`,
`cell_selection=nearest`, `elevation=nan` and UTC. This avoids silently mixing
ERA5-Land, forecast products or provider elevation downscaling. Requested nodes,
provider-selected coordinates, retrieval provenance and input checksums remain
available. The existing connector aligns radiation's preceding-hour means with
averaged instantaneous endpoint temperature, wind and humidity.

For each land display cell, corrections come from the nearest four eligible
stations within 75 km, using inverse squared distance and a 1 km distance floor.
This is a transparent **spatial transfer assumption**, not terrain downscaling.
The display grid is 5 km; ERA5 drivers retain approximately 0.25-degree support.
Fine coastal masks only clip the presentation. They do not create fine weather
information. A cell without support for all three variables stays uncalibrated.

## Validation and limits

`validation.csv` contains two independent-of-fitting checks on 2023:

- Temporal holdout: each station's 2022 correction against its 2023 observations.
- Spatial and temporal holdout: remove the target station entirely from the
  correction field, then compare transferred corrections with its 2023 observations.

Both raw and adjusted monthly RMSE and mean bias are retained, including worse
results. No selection or parameter tuning uses the holdout year. The station
inventory does not imply complete observations or sensor coverage. Elevation,
exposure and mountain/coastal transitions can cause poor transfer; a lower
regional average RMSE does not establish improvement at every grid cell.
Station anemometer heights are not established by the downloaded inventory;
wind transfer assumes compatibility with the 10 m ERA5 variable.
Daily mean corrections preserve ERA5 subdaily structure, so calibrated hourly
extremes, fatigue cycles and joint temperature-humidity behavior are not claimed.
Relative humidity is bounded to 0–100%; clipped-hour counts are retained.

## How degradation rates are calculated

The existing `energy_methods.degradation` equations and the explicitly recorded
Kaaya 2019 mono-Si parameters are reused. No material prefactor is fitted to
AEMET weather. Rates in numerical **%/year are model scenarios**, not observed
Canary PV plant losses or validated warranty/lifetime predictions.

| Parameter | Value |
| --- | ---: |
| Hydrolysis prefactor A_H | 49,100,000 |
| Photodegradation prefactor A_P | 71.83 |
| Thermomechanical prefactor A_Tm | 2.04 |
| Activation energies H / P / Tm (eV) | 0.74 / 0.45 / 0.43 |
| Humidity / UV / thermal-range exponents | 1.9 / 0.63 / 2.24 |
| Combined normalization A_N (scenario assumption) | 1 |
| Cycles/year (scenario assumption) | 365 |

Normalization follows the repository's 2019 convention: RH in percent, UV in
kWh/m²/year, Kelvin in Arrhenius terms, thermal difference in degrees C.
The combined rate is `A_N × product(1 + mechanism_rate) − 1`, not their sum.
This is not an exact reproduction of published rasters.

Hourly module temperature uses the study's GHI-based Faiman approximation,
U0=26.9, U1=6.2 and 2 m wind height (10 m wind scaled by exponent 0.2).
Annual mean module temperature and ambient RH, mean daily module maxima/minima,
and full-year integrated UV feed the rate model. All 8,760 hours are required.
Mounting and technology are an open-rack mono-Si scenario, not an island inventory.

**Solar radiation has not been calibrated with AEMET radiometer measurements.**
ERA5 GHI is unchanged; UV is an explicit 5% broadband proxy, with 4% and 6%
scenario sensitivity in `rates.csv`. This is not measured spectral UV or a
statistical confidence interval. PID, LID, LeTID, salt corrosion, hail, cracking,
soiling and failure-event rates are outside this model.

## Reproduce

```bash
uv sync --locked --all-packages
# Requires AEMET_API_KEY for fresh acquisition; no credentials are published.
uv run --no-sync python scripts/prepare_aemet_canary_calibration.py
# Offline from the captured inputs:
uv run --no-sync python scripts/analyze_aemet_canary_calibration.py
cd examples/analysis
uv run --no-sync python plot_aemet_era5_canary.py
```

The acquisition workflow stores AEMET source snapshots as an Actions artifact,
and commits the Canary subset, station/field metadata and node/year-partitioned hourly
weather to the study branch. `aemet_provenance.json` and `era5_provenance.json`
record source requests and per-partition hashes. Daily inputs are split by station;
hourly inputs by native node and year, to keep source files bounded and readable. Raw daily metadata is retained to audit
variable definitions. The offline pipeline writes `calibration_parameters.csv`,
`validation.csv`, `rates.csv`, `summary.json` and three four-band GeoTIFFs.
The gallery recalculates rates from saved annual stresses before plotting them.

## Sources

- [AEMET OpenData specification](https://opendata.aemet.es/AEMET_OpenData_specification.json).
  Fuente: AEMET; retain the acquisition dates in the provenance.
- [Open-Meteo historical API](https://open-meteo.com/en/docs/historical-weather-api).
  ERA5/Copernicus C3S, distributed through Open-Meteo under CC BY 4.0.
- [Kaaya et al. (2019), Table IV](https://doi.org/10.1109/JPHOTOV.2019.2916197).
  Parameters also checked in Kaaya's doctoral thesis Table 4.3.
- [Global climate degradation mapping (2019)](https://doi.org/10.3390/en12244749).
- [Kaaya et al. (2021), UV approximation comparison](https://doi.org/10.1016/j.solener.2021.01.071).
- Coastline masks: the existing attributed CHELSACanaryClim assets; see
  [the original Canary guide](pvdeg-canary.md).
