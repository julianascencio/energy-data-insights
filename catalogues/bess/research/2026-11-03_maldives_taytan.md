# Maldives project reconciliation and TESVOLT exact configurations

Research checkpoint: 3 November 2026, 20:04 Atlantic/Canary (UTC+00:00).
Started 19:47:30 UTC; approximately 17 minutes of active discovery, extraction,
implementation and validation through this checkpoint. Publication and concurrency
checks follow; their timestamps are recorded in the accompanying concurrency ledger.

## Baseline and accepted changes

PR #102 had merged at 19:19:59 UTC. This isolated checkout starts from main
`2fd691a7a3f2f55b0c24748c5a8299d844d27b85`; it does not reuse a closed PR.
The November 1 PR #44 totals are historical. Current baseline was 1,926 projects
in 40 countries / 295 sources, and 707 equipment rows / 45 manufacturers /
354 sources. Repository instructions, current schemas/dictionaries, source registers,
coverage manifests, recent BESS/PV research conventions and open PR paths were reviewed.

| Entity | Candidates reviewed | New | Substantively enriched | Held | Deleted |
|---|---:|---:|---:|---:|---:|
| Projects | 40 | 21 | 18 | 1 | 0 |
| Exact equipment configurations | 13 | 11 | 0 | 2 | 0 |

Four project fields retain unresolved evidence: three historical ASSURE energy
ratings and Thoddoo's grid connection. Two further discrepancies concern programme
totals, not additional projects. No whole accepted record was quarantined; no
equipment field conflict was introduced. Held candidates are not accepted rows.

Proposed totals: **1,947 projects / 40 countries / 299 sources**, and **718 equipment
rows / 45 manufacturers / 357 sources** (705 configurations and 13 family rows).
There are no new countries or manufacturer entities. All six existing world regions
remain covered. These counts describe catalogue coverage, not installed capacity.

## Primary batches and identity review

- **ARISE:** all 18 rows in the ministry's 9 December 2021 screening table, matched
  to the August 2022 tender and Gazette procurement notice. Added historical energy,
  container/area estimates, atoll/island, applications, procurement lot and identifiers,
  proposed dates and qualified land ownership. No installed container count, actual
  COD, site power or current asset owner is inferred. The two Addu electricity grids
  remain distinct; Isdhoo–Kallaidhoo–Dhanbidhoo is one shared-grid record. Laamu
  Hithadhoo is not Addu Hithadhoo. The 32.7 MWh table sum is not scaled to the
  approximate 37 MWh cover or subsequent 40 MWh tender. Lot MW/MWh and financing
  stay in explicitly non-site extensions.
- **ASSURE:** all 20 rows of the March 2023 draft IEE Table 7. Eighteen manually
  matched existing projects gain chemistry, microgrid configuration, powerhouse
  siting, grid upgrades, associated PV type, planned operating arrangements and
  battery end-of-life requirements. Later 2025 signed-programme ratings remain
  canonical; the three different older estimates remain evidence conflicts.
  Added the two flow pilots without promoting anticipated vanadium to confirmed
  electrolyte. The table's 43.3 MWh and prose's 44 MWh remain separate observations.
- **Thoddoo:** one 626 kWh irrigation battery project, comprising 96 and 530 kWh
  banks, with 191.9 kWp associated PV. Its contradictory connected/off-grid design
  claims leave connection type null. Inverter kVA does not become battery MW.
  March-only document dates are explicitly normalized to reporting month-end,
  not represented as exact event dates. A further Manadhoo wind-pilot battery is
  held because its relationship to the existing 3 MWh project is unresolved.
- **TESVOLT:** all eight exact TAYTAN/03-40 through /10-40 columns, one FORTON/12-30,
  and two TS HV 90/10-20 and /12-20 assemblies. Added explicit energy, battery power
  where stated, voltage/current, chemistry, module counts, dimensions/weight,
  temperature/altitude, cooling/IP, test conditions, cycle claims and qualified
  warranty/throughput observations. TAYTAN remains preliminary; undeveloped
  efficiency/auxiliary specifications remain null. The FORTON printed document
  number differs from its filename and is retained. External PCS and cell suppliers
  retain their roles; none is assigned to a Maldives project. Two TPS HV E string
  candidates are held for possible overlap with existing cabinets, rather than
  multiplied into hypothetical container/inverter configurations.

