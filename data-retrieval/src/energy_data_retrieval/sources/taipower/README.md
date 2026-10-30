# Taiwan: Taipower live generation

Read Taipower's public JSON snapshot of net generation from self-owned and
purchased generation. The snapshot contains reported assets, grouped assets,
technology subtotals and separate storage charging rows.

```python
from energy_data_retrieval.sources.taipower import TAIPOWER_HOSTS, TaipowerClient
from energy_data_retrieval.transport import HTTPClient

with HTTPClient(TAIPOWER_HOSTS) as http:
    result = TaipowerClient(http).latest()
```

The source updates every ten minutes, but **this is not a documented ten-minute
average**. Values remain **MW power snapshots** with `measurement_kind` explicitly
set. The timestamp is interpreted in `Asia/Taipei` and converted to UTC. No energy
integration is implied. The source's installed capacity is a separate MW field;
missing capacity during trial operations remains missing.

Default parsing excludes recognised group labels/subtotals and storage-load rows.
Pass `include_aggregates=True` and/or `include_storage_load=True` to retain them
with `aggregation`, `is_total`, `is_aggregate` and `flow` labels. A reported asset
can be a generating unit or a plant: the display label does not establish a
complete equipment registry. Original Chinese technology, asset labels, status
notes and snapshot datetime are retained, including communication/fault notes.

`parse_generation` reads an acquired snapshot without network access. `latest`
bypasses the public cache, imposes response/row limits and records provenance.
The gallery includes one genuine complete response with an unmodified-byte hash.
The source is free under Taiwan's **Open Government Data License 1.0**.

The separate large historical JSON feed is documented by the publisher but is
not fetched by this bounded live-snapshot connector.

- [Official live dataset and licence](https://data.gov.tw/en/datasets/8931)
- [Historical dataset, publication lag and EMS limitations](https://data.gov.tw/en/datasets/37331)
