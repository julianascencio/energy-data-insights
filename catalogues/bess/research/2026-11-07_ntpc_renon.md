# 7 November 2026 — Indian procurement packages and Renon residential specifications

Started approximately 08:00 Atlantic/Canary (UTC). The isolated checkout starts
from main `dbd83f047b8d86f7940446c39b9ffe7fd78e7723`. PR #44 and the subsequent
BESS PR #193 are merged; no compatible BESS PR was open. Current main, repository
instructions, both catalogue schemas/dictionaries/source registers/manifests,
PV conventions and recent BESS logs/holds were reviewed. Historical launch totals
were not used as current counts. The branch is `research/bess-database-20261107T0800`.
No agents were spawned and no prior holds or accepted records were deleted.

## Project batch and reconciliation

Two official NTPC invitation-for-bids tables were reviewed before extraction:
[Lot 1](https://ntpctender.ntpc.co.in/Uploads/job_44700.pdf), dated 30 September 2025,
and [Lot 2](https://ntpctender.ntpc.co.in/Uploads/job_44817.pdf), dated 6 November 2025.
All seven and nine battery-specific rows were visually checked. The source-specific
offline parser checks exact notice/date, MWh units, complete row numbering,
within-table unique names and the separate 2,334/2,670 MWh control totals. It stages
facts without importing or merging identities. These totals are procurement
requirements, not installed-capacity statistics.

**16 candidates → 16 new project/package records; zero existing-project updates,
zero project holds or rejections.** Exact site/lot identities were compared with
all canonical Indian records and with the incoming batch. Both Solapur packages
are separately identified in Solarworld's FY2025–26 annual report, PDF page 7,
printed 10–11: Lot 1 132 MW/264 MWh and Lot 2 75 MW/150 MWh. The same report supplies
Unchahar's 50 MW/100 MWh and Solarworld's EPC award role for all three. No aggregate
257 MW/514 MWh project is added. An anonymous earlier 125 MW/250 MWh award is not an
identified site candidate and is not imported.

Mouda's 26 September 2026 retender remains one 400 MWh site, not a second project.
Its one-page brief scope adds 12-year designed service life, two required cycles
per day and 11-year CAMC after the performance-guarantee test. These are procurement
requirements, not warranty or tested operation. The three Solarworld awards use
`announced` with an explicit awarded-stage extension because the current schema
has no awarded enum. Every status retains its supporting publication date; none
is promoted to construction/operation by elapsed time or a supply agreement.

All 16 rows retain MWh, exact package IDs, tender locators, procurer, required
systems, CAMC scope and financing intention. NTPC's current host-station table
supplies nine states: Andhra Pradesh, Assam, Bihar, Karnataka, Madhya Pradesh,
Maharashtra, Tamil Nadu, Telangana and Uttar Pradesh. Thermal MW and thermal
ownership do not transfer to battery records. Corporate Noida/Delhi addresses
are excluded. Internal 33 kV pooling switchgear is not a grid-connection voltage.
Power remains unknown for 13 packages; chemistry, COD, coordinates and battery
OEM assignments remain unknown throughout.

## Equipment batch and conflicts

Three original Renon documents were acquired with SHA256 hashes and inspected
as rendered tables: XPro sheet page 2; residential brochure pages 7/15/17
(printed 4/12/14); Xtreme HV A04 manual page 45. Brochure V4.9 is an index/filename
label, not an asserted printed revision/date. Source URL dates are not publication dates.

**17 reviewed configuration candidates → 9 new, 7 existing substantively enriched,
1 held identity; zero rejected.** New configurations are five explicit XPro
module-count columns, two EBrick OUT exact codes and two Xtreme HV exact codes.
The seven existing 16-series-cell Xtreme LV configurations gain explicitly reported
output kW, timed peak currents, natural cooling and storage conditions. Existing
15-series-cell rows are unchanged. No region/heating/V2G cross-product variants
or family-wide extrapolations are created.

Fields include nominal/usable energy boundaries, module quantity, exact
module/controller relationships, battery versus inverter power, voltage/current
limits, timed peaks, separate charge/discharge temperature ranges, dimensions,
mass, enclosure, altitude, interfaces, design life and qualified cycle claims.
EBrick OUT's 8000-cycle claim preserves 25°C, 0.5C, 80% DoD and 80% EOL. Two exact module
references link to the existing R-EB005161 record; no other component or project
assignment is invented. Renon remains the system brand/manufacturer; cell OEM
is not inferred. No new supplier or country is introduced.

Seven accepted equipment rows retain field conflicts:

- Two HV models: A04 versus brochure charge-current, enclosure and mechanical
  differences. Conflicting scalar fields stay unset; both observations remain.
- Two OUT cabinets: published Ah versus nominal-energy/module/voltage boundary
  inconsistency. No arithmetic repair or active-power inference.
- Three existing LV models: brochure/manual height differences; R-XL035071 also
  retains its prior 35.85 kWh scalar and the brochure 35.84 kWh discrepancy.

The 9.6 kWh HV configuration is held because the manual says R-XH096021 and the
brochure R-XH009021. Neither automatic typo correction nor two separate models
is justified. Unconditioned 8000-cycle claims, 10-year warranty-letter pointers and
“coming soon” UL statements do not become tested life, applicable warranty or
certification. Optional V2G ratings do not describe installed XPro equipment.

The existing upsert API accepts the new rows and quarantines seven expected
nested-object enrichment collisions. Each is explicitly reviewed as an additive
namespace/provenance merge. Every previous fact, `created_at`, prior conflict and
unrelated record is preserved. Only the seven substantive OEM enrichments change
update/verification timestamps. The review ledger identifies every candidate.

## Access, rights and alternatives

NTPC's tender copyright policy and corporate disclaimer were inspected. No open
bulk-reuse licence is asserted. This is bounded factual transcription of two
public IFB tables and specific technical/award observations; no copyrighted PDF,
prose, images, logo or tender contact information is committed. The corporate
disclaimer's images and Contracts Concluded materials are not used. Solarworld
and Renon publications likewise retain their copyrights; only facts/evidence
metadata enter the catalogue. Original downloads and rendered pages stay outside Git.

CEA's legacy route returned 404; the new division/API returned 503 and the web
report dashboard 502. The indexed 30 September report's aggregates are not named
project rows, and its construction category includes contractual stages. No CEA
aggregate becomes a project or comparable operating-GWh market rank. Eskom's
portfolio was sampled before its saved reuse hold was recognized; collection and
ingestion stopped, with zero accepted facts from it. The four saved phase 2 holds
remain. MaStR partition 9 and Philippine DOE/IEMOP items are carried forward,
explicitly not claimed as freshly retried in this pass.

The dated backlog ranks CEA recovery, refreshed MaStR partition 9, later NTPC
awards, HV corrections and independent African evidence. It records URLs,
versions, rights/access assessment, expected yield, fields, completed partitions,
retry conditions and next action. The selected 16-site NTPC tables and OEM columns
are exhausted. Project yield is below 50 because the next national inventory
could not be acquired and no aggregate, anonymous award or restricted source was
substituted. Equipment depth reaches 16 accepted new/enriched configurations.

## Market comparison and coverage

The IEA 29 May 2026 commentary was freshly checked. Comparable selected-country
**2025 utility-scale battery power additions (GW)** rank China about 55, US over 16,
Australia about 4.2. Europe 4.6 is a region and excluded from the country ranking.
This is not an exhaustive world ranking or operational stationary energy stock.
Comparable GWh stock was unavailable in the examined source and is not inferred.
India is prioritized for underrepresented coverage; no US bulk import was used.

New branch totals: **2,409 projects / 51 countries / 474 sources**; **1,388 equipment
records / 60 supplier labels / 599 sources** (1,375 configurations, 13 families).
India has 35 project records; Renon has 41 equipment configurations. All six world
regions remain represented. Current completeness and reproducible snapshot hashes
are in the dated manifests; record counts are not market capacity.

## Concurrency and validation

Open PR #205 (forecast),206 (hydro),207 (wind) and208 (data centres) were inspected by
title and changed paths. No BESS data/parser overlap was present. PRs #205/#207 modify
shared scientific-reference exports, and #207 modifies the shared viewer; those
writes are skipped under the requested concurrency safeguard. All nine accepted
primary sources are fully registered in the established BESS source registries;
shared citation consolidation is deferred. Existing citation exports still pass
consistency validation. No shared schema, viewer or package dependency is changed.

Validation and actual elapsed effort are recorded in the accompanying validation
ledger after checks finish. Both typed Zstandard snapshots were independently
rebuilt twice with identical manifests; every prior project and all but seven
reviewed OEM rows are semantically identical. Binary snapshots remain outside Git.
The PR is for review, not merged content, and must remain open.

Local validation completed at 08:27 Atlantic/Canary on 7 November: approximately
27.7 minutes elapsed (about 17 research/reconciliation and 10 validation/preparation).
The selected defensible source batches are exhausted; the remaining national
export/rights and OEM identity blocks explain the lower project yield. Publication
and hosted CI follow this checkpoint; their final state is recorded in the PR.

Full Python 3.13 suite: **3,499 passed**; BESS-focused suite: **664 passed**, including
12 new parser cases; Node viewer: **40 passed**. Both offline BESS examples, repository
Ruff formatting/lint, ty, hygiene, citation consistency, validators and diff checks
passed. Three wheels/three sdists built and strict metadata checks passed. Full
Sphinx documentation/gallery passed on sequential retry; **776 HTML pages** passed
link/asset checks. Published docs Parquet matches the independent snapshots.
Initial attempts exposed a physical-core warning, missing optional Python 3.13
dependency, and a concurrent docs process killed with exit 137; the corrected full
runs passed. Installed-wheel smoke checks were not run locally. No pending remote
check is represented as passed.
