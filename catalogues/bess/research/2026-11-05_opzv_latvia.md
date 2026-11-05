# TAB OPzV and Latvia — 5 November 2026

Started **14:27:14 Atlantic/Canary (UTC)** from live open PR #172 head
`ff1e0f18f9bdc7a69b57940db63c970996300c69`; main
`76179409be2ce1166d60714145f1711776182b16`. Used an isolated checkout. Read
current instructions, schema/dictionary, source registers, current coverage and
prior logs; inspected every open PR title and changed-path list. Other PV, wind,
hydro and data-centre work did not overlap these scoped writes. Historical PR #44
and launch counts are not the current baseline. No merge or force-push.

## Accepted changes

| Entity | Candidates reviewed | New | Substantively enriched | Rejected rows |
| --- | ---: | ---: | ---: | ---: |
| Named Latvian BESS sites | 8 | 8 | 0 | 0 |
| Exact TAB OPzV cells | 14 | 14 | 0 | 0 |
| Existing TAB OPzS cells/blocks | 28 | 0 | 28 | 0 |

The project total is **2,146 records / 48 countries / 402 sources**; equipment is
**1,106 records / 55 supplier labels / 479 sources**, comprising 1,093 exact
configurations and 13 families. No new country or supplier label this pass. All
six geographic regions remain represented. Latvia grows from four to twelve
named project records. Counts describe accepted PR content, not merged main.

## Project batch and evidence boundaries

Processed the downloadable Saules BESS owner/issuer portfolio before considering
individual releases: the August Q2 report, 9 June offering memorandum, dated
28 August issuer announcement on Nasdaq, current issuer site, parent site and
Merito owner article. The memorandum explicitly defines eight **BESS Projects**
at named PV sites; these are not inferred battery rows from a solar-only list.
The reviewed definitions provide localities/admin regions and host-PV capacities.
The report supplies battery owner/operator, EPC, equipment supplier and lifecycle.

Cēsis, Kalkūne and Carnikava began Nord Pool day-ahead commercial operation in
August 2026. Zilupe, Brenguļi, Inčukalns, Koknese and Valmiera remained under
construction in the dated evidence. Balancing qualification remained future;
neither a financing close nor appointment of Capalo AI proves that qualification.
Kehua is retained as equipment supplier, not assigned as cell manufacturer or an
invented exact model. KL Systems is the EPC. The eight incoming identities were
manually checked against all four existing Latvian projects and one another.

The 120 MWh portfolio and 70/50 MWh stage totals are retained **once in the review
ledger**, not divided among sites or entered as a ninth aggregate asset. Likewise,
the approximately 55 MW portfolio grid-access limit is not battery nameplate.
All eight site MW/MWh values remain unknown. The EUR22m senior bond financing is
portfolio-only. A EUR25m budget excluding VAT in the report versus EUR24m capex
on the undated homepage is one unresolved portfolio cost conflict; both are held
in the ledger, with no site capex inferred. The PV MW fields are explicitly host
ratings and are excluded from battery capacity.

## Equipment batch and reconciliation

Refreshed original TAB PDF bytes (checksum unchanged), extracted all fourteen
OPzV rows on page12, inspected the rendered table/dimension sketch and compared
all 168 numeric/table cells against a fresh direct OEM HTML download. The live
HTML differs from both the brochure and search-index rendition. **86 conflicting
numeric fields across all fourteen models** are quarantined with both source
observations: measured rate-capacity Ah, fault current, twelve wet masses and four
resistances. No source wins automatically. Accepted fields include matching
nominal Ah and dimensions, explicit gel/VRLA chemistry, construction, terminal
and torque, float/boost conditions, conditional cycle/life claims and test-standard
claims. Two agreeing wet masses and matching resistance observations remain usable.
No nominal voltage, energy, operating current or active power was inferred.

H1 and H2 remain distinct; the rendered diagram identifies H2 as overall height
including terminals. Nominal Ah is separate from measured C10 Ah. Fault current
is not operating power. OEM tests are not independent certifications; up-to-20-year
life and 1,200 cycles are not warranties and have no invented temperature/DoD.
The new offline source-specific parser stages the complete reviewed partition,
rejecting altered units/revision/identities, partial pages and malformed heights.
It never writes canonical records or resolves conflicts by itself.

