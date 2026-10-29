# Data retrieval

Country-neutral acquisition infrastructure with one folder per source. The Chile
adapter uses stable CEN identities. Weather adapters can be reused in another
country with a different site registry.

| Source folder | Implemented products |
| --- | --- |
| `sources/cen` | Public registry, authenticated actual generation, public archive downloads and historical bulk/Qlik export import |
| `sources/open_meteo` | Explicit ERA5 historical weather or archived ECMWF IFS forecasts |
| `sources/earthmover_era5` | Native ERA5 tiles from a pinned public Icechunk snapshot; optional dependencies |
| `sources/station` | Explicitly mapped measured hourly weather from preserved CSV/XLSX exports |

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

### Historical CEN bulk and Qlik exports

`cen-history` imports a **preserved export with an explicit source contract**.
It supports CSV, read-only XLSX, or one explicitly selected CSV/XLSX member of a
ZIP archive. This is a configurable adapter, not a claim to reproduce a particular
archived production release or to have ingested all historical Chilean records.

```bash
uv run energy-retrieve cen-history \
  --input inputs/generation-export.csv \
  --mapping inputs/verified-historical-units.csv \
  --schema Data-retrieval/examples/cen_qlik.toml \
  --output data/history/qlik-hourly.parquet

uv run energy-retrieve cen-history \
  --input inputs/historical-workbook.xlsx \
  --mapping inputs/verified-historical-units.csv \
  --schema Data-retrieval/examples/cen_bulk_wide.toml \
  --output data/history/bulk-hourly.parquet
```

Example column names and sheet names are **illustrative**. Inspect the selected
provider file and set its actual headers, sheet, preamble length, separator and
time conventions before use. All TOML keys map to `HistorySchema`. Declare:

| Setting | Contract |
| --- | --- |
| `identity_column` | Exact exported unit/name key; no fuzzy or nearest-name matching |
| `timestamp_column` | ISO timestamp labels; alternatively use `date_column` plus `hour_column` or `hour_columns` |
| `hour_columns` | Exactly 24 named columns, ordered by hour; expanded only when the source actually is hourly |
| `hour_origin` | Numbering of 24 intervals: `1` means 1–24, `0` means 0–23 |
| `timestamp_label` | `start` or `end`; for date/hour records, the first interval is 00:00–01:00 civil time |
| `timezone` | Timezone for offset-free labels; explicit UTC offsets resolve repeated Chilean hours |
| `energy_unit` | `MWh`/`kWh` for hourly energy, or `MW`/`kW` for mean power over one elapsed hour |
| `measurement_basis` | `gross`, `net` or `unspecified`; never inferred from source names |
| `decimal_places` | Optional source precision declaration, recorded without re-rounding observations |
| `technology_column`, `pv_technology_values` | Optional exact PV filters with explicit accepted labels; do not include CSP or BESS as PV |

The mapping CSV requires `source_id,unit_id,site_id`. It declares a complete,
verified unit roster for this historical period. Several source aliases may refer
to the same unit. Equal duplicate unit-hours are counted once, including equal
missing values; conflicting values fail for reconciliation, even if one is null.
Unknown keys fail rather than being attached to a similarly named plant. Retired
sites can remain in the mapping and analysis registry. Mapping validity across
upgrades and ownership/name changes must be established per source period.

Hourly bulk products and daily historical products remain distinct. Daily SING
values cannot enter this hourly adapter, and no hourly profile is synthesized.
Wide 24-column days that hit a daylight-saving ambiguity or nonexistent civil
hour are rejected: reshape and resolve them using the provider's actual UTC
offset/fold evidence. Arbitrarily shifting a clock label or deleting an hour
would change the energy accounting. Offset-bearing long records can represent
both occurrences of a repeated hour correctly.

