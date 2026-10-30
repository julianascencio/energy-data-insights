# Colombia: XM SIMEM actual hourly generation

`XMClient` uses the public, credential-free SIMEM GET endpoint for dataset
**055A4D, Generación real**. It requests one inclusive Colombian civil day at a
time and one explicitly selected settlement revision. The return value is
`GenerationResult(frame, requests)` with HTTP hashes, byte counts and retrieval
times. Only `www.simem.co` is an approved source host.

```python
from datetime import date
from energy_data_retrieval.sources.xm import XM_HOSTS, XMClient
from energy_data_retrieval.transport import HTTPClient

with HTTPClient(XM_HOSTS) as http:
    result = XMClient(http).generation(
        date(2024, 6, 1), date(2024, 6, 1), version="TXF", resource_ids=["TPUY"]
    )
```

Dataset 055A4D contains actual hourly generation at generation boundaries from
2013 onward. The variable must be `GReal`, duration `PT1H` and unit **kWh**.
Normalized `value` is **MWh**, divided by 1000, with the original kWh retained in
`source_value` and `source_unit`. `CodigoPlanta` and `CodigoSICAgente` identify the
plant/resource and agent. This is not an installed-capacity dataset. The SIMEM
README's example E17D25 contains daily estimated SCADA and schedules and is
deliberately not used by this connector.

The same plant/hour can appear in revisions TX1, TX2, TX3, TX4, TX5, TXF and TXR.
The default is **TXF**. The server-side Version filter is used and the response is
checked again locally. If that revision is unavailable, retrieval fails; there
is no automatic fallback or summation across revisions. A caller seeking recent
provisional data must explicitly choose the corresponding available revision.

Native `FechaHora` labels are interpreted in Colombia's `America/Bogota` clock
(UTC−05) and converted to UTC without changing their interval-label convention.
The parser does not infer a start/end boundary that the public metadata does not
state. Null remains missing, zero remains zero, and negative measurements remain
negative. Identical rows are deduplicated; conflicting plant/hour observations
within the selected version fail.

Default limits are 31 one-day requests, one million native/returned records and
the shared HTTP response byte cap. Wrong datasets, granularity, unit, variable,
date, revision and absent requested resource IDs produce explicit errors.
`parse_generation` accepts a saved native JSON response offline.

Official sources (attribution: XM / SIMEM):

- [Actual generation dataset](https://www.simem.co/datadetail/055a4d5f-3616-45e3-9bcd-1d3e3a4a47bd)
- [Official dataset catalogue API](https://www.simem.co/backend-files/api/PublicData?datasetId=e007fb)
- [XM API reference client](https://github.com/EquipoAnaliticaXM/API_XM/blob/master/pydataxm/pydatasimem.py)

The offline gallery contains 72 actual records, three plants over one complete
source day, selected from a captured TXF response. Original metadata is retained;
JSON reserialization and record selection are documented with hashes. Cite XM
and the settlement revision when reusing or comparing results.
