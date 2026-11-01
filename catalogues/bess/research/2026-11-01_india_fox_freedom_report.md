# India inventory, Fox ESS models and Freedom Won technical/warranty depth

Research date: 1 November 2026. Started 21:12:52 Atlantic/Canary (UTC+00:00).
The final validation checkpoint below records elapsed effort. Database timestamps are UTC.

## Accepted changes and reviewed candidates

| Entity | Candidates reviewed | New | Existing enriched | Held | Rejected |
| --- | ---: | ---: | ---: | ---: | ---: |
| Projects | 21 | 9 | 1 | 11 | 0 |
| Exact equipment / existing warranty candidates | 23 | 17 | 4 | 2 | 0 |

One accepted project (Modhera) has conflicting energy observations quarantined and
its scalar energy remains null. One accepted equipment configuration (ENVA 60HV)
has incompatible warranty-cycle DOD definitions retained as `needs_review`.
These flags are subsets of accepted records, not additional records or rejections.
No OEM entity table was invented. Fox ESS is one new product supplier; Freedom Won
already existed. No new project country. Project coverage remains all six regions.

Final snapshot: **1,275 project/plant records, 30 countries, 91 sources**;
**138 equipment records, 31 suppliers, 71 sources**, comprising 125 exact
configurations and 13 explicitly configurable families. Counts come from canonical
JSONL, not launch reports. This iteration adds 14 primary-source registry entries.

## Scalable projects and enrichment

The first attempted batch was CEA's September 2026 status inventory. It is a
2-page aggregate, attributes IESA, and has a prior-permission reuse policy. Its
project counts do not identify importable sites. SECI's owner portfolio then
identified four BESS candidates but its website policy also restricted reuse.
Neither batch supplied canonical facts. Independent Ministry of Power/MNRE
releases through PIB provided a reusable alternative under PIB's attributed-reuse
policy, excluding third-party material.

PIB release 2291650, published 30 July 2026, has 18 numbered installed-BESS rows
reported at 30 June. The operational label normalizes that installed-capacity
inventory; it does not assert dispatch availability or exact COD. The new offline adapter stages all rows, distinguishes the
MW and MWh columns from numbers in hybrid descriptions, checks the published
totals and sequential row numbers, deduplicates identical desktop/mobile tables,
and rejects conflicting copies or structural drift. It does not infer identities
or import automatically. All 18 rows have explicit dispositions in
[the review ledger](2026-11-01_india_review.json).

Eight rows become reviewed site records: Rohini, Dollygunj/Attam Pahad,
Modhera/Sujanpura, Kavaratti, KLTPS, NTPC NETRA flow battery, Khavda's named
250 kW pilot and Charal/Sanand. Dollygunj/Attam Pahad stays one explicitly
combined registry asset, not two overlapping phase records. Solar, lignite and
separate microgrid capacities are excluded from battery ratings. The Modhera
19.2 MWh / 15 MWh conflict remains unresolved; the separate temple battery is
excluded. Nandyal is the ninth new project, from an independent November 2025
PIB approval release: 1,200 MWh, power unknown, historical announced status.
Later restricted owner-page claims do not promote it to construction.

The existing Rajnandgaon record gains 132 kV connection and Thelkadih substation,
100 MW AC solar association (155.02 MWp DC separately scoped), land metadata,
evening peak shifting, CSPDCL offtaker/long-term PPA and World Bank/Clean Technology
Fund financing context. Its stable ID, created timestamp and existing ratings
are preserved. A malformed solar-capacity unit in the release is excluded.
Inaugurations are stored as inaugurations, not exact COD. WRPC's possible COD
is a next-step candidate pending source terms and meeting-document review.

Nine inventory rows stay held: unresolved tender/site identities, conflicting
Kajra and RTC ratings, Kolkata rail-system scope, and merchant or multi-site
portfolios. Taru/Phyang and a distinct NETRA NMC microgrid battery are the two
additional holds. These are not silently fuzzy-merged or represented as thin rows.

## Exact equipment and quality

Two Fox ESS tables provide five EQ3300 L2–L6 and eight EQ4800 L2–L9 configurations.
Every configuration keeps its own printed model column, revision, nominal
energy, DC voltage range, module counts, current/peak-duration limits, dimensions,
weight, thermal/environmental constraints and manufacturer standards claims.
Battery-pack RTE is strictly greater than 95%, with its DC boundary, comparator
and unknown test conditions retained. No AC system efficiency, active power,
cell supplier, warranty or project assignment is inferred.

Four previously deferred Freedom Won configurations are now accepted: ENVA 5,
ENVA 16, the 12-module ENVA 60HV, and COREVA exact model
COR-5000-HVXA-14971164. Their tables preserve nominal versus DOD-qualified energy,
maximum versus continuous current/power, charging versus discharging,
module versus bank limits, temperature derating, dimensions, safety status,
communications, thermal management and fire provisions. Printed dates take
precedence over inconsistent filenames. IEC62619 marked in progress stays in
progress; a manufacturer standards list is not independent certification.

