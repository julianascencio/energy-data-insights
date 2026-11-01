# Spain regulatory and GoodWe specification pass — 1 November 2026

Three new project identities and 12 exact equipment configurations accepted across separate open PRs #44 and #45. No existing record changed; zero substantive enrichments. No new country; GoodWe is a new supplier. Project snapshot: 1,266 records / 30 countries / 85 sources. Equipment snapshot: 121 records / 30 suppliers / 63 sources (108 configurations, 13 families). These are PR-head snapshots, not merged content or live deployments.

## Projects and reconciliation

Started with the owner portfolio, reviewing 13 named battery identities before isolated releases. Iberdrola España reuse terms restrict redistribution: its facts were not imported. Independent BOE authorisations were the accepted alternative. Three records capture historical authorised designs for Romeral, Olmedilla and Andévalo, with legal entities, source decision/publication dates, lithium-ion chemistry (no inferred LFP), battery-only energy, container counts, solar association, connection voltage, substation and separately scoped site access limits. No individual landowners or cadastral tables are copied.

All three accepted records are needs_review. Scalar current power remains null. Romeral/Olmedilla authorisations distinguish nominal 27.46 MW and installed inverter 30.576 MW; October wind-hybrid notices cite 28.78 MW battery ratings. These do not create new battery phases. Implausible 288 MWh per-rack text is quarantined rather than silently corrected. Andévalo's historical permit power remains an explicitly dated observation in extensions, pending as-built reconciliation. Status is a dated permit observation, not a claim that a subsequent operation announcement is false. Container counts and stored energy likewise describe the permit design. Grid access limits are not battery nameplate ratings. Eiffage's alternative portfolio was inspected and adds a further 60-versus-58-MW reconciliation question for Campo Arañuelo; no unreviewed EPC fields imported.

13 project candidates: three accepted, ten held (including an existing Arañuelo III enrichment), zero rejected. The held list and next independent-source actions are in the review ledger/backlog. This bounded permit batch is below the 50–200 project planning objective because owner reuse restrictions and rating/lifecycle conflicts prevented defensible bulk acceptance. Do not ingest a wind-hybrid notice as an additional battery or classify pumped storage as BESS.

## Equipment and quality

Two complete GoodWe OEM tables: four original Lynx Home F models (2023-01-05 EN V2.1), eight Lynx F G2 models (2025-01-24 EN V2.1). Original downloaded bytes retained outside Git and SHA-256 recorded; both page-2 tables visually checked. All 109 baseline records and natural identities reviewed; no GoodWe model existed. Twelve within-batch identities unique; existing upsert/validation APIs used, no schema/parser changes.

Preserve usable DC energy with BOL, 100% DOD, 0.2C and 25 +/-2°C conditions; explicitly reported nominal DC power; voltage bounds, nominal current, module model/count, dimensions/mass, IP55, altitude, separate charge/discharge temperatures and manufacturer-listed standards. G2's smallest tower cannot start ET 15–30kW inverters; this exception is explicit. No inferred voltage-times-current power, duration, cell supplier, warranty, active sales status or independently verified certification. Unversioned website IP claims are not mixed into the dated configuration. Four Freedom Won COREVA/ENVA candidates were reviewed and deferred for revision/current-boundary checks, not counted as accepted additions. The 12-model batch meets the equipment planning objective and exhausts both selected model tables.

## Market ordering, coverage and next action

Rechecked IEA Global Energy Review 2026 battery chapter on 1 November: 2025 new battery power deployment ranks China, United States, Europe (region). This is GW additions, not cumulative operational GWh or a country-only ranking. Comparable operational-GWh ordering remains unverified. Source: https://www.iea.org/reports/global-energy-review-2026/technology-battery-storage (CC BY 4.0). All six regions remain covered by the existing catalogue; this pass deepens Spain and adds an Asian OEM following Africa/Oceania/Latin America passes.

Next scalable project partition: BOE battery-specific amendments/exploitation permits, then fresh availability check of licensed MaStR. Next equipment batch: printed-revision COREVA/ENVA documents, preserving in-progress certification and peak/continuous distinctions. Earlier held Chile phases and Omburu ratings remain untouched. Source URLs, dates, terms, offered fields, cursors, retry conditions and priority are in the persistent backlog.

## Attribution

Basado en datos de la [Agencia Estatal Boletín Oficial del Estado](https://www.boe.es). This is an adapted factual extraction, not an official publication or BOE-endorsed product. Terms: https://www.boe.es/informacion/aviso_legal/ (effective 28 June 2024). Original dates and technical scope remain in source metadata. GoodWe PDFs remain copyrighted and are not redistributed; factual model observations have individual field evidence.

## Validation

1,445 full-suite tests passed, five optional-dependency skips; 14 focused tests passed. Catalogue validation, source-byte hashes, duplicate/preservation audit, Ruff lint/format, ty, repository hygiene, citation consistency, offline example, typed Zstandard snapshots and strict Sphinx/gallery build passed. Local documentation links checked. No package builds or browser DOM rerun: no production code/schema/viewer changes. Project branch changes one report test to bound the report UI separately from its growing complete bibliography; keeps the 150,000-character UI bound and verifies the bibliography delimiters/content. Full suite rerun passed after normalizing bibliography IDs.

Actual elapsed effort through validation: 9.8 minutes (11:46:29–11:56:17 Atlantic/Canary, 1 November 2026; UTC+00:00). Publication follows. Finished early because the two defensible OEM model tables and the selected permit/notice batch were exhausted; project ratings and reuse gates remain explicit. No waiting to fill the requested window. Current main and both BESS heads rechecked before leased publication; concurrent PV paths do not overlap this iteration's test/data edits.
