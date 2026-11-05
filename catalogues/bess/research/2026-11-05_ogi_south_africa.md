# TAB OGi and South African lender evidence — 5 November 2026

Started **15:01:50 Atlantic/Canary (UTC)** on open PR #172 at
`267e53b1d944fa1ea059b6a8ea4d9ab090d2e12c`; main remained
`76179409be2ce1166d60714145f1711776182b16`. Used an isolated checkout, read the
current catalogue instructions, schemas/dictionaries, sources, coverage and recent
research ledgers, and inspected all open PR titles and changed paths. No parallel
agents, merge, force-push, shared-schema changes or PV edits. PR #44 is historical.

## Accepted changes and current coverage

| Entity | Reviewed accepted-batch candidates | New | Substantively enriched | Rejected rows |
| --- | ---: | ---: | ---: | ---: |
| South African projects | 8 | 1 | 7 | 0 |
| Exact TAB OGi models | 25 | 25 | 0 | 0 |

Totals are **2,147 projects / 48 countries / 404 project sources** and
**1,131 equipment records / 55 supplier labels / 480 equipment sources**.
Equipment comprises 1,118 exact configurations and 13 families. No new country or
OEM label this iteration. All six regions remain represented. These are accepted
branch counts, not merged-main counts. The PR cumulatively adds 13 projects,
enriches nine pre-existing projects, adds 67 exact models and enriches 17
pre-existing Microcare models; enrichment of new-in-PR OPzS models is retained.

## Project inventory attempts and accepted alternative

Attempted the Philippine DOE national inventories first. The March 2026 named
article route returned a page shell / Page Not Found; original existing/indicative
Luzon downloads returned Cloudflare 403. The indexed indicative file is dated
31 July 2025, not 2026. ERC's generation-certificate page and the EVOSS alternative
also returned 403. No bypass, repeated retries, third-party document copies or
unsupported registry observations were used. Inspected the 33 canonical Philippine
records for likely overlap, but zero source rows were accepted from these blocked
routes. The Taiwan result was a request for data, not a released registry.

An Eskom owner-portfolio attempt encountered a restriction already recorded in
older research ledgers. Downloads made before finding that entry were discarded;
no facts from the restricted page, report or EIA entered accepted records. The
alternative was independently hosted AfDB and World Bank project documentation.

The AfDB project index still lists the March 2026 IPR, published 28 May; its original
checksum is unchanged. The 2021 appraisal's seven-site table was reviewed, including
its rendered page. Seven existing records gain procurement design-rating basis and
five-year plant operation/maintenance requirements. Minimum usable package ratings
remain historical procurement requirements, separate from scalar operating ratings,
COD and warranties. Original status, capacities, creation times and previous nested
facts are retained. Historical lot numbering is explicitly dated rather than
silently replacing later package numbers.

The October 2018 ESMF explicitly links **Rietfontein** to the BESS/PV installation
at **Andriesvale**, explaining the substation-derived name. The World Bank's
15 August 2022 procurement plan identifies P04 / `ZA-ESKOM-298241-CW-RFB`, pairing
Melkhout Lot A with Rietfontein Lot B. The later AfDB IPR pairs Melkhout with
Reinfontein/Reinfointein under Package 4. This shared package and named partner,
with direct geography, supports a reviewed identity match, not fuzzy merging.
One canonical Rietfontein/Andriesvale project is added as announced with delayed
package progress as of 21 May 2026. MW/MWh, chemistry, exact equipment, coordinates,
contract award and COD remain unknown. The September 2027 programme target is not
site COD. The appraisal's broad Upington wording is retained as a review caveat;
no Upington point or administrative boundary is inferred.

Melkhout also gains the procurement ID, lot relationship, tender method, service
scope and historical settlement evidence. **One locality-spelling conflict**
(Koega in the appraisal versus Kouga/Humansdorp in the ESMF) is quarantined; the
existing locality is preserved. The USD88.218m P04 estimate covers both lots and is
recorded once in the review ledger, not allocated as site capex. A reported zero
actual amount is not interpreted as zero project cost. Four older site holds
(Witzenberg, Ashton, Cuprum, Kiwano) remain. Mt Fletcher is a historical 2018 concept
candidate requiring later lifecycle reconciliation; the ESMF's 47-site aggregate
is not expanded into fabricated site rows.

## Exact equipment and evidence reconciliation

Refreshed the original TAB brochure and live OGi table. The brochure checksum is
unchanged; preserve the literal `V15-03-01-2022 (atelje jk®)` print mark without
interpreting date order. Visually inspected PDF pages 6–7, including column units,
model nomenclature and dimension sketch. Accepted all 25 exact PDF configurations:
13 two-volt cells, six six-volt monoblocs and six twelve-volt monoblocs. Sixteen
additional website-only models are deferred to a separate scoped review.

