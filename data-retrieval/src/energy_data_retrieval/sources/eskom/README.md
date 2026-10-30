# Eskom hourly renewable generation

The [hourly renewable dataset](https://www.eskom.co.za/dataportal/renewables-performance/hourly-renewable-generation/)
covers Eskom-owned/contracted wind, PV, CSP and other renewables. Embedded
generation is excluded. It is not a complete national plant registry or all
South African renewable generation.

```python
from energy_data_retrieval.sources.eskom import ESKOM_HOSTS, EskomClient
from energy_data_retrieval.transport import HTTPClient

with HTTPClient(ESKOM_HOSTS) as http:
    result = EskomClient(http).generation()
```

The chart page can retain a stale monthly file link. Discovery uses the provider's
public WordPress media catalogue and selects the latest exact
`Hourly_Generation.csv` family, excluding `Total_Hourly_Generation.csv`. A known
official archive URL can be passed as `url=`. Host/path checks, the HTTP byte cap
and a native row cap bound retrieval.

`Date Time Hour Beginning` is localized as Africa/Johannesburg, UTC+02:00.
Measurements use Eskom's reported hourly MW convention; the connector does not
claim a finer sampling definition or convert reports into independently metered
energy. Missing and signed values are retained. The parser rejects bad schema,
invalid/infinite values, non-hourly labels and conflicting duplicate keys.

Optional `start`/`end` dates are inclusive **local** dates within the selected
file. The latest export is not an arbitrary historical archive, and filtering
does not fill absent requested dates. The result retains request records for
both discovery and file retrieval, plus source scope and time metadata.

The gallery includes a complete real native capture, its exact source URL,
checksum and first-week visualization. Use `energy-retrieve eskom-generation
--help` for immutable Parquet output with a provenance manifest.
