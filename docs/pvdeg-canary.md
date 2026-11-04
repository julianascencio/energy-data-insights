# PVDeg integration and Canary Islands thermal screening

This contribution imports **PVDeg 0.7.4**, rather than reproducing its algorithm.
The [runnable gallery](https://julianascencio.github.io/energy-data-insights/auto_examples/analysis/plot_pvdeg_canary.html)
includes a 100 m archipelago map, a Tenerife detail and parameter sensitivity.

## Connector, method and analysis

- `energy_data_retrieval.pvdeg.to_pvdeg_weather` validates canonical weather
  columns and UTC timestamps for PVDeg workflows. The existing PVGIS connector
  remains the acquisition layer. Missing humidity is rejected, never invented.
- `energy_methods.pvdeg.thermal_stress_index` calls
  `pvdeg.degradation.arrhenius` with duration weights and normalizes exposure
  against the same duration at a constant reference temperature.
- `energy_analysis.pvdeg_canary.screen_climate_tile` applies that method to
  twelve monthly temperature bands; `write_stress_geotiff` exports the results.

The index is `sum(w * exp(-Ea/(R*T))) / exp(-Ea/(R*Tref))`, with weights summing
 to one, Kelvin temperatures, R in kJ/mol/K, and Ea in kJ/mol. The default
reference is 25 C. A value of two means twice the modeled thermal exposure
under the specified assumptions, **not twice the annual power loss**.
Missing any month invalidates a cell; ocean and missing inputs are transparent.

## Data and resolution

CHELSACanaryClim v1.0 monthly air temperature covers 1979–2013, CC0-1.0,
[Karger et al. (2025), DOI 10.16904/envidat.692](https://doi.org/10.16904/envidat.692).
The processor downloads twelve SHA-256-pinned source files through the existing
CanaryClim connector, masks encoded nodata, decodes Kelvin and converts to Celsius.
Each 100 m EPSG:32628 cell samples the nearest native source pixel; this is a
point sample, not an area average. Stored temperatures retain 0.01 C encoding,
which does not imply that precision in the underlying climate model.

The 2025 source COG spacing is about 5 m; the published model comparison used
100 m ([Patiño et al., 2023](https://doi.org/10.1111/ddi.13757)). Neither spacing
validates local PV degradation accuracy. Input footprints define coastlines;
no artificial smoothing or coastal extrapolation is applied. Seven disjoint
windows include La Graciosa, Chinijo and Lobos. Provenance records the source
URLs, hashes, period, license, processing grid and scenario.

## Interpretation limits

The central scenario uses **60 kJ/mol and air temperature +20 C**. These are
illustrative assumptions, not fitted material parameters. The gallery varies
Ea over 40/60/80 kJ/mol and offsets over 0/20/40 C. Sensitivity curves are not
confidence intervals. Humidity and irradiance exponents are zero.
Monthly temperatures plus a constant offset do not represent hourly module
thermal behavior, solar heating, wind cooling, mounting or nighttime conditions.
Nonlinearity means monthly means generally cannot reproduce hourly exposure.
This supports regional screening and prioritization of further data collection;
it does not predict annual degradation, a 30–50 year lifetime, warranty outcomes,
LeTID, UV damage, moisture ingress, corrosion or measured reliability.

For a calibrated follow-up, acquire common-period hourly weather with PVGIS,
validate it with the weather adapter, calculate module temperature using measured
mounting and wind conditions, and obtain mechanism-specific material parameters
and field validation before making lifetime claims.

## Reproduction

```bash
uv sync --locked --all-packages --group docs
# About 0.8 GB transferred; one month in memory, no raw disk cache.
uv run --no-sync python scripts/prepare_pvdeg_canary.py
# Compare/copy the resulting tiles and manifest to examples/analysis to refresh.
cd examples/analysis
uv run --no-sync python plot_pvdeg_canary.py
```

For package use: `pip install 'energy-methods[pvdeg]'`. The dependency is optional
because upstream PVDeg includes substantial geospatial/notebook dependencies.
The documentation group and CI explicitly install it; gallery execution uses
real imported PVDeg and offline climate fixtures, never a substitute backend.

## Credit

[Springer et al. (2026), PVDeg software](https://doi.org/10.5281/zenodo.8088382),
National Laboratory of the Rockies / DuraMAT, BSD-3-Clause.
[PVDeg documentation](https://pvdegradationtools.readthedocs.io/en/latest/).
The upstream documentation describes its JOSS paper as in review; no published
paper DOI is asserted. This is an independent PVDeg integration, not a claim
that its mechanism originates in the repository's foundational thesis.
