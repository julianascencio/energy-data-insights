# Terrain connectors and native resolution

Four public connectors retrieve numeric elevation data without an API key.
SRTM's finest public product is **1 arcsecond, approximately 30 m**, not 1 m.
Angular spacing varies in ground distance with latitude; pixel size is not
vertical accuracy. The alternatives below retain their own grids and datums.

| Connector | Product / native sampling | Coverage and surface | Height reference |
|---|---|---|---|
| `SRTMClient` | SRTMGL1, 1 arcsecond; 3601 × 3601 HGT posts per tile | Land between 56° S and 60° N, subject to tile availability; radar surface with void filling | EGM96 orthometric metres |
| `CopernicusDEMClient` | AWS GLO-30 Public COG; 1 arcsecond north–south, wider longitude spacing poleward | Broad land coverage with missing/restricted tiles; DSM includes vegetation and buildings | EGM2008 orthometric metres |
| `IGNTerrainClient` | IGN Spain WCS, 5 m projected grid | Mainland/Balearic and Canary grids; bare-earth DTM, actual valid mask applies | Spanish official orthometric heights; mainland and island references vary |
| `USGS3DEPClient` | Project-based 3DEP 1 m DEM | Available US lidar projects; not complete nationwide coverage; bare-earth DTM | NAVD88 in CONUS; inspect project metadata elsewhere |

IGN's separate CNIG catalogue also lists 2 m and 0.5 m regional products.
The WCS connector specifically retrieves its advertised 5 m grid; it does not
claim those finer products. The USGS connector explicitly selects project-based
1 m data, not the newer seamless 1 m dataset. Copernicus EEA-10 is subject to
separate access conditions and is not downloaded by the public GLO-30 client.

## Get SRTM at its finest public sampling

```python
from pathlib import Path
from energy_data_retrieval.sources.srtm import SRTM_HOSTS, SRTM_SOURCE, SRTMClient
from energy_data_retrieval.terrain import read_terrain, write_terrain_window
from energy_data_retrieval.transport import HTTPClient

site = {"latitude": 28.25, "longitude": -16.65}
bounds = (-16.655, 28.245, -16.645, 28.255)  # west, south, east, north
with HTTPClient(SRTM_HOSTS) as http:
    tile, request = SRTMClient(http).download_tile(Path("terrain"), **site)
window = read_terrain(tile, SRTM_SOURCE, bounds_wgs84=bounds)
print(window.sample(**site))  # nearest native cell, metres; None for nodata
write_terrain_window(window, Path("terrain/site_srtm.tif"))
print(request.endpoint, request.sha256)  # original downloaded ZIP provenance
```

The source is NASA SRTMGL1 distributed by ESA's public SNAP auxiliary mirror.
The connector verifies a 3601 × 3601 signed big-endian HGT member, then writes a
GeoTIFF with the correct post-centred transform. Shared tile boundary posts
are retained. The `-32768` void code becomes missing when read, while zero
and negative elevations remain valid. The TIFF remains in EGM96; SNAP's
optional conversion to ellipsoidal heights is not applied.

The default read budget is four million pixels. Request a site window instead
of loading a whole degree tile. `degree_tiles(bounds)` lists intersecting tile
origins, with a default 16-tile limit; download each explicitly. A window that
crosses a file boundary raises an error. This API does not silently clip,
reproject, mosaic or choose a coarser dataset. Split antimeridian areas before
requesting tiles.

## Look up all terrain metadata for one site

```python
from dataclasses import asdict
from energy_data_retrieval.terrain import describe_terrain

metadata = describe_terrain(tile, SRTM_SOURCE)
site_terrain = {
    "site": site,
    "elevation_m": window.sample(**site),
    "terrain_metadata": asdict(metadata),
    "request": asdict(request),
    "window_bounds_native": window.metadata.bounds,
}
print(site_terrain)
```

This records product identity, surface type, vertical datum, reference IDs,
horizontal CRS and units, native pixel spacing, shape, bounds, raw nodata,
scale/offset, download URL, acquisition-of-response time, byte count and hash.
`read_terrain` applies the scale/offset **after** masking and returns metres
with NaN for missing cells. Its metadata describes the decoded window;
`describe_terrain` describes the original file. A NaN nodata sentinel is recorded
as the string `"NaN"` so metadata can be serialized as strict JSON. For USGS also retain the full
`product.metadata`, including project description, dates, extent and metadata
URLs. Publication dates and retrieval timestamps are not survey dates.

Join this dictionary to the same coordinates used in the
[single-site climate lookup](site-climate.md). Climate classification, terrain
elevation and degradation scenarios are different pieces of evidence; elevation
does not determine a climate class or a measured degradation rate.

Use the metadata to:

1. Check actual coverage and valid cells before using the value in a model.
2. Choose a surface: a bare-earth DTM for ground slope or drainage; a DSM when
   above-ground objects matter, while checking whether their size is resolved.
3. Use terrain elevation to check site coordinates and model inputs. A 30 m
   surface cannot resolve roof edges, row spacing or individual small obstacles.
4. Obtain a much wider surrounding area for terrain-horizon/shading work and
   compare with the [PVGIS horizon connector](pvgis.md). The small gallery crops
   are a resolution demonstration, not a complete horizon or shading model.
5. Project angular grids appropriately before computing slope or distances.
   Preserve the original grid, survey/project metadata and processing choices.
6. Convert heights to a common vertical reference before comparing sources.
   EGM96, EGM2008 and NAVD88 are not interchangeable. No connector performs a
   vertical-datum transformation, and differences are not terrain change.

## Copernicus GLO-30 Public

