# AEMO dispatch-unit SCADA

This connector reads public NEMWeb `DISPATCH_UNIT_SCADA` observations for
Australia's National Electricity Market. It supports individual five-minute
interval ZIPs, daily ZIPs containing interval ZIPs, and downloaded MMS CSV.
No API key is required.

```python
from datetime import date
from energy_data_retrieval.sources.aemo import AEMO_HOSTS, AEMOClient
from energy_data_retrieval.transport import HTTPClient

with HTTPClient(AEMO_HOSTS) as http:
    source = AEMOClient(http)
    listing = source.list_files(archive=True)
    print(listing.urls[-3:])  # Date availability changes as archives expire.
    day = source.generation_day(date(2026, 10, 27), duids=["NYNGAN1"])
    print(day.frame)
    print(day.request)  # URL, retrieval timestamp, archive byte size and SHA-256.
```

## What the observations mean

- `timestamp` preserves the published `SETTLEMENTDATE` dispatch label converted
  to UTC. NEM market time is fixed AEST (UTC+10) throughout the year; Sydney or
  Melbourne daylight-saving time must not be applied.
- `value` is `SCADAVALUE` in **MW**, an instantaneous snapshot at the start of
  the dispatch interval. It is neither five-minute mean power nor settlement
  energy. No automatic MW-to-MWh conversion is performed.
- `unit_id` is the exact DUID. Native columns remain available as
  `source:SETTLEMENTDATE`, `source:DUID`, `source:SCADAVALUE`, and any additional
  source fields such as `source:LASTCHANGED`.
- Technology is left unknown. Join an official generator/load registry before
  filtering generator DUIDs or labeling fuel types. Scheduled loads and storage
  may also appear; this table is not solely a generator inventory.
- Missing readings remain missing, negative readings remain negative, and
  duplicate label/DUID keys fail explicitly. No interpolation or inferred
  completeness is applied.

The table covers scheduled and semi-scheduled units and some non-scheduled
units where SCADA exists. It does not provide complete behind-the-meter or
distributed generation. A daily archive uses NEM dispatch labels from 00:05
through 00:00 the following day, which is not a UTC calendar day.

## Retrieval and reproducibility

`list_files()` discovers current interval files; `list_files(archive=True)`
discovers available historical daily files. `fetch_file(url)` retrieves one
listed ZIP and `generation_day(day)` constructs the documented daily archive
filename. Current and historical directory retention is finite. Missing files
raise a retrieval error, and the connector does not fall back to synthetic data.

HTTP reads use the repository's allowlisted, retrying, byte-bounded transport.
CSV row counts, ZIP nesting, member counts, and total decompressed bytes are
bounded separately. ZIP members are read in memory and never extracted to
member-supplied filesystem paths. Retain `result.request` alongside any saved
DataFrame to preserve its acquisition URL, date, source hash and byte count.

The gallery includes 864 real native rows: three DUIDs, each with all 288 labels
on 27 October 2026. Its manifest records the original archive and exact subset
hash, with reproducible selection instructions. The gallery builds offline.

## Official references and attribution

- [AEMO DISPATCH_UNIT_SCADA data dictionary](https://visualisations.aemo.com.au/aemo/nemweb/MMSDataModelReport/Electricity/MMS%20Data%20Model%20Report_files/MMS_123.htm).
- [Current dispatch SCADA files](https://nemweb.com.au/Reports/CURRENT/Dispatch_SCADA/).
- [Daily dispatch SCADA archives](https://nemweb.com.au/Reports/ARCHIVE/Dispatch_SCADA/).
- [AEMO glossary: AEST and market time](https://markets-portal-help.docs.public.aemo.com.au/Content/TOC_common-topics-DOnotChange/Glossary.htm).

Attribute the Australian Energy Market Operator and preserve acquisition
provenance. Public availability does not change the source's reuse conditions;
consult AEMO's applicable terms when redistributing larger data extracts.
