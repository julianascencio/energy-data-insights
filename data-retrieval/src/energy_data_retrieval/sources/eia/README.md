# U.S. Energy Information Administration (EIA)

This connector retrieves reported electricity generation from official U.S. EIA
open data. It has three routes:

| Route | Observation level | Frequency | Access |
| --- | --- | --- | --- |
| API v2 `electricity/rto/fuel-type-data` | Balancing authority, region or Lower 48, by fuel | Hourly | Free registered `EIA_API_KEY` |
| API v2 `electricity/facility-fuel` | Power plant, fuel and prime mover | Monthly | Free registered `EIA_API_KEY` |
| Public EIA-930 six-month balance CSV | Individual balancing authority, by fuel | Hourly | No key |

## Usage

```python
from datetime import UTC, datetime
from pathlib import Path

from energy_data_retrieval.sources.eia import EIA_HOSTS, EIAClient
from energy_data_retrieval.transport import HTTPClient

with HTTPClient(EIA_HOSTS) as http:
    client = EIAClient.from_environment(http)
    hourly = client.hourly_generation(
        datetime(2024, 6, 20, 8, tzinfo=UTC),
        datetime(2024, 6, 27, 7, tzinfo=UTC),
        respondents=["CISO"],
        fuel_types=["SUN", "WND"],
    )
    print(hourly.frame)
    # Inclusive reporting month bounds; replace with actual EIA plant codes.
    # plants = client.monthly_generation(
    #     "2024-01", "2024-12", plant_codes=["YOUR_PLANT_CODE"]
    # )
    # Official metadata lists available facets and data fields.
    metadata, request = client.metadata("monthly")

with HTTPClient(EIA_HOSTS) as http:
    # Public full-file download; no API key required, ~42 MB for this vintage.
    public = EIAClient(http).balance_file(
        2024,
        1,
        Path("EIA930_BALANCE_2024_Jan_Jun.csv"),
        respondents=["CISO"],
        fuel_types=["SUN", "WND"],
    )
```

Register your own key at <https://www.eia.gov/opendata/register.php>. Keys are
passed through the shared transport's secret handling; they are excluded from
client representations, request provenance, public caches and error messages.

## Time, units, aggregation and missing observations

- API hourly bounds are **inclusive UTC hour-ending labels**. Provide aware
  datetimes on whole-hour boundaries. The API request explicitly selects UTC
  `hourly` frequency, never the ambiguous `local-hourly` frequency.
- Hourly `timestamp` and `interval_end_utc` denote the **end** of the interval;
  `interval_start_utc` is one hour earlier. Use the latter when assigning energy
  to a local operating day. Daylight-saving days can contain 23 or 25 hours.
- API `value` is energy in **MWh**. The public CSV headers label the hourly
  integrated average power as MW; its energy is calculated for the explicit
  one-hour interval, numerically equal in MWh. `source_value`, `source_unit`
  and `source_column` preserve the source convention.
- The public CSV parser uses **reported** fuel columns. Imputed, adjusted,
  demand, interchange and total-generation columns do not enter the fuel sum.
  It supports the older fuel columns and the expanded 2025 storage/hybrid
  categories, including negative charging observations. Unknown future fuel
  columns fail explicitly so a schema change cannot silently omit a resource.
- Missing/null/suppressed values remain `NaN` with their source representation
  and status. Zero and negative observations remain unchanged. Unknown value
  markers, non-finite values, unit changes and conflicting duplicates fail.
- Hourly observations describe **systems**, not power plants. Regional and
  `US48` totals overlap BA observations; do not add these aggregation levels.
  EIA-930 generally does not cover resources outside BA metering, including
  much distributed solar. The API preserves respondent codes and names.
- Monthly records retain `plantCode`, `fuel2002`, `fuelType` and `primeMover`.
  A plant can have multiple fuels and prime movers, and `ALL` categories may
  overlap their detail rows. The connector never silently collapses them.
  `unit_id` is the **plant code**, not a generator identifier. Monthly
  `timestamp` is an indexing label for the month, not an instantaneous UTC
  measurement or an inferred plant timezone.

## Completeness and reproducibility

API requests use stable sorting on all identity dimensions and up to 5,000 rows
per page. Every advertised page is retrieved, or the request fails. Changed
totals, short/repeated pages, out-of-range periods and ignored filters are
rejected. Bounds on pages, HTTP bytes, retries and request pacing prevent
unbounded downloads. A stable count cannot guarantee the source remained
unchanged during a multi-page request; EIA can revise historical data.

`EIAResult.requests` contains each request's non-secret parameters, retrieval
time and sanitized response checksum. `balance_file` keeps the downloaded CSV
and its checksum manifest. Pure `normalize_hourly_generation`,
`normalize_monthly_generation` and `parse_balance_csv` functions support replay.
There is no assertion that missing intervals mean zero or that all generators
in a geography are represented.

The gallery example `examples/connectors/plot_generation_eia.py` parses 168 real CISO
operating hours from a byte-preserved public CSV excerpt. Its adjacent JSON
manifest identifies the full source file and excerpt checksums. No credentials
or network access are required to build the gallery. API tests use explicitly
synthetic responses; credentialed live API validation requires a user's key.

## Official references

- [EIA API v2 documentation](https://www.eia.gov/opendata/documentation.php)
- [Hourly fuel generation API browser](https://www.eia.gov/opendata/browser/electricity/rto/fuel-type-data)
- [Plant generation API browser](https://www.eia.gov/opendata/browser/electricity/facility-fuel)
- [EIA-930 coverage, units, timing and data quality](https://www.eia.gov/electricity/930-content/about.html)
- [EIA-930 reporting instructions](https://www.eia.gov/survey/form/eia_930/instructions.pdf)
- [EIA-930 official energy source codes](https://www.eia.gov/electricity/930-content/EIA930_Reference_Tables.xlsx)
- [Public six-month file catalogue](https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/EIA930_File_List_Meta.csv)
- [EIA-923 detailed generation data](https://www.eia.gov/electricity/data/eia923/)
- [EIA data reuse and attribution](https://www.eia.gov/about/copyrights_reuse.php)

These data are attributed to the U.S. Energy Information Administration. The
connector is not an EIA product and does not imply EIA endorsement.
