# France: RTE / ODRÉ éCO2mix consolidated generation

`RTEClient.generation(start, end)` retrieves inclusive French civil dates from
`eco2mix-national-cons-def` through the public Explore API 2.1. No credentials
are needed. Each day is paginated in timestamp order with a maximum page size
of 100; the client checks the advertised total, duplicate pages, date filtering,
request limits and total output-row bounds. All response provenance is retained.

```python
from datetime import date
from energy_data_retrieval.sources.rte import RTE_HOSTS, RTEClient
from energy_data_retrieval.transport import HTTPClient

with HTTPClient(RTE_HOSTS) as http:
    result = RTEClient(http).generation(date(2024, 6, 1), date(2024, 6, 1))
```

## Actual production, not forecast placeholders

The consolidated dataset combines **quarter-hour consumption forecasts** with
**half-hour actual generation in MW**. Forecast-only rows at minutes 15 and 45
have null generation fields. The parser excludes and counts those rows; it
does not create a quarter-hour generation series by interpolation or zero fill.
Nulls in actual half-hour records remain missing. If a future schema starts
publishing actual generation on those quarter-hour rows, the parser fails
explicitly so the changed measurement convention can be reviewed.

The eight top-level technologies are oil, coal, gas, nuclear, wind, solar,
hydro and bioenergy, retaining the native French identifiers. Detailed
subcategories, pumping, demand and cross-border exchanges are excluded to
prevent double counting. `nature` retains consolidated/definitive status and
the source's offset-bearing timestamp is converted to UTC. The connector does
not turn MW into MWh or label system totals as plant telemetry.

This first connector deliberately accepts only `dataset="consolidated"`.
The real-time dataset has a different quality and timing contract. National
consolidated history starts in January 2012; technology details start in 2013.
Missing source history or categories are never inferred.

## Sources and reuse

- [Dataset, schema and temporal definitions](https://odre.opendatasoft.com/explore/dataset/eco2mix-national-cons-def/)
- [Dataset API console](https://odre.opendatasoft.com/explore/dataset/eco2mix-national-cons-def/api/)

The dataset is distributed under **Etalab Open Licence v2.0**. Attribute RTE and
ODRÉ. Keep requests bounded and cached: the portal documents a quota of 50,000
API calls per user per month. The gallery keeps one complete real response with
its URL, retrieval time and checksum, including the original forecast-only rows.
