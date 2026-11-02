# Dyness exact models and Nordic/Baltic BESS projects

2 November 2026, Atlantic/Canary (UTC). Started 01:52:49. PR #54 was merged;
this iteration starts from main `ecedd9dde26a9f09940b94b5a722e40108387cd4`
in an isolated checkout. Open PRs #47–49 and #56–59 were inspected by title
and changed paths: CI/Pages or PV work, with no BESS overlap. The current
catalogue instructions, dictionaries, schemas, source registers, coverage and
recent Australia/Chile, Africa, Philippines and Pylontech/Saft logs were read.
Historical reports and unresolved Atacama/Solar Ray identities remain unchanged.

## Accepted records and useful enrichment

**Nine new projects, two substantively enriched projects and twenty new equipment
records.** Latvia is the new country; Dyness was already a supplier. No existing
OEM record changed. Current totals are **1,292 projects / 31 countries / 112 source
publications**, and **204 equipment records / 32 suppliers / 83 sources**
(191 configurations/components and 13 configurable families). Existing coverage
across all six requested world regions remains. Counts are researched catalogue
observations, not worldwide installed-capacity totals or a complete census.

New project identities are Akkula, Isbillen, Kelmė, Mažeikiai, Tume (Ignitis),
Kruonis, Nord Wind Park, AST Rēzekne and AST Tume. AST Tume's 20 MW / 40 MWh battery
is distinct from Ignitis Tume's 107 MW / 215 MWh solar co-location. Kruonis's 99.2 MW /
198.5 MWh electrochemical installation is distinct from the pumped-hydro plant
and its fifth hydro-unit expansion. Nord Wind Park's 20 MW / 80 MWh battery portion
is separate from 200 MW wind and 50 MW solar capacity; acquisition is not construction.
No aggregate Ignitis or Sunly portfolio record was created.

Evidence adds precise battery ratings, ownership shares and legal project companies,
construction/operating status, container counts, grid voltage/operator, integration
and construction roles, co-location, forecast operation years, services and investment
scope. Kelmė and Mažeikiai retain the annual report's project-specific acquisition
and construction investment estimates. Tume's approximately EUR 35 million figure is BESS
investment, not the separate solar project's expenditure. Price base remains unknown.
Kruonis retains 33 battery containers, 11 PCS containers, 110 kV connection and 95 MVA
transformer as distinct quantities. Its nearly EUR 47 million cost remains a qualified
extension rather than an exact capex point. AST's EUR 77.07 million combined investment
is portfolio context and is not allocated to each installation.

The AST annual market review confirms actual balancing-capacity participation from
29 October 2025, separately from the earlier opening/forecast announcement. Storen
gains 20 containers, 130 kV E.ON connection, Nidec integration, services and historical
40 MW / 40 MWh design context without changing its 52 MW / 52 MWh operating rating. E.ON
is the connected network; Svenska kraftnät is the service recipient. Yllikkälä Two
gains actual construction months, cable type and separately identified Destia/Despro
roles. All prior populated facts, stable IDs and creation timestamps are preserved.

Kelmė has one **quarantined energy field**: 294.8 MWh in the annual report, 295 MWh
in the current portfolio bullet and 294 MWh in the same page's prose. Its canonical
energy scalar is null and `quality_status=needs_review`, with all observations
and locators in `conflicts_json`. The other project facts are accepted. This is
not a wholly rejected or quarantined project. No record was rejected.

## Equipment and reproducible implementation

Five Tower models, thirteen explicitly named STACK100 strings, S51100 module
and SBDU100 control unit are accepted. Tower is distinct from the five existing
Tower Pro models. Every string is a real column in the OEM table; no option
cross-product or module-count enumeration from a mere family range was imported.
The separately specified components are not additional complete battery systems.

Captured specifications include nominal/usable energy distinctions, explicit
DC power and its rating kind where published, module counts, voltage bounds,
recommended/maximum/peak currents and peak duty/temperature, thermal envelopes,
dimensions/mass, chemistry, DoD, cycle lower bounds and conditions, warranty
limitations, communication, IP, cooling, fire equipment and qualified standards
claims. No active power is calculated from voltage/current. No duration, AC-to-AC
efficiency, cell supplier or project assignment is invented. Tower T21's printed
20.225 kWh usable energy is not replaced by a nominal-times-DoD calculation.

The 2025 STACK100 manual and 2026 family sheet have differing voltage, temperature
and dimensional specifications. The thirteen exact manual configurations are
explicitly `historical_document`; the newer family envelope is not extrapolated
across those columns. The dated review records both editions and differences.
Cycle-life time claims are not warranties, and certification lists remain
manufacturer claims. The current sheet separately specifies SBDU100.

