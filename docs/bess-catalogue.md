# Worldwide BESS projects database

The new battery energy storage section starts with **37 projects in 22 countries**
and **30 primary sources**. It complements the PV catalogue with its own 60-field
schema and typed Parquet export. This is an initial global sample, not a census
or a ranking of current installed capacity.

Open the [BESS project viewer](https://julianascencio.github.io/energy-data-insights/bess-database-viewer.html),
[Database gallery](https://julianascencio.github.io/energy-data-insights/auto_examples/database/index.html),
[catalogue/update guide](../catalogues/bess/README.md),
[data dictionary](../catalogues/bess/DATA_DICTIONARY.md), or
[launch research notes](../catalogues/bess/research/launch_report.md).

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
E/P ratio. Coordinates and many supplier/financial fields remain unpopulated.

Status is tied to its source date; it is not live availability. Old commissioning
releases remain historical evidence. Coya, Tamaya and Jurong Island contain
unresolved rating observations and are explicitly marked `needs_review`.
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
no original articles or datasheets are redistributed. The next useful expansion
is audited national registry ingestion and more primary project evidence,
particularly across Africa, Asia and Latin America.
