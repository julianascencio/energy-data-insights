# Energa procurement, TAURON funding and exact BYD configurations

Started 3 November 2026 at 15:54:21 Atlantic/Canary (UTC), from open PR #102
head `bb1f4c98` and main `5063c416`. PR #44 is historical. Current instructions,
workflow, schemas/dictionaries, source registers, manifests and prior research
ledgers were reviewed. Starting-head Python/package and docs CI passed. Work was
isolated; no schema, importer, shared viewer or bibliography files were changed.
PV #103 advanced during this pass; its incremental changed paths were inspected
and remain PV-only. Wind #101 and Data Center #100 are separately scoped.

## Accepted changes

**Projects: 24 selected candidates → 3 new records, 20 substantively enriched,
one held.** This is a national funding register joined to independently verified
owner battery identities, not an indiscriminate storage-programme import.

The refreshed NFOŚiGW signed-contract register contains 179 electricity-storage
rows. Its downloaded SHA256 is identical to the earlier same-day observation.
Eleven complete TAURON titles match existing manually reviewed aliases; these add
contract IDs, funding beneficiary roles, grant amounts and source-row locators.
Signed grants do not establish disbursement, construction or operation. Proposed
investment budgets and actual expenditure remain separate.

The owner release of 8 December 2025 adds seven missing battery MWh ratings and
province evidence: Laryszów, Ogrodzieniec, Bałków, Twardogóra, Dąbrowa Środkowa,
Stare Bogaczowice I and standalone Bytom. The exact MW/site combinations distinguish
these from other phases and the Bytom hybrid. Gross/usable and AC/DC bases remain
unknown. An eighth observation, Kuźnia Raciborska at 30 MWh, conflicts with the later
9 December 28 MWh release. Both are retained, the prior canonical 28 MWh stays,
and the discrepancy is quarantined. No derived duration or silent rating replacement.

The original Energa EGD/0001/2026 public ZIP resolves three previously held sites:
**Barczewo, Działdowo and Wąbrzeźno**. Each is a separately named task adding battery
storage to an existing PV installation. Common technical requirements explicitly
refer to cells, battery modules, BMS and bidirectional inverters. Exact title and
beneficiary matches add signed grants; a freshly downloaded, checksum-identical
ranking adds application IDs, proposed battery investment costs and regions.
These three records have meaningful identity, commercial, lifecycle and co-location
metadata; technical MW/MWh remain null because detailed site OPZ documents require
an NDA. No NDA request, contact, registration or access-control bypass was attempted.

All thirteen tender tasks were reviewed. Nine existing Energa records gain their
task mapping, required 60-month battery service scope and the later procurement
result. The 9 July 2026 notice **annuls the procurement because all submitted bids
are subject to rejection**. It is not a project cancellation or an award; existing
dated project status is preserved. Service requirements are not warranties or
awarded service contracts. The Płońsk 1+2 task remains held: one funding title and
two plant/phase labels do not resolve physical battery allocation. Existing
Dźwierzuty, Kwidzyn and Nowe Skalmierzyce scope is retained with the exact 1+2 task
label; no additional phases or aggregate records are fabricated.

**Equipment: 16 candidates → 16 new exact BYD configurations**, zero existing
model changes. Six LVS towers, LVL15.4 (2021), and nine HVB towers have distinct
manufacturer model labels and individually reviewed technical columns. Adds usable
DC energy and its 100% DoD / 0.2C / +25°C test conditions, module quantities, voltage
ranges, output/peak current and duration, dimensions, mass, temperature/derating,
IP, communications, mounting and qualified scalability/compliance observations.
HVB 26.7 and 29.6 use the explicitly printed 26.72 and 29.69 kWh; values are not
extrapolated from the module's designed capacity. No power is calculated from
voltage/current and no AC-to-AC efficiency is inferred from the ≥95% RTE claim.
Ten- and fifteen-year warranty statements stay qualified datasheet claims pending
applicable contract review; the previously reviewed HVS/HVM contract is not applied
to these different models. No project-equipment assignments are invented.

The indexed BYD HVB V1.4 URL returned 404. The manufacturer-named EU service partner
EFT supplied the public manufacturer-authored V1.7 English PDF, dated 17 September
2026. Its public document-list API and listed file URL were used; translations were
not counted as more models. All three PDF technical pages were rendered and visually
checked, including footnotes and merged-row scope. Raw PDFs, ZIPs, HTML and typed
Parquet snapshots remain outside Git. Six new source registrations retain original
byte checksums, exact URLs, timestamps and locators; ZIP members have their own
checksums/name mapping. Existing source metadata is preserved for unchanged bytes.

The established upsert API exposed twenty populated-field collisions for explicit
review. Creation timestamps and all prior verified facts are preserved. New funding
facts retain NFOŚiGW CC BY-SA 4.0 attribution and modification notes. Owner/OEM
material is bounded, manually reviewed factual extraction; public access is not
represented as an open bulk-reuse licence.

## Coverage, limits and continuation

Current proposed totals: **1,886 projects / 39 countries / 287 sources**, and
**695 equipment records / 44 suppliers / 346 sources** (682 exact configurations,
13 families). No new country or OEM this pass; all six regions remain represented.
The cumulative open PR adds 97 projects and 83 equipment records versus main;
existing-main enrichments remain 5 projects and 12 equipment records. This pass's
20 project enrichments affect records introduced earlier in this same PR.

One project candidate remains held and one project rating observation is quarantined;
zero permanent whole-record rejections and zero new equipment quarantines. Historical
holds/conflicts remain intact. The three newly resolved Energa candidates are tracked
in the review ledger without rewriting historical launch reports or decisions.

The same-day [IEA market comparison](2026-11-03_poland_containers_markets.json)
uses 2025 annual stationary battery **GW additions**, among quantified countries:
China, United States, Australia, Chile. It is not a worldwide operational GWh ranking.
Comparable operational GWh and missing national ranks remain unavailable; no
MW/MWh conversion or region-to-country rank substitution is made.

The selected register matches, complete owner energy paragraph, thirteen tender
tasks and sixteen model columns are exhausted for defensible acceptance. The
project yield is below the planning range because the remaining national applicants
need independent battery/identity evidence and detailed Energa specifications are
gated. The equipment objective is met with sixteen substantive exact configurations.
Next: publicly available replacement Energa procurement and site ratings, Płońsk
allocation, TAURON commissioning/rating reconciliation, and model-specific BYD
warranty terms. The ranked [backlog](2026-11-03_energa_byd_backlog.json) records
versions, terms, partitions, retry conditions and next actions. Six bibliography
entries are queued (96 cumulatively) while Wind overlaps the shared registry.

## Completed validation

1,860 Python tests passed without skips; 28 final catalogue tests passed after the
last funding enrichment. Catalogue validators, preservation/natural-identity audits,
two identical typed Zstandard Parquet builds per catalogue, Ruff, formatting, ty,
repository hygiene, existing citation consistency and whitespace checks passed.
All 13 viewer tests and both offline usage examples passed. Strict Sphinx and the
449-page link/asset audit passed. Package builds were not repeated because package
code and dependencies are unchanged; starting-head remote CI passed.

Validated at 16:11:38 Atlantic/Canary: 17.3 minutes actual elapsed effort
through local validation, followed by leased publication and remote-state checks.
The selected defensible source batches are exhausted; no idle time was added.
