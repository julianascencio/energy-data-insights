# Huntly phase reconciliation and further exact ECS configurations

1 November 2026, Atlantic/Canary (UTC). Started 22:48:56. Continues open PR #52
from bbae438; main 0cbb824 includes the separately merged PV PR #51. PR titles
and changed paths were inspected; #47–49 change workflows only. No competing
BESS database, automatic merge, parallel agents or PV edits.

## Accepted records and evidence

This iteration adds **two projects and 12 exact equipment configurations**;
zero existing-record enrichments, zero new quarantines and zero rejected rows.
All 1,276 prior project records and 150 prior equipment records, including their
creation/update/verification timestamps, remain byte-equivalent as parsed JSON.
Totals: **1,278 projects / 30 countries / 94 sources; 162 equipment records /
31 suppliers / 75 sources** (149 configurations, 13 configurable families).
No new country or manufacturer. Coverage across all six regions remains intact.

The official EA proposed-generation CSV was attempted before isolated releases:
164 rows, nine explicitly classified chemical battery proposals. Two match
existing Glenbrook-Ohurua/Ruakaka assets and are not reimported. Six remain held
for identity/freshness or aggregation review. One (Huntly Stage 1) is resolved
through a newer owner report, which also identifies a separate Stage 2.
The 2024 Stage 2+ 300 MW umbrella is not the 2026 Stage 2 100 MW project.
WEL's 35 MW Huntly entry must not be merged into Genesis' projects; possible
Rotohiko alias needs separate evidence. The ledger preserves all nine decisions.

Genesis' 22 October 2026 FY27 Q1 report, slides 4–5, explicitly identifies Stage 1
as operating at 100 MW / 200 MWh and Stage 2 as FID delivered at 100 MW / 200 MWh.
The April FID release supplies the latter's permitted status, 17 April FID date,
balance-sheet financing, expected ownership, Saft supply/service role and cost
scope. Reported capex is NZD 135m and NZD 106m respectively; real-price year is
unknown. Stage 2 cost includes contingency but excludes capitalised interest
and an FX management reserve. Planned fiscal quarters remain strings, not guessed
calendar dates. Neither phase has inferred chemistry, AC/DC basis, usable-energy
basis, equipment model or exact COD. No aggregate site record is added.
The previous HLY11 hold is resolved at the named-project lifecycle level; the
registry unit is not assigned to a phase without explicit evidence.

ECS4800-H2–H7 use the English April 2025 V2.0 PDF from the official Vietnam host;
ECS2800-H2–H7 use the Spanish July 2023 V1.4 PDF. All 12 columns and footnotes were
visually inspected. Fields include nominal DC energy, voltage ranges, charge and
peak currents, module counts, dimensions, weight/tolerances, cooling, IP rating,
altitude, temperature/humidity, communications and conditional cycle/RTE claims.
The 2800 weights retain ±1 to ±3.5 kg tolerances. Its 48 A maximum and 2,000 m
altitude are not copied from the 4800's 50 A / 3,000 m limits. Storage temperature
ranges also differ. These are documented revisions, not claims of current sale.
No active power, duration, warranty, certification validity or component/project
assignment is inferred. Manufacturer-listed standards remain qualified claims.

## Access, market context and remaining work

The indexed January 2025 ECS4800 and newer English ECS2800 URLs returned 404;
the UK ECS2800 link redirected to a missing file. Accessible official regional
PDFs were used instead, with exact revisions and SHA-256 hashes. No silent
cross-revision substitution. Raw CSV/PDF/HTML and rendered pages stay outside Git.
OEM/issuer documents are copyrighted; only bounded factual observations are
committed, not full documents or an asserted bulk-reuse licence. EA CC BY 4.0
policy and third-party exceptions were rechecked; the pipeline is used here as
a discovery/reconciliation source, not imported as unverified current projects.

Freedom Won's current download catalogue exposes individual Encore sheets and
manuals. Four previously held PCS candidates remain held for explicit product-level
mapping; the manual also distinguishes a UK 3.6K variant. This is useful backlog
progress, not four new accepted models. No contact, registration or paid access.

The dated IEA market comparison in `2026-11-01_india_fox_freedom_markets.json`
remains the reference: 2025 annual stationary-battery power additions, GW, ordering
only quantified countries (China, US, Australia, Chile); regional aggregates are
separate. A comparable worldwide operational-energy GWh ranking is unavailable.
This pass does not relabel annual MW additions as installed MWh.

Project yield is below the planning objective because the selected official
partition has only nine battery entries, with overlapping identities, stale
proposals and an aggregate expansion. Both six-model tables are exhausted and
the equipment objective is met. Next highest-value project source is the current
EA investment dashboard, followed by owner confirmation of Stratford, Manawatu,
Bunnythorpe and NZ Clean Energy Glenbrook. Equipment next: exact Encore PCS
representation and accessible newer ECS2800 revision/warranty, without new rows
for identical configurations. See the dated ranked backlog and review ledger.

## Validation and effort

Completed local validation at approximately 22:54 Atlantic/Canary / UTC: about
six minutes elapsed (four minutes discovery/reconciliation/implementation, two
minutes validation/publication preparation). Early completion follows exhaustion
of the selected inventory partition and two OEM tables, not an acceptance quota.

Both catalogue validators passed. Focused suite: 34 passed; after the final capex
column mapping, 28 catalogue tests passed again. Ruff lint/format (515 files), ty
with the project virtual environment, citation consistency and repository hygiene
passed. An initial ty invocation used the host environment and failed dependency
resolution; rerunning with the correct environment passed. Four viewer JS tests,
strict Sphinx with executable offline gallery and local-link checks passed.
Both offline BESS examples ran; typed Zstandard snapshots and independently
repeated manifests match. The preservation audit verifies all old records and
identities; new natural identities were reviewed against both incoming and stored
rows. No code/schema changed, so the full Python suite and package build were not
rerun in this data-only iteration. Remote CI is separate and pending publication.
PR #52 remains open, with no automatic merge.
