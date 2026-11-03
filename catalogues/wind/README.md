# Global Wind Database

Canonical JSONL lives in `records/`; projects, exact equipment configurations,
individual turbines and numerical curves share stable linked identities.

The proposed branch contains 5,355 project records (5,354 non-group records),
53 exact equipment records (51 turbines, one blade and one converter), two original numerical
power curves, 59 countries and six manufacturer names. Merged-main Wind totals
remain zero at `15e9d60b`. These are catalogue counts, not an operating census.

The initial 5,344-row WRI import is historical. The latest continuation enriches
642 existing identities through the complete REPD Q2 2026 Wind/crosswalk review,
adds 22 exact OEM records, and preserves all 642 capacity-scope exclusions.
2,216 other REPD applications remain deferred for identity review. No individual
turbine inventory has yet been imported. See the dated ledgers for per-run counts.

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
