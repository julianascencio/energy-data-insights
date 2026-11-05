# Chile PVDeg thermal screening at native climate resolution

This extends the [Canary Islands PVDeg workflow](pvdeg-canary.md) using actual
CHELSA v2.1 temperature data for continental Chile and coastal islands.
It imports **PVDeg 0.7.4**, with the same relative Arrhenius exposure method.
The [runnable gallery](https://julianascencio.github.io/energy-data-insights/auto_examples/analysis/plot_pvdeg_chile.html)
includes northern, central and southern maps, Atacama and Santiago-Rengo
close-ups, and activation-energy/module-temperature sensitivity at six sites.

## Resolution, coverage and evidence

- **Native 30 arcseconds**: approximately 927 m north-south and 519–884 m
  east-west across the study. This is about 1 km, not 100 m. Every original
  climate-cell centre is preserved; there is no interpolation or upsampling.
- **Period**: monthly climatological mean air temperatures, 1981–2010.
  CHELSA is downscaled modeled climate, not a grid of field observations.
- **Coverage**: continental Chile, Chiloe, Tierra del Fuego and coastal
  archipelagos within 76–66 W and 56–17.4 S. Rapa Nui, Juan Fernandez,
  other Pacific oceanic islands and Antarctica are excluded.
- **Mask**: Natural Earth Admin 0, 1:10 million, with all Chile polygons and
  holes retained within the geographic window. Its `10m` means cartographic
  scale, not ten-metre positional accuracy. Whole cells are selected by centre.
- **Missing data**: any missing monthly input invalidates the cell. Gray is
  land without complete climate; light blue is outside the boundary.

This temperature-only study has no dependency on the Global Solar Atlas Chile
coverage limit at 45 S. It can evaluate southern cells where CHELSA has all
months, without inventing southern irradiation. No claim of validated 1 km
PV-degradation accuracy is made.

## Model and assumptions

`energy_analysis.pvdeg_chile.screen_monthly_rasters` reads bounded row batches
from twelve aligned rasters, masks nodata, applies each source scale/offset,
converts kelvin to Celsius, and calls the shared
`energy_methods.pvdeg.thermal_stress_index`. This calls PVDeg's
`degradation.arrhenius`, weights months by their non-leap-year hours, and
normalizes against exposure at constant 25 C.

Central assumptions are **air temperature +20 C**, **60 kJ/mol activation
energy**, and zero humidity/irradiance exponents. A value of two means twice
the modeled thermal exposure under those assumptions. It is **not percent
power loss per year, remaining lifetime, or a warranty assessment**.

Monthly means and a constant temperature offset do not capture hourly peaks,
nighttime cooling, mounting, module construction or wind cooling. Sensitivity
curves vary activation energy over 40/60/80 kJ/mol and module-air offsets over
0/20/40 C; they are scenarios, not confidence intervals. Source pixels at the
six named sites are sampled directly without interpolation. This supports
regional screening and planning further measurements, not investment-grade
reliability claims or 30–50 year service-life forecasts.

## Run and export

```bash
uv sync --locked --all-packages --group docs
cd examples/analysis
uv run --no-sync python plot_pvdeg_chile.py
```

Download the gallery ZIP or keep the script, twelve temperature TIFFs, GeoJSON
boundary and provenance together. All calculations run offline with PVDeg.

From the repository root, export the georeferenced result for QGIS:

```python
from pathlib import Path
from energy_analysis.pvdeg_chile import run_chile_study

values, profile, manifest = run_chile_study(
    Path("examples/analysis"),
    Path("artifacts/pvdeg-chile/chile_thermal_stress.tif"),
)
```

The output is a single-band float32 GeoTIFF in EPSG:4326 with nodata -9999,
dimensionless exposure, the original climate grid and scenario metadata.
Input TIFFs retain encoded uint16 Kelvin values; apply their embedded scales
and offsets before subtracting 273.15. Mask 65535 before conversion.

## Reproduce the inputs

```bash
uv run --no-sync python scripts/prepare_pvdeg_chile.py \
  --source-manifest examples/analysis/pvdeg_chile_provenance.json
```

The existing CHELSA connector uses bounded HTTP ranges with strong ETags and
`If-Match`, without downloading whole-world rasters. ETags are object-version
validators, not SHA-256 hashes. The saved manifest additionally pins raw crop
pixel SHA-256 values, local input-file SHA-256 values and the country archive.
The processor uses two download workers and native cell-centre masking.
`--cache` and `--output` override the artifact directories; TLS verification
remains enabled and configured HTTPS proxies are supported.

## Attribution

- Karger et al. (2021), CHELSA v2.1 climatologies,
  [DOI 10.16904/envidat.228](https://doi.org/10.16904/envidat.228), CC0-1.0.
- Karger et al. (2017), climate downscaling,
  [DOI 10.1038/sdata.2017.122](https://doi.org/10.1038/sdata.2017.122).
- Springer et al. (2026), PVDeg,
  [software DOI 10.5281/zenodo.8088382](https://doi.org/10.5281/zenodo.8088382),
  BSD-3-Clause; integration pins version 0.7.4.
- [Natural Earth country boundaries](https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-0-countries/),
  public domain. Cropping and raster masking are modifications; no endorsement implied.
