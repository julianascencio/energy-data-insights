# New Zealand project reconciliation and Sinexcel exact PCS models

Research started 3 November 2026 at 08:51:55 Atlantic/Canary (UTC+00:00).
Validation completed at 09:16:56 Atlantic/Canary: **25.02 minutes** of elapsed research, implementation and checks. Publication follows this checkpoint; no idle time was added.
This pass continues from main `47cf12e8d95e4da29a52a54e3235db41ecce0d08`:
PR #94 was already merged at 08:22:07 UTC. The old PR #44 launch counts are
historical. A new isolated `research/bess-database-20261103T0855Z` branch is
therefore appropriate; no closed PR is reused and no PR is merged by this run.

## Accepted changes

| Entity | New | Substantively enriched | New field quarantines | Whole-record rejections |
|---|---:|---:|---:|---:|
| Projects | 4 | 4 | 0 | 0 |
| Exact equipment | 11 | 0 | 5 records | 0 |

The project catalogue now has **1,789 records, 37 countries and 253 sources**.
Equipment has **612 records, 43 suppliers and 284 sources**: 599 exact
configurations and 13 explicitly configurable families. Sinexcel is the new
OEM; no new country is claimed. Existing coverage in Africa, Asia, Europe,
Latin America/Caribbean, North America and Oceania is retained. Suppliers are
represented through the existing equipment schema, not a competing entity table.

New projects are NZCE Masterton, Darfield and Dannevirke optional batteries,
and Contact's Glenbrook Ohurua Battery 2. The three optional batteries retain
up-to power and 200–400 MWh option ranges in extensions; fixed nameplates remain
null. Consent and early solar works do not establish battery construction.
Solar ratings, grid infrastructure, site area, PPA counterparties and finance/
construction forecasts retain their hybrid-site scope.

Glenbrook Battery 2 is a separate 200 MW / 400 MWh phase, explicitly under
construction with expected 2028 operation. Its 112 Tesla Megapack 2 XL units
are sourced rather than inferred. Battery 1 is enriched with its 56 units,
Tesla role, first trading and opening dates, reported investment and reciprocal
phase link. Opening is not labelled exact COD. The source's dollar symbol is
retained with currency and price-base-year null because an ISO currency was
not explicitly printed in the examined announcement. Annual output GWh is not
storage energy. No aggregate 300 MW facility row is added.

Existing Ruakākā, Rotohiko and Huntly Stage 1 receive dated dispatch/planning
evidence. Three records' EA-backed status dates are corrected from an access
date to the article's printed **19 May 2026** publication date. Historical 2024
planning observations cannot overwrite later operating status. Prior identities,
creation timestamps, ratings and nested facts remain intact.

Eight individually reviewed Chinese Sinexcel datasheets yield 11 exact models:
PWS1-1250KTL-H, 1375KTL-H, 1500KTL-H, 1575KTL-H, 1725KTL-H, 100M, 125M,
500KTL, 630KTL, 215M-H-O, and PWS2-30P-CN. Added fields include maximum DC power,
AC apparent power, voltage/current limits, DC connection options, ordered
mechanical dimensions, mass, IP, cooling, ambient limits and derating,
interfaces/protocols and explicit black-start claims. AC kVA is never treated
as active kW. The 3000 m derating threshold is not an altitude ceiling.
Conversion efficiency is not round-trip efficiency. Five models retain the
conflicting page-1 `>99%` claim and page-2 `99%` table in field quarantine.
No chemistry, energy, warranty, certification or project assignment is inferred.

## Source batches and exclusions

The machine-readable review contains URLs, hashes, retrieval times, row/page
locators, all nine EA identity decisions and the accepted-record list.
Source counts below describe overlapping observations, not additive unique projects.

- **EA September 2024 pipeline:** all 164 rows inspected; nine explicitly
  classified chemical batteries, 155 non-battery rows excluded. Three exact
  existing identities enriched; six proposals held for scope/identity work.
  WEL Huntly is not automatically equated to Rotohiko; Huntly Stage 2+ is not
  split arithmetically; NZCE Glenbrook is not merged with Contact's site.
  CC BY 4.0 terms and attribution are recorded in `../licenses/NZ-EA-NOTICE.md`.
