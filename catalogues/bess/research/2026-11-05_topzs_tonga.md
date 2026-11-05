# TAB TOPzS and Tonga contract-status enrichment — 5 November 2026

Started **17:52:35 Atlantic/Canary (UTC)**. Isolated checkout of open PR172 at
`97e347222c9620aacb08706fc0a46c826bd38951`; main `76179409` unchanged.
Read current instructions, dictionaries/schema, source register, coverage and recent
ledgers. All11 open PR titles and complete changed-path inventories reviewed:
only172 touches BESS. No shared-schema/PV edits, agents, force push or merge.

## Accepted records and evidence

Equipment: **10 new exact models**, zero existing-model enrichments or whole-record
quarantines/rejections. Eight TOPzS candidates accepted; two remaining live-only
OPzS candidates accepted. The28 previously imported OPzS identities were checked
and skipped. All30 OPzS table identities now map to canonical records. Eight live
TOPzS rows crosscheck80 numeric observations against the brochure after explicitly
reversing wet/dry mass columns. The printed `6 TOPzS750` spelling is retained with
its reviewed web spacing alias, not duplicated as a configuration.

Fresh original TAB brochure and two HTML pages returned200; SHA256, exact URLs,
retrieval times and lengths are in captures. Rendered PDF page11 checked. TOPzS
pages10–11 support2V cell identity, three rate-specific Ah observations, resistance,
fault current in A, dimensions, dry/wet masses and tolerances, construction,
float/boost voltage, temperature limits, self-discharge and maintenance. C10 is at
20°C/1.80V per cell; C100 is at25°C/1.85V. C20 temperature stays unknown. The1200-cycle
claim lacks DoD/retention; normal-use80% DoD is not a test condition. Up-to15-year
operational life is not a warranty. Test-standard claims are not independently
verified certificates. No energy or active-power inference.

The26 OPzS3250 and28 OPzS3500 rows add four rate capacities, resistance, fault
current, physical dimensions, dry/wet masses and eight terminal poles. Their live
source does not establish nominal voltage, capacity-test temperature, cycle/design
life, warranty or operating limits. Brochure-only conditions were not copied.

Projects: **11 existing Tonga sites reviewed and substantively enriched**, zero
new projects or whole-record rejections/quarantines. Began with the official TPL
portfolio/TREP index and attempted the FY2024–25 annual report. Reader timeout/502
and original-download503 prevented annual-report ingestion. Four indexed primary
contract tables provide a defensible alternative; direct pages216/217 returned502,
219/220 timed out. Original checksums are null, not hashes of search excerpts.

TREP-03 Lot2 matches Kotu, Oua, Tungua, Moungaone and Niuafoou; TREP-12 matches Ofu,
Hunga, Kapa Otea and Kapa Falevai. **Nine statuses** move from historical planning/
construction to an owner-reported operating observation, dated by access to the
undated table. Prior statuses, source periods, notes and namespaces are retained.
Niuafoou clinic/OIREP assets and other islands are excluded from these identities.
Contractor, procurement procedure, bidder counts, award/certificate/commissioning
periods and contract-level funds dispersed are recorded without inferring EPC/OEM
roles, site capex or ownership. TREP-12's estimated certificate remains an estimate.

TREP-01 Popua and TREP-02 Matatoa gain contract milestones, with **two chronology
holds**: Q4 2021 commissioning versus earlier2022 opening/2023 commissioning-year
observations. These remain qualified in the new evidence namespace; exact COD is
not selected. Existing capacity conflicts and all MW/MWh values remain unchanged.
Owner-index status is not proof of present availability. No component assignments.

Copyright retained for all sources; bounded factual review only, no open bulk reuse
licence asserted. No full documents/prose, personal contacts or binary dumps in Git.
No contact, login, payment or access-control bypass. Existing restricted-source
and backoff conditions remain in effect.

## Implementation, counts and continuation

New offline `stage_bess_tab_topzs.py` parser checks exact identities, table headers,
rate conditions, A versus kA, numeric width and mass order; nine synthetic tests.
Existing upsert API used. Eleven collision-bearing project patches were explicitly
reviewed; nine follow-up editorial-note patches preserve the prior text in history.
Old facts, creation times and conflicts retained; replay is idempotent.

Totals: **2147 projects /48 countries /408 sources;1172 equipment records
(1159 configurations,13 families) /55 suppliers /482 sources**. No new country or
OEM this iteration; all six regions remain represented. Cumulative PR versus main:
13 new projects,20 enriched pre-existing projects,108 new exact models and17 enriched
pre-existing Microcare models. Counts are unmerged branch content, not merged main.

Same-day IEA comparison retains its original verification time: selected-country
2025 utility-scale battery POWER additions in GW, China/US/Australia. It is not a
complete world ranking or comparable operational stationary GWh inventory.

The10-model batch meets the equipment planning range. Project yield is below50–200:
the selected owner table partition contains11 already-catalogued sites, with useful
status/contract enrichment; the broader annual report was inaccessible. All selected
38 equipment identities (10new/28previous) and11 project identities are reviewed.
These selected partitions are exhausted, not the global research backlog. Next:
original TPL FY2024–25 report after the saved backoff, permitted Philippine national
inventory, and another regional OEM beyond the completed TAB brochure. Keep CEA,
Microcare, Philippine, Eskom, Irish and Chile restrictions/holds unchanged.

## Validation and effort

Both catalogues and field references validate. Two independent typed Zstandard
Parquet builds are byte-identical, with row counts/schema/compression read back.
Creation timestamps, original fields, reviewed natural identities, existing ratings
and conflicts are checked.500 focused BESS tests (nine new) and25 viewer DOM tests
passed, along with Ruff lint/format,ty, repository hygiene/citations, offline OEM
example, three wheel/sdist builds, strict Twine and installed-wheel CLI checks.
Strict local Sphinx/gallery-disabled and link results are appended after completion.
Full local suite was not claimed because of the prior host Dask/psutil limitation;
final published-head Python3.12/3.13 and documentation CI are reported in the PR.

[Review](2026-11-05_topzs_tonga_review.json),
[captures](2026-11-05_topzs_tonga_captures.json),
[backlog](2026-11-05_topzs_tonga_backlog.json),
[market comparison](2026-11-05_topzs_tonga_markets.json),
[coverage](2026-11-05_topzs_tonga_coverage.json),
[manifests](2026-11-05_topzs_tonga_manifests.json),
[audit](2026-11-05_topzs_tonga_audit.json).

Strict local Sphinx and link checks passed; local asset publishers ran without shared edits.
Local validation checkpoint **18:08:23 Atlantic/Canary (UTC)**, **15.8 minutes actual effort**.
Selected partitions exhausted; publication and final CI follow. No idle time added.
