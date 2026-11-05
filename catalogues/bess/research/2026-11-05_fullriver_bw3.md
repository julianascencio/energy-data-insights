# Fullriver exact models and South African bid identities

Research started 5 November 2026 at 20:55:44 Atlantic/Canary (UTC), the first recorded
execution timestamp. Fresh main `600db672` includes externally merged PR #172.
All nine open PR titles and fully paged changed paths were inspected; no compatible
open BESS PR exists. A new scoped branch is required. Shared references and viewer
files remain with concurrent Wind/PV work; full attribution is in BESS registers.
Read CONTRIBUTING, both schemas/dictionaries, workflow/research prompt, source
registers, current manifests and recent ledgers; historical Australia/Chile identities
and their holds remain untouched. Existing PV upsert and typed snapshot APIs reused.

## Accepted equipment

20 exact Fullriver DC Series battery units from the complete two-table brochure
partition; the same models repeated on PDF pages 2 and 3 are counted once. 18 exact
names occur in the live cards; DC210-12/DC260-12 do not, and similar suffixed models
are not substituted. Fullriver Battery is a new supplier label; no separate entity
table or project component assignments are invented. The OEM explicitly includes
off-grid solar applications and identifies every DC Series model as AGM lead-acid.

Adds explicit V, battery-unit Ah at 5 h / 20 h, reserve minutes at 25/75 A (56 A for 8 V rows),
CA at 32°F and CCA at 0°F, terminal type, group labels, dimensions and mass. Amp-hour
rates remain observations, not cell Ah or derived MWh. Cranking ratings are not
continuous power/current. Starred removable posts change total height by 0.86 inch;
no cosmetic variant is created. Capacity temperature/end voltage, cycles, warranty,
continuous power, usable energy and counts remain unknown. Live charging guidance
is qualified up to 35% of C20 Ah, with no calculated per-model amperes.

The raster table cannot be recovered from pdftotext. Both PDF pages were visually
read and a factual transcription is committed. The tested offline HTML-card parser
reproduces the 18 live comparisons without fuzzy matching or unit coercion.
PDF p2/p3 disagree on DC150-12 capacity/reserve values and DC85-12 height. Web/PDF
physical values differ on additional models: 16 accepted models carry field conflicts.
Affected normalized mass/height is unset; all native observations and locators are
retained. Undated sources are not ordered by upload path or retrieval date.

## Accepted projects and held alternatives

The national procurement inventory was attempted before isolated announcements.
All 33 submissions in DEE's 28 November 2024 BW3 list were screened. Five exact
name/substation/contracted-MW matches enrich Erfdeel, Vanilla, Haru, Retreat and
Bloemhoek with bid IDs, tender ID and project-company observations. Existing
preferred-bidder evidence, ratings, ownership, forecasts, conflicts and current
status dates are preserved. A project-company label is not an owner/EPC assignment.

All 28 entries in the separate Part C unsuccessful-bidder table match the other
bid IDs. They remain candidate holds: competing proposals at shared substations
are not automatically distinct physical assets, and unsuccessful procurement does
not prove cancellation. Fennel and Oasis Theseus have differing substation labels
between the two tables; Acamas has a spelling discrepancy. No value was silently
repaired, no company identifier conflict in Bloemhoek was resolved by the bid ID.

## Source decisions, counts and next work

Fullriver footer/privacy/ordering terms and DEE index/footer were inspected.
Neither is labelled openly licensed for bulk reuse. Only bounded factual
observations are committed, with original-byte checksums, retrieval UTC, exact
model/row locators and version uncertainty; no copyrighted documents/artwork.
HOPPECKE was held because its explicit terms require consent for electronic
processing. Six Fullriver PowerVault packs are excluded from this stationary batch:
the source identifies Class III material-handling applications. No controls bypassed,
people contacted, registration submitted, purchases made or held sources retried.

Accepted: 20 new models, 0 model enrichments ; 0 new projects, 5 project enrichments.
Canonical whole-record quarantines/rejections: 0. Candidate decisions: 28 project holds,
6 mobility-only equipment exclusions; HOPPECKE source-level rights hold (estimated 13
models, not 13 accepted/rejected records). 16 accepted models have field-level holds.
No new country; one supplier. Totals: 2,149 projects / 48 countries / 410 sources;
1,192 equipment records / 56 supplier labels / 486 sources, comprising 1,179 configurations and
13 families. All six regions retained. No new OEM table required by this repository.

IEA commentary was freshly checked: selected-country 2025 utility-scale POWER
additions rank China ~55 GW, US >16 GW, Australia ~4.2 GW. Europe is a region, excluded
from country ordering. Comparable operational stationary GWh ranking remains
unavailable; no power-to-energy conversion or complete global ordering claimed.

The selected 20-model table and 33-row procurement review are complete. Project
yield is below the 50–200 planning range because 28 competing submissions lack
reconciled physical identities; equipment meets the 10–30 planning range. The live
page's 34 additional headings need exact-sheet review. Next priorities are resolving
16 model field conflicts, then those 34 models, and newer project-specific commercial
close/grid evidence. Prior source rights/access backoffs are linked in the backlog.
Broader research remains ongoing; no idle time is added to satisfy a duration.

Sibling audit/review/captures/backlog/markets/coverage/manifests preserve decisions.
Checks and actual elapsed effort are appended before publication; final-head CI and
publication completion time are recorded in the PR description. Binary snapshots
remain outside Git and use the existing CI artifact/build mechanism.

## Validation and elapsed checkpoint

At 2026-11-05 21:13:05 Atlantic/Canary (UTC), 17.4 actual elapsed minutes
covered discovery, terms review, visual extraction, reconciliation, implementation
and local validation. Selected source partitions are complete; broader research
continues through the ranked backlog. Publication/final-head CI completion and total
elapsed time will be recorded in the PR description without timestamp-only commits.

Passed: both catalogue validators and source-reference checks; 510 focused BESS
tests; exact offline CLI replay of 18 models / 36 unit panels; 25 Node viewer tests;
Ruff lint and format; repository-wide ty; repository hygiene/citation checks; offline
OEM example; strict Sphinx with gallery execution disabled; and the subsequent
692-page internal-link/asset check. An initial new-parser typing diagnostic was
fixed with a TypedDict before the successful type recheck.

Two independent typed Zstandard builds per catalogue are byte-identical, read back
with expected row counts and ZSTD compression, and preserve no-op upsert timestamps.
All 1,172 prior equipment records are unchanged; all old project fields, nested
observations, registry IDs, citations and creation times are preserved. Exactly five
projects receive additive observations; 2,144 old projects are unchanged. The full
local Python suite is running at this checkpoint; no pass is claimed until its
result is recorded in the PR. Final-head CI will also exercise package builds.

Reproduce the source-card comparison with `PYTHONPATH=data-retrieval/src python
scripts/stage_bess_fullriver.py LOCAL_HTML --models EXACT_MODEL_NAMES --output
NEW_JSON`. Accepted PDF facts are in the sibling transcription ledger and records.
Tests: `pytest -q data-retrieval/tests/test_bess*.py`; `ruff check .`;
`ruff format --check .`; `ty check`; `node --test tests/js/test_database_viewer.mjs`;
`python -m sphinx -W --keep-going -D plot_gallery=0 -b html docs OUTPUT`;
`python scripts/check_docs_links.py OUTPUT`. No binary snapshot is committed.