A new offline source-specific adapter and CLI stage the thirteen exact model
identities, rounded energy values and voltage limits from the reviewed manual.
They reject another revision, missing/duplicate/reordered model columns, changed
units, truncated rows and invalid voltage bounds. Eleven synthetic tests cover
these failure modes. Original PDF and extracted-text SHA-256 fingerprints accompany
the staged candidates; all thirteen core records were reconciled with the accepted
canonical data. Staging never imports automatically. The existing `upsert_records`
API handled all accepted additions and enrichments; schemas were not extended.

## Source selection, access and remaining work

The scalable Eskom owner inventory was attempted first: 12 sites were reconciled,
seven already covered and five previous holds unchanged. WSP acceptance-date
metadata was already present. A newer, bounded Ignitis owner-portfolio/annual-report
batch and AST system-operator portfolio supplied the accepted Baltic projects.
Neoen supplied Nordic project evidence. Finnish, Swedish and Lithuanian sources
were read in their local languages as well as English.

Nine new plus two enriched records resulted from eleven accepted project identities.
Including the 12 Eskom comparisons, 23 project identities were fully reconciled. Four
additional discovery groups are held: the stale Kaunas pilot, Sunly Valmiera,
the other three unnamed-in-contract Latvian BESS sites, and the Risti MoU. These
groups are not counted as four fully reconciled projects. Sunly's 490 MWh aggregate
and solar-site MW cannot establish individual battery ratings or exact identity.
All 20 selected OEM candidates were accepted; Sungrow SBR/SBH discovery candidates
were already catalogued and were not duplicated.

All original downloaded bytes remain outside Git. Source registrations retain
exact URLs, publishers, revisions, retrieval times, locators and byte checksums.
Three Neoen country pages returned 503 directly but were readable as indexed primary
content; their unavailable-original-byte checksums are explicitly recorded. The
Yllikkälä publication reuses its established source ID rather than inflating sources
with a second ID for the same URL. Public access is not an open bulk-reuse licence.
Copyright and website notices were reviewed; only independently structured factual
metadata is committed, with no original prose, images, layouts or full documents.
No registration, contacts, payment or access-control bypass was used.

The market assessment rechecks IEA's named comparable metric: **annual 2025 stationary
battery power additions, GW**, including utility-scale and behind-the-meter systems.
China, US, Australia and Chile are ordered only among the quantified country examples;
Europe and Middle East remain separate regional comparisons. A comparable exhaustive
ranking of operational stationary energy in GWh was unavailable; no conversion from
GW or non-battery storage was made. The regional selection follows underserved
Nordic/Baltic coverage while retaining all six-region catalogue coverage.

Project yield is below 50–200 because the bounded owner/TSO batches contain few sites,
Eskom duplicates were excluded, and Sunly/Kaunas require additional scope/lifecycle
resolution. The 20 exact equipment additions meet the equipment planning objective.
Next actions are ranked in the backlog: Kelmė's technical annex to resolve energy;
AST connection tables for further battery identities; Sunly site-specific schedules;
a current exact-column STACK100 manual and warranty evidence. The selected three
OEM tables and the reviewed owner/TSO site batches are exhausted for defensible facts.

## Validation and publication

Research, implementation and validation ran from 01:52:49 through 02:16:16
Atlantic/Canary (UTC), **23.5 minutes** before the publication handoff. The selected
bounded source batches were exhausted; this pass did not idle to reach 45 minutes.

- Both catalogue validators passed; typed Zstandard Parquet snapshots rebuilt twice
  with identical manifests. Binary artifacts remain outside Git.
- Full Python suite: **1,545 passed, 1 skipped** (optional `cdsapi` unavailable).
  This includes eleven new parser/identity failure-mode tests.
- Real-manual staging produced thirteen candidates whose core fields exactly match
  the accepted manual configurations; PDF and text hashes are in the audit.
- Ruff formatting/checks and `ty check` passed. Repository check passed with
  1,918 candidate files and no flagged secrets/data; citation exports are consistent.
- Strict Sphinx build passed; documentation check resolved local links/assets across
  389 HTML pages. Viewer DOM tests: four passed.
- Both offline BESS usage examples passed. All three packages built sdist and wheel.
- Audit confirms stable existing IDs and creation timestamps, no erased existing
  facts, no timestamp-only changes, exact incoming/canonical identity reconciliation,
  and no invented project-to-equipment relationships.

The intended new scoped research PR remains open for review. These are accepted,
validated branch additions, not merged main-branch content. Publication rechecks
main and relevant open PR heads; no existing research PR is reused after closure.
