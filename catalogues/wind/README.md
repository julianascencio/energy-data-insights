# Global Wind Database

Canonical JSONL lives in `records/`; projects, exact equipment configurations,
individual turbines and numerical curves share stable linked identities.

The proposed branch contains 5,427 project records (5,426 non-group records),
60 exact equipment records, 321 registry turbine records and two original numerical
power curves, across 59 countries and seven equipment manufacturer names.
Merged main at `5063c416` contains 5,355 projects, 53 equipment, zero individual
turbines and two curves. These are catalogue counts, not an operating census.

The initial 5,344-row WRI import is historical. REPD lifecycle enrichment does
not resolve capacity scope; 2,216 other applications remain deferred. Swedish
registry areas and their explicit turbine children also stay outside project
capacity totals until physical phase/repowering scope is reconciled.

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

The 2026-11-03 08:35 continuation adds 232 previously omitted procedural dates
to 114 linked UK projects, preserving all lifecycle and capacity fields. The first
200 unlinked applications remain deferred after structural review. Refusals and
later successful appeals are history, not contradictory current statuses.

The 09:35 Canadian continuation reviews all 327 NRCan project groups and enriches
117 existing identities with inventory fleet details; 210 remain deferred.
Lifecycle and all capacity exclusions remain unchanged. Individual turbines
and exact OEM records are not inferred from inventory model labels.

The 10:35 continuation processes all 89 land-based registry areas and 348 turbine
rows in Stockholm, Uppsala and Södermanland. It adds 72 named project identities
and 321 linked turbines; 17 areas and two orphan turbine rows remain deferred.
Seven current VENSYS technical sheets yield seven exact configurations. The
VENSYS 136 sound-power conflict remains null with both observations preserved.
