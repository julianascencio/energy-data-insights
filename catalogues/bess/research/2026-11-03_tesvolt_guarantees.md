# Maldives ASSURE and TESVOLT guarantee enrichment — 3 November 2026

Started at 18:46 Atlantic/Canary (UTC), from open PR #102 head
`ab30c8ce84e104e5971eafbd1e6c074198e3ce41`; main remained
`5063c41694b17b1a3fc856ea9527a32211278203`. Reused the instructions, dictionaries,
schemas, source registers, upsert API, previous coverage/reconciliation logs and
same-day market assessment. The previous commit's Python 3.12/3.13 and documentation
CI passed. PR #44 is historical. No subagents or shared-schema changes.

## Accepted facts and boundaries

**18 new projects, zero existing project edits; 12 equipment enrichments, zero new
models.** No canonical field quarantines or permanent record rejections. Maldives
is new; no new OEM. Proposed totals: **1,926 projects / 40 countries / 295 sources**;
**707 equipment records / 45 suppliers / 354 sources** (694 configurations,
13 families). All six regions remain represented. Cumulative versus main:
137 new projects, five existing-main project enrichments, 95 new equipment records,
12 existing-main equipment enrichments. The 12 TESVOLT records were introduced
in this PR, so this pass does not increase the existing-main enrichment count.

The official URA Energy Supply and Demand Study 2018–2022 was downloaded first.
Section 4.1.3/Table 4-3 reports STELCO, FENAKA and national battery totals, not named
sites: three aggregate rows excluded from project ingestion. No country aggregate
record was created. A ministry ARISE screening PDF returned 503, and an independent
reader timed out. The Gazette procurement alternative also timed out. These are
access limitations, not evidence that the projects were cancelled or absent.

A separate **ASSURE** programme offered a defensible alternative: SINOSOAR's
10 April 2025 first HTML table enumerates 18 named island battery capacities; the
President's Office reproduces the ministry's 7 April 2025 agreement for 38 MWh across
18 islands. All 18 named cells were reconciled; their original kWh sum is 38,000,
matching the independently reported 38 MWh. Each conversion is explicitly kWh/1000.
Later unrelated global-case tables on the supplier page were excluded. The database
had no Maldives records, and the incoming names are unique. Original spellings
are preserved, including Dharaavndhoo, Rainmandhoo, Faresmaadhodaa and Gahdhoo;
no fuzzy geographic correction or coordinates were invented.

Each project records the island/atoll, battery energy, agreement date, ADB-supported
programme and renewable-integration application. Procurement evidence maps to
announced status; signing does not establish physical construction or operation.
No site power, chemistry, battery manufacturer/model, ownership or contractor
assignment is inferred. SINOSOAR's programme implementation statement is kept
separate from unverified per-site contract allocation. No aggregate 38 MWh project
is added, and ASSURE is not conflated with the distinct ARISE programme.

The two project pages are copyrighted public disclosures, not open bulk datasets.
The review is a bounded extraction of factual island names/ratings, not wholesale
article or image redistribution; no explicit open bulk licence is claimed. Exact
URLs, retrieval times, original HTML checksums and table locators are registered.

## Equipment enrichment

Read two original TESVOLT guarantee letters: E-series **v3.0**, applicable to
qualifying products distributed since 1 July 2024, and A-series **v1.0**, applicable
since 1 December 2023. These applicability dates are not publication dates. The
printed page 4 cycle tables were visually checked as well as extracted text.
The current legal-notice page was retrieved; bounded individual-use factual
extraction continues, without redistributing the letters or claiming open licensing.

All seven existing E-series cabinets and five A-series configurations gain:

- Business-customer scope, authorized installation and 31-day commissioning notice.
- Worldwide scope with country-dependent remedies; external inverter/EMS exclusions.
- Separate system and module-performance periods and their different start events.
- Conditional 70% module nominal-capacity retention, limited by time AND guaranteed cycles.
- Temperature/C-rate cycle tables, pro-rata partial cycles, and weighted-temperature rules.
- Exact module capacity-test conditions, kept distinct from cabinet voltage limits.

E-series system cover is 10 years; A-series is 5 years. Module-performance cover is
10 years in both letters. The performance clock begins at the earliest of initial
commissioning, eight weeks after delivery, and six months after module DOLC.
The system clock begins at commissioning or eight weeks after delivery, whichever
comes first. Replacement does not extend the original term. Eligibility of any
particular installed unit is unknown.

E-series uses external **ambient** temperature with at least three-minute logging
and one-year retention; A-series uses average **module** temperature from the
internal log. E-series daily high-temperature cycle deductions and temperature
exclusions remain separate from A-series hour-weighted bands. The v3.0 capacity
test uses 23°C, 0.2C, module test voltages and the second DC discharge; A-series uses
18–28°C and C/3 with its own rest/CV-termination sequence. Warranty cycle limits
are not substituted for datasheet expected life. Previous datasheet guarantee
claims are retained in extensions; original creation times and other facts remain.
These are selected structured conditions, not a replacement for the full contract.

## Coverage, continuation and limitations

Retained the same-day IEA market assessment in
`2026-11-03_poland_containers_markets.json`: 2025 stationary battery power additions
in GW, ranked only among quantified country examples. Comparable worldwide
operational stationary energy GWh is unavailable. The historical URA utility totals
are not mixed into that ranking. The regional rotation deepens South Asian islands
rather than repeating a US bulk import.

All 18 accepted island rows and 12 warranty configurations in the selected batches
are exhausted. Project yield below 50 reflects the bounded 18-island table,
aggregate-only URA inventory and failed ARISE/Gazette access. Equipment yield is
12 substantive enrichments rather than new variants. No records were inflated
from optional configurations, portfolio totals or anonymous global-case tiles.

Next: obtain a current public ARISE site schedule with clear reuse terms and
reconcile its identities against ASSURE before adding any overlapping island.
Then seek named commissioning evidence for the 18 ASSURE sites, retaining planned
ratings separately. A newer official inventory or original island/site appendix
has higher value than another undated supplier portfolio. The ranked backlog
records assessed and unprocessed partitions and retry conditions.

## Validation and publication

Both catalogues validate; two final independent Zstandard Parquet builds match.
Snapshots and raw sources stay outside Git, with reviewable JSONL and completeness
manifests committed. Existing importer/upsert collisions for the 12 known equipment
identities were reviewed explicitly; no automatic fuzzy merge.18 incoming project
identities are unique and do not collide with the canonical dataset.

Validation passed:1,869 Python tests without skips;28 final catalogue tests; Ruff lint/format, ty, hygiene, citations,13 viewer tests and both offline examples. Strict Sphinx reran examples against the final data and the451-page link/asset audit passed. Local validation completed at 18:58:01 UTC, approximately 11.4 minutes after starting; publication follows the final head check. The selected source batches were exhausted, so the pass ends without waiting to fill45minutes. Detailed outcomes are in the validation ledger.
No code/schema changes were made, so no implementation-mirroring tests or package
rebuild were added. Final catalogue tests and examples cover the accepted data.

Open PRs were inspected by title and paths. Wind #101 and Data Center #100 advanced;
their changed paths are outside this increment. PV #103 and Timestral #104 remain
separate. Wind/Timestral still overlap the shared reference registry, so four new
bibliography entries are queued (112 cumulative) while complete field evidence
is committed. The final branch update uses a non-forced expected-head lease.
The recurring PR remains OPEN and unmerged.
