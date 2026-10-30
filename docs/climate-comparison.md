# Comparing PV climate classifications

The package adds three complementary methods alongside KGPV: JRC parametric
performance climates, a seven-feature ML21 refit workflow, and PVCZ thermal and
humidity stress zones. These schemes answer different questions. A PVCZ class
is not an annual degradation rate, and agreement with a published map is not
validation against measured PV performance.

| Scheme | Inputs and purpose | Available implementation |
| --- | --- | --- |
| KGPV | Monthly temperature/rainfall and annual GHI; broad PV climate | Existing `energy_methods.kgpv`; published reference labels also imported from ML21 supplement |
| JRC parametric | Annual **plane-of-array** irradiation and irradiance-weighted **module** temperature; performance climates | `performance_features`, `fit_jrc_climate`, frozen JSON model |
| ML21 | Seven temperature, GHI and UV statistics, weighted by their fitted relationship to specific yield | Original 21-class labels plus a separately identified `fit_ml21` workflow |
| PVCZ | Arrhenius-equivalent module temperature at 1.1 eV and mean **specific** humidity in g/kg | `equivalent_temperature`, fixed `classify_pvcz`, published 50-class catalogue |

The thesis remains the repository's primary scientific citation. Cite the
individual method and dataset authors too; see the [reference catalogue](references.md).

## Published maps and new fits

`energy_methods.climate_zones` supplies `ClimateProvenance`, `ClimateZones` and
`ClimateClusterModel`. Class ID zero and an empty code mean missing data. Positive
IDs are local to a scheme and model version: never join unrelated schemes on
numeric class ID. Results retain readable labels and the caller-declared source,
period, resolution and application status.

Cluster models serialize to ordinary versioned JSON, with feature order, scaling,
weights, centers, training bounds, parameters, software versions and attribution.
`predict` does not refit; it works in bounded batches and preserves missing rows.
Training-range flags identify feature extrapolation, not a calibrated confidence
probability. All training rows must be complete; prediction infinities fail.

```python
import json
from pathlib import Path
from energy_methods.climate_zones import ClimateClusterModel

model = ClimateClusterModel.from_dict(
    json.loads(Path("examples/analysis/climate_jrc_model.json").read_text())
)
zones = model.predict([[1800, 35], [2200, 42]])
print(zones.zone, zones.provenance.period)
```

### JRC parametric climates

The global reference inputs come from PVGIS/ERA5 for **2005–2023**, at **0.1°**
native spacing and optimal tilt. Source `G` is annual in-plane irradiation in
kWh/m²; it is not GHI. `Tw` is irradiance-weighted module temperature. `E` and
`eff` are modeled outputs, not observations of operating plants.

`performance_features` integrates `G * duration / 1000` and computes
`sum(G * T * duration) / sum(G * duration)` over the last axis. Supply a complete
year; annualize the irradiation explicitly for a complete multiyear record.
Missing intervals propagate, and zero irradiation gives undefined weighted
temperature. The function cannot detect omitted timestamps.

`fit_jrc_climate` follows the documented global workflow: complete rows at 0.5°
nodes, population-standard-deviation scaling, cosine-latitude centroid weights,
10 clusters, seed 10, 100 random initializations and at most 20 Lloyd iterations.
The best run minimizes **unweighted** squared distance, as in the author notebook;
centers are ordered by `[1, 1.5]` in normalized feature space. Sklearn convergence
and empty-cluster handling are explicit adaptations. `JRC01`–`JRC10` identify
this **documented refit**, not an exact reproduction of an author raster.
Distribution-based optimal-transport climates are outside this implementation.

### ML21

The publisher's supplementary workbook supplies **55,418** locations, original
ML21 labels (`Tro1`–`Tro4`, `Des1`–`Des3`, `Mou1`–`Mou3`, `Tem1`–`Tem5`,
`Col1`–`Col4`, `Pol1`–`Pol2`), inherited KGPV labels and a specific-yield target.
The maps display these original labels. Their source climatologies differ; the
workbook is not represented as a common-period measured dataset.

A new fit uses the ordered features `Tann, Tmax, Tmin, GHIann, GHImax, GHImin,
UVann`. It standardizes training features, fits ordinary least squares against
training yield, weights standardized distances by absolute coefficients, and
runs 21-cluster k-means. Normalizing all weights by their common maximum leaves
assignments unchanged. Refitted classes are named `ML01`–`ML21`, ordered by
mean irradiation statistic then temperature. They are **not** mapped onto the
published semantic labels or rounded published regression coefficients.

**Preserve the source feature convention.** The connector retains the workbook's
radiation statistics in their native J/m² convention. It does not infer that
`GHIann` is a physical annual total or silently convert it to kWh/m²/year.
New fits require an explicit `feature_convention`; applications of a frozen model
must use the same units and aggregation. Temperatures are Celsius and target
yield is kWh/kWp/year. Numeric shape checks cannot establish semantic equivalence.

The included refit uses 44,818 training sites and 10,600 held-out sites selected
by fixed 5° geographic blocks. Both scaling and yield weights are fitted only
on training sites. The manifest records adjusted Rand agreement with published
labels and within-class yield dispersion. The original reference map was built
using its own training data, so this agreement is not independent field
validation. `class_target_rmse` computes dispersion around class means within
the evaluated sample, **not predictive RMSE**. A scientific ranking would also
require common input periods, identical sites, area weights, equal class counts,
and independent measured outcomes. The paper's reported SSE improvement is not
a percentage improvement in forecasting accuracy.

