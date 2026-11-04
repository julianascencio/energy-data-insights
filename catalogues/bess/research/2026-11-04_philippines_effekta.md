# Philippines projects, EFFEKTA monoblocs and Pylontech communications — 4 November 2026

This continuation of open PR #133 adds **8 projects**, substantively enriches **19 existing projects**, and adds **21 exact equipment models**. Nothing is merged. The live starting head was `b32c6f8e7f34385605d05fa1e3690b9b98453d4a`; main was `6b38f9a406c07bb2490f2ec49a612d37d9ebf349`. The older PR #44 checkpoint is historical, not the active branch or current count.

The resulting catalogue has **2,005 projects in 42 countries, with 321 project sources**, and **795 equipment records from 47 product suppliers, with 376 equipment sources** (782 configurations and 13 families). EFFEKTA is the new product brand/supplier; its underlying cell manufacturer remains unknown. No new country or installed project/equipment relationship is asserted. Coverage across Africa, Asia, Europe, Latin America/Caribbean, North America and Oceania is retained.

## Project batches and identity decisions

The scalable inventory work preceded isolated owner releases. NGCP March and September 2026 bulletins contain **21 and 22 reviewed battery service rows**, respectively. The historical DOE July 2024 Mindanao committed inventory contains **nine battery rows, totalling 220 MW of historical planned/rated power**. These partitions, with the MGEN owner cross-check, represent **30 reviewed project identities: 8 new, 19 enriched, one already evidenced and unchanged, two withheld**. These are overlapping source observations, not 52 new projects.

- Seven new DOE projects: Pitogo, Sangali, Tagum, Aurora, Placer, Maramag and General Santos. Preserve the source's locality, province, named company, planned MW, month/year targets and delay notes. Placer, Maramag and General Santos are explicitly on hold as of July 2024. Other entries retain a historical announced status. Past targets do not establish operation, and Company Name does not automatically mean owner/operator. Sangali also gains a September 2026 NGCP contract observation, without inferring physical lifecycle or as-built ratings.
- MGEN Toledo Phase 1 adds owner-reported **25 MW / 56.44 MWh**, lithium-ion chemistry, developer Toledo Energy Development Corporation, host Carmen Copper Corporation and reported two-hour duration. The planned equal-sized second phase remains nested and excluded from operating capacity; its June 2027 target is conditional. The NGCP Carmen name is reconciled by provider and site. This differs from the existing SMGP Toledo project. CATL and SUMEC remain named partners, with no invented cell/EPC/model assignments.
- Nineteen existing projects gain service types, ERC case numbers, provider roles, exact phase scope and certification/no-ASPA distinctions. Alaminos' two service phases remain one canonical project. Bataan maps to Limay, not Lamao. Masinloc's observation explicitly concerns Advancion Phase 1, not the combined facility rating. Kabankalan was already fully evidenced and remains unchanged.
- September changes add Lumban's new ASPA case and preserve the disappearance of the earlier San Manuel/Jasaan firm-capacity warning as a dated observation only. It does not prove restored service delivery. Omission of Gamu/Villanueva from September is not retirement.
- Tagoloan Phase 2 remains withheld pending reconciliation with Villanueva. The older DOE Villanueva 20 MW value is not substituted for the existing 22.83 MW. Makban-Bay Unit 2 remains withheld until reusable primary evidence establishes its battery-specific scope and useful technical metadata.

**BSS means black start service**, not battery storage. Hydro, coal, diesel and other non-battery entries in the NGCP service list are excluded. Contract certification is not COD.

The DOE historical PDF was successfully read through the public web PDF reader, but direct original retrieval returned 503 and later reader attempts returned 502. Its original-byte checksum is **null**, not a hash of an error page or reconstructed text. This is an explicit evidence limitation; recovering the original PDF and finding the current inventory are high-priority backlog actions. Current DOE routes and legacy downloads were attempted rather than silently treating July 2024 as current.

## Equipment batch and boundaries

**27 exact primary-source identities were reviewed: 21 accepted, six suffix variants withheld**. The accepted records comprise 18 EFFEKTA BTL AGM monoblocs, two BTLi LFP monoblocs and Pylontech LV-Hub-A. Eleven of the 17 individual BTL archive members match overview models exactly after whitespace normalization and add current/temperature evidence to those same new records; they are not eleven additional models. Six K/L/R suffix variants remain held without automatic suffix stripping or cosmetic duplicates.

BTL rows retain C20 **monobloc Ah**, 12 V, dimensions including separate case/terminal heights, weight, terminals and qualified lifetime/warranty claims. Eleven exact individual sheets add charge current, five-second peak current, resistance, charge/discharge/storage temperatures and source-member checksums. Rate-dependent capacities in individual sheets are not silently substituted for overview C20 values. Ah is not put in the cell-capacity field, and no MWh or active power is inferred.

