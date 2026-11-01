# Sungrow and Freedom Won specification pass — 1 November 2026

**19 new exact configurations; zero existing records changed.** Current snapshot: **109 records, 29 supplier brands, 61 sources**, comprising 96 configurations and 13 families. Freedom Won is new. The separate project PR #44 adds 13 projects and enriches two, including new countries Namibia and Senegal. Both PRs remain open; this is not merged/live viewer content.

## Evidence and configuration boundaries

Sungrow: six SBR models (096/128/160/192/224/256), Spanish datasheet version 13, and seven SBH models (100/150/200/250/300/350/400), Spanish version 3.1. All columns transcribed; both page-2 tables visually checked against text. Preserve usable DC energy, explicitly rated DC power, voltage range, module count, continuous current, mass, dimensions, natural convection, IP55, altitude and separate charging/discharging temperatures. The energy footnotes specify 25°C, 100% DOD and 0.2C. No current-times-voltage power calculation, duration inference, extra language variants or SBH-V12 extrapolation.

Freedom Won: exact SOLVA DC208, AC261, DC261, RT261, AC418 and DC418, all dated 17 September 2026. Useful fields include nominal DC energy, LFP/cell Ah, module topology, voltage ranges, thermal auxiliary/cooling/heating specifications, dimensions with tolerance, mass, fire suppression, interfaces, altitude derating and PCS output where explicitly provided. RT261 has a rectifier input rating, not an assumed bidirectional PCS. DC busbar connection ratings are not promoted to battery continuous output. Unqualified efficiency and >=8000-cycle claims remain extensions with missing test conditions; warranty headline is not a verified contract. No project/equipment assignment or cell OEM inferred.

Two downloaded Sungrow PDFs have SHA-256 hashes. Six direct Freedom Won PDF requests returned 403; readable public search-service PDF text supported transcription, but no original bytes/checksum is claimed. No bypass or retries against the restriction. Copyright documents are not committed. Fields map individually to exact sources, revisions and page locators.

## Candidate accounting and backlog

21 equipment candidate reviews: 19 accepted, two held, zero definitive rejections. Pylontech US5000's old indexed table could not be reconciled to the current app-shell page/revision. Freedom Won EMS has predefined packages and a component role that the present systems-only schema does not cleanly model; no fictitious package combinations or standalone EMS entity inserted. Earlier five Dyness Tower holds remain unchanged.

This meets the 10–30-model working objective. Selected tables exhausted; next useful batch is Freedom Won COREVA 5 and ENVA 5/16/60HV, then the latest applicable SBR064/SBH-V12 documents. The shared ranked backlog records URLs, revisions, rights/access limits, processed models and retry conditions. Project discovery attempted national inventories and alternative owner/lender portfolios; details in PR #44.

## Verification and publication

Typed Zstandard Parquet and completeness manifest rebuilt through the package. No binary snapshot committed. Natural identities checked against all 90 baseline records and within the 19-row batch. Existing upsert API used; zero timestamp-only changes or schema/code changes. 

Final checks: **1,445 full-suite tests passed, five skipped** for absent optional CDS/orbital imagery integrations. 14 focused tests passed. Ruff lint/format, Python 3.13 ty, catalogue validation, repository hygiene, citation consistency, preservation audit and offline example passed. Typed Zstandard snapshots and current completeness manifest rebuilt outside Git. Strict Sphinx HTML documentation and offline gallery build passed. Browser DOM and package builds were not rerun because no code/schema/viewer changed.

All 16 newly registered project source checksums and both downloaded OEM PDF checksums match retained bytes. Six OEM source entries explicitly have no byte checksum because direct PDF retrieval returned 403. The initial project full-suite run exposed repetitive citation boilerplate pushing the report-size budget over its limit; concise source-register pointers removed irrelevant repeated OEM wording, and the unchanged test passes. No test threshold or application code was changed.

Elapsed active wall-clock effort through validation: **20.9 minutes**, 10:54:24–11:15:18 Atlantic/Canary on 1 November 2026 (UTC+00:00). Publication immediately follows. Finished before 45 minutes because the selected defensible tables and project portfolios were exhausted; equipment target met, project inventory access/reuse gates recorded rather than padded records. Head/main and open-PR path checks found no conflicting advancement before publication; expected-head leases protect both writes. The hourly task remains enabled.
