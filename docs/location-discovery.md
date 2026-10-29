# Find stations and gridded datasets from coordinates

The `discover` command accepts one latitude/longitude point, searches the
integrated station catalogues, ranks nearby candidates and describes the
gridded products that can be considered for that location. It returns machine
readable JSON with source identities, distance, coverage evidence, access
requirements, retrieval parameters and citations.

## One command

```bash
uv run energy-retrieve discover \
  --latitude 28.4775 --longitude -16.3294 \
  --radius-km 100 --limit 20 \
  --output data/discovery/tenerife.json
```

Coordinates are decimal degrees, with latitude first. Latitude must be in
`[-90, 90]` and longitude in `[-180, 180]`. The default search radius is 100 km
and the default result limit is 20 stations **across all selected providers**.
The command prints the full JSON when `--output` is omitted. A saved snapshot
is never overwritten; choose a new filename to refresh the search.

Fresh station searches use the existing bounded HTTP transport. Public requests
can use `--cache-directory data/discovery/cache`. AEMET requires
`AEMET_API_KEY` for a fresh catalogue. Missing credentials and individual
provider failures appear in `source_status`, while successful results remain
available. The top-level `partial` status means at least one requested source
could not be checked; it does not mean all stations were searched successfully.

### Select sources or reuse local catalogues

Repeat `--station-source` to choose specific providers:

```bash
uv run energy-retrieve discover \
  --latitude 28.4775 --longitude -16.3294 --radius-km 150 \
  --station-source noaa --station-source bsrn
```

Use an existing station catalogue and its manifest/required sidecars for an
offline lookup:

```bash
uv run energy-retrieve discover \
  --latitude 28.4775 --longitude -16.3294 --radius-km 100 \
  --station-source aemet \
  --catalogue aemet=data/aemet/stations.parquet \
  --offline --output data/discovery/tenerife-offline.json
```

Local catalogues retain their original bounding box and country filter. A
filtered Canary Islands catalogue is never described as a global inventory.
The source scope remains visible even when it produces no matches. Checksums
and required source artifacts are verified before a saved catalogue is reused.
An invalid local snapshot is reported explicitly and does not silently trigger
a replacement network acquisition.

The optional `--grid-only` mode skips station catalogues. With no data probe,
grid discovery uses the documented product contracts and makes no requests:

```bash
uv run energy-retrieve discover \
  --latitude -23.65 --longitude -70.40 --grid-only
```

## Station results

Each returned station keeps its native identifier and catalogue fields and
adds `source`, `distance_km`, a one-based `rank`, and retrieval hints. Catalogue
coordinates that are missing, nonnumeric or outside valid ranges are excluded
from ranking and counted. Source records are not merged based on similar names
or coordinates.

