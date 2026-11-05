# Microcare exact configurations, Freedom Won controls and Mauritius projects

Started 5 November 2026 at 11:46:05 Atlantic/Canary (UTC on this date). The working
checkout was restored after workspace maintenance. PR #159 was already merged
externally at 10:55:47; no closed branch was reused. This iteration starts from
main c44b15a0 in isolated branch research/bess-database-20261105T115600Z.
Read current dictionaries, schemas, sources, coverage and the earlier Australia/
Chile ledger and latest Studer/Neata logs; historical launch reports are unchanged.
Open PR titles and changed paths were inspected for #166, #161, #157, #47–49, and newly
opened #167. No BESS overlap. PR #157 overlaps the shared bibliography, so new
bibliographic metadata is committed in the source registers and reference queue.

## Accepted work and identity review

- **17 new Microcare exact inverter configurations**, a new South African
  manufacturer label. The three original manuals stage 18 columns: the same
  5kW48V appears twice with identical staged ratings and becomes one record.
  Explicit variants are 1 kW at 12/24/36/48V,2kW at 12/24/36/48V,3kW at 24/36/48V,
  5kW at 24/36/48V, and 8/10/15kW at 48 V. These are distinct published electrical
  configurations, not arbitrary combinations or separate records for software versions.
- Added active AC power, battery voltage envelopes, DC current and standby
  observations, charging current, AC voltage/frequency/regulation, power factor,
  fan cooling, width/depth, native LxWxD dimensions, efficiency boundaries,
  float voltage and manufacturing-date-qualified carry-in warranty. Battery
  energy/chemistry, charging power, RTE, certifications, IP and mass remain unknown.
  Grid-assisted 200% throughput is not doubled battery inverter power. Datasheet
  peak efficiency below 94% and manual 90% efficiency have different stated bases.
- **Nine existing Freedom Won LiTE2 Commercial configurations enriched** with
  CAN2.0/SAEJ1939, optional 250 kbps versus usual 500 kbps profiles, interface counts,
  Ethernet gateway, maximum 20 same-model parallel units, warranty retention,
  cycle/DoD/sales-date limits, transport exclusions and service conditions.
  Explicit matching model tables bound applicability. All previous scalar facts,
  nested observations, evidence references and created_at were preserved.
- **Two new Mauritius projects**: L’Avenir and the Trèfles solar-hybrid battery.
  L’Avenir is one named-site record for two planned 20 MW / 60 MWh systems; 40 MW / 120 MWh
  are documented arithmetic totals, with unspecified electrical/energy bases and
  no inferred duration. June 2025 acceptance/award and forecast milestones are
  retained without asserting physical construction or operation. Trèfles has
  1 MWh battery energy; 500 kW AC belongs to its PV component, not battery power.
  PSIP IDs and fiscal estimates are retained; hybrid/site budget values are not
  silently converted into battery-only capex or contract prices.

No existing project received a substantive update. No new country, standalone OEM
entity table or project/equipment assignment was created. Both catalogues retain
coverage across Africa, Asia, Europe, Latin America/Caribbean, North America and
Oceania. Counts are researched records, not a census or installed-capacity ranking.

## Holds and conflicts

Six project decisions: 2 accepted, 2 held, 1 excluded unnamed programme and 1 already
covered. PointeMonnier2MW/4MWh may be an expansion, replacement or revision of the
existing 1.5 MW project; no duplicate created. TamarindFalls15MW/68MWh feasibility
was shelved in the annual report, while the later budget describes 17.5 MW PV with
12 MW battery: revival/phase identity needs primary clarification. Five unnamed
water-treatment sites are excluded as individual projects. Amaury20MW/10MWh
commissioning, contractor and grid facts are already covered and were not churned.

All 17 Microcare identities are accepted. Three retain field-level conflicts:
8kW maximum input current 200 A versus 375 A, standby 100 W versus 90 W and charger 40 A
versus 80 A; 10/15 kW AC-current rows disagree between manuals and datasheets. Both
observations retain citations; no resolved values are fabricated. Two further
Freedom Won candidates are held: existing 230/184 HV versus manual HV+ identity,
and 500/400 HV pending revision reconciliation. Neither becomes a new record.

## Evidence, source access and implementation