The offline parser preserves seven discharge-rate Ah observations, final voltage
and reference temperature, milliohm resistance, **kA fault current**, dimensions
and separate dry/wet masses. The PDF order is dry/wet; the live HTML order is
wet/dry. All 350 numeric cells were compared. **Seven capacity discrepancies across
two models** are quarantined with both sources and exact model/column locators;
neither source wins automatically. Other agreeing observations remain accepted.
The printed temperature-compensation coefficient has a potentially erroneous
**mV/K** unit: its literal text is retained as one shared issue affecting all 25
models, with no normalized coefficient accepted. No whole equipment row rejected.

Added vented lead-acid chemistry, rated model voltage, SAN construction, terminal,
qualified protection/test claims, temperature bounds and recommendations, normal-use
DoD recommendation, float/boost and conditional recharge requirements, maintenance,
self-discharge, conditional upper-bound life and cycle claims. The 1,000-cycle claim
does not state test DoD/retention; the normal-use 80% recommendation is not substituted
for those conditions. Cell Ah is never populated from monobloc Ah. Fault current is
not operating current or power. No energy, active power, warranties, independent
certifications or project component assignments are inferred.

The source-specific parser rejects altered units, row order/identities, missing or
duplicate partitions and invalid capacity/mass ordering. Twelve synthetic tests
exercise these boundaries without redistributing an OEM document. Existing upsert
API used for additions and enrichments; seven nested JSON collisions were explicitly
reviewed as additive patches. Repeat-upsert and substantive timestamp preservation
checks passed; verification-time normalization was checked separately, not committed
as catalogue-wide churn.

## Priority, yield and next work

The dated market comparison retains the same-day IEA primary verification: selected
country ranking by **2025 utility-scale battery power additions in GW** (China,
United States, Australia). Comparable operational stationary battery energy GWh is
not available from that source, so no fabricated GWh ranking or power conversion.
This pass pursued underserved Asian inventory access and African enrichment while
deepening a regional Slovenian manufacturer's exact configurations.

Project yield is below 50–200 because official Philippine originals and two
alternatives were blocked, Eskom's collection restriction prevented that route,
and independent lender sources offered eight defensible project changes. The
25-model batch meets the planning range. The selected PDF partition and lender
rows are exhausted; no extra variants, old aggregate rows or stale status updates
were added to reach a quota. Next highest-value work is the 16 remaining OGi HTML
models with independently scoped conditions, the TAB UPS table, a new accessible
original Philippine inventory, and the next AfDB IPR/site-specific technical
schedule. Existing CEA/Microcare backoffs, Irish reuse restrictions, Chile rating
holds and all historical logs remain intact.

## Validation

- Both catalogue validators, references, natural identities and preservation checks passed.
- Each snapshot rebuilt twice: deterministic byte-identical output, typed Parquet
  readback and ZSTD verified. JSON coverage/manifests committed; source bytes and
  binary snapshots remain outside Git via the established artifact workflow.
- **471 focused BESS tests passed**, including 12 new parser cases.
- Repository Ruff lint/format and `ty` passed.
- Repository hygiene, citation checks, 25 viewer DOM tests and offline OEM example passed.
- Three wheel/sdist builds, strict Twine and isolated installed-wheel CLI checks passed.
- Strict local Sphinx build with gallery execution disabled passed; 660-page link/asset check passed after regenerating missing wind/hydro outputs with their existing publishers (no shared-code changes).
- No full local-suite pass claimed: the immediately preceding run documented the
  host Dask/psutil PID5 collection failure. Full Python 3.12/3.13 and gallery CI
  will be checked on the published commit and reported in the PR description.

Evidence: [review](2026-11-05_ogi_south_africa_review.json),
[captures](2026-11-05_ogi_south_africa_captures.json),
[backlog](2026-11-05_ogi_south_africa_backlog.json),
[markets](2026-11-05_ogi_south_africa_markets.json),
[coverage](2026-11-05_ogi_south_africa_coverage.json),
[manifests](2026-11-05_ogi_south_africa_manifests.json).

Local validation and publication preparation completed at **15:28:31 Atlantic/Canary (UTC)**, after **26.7 minutes** of actual effort. Publication and remote CI monitoring follow and are reported on the PR. Selected source partitions exhausted; no idle time to meet a duration. Final all-PR path check found no overlapping writes; main and target head unchanged.

[Cumulative and iteration audit](2026-11-05_ogi_south_africa_audit.json) recomputes counts against both live main and the iteration base.
