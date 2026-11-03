# Residential equipment and owner-history follow-up

Started 3 November 2026 at approximately 23:48 Atlantic/Canary (UTC). Continued
open PR121 at d74a8e6 in an isolated worktree. Main advanced to7af547f (PV build/type
fixes); merged main locally without changing its files. Open PRs119/120/122/124/125
were inspected by titles and changed paths: no overlap with these catalogue writes.
The older PR44 checkpoint is historical. Existing schemas, source registries,
research workflow, dictionary/manifest conventions and PV upsert were reused.

## Accepted partition

The complete named tables on PDF pages13,17,18 of BSLBATT's 2026 residential
catalogue yield12 new exact configurations: three B-LFP48-PW wall batteries,
five MatchBox HVS stacks and four PowerNest LV systems. Model columns and merged
cells were checked against rendered pages. Capture includes nominal versus usable
energy, rated versus one-second discharge power, separate charging limits, cell/
module arrangement, voltage limits, temperature by mode, mass/dimension tolerance,
communications, and qualified warranty/life claims. No inferred duration, inverter
model assignment, chemistry for PowerNest, or independently verified certification.
The PW safety row applies to an old200PW version; it is not assigned across models.

Page12 adds useful contradictory evidence to three existing rack models:95%DoD
and new usable-energy values versus90% in the prior individual sheets. Their old
ratings, original evidence and dimension conflicts remain intact. Undated edition
applicability is unresolved. Four new PowerNest records retain malformed dimension
separators and the unusual PF interval in quarantine; no silent correction. This
is seven records with new field holds, not seven rejected or extra model records.

The four-island owner Annual Report2024 portfolio was reviewed as the project batch.
All four existing Cabo Verde projects gain programme implementation and shareholder
bridge-finance history. São Vicente/Boa Vista also gain public-tender award history.
These are programme statements, not site-specific construction/COD dates or finance
allocations. Original download returned403; the public document reader was used and
original checksum remains null. Report publication evidence is the27March2025 board
date. No older statement overwrites later lifecycle evidence.

EIB's financed-project inventory, terms and release2025-483 were examined. No bulk
export or individual battery loan allocation was accepted: mixed wind/battery finance
cannot be assigned to each site. Its terms do not establish an open bulk-reuse licence.
The owner report was the alternative. Source documents/images stay outside Git;
only bounded factual observations and locators are committed. No access bypass.

## Yield and next partition

15 reviewed equipment identities:12 new,3 substantively enriched. Four reviewed
project identities:0 new,4 enriched. No whole-record rejection or new whole-record
quarantine. Existing HV PACK, Eskom and other holds remain unchanged. New countries
and suppliers: none. Proposed totals1,989 projects/41 countries/308 sources and
749 equipment/46 suppliers/366 sources (736 configurations,13 families).

The selected exact-model tables and owner portfolio are exhausted. Project yield
falls below the planning target because this is a four-site existing portfolio and
financing aggregates do not establish new sites. Equipment target is met. Li-Pro,
PowerLine and ECO pages are separate unprocessed partitions, not invented accepted
variants. Next: exact Li-Pro table and current rack contract/edition applicability;
for projects obtain site acceptance/as-built documents or a licensed registry export.

The same-day IEA market comparison in2026-11-03_poland_containers_markets.json
remains the planning basis:2025 annual stationary power additions(GW), quantified
examples China>US>Australia>Chile. This is neither a comprehensive ranking nor
operational energy(GWh); the latter remains incomparable/unavailable. All six
regions remain covered; this pass deepens African evidence and residential equipment.

Existing importer/upsert accepted new identities. Its seven collisions for additive
nested evidence were explicitly reviewed: append new history/conflict observations,
retain old values and created_at, update only changed records. Preservation and
repeated typed Zstandard snapshot manifests accompany this log. No schema/parser
changes, binary commits, merges of the PR or timestamp-only records.

Validation completed at 23:57:41 Atlantic/Canary after approximately 9.2 minutes. Full suite:2,124 passed;28 final catalogue and29 reference tests;15 viewer tests; lint,format,repository typing,citations,hygiene,offline examples,package builds and strict documentation passed. See validation JSON for exact checks and corrected attempts.
