# Real electricity generation connectors

The retrieval package now connects to four additional official generation
providers alongside Chile's CEN. Select the product by its physical scope and
time convention before combining sources. These adapters retrieve observations;
they do not simulate missing generation or infer a plant registry.

## Choose a product

| Provider and product | Physical scope | Native quantity and time | Access |
| --- | --- | --- | --- |
| **AEMO NEMWeb Dispatch SCADA** | Published dispatchable unit IDs (DUIDs) in Australia's NEM | Instantaneous MW, published every five minutes; fixed AEST (UTC+10) dispatch labels | Public files, no key |
| **U.S. EIA API v2, EIA-930** | Balancing authority, regional or Lower-48 generation by fuel | Hourly MWh; UTC hour-ending labels | Free registered `EIA_API_KEY` |
| **U.S. EIA public balance CSV** | Individual balancing authorities by fuel | Hourly average MW in the source, explicitly multiplied by one hour to produce MWh | Public six-month files, no key |
| **U.S. EIA API v2, facility-fuel** | Power plant, fuel and prime mover | Monthly net-generation MWh; reporting-month labels | Free registered `EIA_API_KEY` |
| **Spain REE / REData** | National or electrical-system/community generation by technology | Daily/monthly/yearly MWh; source civil-period labels with UTC offsets | Public API, no key |
| **Europe ENTSO-E Transparency A75** | Selected area and production type | Interval-average MW; UTC interval start/end and duration | Approved `ENTSOE_API_TOKEN` |
| **Europe ENTSO-E Transparency A73** | Individually published generation units | Interval-average MW and unit EICs; incomplete coverage of small plants | Approved `ENTSOE_API_TOKEN` |