| Source | Geographic discovery | What the catalogue establishes |
| --- | --- | --- |
| NOAA GHCNh | Current NCEI station inventory | Identity and location; station-specific date and variable availability need an observation request |
| AEMET | OpenData daily-climate station inventory | Identity and location; historical daily and recent-observation availability remain separate checks |
| DWD CDC | Hourly solar station catalogue | Identity, location and published date extent; the extent does not establish continuous observations |
| NOAA SURFRAD | Supported network catalogue | Current station metadata and installation information; historical file headers can contain different coordinates |
| BSRN | [Official PANGAEA station catalogue](https://dataportals.pangaea.de/bsrn/stations?format=textfile) | Event identity, coordinates and event time metadata; monthly data availability requires the existing DOI search and validation |

The BSRN catalogue is linked from the [official BSRN station overview](https://bsrn.awi.de/stations/overview/).
Catalogue codes that the current monthly adapter cannot retrieve are retained
with an explicit unsupported-retrieval indicator. SURFRAD participates in BSRN,
so the two sources can contain overlapping observations; discovery keeps both
identities visible.

Distances use a haversine calculation on a sphere with mean radius
6371.0088 km. The method handles the antimeridian and poles and ignores altitude,
terrain, exposure and microclimate. Equal-distance ties are resolved by source,
station ID and original row order. Geographic proximity alone does not establish
a suitable PV reference station. See the [BSRN guidance on station representativeness](https://bsrn.awi.de/stations/overview/).

## Gridded dataset results

The registry describes only the four already integrated offerings. It does not
add a new data provider or claim that a catalogue entry proves usable data at
every date and grid cell.

| Dataset | Geographic evidence | Retrieval behavior |
| --- | --- | --- |
| Open-Meteo ERA5 | Documented global coverage | Explicit ERA5 hourly output, nearest cell, elevation adjustment disabled |
| Open-Meteo archived IFS | Documented global model coverage | Explicit `ecmwf_ifs` archived forecast product; model vintage, start and resolution require product-specific evidence |
| Earthmover native ERA5 | Documented global ERA5 grid | Uses the repository's pinned Icechunk snapshot; that snapshot's actual time bounds and cell data need inspection |
| CMIP6 | Depends on the explicitly selected dataset and native grid | Requires model, experiment, ensemble member, table, variable, grid and resolved version |

Each row records supported source variables, normalized output variables,
spatial/temporal descriptions, known coverage bounds, access requirements,
retrieval hints, reference IDs and status. Unknown bounds stay unknown. Grid
cell coordinates remain null until they are returned by an actual response;
they are not fabricated by rounding the requested point.

Source documentation: [Open-Meteo historical weather](https://open-meteo.com/en/docs/historical-weather-api),
[Open-Meteo historical forecasts](https://open-meteo.com/en/docs/historical-forecast-api),
and the [Earthmover ERA5 registry](https://registry.opendata.aws/earthmover-era5/).
The [CMIP6 source contract](../data-retrieval/README.md#cmip6-climate-model-data)
describes the supported ESGF selection and plan workflow.

### Verify a small sample at the point

```bash
uv run energy-retrieve discover \
  --latitude 28.4775 --longitude -16.3294 \
  --grid-only --probe-date 2025-01-01 \
  --output data/discovery/tenerife-grid-sample.json
```

This calls the two existing Open-Meteo clients for one requested UTC day. Their
established interval-end convention also requests the following day for boundary
samples, then normalizes only the requested day. The result records the actual
selected cell, per-variable non-null and missing counts, sample completeness
and the safe request record/hash. An all-missing sample and a provider failure
remain distinguishable. A verified sample establishes evidence for that date
only; it does not certify the full historical period. `--probe-date` cannot be
combined with `--offline`.

Native ERA5 and CMIP6 are not implicitly downloaded by this probe. Native ERA5
requires its optional dependencies and pinned-snapshot retrieval. For CMIP6,
first create an explicit plan using `cmip6-search`, then attach it:

```bash
uv run energy-retrieve discover \
  --latitude -23.65 --longitude -70.40 --grid-only \
  --cmip6-plan data/cmip6/plan.json \
  --output data/discovery/chile-cmip6.json
```

The result contains the selected datasets and native file metadata, with
`point_coverage_unverified`. Latitude and longitude are not silently passed as
a CMIP6 catalogue filter or used to assume a regular grid. Inspect the native
coordinates, masks, calendar, units and time bounds before selecting a point
or converting output for a performance study.

## Python API

```python
from energy_data_retrieval.discovery import DISCOVERY_HOSTS, find_sources
from energy_data_retrieval.transport import HTTPClient, HTTPConfig

with HTTPClient(
    DISCOVERY_HOSTS,
    config=HTTPConfig(minimum_interval_seconds=1.6),
) as http:
    result = find_sources(
        28.4775,
        -16.3294,
        radius_km=100,
        limit=20,
        http=http,
    )

print(result.stations[["source", "station_id", "distance_km", "rank"]])
print(result.grids)
snapshot = result.as_dict()
```

Passing `http=None` enables only local catalogue lookup and documented grid
metadata. `catalogues={"aemet": Path("data/aemet/stations.parquet")}` supplies a
saved catalogue. `station_sources=()` skips station sources.

For a user-supplied station inventory, call the pure distance method directly:

```python
from energy_data_retrieval.spatial import nearby_stations

# stations is a DataFrame with station_id, latitude and longitude columns.
nearest = nearby_stations(stations, 28.4775, -16.3294, radius_km=100, limit=10)
```

This preserves all supplied columns and attributes and performs no I/O. Its
`spatial_search` attributes record invalid-coordinate counts, the number within
the radius, the returned count and whether the limit truncated the result.

## Reproducibility and scientific attribution

Discovery JSON includes its query, creation time, source-specific status and
scope, safe request records, distance assumptions and references. Its
`discovery_sha256` hashes the complete JSON object before that checksum field
is added, using Python's `json.dumps(..., sort_keys=True, allow_nan=False)`.
Missing values are serialized as JSON nulls.

The preferred scientific citation remains Julián Andrés Ascencio Vásquez's
doctoral thesis. Provider references accompany the discovery evidence. The
complete bibliography is in [references](references.md). Discovery does not
change observations, infer station-to-plant mappings, apply quality filtering,
resample data, or merge modeled and measured values.