Current Qlik exports and historical bulk data can have different precision and
gross/net definitions. Keep those regimes in separate output partitions until
they have been reconciled. This importer neither chooses an automatic source
precedence nor rounds a precise bulk observation to match a coarser Qlik value.
The [CEN Qlik download interface](https://qap-prd.coordinador.cl/ext/extensions/mashup_Generacion_Real_Descargable/mashup_Generacion_Real_Descargable.html)
may require a permitted browser/session. The import command works with an export
obtained through authorized access; it does not bypass Qlik authorization or
claim that anonymous live extraction is available.

A known **public**, query-free CEN archive URL can be downloaded separately:

```bash
uv run energy-retrieve cen-download \
  --url "$CEN_PUBLIC_EXPORT_URL" --output inputs/historical-workbook.xlsx
```

Allowed hosts are `www.coordinador.cl`, `coordinador.cl` and `sic.coordinador.cl`.
No archive URLs are guessed or generated. Redirects, 401/403 responses and URLs
containing credentials/query strings stop; retrieve session-protected exports
through the authorized provider interface. `--sha256` can supply an independent
expected digest. Downloads stream to disk with a 512 MiB default size limit,
finite retries and atomic file publication. A completed file and its download
manifest are reused only after checking source URL, byte size and SHA-256. A
failed transfer restarts from byte zero; it never appends bytes from a potentially
changed archive. An incomplete or tampered checkpoint requires inspection.

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

### Measured weather-station exports

`station-import` uses actual station observations as a separate source. Its
mapping CSV requires `station_id,site_id`. One station can be explicitly assigned
to several sites; each site uses one station in a given import. There is no
automatic nearest-station selection or implied claim that a sensor represents
the plant's conditions.

```bash
uv run energy-retrieve station-import \
  --input inputs/station-hourly.csv \
  --mapping inputs/station-sites.csv \
  --schema Data-retrieval/examples/station.toml \
  --output data/station/weather.parquet
```

Configure actual header names, UTC/civil labels and units in `StationSchema`.
Only one-hour means enter the hourly GHI/temperature/wind contract. Accumulated
GHI in Wh/m² over one hour becomes mean W/m²; kWh/m² is multiplied by 1000.
Kelvin/Fahrenheit become Celsius and km/h becomes m/s. Gust metadata explicitly
records whether it is an hourly maximum or an instantaneous end observation.
POA irradiance cannot be relabeled as GHI, and instantaneous/5-minute source
records require a separate, justified resampling step before import.

Absent optional weather observations remain null. Reported zeros and negative
observations are preserved for subsequent quality checks; duplicates must agree.
No modeled replacement, calibration claim, interpolation or forward fill is
automatic. The output records station identity, source label, exact source and
mapping hashes, units and interval conventions; sensor quality and spatial
representativeness are explicitly unconfirmed. Use these products in
`energy-chile prepare` only after checking the source's measurement quality.

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

The [repository reference catalogue](../docs/references.md) and
[BibTeX bibliography](../references.bib) provide the verified thesis, method and
provider citations. For station exports, set `source_label` to the actual
provider/dataset and retain its attribution with the acquired source; the adapter
does not invent a citation or licence for an unnamed station.

- [CEN actual-generation API endpoint](https://sipub.api.coordinador.cl/generacion-real/v3/findByDate)
- [CEN public registry endpoint](https://api-infotecnica.coordinador.cl/v1/centrales-sin-filtrar/extended/)
- [CEN reports and statistics](https://www.coordinador.cl/reportes-y-estadisticas/)
- [Open-Meteo Historical Forecast API](https://open-meteo.com/en/docs/historical-forecast-api)
- [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)
- [Open-Meteo hourly variable definitions](https://open-meteo.com/en/docs)
- [Earthmover Icechunk ERA5 public catalogue and attribution](https://registry.opendata.aws/earthmover-era5/)
- [ERA5 single levels, DOI 10.24381/cds.adbb2d47](https://doi.org/10.24381/cds.adbb2d47)

The existing API endpoint schemas and interval conventions are adapted from the
prior Chile study's acquisition scripts, with explicit validation and no embedded
data or credentials. Historical export and measured-station adapters use explicit
contracts and synthetic fixtures. Live source availability, a complete historical
release, historical identity validity and metrological quality require separate
evidence; offline tests do not establish them.
