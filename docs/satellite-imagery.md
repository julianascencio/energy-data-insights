# Satellite imagery through Orbital PV

`sources.orbitalpv_imagery` reuses **Orbital PV's actual Sentinel-2 connector,
native COG reader, GeoTIFF writer and checksum-verified offline loader**. It adds
bounded discovery in the Maxar/Vantor Open Data archive and resolution-aware
selection. The connector returns Orbital PV `GroundImage` objects directly.

[Run the illustrated example](https://julianascencio.github.io/energy-data-insights/auto_examples/connectors/plot_satellite_imagery.html)
or [download the complete offline bundle](https://julianascencio.github.io/energy-data-insights/auto_examples/connectors/plot_satellite_imagery.html).

## Install

```bash
uv sync --locked --all-packages --extra imagery --group docs --python 3.13
```

For an installed distribution, use `uv pip install 'energy-data-retrieval[imagery]'`
under Python 3.13+. The optional dependency pins Orbital PV to commit
`498c47e182f9f0e1b0f0d40bc3125ef7c2110a05`: the earlier PyPI 0.7.0 artifact does
not contain these ground-imagery APIs. This Git dependency needs Git and GitHub
access at installation. Core Energy Data Insights still supports Python 3.12;
only the Orbital PV image operations require 3.13. Metadata inspection and Maxar
catalogue search work without the optional dependency.

## Which resolution is available?

| Source / asset | Native detail and output grid | Coverage and access |
| --- | --- | --- |
| Sentinel-2 `visual`, red, green, blue, NIR | 10 m bands; RGB is a rendered display product | Broad land coverage, dated scenes and native masks; public Earth Search |
| Sentinel-2 SWIR / `scl` | 20 m; classification is categorical | Same scene search; do not upsample and claim 10 m native detail |
| WorldView / GeoEye `pan_analytic` | Scene-specific sub-metre panchromatic sampling; **0.33 m declared GSD and ~0.323 m raster spacing in the supplied crop** | Selected disaster events in Maxar Open Data; **CC BY-NC 4.0** at program/event level |
| WorldView `visual` | Provider-rendered pansharpened RGB; sample has ~0.305 m grid and **0.33 m conservative detail bound** | Same limited event archive; 8-bit colour is not calibrated reflectance |
| Maxar `ms_analytic` | Native multispectral grid, coarser than pan; unknown native GSD stays unknown unless declared for that asset | Scene-level pan GSD is never assigned to native multispectral bands |

“Finest” means the smallest conservative sampling bound **within the specified
provider, event, area, dates and asset type**. It is not the highest resolution
available worldwide or a guarantee of usable clear pixels. The bound is the
larger of declared native GSD and delivered grid spacing, with the pan grid
also checked for pansharpened RGB. GSD is not measured resolving power or
geolocation accuracy. Oversampling, JPEG previews and sharpening do not add
native detail. Cloud, shadow, off-nadir geometry and the native validity mask
still matter. A search matches intersecting footprints; the reader requires
the requested window to fit in the selected raster and may contain nodata.

For arbitrary sites, licensed commercial sub-metre imagery may be required.
This connector does not purchase imagery or imply access to commercial archives.
It never silently substitutes an aerial photograph for a satellite image.

## Find the finest matching public scene and read native pixels

```python
from dataclasses import asdict
from energy_data_retrieval.sources.orbitalpv_imagery import (
    IMAGERY_HOSTS,
    OrbitalPVImageryClient,
    describe_asset,
    select_finest,
    load_satellite_image,
)
from energy_data_retrieval.transport import HTTPClient

bbox = (-118.1220, 34.2100, -118.1205, 34.2115)  # west, south, east, north
with HTTPClient(IMAGERY_HOSTS) as http:
    client = OrbitalPVImageryClient(http)
    events = client.events()  # inspect current event IDs; no global coverage claim
    found = client.search_maxar(
        "WildFires-LosAngeles-Jan-2025",
        bbox,
        time_min="2025-01-08",
        time_max="2025-01-09",
        maximum_documents=512,
        maximum_items=500,
    )
    scene = select_finest(found, asset="pan_analytic", maximum_detail_m=0.35)
    print(asdict(describe_asset(scene, "pan_analytic")))
    image = client.read_image(scene, bbox, asset="pan_analytic", maximum_samples=2_000_000)
    image.save_geotiff("site-pan.tif")
    colour = client.read_image(scene, bbox, asset="visual")
    colour.save_geotiff("site-rgb.tif")

saved = load_satellite_image("site-pan.tif")  # verifies SHA-256 and metadata
print(saved.data.shape, saved.crs, saved.transform, saved.bounds)
print(saved.item_metadata["properties"])  # acquisition, platform, GSD, licence provenance
print(saved.asset_metadata)  # bands, scale/offset, projection, native shape
print(saved.data.count() / saved.data.size)  # valid fraction; not a cloud-free fraction
```

Maxar traversal retains complete STAC item/asset metadata, provider URLs and a
receipt for every catalogue document. Relative links are resolved within the
selected public event. Exhausted document/item budgets raise an error, rather
than presenting partial results as the finest selection. Optional
`acquisition_ids=("104001009C64B300",)` further narrows the search and its claim.
No matching scene or no known resolution meeting the requested limit raises
an explicit error. Review clouds/validity and other candidates before use.

## Broader coverage: one site's Sentinel-2 metadata and pixels

```python
bbox = (-16.447, 28.192, -16.439, 28.198)  # Icor area, Tenerife
with HTTPClient(IMAGERY_HOSTS) as http:
    client = OrbitalPVImageryClient(http)
    found = client.search_sentinel(
        bbox,
        time_min="2026-08-01",
        time_max="2026-08-06",
        max_cloud_cover=10,
        max_items=100,
        cache_path="site-scenes.json",
    )
    scene = select_finest(found, asset="visual")
    print(scene["properties"])  # complete acquisition and quality metadata
    print(scene["assets"])  # available bands and their native metadata
    red = client.read_image(scene, bbox, asset="red")
    scl = client.read_image(scene, bbox, asset="scl")
    reflectance = red.reflectance()  # explicit scale and offset; masks retained
    red.save_geotiff("site-red.tif")
```

Orbital PV implements query-bound, hashed search caches; keep the JSON and its
`.meta.json` together. A capped Sentinel search is marked incomplete and
`select_finest` rejects it by default. Expand the cap or explicitly choose to
rank the partial selection with `allow_incomplete=True`. Equal-detail ties use
acquisition timestamp then item ID; this is not a “latest or clearest” policy.
`max_cloud_cover` is scene-wide. Inspect SCL locally: 0 nodata, 1 defective,
2 dark/topographic shadow, 3 cloud shadow, 4 vegetation, 5 non-vegetated,
6 water, 7 unclassified, 8/9 cloud, 10 cirrus, 11 snow/ice. Align categorical
grids explicitly with nearest-neighbour sampling if a later analysis needs a
common grid; the retrieval connector performs no such resampling.

## Use the imagery in a PV study

1. Keep the original TIFF, its checksum sidecar, full STAC metadata and the
   search scope. Record dates, CRS, pixel spacing, nodata, cloud state and rights.
2. Overlay verified plant or roof polygons to inspect visible layout, access
   roads and surrounding features. A pixel trace needs positional uncertainty
   and independent validation; do not infer individual modules from 10 m data.
3. Combine with the [terrain connector](terrain.md) after explicit CRS/grid
   alignment. Satellite RGB is not an elevation model. DEMs provide terrain
   context; buildings and vegetation can require finer surface information.
4. Use [PVGIS](pvgis.md) for irradiance and modelled yield, and the
   [site climate profile](site-climate.md) for climate metadata and stressors.
   Observed capacity, meter output and dated maintenance evidence remain
   necessary to validate energy performance and [degradation](degradation.md).

`maximum_samples` limits bands × rows × columns before the pixel read.
GDAL can transfer complete compressed COG blocks, so this is not a strict
network-byte budget. No whole-scene downloads, resizing, artificial
super-resolution, sharpening or implicit cloud removal are performed.

## Provenance and reproduction

Run the explicit live script into an external directory (fresh destination):

```bash
uv run --no-sync python scripts/prepare_satellite_imagery_samples.py \
  --output-directory /tmp/imagery-samples
```

The committed small crops, full STAC sidecars and search manifest let the
gallery run offline. TIFF checksums, masks and native grid metadata are
validated by the actual Orbital PV loader. The panchromatic gallery stretch
only changes display contrast, not stored pixel values. These are real source
crops, not synthetic illustrations; catalogue and transport unit tests use
clearly synthetic fixtures.

**Attribution:** Orbital PV (pinned source); Copernicus Sentinel data (2026),
processed by ESA and distributed by Element 84 Earth Search; © Maxar/Vantor
Open Data Program. The Maxar program/event declares CC BY-NC 4.0, while its
generic acquisition collection declares “proprietary”. Both original
declarations are retained in `edi:open_data`; the connector does not rewrite
them or grant commercial rights. Follow the provider's Open Data terms and
retain attribution when sharing the supplied noncommercial crops.

Sources: [Orbital PV](https://github.com/julianascencio/orbital-pv),
[Earth Search](https://github.com/Element84/earth-search),
[Sentinel-2 documentation](https://documentation.dataspace.copernicus.eu/Data/SentinelMissions/Sentinel2.html),
[Maxar Open Data](https://xpress-docs.maxar.com/OpenData/OpenData_intro.htm)
and [archive catalogue](https://maxar-opendata.s3.amazonaws.com/events/catalog.json).
