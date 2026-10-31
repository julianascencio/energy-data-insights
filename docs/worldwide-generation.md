# Worldwide generation data

Seventeen additional provider modules extend the existing CEN, AEMO, EIA, REE
and ENTSO-E connectors. Each has a worked example in the **Connectors** gallery,
a Python API, a command-line workflow and provenance. The gallery keeps the
**Methods → Connectors → Analysis** organization.

These sources publish different products: plant meter records, operational
SCADA, technology totals and instrumented PV arrays. Their scope, units and
clocks remain explicit. Combining them requires choosing compatible products;
an MW snapshot is not an MWh meter interval, and a regional series is not a
plant-level observation.

## Worldwide connector coverage map

The **[worldwide connector coverage example](https://julianascencio.github.io/energy-data-insights/auto_examples/connectors/plot_generation_coverage.html)**
adds two offline figures and their executable Python code to the Connectors
gallery. Its reviewed inventory includes all 47 implemented source modules:
22 generation providers, five station networks, 18 weather/climate/terrain grid
adapters, the local station-file importer and Natural Earth.

| View | What the map represents | Interpretation |
| --- | --- | --- |
| Generation sources | Country/system host countries, regional providers, selected ENTSO-E areas and PV research-site locators | Country shading identifies an implemented source in a country; it does not define its electrical footprint or establish complete national, plant or technology coverage. |
| Station catalogues | Actual source coordinates from NOAA GHCNh, BSRN, DWD hourly solar and the seven supported SURFRAD stations | Locations include historical catalogue entries and do not establish available variables, dates or operational status. AEMET's credentialed Spanish catalogue is listed separately. |
| Weather, climate and terrain scope | Documented global, land, regional and explicitly selected model-grid products | A product's geographic domain does not prove that a particular coordinate/date has a valid value; native land masks, grid selection and access requirements still apply. |

Regional markers are schematic location aids, not provider offices, power plants
or service-area polygons. AEMO represents the National Electricity Market,
IESO Ontario, AESO Alberta, CAISO its California-area product, and TEPCO the
Tokyo area. The ENTSO-E marker represents caller-selected transparency areas;
it does not shade the European Union as a single coverage region. PVDAQ shows
example system 4, NIST a reference testbed, and DKASC its Alice Springs precinct.
These points do not indicate national PV monitoring coverage.

The grid-scope panel also includes the two regional sources used by the
[Canary Islands KGPV analysis](kgpv-canary.md). **CanaryClim** implements monthly
temperature and precipitation climatologies for the Canary Islands, baseline
1979–2013, from the v1.0 2025 COG release. The approximately 5 m file pixel
spacing does not establish validated 5 m climate accuracy. **Global Solar Atlas**
implements the pinned 2019 annual-GHI archives for **Spain** (1994–2018) and
**Chile** (1999–2018), at 9 arcseconds (nominally 250 m). Usable Chile GHI stops
at 45°S despite the raster rectangle extending to 46°S, so southern mainland
Patagonia remains unclassified. The adapter is not a general worldwide
downloader or the current live solar-map service. Country codes provide
geographic context only and do not add generation coverage or imply observations
throughout Spain or Chile.

**CHELSA v2.1** adds global land temperature and precipitation climatologies,
baseline 1981–2010, through bounded native windows at 30 arcseconds (about 1 km).
The [Chile KGPV analysis](kgpv-chile.md) uses these climate fields with Chile's
solar archive; sampling them onto the finer solar grid does not add climate
detail. Native masks and the distinct climate/solar periods remain explicit.

The station figure uses **metadata rather than weather observations**. It keeps
valid catalogue coordinates without selecting recent or active stations. BSRN
and SURFRAD can represent the same physical sites, so points across providers
are not a count of unique stations. BSRN catalogue entries unsupported by its
observation API remain labelled as catalogue locations. AEMET requires an API
key, and the local station importer has whatever coverage the user's files
provide. Neither receives invented station coordinates.

The bundled 2026-10-30 snapshot contains 39,010 catalogue locations: 38,868 NOAA
GHCNh, 79 BSRN, 56 DWD hourly-solar and seven SURFRAD entries. Two NOAA rows with
out-of-range latitudes are excluded and identified in the provenance manifest;
their coordinates are not repaired. The BSRN `e13` entry is retained as a
catalogue location even though the observation API accepts only three-letter
station identifiers.

The code reads the reviewed connector catalogue, Natural Earth polygons and
station-coordinate capture from the adjacent `data/` directory. Their
`generation_coverage_*` filenames are included in the downloadable generation
ZIP, together with provenance containing source URLs, capture timestamps and
SHA-256 checksums. The Natural Earth 5.1.1 backdrop preserves 176 unchanged
country features at 1:110 million scale; Antarctica is explicitly omitted
because its original unsplit ring fails the existing antimeridian contract.
Administrative borders are geographic context, and this scale is not metre
accuracy. The [country-mapping guide](country-mapping.md#draw-categorical-country-boundaries)
shows the reusable plotting helper.

Run the example from a checkout after installing the documentation dependencies:

```bash
uv sync --locked --all-packages --group docs
uv run --no-sync python examples/connectors/plot_generation_coverage.py
```

Ordinary runs and documentation builds read the checked-in fixtures and make
no provider requests. Maintainers can explicitly refresh the boundary fixture
and station catalogues with the following bounded preparation scripts:

```bash
uv run --no-sync python scripts/prepare_connector_coverage.py
uv run --no-sync python scripts/prepare_connector_station_coverage.py
```

The boundary preparation pins the reviewed archive checksum; a changed upstream
archive fails rather than silently changing the map. The station preparation
records the newly retrieved inventory and its exclusions; review the resulting
data and manifest changes before committing them. Both accept
`--use-environment-proxy` when needed. A saved station capture can be reproduced
without network access using `--from-cache`.

## Provider catalogue

| Provider / region | Implemented product | Native measurement and clock | Access and example |
| --- | --- | --- | --- |
| **ONS · Brazil** | Verified plant generation; separate PV constrained-off detail | Hourly MW; half-hour PV output, limits and availability retained separately; explicit Brazilian source timezone | Public CKAN catalogue + bounded Parquet files; real captures |
| **IESO · Ontario, Canada** | Generator output and capability report | Hourly unit MW; hour-ending labels in fixed EST, UTC-05 | Public XML, recent report archive; real capture |
| **AESO · Alberta, Canada** | Current asset net generation and historical CSD export import | Current operational MW; historical five-minute/hourly MW with declared interval, fixed MST fields | `AESO_API_KEY` for current API; native CSV import from public historical archive; real historical capture |
| **XM / SIMEM · Colombia** | Actual hourly generation, dataset `055A4D`, selected settlement revision | Source kWh retained and normalized MWh; native labels in Colombia UTC-05 | Public API; real capture; default `TXF`, no silent revision fallback |
| **ADME · Uruguay** | Plant SCADA from the official SAS archive | Native measured MW, sampling period retained; explicit local clock | Public archive discovery + native SAS parser; real capture |
| **Elexon · Great Britain** | B1610 metered volumes by BM unit | Signed half-hour MWh; UTC end label checked against UK settlement date/period | Public Insights API; real capture |
| **RTE / ODRÉ · France** | Consolidated national éCO2mix generation by technology | Half-hour MW, offset-aware timestamps; forecast-only quarter hours excluded | Public Explore API with checked pagination; real capture |
| **SMARD · Germany** | Solar, onshore wind and offshore wind actual generation | Quarter-hour MWh, UTC timestamps derived from source epoch labels | Public series-index/weekly JSON files; real captures |
| **CAISO · California, USA** | Today's Outlook historical fuel mix | Operational five-minute MW in Pacific local labels; storage, imports and mixed Other supply identified separately | Public daily CSV; real capture; ambiguous DST-day labels fail explicitly |
| **EMI · New Zealand** | Plant/connection metered generation injection | Half-hour kWh; Pacific/Auckland trading periods with 46/48/50-period days | Public monthly CSV; real capture including a DST change |
| **Taipower · Taiwan** | Current generation by published unit/asset | MW snapshot in UTC+08; the refresh cadence is not an averaging interval | Public JSON; real capture; aggregate/storage-load rows excluded by default |
| **TEPCO · Tokyo area, Japan** | Area generation by technology, current `_03` CSV schema | Half-hour average MW; source unit row checked; UTC+09 | Public monthly CP932 CSV, current schema from February 2024; real capture |
| **KPX · South Korea** | Regional solar electricity traded in the market | Hourly net market-traded MWh; hour 01 is 00:00–01:00 KST, UTC+09 | Approved `KPX_API_KEY`; offline request-plan example and optional live retrieval |
| **Eskom · South Africa** | Eskom-owned/contracted renewable output | Reported hourly MW, hour beginning, UTC+02; embedded generation excluded | Public media discovery + latest CSV; real capture |
| **PVDAQ / OEDI · USA and contributed sites** | Measured system power channels and channel metadata | Native W/kW/MW selected explicitly; system clock and sampling conventions must be checked | Anonymous daily CSV + metadata; real complete-day capture |
| **NIST · Gaithersburg, USA** | Native PV testbed CSV/TOA5 import | One-minute average or one-second instantaneous AC kW; fixed EST with no DST | Download through PV portal, then import locally; offline import guide |
| **DKASC · Alice Springs, Australia** | Native measured PV array CSV import | Five-minute average AC kW; UTC+09:30; exact exported columns/date format selected | Provider form and data terms, then local import; offline import guide |

Official documentation and current access links are collected in the
[source references](references.md). Each module's README provides a focused
usage example and its provider-specific restrictions. The
[original generation guide](generation-connectors.md) covers CEN-adjacent AEMO,
EIA, REE and ENTSO-E workflows.

## Start with the gallery

The [Connectors gallery](https://julianascencio.github.io/energy-data-insights/auto_examples/connectors/index.html)
contains an executable example for every provider above. Download the generation
ZIP from its index and extract the `data/` directory alongside the scripts.
Install the workspace before running examples:

```bash
uv sync --locked --all-packages --group docs
uv run --no-sync python examples/connectors/plot_generation_emi.py
uv run --no-sync python examples/connectors/plot_generation_pvdaq.py
```

Captured examples use actual upstream observations with a source URL, retrieval
time, exact selection/transformation description and SHA-256 manifest. Subsets
are labelled as subsets, and any encoding conversion is documented. A checksum
verifies the saved capture; it does not guarantee that upstream values cannot
later be revised. Negative and missing observations are retained.

KPX has a real client and documented-schema tests, but its gallery defaults to
a request plan because no approved API key is bundled. NIST and DKASC have
functional native-file importers; their gallery pages explain the download and
import steps until the user supplies an export. They display no invented power
curves. Documentation builds need no credentials and make no provider requests.

## Command-line workflows

The new commands all write `.parquet` plus a neighboring `.parquet.json`
manifest. The manifest records the requested source/product, public query,
source metadata, response hashes or local input hash, and output identity.
Matching existing snapshots are checked before reuse. Use a new output path to
save a later provider revision. Changed local input bytes cannot silently reuse
an old import result.

| Product | Command | Selection |
| --- | --- | --- |
| Brazil plant generation | `ons-generation` | Inclusive dates; optional repeated `--plant-id` |
| Brazil solar constrained-off detail | `ons-solar-curtailment` | Inclusive dates; optional plant IDs; distinct curtailment fields |
| Ontario units | `ieso-generation` | Inclusive dates; optional repeated `--unit-id` |
| Alberta current assets | `aeso-generation` | Optional repeated `--asset-id`; environment API key |
| Alberta historical CSV | `aeso-history` | `--input`, required `--interval-minutes 5` or `60` |
| Colombia settlement generation | `xm-generation` | Inclusive dates, revision `--version`, optional resource IDs |
| Uruguay plant SCADA | `adme-generation` | Inclusive dates, `--central-id`, optional exact `--power-series` |
| Great Britain metered volumes | `elexon-generation` | Inclusive dates, optional `--bm-unit` |
| France consolidated mix | `rte-generation` | Inclusive dates, bounded page size |
| Germany solar/wind | `smard-generation` | Inclusive dates, repeated `--technology` selection |
| California operational fuel mix | `caiso-generation` | Inclusive Pacific dates |
| New Zealand plant injection | `emi-generation` | Inclusive source dates, optional repeated `--plant` |
| Taiwan current snapshot | `taipower-generation` | Optional aggregate/storage-load inclusion |
| Tokyo area generation | `tepco-generation` | Inclusive source dates; optional distinct flow rows |
| Korean traded solar | `kpx-generation` | Inclusive source dates, optional `--region`; environment API key |
| Eskom renewables | `eskom-generation` | Latest file, optional local dates or verified archive `--url` |
| PVDAQ measured channel | `pvdaq-generation` | System, dates, channel, unit and source timezone |
| PVDAQ channel metadata | `pvdaq-metrics` | `--system-id`; metadata output, not observations |
| NIST exported PV data | `nist-import` | `--input`, `--array`; optional channel/resolution |
| DKASC exported PV data | `dkasc-import` | `--input`, system, exact time/power columns and date format |

### Public API and archive examples

```bash
uv run energy-retrieve elexon-generation \
  --start 2024-06-01 --end 2024-06-01 --bm-unit T_SUTBS-1 \
  --output data/elexon_sutbs_2024-06-01.parquet

uv run energy-retrieve smard-generation \
  --start 2024-06-01 --end 2024-06-07 --technology solar \
  --output data/smard_solar_2024-06.parquet

uv run energy-retrieve xm-generation \
  --start 2024-06-01 --end 2024-06-01 --version TXF \
  --output data/xm_actual_txf_2024-06-01.parquet

uv run energy-retrieve eskom-generation \
  --output data/eskom_latest_snapshot.parquet
```

Dates in these commands refer to the documented source clock, including daylight
saving where applicable. Provider archives have different retention periods and
publication delays. An accepted date range does not promise that every plant
has a measurement in every interval. Empty/missing observations stay distinct
from reported zero output.

### Measured PV systems

```bash
uv run energy-retrieve pvdaq-metrics --system-id 4 \
  --output data/pvdaq_4_channels.parquet

uv run energy-retrieve pvdaq-generation --system-id 4 \
  --start 2023-01-01 --end 2023-01-01 \
  --power-column ac_power__315 --unit W --source-timezone=-07:00 \
  --output data/pvdaq_4_2023-01-01.parquet

uv run energy-retrieve nist-import --input inputs/nist_ground.csv --array ground \
  --output data/nist_ground.parquet
```

PVDAQ CSV column names encode metric IDs but not units; inspect the channel
metadata and system clock first. For NIST, the default `InvPAC_kW_Avg` and fixed
EST are verified against the [measurement paper](https://doi.org/10.6028/jres.122.040).
For DKASC, use `dkasc-import --help` and select the exact timestamp and measured
power columns from the downloaded file. Its
[data terms](https://dkasolarcentre.com.au/download/terms-conditions) govern
redistribution, including excerpt size, attribution and the provider disclaimer.

### Credentials and bounded retrieval

New credentialed routes read **`AESO_API_KEY`** and **`KPX_API_KEY`** from the
environment. Keys are never CLI arguments and never part of public query
identity, caches or manifests. Existing `EIA_API_KEY`, `ENTSOE_API_TOKEN` and
`CEN_USER_KEY` workflows continue to use their own environment variables.

Run each command with `--help` to inspect supported row, request, page and byte
limits. These limits fail explicitly; they do not silently truncate a requested
result. ONS selects Parquet resources to avoid fetching much larger monthly CSV
exports. HTTP retries are bounded and endpoints are provider-host allowlisted.
Portal-only imports read a bounded existing local file and perform no HTTP call.

## Interpretation and coverage limits

**Keep measurement type and scope.** AESO current and Taipower report snapshots;
CAISO and ADME publish operational data; Elexon and EMI publish metered records;
KPX covers market-traded solar rather than every rooftop system. RTE is national
consolidated generation and TEPCO is the Tokyo area. SMARD support is currently
the verified German solar and wind series. Eskom excludes embedded generation.

**Keep disjoint quantities separate.** Dispatch limits, available generation,
forecast output, storage charging, imports, mixed Other supply and aggregate totals may appear next
to generation. Adapters label or exclude them as documented; they are not extra
generation to add to detailed plant/fuel output. ONS estimate inclusion requires
an explicit option, and XM revision selection is explicit.

**Respect source clocks.** IESO and NIST use fixed EST, AESO historical files use
fixed MST, and DKASC uses UTC+09:30. Other products use civil time and daylight
saving. CAISO's historical CSV can publish ambiguous/nonexistent local labels
on clock-change days; those requests fail instead of inventing a UTC timeline.
PVDAQ requires the caller's verified clock convention.

**Validate before analysis.** Adapters preserve source observations and metadata;
they do not establish complete capacity histories, repair instrument failures,
infer plant identities or certify energy balances. Join official asset metadata
and choose a justified aggregation before applying the Methods or Analysis
examples to generation records.
