# 2 November 2026: second French registry partition and remaining Rolls flooded models

## Accepted work

Continue OPEN PR #77 from `a1bdcdabcd31f1ef5964555dff3597bd8adba216`, with
main `f379469be29427b5265d0347cf883d7efdd2957a`. Current instructions,
schemas/dictionaries, source registers, coverage manifests and previous research
ledger were inspected. PR #76 is PV-only; #47–49 are workflow-only by changed
paths. No shared schema/importer changes or PV writes are included.

This iteration adds **85 French battery installations**, enriches **one existing
Bellac project**, and adds **16 exact Rolls models**. No new countries or supplier;
no equipment enrichment. Totals are **1,550 projects / 34 countries / 197 sources**
and **413 equipment records / 39 suppliers / 169 sources** (400 configurations,
13 families). Six-region coverage is retained. Cumulative PR additions are
198 projects, two enriched projects and 32 exact equipment models.

## Evidence and reviewed boundaries

The national ODRÉ register was refreshed before extraction. Its reporting date
remains 31 August 2026, processed 20 October 2026. Etalab Open Licence v2.0 remains
explicit in metadata. All 798 battery-only >=1 MW rows were downloaded in eight
bounded 100-row API pages to screen EIC/commune identity. This pass reviewed offsets
200–399: 85 accepted, **106 new holds**, and **nine previously reviewed entries
skipped**, including RTE sites already covered by the earlier ledger. The previous
107 holds and Atacama/Solar Ray decisions remain unchanged.

Holding reasons overlap: 58 rows share a commune with other named EICs, 36 names
are confidential, and 14 additional candidates have numeric phase/hybrid labels.
The previously reviewed Les Mées hybrid is also skipped. Plouguin's explicit
storage-plus-wind name is held even though the battery classification matches;
phase suffixes II/2/3 are not assumed to represent independent facilities. No
fuzzy merge or automatic phase consolidation was performed. Every accepted EIC
is absent from canonical records and the earlier candidate ledger. Published
registry labels are retained, including spelling anomalies, without inferring
owners from an NWJ/Saft/Entech name.

Fields added: installed MW, stored MWh, dated operating status, charging and grid
connection capacities, network operator, substation, published voltage where
available, region/department/commune and industrial-service/version dates. MW,
stored kWh and annual energy remain distinct. No AC/DC or usable-energy basis,
chemistry, coordinates, commercial COD or equipment assignment is inferred.
All 85 accepted energy values pass the existing anomaly screen. There are no new
field quarantines or permanent whole-record rejections in this batch.

Existing **BEL12S01 / Bellac RINGO** is identified by exact EIC and locality,
with matching 10 MW in RTE's project page. RTE explicitly reports 12 containers,
Saft assembly in Bordeaux, Saft/Schneider industrial partners and coordinated
renewable surplus/congestion management. The record gains container count,
battery manufacturer, applications and qualified historical installation details.
The December 2020 first-battery caption is not COD. Existing 24 MWh, status and
all prior facts remain untouched. Secondary tender mirrors suggest later useful
energy observations; those are discovery leads, not accepted technical evidence.
Web fetch timed out, but an ordinary direct download succeeded and was checksummed.

## Exact equipment

The current OEM index explicitly classifies these 16 remaining flooded models
for renewable energy: 8 CS 17P, 8 CS 25P, 6 CS 27P, 8 CS 27P, S2 L16-EX,
4 KS 21P, S2 L16, S2 L16-HC, 4 KS 25P, S2 L16-SC, 4 KS 27P, 2 KS 33P,
2 OS 33P, 2 YS 27P, 2 YS 31P and 2 YS 62P. The exact page headings, not
calculator combinations, define identity. Space-normalized comparison against
existing names prevents reimporting earlier compact CS designations. All 16
model pages were independently staged with the existing offline parser and
reviewed; each provides nine discharge-rate Ah/current observations.

Retained specifications include 2/4/6/8 V, cell count, plates per cell, charge
voltage/float conditions, published charge currents, self-discharge, standard
terminal/thread, electrolyte reserve, container/cover materials when supplied,
dimensions and qualified sample mass. One-cell units are distinguished from
multi-cell components. The 2 YS 62P page reports two cells at 2 V; both
are preserved without inferring internal topology or per-cell capacity. No MWh is inferred from V×Ah; Ah stays rate-dependent.
Warranty text is an unadjudicated page claim, not warranty_years; manufacturing
variation and test-condition unknowns remain explicit. No project assignments,
cycle counts, efficiency or temperature range were extrapolated.

The marketing page was reread: copyright is retained and direct references to
current specifications are encouraged. This is not treated as an open bulk-use
licence. Only bounded factual observations/evidence metadata are committed; raw
HTML remains outside Git. All 16 remaining stationary flooded model pages are
exhausted; the next OEM partition is exact LFP rack/cabinet configurations.

## Research priorities and reproducibility

The primary IEA 29 May 2026 commentary was reopened. The comparable metric is
2025 annual stationary battery **power additions in GW**, not operational GWh.
Quantified country examples are China >63, US 19, Australia nearly 8, Chile
nearly 1. Europe 6.2 and Middle East >3 are regional comparators. No complete
operational-energy ranking is claimed. The dated markets file records limits.

The existing ODRÉ and Rolls adapters and upsert API were reused. This is a data
and evidence update, with no code/schema changes requiring new parser tests.
All prior records except the explicitly enriched Bellac identity remain byte-for-
byte equivalent as parsed JSON; all prior facts and creation dates are preserved.
New source bytes are SHA256-verified. Parquet snapshots were built twice with
matching hashes, typed columns and Zstandard compression. Canonical JSONL,
coverage manifests, review decisions and ranked continuation backlog are committed;
binary snapshots and source documents remain in ignored artifacts.

Next highest-value partition: refresh ODRÉ offsets 400–599, then adjudicate the
held same-commune/phase groups using independent owner or planning evidence.
The two selected 100-row pages and 16 exact OEM pages are complete. Both planning
yield objectives are met; no claim is made that the whole French inventory is
exhausted. Historical launch reports and source blocks remain intact.

## Validation and elapsed effort

Python 3.13 full suite: **1,647 passed, one optional cdsapi skip**; final focused
catalogue/parser suite: **49 passed**. Both catalogue validators, Ruff lint/format,
ty, repository hygiene, citation exports, both offline usage examples, eight viewer
DOM checks, three package builds, six Twine artifact checks and installed-wheel
public entry-point checks passed. Strict Sphinx build passed; all **405 HTML pages**
passed local link/asset checks. Repeated typed Zstandard Parquet manifests match,
and source-byte checksums and preservation audits passed. An initial Python 3.12
docs attempt lacked the required imagery environment; the documented Python 3.13
environment was installed and the full suite/docs rerun successfully. Remote CI
results are separate from these local checks.

Actual active effort through final publication preparation: approximately
**14 minutes**, 17:52:28–18:06 Atlantic/Canary on 2 November 2026 (UTC+00:00).
Discovery/extraction/reconciliation occupied about eight minutes, validation and
publication preparation about six. Reusing the established reviewed adapters and
upsert API made this shorter than the planning window. The selected 200-row
registry partition and all 16 remaining stationary flooded model pages are fully
reviewed; neither yield target required padding, timestamp churn or additional
unreviewed rows. The wider inventory and research goal remain ongoing. Main and
PR #77 head were unchanged at the final prepublication check; the PR remains open
for review, with no merge requested or performed.