### PVCZ

The pinned author CSV uses GLDAS **2010–2018**, at **0.25°** native spacing. The
reference thermal stress is based on an open-rack polymer-back module model.
`equivalent_temperature` implements the Arrhenius mean with duration weighting,
including night intervals; it uses a numerically stable log-sum-exp calculation.
For the published scheme use the default activation energy of **1.1 eV**.

Temperature boundaries are 14, 19, 24, 29, 34, 39, 44, 49 and 54 °C; humidity
boundaries are 3, 4.1, 5.9 and 10.5 g/kg. Equality enters the warmer/wetter class.
Codes run from `T1:H1` to `T10:H5`; positive package IDs equal upstream IDs + 1.
Humidity is not relative humidity. No percent/year degradation or lifetime is
inferred from these stress classes.

The source CSV rounds stresses and coordinates to limited precision. Distinct
native cells can share a reported coordinate. The reader preserves these rows;
coordinates are not unique identifiers. Rounded stresses at a threshold can
recompute to a different class, so reference maps retain original author labels.
Neither exact 0.25° centers nor fine local boundaries are reconstructed.

```python
from energy_methods.climate_zones import ClimateProvenance
from energy_methods.pvcz import classify_pvcz, equivalent_temperature

teq = equivalent_temperature([[20, 35, 50, 25]], duration_hours=6)
result = classify_pvcz(
    teq,
    [6.0],
    provenance=ClimateProvenance(
        "Illustrative complete daily cycle", "synthetic day", "one site", "demonstration"
    ),
)
print(result.zone)
```

## Offline maps and coverage

The gallery compares all four schemes for the world, contiguous mainland Chile,
and the Canary Islands. Source CSV subsets, frozen models, hashes and map scripts
are downloadable together. Global display samples retain one actual point near
each 2° bin center; there is no averaging of labels or ocean gap filling. The
Chile JRC display samples use 0.2° bins, and country plots select centers within
the existing mainland contour. CSV regional bounds can include neighboring
countries; only the plotted subset is mainland Chile. Display marker size is
not climate resolution. Each map has its own legend.

The Canary examples contain 45 JRC points, two ML21/KGPV reference points and
**no PVCZ observations**. Empty coverage is shown explicitly. Outlines reuse the
existing Canary climate-raster footprints, not surveyed coastlines. For the
separate detailed KGPV applications see [Canary Islands](kgpv-canary.md) and
[mainland Chile](kgpv-chile.md); those maps use different source periods and
must not be passed off as higher-resolution versions of these reference tables.

## Retrieval and regeneration

The three `energy_data_retrieval.sources` readers (`jrc_climate`, `ml21`, `pvcz`)
use the shared bounded HTTP transport when explicitly asked to download. JRC
is about 212 MB, ML21's XLSX about 11 MB, and PVCZ about 49 MB. Downloads record
hashes. The PVCZ object is pinned to commit
`aa89fab8d1d66f46f4ea8575e2452aa75a927535`; no untrusted pickle is loaded.
The XLSX reader bounds the declared expanded archive size at 300 MB.

From the repository root, with the normal workspace installed:

```bash
uv run python -m energy_analysis.climate_comparison.prepare \
  --raw-directory .local/pv-climate-sources \
  --output-directory examples/analysis \
  --world-boundaries examples/connectors/data/generation_coverage_world.geojson \
  --download

cd examples/analysis
uv run python plot_climate_world.py
uv run python plot_climate_chile.py
uv run python plot_climate_canary.py
```

Omit `--download` to reuse raw sources named `jrc_means_global.csv`,
`ml21_supplement.xlsx`, and `pvcz.csv`. Full datasets stay outside version control;
small attributed CSV samples and numerical JSON state are committed. Keep the
existing Chile contour and Canary TIFF context files beside regional examples.
A fresh preparation records new source bytes and model versions; compare the
manifest to the reviewed one before treating it as the same study. Gallery and
CI execution are offline and do not refit or contact providers.

## Sources and reuse

- Medina, Martínez and Dunlop, *Parametric and distribution-based definition of
  climatic zones for photovoltaics*, Solar Energy 306 (2026), 114295.
  [Paper](https://doi.org/10.1016/j.solener.2025.114295),
  [JRC dataset](https://data.jrc.ec.europa.eu/dataset/71142004-19c2-4827-bfa3-16d640528e5a),
  [author workflow](https://github.com/ismedina/climatic-zones-pv).
  Independent implementation; no author notebook code is vendored.
- Francisco Javier Triana de las Heras, Olindo Isabella and Malte Ruben Vogt,
  *A machine learning approach to PV-climate classification*, Renewable Energy
  256 (2026), 123685. [Paper](https://doi.org/10.1016/j.renene.2025.123685),
  [supplement](https://ars.els-cdn.com/content/image/1-s2.0-S0960148125013473-mmc1.xlsx).
  Article licensed CC BY; extracts retain author/source attribution.
- Todd Karin, C. Birk Jones and Anubhav Jain, *Photovoltaic Degradation Climate
  Zones*, IEEE PVSC (2019). [Author repository and paper](https://github.com/toddkarin/pvcz).
  CSV redistribution retains its MIT notice in `examples/analysis/climate_PVCZ_LICENSE.txt`.
- European Commission JRC source reuse requires attribution; see its
  [legal notice](https://commission.europa.eu/legal-notice_en).
  Natural Earth outlines are public domain. Canary footprint attribution remains
  in the existing [Canary source guide](kgpv-canary.md).
