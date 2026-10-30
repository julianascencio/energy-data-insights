# SMARD: German solar and wind generation

`SMARDClient.generation(start, end, technologies=...)` retrieves inclusive
German civil dates from Bundesnetzagentur's public chart downloads. This
connector supports region `DE` and the verified actual-generation series
`solar` (4068), `wind_onshore` (4067) and `wind_offshore` (1225).

```python
from datetime import date
from energy_data_retrieval.sources.smard import SMARD_HOSTS, SMARDClient
from energy_data_retrieval.transport import HTTPClient

with HTTPClient(SMARD_HOSTS) as http:
    result = SMARDClient(http).generation(
        date(2024, 6, 1), date(2024, 6, 2), technologies=["solar", "wind_onshore"]
    )
```

No API key is required. The client discovers actual week boundaries from each
series index, then downloads only overlapping weekly `quarterhour` files.
Epoch-millisecond interval starts are timezone-safe across 23/25-hour civil days;
the result is filtered to the requested dates in `Europe/Berlin`. Request and
row limits are explicit, and every index and weekly response has provenance.

## Units, scope and revisions

SMARD has **already converted upstream quarter-hour average MW into MWh**.
Native chart values are interval energy and must not be divided by four again.
`timestamp` is the UTC interval start, `interval_end` is 15 minutes later,
and `unit` remains `MWh`. Null values remain missing. Exact duplicate
observations collapse, while conflicting duplicate intervals raise.

These are national **net grid-feed** series, not plant telemetry or total
behind-the-meter generation. The selected solar/wind sources are not the whole
German generation mix. SMARD republishes checked data originating at ENTSO-E,
so comparisons with the ENTSO-E connector are not independent validation.
Revisions remain possible; original response hashes and source creation metadata
identify the exact downloaded publication.

## Sources and reuse

- [SMARD user guide: actual generation and MW/MWh convention](https://www.smard.de/resource/blob/205652/63fcff2c9813096fa2229d769da164ef/smard-user-guide-09-2021-data.pdf)
- [Data use and source attribution](https://www.smard.de/en/datennutzung)

The generation data use **CC BY 4.0**. Attribute **Bundesnetzagentur | SMARD.de**.
The gallery includes three unchanged, attributed weekly solar/wind responses
with retrieval metadata and checksums. The public chart-download interface is
validated against native schema version 1; schema changes fail explicitly.
