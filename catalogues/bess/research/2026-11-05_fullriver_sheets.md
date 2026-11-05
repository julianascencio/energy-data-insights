# Fullriver individual datasheets and project-source review

Started 5 November 2026 at 21:49:36 Atlantic/Canary (UTC). PR #180 was externally
merged at 21:48:58; this isolated checkout starts from main eb03f8f4. All seven
open PR titles and fully paged changed paths were inspected. No open BESS PR or
BESS overlap exists. Shared references/viewer remain with concurrent Wind/PV work.
Repository instructions, schemas, dictionaries, current source registers, prior
coverage/review logs and the historical Australia/Chile holds were reviewed.

## Accepted batch

20 existing Fullriver identities reviewed against the freshly downloaded OEM index.
18 exact linked PDFs were retrieved and checksummed. 17 have text electrical tables;
DC105-12 page 1 is raster and was visually transcribed separately. Representative
DC224-6 and DC150-12 tables/footnotes were visually checked. All 18 enrich existing
records; no new models, suppliers, projects or countries. DC210-12 and DC260-12 are
held because the current index has no exact links; no suffix substitution.

Each accepted model gains 100/20/10/5-hour battery-unit Ah observations, internal
resistance in milliohms and explicit 100% SoC, 25°C, 1.75 V per-cell endpoint
conditions. These conditions apply to the individual-sheet observations only,
not retroactively to the old brochure. No cell capacity, stored MWh, duration,
continuous power or resistance-to-current derivation. OEM ratings are estimates
and designs may change. No graph digitisation or warranty assertion.

DC150-12 remains conflicted: its sheet reports 135 Ah at 20 h and 117 Ah at 5 h,
versus brochure page 2's 150/130 Ah. Both observations are retained with source IDs;
no preferred undated revision selected. The 16 earlier model conflicts remain.
No whole-record quarantine/rejection; two absent-sheet candidates held.

Existing upsert API used; additive nested-JSON collisions manually reconciled with
all old scalar/nested data and creation times preserved. No-op replay is stable.
The new parser rejects changed identities, duplicate rows, missing conditions and
wrong capacity/resistance units. Six synthetic tests cover these boundaries.

## Project stream and access

Attempted Eskom's official 2025 annual-report portfolio before isolated news.
The primary reader rejected its 12.2 MB size; no restricted original download was
retried. WSP's alternate eight-site portfolio offers useful acceptance/role evidence,
but its explicit terms restrict republication; zero project facts were imported.
This is a source-level hold, not eight accepted or rejected projects. Previous
KPLC/CEA/TPL/Microcare and rights backoffs remain in the linked backlog.

Fullriver's index/footer and privacy were freshly reviewed. Ordering-policy refresh
failed; the earlier same-day review remains explicitly historical. Bounded factual
specifications only; no open bulk licence, full documents or artwork redistributed.
Original source bytes are outside Git. No contact, payment, registration or bypass.

IEA's dated 29 May 2026 commentary was freshly checked. The selected-country metric
remains 2025 utility-scale battery power additions: China approximately 55 GW,
US over 16 GW, Australia approximately 4.2 GW. Not an exhaustive global ranking;
Europe is a region and comparable operational stationary GWh remain unavailable.

## Counts, validation and next partition

18 existing models enriched; zero new/enriched projects; zero new models/OEMs.
Totals: 2,149 projects / 48 countries / 410 sources; 1,192 equipment records /
56 supplier labels / 504 sources (1,179 configurations, 13 families). All six
regions retained. Project yield is below the planning range because both selected
portfolio sources were blocked; equipment enrichment meets the model planning range.
The selected electrical-table partition is exhausted. Next: individual-sheet
operating/charging tables, exact missing sheets, then 34 other live model headings.

Passed: 516 focused tests, both catalogue validators, field references, preserved
creation times/scalars, no-op upsert, two byte-identical typed Zstandard snapshots
per catalogue and readback; Ruff format/lint and repository-wide ty. Viewer,
offline example, hygiene/citations and strict documentation checks are run before
publication; final-head wider CI results and completion time are recorded in the PR.
No raw documents or binary snapshots committed; existing package/artifact workflow.

Replay: use `pdftotext -layout` on permitted original bytes, then
`parse_datasheet(text, model=exact_model)` from
`energy_data_retrieval.bess_oem_catalogue.fullriver`. DC105-12 remains explicitly
manual in the review ledger. Tests: `pytest -q data-retrieval/tests/test_bess*.py`.

Pre-publication checkpoint 2026-11-05T21:55:32.531178+00:00: 5.9 actual elapsed minutes. Final publication/CI effort will be recorded in the PR; no idle time added.
