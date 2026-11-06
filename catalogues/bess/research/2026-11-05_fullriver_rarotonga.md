# Fullriver exact sheets and Rarotonga enrichment

Started 5 November 2026 at 23:54:25 Atlantic/Canary (UTC). Continued open PR187
at 5b91c1315 in an isolated checkout; current main remains 4ef42de4. Open PR183–187
titles and full changed paths were inspected; no overlapping BESS writes.
Repository contribution/workflow instructions, dictionaries, existing sources,
coverage and recent logs were reviewed. Historical Australia/Chile holds remain.

## Accepted changes

Fifteen exact OEM headings reviewed: fourteen new configurations, one identity held
(DC50-12 index points to a DC50-12A sheet). No existing equipment updates.
Models: DC50-12B, DC60-12A/B, DC65-12A/B, DC70-12, DC80-12, DC90-12,
DC115-12B, DC120-12A/B/C, DC145-12 and DC180-12. Exact suffixes have distinct
physical/rating tables. They are battery units, not cells or integrated AC systems.

Each accepted row has exact-sheet Ah by discharge rate, nominal voltage,
milliohm resistance, mechanical data and bank-voltage charging/temperature
conditions. Five rows retain field holds: DC60-12B unusual C100 value, DC65-12B
native rounding differences, and DC80-12/DC115-12B/DC120-12A width discrepancies.
DC60-12B C100 and DC120-12A mechanical table were visually inspected.
Affected values stay outside resolved scalars; no inferred energy, power,
duration, cell count, cycle warranty or installed project assignment.
DC60-12A/DC65-12A have exact sheets but no exact live cards; no suffix substitution.

One project enriched: Te Mana o Te Ra MPower BESS. Independent integrator evidence
adds grid connection, co-location, customer and qualified project-value observations.
The 11kV connection is explicit. Its 5.6MWh usable observation differs from the
historical 4MWh unspecified scalar; preserve both and flag the basis/revision gap.
No new project, country or supplier; no operational-status refresh. Project value's
currency and price year remain unknown. No ministry-derived Airport West alias.

## Source review and limits

ADB's Cook Islands multi-component register and procurement-plan original returned
403. A government fiscal portfolio and newer ministry review were alternatives,
but the ministry terms impose personal/noncommercial and electronic-copy limits.
No ministry technical facts were imported. The previously downloaded report and
text were removed after that assessment; only discovery/checksum metadata remains.
Three distinct unresolved phase candidates remain held, not new canonical records.
MPower's independent case page supplied the one accepted enrichment.

Fullriver index, cards, fifteen PDFs, privacy and ordering policies were freshly
retrieved. Copyright retained; bounded factual extraction, not an asserted open
bulk licence. Original PDFs/HTML stay outside Git. Source metadata retains URLs,
retrievals, original-byte hashes, publisher, exact model, page locator and unknown
revision. Existing offline source-specific parsers were reused without schema/code
changes. No parser changes or new synthetic tests were needed for this data batch.

Current totals: 2,150 projects /48 countries /412 sources and 1,216 equipment rows
/56 supplier labels /530 sources (1,203 configurations and13 families). Six regions
remain represented. IEA 29May2026 selected-country 2025 utility-scale GW additions
ranking was freshly checked; operational energy GWh comparison remains unavailable.

The fifteen-heading equipment partition is exhausted. Project yield falls below
the planning range because original register access and alternate reuse terms
blocked phase resolution. Next: eight remaining DC headings and independent dated
Rarotonga/Aitutaki as-built records, retaining all prior holds. This is not a claim
that worldwide research is exhausted.

## Validation checkpoint

Both catalogues validate. Independent typed Zstandard snapshots are byte-identical,
with reference checks, no-op upsert and preservation of every prior fact/source and
created_at. The one nested-JSON upsert collision was reviewed as an additive
namespace; no prior value was overwritten. Focused tests and repository checks are
recorded in the validation ledger. Full published-head CI will be recorded in the
PR description. Actual pre-publication elapsed effort is recorded there with final
publication/CI time; no waiting to meet a duration target.

Research, extraction/reconciliation and first validation checkpoint completed at
00:02 on 6 November Atlantic/Canary, approximately eight actual elapsed minutes.
Existing parsers enabled this bounded fifteen-sheet partition to be processed
quickly. Publication and full hosted CI are additional effort, reported on the PR.