Scalable sources were attempted first: CEB's replacement publications index,
its 2024/2025 annual report, and the Ministry of Finance 2026–2031 PSIP. Original
PDFs were downloaded, searched for every battery mention and relevant tables
visually reviewed. The CEB download was slow but succeeded; no cached portfolio
snippet was promoted. No repeat of the earlier PV-only award or blocked CEA
request within its 24-hour backoff window.

Microcare's original public product page links three manuals and three datasheets;
all were downloaded, checksummed and reconciled, alongside manufacturer identity
and sales terms. Model tables control ratings; copied 10/15 kW introductory text in
small-inverter sheets and copied 5/8 kW web bullets do not. The catalogue uses bounded
factual observations with attribution; no open bulk-reuse licence is asserted.
CEB/Ministry and OEM copyright is retained; no full documents or raw binaries in Git.

Freedom Won originals returned 403 once each; no bypass or repeated retry. The
public primary PDF web reader supplied reviewed historical manual text, clearly
registered as reader access. Its extract checksum is **not** an original-PDF hash.
The cover revision table and running-header disagreement is preserved. Older
manual thermal/electrical ratings never replace newer datasheet values.

`stage_bess_microcare.py` and the package adapter read local layout text only.
Revision, exact ordered models, units, column counts and voltage envelopes must
match. Seven synthetic tests exercise column permutation, units, missing columns,
invalid ranges, revision changes and duplicates. Original-byte replay yields the
18 observations / 17 reviewed identities. Existing upsert API was used; nine nested
additive collisions were explicitly reviewed, with preservation and idempotent
replay assertions. No fuzzy merge, null erasure or timestamp-only change.

## Coverage and market comparison

Current branch totals: **2,134 projects / 47 countries / 393 project sources** and
**1,064 equipment / 54 supplier labels / 476 equipment sources**. Equipment comprises
1,051 exact configurations and 13 families. Net delta is 2 projects, 17 equipment,
9 equipment enrichments and 11 source registrations. New supplier: Microcare;
no new country. Detailed field completeness and snapshot hashes are committed.

Freshly rechecked IEA 29 May 2026 commentary ranks the explicitly quantified selected
countries by 2025 utility-scale battery **power additions**: China≈55GW,
United States>16GW, Australia≈4.2GW. This is not an exhaustive world ordering or
operational stationary energy in GWh. Europe is a region and excluded from country
ranking; no MW/MWh conversion is inferred. The source and licence are in the
market ledger.

## Validation and next work

Both catalogues validate; final typed Zstandard snapshots rebuilt twice with
identical bytes outside Git. All prior facts/created_at and reference integrity
checked; upsert replay is idempotent. 437 focused BESS tests, including 7 new parser
tests, passed ; 35 catalogue/parser tests passed again after final data adjustments.
25 viewer tests, offline OEM example, repository-wide Ruff/format, explicit-runtime
ty, repository hygiene, citation consistency, all three package wheel/sdist builds,
and strict gallery-disabled Sphinx passed. 652 HTML pages passed links/assets checks.

Full pytest encounters an existing psutil.NoSuchProcess collection failure on
unchanged main as well. Excluding only that file for diagnosis gives 2723 passes,
5 skips, 31 failures and 24 errors; every failure/error endpoint is the same psutil
exception. This is not a full-suite pass. Unchanged main produces 2716 passes, 5 skips, 31 failures and 24 errors,
with the same failing/error test identities. The branch adds exactly seven passing
parser tests. Exact final check results are in the validation ledger. No tests, dependencies or runtime
checks were changed to conceal this environment problem. Remote CI is separate.

The selected three manual tables, exact-model reconciliation and official annual/
budget battery sections are exhausted for this pass. The 17 new-model objective is
met; the 50–200 project objective is not: the official source batch has only six
reviewable decisions, two unresolved identities and an unnamed aggregate. The
wider research queue is not exhausted. Next: independent CEB site/contract evidence
for PointeMonnier/TamarindFalls, Microcare's separately identifiable monitoring
hardware, then CEA September inventory after 2026-11-06T07:59:49Z backoff. The 47-entry
backlog preserves earlier cursors, terms and retry conditions.

Actual elapsed through final validation and publication preparation: 29.8 minutes, ending 12:15:53 Atlantic/Canary. About 15 minutes covered discovery/extraction/implementation; the remainder covered validation, reconciliation and publication preparation. Subsequent upload/CI time is not included in this checkpoint.
