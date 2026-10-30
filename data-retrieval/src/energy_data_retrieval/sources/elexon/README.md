# Elexon Insights: Great Britain BM-unit metered energy

`ElexonClient.generation(start, end, bm_unit=...)` retrieves inclusive UK
settlement dates from the public `B1610/stream` endpoint. No API key is required.
Requests are split into at most six-hour UTC intervals and have explicit request
and output-row limits. `GenerationResult` carries the normalized frame and a
`RequestRecord` for every response, including its URL, non-secret parameters,
retrieval time and SHA-256.

```python
from datetime import date
from energy_data_retrieval.sources.elexon import ELEXON_HOSTS, ElexonClient
from energy_data_retrieval.transport import HTTPClient

with HTTPClient(ELEXON_HOSTS) as http:
    result = ElexonClient(http).generation(
        date(2026, 10, 1), date(2026, 10, 1), bm_unit="T_SUTBS-1"
    )
```

## Physical meaning and time

- `quantity` is **metered energy in MWh per half-hour**, including negative
  demand and zero. The generic source `psrType=Generation` is not a fuel label.
- BM units can generate or consume. `flow=net_generation_or_demand` preserves
  that distinction without identifying every BM unit as a generating plant.
- `timestamp` and `interval_start` are reconstructed from the UK settlement date
  and period. The local civil day may have 46, 48 or 50 periods. The source's
  `halfHourEndTime` is UTC even when its string omits `Z`; it must agree with the
  reconstructed end time.
- Elexon publishes these data after about five working days and replaces them
  as later settlement runs become available. `settlement_run` is retained.
  Exact duplicate rows collapse, but conflicting values/runs for the same key
  raise instead of silently summing or selecting a revision.
- Null quantities remain missing. No missing BM unit or interval becomes zero.
  A bounded response is not a claim of full system coverage.

## Sources and reuse

- [Public API developer portal](https://developer.data.elexon.co.uk/)
- [B1610 metered-volume explanation](https://www.elexon.co.uk/bsc/article/bsc-insight-how-to-get-more-detailed-metered-volume-data-from-our-insights-solution/)
- [BMRS open-data licence](https://www.elexon.co.uk/bsc/data/balancing-mechanism-reporting-agent/copyright-licence-bmrs-data/)

Attribution and the BMRS licence apply. The gallery contains one complete,
unchanged real BM-unit day with a capture manifest. It is settlement evidence,
not live SCADA, a whole-country inventory or a validated plant-performance case.
