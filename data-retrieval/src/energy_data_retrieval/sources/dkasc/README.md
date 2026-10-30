# Desert Knowledge Australia Solar Centre

Import a measured native PV array CSV obtained through the
[DKASC download form](https://dkasolarcentre.com.au/download?location=alice-springs).
The form asks for user details and acceptance of provider data terms. This
connector works with the resulting export and does not submit that form for you.

```python
from pathlib import Path
from energy_data_retrieval.sources.dkasc import DKASCClient

# Replace these selections with exact names and the date format in your export.
result = DKASCClient().read_export(
    Path("inputs/dkasc_array.csv"),
    system_id="Your array",
    timestamp_column="Timestamp",
    timestamp_format="%Y-%m-%d %H:%M:%S",
    power_column="Your array - 5-Min-Avg kW",
)
```

The [official glossary](https://dkasolarcentre.com.au/glossary) defines five-minute
average AC power in kW, from one-second readings. Total (`kWtot`) and phase
(`kWa`, `kWb`, `kWc`) columns are also accepted, but not cumulative kWh registers.
Select one channel explicitly and do not add a total to its phases. Timestamp
format is explicit to avoid swapping day/month in native exports. Alice Springs
uses Australia/Darwin, UTC+09:30 with no daylight saving. The parser preserves the
source label and does not assume which edge of the five-minute interval it marks.

The full native table, selected power channel, signed/missing measurements and
input filename/SHA-256 are retained. The result has no HTTP request records.
Duplicate conflicts, invalid measurements, unexpected channels and row-limit
violations fail. Use `energy-retrieve dkasc-import --help` for immutable output.

[Provider terms](https://dkasolarcentre.com.au/download/terms-conditions) permit
small unaltered excerpts up to 5,000 data cells under attribution/disclaimer
conditions; larger redistribution requires permission. Check those terms for
your intended publication. No DKASC observations are bundled in the repository;
the gallery shows the import workflow until a real export is supplied.