Two guarantee documents add model-specific five-year terms, cycle limits,
70% retention, test rate/temperature, cycle definitions, commencement dates,
storage and operating restrictions, non-cell coverage and remedy exclusions.
Four existing SOLVA AC261/DC261/AC418/DC418 records are substantively enriched.
DC208 and RT261 are held because the guarantee does not explicitly name them.
ENVA 60HV's datasheet 90% DOD and guarantee 100% DOD cycle definitions remain a
visible conflict. A paid ten-year extension is not represented as the standard
warranty. Design life is not a warranty.

## Evidence, priorities and reproducibility

All 14 new registered sources retain exact URLs, publisher/title, printed revision
or date, retrieval time, SHA-256 of downloaded bytes, page/table/row locators and
source-specific rights assessments. Every populated field maps to source IDs;
model columns and inventory rows have additional locators. Original HTML/PDFs and
rendered review images remain outside Git; only factual records and evidence
metadata are committed. Existing importer/upsert APIs were used. Incoming and
canonical identities were reconciled manually, no automatic fuzzy merge.
Existing created timestamps and unrelated records are unchanged; verification
and substantive update dates remain separate.

[Market priorities](2026-11-01_india_fox_freedom_markets.json) use the IEA's dated
2025 annual stationary battery **power additions in GW**, covering utility and
behind-the-meter storage. China, US, Australia and Chile are ordered only among
quantified country examples. Europe/Middle East remain separate regional figures.
A comparable worldwide operational stationary **GWh** ranking was unavailable;
GW is not converted into GWh and unquantified countries remain unranked.

The [ranked backlog](2026-11-01_india_fox_freedom_backlog.json) retains URLs,
versions, access/rights findings, byte hashes, fields, yields, processed cursors,
retry conditions and next actions. Highest-value next project work is the held
PIB site/phase partition and Kajra rating reconciliation using independent
primary evidence, followed by WRPC Rajnandgaon COD verification. Current Fox and
Freedom Won selected tables are exhausted; obtain model-specific warranties
before further SOLVA enrichment. The earlier Australia/Chile mapping and held
Atacama/Solar Ray candidates are unchanged.

Project yield is below the 50–200 planning objective because the reusable table
contains only 18 rows and nine require unresolved identity/rating review; the
larger CEA and owner alternatives could not be ingested. Equipment yield meets
the 10–30 model objective with substantive specifications. No sparse records,
cosmetic variants, duplicate phases or timestamp-only edits were added.

## Concurrency and publication

Discovery began on open PR #44, then head aa6c411. The OEM foundation PR #45 was
already merged. PR #44 was subsequently repaired and merged by another session
at 21:26:04 UTC, producing main 19831ad. This batch moved to a fresh isolated
branch `research/bess-database-20261101T213000Z` based on that main commit. All
270 existing citation entries and their main-branch order are preserved; 15
new references are appended. Closed PR #44 is not reused. No PR was merged by
this research run. Other open PRs #47–49 only change workflow action versions.

## Validation checkpoint

Validated at 21:36:34 Atlantic/Canary / UTC; 23.7 minutes elapsed from
21:12:52 start (research/extraction/reconciliation approximately 15 minutes,
validation/integration/publication preparation approximately 8.7 minutes).
Selected defensible batches were exhausted; no waiting to meet a duration.

- Full Python suite: **1,518 passed, one optional CDS dependency skip**. The 12
  new parser cases cover mixed hybrid numbers, duplicate/conflicting tables,
  units/totals/row drift, malformed numeric grouping, invalid values and zero.
- Ruff format/lint and ty: passed. Repository hygiene, citation regeneration and
  consistency, whitespace checks: passed. Original citation ordering was restored
  after an initial integration failure; the final suite passes without test weakening.
- Both catalogue validators and typed Zstandard Parquet builds passed. Rebuilding
  the final snapshots exactly reproduced the committed input/output hashes and
  completeness manifests. Fourteen downloaded-source hashes verified.
- Preservation audit: all existing IDs/created timestamps retained, 1,265 projects
  and 117 equipment records byte-equivalent to the baseline; only one existing
  project and four existing model records changed substantively.
- Both offline database examples passed. Strict Sphinx/gallery build passed after
  installing the repository-pinned optional imagery dependency; all **385 HTML
  pages** passed the local-link/asset check. Four Node viewer tests passed.
- All three packages built as wheels and source distributions; fresh installed-wheel
  entry-point checks passed. No binary snapshots or source PDFs/HTML committed.

No publication blocker remains. Held project identities, rating conflicts, warranty
scope and CEA/SECI rights limits remain concrete research blockers, documented in
this report and the backlog. This batch is for a new open PR, not merged content.
