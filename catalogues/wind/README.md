# Global Wind Database

Canonical JSONL lives in `records/`; projects, exact equipment configurations,
individual turbines and numerical curves share stable linked identities.

The proposed branch contains 6,713 project records (6,712 non-group records),
202 exact equipment records, 5,745 registry turbine records and two original numerical
power curves, across 59 countries and eleven equipment manufacturer names.
Merged main at `273fe81f` contains 6,574 projects, 168 equipment records and 5,190 turbines
and two curves. These are catalogue counts, not an operating census.

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

The 11:35 increment adds 192 Östergötland project areas, 559 linked turbines and
four exact ENERCON configurations. Thirty-five areas remain held; no prior
record or capacity total changes. See the 1135 ledgers for source partitions.

The 12:35 increment adds 22 Schleswig-Holstein parks and 105 linked MaStR units
from a complete 4,788-unit state partition, plus two exact ENERCON models with
qualified optional yield modes. All 6,565 preceding records remain unchanged.
The 1,717 deferred name groups retain explicit decisions; accepted park scopes
remain excluded from capacity totals. See the 1235 ledgers.

The 13:35 increment reviews all9,034 Niedersachsen units, adding73parks and366
linked turbines;2,973namegroups remain held. Two exact Winergy integrated
gearbox-generator assemblies add component coverage. Capacity exclusions remain.

The14:35 increment adds67Nordrhein-Westfalen parks,314linked turbines and14NGC
yaw/pitch gearbox types. All6,753state units reviewed;2,665namegroups held.

The15:35 increment adds131projects and791turbines from complete Brandenburg and
Jönköping partitions, plus nine Bonfiglioli gearbox models. All prior rows remain.

The16:35 batch adds64projects,433turbines and15exact ABB converter types.

The17:35 batch adds168projects/918turbines and enriches15existing ABB models.

The18:35 batch adds83projects,369turbines and18exact ACU401inverters.

The 19:35 batch adds 52 projects, 188 turbines and 20 exact ACU configurations
from complete Mecklenburg-Vorpommern/Blekinge partitions and OEM type tables.
All 10,529 preceding records and six capacity totals remain unchanged.

The 20:35 batch adds 295 projects, 826 turbines and 24 exact ACUx10 configurations
from complete Rheinland-Pfalz/Skåne partitions and R04_0 frame7/8 tables.
All 10,789 preceding records and six capacity totals remain unchanged.


## Hessen, Halland and remaining ACUx10 tables

The 21:35 continuation follows merged PR #111 and preserves the new gallery hierarchy.
Complete Hessen (1,807 units / 627 groups) and Halland (176 areas / 691 units)
partitions add 139 projects and 555 linked turbines. All 11,934 preceding records,
prior source entries and six capacity totals remain unchanged. All new scopes
remain excluded pending phase and repowering reconciliation. Holds cover 589
German groups and 75 Swedish areas plus two orphan units (306 turbine rows).
No country or manufacturer is newly counted.

Bonfiglioli R04_0 pages 19–23 (`bonfiglioli_acu_r04_0`) supply 34 exact
configurations: 12 ACU210 and 22 ACU410 columns. The source checksum was reverified
and all five tables visually reviewed. Input-phase ratings and column-specific
line-choke requirements stay distinct. Standard, coldplate and liquid dimensions
and brake options remain nested. ACU410-12 is explicit on page 21 despite its
omission from the nomenclature summary. Unclaimed approvals remain unknown.
Series yaw applicability is documented; turbine compatibility and independently
validated operational performance are not inferred. The gallery includes the new
230 V ACU210 entries.