- **EA performance article:** three existing records enriched from its dated
  observations through 28 April 2026; it does not prove a fresh November status.
- **NZCE:** the complete three named-project portfolio processed, three accepted
  optional BESS proposals. **Contact:** two explicit phases reviewed, one new
  and one enriched. Copyright retained; bounded factual observations only,
  no open bulk licence asserted and no full source content redistributed.
- **Transpower October 2026 workbook:** 41 forward BESS rows staged outside Git
  (seven named, 34 unnamed) and four completed observations reviewed. All held
  from canonical ingestion because compatible bulk reuse was not established.
  Main-site intellectual-property terms were checked, not a different service's
  terms. Connection-stage percentages are not physical construction status;
  Max MW is not automatically battery nameplate. A tested offline adapter is
  delivered, separately from accepted data.
- **Sinexcel:** eight selected exact tables exhausted, 11 models accepted. No
  fabricated configurations for optional DC branch arrangements. Copyright
  retained; factual model observations only; PDFs remain outside Git.
- **Africa/Asia alternatives:** AMEA, EBRD, IFC and CEEC terms were examined;
  restrictions triggered alternative-source research rather than bypasses.
  MIGA's 23-project AMEA portfolio contained nine battery candidates; all held
  pending reuse and phase/rating reconciliation. The web reader returned 403
  while normal public download worked; this is not misreported as inaccessible.
  A suspicious EBRD cross-link to a non-battery Kazakhstan project was not
  imported. No existing historical records were deleted because of this pass.
  Hubble's 18 existing configurations were checked for catalogue overlap;
  this does not claim 18 fresh datasheet reviews.

## Reproducibility and continuation

Two offline source-specific staging CLIs and 15 synthetic parser tests cover
exact model columns, units, missing values, duplicate identities, historical
planning scope and anonymous connection rows. Original source bytes are hashed
and kept outside Git; the fixtures do not reproduce copyrighted documents.
Existing upsert APIs accept the new rows and null-field fills. Reviewed additive
nested evidence and the three explicit date corrections preserve prior facts.
Both canonical and incoming identities were checked without fuzzy merging.

Typed Zstandard Parquet and coverage manifests were rebuilt twice through the
existing packages and compared byte-for-byte. Binary outputs remain outside
Git; the existing catalogue artifact workflow can regenerate them. The dated
manifest captures final record/source/schema/output hashes and completeness.
See the validation JSON for commands actually executed and the optional skip.

The equipment working objective was met. Project yield is below 50–200 because
the reusable EA file has only nine batteries, six require identity work, the
three-project NZCE and two-phase Contact batches are exhausted, and the larger
current operator/AMEA batches have concrete reuse or scope blockers. No sparse
rows were added to satisfy a quota. Finishing follows exhaustion of these
selected defensible batches, not the passage of a fixed duration.

Next: corroborate Transpower's seven named proposals through permissible owner
or permit records, retaining all 34 anonymous rows as unresolved. Then inspect
Sinexcel PWS1-160M regional variants and PDS1 DC/DC tables, preserving conversion
boundaries. The ranked backlog records versions, partitions, fields, expected
yield, reuse assessment and retry conditions. Earlier Australia/Chile holds,
including Atacama and Solar Ray, remain untouched.

The market file records IEA's comparable 2025 annual stationary-storage **GW
additions** among quantified country examples, with regional comparisons kept
separate. A comparable worldwide operational-energy GWh table was not obtained;
no GW-to-GWh conversion or exhaustive global ranking is claimed.

Concurrency checks found Wind #97 and PV #98 with no changed-path overlap
with this BESS change, including its bibliography exports. Both merged during
validation; this branch was rebased onto main `a7ae7d6524f0244a2ec5a20ab5c67594ac4b7484`
and the full suite was rerun. Their branches are not modified. Dependabot changes
are limited to workflows. The publication checkpoint rechecks main and relevant
heads; this research PR remains open.
