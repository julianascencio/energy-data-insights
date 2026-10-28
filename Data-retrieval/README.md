# Data retrieval

Country-neutral acquisition infrastructure with one folder per source. The Chile
adapter uses stable CEN identities. Weather adapters can be reused in another
country with a different site registry.

| Source folder | Implemented products |
| --- | --- |
| `sources/cen` | Public plant registry and authenticated, paginated actual generation |
| `sources/open_meteo` | Explicit ERA5 historical weather or archived ECMWF IFS forecasts |
| `sources/earthmover_era5` | Native ERA5 tiles from a pinned public Icechunk snapshot; optional dependencies |

All acquisition is explicit. Importing a module or running the tests makes no
network requests. Test fixtures are synthetic and are not evidence of live API
availability, authorization or complete Chilean generation coverage.

## Install and use

From the repository root:

```bash
uv sync --all-packages
uv run energy-retrieve --help
uv run energy-retrieve cen-registry --output data/registry.parquet
```

Set `CEN_USER_KEY` in your environment using your secret manager. It is the user
key accepted by the CEN API. Do not commit it or pass it on the command line.

```bash
uv run energy-retrieve cen-generation \
  --start 2026-10-01 --end 2026-10-27 \
  --output data/cen-units
```

This writes **unit-level** Parquet partitions and their provenance. To produce
site-level energy, supply a verified roster with `site_id,unit_id` columns valid
for the entire requested period:

```bash
uv run energy-retrieve cen-generation \
  --start 2026-10-01 --end 2026-10-27 \
  --unit-roster inputs/verified-unit-roster.csv \
  --output data/cen-sites
```

CEN's API returns mean power in `gen_real_mw`. Each accepted row represents a real
one-hour interval, giving `actual_mwh = gen_real_mw × 1 h`. Source timestamps are
Chile civil interval starts. They become UTC timestamps after explicit timezone
resolution. Nonexistent DST labels are excluded and audited; ambiguous labels
fail until the source provides disambiguating evidence. No clock shift is guessed.

A site-hour is complete only if **every expected unit has a non-null value**.
Incomplete hours retain `reported_mwh` but set `actual_mwh` to null. An unexpected
unit fails roster validation. Exact duplicate unit-hours are removed; conflicting
ones fail. Missing site IDs are quarantined; they are never guessed from names.
A historical phase or changed unit roster requires a separately valid roster.

The registry's `potencia_maxima` is retained as `reported_maximum_power_mw`.
It is not automatically assigned to DC or AC nameplate capacity. The normalized
metadata leaves both capacity fields null and `dc_capacity_qualified` false.

### Weather

A site CSV or Parquet file must contain `site_id,latitude,longitude`. Choose the
weather product explicitly. Both are **modelled weather**, not station observations.

```bash
uv run energy-retrieve open-meteo \
  --sites inputs/sites.csv --start 2026-07-28 --end 2026-10-27 \
  --product ifs --workers 2 --chunk-days 31 \
  --cache-directory data/public-cache --output data/ifs

uv run energy-retrieve open-meteo \
  --sites inputs/sites.csv --start 2020-01-01 --end 2020-12-31 \
  --product era5 --output data/era5
```

The API is asked for UTC Unix timestamps, m/s and Celsius, nearest-cell selection,
and no elevation adjustment. It requests an extra day to obtain interval-end
samples, then checks and crops the exact requested UTC intervals. Missing source
values remain null. Missing time labels, incomplete endpoint coverage or changed
units fail rather than being silently filled.

| Output | Alignment to the interval beginning at `timestamp` |
| --- | --- |
| `ghi_wm2` | API preceding-hour mean at `timestamp + 1 h` |
| `temperature_c` | Mean of instantaneous start and end temperatures |
| `wind_speed_ms` | Mean of instantaneous start and end wind speeds |
| `gust_ms`, IFS forecast | API preceding-hour maximum at interval end |
| `gust_ms`, Open-Meteo ERA5 archive | Instantaneous end sample, according to the archive's variable definition |

The distinction for gust is preserved in metadata; an archive end sample is not
relabeled as an hourly maximum. An endpoint mean of temperature or wind is a
declared approximation, not a directly measured hourly mean.

If using an Open-Meteo customer plan, set `OPEN_METEO_API_KEY`. The adapter selects
the matching `customer-` host and keeps authenticated responses out of the public
cache. Confirm the provider's applicable usage terms before operational acquisition.

### Native ERA5 history

The native adapter retains the source used for the earlier historical study. It
pins snapshot `TZ2KX6A24CJ5DG17T7MG`; availability is checked against that snapshot,
not inferred from a current catalogue's headline end date.

