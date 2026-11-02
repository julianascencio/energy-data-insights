# Worldwide BESS projects database

The battery energy storage section contains **1,292 records in 31 countries**
and **114 primary sources**. It complements the PV catalogue with its own 60-field
schema and typed Parquet export. It combines commercial projects and registry-defined plants, not a census
or a ranking of current installed capacity.

Open the [BESS project viewer](https://julianascencio.github.io/energy-data-insights/bess-database-viewer.html),
[Database gallery](https://julianascencio.github.io/energy-data-insights/auto_examples/database/index.html),
[catalogue/update guide](../catalogues/bess/README.md),
[data dictionary](../catalogues/bess/DATA_DICTIONARY.md), or
[latest research and reconciliation](../catalogues/bess/research/2026-11-01_expansion.md).

## Published snapshot

After a successful main documentation deployment, download:

- [Projects Parquet](https://julianascencio.github.io/energy-data-insights/datasets/bess/projects.parquet)
- [Snapshot manifest](https://julianascencio.github.io/energy-data-insights/datasets/bess/manifest.json)
- [Source registry](https://julianascencio.github.io/energy-data-insights/datasets/bess/sources.json)
- [Versioned schema](https://julianascencio.github.io/energy-data-insights/datasets/bess/schema.json)

JSONL is canonical in Git. Parquet uses Zstandard, native source lists, nullable
numeric fields and UTC timestamps. The browser projection comes from the exact
Parquet snapshot and carries matching checksums. Search all fields, filter
country/status/chemistry, choose columns, inspect evidence, compare groups and
export filtered CSVs. The existing PV viewer remains available separately.

## Metadata and interpretation

| Group | Standard fields |
| --- | --- |
| Identity and location | Stable UUID, name/aliases, country, region, locality, sourced coordinates, external IDs |
| Ratings | BESS power MW, energy MWh, electrical/energy basis, source-reported duration, charging MW |
| Configuration | Chemistry, standalone/co-located/microgrid, grid operator, substation, voltage, applications |
| Parties and equipment | Owners, developers, operators, EPCs, integrators, battery/PCS suppliers and models |
| Lifecycle and economics | Dated status, confirmed/expected COD, capital cost/currency/scope, design life |
| Evidence and maintenance | Source lists, per-field evidence, creation/update/access timestamps, conflicts, phases, extensions |

Unknown values remain null. Power and energy must never be combined into one
capacity column. A solar rating or site interconnection rating is not battery
output. Do not assume that MW is AC or MWh is usable energy when a source does
not state the basis. Source-reported duration is separate from any calculated
E/P ratio. U.S. inventory plant coordinates are retained as reported; UK grid coordinates
stay in native metadata. Many supplier/financial fields remain unpopulated.

Status is tied to its source date; it is not live availability. Old commissioning
releases remain historical evidence. Coya, Tamaya, Jurong Island, Salisbury and Edwards & Sanborn contain
unresolved rating or scope observations and are explicitly marked `needs_review`.
Phases and fleet totals are not additional project rows. Inspect `capacity_scope`
and `phases_json` before any aggregation, including partly operating projects.

## Reproducible offline analysis

```bash
uv run python -m energy_data_retrieval.bess_catalogue validate
uv run python -m energy_data_retrieval.bess_catalogue build --output artifacts/bess-v1
uv run python examples/database/plot_bess_projects.py
```

```python
import pandas as pd
from energy_analysis.pv_database import field_profile, grouped_statistics

bess = pd.read_parquet("artifacts/bess-v1/projects.parquet")
print(bess.groupby(["country_code", "status"], dropna=False).size())
print(field_profile("artifacts/bess-v1/projects.parquet"))
print(
    grouped_statistics("artifacts/bess-v1/projects.parquet", "country_code", "energy_capacity_mwh")
)
```

The shared `pv_database` analysis helpers accept any compatible Parquet schema,
including BESS. Reported sums describe selected source records only. They do not
harmonize rating bases, dates, status or scope and are not national market totals.

Source terms apply to exports. Only factual metadata and attribution are included;
no original articles or datasheets are redistributed. The U.S. EIA-860 2025 and UK REPD July 2026 snapshots are pinned by SHA-256.
See the catalogue guide for offline candidate staging and the explicit exclusion
ledger. Coverage remains strongly weighted toward the U.S. and UK; further
research should prioritize China, Australia, Chile and other national registries.
