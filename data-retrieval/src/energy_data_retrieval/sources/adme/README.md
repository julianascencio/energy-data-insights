# Uruguay: ADME measured plant SCADA

`ADMEClient` discovers and downloads native measured SCADA SAS files from ADME's
public archive. The archive is linked from ADME's PRONOS application, but its
**SCADA** directory is distinct from the forecast directory. The connector never
fetches forecast files as actual generation. No credentials are required.

```python
from datetime import date
from energy_data_retrieval.sources.adme import ADME_HOSTS, ADMEClient
from energy_data_retrieval.transport import HTTPClient

with HTTPClient(ADME_HOSTS) as http:
    result = ADMEClient(http).generation(date(2026, 10, 22), date(2026, 10, 27), central_id=7)
```

Central ID 7 is Cerro Grande wind farm, as identified in ADME's own open-data
instructions. To find another plant's identifier, select it in the official
PRONOS application; the URL contains `central`. The connector does not invent a
countrywide plant catalogue or claim that one archive covers all generators.

Native SAS is a tab-separated text format with six header lines and Excel /
LibreOffice serial timestamps. `parse_scada_sas` validates the declared series
and sample counts and the sampling period. It selects the actual
`GETOTMEDP.AV` power channel when there is exactly one, or accepts an explicit
`power_series` among multiple such actual-power channels. Other channel names,
including wind speed, turbine count, dispatch limits and forecasts, are rejected
as the generation channel. Every native series
is retained; unnamed columns receive positional names. A unique
`CONSIGNAP.AV` is also exposed as `dispatch_limit_mw`, separate from actual MW.

ADME documents values below **−10000** as missing data. These become NaN, while
other negatives and real zeros are preserved. The native timestamp label is
interpreted in caller-visible `source_timezone="America/Montevideo"` by default,
then converted to UTC. Since the file provides no offset, this is an explicit
clock interpretation; callers can select another documented timezone. Ambiguous
or nonexistent local times fail. Floating serial-date roundoff is rounded to
whole seconds and checked against the header's sample grid. No interval energy
or interval boundary is inferred.

The archive exposes rolling seven-day files. The client uses one directory
request plus one file for each six-day requested chunk, chooses a suitable
published filename, and verifies that the native file covers every requested
local date. The default limits are 32 requests and 100,000 inspected rows,
plus the shared HTTP byte limit. Missing files, shifted headers, partial coverage
or changed schemas fail explicitly. No historical guarantee is inferred from
the currently listed files.

The older ADME PHP CSV exporter returned warning-contaminated output during
implementation. This connector uses the documented raw SCADA route instead.
`parse_scada_sas` supports saved native files without a live request.

Official sources (attribution: Administración del Mercado Eléctrico, ADME):

- [Open-data instructions and SAS format](https://www.adme.com.uy/datosabiertos.html)
- [PRONOS plant selector](https://pronos.adme.com.uy/svg/)
- [Measured SCADA archive](https://pronos.adme.com.uy/svg/pronos/cache_series_scada/)

The offline gallery uses one complete, unmodified 169-sample SCADA file for Cerro
Grande. Eight genuinely missing actual-generation readings remain missing. Its
manifest records URL, acquisition time and identical source/fixture SHA-256.
The dispatch limit does not measure curtailed energy; unavailable potential
generation requires separate evidence.
