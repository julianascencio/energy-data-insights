# Look up climate metadata for one site

`energy_analysis.climate_comparison.site.site_climate_profile` returns KGPV,
JRC, ML21 and PVCZ context in one JSON-compatible record. The result includes
class codes and meanings, every column in the selected source rows, units where
defined, coordinates, distances, source periods/resolutions, provenance, uses
and limitations. JRC also retains its frozen model and training-range flags.

The gallery tutorial uses **(-34.406, -70.858)** near Rengo, Chile, as an example
coordinate. It is not a surveyed plant. The bundled source subsets contain every
row within 75 km of that coordinate and preserve **10 JRC, 18 ML21 and 49 PVCZ
columns**. KGPV labels are imported from the ML21 workbook. The full native
metadata is exposed even where a column's units must be checked in the provider
documentation; unknown units are never guessed.

The tutorial also uses PVCZ's full metadata to compare open-rack and close-roof
Arrhenius-equivalent temperatures at 1.1 eV. That practical mounting-stress screen
helps identify a follow-up thermal study; it does not estimate a measured site
temperature change or a %/year degradation penalty.

## Short offline example

```python
import json
from pathlib import Path
from energy_analysis.climate_comparison.site import load_site_example, site_climate_profile

catalogues, metadata, model = load_site_example(Path("examples/analysis"))
profile = site_climate_profile(
    -34.406,
    -70.858,
    catalogues=catalogues,
    source_metadata=metadata["sources"],
    jrc_model=model,
    radius_km=50,
)
for scheme, entry in profile["classifications"].items():
    print(scheme, entry["status"], entry["code"], entry["distance_km"])
    print(entry["source"])  # period, resolution, URL, hashes and references
    print(entry["candidates"])  # all fields of every equally nearest source row
    print(entry["field_metadata"])
Path("site_climate.json").write_text(json.dumps(profile, indent=2, allow_nan=False))
```

The example returns **KGPV DH**, **JRC09**, **ML21 Mou1**, and **PVCZ T6:H3**.
JRC and PVCZ source coordinates are about 3.91 km away; KGPV/ML21 source
coordinates are about 16.70 km away. These are **nearby reference classifications**,
not an independently validated assignment at the requested coordinate. In
particular, the mountainous ML21 class illustrates why terrain and source-grid
support should be checked before accepting a nearby class for a lowland site.

## How matching works

| Result status | Meaning and next action |
| --- | --- |
| `matched` | All equally nearest rows agree on a usable class. Check distance, source support and terrain. |
| `ambiguous` | Equally nearest records have different codes. All candidates are retained; no winner is invented. |
| `missing_inputs` | The nearest JRC source row lacks required features. Retrieve appropriate site data. |
| `outside_radius` | The nearest supplied point is farther than the selected limit. No class is assigned. |
| `outside_sample_coverage` | The requested search circle exceeds a bundled subset's known support. Load full catalogues. |
| `no_source_rows` | The supplied catalogue is empty. This alone does not prove provider coverage is absent. |
| `source_not_supplied` | This provider table was not passed to the function. |
| `model_not_supplied` | A nearby JRC row exists, but its frozen classifier was not supplied. |

The distance is a great-circle approximation on a mean-radius sphere. The
inclusive radius is a caller-selected search limit, not a validated threshold
for local representativeness. Coincident rounded PVCZ coordinates remain separate
candidates. There is no interpolation and no search past a missing nearest row
to obtain a more convenient label. Numeric class IDs are local to each scheme.

## Use full catalogues for arbitrary sites

The bundled Rengo subset cannot answer arbitrary world coordinates. Explicitly
download the full source objects using the existing connectors, or reuse a
saved copy. JRC is about 212 MB, ML21 about 11 MB and PVCZ about 49 MB. For example,
the following retrieves the pinned objects through the shared transport:

```python
from pathlib import Path
from energy_data_retrieval.sources.jrc_climate import client as jrc
from urllib.parse import urlsplit
from energy_data_retrieval.sources.ml21 import client as ml21
from energy_data_retrieval.sources.pvcz import client as pvcz
from energy_data_retrieval.transport import HTTPClient, HTTPConfig

raw = Path("data/pv-climate")
raw.mkdir(parents=True, exist_ok=True)
hosts = frozenset(urlsplit(client.URL).hostname for client in (jrc, ml21, pvcz))
with HTTPClient(allowed_hosts=hosts, config=HTTPConfig(maximum_response_bytes=300_000_000)) as http:
    jrc.download(http, raw / "jrc_means_global.csv")
    ml21.download(http, raw / "ml21_supplement.xlsx")
    pvcz.download(http, raw / "pvcz.csv")
```

Then load all fields and supply metadata matching the actual downloaded version:

```python
from energy_data_retrieval.storage import sha256_file
from energy_methods.climate_zones import ClimateClusterModel
from energy_analysis.climate_comparison.site import site_climate_profile

catalogues = {
    "jrc": jrc.read_catalogue(raw / "jrc_means_global.csv"),
    "ml21": ml21.read_catalogue(raw / "ml21_supplement.xlsx"),
    "pvcz": pvcz.read_catalogue(raw / "pvcz.csv"),
}
source_metadata = {
    "jrc": {
        "source": "JRC PVGIS/ERA5",
        "period": "2005-2023",
        "resolution": "0.1 degree",
        "url": jrc.URL,
        "sha256": sha256_file(raw / "jrc_means_global.csv"),
    },
    "ml21": {
        "source": "Publisher supplementary workbook",
        "period": "Mixed source climatologies",
        "resolution": "0.5 degree",
        "url": ml21.URL,
        "sha256": sha256_file(raw / "ml21_supplement.xlsx"),
    },
    "pvcz": {
        "source": "PVCZ author catalogue",
        "period": "2010-2018",
        "resolution": "0.25 degree; rounded coordinates",
        "url": pvcz.URL,
        "sha256": sha256_file(raw / "pvcz.csv"),
    },
}
# Reuse the saved global model; do not refit it on the requested site's vicinity.
model = ClimateClusterModel.from_dict(
    json.loads(Path("examples/analysis/climate_jrc_model.json").read_text())
)
latitude, longitude = -34.406, -70.858  # Replace with your site's coordinates.
profile = site_climate_profile(
    latitude,
    longitude,
    catalogues=catalogues,
    source_metadata=source_metadata,
    jrc_model=model,
    radius_km=50,
)
```

This metadata describes the reviewed releases. If files change, verify their
period, units and schema before reusing it. Preserve provider attribution and
the PVCZ MIT notice. The publisher's ML21 radiation statistics use their native
J/m² convention; do not silently reinterpret them as annual irradiation totals.
The companion preparation script verifies the reviewed full-file hashes before
extracting a new tutorial bundle:

```bash
uv run python scripts/prepare_site_climate_example.py --raw-directory data/pv-climate
```

## What to do with the result

| Context | Practical use | Additional evidence needed |
| --- | --- | --- |
| KGPV | Form broad climate/irradiation peer groups for fleet benchmarking. | Comparable module technology, mounting, age, data quality and period. |
| JRC | Screen irradiation and module-temperature regimes for yield/thermal analysis. | Local hourly weather, actual tilt, mounting, ventilation and measured performance. |
| ML21 | Stratify PV performance comparisons by climate family. | Site representativeness and out-of-sample performance validation. |
| PVCZ | Plan climate-stress qualification or targeted thermal/humidity inspections. | Actual module materials, mounting and field failure/inspection evidence. |
| Degradation model | Estimate a calibrated climate-degradation scenario in %/year. | Explicit module parameters plus temperature, RH, UV and cycle stresses. |

A useful workflow is: verify source support → select comparable peers → retrieve
local weather and PV records → run the appropriate physical/statistical model →
compare against observations. The existing `energy-retrieve discover` command
can find nearby weather stations and available grid products from the same
coordinates; see [location discovery](location-discovery.md).

Do not convert a class number into a loss percentage, average IDs across schemes,
infer degradation from PVCZ alone, or treat model-range flags as confidence
probabilities. For the rate workflow, see [degradation mapping](degradation-gallery.md).