```bash
uv sync --all-packages --extra era5-native
uv run energy-retrieve era5-native \
  --sites inputs/sites.csv --start 1940-01-01 --end 2025-12-31 \
  --snapshot TZ2KX6A24CJ5DG17T7MG --output data/era5-native
```

The source `single/temporal` layout is validated as `(8736, 12, 12)`. Acquisition
reads only intersecting tiles and bounded time blocks. Sites sharing a tile reuse
the five loaded variables. Verified existing output partitions are checked before
remote weather arrays are read. Each block includes its end sample, preserving
continuity across partition boundaries. Dataset metadata still has to be opened
to resolve the pinned snapshot, native grid and coverage.

Kelvin becomes Celsius; accumulated `ssrd` in J/m² is divided by 3600 for GHI in
W/m²; `hypot(u10,v10)` gives instantaneous wind speed. GHI and `fg10` retain their
source accumulation/max interval at the end label; temperature and wind use
endpoint means. The snapshot must contain both endpoints of every requested
hour. No fallback to a different ERA5 vintage or forecast product is automatic.
The Icechunk object's S3 transport is separate from the REST transport below;
its optional native acquisition is covered by mocked tile tests, not live S3 tests.

## Resource limits and restart semantics

- REST reads have a timeout, maximum decoded response size, bounded attempts and
  rate spacing. HTTP 429 and transient server/transport errors are retried with
  exponential backoff and capped `Retry-After`; 401/403 and redirects stop.
- Only approved HTTPS source hosts are accepted. Redirects are disabled.
- At most `workers` tasks are submitted at a time, with a maximum of eight.
  Generation is retrieved one day at a time and weather in bounded date chunks.
- Public request caching has deterministic keys, an expiry and stored-content
  checksum validation. Authenticated responses bypass it completely.
- Credential parameters, encoded credential echoes and HTTP client logs are
  redacted. No error body or credential-bearing exception URL is propagated.
- Parquet uses Zstandard compression. A partition and its JSON provenance are
  published atomically as individual files, with SHA-256 and request fingerprints.
  A crash between these two file publications is detected on restart. Inspect an
  incomplete pair or choose a new output directory; it is not silently accepted.
- Re-running an identical completed acquisition reuses its verified local
  snapshot. To intentionally retrieve a revised provider vintage, use a new output
  directory. Do not overwrite a prior study's data silently.

The manifests record UTC times, exact request semantics, response identities,
selected grid coordinates, units and alignment. Secrets are supplied separately
and never enter request fingerprints. Complete API pagination does not imply
complete national coverage or complete metering at every site.

## Programmatic interfaces

```python
from datetime import date
from energy_data_retrieval.sources.open_meteo import OpenMeteoClient, Site, WeatherProduct
from energy_data_retrieval.sources.open_meteo.client import OPEN_METEO_HOSTS
from energy_data_retrieval.transport import HTTPClient

with HTTPClient(OPEN_METEO_HOSTS) as transport:
    client = OpenMeteoClient(transport, WeatherProduct.ERA5)
    for chunk in client.iter_weather(
        [Site("site-1", -34.4, -70.9)], date(2025, 1, 1), date(2025, 12, 31)
    ):
        # Persist/process one chunk at a time; do not collect the entire history.
        print(chunk.site.site_id, len(chunk.frame))
```

The canonical interval columns are `site_id` (string), `timestamp` (UTC-aware
interval start), and `duration_hours`. Site generation adds `actual_mwh` and
`generation_complete`; weather adds `ghi_wm2,temperature_c,wind_speed_ms,gust_ms`.
Feed site-aggregated generation and matching weather into the
`energy_analysis.chile_fleet` workflow in `Analysis/`.

## Source and method references

- [CEN actual-generation API endpoint](https://sipub.api.coordinador.cl/generacion-real/v3/findByDate)
- [CEN public registry endpoint](https://api-infotecnica.coordinador.cl/v1/centrales-sin-filtrar/extended/)
- [CEN reports and statistics](https://www.coordinador.cl/reportes-y-estadisticas/)
- [Open-Meteo Historical Forecast API](https://open-meteo.com/en/docs/historical-forecast-api)
- [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)
- [Open-Meteo hourly variable definitions](https://open-meteo.com/en/docs)
- [Earthmover Icechunk ERA5 public catalogue and attribution](https://registry.opendata.aws/earthmover-era5/)
- [ERA5 single levels, DOI 10.24381/cds.adbb2d47](https://doi.org/10.24381/cds.adbb2d47)

The endpoint schemas and interval conventions are adapted from the actual prior
Chile study's acquisition scripts, with explicit validation and no embedded data
or credentials. Bulk CEN spreadsheet/Qlik extraction and measured station adapters
are not implemented by this package yet; they are not silently represented by
modelled weather or this paginated API.
