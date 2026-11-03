# Global Wind Database

Canonical JSONL lives in `records/`; projects, exact equipment configurations,
individual turbines and numerical curves share stable linked identities.

The first proposed batch contains 5,355 project records (5,354 non-group records)
in 59 countries, 30 exact turbine configurations across three manufacturer names,
and two original numerical power curves. The 5,344-row WRI partition is historical,
not a current operating census. Thirteen project records have additional primary
source evidence, including two enrichments within the initial import. No individual
turbine inventory has yet been imported. Merged totals were zero at the baseline.

See [the evidence guide](../../docs/wind-catalogue.md),
[viewer source](../../docs/wind-database-viewer.rst),
[batch checkpoint](research/latest.json), [ranked backlog](research/backlog.json),
[source registry](sources.json), and
[schema](../../data-retrieval/src/energy_data_retrieval/wind_catalogue/schema.json).

```bash
uv run python -m energy_data_retrieval.wind_catalogue validate
uv run python -m energy_data_retrieval.wind_catalogue build --output artifacts/wind-v1
uv run python examples/database/plot_wind_catalogue.py
```

Use a fresh output path. Parquet is reproducibly generated, not committed; Sphinx
publishes it with the viewer. Unknown stays null. Parent totals, unresolved scopes
and overlapping generations are excluded from capacity summaries, which separate
lifecycle states. OEM curves and specifications are not operational validation.
