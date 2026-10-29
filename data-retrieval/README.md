# Data retrieval

Country-neutral acquisition infrastructure with one lowercase folder per source.
The Chile adapter uses stable CEN identities. Weather adapters can be reused in
another country with a different site registry. Climate-model retrieval preserves
the provider's native files and metadata for subsequent climate analyses.

| Source folder | Implemented products |
| --- | --- |
| `sources/cen` | Public registry, authenticated actual generation, public archive downloads and historical bulk/Qlik export import |
| `sources/open_meteo` | Explicit ERA5 historical weather or archived ECMWF IFS forecasts |
| `sources/earthmover_era5` | Native ERA5 tiles from a pinned public Icechunk snapshot; optional dependencies |
| `sources/station` | Explicitly mapped measured hourly weather from preserved CSV/XLSX exports |
| `sources/bsrn` | Public PANGAEA DOI discovery and BSRN monthly radiation observations with source metadata and qualifiers |
| `sources/noaa` | Current GHCNh station catalogue and native station/year weather observations from NOAA NCEI |
| `sources/aemet` | Authenticated station inventory, historical daily climate and recent station observations from AEMET OpenData |
| `sources/dwd` | DWD CDC hourly solar station catalogue and native radiation archives |
| `sources/surfrad` | NOAA SURFRAD station catalogue and native daily radiation/weather observations |
| `sources/cmip6` | ESGF STAC discovery, versioned retrieval plans and verified native CMIP6 NetCDF downloads |

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
  --schema data-retrieval/examples/cen_qlik.toml \
  --output data/history/qlik-hourly.parquet

uv run energy-retrieve cen-history \
  --input inputs/historical-workbook.xlsx \
  --mapping inputs/verified-historical-units.csv \
  --schema data-retrieval/examples/cen_bulk_wide.toml \
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

### CMIP6 climate-model data

The CMIP6 provider uses the current public ESGF STAC API and the package's existing
HTTP transport. It needs no additional package dependencies or account for the
supported public endpoints. Discovery and file transfer are separate commands:
first save a bounded retrieval plan, then download the files identified by that
plan. The default discovery index is `https://discovery.east.esgf.io`; select
`--index west` explicitly for `https://discovery.west.esgf.io`. The client does not
switch indices automatically.

Specify one exact model, experiment, ensemble member, CMOR table, variable and
grid for each plan. Preserve their official spelling and case, such as
`CanESM5`, `Amon` and `sfcWind`. This request selects monthly surface shortwave
radiation for the SSP2-4.5 experiment:

```bash
uv run energy-retrieve cmip6-search \
  --model CanESM5 --experiment ssp245 --member r1i1p1f1 \
  --table Amon --variable rsds --grid gn \
  --start-year 2030 --end-year 2050 \
  --output data/cmip6/rsds-plan.json

uv run energy-retrieve cmip6-download \
  --plan data/cmip6/rsds-plan.json --output data/cmip6/rsds \
  --maximum-file-bytes 536870912 --maximum-total-bytes 2147483648
```

The search downloads metadata only. Inspect the plan's resolved dataset version,
file count, advertised sizes, URLs and citation information before transferring
data. Add `--version 20190429` to request that specific catalogue version; without
it the search resolves the latest available version and pins that result in the
saved plan. Repeat discovery into a new plan when deliberately updating a study.

Supply both `--start-year` and `--end-year`, or neither. A year range selects
**whole native files that overlap those years**. It does not trim NetCDF content
or establish complete coverage of every requested time step. On 29 October 2026,
the public catalogue returned one `v20190429` file for the example above:
`rsds_Amon_CanESM5_ssp245_r1i1p1f1_gn_201501-210012.nc`, advertised as 28,407,606
bytes. Its entire 2015–2100 range is downloaded even though the selection is
2030–2050. Availability depends on the selected index and current holdings.

For a small fixed field, this selection was also verified against the catalogue
on that date, with one advertised 51,899-byte file. Fixed fields do not take a
year range:

```bash
uv run energy-retrieve cmip6-search \
  --model CanESM5 --experiment historical --member r1i1p1f1 \
  --table fx --variable areacella --grid gn --version 20190429 \
  --output data/cmip6/areacella-plan.json

uv run energy-retrieve cmip6-download \
  --plan data/cmip6/areacella-plan.json --output data/cmip6/areacella \
  --maximum-file-bytes 1048576 --maximum-total-bytes 1048576
```

