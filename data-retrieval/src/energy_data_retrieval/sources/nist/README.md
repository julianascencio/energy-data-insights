# NIST photovoltaic testbed exports

Import measured native CSV exports obtained from the [NIST PV portal](https://pvdata.nist.gov/).
This is a file import connector; it does not automate the portal's download
service or store transient download tokens. The public data describe the Ground,
Roof and Canopy research arrays in Gaithersburg, Maryland.

```python
from pathlib import Path
from energy_data_retrieval.sources.nist import NISTClient

result = NISTClient().read_export(Path("inputs/nist_ground.csv"), array="ground")
```

The default is one-minute `InvPAC_kW_Avg`, measured inverter AC power in kW.
`PwrMtrP_kW_Avg` selects AC meter power. Native TOA5 headers are supported and their
kW/Avg entries checked. One-second exports require both
`power_column="InvPAC_kW"` and `resolution="one-second"`. Cumulative energy
registers are excluded from power-channel selection. Original columns, negative
values and missing `NAN` readings remain available.

The [NIST measurement paper](https://doi.org/10.6028/jres.122.040) specifies fixed
Eastern Standard Time, UTC-05:00, with no daylight saving. The
[data dictionary](https://www.nist.gov/document/datadictionarysupplementalcontentpdf)
specifies `TIMESTAMP` in local standard time and kW power units. The parser uses
that clock by default and preserves the native timestamp label without inventing
an averaging-interval edge. An explicit timezone override is available for a
separately documented transformed export.

`read_export` returns a `GenerationResult` with no HTTP request records and with
the exact local input's filename/SHA-256 in frame metadata. Input parsing is
bounded; conflicting duplicates, wrong units and invalid values fail. The gallery
is an offline import guide until `NIST_PV_CSV` points to a real downloaded file.
No NIST observations are fabricated or bundled. Use
`energy-retrieve nist-import --help` to save a Parquet snapshot and manifest.
