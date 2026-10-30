# CAISO: five-minute public supply data

`CAISOClient.generation(start, end)` downloads native `fuelsource.csv` files for
inclusive Pacific calendar dates from Today's Outlook. No API key is needed.
The result retains one provenance record per daily file and enforces request,
response-byte and normalized-row bounds.

```python
from datetime import date
from energy_data_retrieval.sources.caiso import CAISO_HOSTS, CAISOClient
from energy_data_retrieval.transport import HTTPClient

with HTTPClient(CAISO_HOSTS) as http:
    result = CAISOClient(http).generation(date(2024, 6, 1), date(2024, 6, 1))
generation = result.frame.loc[result.frame["flow"].eq("generation")]
```

## Physical meaning

Source values are **five-minute average power in MW**, not interval energy.
The connector preserves zero, signed values and missing cells. Imports carry
`flow=net_import` and batteries carry `flow=net_storage`. The native **Other**
category carries `flow=other_supply` because it can include proxy demand response
and miscellaneous supply. These three categories remain separate from rows
labelled `flow=generation`. Negative storage is preserved as charging. The entire
display is not a plant inventory.
Hybrid components are already included in their corresponding fuel categories;
separately downloaded hybrid charts must not be added again.

The CSV publishes only `HH:MM` clock labels. For unambiguous times these are
localized to `America/Los_Angeles` and converted to UTC. `timestamp` preserves
the clock-label convention; it is not asserted to be an interval start or end.

**DST limitation:** the inspected 2024 transition-day archives contain 288
unique labels with no offsets, even on 23/25-hour civil days. Such labels cannot
uniquely reconstruct every UTC interval. The parser rejects ambiguous or
nonexistent Pacific times rather than guessing, dropping an hour or shifting
measurements. A range containing those files consequently fails explicitly.

## Sources and quality

- [Today's Outlook supply, downloads and interpretation](https://www.caiso.com/todays-outlook/supply)
- File pattern: `https://www.caiso.com/outlook/history/YYYYMMDD/fuelsource.csv`

CAISO describes these as informational operational data, subject to revision;
they should not be used for billing or operational planning. Provider reuse
terms apply. The gallery includes one real complete ordinary-day CSV with the
original bytes, retrieval URL, capture time and SHA-256. The connector does not
claim settlement-quality measurements or coverage of all distributed generation.
