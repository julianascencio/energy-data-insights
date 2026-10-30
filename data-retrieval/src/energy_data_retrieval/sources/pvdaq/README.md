# PVDAQ / OEDI measured PV systems

Public [OEDI PVDAQ archive](https://data.openei.org/submissions/4568), with the
[official schema](https://github.com/openEDI/documentation/blob/main/pvdaq.md).
`PVDAQClient` reads one system's explicitly selected daily CSV partitions and
retains native sensor columns. It does not download an entire bucket.

```python
from datetime import date
from energy_data_retrieval.sources.pvdaq import PVDAQ_HOSTS, PVDAQClient
from energy_data_retrieval.transport import HTTPClient

with HTTPClient(PVDAQ_HOSTS) as http:
    client = PVDAQClient(http)
    channels = client.metrics(4).frame
    result = client.generation(
        4,
        date(2023, 1, 1),
        date(2023, 1, 1),
        power_column="ac_power__315",
        unit="W",
        source_timezone="-07:00",
    )
```

`metrics(system_id)` retrieves provider Parquet channel metadata, including units,
calibration fields and aggregation type; `system_metadata(system_id)` reads the
public site/system metadata. These metadata calls are separate from measurements.
For the example channel, scale=1, offset=0, units=W and aggregation=avg. The CSV
values are retained without reapplying calibration. Select the actual power
channel, units and source clock explicitly for another system. Numeric catalogue
offsets and CSV column names alone are not enough to infer these semantics.

Dates are inclusive source-calendar dates. A missing daily file raises a retrieval
error. Default limits are 31 daily requests and 1,000,000 rows, plus the shared
HTTP byte cap. Invalid/infinite numbers, wrong system/date and conflicting records
fail; signed, zero and missing measurements remain unchanged. Local DST labels
that cannot be mapped uniquely to UTC are rejected.

The gallery includes a real complete day of system 4, its channel metadata and
source/selection/checksum manifest. The fixed UTC-07 offset shown is explicit for
that winter date, not a convention asserted for every PVDAQ site or season.
Use `energy-retrieve pvdaq-generation --help` and `pvdaq-metrics --help` for
immutable Parquet snapshots and provenance manifests.