The JSON review ledger contains every accepted candidate ID, explicit matches,
source URLs, retrieval timestamps, document versions, page/table locators and
download SHA-256 values. Canonical field evidence maps to those sources; row/model
locators are preserved in extensions. The preservation audit confirms unchanged
created timestamps, no removals or erased non-null facts, and no changes to existing
project names, energy, status or status-as-of dates.

## Access, scope and next partition

Public access was not treated as an open bulk licence. This pass extracts bounded,
attributed factual observations; no source PDF, image, contact details or binary
dump is committed. TESVOLT legal terms and the borrower-report/ADB terms qualification
were reviewed. Downloaded bytes and visual checks remain outside Git under
`/tmp/bess1947`; HTTP error hashes are explicitly identified as error-response hashes.

Migrated ministry URLs returned 503/404, but original legacy downloads succeeded.
The ADB IEE landing returned 403; the ministry original supplied the reviewed report.
AIIB's December 2025 progress report was reader-accessible but the original file
returned 403 on two public host variants. Programme-wide civil-work statements
were not promoted to per-site current status. Eydhafushi commissioning discovery
has inconsistent 1.5/1.7 MWh claims; obtain primary final ratings before replacing
the historical 1 MWh design observation.

The dated market comparison reuses the same-day verified
`2026-11-03_poland_containers_markets.json`: IEA's **2025 annual stationary battery
power additions (GW)**, ordered among quantified countries as China, United States,
Australia and Chile. This is neither an exhaustive ranking nor operational energy
in GWh. Comparable worldwide operational GWh remains unavailable; no conversion
from power was made. This iteration deepens an underserved island market rather
than repeating US bulk ingestion.

The project working objective was not reached because the selected defensible
named tables contain 39 accepted identities, with one additional scope ambiguity;
they are exhausted, not artificially expanded by connected islands, battery banks
or portfolio totals. The 11 exact equipment additions meet the equipment objective.
Finishing before 45 minutes reflects exhausted reviewed batches, not an idle timer.
Next highest-value scalable partition: obtain the **named POISED completion/island
battery register** (the 70-island aggregate is insufficient), then rotate to an
underserved African or Latin-American official owner inventory. First enrichment
priority is current ARISE site commissioning and final ratings. The ranked backlog
records offered fields, access/reuse limits, processed partitions and retry conditions.

## Implementation and validation

`scripts/stage_bess_arise.py` and the package adapter stage the reviewed local
`pdftotext -layout` table without assigning identities. They fail closed on changed
revision, units, page, missing/duplicate sites and non-positive observations. Nine
synthetic parser/identity tests avoid redistributing the original document. Accepted
records use the existing upsert API; the 18 collision reports were manually reviewed
as evidence augmentation rather than automatic fuzzy merges.

Checks actually passed:

- Both catalogue validators, reference checks and preservation audit.
- 37 focused tests; full Python suite: **1,990 passed**.
- Repository-wide Ruff lint/format, ty, repository hygiene and citation checks.
- Viewer DOM/logic: **15 passed**; both offline BESS usage examples.
- Strict Sphinx build with all gallery examples; **469 HTML pages** passed local
  link/asset checks.
- All three packages built as wheels and source distributions; strict Twine
  checks and fresh-environment wheel installation/public-entrypoint smoke tests.
- Two independent typed Zstandard Parquet builds per catalogue produced identical
  manifests/hashes; committed coverage/completeness manifests describe these outputs.

The first Ruff run identified ambiguous Unicode punctuation in parser literals;
explicit escapes fixed it and the rerun passed. Raw sources and Parquet remain
outside Git. The existing documentation build regenerates downloadable catalogue
assets; its established Pages artifact is uploaded only after a main-branch build.
No release, Pages deployment or merge is performed by this iteration.

Open Wind #106 and forecasting #107 modify shared citation files. Seven new
bibliography entries are therefore queued in the scoped pending-reference ledger;
their canonical source registers are complete. No shared bibliography/schema/importer
API was overwritten. Validation details and pre-publication main/PR checks are in
the companion JSON ledgers. Remote CI results are separate from these local checks.