```python
from energy_data_retrieval.sources.copernicus_dem import (
    COPERNICUS_DEM_HOSTS,
    COPERNICUS_DEM_SOURCE,
    CopernicusDEMClient,
)

with HTTPClient(COPERNICUS_DEM_HOSTS) as http:
    client = CopernicusDEMClient(http)
    available = client.available_tiles()  # provider tileList.txt and request record
    cop_tile, cop_request = client.download_tile(Path("terrain"), **site)
cop_window = read_terrain(cop_tile, COPERNICUS_DEM_SOURCE, bounds_wgs84=bounds)
```

The bucket encodes GLO-30 with `COG_10`: this means 1.0 arcsecond, not 10 metres.
The distributed COG removes the duplicate southern/eastern posts and has 3600
rows. Longitude spacing increases poleward; inspect the transform rather than
assuming a square 30 m grid. Reads use native pixels, not overview images.
Missing tiles raise errors and are not filled with GLO-90 or assumed zero.
The original file stays unchanged, so its request checksum remains verifiable.

## IGN Spain: numeric 5 m WCS terrain

```python
from energy_data_retrieval.sources.ign_terrain import (
    IGN_TERRAIN_HOSTS,
    IGN_TERRAIN_SOURCE,
    IGNTerrainClient,
)

with HTTPClient(IGN_TERRAIN_HOSTS) as http:
    client = IGNTerrainClient(http)
    capabilities = client.capabilities()
    description = client.describe("canaries")
    ign_file, ign_request = client.download_window(
        Path("terrain"),
        bounds,
        region="canaries",
        maximum_pixels=1_000_000,
    )
ign_window = read_terrain(ign_file, IGN_TERRAIN_SOURCE)
```

Use `region="peninsula"` for the mainland/Balearic grid (EPSG:25830) or
`"canaries"` for REGCAN95 / UTM zone 28N (EPSG:4083). The client reads
DescribeCoverage, aligns the enclosing request to that native grid, sends two
repeated `SUBSET` parameters, and verifies the returned CRS, 5 m spacing and
extent. It requests no scaling or output reprojection. The provenance sidecar
retains both the description and data requests, including the original XML.

The live DescribeCoverage response labels its range with generic radiance
units, despite describing the official elevation product. The connector
retains that XML and uses the documented MDT metre units. The tested TIFF
response is signed int16 in whole metres and declares no nodata value; do not
infer missing values from zero or claim sub-metre vertical precision. Higher
horizontal sampling does not guarantee a newer survey or finer height precision.

## USGS: find available 1 m projects, then select explicitly

```python
from energy_data_retrieval.sources.usgs_3dep import (
    USGS_3DEP_HOSTS,
    USGS_3DEP_SOURCE,
    USGS3DEPClient,
)
from energy_data_retrieval.transport import HTTPConfig

colorado = (-105.350, 39.996, -105.347, 39.999)
with HTTPClient(
    USGS_3DEP_HOSTS,
    config=HTTPConfig(maximum_response_bytes=512 * 1024 * 1024),
) as http:
    client = USGS3DEPClient(http)
    results = client.search(colorado, maximum_items=100)
    for product in results.products:
        print(product.source_id, product.title, product.size_bytes, product.metadata)
    # This is the explicit project captured by the example, not a newest-first rule.
    selected = next(p for p in results.products if p.source_id == "69c20ed7b66b01d6ebf33c9a")
    usgs_file, usgs_request = client.download_product(Path("terrain"), selected)
usgs_window = read_terrain(usgs_file, USGS_3DEP_SOURCE, bounds_wgs84=colorado)
print(usgs_window.sample(39.9975, -105.3485))
```

Searches retain all matching projects up to a declared budget and fail on
truncation, duplicate pages or a changing total. A catalogue bounding box can
intersect a site while the pixels there are nodata. Review project metadata
and test the site; do not automatically take the first result. Tiles can be
hundreds of megabytes. The byte budget is checked before download and the
advertised size and optional expected SHA-256 are verified. Downloads are
restricted to official 3DEP 1 m GeoTIFF paths, with no arbitrary URL following.

## Reproducible maps and source attribution

The [offline terrain gallery](https://julianascencio.github.io/energy-data-insights/auto_examples/connectors/plot_terrain_sources.html)
plots three real Tenerife crops and a separate Colorado 1 m crop. Each retains
native pixels, source/datum metadata and hashes in `terrain_provenance.json`.
The downloadable bundle runs without network access. To refresh intentionally:

```bash
uv run python scripts/prepare_terrain_samples.py --download-directory /absolute/path/outside/repository
```

The script uses an explicit USGS project ID and stops if it disappears. It does
not substitute another project or synthesize elevations. Source snapshots
support the example only; they do not establish current universal coverage.

References: [NASA/USGS SRTM](https://doi.org/10.5066/F7PR7TFT),
[ESA SRTM mirror](https://step.esa.int/auxdata/dem/SRTMGL1/),
[Copernicus product and licence](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM),
[AWS COG layout](https://copernicus-dem-30m.s3.amazonaws.com/readme.html),
[IGN elevation products](https://centrodedescargas.cnig.es/CentroDescargas/modelos-digitales-elevaciones),
[IGN WCS](https://servicios.idee.es/wcs-inspire/mdt?SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCapabilities),
[USGS 3DEP](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services),
[USGS National Map API](https://www.usgs.gov/the-national-map-data-delivery/gis-data-download).

Copernicus crop attribution: produced using Copernicus WorldDEM-30 © DLR e.V.
2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS
by the European Union and ESA; all rights reserved. IGN: contains geographic
information from IGN Spain, MDT WCS, CC BY 4.0. USGS 3DEP: public domain.
