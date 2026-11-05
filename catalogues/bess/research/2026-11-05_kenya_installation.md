# Kenyan battery replacements and exact inverter installation requirements

Started 5 November2026 at19:50:41 Atlantic/Canary (UTC). Continued open PR172
from1d0e035, main76179409. All11 open PR titles and changed paths reviewed;
no other BESS edits. Shared bibliography edits remain excluded because of
concurrent wind/PVDeg work. Full attribution stays in catalogue source registers.

Two new projects: Syamakhanga and Buyende battery mini-grids near Busia, Kenya.
The22October2025 supplier release includes an attributed operator account of
replacement of failing lead-acid batteries with functioning lithium-ion BESS.
Kudura Power East Africa is the operator; Vittoria Energy is the named financing
counterparty, not an inferred manufacturer/EPC. The shared36-month Equipment
Sale and Use Agreement is not a site capex, completed ownership transfer or
warranty. Exact COD, MW/MWh, cell subtype and models remain unknown. No separate
old/replacement phase rows or inferred coordinates. Both names were reviewed
against all existing Kenyan rows and incoming identities; no fuzzy merge.

Nine existing exact MultiPlus-II230V configurations enriched from all nine
rows of original manual section4.3. External battery-bank Ah ranges, DC fuse
recommendations and two distance-dependent copper cable sizes remain installation
observations, never cell Ah, stored energy or continuous device current.90°C
cable rating, local-rule and open-conduit conditions preserved. Sections4.5.7–8
qualify parallel arrangements, equal DC cabling, ventilation and wye/delta
compatibility.8/10/15k models require an external AC transfer switch; no unsupported
six-unit limit assigned to them. New-style4k/4k5/6k5/10k and120V variants excluded
because they are absent from this table. Existing technical scalars, warranty,
conflicts, earlier namespaces and creation times remain unchanged.

The national owner annual-report batch was attempted first. Its174-page PDF
had no readable primary-reader text and direct transfer did not complete during
bounded review. No report facts were accepted. The independent supplier release
was the alternative; REREC reuse restrictions were not bypassed. Accepted source
bytes were captured outside Git with SHA256, UTC retrieval and exact locators.
No full documents, images or personal contacts are committed. No new parser or
schema; manual row review and the existing upsert API were used, with nine
additive nested collisions explicitly reconciled and idempotence checked.

Yield:2/2 named project candidates accepted;9/9 exact equipment candidates
substantively enriched;0 new models,0 existing project enrichments,0 new canonical
quarantines or permanent rejections. No new country/OEM. The selected model
partition contains nine rather than ten models; no variants invented to meet
planning targets. Project yield is below50–200 because the broader report could
not be extracted, while the alternative names only two sites. Selected accessible
batches exhausted; larger source queues remain open.

Totals:2,149 projects,48 countries,409 project sources;1,172 equipment records,
55 supplier labels,484 equipment sources. Existing six-region coverage retained.
Same-day named IEA selected-country2025 utility-scale battery power-additions
ranking retained, explicitly not operational stationary GWh or a complete ranking.

See linked sibling JSON audit, review, captures, backlog, markets, coverage and
manifests. Typed Zstandard Parquet snapshots stay outside Git. Validation and
actual elapsed checkpoint are appended before publication; final CI and total
elapsed time will be recorded in the PR description.

Local checkpoint 2026-11-05 19:58:56 Atlantic/Canary (UTC): approximately nine minutes elapsed, about four for source extraction/reconciliation and five for validation.500 focused BESS tests,25 viewer tests, preservation/idempotence, both validators, two deterministic ZSTD builds, Ruff/format/ty, hygiene/citations, offline example and strict Sphinx passed. Initial link scan ran before asset generation finished; final scan follows completed build. No full local suite or new package build claimed; published-head CI follows.
