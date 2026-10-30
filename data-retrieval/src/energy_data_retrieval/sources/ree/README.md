# REE / REData generation

`REEClient` retrieves actual system generation by technology from the public
`generacion/estructura-generacion` widget. It does not require an API key.

```python
from datetime import date
from energy_data_retrieval.sources.ree import REE_HOSTS, REEClient
from energy_data_retrieval.transport import HTTPClient

with HTTPClient(REE_HOSTS) as http:
    result = REEClient(http).generation(date(2024, 6, 1), date(2024, 6, 30), system="national")
print(result.frame)
print(result.requests)
```

Use `system="peninsular"`, `"canarias"`, `"baleares"`, `"ceuta"` or `"melilla"`
for an electrical system. For a community, supply `system="ccaa", geo_id="7"`
using the exact ID in the provider catalogue. Each regional request sends
`geo_trunc`, `geo_limit` and `geo_ids` together. Date ranges are split at year
boundaries and bounded by `maximum_requests` and `maximum_rows`.

`time_trunc="day"`, `"month"` and `"year"` are supported. Monthly/yearly requests
must cover full calendar periods. Daily dates are inclusive source calendar
dates. The offset in each source label is preserved as `source_datetime` and
converted to UTC in `timestamp`; `period` retains the source calendar date.
No naive timestamps, hourly disaggregation or mean-power conversion is assumed.

The widget's values are **MWh**, including when its website displays a scaled
GWh chart. The connector is specific to this generation widget (`gen1`) and
rejects other widgets or conflicting unit metadata. Source `magnitude` is often
null, so the documented widget energy convention is recorded explicitly.
Source technology IDs/names, percentages, series types and update dates remain.

Null values remain missing and negative observations remain unchanged. Exact
duplicates are collapsed; conflicting technology-period duplicates fail. The
provider total is excluded by default; use `include_total=True` only if you
will keep `is_total` rows separate from technology sums. An empty result is not
zero generation and the connector does not claim every requested date exists.

This is a national/regional statistical series, **not plant telemetry**. REE's
generation page excludes total estimated self-consumption and describes which
surplus injections are included. The existing CEN connector and the AEMO/EIA/
ENTSO-E unit products cover different levels of physical aggregation.

Official sources:

- [REData API and geographic parameters](https://www.ree.es/en/datos/apidata)
- [Generation structure and units](https://www.ree.es/es/datos/generacion/estructura-generacion)
- [Generation scope and glossary](https://www.ree.es/es/datos/generacion)
- [Provider reuse terms](https://www.ree.es/es/aviso-legal)

The offline gallery preserves a real June 2024 response with an explicit hash,
retrieval date and source update dates. Source data remain subject to the
provider's terms; the software license does not relicense provider data.
