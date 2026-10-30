# South Korea: KPX hourly regional solar

Use the Korea Power Exchange's **regional hourly solar generation** API through
data.go.kr. The official service is `PvAmountByLocHr/getPvAmountByLocHr`; it
returns `tradeYmd`, `tradeNo`, `regionNm` and `amgo` (MWh).

Apply for the free service on data.go.kr, then store the **decoded** service key
locally in `KPX_API_KEY`. Development and production access have different
approval/traffic conditions. Do not include the key in notebooks, URLs or files.

```python
from datetime import date
from energy_data_retrieval.sources.kpx import KPX_HOSTS, KPXClient
from energy_data_retrieval.transport import HTTPClient

with HTTPClient(KPX_HOSTS) as http:
    result = KPXClient.from_environment(http).solar_generation(date(2024, 9, 1), date(2024, 9, 2))
```

The client makes daily requests, follows all pages, checks `totalCount`, rejects
repeated/inconsistent pages and applies total request/row limits. Authentication
is passed through the transport's secret mapping; provenance and caches exclude
the key. An optional `region` selects an exact source region label after retrieval.

KPX trading hours **01 through 24 label interval ends**. Hour 01 is 00:00-01:00
in `Asia/Seoul`, and hour 24 ends at the next midnight. `timestamp` is normalized
to UTC interval start, with a separate `interval_end`. Values remain **MWh**;
nulls, zero and negative values remain distinguishable.

Coverage is **market-participating solar generators**, not all Korean solar.
Direct KEPCO trades and self-generation can be excluded. Coupled ESS can produce
nighttime solar-category output; do not automatically discard it. Settlement
revisions may change past data. Response hashes identify the actual acquisition.

`solar_requests` creates secret-free first-page request plans without an account.
The gallery uses that offline plan, with an explicit opt-in live branch; it does
not present synthetic values as Korean measurements. Live authenticated retrieval
has not been exercised in the gallery; parser/pagination tests use labelled
synthetic responses following the official Swagger schema.

- [Official API, field definitions and access conditions](https://www.data.go.kr/data/15103243/openapi.do)
- [KPX data guide: generation coverage and ESS](https://new.kpx.or.kr/boardDownload.es?bid=0045&list_no=71003&seq=2)
- [KPX market definitions: trading-hour end convention](https://marketrule.kpx.or.kr/lmxsrv/law/joHistoryContent.do?DATE_END=20231230&DATE_START=20210501&SEQ=2&SEQ_CONTENTS=7335)
