# Map degradation rates

The gallery now executes the existing climate-degradation model against saved
annual stresses from the 2016–2018 ERA5 study. It shows hydrolysis,
photodegradation, thermomechanical and combined **%/year** maps, plus the thesis's
0.2%/year rate categories. The source is modelled weather; the rates are a
module-specific scenario, not measured field degradation.

Run the example from the repository root:

```bash
uv sync --locked --all-packages --group docs
cd examples/analysis
uv run python plot_degradation_rates.py
```

The gallery's complete ZIP contains this script, annual stress CSV, original
rate table, parameter JSON, source-cell coordinates, provenance and Natural
Earth outlines. Extract it and run the script from that directory with the
workspace packages installed. No network request occurs during execution.

## What is calculated

`load_degradation_example(Path("."))` verifies the input checksums, reconstructs
the annual xarray grid, calls `energy_methods.degradation_mapping.map_degradation`,
and compares all rates, classes and valid-year counts with the archived study.
The code is in `energy_analysis.degradation.gallery`; the numerical equations
remain in `methods` and the provider acquisition stays in `data-retrieval`.

The run contains 1,867,584 hourly location records at 71 CRU-supported land
centres. Sixty-three centres pass the complete-year checks; eight Arctic
centres stay missing because of invalid solar inputs. The input grid is sampled
at **15° spacing**. It is not a continuous high-resolution land map. Rectangles
show coarse sample footprints, including coastal ocean portions, and do not
imply uniform climate inside those footprints. Outlines are visual context only.

The saved combined scenario rates range from approximately **0.019 to
1.101%/year**. This range is specific to the input period, sampling, calibration
and processing conventions. It is not a worldwide empirical confidence range.

## Calibration and scientific interpretation

The scenario uses the published Kaaya mono-Si coefficients, with `A_N=1`,
arithmetic ambient RH in percent, mean daily module-temperature extrema,
one thermal cycle per day, GHI-based Faiman temperature, and Wald 280–400 nm UV.
These choices are recorded; they do not establish that the original calibration
transfers unchanged to a different module, mounting or effective-stress definition.

The combined equation is multiplicative. Do not add mechanism rates or convert
them into shares summing to 100%. Numerical `0.5` means **0.5%/year** under the
model's convention. The second calculation in the tutorial compares
`mean_stress` with `mean_rate`; their difference is an aggregation sensitivity,
not a calibrated uncertainty interval.

The primary reference remains Julián Ascencio Vásquez's 2021 thesis, equations
3.14–3.17 and Section 6.4. See [equations and inputs](degradation.md) and
[the full applied study](../analysis/src/energy_analysis/degradation/README.md)
for the original method authors, weather processing and limitations.

## Make a regional or site study

1. Copy `analysis/examples/degradation/global_2016_2018.toml`. Choose a bounded
   regional grid, complete years and a separate input/output directory. The
   configuration bounds specify **cell centres**, not polygon edges.
2. Supply explicit module coefficients and their source. Use the published
   scenario only when its assumptions are acceptable for the intended comparison.
3. Run `energy-degradation-study retrieve`, then `energy-degradation-study run`.
   Both consume the configuration as shown in the applied-study guide. Provider
   access/attribution terms apply; the default Open-Meteo public endpoint is for
   non-commercial use.
4. Inspect missing-hour counts, source versus requested coordinates and all
   scenario metadata. Changing grid spacing does not increase native ERA5 accuracy.
5. Validate against independently measured performance-loss trends and inspections
   before using the result for design, maintenance or financial assumptions.

For already prepared annual stresses, call the reusable method directly:

```python
import json
from pathlib import Path
import xarray as xr
from energy_methods.degradation import DegradationParameters
from energy_methods.degradation_mapping import map_degradation
from energy_methods.mapping import write_geojson

parameters = DegradationParameters(**json.loads(Path("parameters.json").read_text()))
with xr.open_dataset("annual_stresses.nc") as source:
    rates = map_degradation(source.load(), parameters, aggregation="mean_stress")
rates.to_netcdf("degradation.nc")
write_geojson(rates.total_rate, Path("total_rate.geojson"))
```

GeoJSON cell footprints require at least two regular grid centres per axis and
are bounded to 100,000 polygons. Use NetCDF for larger grids. For one location,
call `degradation_rates` with explicit annual stresses rather than inventing a
regional grid. A KGPV/ML21/PVCZ label does not supply those stresses or a rate.

## Recreate the gallery fixtures

Complete a study using the existing workflow, then:

```bash
uv run python scripts/prepare_degradation_gallery.py \
  --study-output artifacts/degradation-2016-2018 \
  --output examples/analysis
```

The exporter verifies the study's completion marker and hashes before extracting
small CSV files. The provenance retains the source manifest hash, original
NetCDF hashes, retrieval-manifest hash, original software versions, parameters,
references and attribution. A new provider retrieval may differ from the saved
2016–2018 capture; compare hashes before claiming an identical reconstruction.

Credit Copernicus ERA5 and Open-Meteo (CC BY 4.0), CRU TS v4.10/Climatic Research
Unit/UEA (ODbL-1.0 and Database Contents License for derived land support), and
Natural Earth (public-domain outlines). No station observations are implied.