BTLi rows add voltage/current limits, cutoff and protection values, cycle conditions with DoD/C-rate, temperature/humidity, Bluetooth, integrated BMS, physical data and IP65. The **BTLi 12-120B energy scalar is quarantined**: the sheet prints 1560 Wh alongside 120 Ah and 12.8 V, whose arithmetic product is 1536 Wh. Neither value is silently selected as the canonical energy. The other unambiguous model facts are accepted; one record is `needs_review`. This is one field conflict, not one rejected model.

LV-Hub-A uses the OEM-authored Information Version 2.2 manual publicly hosted by Victron. The record preserves 48 V supply, 2 W consumption, CAN/RS485 baud/termination, group topology, IP20, mass and temperatures. The unlabelled 442×190×44 mm sequence remains nested without invented axes. The older 12 V/3.5 kg LV-HUB is not merged. This is a communication component, not a battery or PCS. Project assignments remain unknown.

## Access, market context and reproducibility

Public access was not treated as an open bulk licence. IEMOP's legal page explicitly restricts adopting/modifying/reproducing information without prior written consent; **no canonical facts were ingested** from its participant table. ERC returned 403. Bornay restrictions and distributor-authored Pylon technical tables caused exclusions, not permission bypasses or technical fact substitution. NGCP, MGEN and OEM sources are bounded factual reviews with no copyrighted document redistribution. Original downloaded bytes and checksums remain outside Git. The seven newly registered sources have complete catalogue evidence; shared bibliography entries are queued because active wind PR #132 edits the common reference files.

The dated market ledger retains the IEA's named comparable metric: **2025 annual utility-scale battery power additions in GW**, selected country examples China 55.10, United States 16.22 and Australia 4.32. Regional values are not country ranks. A fresh download matches the previous verification bytes. A global operational stationary-energy GWh ranking remains unavailable; MW/GW additions are not converted to MWh/GWh or cumulative stock.

Two offline adapters stage EFFEKTA overview tables and the reviewed NGCP bulletin revisions. They reject malformed/duplicate rows and changed service semantics; NGCP unknown battery rows fail for fresh review. Tests use synthetic factual fixtures, not copied documents. Manual identity mapping and the existing upsert API produce canonical records; updates preserve prior facts and quarantine rather than overwrite conflicts. No schema changes were needed.

The preservation audit confirms **1,978 existing projects and all 774 existing equipment records are unchanged**. All prior numeric fields, nested evidence and creation timestamps survive the 19 project enrichments. Duplicate incoming identities and canonical IDs are checked. Both typed Zstandard snapshots are rebuilt twice, with identical manifests and hashes; binary outputs remain outside Git. The review ledger, coverage/completeness manifests, market assessment, bibliography queue and ranked source backlog accompany this log.

Project yield is below 50–200 because the bounded official service partitions largely enrich existing records, the useful historical DOE subset has only nine projects, and current DOE access, IEMOP reuse and two identity/scope holds prevent defensible bulk acceptance. The 21-model equipment objective is met without padding. The selected defensible batches are exhausted. Next: recover the current DOE grid-connected inventory and reconcile its Philippine battery rows, then review the six exact EFFEKTA suffix variants against current OEM editions.

Validation results and measured elapsed effort are recorded in the adjacent validation ledger and the checkpoint below. Historical launch reports and prior research logs remain untouched.

## Validation and effort checkpoint

Started 04:53:29 Atlantic/Canary (UTC). Validation checkpoint 05:19:04 Atlantic/Canary; **25.58 minutes elapsed**, followed by publication. Research/reconciliation occupied approximately the first18minutes; validation, filesystem recovery and publication preparation followed. Selected source partitions were exhausted; no idling to meet a time quota.

- Both catalogue validators, preservation audit, two identical typed Zstandard builds and both offline usage examples passed.
- **76 focused tests** (including19 new parser tests) and **15 Node viewer tests** passed.
- Full suite retry: **2,162 passed,15 errors**. All15errors arise from the unchanged inherited invalidUTF8 DataCenter KSTAR file, repaired separately in openPR131.
- Strict Sphinx with gallery execution reaches that same inherited encoding error. No successful full documentation/link audit claimed. Initial full tests/docs were interrupted by shared-volume exhaustion; reruns used an available private temporary volume.
- Repository-wide Ruff lint/format, ty, repository hygiene, citation consistency and whitespace checks passed. Three wheels/three sdists built and strictTwine passed. No new installed-wheel smoke or remoteCI pass claimed.
- Main and PR133head remain unchanged at the prepublication check. Open PV134, Wind132 and DataCenter131 changed paths were reviewed. Shared bibliography writes are deferred for Wind132; no unrelated fixes, merge or force-push.
