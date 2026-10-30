# Map one country or selected countries

Choose country names/codes, make a finer regional grid and clip its mapped
values to real country contours. The helpers work with the repository's
soiling/snow, KGPV, degradation and other rectilinear latitude/longitude maps.
The [offline country gallery](https://julianascencio.github.io/energy-data-insights/auto_examples/plot_country_risk.html)
demonstrates Austria plus Slovenia, followed by Slovenia alone, using real
2023 inputs sampled at 0.5°.

## Acquire the country shapefile

The new source adapter downloads Natural Earth Admin 0 country boundaries,
retains their shapefile companions and records version/checksum provenance.
Natural Earth is public domain and uses de facto boundaries by default.
Country codes follow the source's administrative units, which need not equal
sovereign states or every ISO territory. Other boundary datasets can be loaded
locally when a different delineation is required.

```python
from pathlib import Path
from energy_data_retrieval.transport import HTTPClient
from energy_data_retrieval.sources.natural_earth import (
    NATURAL_EARTH_HOSTS,
    NaturalEarthClient,
)

with HTTPClient(allowed_hosts=NATURAL_EARTH_HOSTS) as http:
    download = NaturalEarthClient(http).download_countries(
        Path("artifacts/boundaries"), scale="10m"
    )
print(download.shapefile, download.manifest)
```

| Scale option | Nominal map scale | Typical use |
| --- | --- | --- |
| `10m` | 1:10 million | Detailed country views; default |
| `50m` | 1:50 million | Broader regional views |
| `110m` | 1:110 million | Small worldwide maps |

**`10m` does not mean 10-metre accuracy.** The official download URL can change
with releases. To require the same archive, pass a saved `expected_sha256`.
The adapter verifies cached downloads, bounds expanded size and reads only the
expected flat archive members. Keep `.shp`, `.shx`, `.dbf`, `.prj` and `.cpg`
together. Source archives and generated shapefiles belong under `artifacts/`;
the offline gallery keeps only a small attributed GeoJSON subset.

## Select countries and create a grid

```python
from energy_methods.country_boundaries import load_country_boundaries
from energy_methods.country_mapping import country_grid

spain = load_country_boundaries(download.shapefile, "Spain")
iberia = load_country_boundaries(download.shapefile, ["ESP", "PRT"])
grid = country_grid(iberia, resolution=0.25)
```

Names and codes match exactly, ignoring case and surrounding spaces. Natural
Earth's `ADM0_A3`/`ADMIN` are the default identifier/name fields; ISO A2/A3,
their `_EH` variants, `NAME` and `NAME_LONG` are aliases when present. Duplicate
selectors collapse to one country; unknown or ambiguous selectors raise an
error. For another source use `code_field` and `name_field` explicitly.

All polygon parts, islands and holes remain in the selection. For Spain this
includes the Canaries and Balearics; a default Spain/Portugal extent also
includes their source-defined offshore parts. To focus on mainland Iberia,
make the spatial restriction explicit:

```python
grid = country_grid(
    iberia,
    resolution=0.25,
    bounds=(-10, 35.5, 4.5, 44.5),  # west, south, east, north
)
```

Grid edges align to -180° longitude and -90° latitude. Spacing is in degrees
and must divide 180 (for example 1, 0.5, 0.25, 0.1). Allocation is capped at
250,000 cells by default. `grid.country_mask` marks cells intersecting selected
polygons, including partial coastal/border cells; their centres can be outside
the country. This is an acquisition mask, not a land-fraction estimate.

## Mask, plot and export existing results

The following assumes `risk` is a two-dimensional `xarray.DataArray` on regular
`lat`/`lon` axes. Continuous fields may use NaN; integer class maps should pass
their missing-data code explicitly, such as `nodata=0`.

```python
import matplotlib.pyplot as plt
from energy_methods.country_boundaries import write_country_boundaries
from energy_methods.country_mapping import (
    clip_country_grid,
    plot_country_map,
    write_country_geojson,
)

selected = clip_country_grid(risk, iberia, nodata=0)
fig, ax = plt.subplots()
mesh = plot_country_map(selected, iberia, ax=ax, nodata=0)
fig.colorbar(mesh, ax=ax)
write_country_boundaries(iberia, Path("artifacts/iberia.shp"))
write_country_geojson(selected, iberia, Path("artifacts/risk.geojson"), nodata=0)
```

| Function | Behavior |
| --- | --- |
| `load_country_boundaries` | Reads `.shp` or GeoJSON and selects names/codes |
| `country_grid` | Builds a bounded grid and polygon-intersection mask |
| `country_mask` | Boolean mask using cell `intersects` or `center` membership |
| `clip_country_grid` | Masks raster values and trims only outer empty rows/columns |
| `plot_country_map` | Draws flat-shaded values clipped to the contours, with country borders |
| `write_country_boundaries` | Exports selected contours as `.shp` plus companions or GeoJSON |
| `write_country_geojson` | Exports actual country-cell polygon intersections |

Raster masking retains each partial cell's numerical value. Plotting and
GeoJSON export clip its visible/geometric footprint to the polygon. They do
not smooth or interpolate class IDs. NaN/class-0 cells remain missing, including
inside the country. GeoJSON export omits missing and line-only intersections.
`clip_country_grid` also accepts additional year/month dimensions; select a
two-dimensional layer before plotting/exporting.

Coordinates normalize to EPSG:4326 longitude/latitude. Shapefiles need a `.prj`
or explicit `crs`; projected inputs are transformed with x/y axis order fixed.
RFC 7946 GeoJSON defaults to WGS84. Invalid geometry fails rather than being
silently repaired. Already split antimeridian polygons are supported, but their
default longitude extent may span the world; use separate bounded views for
islands on opposite sides. Unsplit rings crossing the antimeridian are rejected.

The plots use geographic axes, not a metric or equal-area projection. Do not
estimate country areas by summing whole intersecting cells; use geodesic or
equal-area calculations on the clipped polygons. Small islands can be drawn
from the vector boundaries even when source weather remains coarse.

## Retrieve finer soiling/snow inputs

First inspect the acquisition plan; this downloads boundaries if needed but
makes no weather requests:

```bash
uv run python scripts/prepare_weather_risk_example.py \
  --countries AUT SVN --resolution 0.5 --plan-only
```

Prepare the actual inputs and selected shapefiles:

```bash
uv run python scripts/prepare_weather_risk_example.py \
  --countries AUT SVN --resolution 0.5 --year 2023 \
  --output artifacts/country-risk --export-shp
```

Use `--boundaries path/to/countries.shp` to reuse a local dataset, or
`--boundary-scale 50m` to choose a less detailed Natural Earth source.
`--bounds WEST SOUTH EAST NORTH` restricts the acquisition area. Names with
spaces need shell quotes. The default limit is 500 weather sites; exceed it
only by explicitly setting `--maximum-sites`, subject to provider access terms.
Public requests use bounded workers, pacing and caching. Use
`--use-environment-proxy` when the configured HTTPS proxy is required.

Country outputs use `country_risk_*` filenames and do not overwrite the
worldwide `weather_risk_*` fixtures. The documented example has 83 sampled
cells intersecting Austria/Slovenia on a 0.5° grid; its source manifest gives
all requested and selected coordinates, full-year counts, checksums and dates.
One of the 83 snow samples is unavailable and remains missing. Very large
modelled snow-depth sums in some Alpine cells warrant source-quality review;
the repository retains them visibly instead of silently clipping the inputs.
Copy `examples/plot_country_risk.py` alongside the country output files and run
it there for the Austria/Slovenia example. For other countries, change the
selectors and displayed extents in the example, or use the generic functions
above.

**Finer boundaries, finer sampling and finer source data are different.**
NASA POWER AOD550 has 1° source support. The country workflow queries each
needed 1° cell centre once and explicitly reuses it at finer target points.
ERA5-Land snow uses nearest native model cells. A 0.25° grid does not magically
create 0.25° aerosol information. Retrieve suitable higher-resolution weather
where available; do not upsample the 15° global fixture and describe it as new
information. Scientific equations and limitations remain those in the
[soiling/snow guide](soiling-snow.md).

Made with [Natural Earth](https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-0-countries/).
The [bibliography](references.md) also records Shapely, PyProj and PyShp;
NASA POWER/CERES and Open-Meteo/Copernicus ERA5-Land remain the weather sources.