`--page-size`, `--maximum-datasets` and `--maximum-files` bound discovery.
Search reads fresh catalogue metadata; the saved plan provides the frozen
snapshot for subsequent downloads. `--request-interval` controls spacing between
requests. Downloads stream to disk, verify the
advertised byte size and full SHA-256 multihash, and record acquisition provenance.
Unsupported checksum algorithms fail explicitly. Existing downloads are reused
only when their manifest, source identity, size and hash still agree; failed
transfers restart from byte zero. Conflicting or incomplete local outputs are
not overwritten. Downloads accept only approved HTTPS hosts. An additional
provider hostname can be enabled with `--allow-host` after verifying its provenance.

Generated directories use lowercase names derived from dataset hashes. Original
provider filenames, official dataset identifiers, STAC metadata, citation links
and license statements remain intact. The saved mapping connects each local
file to its original model, experiment, member, table, variable, grid and version.

Variables useful for energy studies include the following; definitions and units
come from the [official CMIP6 Amon table](https://github.com/PCMDI/cmip6-cmor-tables/blob/main/Tables/CMIP6_Amon.json).

| Variable | Quantity | Native unit |
| --- | --- | --- |
| `rsds` | Downward shortwave radiation at the surface | W m⁻² |
| `tas` | Near-surface air temperature | K |
| `sfcWind` | Near-surface wind speed | m s⁻¹ |
| `uas`, `vas` | Eastward and northward near-surface wind components | m s⁻¹ |
| `pr` | Precipitation flux | kg m⁻² s⁻¹ |

The NetCDF calendar, time bounds, cell methods, grid and units remain authoritative.
This provider downloads native climate simulations without spatial/date subsetting,
regridding, bias adjustment, ensemble aggregation or conversion to hourly weather.
Monthly radiation and non-Gregorian time axes therefore cannot be passed directly
to the Chile hourly performance workflow. Keep climate projections distinct from
measured weather and reanalysis.

ESGF is migrating its catalogue, and upstream documentation identifies incorrect
member identifiers in some republished CMIP6 records. The provider preserves
and checks the requested identity; an empty result is not evidence that no such
data exist anywhere in CMIP6. Consult the [current ESGF access guidance](https://esgf-pyclient.readthedocs.io/en/latest/)
and [CMIP6 migration notes](https://intake-esgf.readthedocs.io/en/latest/).
The legacy Solr API is deprecated.

Cite [Eyring et al. (2016)](https://doi.org/10.5194/gmd-9-1937-2016) for CMIP6 and
[O'Neill et al. (2016)](https://doi.org/10.5194/gmd-9-3461-2016) when using
ScenarioMIP experiments. Also cite the actual model/experiment datasets and
their versions using the preserved provider citation links. The
[CMIP6 terms](https://pcmdi.llnl.gov/CMIP6/TermsOfUse/TermsOfUse6-2.html) direct users
to the [per-model license inventory](https://wcrp-cmip.github.io/CMIP6_CVs/docs/CMIP6_source_id_licenses.html);
a STAC catalogue-record license alone does not establish the underlying data
license. These references are included in the repository's
[thesis-first bibliography](../docs/references.md).

### BSRN radiation stations

BSRN observations are available programmatically through PANGAEA's
[documented DOI export interface](https://wiki.pangaea.de/wiki/Data_Access_and_Reuse).
The provider retrieves a public dataset's tab-separated data and JSON-LD
metadata over HTTPS. It needs no account or additional package dependencies.
The supported contract is one station/month of basic radiation measurements
(logical record 0100), with supported additional radiation fields from logical
record 0300 when bundled in that dataset.

Discover candidates for an explicit three-letter station code and month, then
choose the actual dataset DOI:

```bash
uv run energy-retrieve bsrn-search \
  --station cab --year 2009 --month 6 \
  --maximum-results 100 --page-size 20 \
  --output data/bsrn/cab-2009-06-search.json

uv run energy-retrieve bsrn-dataset \
  --doi 10.1594/PANGAEA.725795 \
  --station cab --year 2009 --month 6 \
  --maximum-rows 50000 \
  --output data/bsrn/cab_2009-06.parquet
```

The DOI identifies [Knap's Cabauw June 2009 dataset](https://doi.pangaea.de/10.1594/PANGAEA.725795).
The example was retrieved and parsed on 29 October 2026: 43,200 native minute
records, including reported negative and missing values. This establishes that
example's retrieval; it does not certify every station/month's completeness or
measurement quality. The search uses the current internal endpoint used by
[PANGAEA's official Python client](https://pangaea-data-publisher.github.io/pangaeapy/_modules/pangaeapy/panquery.html),
which PANGAEA does not promise as a stable public REST API. Results are DOI
candidates; the dataset command independently checks the BSRN project, station,
month, source schema, citation and license. Direct DOI retrieval does not depend
on discovery continuing to work.

Native UTC minute labels remain unchanged. Radiation outputs retain source names
such as `swd_wm2`, `dir_wm2`, `dif_wm2` and `lwd_wm2`; published standard
deviations, minima and maxima remain separate columns. Supported temperature,
relative humidity and pressure fields are retained when present. Every original
column also remains under `source:<original header>`. Numeric
[PANGAEA qualifiers](https://wiki.pangaea.de/wiki/Quality_flag), including `?`,
`/`, `*`, `#`, `>` and `<`, are retained beside their numeric payload in
`<column>_qualifier`. A flagged number is not an unqualified accepted observation.
Empty numeric fields become null; reported negative values are preserved.
Unsupported fields, units or qualifier formats fail explicitly.

The [BSRN archive guidance](https://bsrn.awi.de/data/data-retrieval-via-pangaea/)
states that detailed BSRN quality-check flags are not archived. These imports
therefore do not claim completed scientific quality control. They do not clip,
fill, interpolate, shift time labels, aggregate to hours or assign a station to
a PV site. Minute observations and their statistics require an explicit time
and quality contract before use in an hourly performance analysis.

Alongside the Parquet file, retrieval saves `.parquet.source.tsv`,
`.parquet.metadata.json` and a `.parquet.json` provenance manifest. These retain
the source export, JSON-LD metadata, dataset citation, release conditions and
hashes. Repeating an identical acquisition reuses that local snapshot only after
verification; changed, incomplete or conflicting outputs stop. A deliberate
new provider snapshot requires a new output path. Discovery and a new dataset
acquisition read fresh metadata. `--request-interval` controls request spacing;
`--maximum-response-bytes` defaults to 67,108,864 bytes (64 MiB), and
`--maximum-rows` defaults to 50,000 for one month.

Cite [Driemel et al. (2018)](https://doi.org/10.5194/essd-10-1491-2018), the actual
monthly dataset and its station collection, using the preserved source citation.
For this example those are the monthly DOI above and
[Knap's Cabauw collection](https://doi.pangaea.de/10.1594/PANGAEA.940531).
Retain each dataset's own license and [BSRN release conditions](https://bsrn.awi.de/data/conditions-of-data-release/).
The scientific and example citations are included in the shared bibliography.

### NOAA GHCNh weather stations

The NOAA source uses the current **Global Historical Climatology Network hourly
(GHCNh), version 1.1.0**, from NCEI. NOAA's
[service transition notice](https://www.nesdis.noaa.gov/news/service-location-change-integrated-surface-data-global-hourly)
reports that ISD stopped receiving updates after 24 August 2025 and directs users
to GHCNh. This provider retrieves the current
[station catalogue](https://www.ncei.noaa.gov/oa/global-historical-climatology-network/hourly/doc/ghcnh-station-list.csv)
and native annual station files over public HTTPS. It needs no API key or
additional dependencies. It does not switch to legacy ISD.

Find station candidates using the catalogue's two-letter ISO country code and,
optionally, a bounding box. This example selects catalogued stations in a Canary
Islands bounding box; it does not establish their variable or date coverage:

```bash
uv run energy-retrieve noaa-stations \
  --country-code ES --bbox -18 27 -13 30 \
  --output data/noaa/stations.parquet
```

The box order is **west, south, east, north**. `--country-code` filters the actual
`ISO_CODE` field; the distinct FIPS country prefix in GHCN station IDs is retained
as `country_fips` and must not be used as an ISO-code substitute. The catalogue
preserves station names, coordinates and source metadata. GHCNh station IDs are
case-sensitive and can contain lowercase letters and underscores: use the exact
catalogue ID without changing its case. Invalid coordinate pairs retain their
original `LATITUDE` and `LONGITUDE` fields, but normalized coordinates are null
and `coordinates_valid` is false; coordinates are not swapped or inferred.
Inspect the station and period before choosing it; no nearest-station assignment
is automatic.

The separate observation example below uses the verified LaGuardia identifier
`USW00014732` and its public 2026 file. An actual study should specify its own
selected GHCNh station ID:

```bash
uv run energy-retrieve noaa-observations \
  --station USW00014732 --start 2026-01-01 --end 2026-01-02 \
  --output data/noaa/observations
```

The provider acquires the **whole native station/year PSV file**, then selects
observations within the inclusive requested UTC dates. It checks every source
row's station and year; a short date request does not reduce the annual transfer
size. A request spanning years becomes bounded annual partitions. Current NCEI
REST subset responses tested during implementation omitted station, time and
quality fields, so this adapter uses the native files that retain those fields.
The [official format documentation](https://www.ncei.noaa.gov/oa/global-historical-climatology-network/hourly/doc/ghcnh_DOCUMENTATION.pdf)
defines the native layout and source-dependent codes.

All original columns are retained as strings, including the 329 columns in the
verified current format. Added columns expose the exact UTC `timestamp`, station
identity, coordinates and available measurements such as `temperature_c`,
`dewpoint_c`, `wind_speed_ms`, `gust_ms`, `station_pressure_hpa`,
`sea_level_pressure_hpa` and `visibility_km`. Native values are already in the
documented physical units, including °C, m/s and hPa; old ISD integer-tenths
scaling is not applied. Each variable's measurement, quality, report-type,
source and source-station codes remain available for interpretation.

Blank numeric fields become null. Flagged observations, reported zeros and
negative values remain present; no quality code is assumed to mean a universal
pass. Exact duplicate records are counted once, conflicting records with the
same station/time/report/source identity fail, and distinct reports at the same
time remain separate. Subhourly and synoptic observation times are not shifted
to an hourly grid. Reported gusts remain short-duration peak observations and
are not relabeled as hourly maxima. The provider does not manufacture GHI,
resample, fill gaps, mask observations or establish station representativeness.

Outputs use lowercase station directories under `data/noaa/observations/`,
with the requested dates in each filename. Directory names distinguish source
IDs that differ only in case; records and provenance retain the exact original
station ID.
Each Parquet partition has a `.parquet.json` provenance manifest and a
`.source.psv` sidecar containing the complete original annual export. Source
and output hashes are checked before reusing an identical completed snapshot.
Use a new output location to acquire a revised source vintage; incomplete or
conflicting files stop instead of being overwritten.

`--maximum-years` defaults to 100 annual partitions and `--maximum-rows` to
600,000 rows per native annual response, before date filtering. The station
catalogue is bounded by `--maximum-stations`, default 100,000.
`--maximum-response-bytes` defaults to 134,217,728 bytes (128 MiB), and
`--request-interval` controls request spacing. These limits bound acquisition;
they do not promise data for every requested hour or variable.

Cite [Menne et al.'s GHCNh dataset](https://doi.org/10.25921/jp3d-3v19) and record
the station IDs, dates, format version, access time and retained source hashes.
The dataset and current documentation are in the shared bibliography, alongside
the repository's main PhD thesis citation.

### AEMET OpenData stations

The AEMET source implements three distinct products through the current
[OpenData specification](https://opendata.aemet.es/AEMET_OpenData_specification.json):
the daily-climate station inventory, historical daily station climate, and a
recent conventional-observation snapshot covering the API's rolling last
12 hours. The recent endpoint does not provide arbitrary historical hourly data.

Obtain your own key from [AEMET OpenData](https://opendata.aemet.es/centrodedescargas/inicio)
and export it as `AEMET_API_KEY` in your shell or job runner. The CLI does not load
`.env` automatically. Credentials are sent in the API's `api_key` header and
never enter source manifests, fingerprints, public caches or logs. AEMET's
[current notices](https://opendata.aemet.es/centrodedescargas/novedades) explain
the retirement of nonexpiring keys and the three-month validity of new keys.

```bash
uv run energy-retrieve aemet-stations \
  --bbox -18 27 -13 30 --output data/aemet/stations.parquet

uv run energy-retrieve aemet-daily \
  --station C447A --start 2025-01-01 --end 2025-01-31 \
  --output data/aemet/daily

uv run energy-retrieve aemet-recent \
  --station C447A --output data/aemet/recent/c447a_snapshot.parquet
```

Use an exact uppercase station ID from the relevant AEMET product. A catalogue
entry alone does not establish that a station has both daily and recent data.
The server's `estado` is validated even when the HTTP status is 200. Returned
data and metadata URLs must remain on the approved HTTPS service; redirects,
unapproved hosts and credential-bearing URLs fail. Each response is bounded.

Daily requests are split into at most 31-day partitions, with an overall
`--maximum-days` default of 3,660. Daily date labels remain dates; no synthetic
midnight UTC observation is created. Original values, units, time fields and
metadata are retained. Locale decimal commas are interpreted explicitly;
precipitation traces remain distinguishable from missing values and reported
zero precipitation. No hourly resampling or quality-pass assumption is made.
Normalized measurement units must agree with the returned field metadata, and
all raw fields remain available. Recent `fint` labels become UTC timestamps only
when their metadata explicitly identifies UTC. Daily variable periods follow
their source definitions; they are not assumed to share one midnight-to-midnight
measurement window.

Outputs include Parquet, provenance and canonical JSON snapshots of the source
payload and metadata. Canonical JSON preserves the returned values and fields;
it is not a byte-for-byte copy of the HTTP encoding. Verified completed outputs
can be reused without a key or network request. Use a new output path to refresh
the rolling recent-observation snapshot or to retrieve revised historical data.
JSON decoding prefers valid Unicode JSON; only when that fails can an explicitly
declared ISO-8859-1 or ISO-8859-15 charset be used. The decoding policy is recorded
with the snapshot, preserving accented station names and unit symbols.
The default `--request-interval` is 1.6 seconds, with configurable response and
row bounds. Respect AEMET's current product-specific access limits.

### DWD hourly solar stations

The DWD source retrieves the public CDC
[hourly solar catalogue and station archives](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/solar/).
The supported product contains global and diffuse solar radiation, downward
longwave radiation where available, sunshine duration and associated metadata.
It needs no key. Other DWD weather products require their own source contracts.

```bash
uv run energy-retrieve dwd-stations \
  --output data/dwd/stations.parquet

uv run energy-retrieve dwd-solar \
  --station 01048 --start 2025-01-01 --end 2025-01-02 \
  --output data/dwd/dresden_2025-01-01_2025-01-02.parquet
```

Station IDs have five digits, including leading zeros. Discovery optionally
accepts `--bbox WEST SOUTH EAST NORTH`. Retrieval downloads the whole selected
station ZIP, then selects rows by the requested inclusive UTC dates. The original
archive includes station history, instrument and parameter metadata; a short
date selection does not reduce the archive transfer.

The reader validates the ZIP structure and the documented parameter contract.
`MESS_DATUM` can contain minute offsets and remains the original UTC label;
`MESS_DATUM_WOZ` is local true solar time and is retained separately. Hourly
radiation totals remain **J/cm²**, following the
[official format description](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/solar/DESCRIPTION_obsgermany_climate_hourly_solar_en.pdf).
No interval boundary, UTC rounding or W/m² conversion is inferred. Original
quality codes and fields remain available; the documented missing sentinel is
kept distinct from a reported zero or a valid negative measurement.

Saved Parquet and provenance are accompanied by the native archive or catalogue
snapshot and hashes. Repeated matching requests verify those files before reuse.
Archive member counts and total uncompressed size are bounded, as are downloaded
bytes and source rows. Defaults are 128 MiB per HTTP response, 512 MiB uncompressed,
128 archive members, 1,000,000 source rows and 10,000 catalogue stations. The
corresponding `--maximum-*` options make larger explicit selections possible
within the reader's validated limits.

Cite DWD's dataset **Hourly station observations of solar incoming (total/diffuse)
and longwave downward radiation for Germany, version v24.03**, and preserve its
CC BY 4.0 attribution, station metadata and access date with the study.

### NOAA SURFRAD radiation stations

SURFRAD is a separate NOAA radiation source with seven supported archive aliases:
`bon`, `tbl`, `dra`, `fpk`, `gwn`, `psu` and `sxf`. The provider retrieves the
[official station catalogue](https://gml.noaa.gov/grad/surfrad/sitepage.html)
and public native daily files, with no API key:

```bash
uv run energy-retrieve surfrad-stations \
  --output data/surfrad/stations.parquet

uv run energy-retrieve surfrad-observations \
  --station bon --start 2026-01-01 --end 2026-01-02 \
  --output data/surfrad/observations
```

The [native format documentation](https://gml.noaa.gov/aftp/data/radiation/surfrad/bon/README_SURFRAD.txt)
defines UTC **interval-end** labels: three-minute averages before 1 January 2009,
and one-minute averages thereafter. The reader records the interval start, end
and duration explicitly while preserving the original labels. It retains
radiation and accompanying meteorological fields, their quality flags, source
headers, missing values and valid negative or zero measurements. UVB is mW/m²;
instrument case/dome temperatures are Kelvin. Those fields must not be silently
interpreted as W/m² or air temperature in Celsius.

Each requested day is a separate Parquet partition with the original source
file and a checksum manifest. Native file-header coordinates are preserved
independently of catalogue metadata. A missing day or invalid file stops with an
error rather than being silently replaced. Requests are bounded by
`--maximum-days` (default 366), `--maximum-rows` (default 1,440 per daily file)
and `--maximum-response-bytes` (default 8 MiB). Verified repeats need no network.

[SURFRAD participates in BSRN](https://gml.noaa.gov/grad/surfrad/overview.html).
The provider marks this relationship in provenance. Joining the two feeds
requires an explicit overlap policy; they are not independent observations merely
because they came from different download routes. Retain the dataset attribution
and both Augustine et al. papers requested by NOAA in the study bibliography.

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
  --schema data-retrieval/examples/station.toml \
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
- Credential query parameters, private headers, encoded echoes and HTTP client logs are
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

For normalized hourly adapters, the canonical interval columns are `site_id`
(string), `timestamp` (UTC-aware interval start), and `duration_hours`.
Site generation adds `actual_mwh` and
`generation_complete`; weather adds `ghi_wm2,temperature_c,wind_speed_ms,gust_ms`.
Feed site-aggregated generation and matching weather into the
`energy_analysis.chile_fleet` workflow in `analysis/`. CMIP6 downloads retain the
separate native NetCDF contract described above. BSRN, NOAA GHCNh, AEMET, DWD and
SURFRAD imports retain their native station products; they do not enter this hourly site schema
without an explicit mapping, quality decision and time aggregation contract.

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
- [CMIP6 data-user and citation guidance](https://pcmdi.llnl.gov/CMIP6/Guide/dataUsers.html)
- [STAC File Info specification](https://github.com/stac-extensions/file/tree/v2.1.0)
- [BSRN network and data description](https://doi.org/10.5194/essd-10-1491-2018)
- [BSRN data retrieval via PANGAEA](https://bsrn.awi.de/data/data-retrieval-via-pangaea/)
- [PANGAEA DOI access and reuse](https://wiki.pangaea.de/wiki/Data_Access_and_Reuse)
- [NOAA GHCNh dataset, DOI 10.25921/jp3d-3v19](https://doi.org/10.25921/jp3d-3v19)
- [NOAA GHCNh format and quality-code documentation](https://www.ncei.noaa.gov/oa/global-historical-climatology-network/hourly/doc/ghcnh_DOCUMENTATION.pdf)
- [AEMET OpenData specification](https://opendata.aemet.es/AEMET_OpenData_specification.json)
- [AEMET current API access notices](https://opendata.aemet.es/centrodedescargas/novedades)
- [DWD hourly solar dataset and native archives](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/solar/)
- [NOAA SURFRAD native format](https://gml.noaa.gov/aftp/data/radiation/surfrad/bon/README_SURFRAD.txt)
- [NOAA SURFRAD network and BSRN relationship](https://gml.noaa.gov/grad/surfrad/overview.html)

The existing API endpoint schemas and interval conventions are adapted from the
prior Chile study's acquisition scripts, with explicit validation and no embedded
data or credentials. Historical export and measured-station adapters use explicit
contracts and synthetic fixtures. Live source availability, a complete historical
release, historical identity validity and metrological quality require separate
evidence; offline tests do not establish them.
