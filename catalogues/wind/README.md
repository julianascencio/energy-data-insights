# Global Wind Database

Canonical JSONL lives in `records/`; projects, exact equipment configurations,
individual turbines and numerical curves share stable linked identities.

The proposed branch contains 7,706 project records (7,705 non-group records),
265 exact equipment records, 11,895 registry turbine records and two original numerical
power curves, across 59 countries and eleven equipment manufacturer names.
Merged main at `6b38f9a4` contains 7,582 projects, 264 equipment records and 10,264 turbines
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


## Thüringen, Västra Götaland and line chokes

This batch adds 618 projects, 2,030 turbines and 23 exact LCVS/LCVT line chokes.
Merged main at the iteration baseline contains 6,713 projects, 202 equipment,
5,745 turbines and two curves; proposed totals are 7,331 / 225 / 7,775 / 2.
All 12,662 preceding records and capacity totals are unchanged. Complete registry
partitions were reviewed; 371 German groups and 226 Swedish areas remain held.
Thirteen duplicated Swedish turbine IDs quarantine their entire parent scope.
Missing area boundaries remain null. All new project scopes are excluded from MW totals.

OEM pp52–56 preserve explicit inverter pairings and original dimension letters.
LCVT025 has conflicting inductance/loss rows; scalar values and the disputed
ACU410-23 pairing are held. No guessed correction or turbine compatibility is added.
The remaining 13 AL-suffix types are the next bounded equipment partition.


## Sachsen, Värmland and electrical components

The 23:35 increment adds 70 projects, 636 linked turbines and 28 exact equipment
types: 13 AL-suffix line chokes and 15 EMC filters. Proposed totals are 7,401
projects, 253 equipment, 8,411 turbines and two curves. Merged main at `7af547f9`
contains 6,713 / 202 / 5,745 / 2; PR #119 cumulatively adds 688 / 51 / 2,666 / 0.
All 15,333 records preceding this increment and all capacity totals are unchanged.
The completed Sachsen partition has 482 held groups; Värmland has 44 held areas
covering 734 turbine rows. All 70 accepted project scopes remain excluded from MW totals.

AL-choke current and dissipation depend on the printed inverter application;
common inductance and assembly dimensions stay on one exact component record.
Two choke-to-inverter links lack a frame identifier and remain held. One filter
application prints ACU210-12, which has no exact existing configuration; its label
is retained without an inferred alias. EMC class/cable conditions remain qualified,
and the general 480V heading is not silently applied to the ACU610 application.
Next: Saarland, Örebro and book-filter assembly tables pp62–63.


## Saarland, Örebro and braking resistors

The 4 November increment adds72projects288turbines11exactBRresistor types and
enriches12EMCfilters with assembly specifications (R04_0 pp62–65).
Saarland114groups andÖrebro25areas/166units remain held. New project scopes
remain excluded from MW totals. Two-resistor combinations retain quantity and
combination ratings within one component record; no artificial assembly model.
HLD110-500/42dimensions and thermal-switch assignments remain unknown.
All previous scalar ratings and creation timestamps are preserved.


## City states, Västmanland and Dalarna

The 4 November continuation adds 53 projects and 637 linked turbines, and
enriches 11 existing resistor records with legacy VEC501R0 electrical, thermal,
mass, terminal and original drawing observations. Current-revision claims are
not inferred. The 103 German groups and 47 Swedish areas held for identity
review remain in decision ledgers. All new project scopes stay excluded from
capacity totals; all previous values and creation timestamps are preserved.


## Gävleborg and offshore identity screening

The 4 November 02:35 increment adds 56 Gävleborg project areas and 928 linked
turbines from all 88 areas and 2,124 turbine observations. The remaining 32
areas/1,196 observations are held for identity/scope review. All 1,813 German EEZ
units were screened across 48 name groups; aliases and sub-array labels prevent
automatic farm additions. The existing E-82 E2 gains revision-qualified 08/2019
base-model specifications. Two restricted Bonfiglioli manuals are excluded.
No new project enters capacity totals; all prior specifications are preserved.


## Västernorrland continuation

The 03:35 batch reviews 97 areas and 2,177 linked/orphan turbine observations,
adding 55 projects and 847 turbines. Forty-two areas and 117 orphan turbines
remain held; no project capacity is inferred. All previous records are unchanged.
The reusable quarantine helper now rejects missing IDs before grouping, so
missing identities cannot be silently hidden as duplicate conflicts.


## Jämtland and converter monitoring

The 04:35 batch reviews all 138 Jämtland areas and 1,729 turbine observations,
adding 69 projects and 784 linked turbines. The remaining 69 areas and 945
turbines are deferred; no project capacity is inferred. ABB system description
3AXD50000022022 Rev C (2020-04-27), pp. 13–14 and 24–25, supplies separately
dated system interfaces for 15 existing exact converters and explicitly names
the optional NETA-21 monitor. Its record and compatibility links preserve that
series/revision boundary; historical ratings are unchanged. Detailed monitor
limits remain unknown after an HTTP 403 download failure. Catalogue claims
are manufacturer documentation, not independently validated performance.