All 28 existing OPzS records gain the explicitly scoped recharge conditions:
6 hours up to92% at 1.5×I10 initial current and2.23V/cell after50%C10 discharge;
water-refill interval greater than2years at20°C. The printed brochure mark
`V15-03-01-2022 (atelje jk®)` corrects the earlier “undated” evidence label without
interpreting its date order or changing stable identities. Original creation times,
existing facts and nested evidence were preserved. The existing upsert API flagged
nested changes; an explicit additive review preserved all previous keys before
accepting the enrichments. Replaying the accepted batch is idempotent.

## Access, market priorities and limitations

No open bulk-reuse licence was assumed. Reviewed bounded factual observations,
source metadata and checksums are committed; original copyrighted HTML/PDF bytes
and generated Parquet remain outside Git. The offering memorandum's securities
placement restrictions were inspected; no offering text, investor contact or
financial recommendation was produced. Source-specific parsers use synthetic
fixtures, not redistributed document pages.

The [market comparison](2026-11-05_opzv_latvia_markets.json) retains the same-day
verified IEA29May2026 comparable metric: selected-country 2025 utility-scale
battery **power additions**, China approximately55GW, US greater than16GW,
Australia approximately4.2GW. This is not an exhaustive country ranking or an
operational stationary-energy GWh ranking. Comparable GWh ordering remains
unavailable; Europe is regional and excluded from the country ordering.

Project yield is eight because the selected owner portfolio has eight explicitly
identified sites; per-site battery allocations were not published in the reviewed
reports. The exact-model batch meets the10–30 planning range, with conflicts
exposed rather than thin duplicate variants added. These selected source batches
are exhausted; the wider research backlog remains open. Irish public-reuse gates,
CEA and Microcare retry deadlines, and earlier Chile/Slovenia holds remain intact.
Next: obtain revision-labelled OPzV specifications and the next Saules site-level
technical/reporting update; the separate TAB OGi partition offers another bounded
model batch after freshness/terms review. Resume Asia/Africa source queues only
when their recorded gates permit.

## Verification and publication

Catalogue validation and all field-source references passed. New/incoming identity
checks and timestamp-preservation review passed. Both catalogues were rebuilt twice
using the package: deterministic byte-identical outputs, typed Parquet readback
and ZSTD verified. JSON manifests and field coverage are committed; binary snapshots
use the established external/CI artifact workflow.

- Focused BESS suite: **459 passed**, including11 new parser/boundary cases.
- Repository Ruff lint/format and `ty`: passed.
- Viewer DOM tests: **25 passed**; offline BESS OEM example passed.
- Repository hygiene and citations: passed.
- Three package wheel/sdist builds, strict Twine checks and isolated installed-wheel CLI smoke checks: passed; new parser bytes verified inside wheel.
- Strict Sphinx build with gallery execution disabled and generated-page link check: passed.
- Local full-suite attempt stopped at collection in `test_kgpv_worldwide_example.py`: host `psutil.NoSuchProcess` for PID5 from Dask initialization. This is the previously observed environment issue; no full local-suite pass claimed. GitHub CI results are tracked on the PR.

Pre-publication work completed at 14:48:22 Atlantic/Canary (UTC), after 21.1 minutes of actual discovery, extraction, reconciliation and validation. Publication/remote-CI monitoring follows and is reported on the PR. Selected source partitions exhausted; no idle time to reach the45-minute ceiling. Final main/head and all open-PR paths rechecked, including newly opened #175; no overlapping BESS writes detected.

Evidence: [review ledger](2026-11-05_opzv_latvia_review.json),
[captures](2026-11-05_opzv_latvia_captures.json),
[ranked backlog](2026-11-05_opzv_latvia_backlog.json),
[coverage](2026-11-05_opzv_latvia_coverage.json),
[manifests](2026-11-05_opzv_latvia_manifests.json).