Provider references: [AEMO data dictionary](https://visualisations.aemo.com.au/aemo/nemweb/MMSDataModelReport/Electricity/MMS%20Data%20Model%20Report_files/MMS_123.htm),
[EIA API](https://www.eia.gov/opendata/documentation.php),
[EIA-930 scope and timing](https://www.eia.gov/electricity/930-content/about.html),
[REData API](https://www.ree.es/en/datos/apidata),
[ENTSO-E API parameters](https://transparencyplatform.zendesk.com/hc/en-us/articles/15696716612372-Request-Parameters).

## Worked gallery examples

Each provider has an executable, step-by-step example with plots:

- [AEMO: real dispatch-unit SCADA](../examples/plot_generation_aemo.py): 864 source observations, three DUIDs and 288 dispatch labels for 27 October 2026.
- [EIA: real California generation](../examples/plot_generation_eia.py): 168 CISO operating hours from 20–26 June 2024, comparing reported solar and wind.
- [REE: Spain's generation by technology](../examples/plot_generation_ree.py): the real daily generation mix for all 30 days of June 2024.
- [ENTSO-E: European generation](../examples/plot_generation_entsoe.py): an offline request plan plus an explicit live-download path for actual Spanish wind/solar generation.

The first three examples use small attributed captures from the official
providers, with original source URLs, retrieval times, transformations and
checksums under `examples/data/`. They are not synthetic measurements. The
ENTSO-E example does not substitute invented measurements for a missing token:
its default chart counts planned API calls and is labelled accordingly.

The gallery page offers one ZIP containing all four scripts and their input
data. Extract it with the `data/` directory intact, install the workspace with
`uv sync --locked --all-packages --group docs`, then run the examples. Ordinary
documentation builds require no credentials and make no provider requests.

## Command-line acquisition

All five commands write Parquet and a neighboring `.parquet.json` manifest.
The manifest records the exact public query, upstream request hashes and time,
plus the output hash and source metadata. An existing matching output is reused
after checksum validation. Choose a **new output path** to capture provider
revisions while preserving the previous snapshot.

### AEMO: one NEM day of unit snapshots

```bash
uv run energy-retrieve aemo-generation \
  --date 2026-10-27 \
  --duid BROKENH1 --duid COLEASF1 --duid NYNGAN1 \
  --output data/aemo_2026-10-27.parquet
```

Omit `--duid` to retain all published units within the configured resource
limits. Archive retention is finite; discover available files with
`AEMOClient(http).list_files(archive=True)`. `list_files()` discovers recent
interval files, and `fetch_file(url)` retrieves one exact discovered file.
The connector supports the nested ZIP structure of daily archives without
extracting archive paths onto disk.

Keep the source's published dispatch label distinct from its measurement
semantics: the SCADA reading is instantaneous at the start of the dispatch
interval. Multiplying snapshots by five minutes is an approximation and is
not metered settlement energy. DUIDs can refer to different resource types;
technology and generator/load classification require an official roster.

### EIA: hourly generation and monthly plant records

Store your registered API key in the `EIA_API_KEY` environment variable. Obtain
it from [EIA Open Data](https://www.eia.gov/opendata/register.php).

```bash
uv run energy-retrieve eia-generation \
  --start 2024-06-20T08:00Z --end 2024-06-27T07:00Z \
  --respondent CISO --fuel-type SUN --fuel-type WND \
  --output data/eia_ciso_2024-06.parquet

# Supply the actual plant code from the official EIA facility catalogue.
uv run energy-retrieve eia-plant-generation \
  --start 2024-01 --end 2024-12 --plant-code "$EIA_PLANT_CODE" \
  --output data/eia_plant_2024.parquet
```

Hourly bounds are **inclusive hour-ending timestamps**, with an explicit UTC
offset. Monthly bounds are inclusive reporting months. The client paginates
past 5,000 rows with a stable identity sort, and rejects incomplete or changing
pagination. `client.metadata("hourly")` and `client.metadata("monthly")` expose
the official route's facets and data fields.

Without a key, use the official public files through the same source module:

```python
from pathlib import Path
from energy_data_retrieval.sources.eia import EIA_HOSTS, EIAClient
from energy_data_retrieval.transport import HTTPClient

with HTTPClient(EIA_HOSTS) as http:
    result = EIAClient(http).balance_file(
        2024,
        1,
        Path("data/EIA930_BALANCE_2024_Jan_Jun.csv"),
        respondents=["CISO"],
        fuel_types=["SUN", "WND"],
    )
print(result.frame)
```

The source download is a six-month file, even when the resulting frame selects
one respondent. The parser chooses reported fuel columns, preserving missing,
zero and negative values. It does not substitute imputed/adjusted series. The
expanded storage/hybrid taxonomy introduced in 2025 is supported.

Hourly regional totals overlap balancing-authority totals. Monthly `ALL` fuel
or prime-mover categories can overlap their detail records. Do not blindly sum
those aggregation levels. A plant code is not an individual generator ID, and
monthly energy cannot reconstruct a measured hourly profile.

### REE: daily or calendar-period generation

```bash
uv run energy-retrieve ree-generation \
  --start 2024-06-01 --end 2024-06-30 --system national \
  --output data/ree_national_june_2024.parquet

uv run energy-retrieve ree-generation \
  --start 2024-01-01 --end 2024-12-31 --aggregation month --system canarias \
  --output data/ree_canarias_2024.parquet
```

Also supported: `peninsular`, `baleares`, `ceuta`, `melilla`, and `ccaa` with an
explicit `--geo-id` from the provider's catalogue. Monthly/yearly requests must
cover full calendar periods. Returned offsets are retained before UTC
conversion, so daylight-saving changes do not silently shift the source date.
The raw API's MWh values are not re-scaled because the website displays GWh.

The provider's generation-total series is excluded by default to prevent
double counting. `--include-total` retains it with `is_total=True`. Keep those
rows separate from individual technologies. Source update dates and reported
percentages remain available; missing observations are not converted to zero.

### ENTSO-E: aggregate and individual generation

Follow the [official token procedure](https://transparencyplatform.zendesk.com/hc/en-us/articles/12845911031188-How-to-get-security-token)
and store the approved token in `ENTSOE_API_TOKEN`. Use an exact area EIC from
the [official area list](https://transparencyplatform.zendesk.com/hc/en-us/articles/15885757676308-Area-List-with-Energy-Identification-Code-EIC).

```bash
uv run energy-retrieve entsoe-generation \
  --area 10YES-REE------0 \
  --start 2025-09-01T00:00Z --end 2025-09-08T00:00Z --psr-type B16 \
  --output data/entsoe_spain_solar.parquet

uv run energy-retrieve entsoe-generation \
  --area 10YES-REE------0 --per-unit \
  --start 2025-09-01T00:00Z --end 2025-09-02T00:00Z \
  --output data/entsoe_spain_units.parquet
```

The end boundary is **exclusive**. Use `--unit-id` with `--per-unit` to select
one published resource EIC. The client requests actual generation (`A16`),
chunks aggregate requests into at most 31 days and unit requests into one day,
and retains complete native intervals within the requested boundaries.

A03 step-valued XML is expanded at the published resolution, including explicit
missing blocks; it is not treated as a sparse list of unrelated samples. A01
missing positions remain missing. Generation and consumption are separate
`flow` values, including pumped storage. The connector retains document IDs,
revisions, unit IDs and interval durations; conflicting duplicates/overlaps
fail. Unsupported compressed/multipart responses are not silently parsed.

For a complete interval, energy is `value * duration_hours` in MWh. Missing
power remains missing energy. A73 is not a complete inventory of small plants;
aggregate actual generation can include estimates submitted by the provider.

## Validation and interpretation

The initial connector contribution was checked against real public AEMO and
EIA bulk downloads and live REE daily/monthly/yearly responses. The committed
gallery captures are replayable offline. EIA's credentialed API routes use
mocked contract tests; ENTSO-E uses mocked tests plus the provider's public XML
schema examples. **Authenticated EIA and ENTSO-E downloads were not live-tested
without personal credentials.** Schema examples are not operational measurements.

Requests use source host allowlists, finite byte/row/page bounds, retry limits,
and source-specific validation. API keys/tokens never enter manifests, error
URLs or the public cache. Every source preserves its units and original time
semantics; a common `value` column does not make the products interchangeable.

Provider attribution and reuse conditions remain attached to the samples.
The repository's software license does not relicense provider datasets.
Before applying the Chile fleet or plant-performance methods, supply the
required plant roster, interval convention and capacity evidence for that
analysis. These system-level series are useful for generation-mix and fleet
context, but cannot establish a particular plant's operational performance.
