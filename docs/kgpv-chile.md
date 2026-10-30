# Contiguous Chile KGPV at the native solar grid spacing

The [mainland Chile gallery](https://julianascencio.github.io/energy-data-insights/auto_examples/analysis/plot_kgpv_chile.html)
provides regional maps, Atacama and central-valley zooms, a downloadable GeoTIFF,
GeoJSON/Shapefile contours, sample input values and source provenance. It uses the
repository's existing KGPV classifier with fixed literature thresholds.
**7,848,061 mainland pixels are classified; 2,621,175 remain unclassified.**

## Resolution and coverage

The output preserves the **9-arcsecond (0.0025°, nominal 250 m) solar lattice**.
This is the finest verified, openly downloadable GHI grid adopted for this
example, not a claim that no finer dataset can exist. No arbitrarily fine grid
is created. Unlike the Canaries, Chile does not use CanaryClim: the regional
Canary climate product does not cover Chile.

| Component | Source and period | Native support and treatment |
| --- | --- | --- |
| Monthly mean temperature | CHELSA v2.1, 1981–2010 | 30 arcseconds, about 1 km; nearest original cell |
| Monthly precipitation total | CHELSA v2.1, 1981–2010 | 30 arcseconds, about 1 km; nearest original cell |
| Annual horizontal GHI | Global Solar Atlas 2.0, 2019 Chile archive, 1999–2018 | 9 arcseconds, nominal 250 m; original pixel centres retained |
| Country contour | Natural Earth Admin 0, 1:10 million | Largest connected Chile polygon; vertices and holes retained |
| Display | Bounded categorical reads and overviews | Nearest-neighbour only; downloadable pixels are unchanged |

In geographic coordinates, 9 arcseconds is about 278 m north–south and
164–265 m east–west across mainland Chile. The climate grid is roughly 927 m
north–south. **250 m output spacing does not establish 250 m climate or KGPV
accuracy.** Natural Earth's `10m` denotes 1:10 million, not ten-metre accuracy.

**Usable GSA Chile values stop at 45°S**, although the file rectangle extends
to 46°S (its southernmost valid pixel centre is 44.99875°S). The map includes the entire
connected mainland outline to approximately 53.89°S, but land south of 45°S is
unclassified. Coastal and other source-data gaps also remain gray. The example
therefore does **not** provide complete classified mainland coverage. Missing
land stays in the denominator of the area chart; it is never hidden as ocean.
The source raster's rectangle extends west to Easter Island, but all islands
are excluded by the mainland mask.

Two potential replacements were investigated but not substituted: CHELSA
`rsds` includes terrain-slope/aspect effects and is not interchangeable with
horizontal GHI; the Explorador Solar SIG download's published kWh/m² label
could not be reconciled with the retrieved raster's unlabelled values. Neither
is silently blended into the southern gap. Higher-resolution or more complete
results need verified horizontal irradiation and climate inputs, with units,
periods, licensing and support recorded explicitly.

## What “contiguous” means

The analysis selects Chile (`CHL`) from the source Shapefile, then chooses its
largest connected polygon by WGS84 geodesic area. This includes the connected
mainland and Brunswick Peninsula. It excludes Tierra del Fuego, Chiloé, the
coastal archipelagos, Easter Island, Juan Fernández and Antarctica. No polygon
simplification or bridge across water is applied. Holes remain excluded.

Output cells are included when their centres lie inside that polygon. Coastal
cells can therefore partly overlap water; the contour is not a surveyed coast.
Area summaries sum WGS84 ellipsoidal areas of these selected whole cells, not
fractional polygon intersections. This is more appropriate than comparing raw
pixel counts across Chile's large latitude range.

## Scientific interpretation

Climate covers **1981–2010** and GHI **1999–2018**. These are different historical
periods. This exploratory application is not a common-baseline climatology,
future scenario or exact reproduction of the thesis map. It calls the existing
cellwise classifier without weakening `map_kgpv`'s shared-baseline requirement.

Encoded CHELSA nodata (`65535`) is masked **before** scale/offset conversion.
Temperature is converted from kelvin to Celsius; precipitation in kg/m²/month
is equivalent to millimetres per month. The pinned GSA XML identifies annual
GHI in **kWh/m²/year**; do not multiply it by 365. Southern Hemisphere seasons
and the existing KGPV threshold/equality conventions are unchanged. There is no
refitting of irradiation percentiles to Chile and no interpolation or filling
of missing inputs.

Downscaled climatologies, mixed periods and cartographic masks can introduce
errors, particularly along coastlines, steep terrain and classification
thresholds. These maps support regional exploration, not site-level yield or
loss predictions. Most repository development is AI assisted; the cited,
developer-selected literature remains the basis for the method, while code
and derived results still require scientific review.

## Offline example and downloads

```bash
uv sync --locked --all-packages --group docs
cd examples/analysis
uv run python plot_kgpv_chile.py
```

The gallery verifies checksums and independently recomputes twelve site samples
from the supplied CSV without network access. Coyhaique, Cochrane and the inland
Punta Arenas sample retain
missing GHI and class zero. Download the three-band GeoTIFF and provenance from
the gallery. The raster is EPSG:4326, 14,553 rows by 3,480 columns:

| Band | Meaning |
| --- | --- |
| 1 | KGPV class 1–12, with labels in the `zone_codes` tag; 0 means unclassified/outside |
| 2 | Mainland mask: 1 inside, 0 outside; distinguish gray gaps from ocean using this band |
| 3 | All required inputs available: 1; otherwise 0 |

GeoJSON is a single-file contour download. For Shapefile use, retain all five
companions (`.shp`, `.shx`, `.dbf`, `.prj`, `.cpg`) together. The acquisition
command also generates these contours locally.

## Reproduce from source data

From the repository root:

```bash
uv sync --locked --all-packages --group docs --group dev
uv run python scripts/prepare_kgpv_chile.py --plan-only
uv run python scripts/prepare_kgpv_chile.py
```

`--plan-only` reads the bundled source manifest and makes no HTTP requests.
The default cache is `artifacts/chile-kgpv/raw`; outputs are in
`artifacts/chile-kgpv/native`. `--cache`, `--output`, `--source-manifest`,
`--tile-size` (128–1024) and `--workers` (1–2) are configurable. If required by
your environment, `--use-environment-proxy` explicitly uses `HTTPS_PROXY`;
TLS certificate verification remains enabled.

CHELSA's global source rasters are accessed through bounded HTTP ranges, not
whole-world downloads. Every request uses the recorded strong ETag with
`If-Match`; a changed object fails closed. The ETag is a version validator,
**not** a SHA-256 checksum. Each regional crop also has a stable SHA-256 of its
native little-endian uint16 pixel bytes. Its separate file SHA-256 detects
local cache corruption. Original transforms, scales, units and full source
sizes are recorded. Crop windows are integral; climate-grid agreement allows
only 1e-10° floating-point tolerance, not meaningful spatial displacement.

The solar archive (145.4 MB) and boundary archive (4.9 MB) are pinned by full-file
SHA-256. Only exact expected archive members are extracted. GSA's temporary
signed redirect remains in memory; provenance retains the canonical public
URL. Raster processing uses bounded tiles and does not load the full 50-million
cell output rectangle plus 24 climate bands into memory. Raw inputs stay outside
Git; the losslessly compressed categorical TIFF is about 0.55 MB.

For other countries or custom contours, see [country mapping](country-mapping.md).
This study's mainland selection and chosen source pins are Chile-specific.

## Sources and attribution

- **Method:** Ascencio Vásquez (2021), doctoral thesis, and Ascencio-Vásquez et al.
  (2019), KGPV classification. See the [method contract](kgpv.md) and central bibliography.
- **Climate:** Karger et al. (2021), CHELSA v2.1 climatologies,
  [data DOI](https://doi.org/10.16904/envidat.228), CC0 1.0;
  [Scientific Data paper](https://doi.org/10.1038/sdata.2017.122).
  [Provider catalogue](https://www.chelsa-climate.org/datasets/chelsa_climatologies).
- **Solar:** [Global Solar Atlas Chile download](https://globalsolaratlas.info/download/chile).
  Data obtained from the Global Solar Atlas 2.0, a free, web-based application
  developed and operated by Solargis s.r.o. on behalf of the World Bank Group,
  utilizing Solargis data, with funding provided by the Energy Sector Management
  Assistance Program (ESMAP). CC BY 4.0 with additional mediation/arbitration
  terms, preserved in full in the provenance. Cropping, climate-cell sampling and
  KGPV derivation are modifications; no provider endorsement is implied.
- **Boundaries:** [Natural Earth countries](https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-0-countries/), public domain.
- **Excluded radiation alternatives:** [CHELSA v2.1 radiation model](https://essd.copernicus.org/articles/15/2445/2023/),
  Section 2.2.3; [Explorador Solar SIG](https://solar.minenergia.cl/sig).
