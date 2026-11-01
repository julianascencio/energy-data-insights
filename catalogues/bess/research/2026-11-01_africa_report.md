# Africa project and OEM-depth pass — 1 November 2026

13 new project records (South Africa 6, Namibia 2, Senegal 1, Egypt 4) and two substantive enrichments (Hex and Abydos I). One accepted new identity, Omburu, has quarantined power/energy ratings and `needs_review`; the other 12 new records are source-backed. Current snapshot: **1,263 records, 30 countries, 80 sources**. Namibia and Senegal are new countries. This is committed research for open PR #44, not merged content.

## Discovery and reconciliation

31 named project candidates reviewed: 13 new, two existing enriched, 16 held, no definitive rejection. Holdings are nine Philippine Luzon battery rows, five South African sites requiring independent evidence/reuse review, and two AMEA-only Egyptian candidates. India CEA source access failed before row-level review and is not included in the candidate count. See the machine-readable review ledger for all accepted IDs and held names.

Official India CEA and Philippine DOE multi-record inventories were attempted first; CEA dashboard returned 502/legacy URL 404 and DOE terms restrict commercial redistribution and technical linking. The direct Eskom 12-site table was examined, then excluded as the canonical basis for new fields after its automated-collection restrictions were found. Alternative primary sources produced the accepted batch: AfDB appraisal/IPR and WSP's technical-advisor portfolio; NamPower's two BESS fact sheets; AXIAN's French financial-close release; Scatec's Egyptian portfolio/releases plus EBRD/EIB/IFC disclosures. These are bounded factual transcriptions, not openly licensed bulk copies. Source documents and binary artifacts are not redistributed in Git.

The 2026 AfDB report documents delays across unfinished packages: no historic forecast is promoted to operation. Pongola/Elandskop operational acceptance (WSP, October 2024) and lender-described commissioning (November 2024) remain separately named milestones. Non-operating ratings from the 2021 procurement table are explicitly scoped as design targets. WSP is the owner's engineer, not automatically EPC or battery OEM. Hex gains operating entity, grid connection and acceptance/engineer metadata without replacing its earlier lifecycle evidence.

Omburu's own fact sheet has 54 MW/54 MWh in the introduction and 51 MW/51 MWh in its technical table. Neither is silently selected: canonical scalar ratings remain null, both observations remain in `conflicts_json`. Chemistry, source-reported coordinates, EPC joint venture, cell supplier and financing are independently useful. Lithops has planned LFP, procurement and funding metadata; its table omits the longitude hemisphere, so no decimal coordinates are fabricated. Kolda is under construction, not operational merely because November 2026 is the target month. Hybrid financing and solar MWp remain separate from battery capacity.

Obelisk's entire battery is in phase 1; the later solar-only phase creates no second battery record. Dandara is phase 1 only (100 MWh), not the full 200 MWh portfolio. Energy Valley remains announced; Shadwan's construction start does not establish construction of Energy Valley. Nefertiti's signed financing does not establish site works. AMEA category navigation labelled “inoperation” is not lifecycle evidence. Abydos I gains project-company, debt-financing and solar AC-basis metadata without claiming COD.

## Equipment workstream and targets

Separate compatible OEM PR #45 adds 19 exact configurations: 13 Sungrow SBR/SBH towers and six Freedom Won SOLVA cabinets. Freedom Won is new, adding regional manufacturer coverage. The selected model tables are exhausted and meet the 10–30-model working objective. The project yield is below 50–200 because no rights-cleared, accessible bulk registry was accepted; no thin rows or fictitious phases were added to fill the gap. No new parser is justified for this curated batch; all writes used the existing upsert and typed validation APIs.

## Dated market ordering and coverage

IEA *Global Energy Review 2026*, battery-storage chapter, published 20 April 2026 and rechecked 1 November, orders **2025 new battery power deployment**: China, United States, Europe (region). This common GW-additions metric is not cumulative operational GWh. A comparable country-only GWh ranking remains unavailable in the inspected sources; no catalogue-count proxy is used. Source: https://www.iea.org/reports/global-energy-review-2026/technology-battery-storage (CC BY 4.0).

All six geographic regions remain represented; this pass deepens Africa after the Australia/Chile and Germany/Netherlands passes. See the fresh completeness manifest, not historical launch totals. The ranked backlog retains India/China coverage needs and the licensed German archive as the highest-yield retry. Next exact equipment batch: Freedom Won COREVA/ENVA; next project partition: licensed MaStR export after a fresh availability/schema check, or CEA after access and rights are resolved.

## Verification and publication

No schema, importer, viewer or package code changed. Historical reports and prior held Chilean/Australian candidates remain unchanged.

Final checks: **1,437 full-suite tests passed, five skipped** for absent optional CDS/orbital imagery integrations. 36 focused tests passed. Ruff lint/format, Python 3.13 ty, catalogue validation, repository hygiene, citation consistency, preservation audit and offline example passed. Typed Zstandard snapshots and current completeness manifest rebuilt outside Git. Strict Sphinx HTML documentation and offline gallery build passed. Browser DOM and package builds were not rerun because no code/schema/viewer changed.

All 16 newly registered project source checksums and both downloaded OEM PDF checksums match retained bytes. Six OEM source entries explicitly have no byte checksum because direct PDF retrieval returned 403. The initial project full-suite run exposed repetitive citation boilerplate pushing the report-size budget over its limit; concise source-register pointers removed irrelevant repeated OEM wording, and the unchanged test passes. No test threshold or application code was changed.

Elapsed active wall-clock effort through validation: **20.9 minutes**, 10:54:24–11:15:18 Atlantic/Canary on 1 November 2026 (UTC+00:00). Publication immediately follows. Finished before 45 minutes because the selected defensible tables and project portfolios were exhausted; equipment target met, project inventory access/reuse gates recorded rather than padded records. Head/main and open-PR path checks found no conflicting advancement before publication; expected-head leases protect both writes. The hourly task remains enabled.
