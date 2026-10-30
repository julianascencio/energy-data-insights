# Alberta: AESO current and historical net generation

The connector supports two real AESO products: the authenticated current
generation API and bounded import of native historical CSD Generation CSVs.
Capacity and contingency reserve are kept separate from actual net generation.

```python
import os
from pathlib import Path
from energy_data_retrieval.sources.aeso import AESO_HOSTS, AESOClient
from energy_data_retrieval.transport import HTTPClient

with HTTPClient(AESO_HOSTS) as http:
    client = AESOClient(http)
    current = client.current_generation(api_key=os.environ["AESO_API_KEY"], asset_ids=["TVS1"])
    historical = client.from_native_file(Path("CSD Generation (Hourly).csv"), interval_minutes=60)
```

## Current API

The official Current Supply Demand v1 operation is
`/public/currentsupplydemand-api/v1/csd/generation/assets/current` on
`apimgw.aeso.ca`. It provides assets over 5 MW and accepts at most 20 `assetIds`.
An AESO developer account and API subscription key are required. The key travels
in the secret `API-KEY` header and is excluded from provenance. One call fetches
one current snapshot with cache disabled; this is not a historical endpoint.

The parser uses the documented `last_updated_datetime_utc` field directly. It
keeps the MPT display label separately and maps `asset_list[].net_generation` to
MW. `maximum_capability` and `dispatched_contingency_reserve` remain separate MW
columns. The complete response schema and version-path convention were checked
against AESO's public developer portal. No authenticated live response was
captured for the gallery, because no subscription key was supplied.

## Historical CSV

AESO publishes five-minute and hourly generation archives through its public Box
folder. Download the desired ZIP from the official historical-generation page,
extract the CSV, and call `from_native_file`. The archive has dynamic download
redirects; the connector does not claim unattended historical HTTP retrieval.
The local importer performs a bounded read (64 MiB by default), validates the
native schema and records `local_file_sha256`, size and acquisition type in frame
attributes. `requests` is empty because the importer did not perform an HTTP
request. `parse_generation_csv` also accepts the native text directly.

`Volume` is **average MW over the interval**, not MWh. Set `interval_minutes` to
5 or 60 to identify the selected product. The parser uses explicit `Date (MST)`
with **fixed UTC−07**, preserving `Date (MPT)` as supplied. This retains both
occurrences of a repeated MPT daylight-saving hour without guessing. Source
labels are not shifted and interval boundaries are not inferred. All native
columns, including capability, asset group, fuel, region and planning area,
remain present. Missing remains missing; negative net output is retained.

Both parsers reject conflicting asset/time duplicates and non-finite values.
The default maximum is one million rows. Historical CSVs are operational records,
may be revised, and should not be presented as settlement energy or complete
distributed-generation coverage.

Official sources (attribution: Alberta Electric System Operator):

- [Historical generation downloads](https://www.aeso.ca/market/market-and-system-reporting/data-requests/historical-generation-data/)
- [API information and access](https://www.aeso.ca/market/market-and-system-reporting/aeso-application-programming-interface-api/)
- [Current Supply Demand v1 official operation](https://developer-apim.aeso.ca/api-details#api=currentsupplydemand-api-v1&operation=getCSDReportByAsset)
- [API access instructions](https://www.aeso.ca/assets/downloads/external/api/API-Access-Instructions-APIM-API-Gateway.pdf)

The gallery contains 336 real hourly observations for Big Sky and Travers solar
from September 2026. It preserves original CSV row bytes/CRLF and includes source
ZIP, native CSV and selection hashes. AESO's source terms govern reuse.
