# TAB live OGi models and South African safeguards — 5 November 2026

Started **15:51:56 Atlantic/Canary (UTC)** from open PR #172 at
`0ba653bf91c9f42789c6bb182ce754df69eea4a9`; main was
`76179409be2ce1166d60714145f1711776182b16`. Isolated checkout; current instructions,
schema/dictionaries, source registers, coverage and prior ledgers reviewed. All
11 open PR titles and changed paths inspected, including PV. No overlapping BESS
writes, shared schema changes, parallel agents, merge or force-push. PR #44 is historical.

## Accepted changes

| Entity | New candidates | New | Substantively enriched | Rejected/quarantined whole rows |
| --- | ---: | ---: | ---: | ---: |
| South African projects | 7 | 0 | 7 | 0 |
| Exact TAB equipment models | 16 | 16 | 0 | 0 |

The complete 41-row live OEM table was reconciled: 25 previously processed exact
identities were skipped and 16 remaining identities accepted. No cosmetic variants
or fuzzy merges. Totals are **2,147 projects / 48 countries / 404 project sources**
and **1,147 equipment records / 55 supplier labels / 480 equipment sources**,
comprising 1,134 configurations and 13 families. No new country or OEM label.
All six world regions remain represented. This PR now cumulatively adds 13 projects
and 83 exact models and enriches nine pre-existing projects and 17 pre-existing
Microcare models. The seven projects in this pass overlap earlier PR enrichment;
they are not counted twice. These are branch counts, not merged-main content.

## Evidence and reconciliation

Attempted the independently hosted official AfDB multi-site lender portfolio
before isolated project releases. The index reader returned 402, but the original
appraisal PDF returned 200 with unchanged checksum. Visually checked PDF page 23
(printed page 12), Table 3.2. All seven named sites receive borrower in-country
ESIA/ESMP disclosure dates and the common Bank disclosure date of 21 May 2021.
These historical safeguard-document disclosures are neither permits nor
construction/COD milestones. Existing lifecycle, scalar MW/MWh, procurement data,
conflicts and creation timestamps remain unchanged. Seven nested upsert collisions
were reviewed as additive namespace patches; previous facts were preserved.

The TAB live table also returned 200 with unchanged checksum. Its malformed row
boundaries require flattened `td/th` text in DOM order, including empty cells.
The new offline adapter validates all 41 exact identities and the capacity-rate,
end-voltage, resistance, fault-current, dimension and wet/dry mass headers. Eleven
synthetic tests cover missing blanks, units, rates, voltage, identity and mass order.
No copyrighted full table or document fixture is committed.

The 16 accepted models gain six or seven rate-specific Ah observations and end
voltages, milliohm resistance, kA short-circuit current, physical dimensions and
separate wet/dry mass with tolerance. Vented lead-acid chemistry is explicit.
Two models explicitly state 2 V; the other 14 have no voltage inference. Fourteen
five-minute Ah cells remain null. The page's 20°C condition belongs to electrolyte
density, so capacity reference temperature stays unknown for all 16. No brochure-only
life, cycle, charging, temperature or terminal specification is extrapolated.
No energy, active power, warranty, independent certification or project equipment
assignment is invented. Existing 25-model brochure conflicts remain untouched.

Existing source IDs are reused because URLs and bytes are identical. Fresh retrieval
timestamps, exact locators, licence assessment and SHA256 are in the capture ledger;
source-register timestamps are not churned. Both sources retain copyright; only a
bounded factual review is committed, not an assertion of permission for bulk reuse.
Raw originals and binary snapshots remain outside Git.

## Priority and backlog

The same-day IEA primary verification is retained with its original check time:
selected-country **2025 utility-scale battery power additions in GW** rank China,
United States and Australia. This is not an exhaustive world ranking. Comparable
operational stationary battery energy GWh is unavailable from that source, so none
is fabricated or converted from MW/GW. The backlog retains all six-region priorities.

Project yield is below 50–200 because this selected lender table has seven useful
existing-site observations, not new project rows. Previously blocked Philippine
DOE/ERC/EVOSS sources are not retried immediately; Eskom's recorded collection
restriction is respected through the independent lender route. The 16-model batch
meets the equipment planning range. Both selected defensible partitions are exhausted;
no thin rows or timestamp changes are added to reach a quota.

Next highest-value equipment work is the unprocessed TAB UPS table, with fresh
revision/terms and model-specific condition review. Next project work is a new AfDB
IPR or independent Rietfontein technical schedule and an accessible original
Philippine inventory. Existing Chile, CEA, Irish reuse, Microcare and South African
holds remain as documented. Rietfontein's prior identity resolution is preserved.

## Reproduction and validation

Extract local HTML cells as `[x.get_text(' ', strip=True) for x in
BeautifulSoup(html, 'html.parser').select('td,th')]`, preserving empty strings,
then run `scripts/stage_bess_tab_ogi_web.py --cells cells.json --output staged.json`.
The stage contains 41 observations; compare exact canonical identities before
accepting only the 16 reviewed extras. The CLI never writes canonical records.

Both catalogue validators and field references passed; duplicate/natural-identity,
creation-time, scalar-status/rating and previous nested-fact preservation checked.
Each typed Parquet snapshot rebuilt twice with byte-identical output and ZSTD
readback. Existing upsert replay is idempotent; no verification-only churn committed.

- 482 focused BESS tests passed, including 11 new synthetic adapter cases.
- Repository Ruff lint/format, ty, hygiene and citation checks passed.
- 25 viewer DOM tests and offline OEM usage example passed.
- Three wheel/sdist builds, strict Twine, installed-wheel CLI checks and exact
  packaged-parser/source comparison passed.
- Strict Sphinx with gallery execution disabled passed. The existing wind/hydro
  publishers regenerated missing local assets without any shared-code edits;
  link/asset validation is reported in the publication checkpoint below.
- Full local suite was not rerun: the preceding iteration documented the host
  Dask/psutil PID5 collection issue. Published-head Python 3.12/3.13 and full
  gallery CI will be checked and reported in the PR description.

Evidence: [review](2026-11-05_ogi_live_safeguards_review.json),
[captures](2026-11-05_ogi_live_safeguards_captures.json),
[backlog](2026-11-05_ogi_live_safeguards_backlog.json),
[markets](2026-11-05_ogi_live_safeguards_markets.json),
[coverage](2026-11-05_ogi_live_safeguards_coverage.json),
[manifests](2026-11-05_ogi_live_safeguards_manifests.json),
[iteration/cumulative audit](2026-11-05_ogi_live_safeguards_audit.json).

Local validation and publication preparation completed at **16:06:06 Atlantic/Canary (UTC)**, after **14.2 minutes** actual effort. The 662-page local link/asset check passed. Publication and remote CI monitoring follow; final elapsed effort is reported in the PR. Selected source partitions exhausted; no idle time added. Main and open-PR path review found no overlapping writes.
