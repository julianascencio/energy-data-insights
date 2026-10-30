# Ontario: IESO hourly generator output

`IESOClient.generation(start, end, unit_ids=None)` retrieves inclusive report
dates from the public daily `GenOutputCapability` XML archive. It returns
`GenerationResult(frame, requests)` with request hashes, retrieval times and byte
counts. No credentials are required; only `reports-public.ieso.ca` is allowed.

```python
from datetime import date
from energy_data_retrieval.sources.ieso import IESO_HOSTS, IESOClient
from energy_data_retrieval.transport import HTTPClient

with HTTPClient(IESO_HOSTS) as http:
    result = IESOClient(http).generation(
        date(2026, 10, 28), date(2026, 10, 28), unit_ids=["GRANDSF"]
    )
```

The parser reads **only** `Outputs/Output/EnergyMW`. Capability and forecast
elements in the same XML document are not measured generation. The report covers
participating facilities with maximum capability of at least 20 MW; it does not
represent all rooftop solar or all Ontario generation. Values are operational
hourly mean MW derived from five-minute telemetry, subject to source correction,
and are not settlement-meter energy.

IESO uses **fixed Eastern Standard Time, UTC−05, throughout the year**. Source
Hour 1 covers 00:00–01:00 and Hour 24 covers 23:00–24:00. `timestamp` is the UTC
interval start and `interval_end` is the UTC interval end. The report date, hour
ending, source creation time, original generator name and fuel type are retained.
Using `America/Toronto` would shift summer observations incorrectly.

Empty/N/A telemetry and native Hour-only outputs without an EnergyMW element
remain NaN and negative output is retained. Identical
duplicates are removed; conflicting unit/hour observations fail. Malformed XML,
external entity declarations, missing actual-output elements, unexpected hours
and wrong report dates fail explicitly. Dates are bounded to 31 requests and one
million observations by default, in addition to the shared HTTP byte limit.

The daily XML archive normally retains about 90 days. Older monthly generator
CSV reports are a separate product and are not silently substituted by this
connector; an expired daily report fails. `parse_generation_xml` also supports
saved native XML reports. For new live requests, choose dates still present in
the archive.

Official sources (attribution: Independent Electricity System Operator):

- [Generator Output and Capability report help](https://reports-public.ieso.ca/docrefs/helpfile/GenOutputCapability_h4.pdf)
- [IESO data directory and retention](https://www.ieso.ca/en/power-data/data-directory)
- [Government of Canada electricity data clock conventions](https://energy-information.alpha.canada.ca/en/resources/high-frequency-electricity-data)

The gallery captures three actual solar-generator elements (24 hours each),
retains the report header, and records the complete-source and selected-file
hashes. XML reserialization is documented; observation values are unchanged.
IESO's source terms apply to reuse.
