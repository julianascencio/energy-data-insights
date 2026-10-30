# Japan: TEPCO Tokyo-area generation

Retrieve TEPCO Power Grid's public monthly generation-mix CSVs for the Tokyo
service area. This connector supports the current `_03.csv` format from
**February 2024 onward**. It is a regional mix, not all of Japan or a plant registry.

```python
from datetime import date
from energy_data_retrieval.sources.tepco import TEPCO_HOSTS, TEPCOClient
from energy_data_retrieval.transport import HTTPClient

with HTTPClient(TEPCO_HOSTS) as http:
    result = TEPCOClient(http).generation(date(2026, 9, 1), date(2026, 9, 3))
```

Dates are inclusive in `Asia/Tokyo`; `timestamp` is the UTC interval start.
The connector verifies the CSV's explicit physical-unit declaration. The live
September 2026 export declares **MW average**, with 30-minute intervals. An
explicit `10000 kW average` declaration is converted to MW. Interval energy is
`value * 0.5` MWh; the API does not relabel average power as energy.

Native downloads use CP932. `download_file` preserves raw bytes and provenance;
the parser accepts lossless CP932 or UTF-8. Missing values remain NaN, never zero.
Generation can include publisher estimates and retrospective corrections, so
`may_include_estimates` remains true and request hashes identify each capture.

By default only generation technologies are returned. `include_flows=True` also
returns **separately labelled** renewable curtailment, net storage and net imports.
Positive storage is discharge and negative storage is charging; positive
interconnector values are imports. Those flows must not be added blindly to a
generation total. Demand and the supplied overall total are always excluded.

`generation_urls` creates bounded request plans; `parse_generation_csv` processes
downloaded files. The offline gallery uses unchanged observations transcoded
from CP932 into UTF-8, with source and fixture checksums. TEPCO's website terms
apply; public availability is not a claim of a separate open-data licence.

- [Monthly downloads and detailed flow definitions](https://www.tepco.co.jp/forecast/html/area_jukyu-j.html)
- [Current data, average-power units and estimate caveats](https://www.tepco.co.jp/forecast/html/area_data-j.html)
