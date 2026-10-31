# Reproducible 3D PV scenes from candidate footprints

The [El Mirlo 3D gallery](https://julianascencio.github.io/energy-data-insights/auto_examples/analysis/plot_rengo_site_3d.html)
continues the [module-counting pilot near Rengo](rengo-module-counting.md). It
combines the same 2,055 candidate module footprints in 22 tables with a pinned
Copernicus GLO-30 elevation crop and explicit mounting scenarios. The result is
**2.5D scenario geometry, not photogrammetry or a surveyed as-built model**.
It covers the same partial southern inspection block, not the complete farm.

## Evidence and assumptions

| Component | Input or rule | Interpretation |
| --- | --- | --- |
| Module XY | Existing image candidates, including review candidates | Unvalidated horizontal footprints; exclusions stay excluded |
| Table groups | Counter's connected table IDs | A common mounting plane per detected table |
| Elevation | Native 48 × 47 crop of GLO-30, roughly 30 m sampling | DSM including vegetation/buildings; not bare-earth terrain |
| Vertical datum | EGM2008 metres | Preserved, with no conversion to ellipsoidal heights |
| Local axes | WGS84 azimuthal equidistant, east/north/up | Origin −70.8615°, −34.4515°; Z=0 at 282 m EGM2008 |
| Default mounting | 20° tilt, 0° facing azimuth, 0.8 m sampled clearance | Illustrative assumptions; not measured or inferred |
| Display grid | 81 × 121 bilinear samples | Smooth display only; no new source resolution |
| Scope | 2,055 candidates, 22 tables, 0 terrain exclusions | Inherited candidates, not a verified asset inventory |

The original same-image audit matched 51 of 72 single-assistant reference centres,
with 21 missed and no extras in the labelled regions. Those annotations were used
during method development and are not independent human or held-out validation.
Adding height does not improve the count's evidence. Main TanDEM-X acquisitions
for GLO-30 date to 2011–2015, with potentially older gap-fill sources. The elevation
surface and the 2024 image need not represent the same physical state.

## Run the pinned example offline

From the repository root, with Python 3.12 or 3.13:

```bash
uv sync --locked --all-packages
uv run --no-sync python examples/analysis/plot_rengo_site_3d.py
```

The example verifies SHA256 hashes, re-runs the candidate detector, builds the
scene and plots the evidence, 3D overview and tilt sensitivity. No provider calls
are required. To write the interactive viewer and meshes to a new directory:

```python
from pathlib import Path
from energy_analysis.site_3d import export_site_scene
from energy_analysis.site_3d.rengo import build_rengo_scene

data = Path("examples/analysis/data")
study = build_rengo_scene(data / "rengo_modules", data / "rengo_3d")
export_site_scene(
    study["scene"],
    "outputs/el-mirlo-3d",
    title="El Mirlo · southern inspection block",
    provenance={
        "terrain": study["terrain_source"],
        "configuration": study["configuration"],
        "counting": study["counting"]["manifest"],
    },
    attribution=study["terrain_source"]["notice"],
    evidence_note=study["configuration"]["assumptions_note"],
)
```

Open `outputs/el-mirlo-3d/viewer.html` directly in a WebGL-capable browser. The
viewer embeds Plotly, needs no server or internet and offers orbit/zoom, layer
toggles, camera presets and explicitly labelled vertical display factors. Its
default metric scale is 1:1. Display exaggeration does not alter exported geometry.
No basemap or imagery texture is embedded in the viewer.

The gallery's ZIP includes both sets of fixtures, this guide, the gallery script,
the recapture script and the generated viewer/meshes. Extract it and run its
`plot_rengo_site_3d.py` using the installed workspace environment. The pinned
dependency versions remain in the repository's `uv.lock`; the ZIP is not a
vendored Python environment.

## Apply the method to another site

Supply a north-up elevation GeoTIFF with metre heights and a declared vertical
datum. It may use a projected or geographic horizontal CRS. Supply a WGS84
GeoJSON FeatureCollection whose features are individual convex quadrilateral
modules, each with a unique `id` and a `table` property. Each ring has four
corners plus a closing repeat. Holes, multipolygons and altitude coordinates
are rejected rather than guessed. A table polygon is not automatically divided
into modules. Features marked `status: excluded` are omitted.

```python
import json
from pathlib import Path
import numpy as np

from energy_data_retrieval.terrain import TerrainSource, read_terrain
from energy_analysis.site_3d import (
    elevation_grid,
    footprints_from_geojson,
    export_site_scene,
)
from energy_methods.pv_site_3d import (
    LocalSiteFrame,
    MountingParameters,
    build_pv_site_scene,
)

footprints = footprints_from_geojson(json.loads(Path("modules.geojson").read_text()))
descriptor = TerrainSource(
    id="my_dem",
    name="My elevation provider and acquisition date",
    surface="Describe DSM or DTM",
    vertical_datum="Declare the source datum",
    reference_ids=(),
)
grid = elevation_grid(read_terrain("terrain.tif", descriptor))
points = np.concatenate([f.vertices_wgs84 for f in footprints])
lon, lat = points.mean(axis=0)
west, south = points.min(axis=0) - 0.0001
east, north = points.max(axis=0) + 0.0001
# Raster coverage needs enough native neighbours for interpolation.
origin_z = float(grid.sample([[lon, lat]])[0])
frame = LocalSiteFrame(float(lon), float(lat), origin_z)
scene = build_pv_site_scene(
    footprints,
    grid,
    frame=frame,
    bounds_wgs84=(west, south, east, north),
    mounting=MountingParameters(tilt_degrees=20, azimuth_degrees=0, minimum_clearance_m=0.8),
    # Optional: table_mounting={"table-7": MountingParameters(10, 180, 1.2)},
)
export_site_scene(
    scene,
    "outputs/my-site-3d",
    attribution="Provider's required credit",
    provenance={"source": "Record URL/date/hash and footprint provenance"},
)
```

Use measured mounting parameters when available, or label alternatives as
scenarios. Azimuth is clockwise from local north towards the module's facing
direction: 0° north, 90° east, 180° south. The implementation supports sites in
either hemisphere without assuming which way they face.
To continue a counter directly, use `footprints_from_count(result, bounds)`;
`bounds` must be the original north-up EPSG:4326 image's **outer pixel edges**.
The adapter applies its half-pixel convention and retains table groups.
The Rengo GeoJSON export now includes table, row and column identifiers.

## Geometry and missingness rules

`energy_methods.pv_site_3d` contains provider-independent geometry. It uses a local
WGS84 azimuthal-equidistant projection with `always_xy` and a default 20 km radius
guard. Longitude/latitude input is never treated as Cartesian metres. Larger or
antimeridian sites should be split into local scenes. The local frame stores its
origin and WKT explicitly; elevation origin subtraction does not change datum.

For tilt β and facing azimuth α, the plane's metric gradient is
`g = -tan(β) × [sin(α), cos(α)]`. For every table, the algorithm samples terrain
at each footprint's four corners, four edge midpoints and centre, then sets
`b = max(terrain_height − g · xy) + minimum_clearance` over those points.
Every module in the table receives `z = g · xy + b − elevation_origin`.
This makes the table coplanar and enforces clearance at the sampled points.
It does not guarantee clearance between samples or account for support hardware.
Tilt is absolute to horizontal, not added to ground slope. Original XY remains
unchanged, so tilt changes slant dimensions; these are not inferred physical
module dimensions. Different tracker positions or mounting heights require
appropriate table groups and measured parameters.
Detected groups may join separate physical racks; split them when mounting differs.

Elevation sampling is bilinear at native pixel centres. It does not extrapolate,
fill nodata or replace missing values with zero. A module lacking any required
terrain sample is rejected with its ID and reason. Display triangles touching
unsupported samples are omitted. Exact valid native centres remain valid next to
nodata. Source features below native resolution remain unresolved even when the
display mesh is dense. All-invalid inputs fail explicitly.
Coordinates within 1e-8 native pixels of a centre are snapped to that centre to
avoid projection round-off creating false nodata rejections.

`energy_analysis.site_3d` adapts the existing terrain connector and counter,
provides plots and exports, and holds the hash-checked Rengo composition.

## Export contract

| File | Contents |
| --- | --- |
| `viewer.html` | Self-contained interactive scene; no network required |
| `site.obj`, `site.mtl` | Triangulated terrain and individually named module surfaces |
| `scene.json` | Full vertices, faces, module/table IDs, CRS, height origin, datum and provenance |
| `summary.json` | Counts, mounting parameters, source information and terrain rejections |
| `README.txt` | Import conventions and source credit |

Import OBJ as **metres, Z up**, keeping its MTL beside it. OBJ itself has no
geographic CRS field, so retain `scene.json`. Meshes are surfaces, not watertight
solids. This version does not reconstruct frames, foundations, wiring or trackers,
and performs no shading, irradiance, yield or engineering calculations.
Output directories must be new to prevent accidental overwrites.

## Refresh the elevation capture explicitly

```bash
uv run --no-sync python scripts/prepare_rengo_3d.py \
  --output outputs/rengo-3d-recapture --download-directory data/copernicus-cache
```

Add `--proxy-from-env` only when an HTTPS proxy is required. The script uses the
existing Copernicus connector, downloads the full S35/W071 tile outside tracked
examples, crops native pixels without resampling, and records the original
receipt, metadata and hashes. It never refreshes imagery or silently replaces
the pinned fixture. Review hash or source changes before adopting a new capture.

## Verification and sources

Tests use analytic planes and multiple geographic origins to check projection,
bilinear sampling, zero versus nodata, common table slopes, clearance, face winding,
preserved XY, per-table overrides, explicit rejection and export indices. The
offline Rengo integration checks the inherited 2,055 candidates, 22 tables and
zero terrain rejections. These are software checks, not field-validation scores.

Primary references: [PROJ azimuthal-equidistant projection](https://proj.org/en/stable/operations/projections/aeqd.html),
[Copernicus DEM description and terms](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM),
[AWS public DEM distribution](https://registry.opendata.aws/copernicus-dem/),
[Plotly mesh API](https://plotly.com/python/3d-mesh/) and
[self-contained HTML export](https://plotly.com/python/interactive-html-export/).
The table lifting rule is a documented implementation choice, not a published
photogrammetric reconstruction method.

Required adapted-data credit:

produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence
and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA;
all rights reserved
