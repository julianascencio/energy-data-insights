# Canary Islands KGPV at native climate pixel spacing

The [Canary Islands gallery](https://julianascencio.github.io/energy-data-insights/auto_examples/analysis/plot_kgpv_canary.html)
maps all eight main islands and nearby islets, with individual island panels,
Tenerife close-ups, sample monthly inputs and seven downloadable native GeoTIFFs.
It applies the existing `energy_methods.kgpv.classify_kgpv` thresholds to public
climate and solar rasters. **304,733,809 native land pixels are classified.**

## What the resolution means

The example preserves the finest grid present in the acquired CanaryClim files;
it does not create an arbitrarily finer grid. Pixel spacing and source accuracy
are different quantities:

| Component | Source grid or evidence | Treatment |
| --- | --- | --- |
| Monthly temperature and rainfall | CHELSACanaryClim v1.0, 2025 COG release: 0.00004684877106756975°, about 5.2 m north-south by 4.6 m east-west | Every native pixel centre is retained |
| Published climate-model comparison | Patiño et al. (2023) evaluated 100 m resolution | The finer COG spacing does **not** establish 5 m climate accuracy |
| Annual GHI | Global Solar Atlas 2.0, 9 arcseconds / 0.0025°, nominally 250 m | Nearest source-cell value; no invented finer solar information |
| Web figures | Bounded nearest-neighbour reads and categorical overviews | Display reduction only; downloadable TIFFs retain native results |
| Outlines | Native climate-input footprint | Raster coverage contour, not a surveyed or administrative coastline |

The full results occupy approximately 2.7 MB with lossless compression. Their
small file size reflects large contiguous categorical regions, not a reduction
of the native grid. A fine climate boundary within a solar pixel can change
KGPV class, but does not imply an independent solar observation there.

## Periods, units and missing data

Climate covers **1979–2013**; the downloaded 2019 Spain solar archive covers
**1994–2018**. This is an **exploratory mixed-period application**, not a
common-baseline climate map or reproduction of the published worldwide map.
The application calls the cellwise classifier and records both periods. It does
not bypass or weaken `map_kgpv`'s requirement for a shared climatological baseline.

Temperature and precipitation are stored as encoded unsigned integers. The
reader masks raw nodata first, applies each band's scale and offset, converts
temperature from K to °C, and reads precipitation in kg/m²/month as mm/month.
The solar file already contains **annual GHI in kWh/m²/year**; multiplying by
365 again would be incorrect. Source months, variables, units and aligned grids
are validated before processing. No thresholds are refitted to the Canaries.

Gray indicates land without all required inputs. The source temperature
footprint contains 310,567,549 pixels, including **5,833,740 unclassified pixels**.
Checks found missing summer rainfall values among these gaps; no gap filling or
coastal extrapolation is applied. Pixels outside the source footprint are
transparent over the ocean background. The example is a climate classification,
not a site-specific yield, shading, soiling or snow-loss prediction.

## Run the offline gallery

From a checkout of the repository:

```bash
uv sync --locked --all-packages --group docs
cd examples/analysis
uv run python plot_kgpv_canary.py
```

The gallery verifies map and sample SHA-256 hashes, then recomputes eleven
sample-site classifications. It makes no network requests. The same inputs and
derived maps accompany the downloadable gallery script.

## Recreate the native maps

From the repository root:

```bash
# Inspect the download size without fetching data.
uv run python scripts/prepare_kgpv_canary.py --plan-only

# Fetch 24 monthly climate COGs and one solar archive, then process all islands.
uv run python scripts/prepare_kgpv_canary.py

# Reuse the cache and process only Tenerife, with smaller working tiles.
uv run python scripts/prepare_kgpv_canary.py --islands tenerife --tile-size 256
```

Initial downloads total approximately **1.92 GB** and need no account. The raw
cache is `artifacts/canary-kgpv/raw`; outputs default to
`artifacts/canary-kgpv/native`. `--cache` and `--output` select other locations.
All 24 climate files are still required for an island subset. The processor
reads small tiles rather than materializing the roughly four-billion-cell
climate source grid. Two downloads can run concurrently; `--workers 1` selects
sequential acquisition. In a proxy-dependent environment, explicitly pass
`--use-environment-proxy` to use `HTTPS_PROXY`.

Allowed `--islands` values are `el_hierro`, `la_palma`, `la_gomera`, `tenerife`,
`gran_canaria`, `fuerteventura` (including Lobos), and `lanzarote` (including
La Graciosa and the Chinijo islets). Multiple selections can follow the flag.
These windows use the source raster mask rather than clipping to a coarser
country polygon. The separate [country mapping guide](country-mapping.md)
covers administrative shapefile contours and selected-country grids.

The supplied provenance pins source SHA-256 hashes, sizes and canonical public
URLs. Cache corruption and changed provider bytes fail validation. The solar
download follows only the provider's exact Spain object redirect; temporary
signed URLs are not saved. Provider outages or changed archives may require a
reviewed source update. Acquisition and analysis tests use offline fixtures.

## Reuse the GeoTIFFs

Open `kgpv_canary_<island>.tif` in QGIS or Rasterio. Each file is EPSG:4326:

| Band | Values |
| --- | --- |
| 1 | KGPV class IDs 1–12 in the existing `ZONE_CODES` order; 0 unclassified |
| 2 | January temperature's native valid footprint: 1 within coverage, 0 outside |

Both bands have nodata 0. Band 2 distinguishes missing land inputs from ocean;
it is a source coverage mask, not an independent land survey. Embedded tags
record zone codes, both periods, resolution limits and source attribution.
Overviews use nearest-neighbour classes. Keep the accompanying
`kgpv_canary_provenance.json` when sharing or adapting the derived rasters.

## References and attribution

The primary scientific reference remains **Ascencio Vásquez (2021), doctoral
thesis**, with the KGPV classification of **Ascencio-Vásquez, Brecl and Topič
(2019)**. See the [bibliography](references.md) for the method and datasets.

- **Karger et al. (2025), CHELSACanaryClim-climatologies**, v1.0,
  [DOI 10.16904/envidat.692](https://doi.org/10.16904/envidat.692), CC0 1.0.
- **Patiño et al. (2023)**, *Spatial resolution impacts projected plant responses
  to climate change on topographically complex islands*,
  [DOI 10.1111/ddi.13757](https://doi.org/10.1111/ddi.13757).
- **Global Solar Atlas 2.0**: data obtained from the free web application
  developed and operated by **Solargis s.r.o.** on behalf of the **World Bank
  Group**, utilizing Solargis data, with funding from **ESMAP**.
  Source: [globalsolaratlas.info](https://globalsolaratlas.info).
  Solar data use CC BY 4.0 with the provider's additional mediation/arbitration
  terms; the complete downloaded license is retained in the provenance.

Changes comprise regional extraction, nearest-cell sampling and derived KGPV
classification. Provider endorsement is not implied. This example also uses
[Rasterio](https://rasterio.readthedocs.io/en/stable/) for windowed raster I/O,
nearest-neighbour reprojection and categorical overviews.
