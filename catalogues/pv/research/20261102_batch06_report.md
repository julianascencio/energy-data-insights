# GEM publication batch 06 — 2 November 2026

Adds 3,552 previously reviewed project/location records from UUID prefixes 50–5f.
This is recovery publication, not newly discovered projects or independent site validation.

## Reconciliation and source

Main baseline is 65931a16f949d3e5db1c014d8330914a971f3d80, including merged PR #59
(batches 04–05) and BESS PR #60. The open PR list was checked before preparation;
only three dependency-update PRs were open. No overlapping research branch was open.
The provider repository's latest commit affecting the February 2026 workbook remains
06587e9b6c4e332e646347f6e62af54b10df5ef3. Reused the locally cached original workbook;
the parser verified its complete SHA-256 against the immutable source registry before
reading all 103,940 phases. No fresh download or newer global-release search is claimed.

The unchanged replay pipeline reran technology, restricted-lineage, identity/name,
proximity and US/EIA gates. The complete 56,605 accepted-ID digest matched; every
partition's counts and country distribution were validated before batch selection.
All 3,552 selected IDs were absent from main. The existing upsert API returned zero
conflicts; every one of the 50,232 baseline PV catalogue records remains identical.

## Coverage and boundaries

Branch coverage: **29,724 projects across 167 countries/territories**. Adds American
Samoa, Cabo Verde, Liberia, Solomon Islands, Vanuatu and Yemen to main's coverage.
The selected batch spans 95 country/territory codes. China contributes 831 records,
Japan 653, Germany 502, Brazil 199, Spain 76, Italy 68, India 18, Australia 16 and
Pakistan three; no US additions. Exact distributions are in the dated summary.

Equipment is unchanged: 21,605 modules, 2,403 inverters, 15 trackers, 37 combiners.
No existing enrichment, new equipment, manufacturer, quarantine or rejection this
iteration. Historical 37,886 held GEM locations remain excluded. No source/scientific
method/schema changes. Existing source attribution and original evidence are preserved.
Dated phase status is not proof of present operation; capacities retain source ratings
without inferred AC/DC conversions. No original workbook or generated binary committed.

## Validation

1,577 tests passed; one optional cdsapi skip. Ruff, formatting (538 files), ty,
repository hygiene, citations and whitespace checks passed. Five typed Zstandard
Parquet tables rebuilt outside Git: 53,784 records in total, with all row counts,
SHA-256 and per-column compression verified. A separate Git-baseline comparison
verified exactly 3,552 additions and no edits/removals to pre-existing records.
Strict Sphinx/gallery build passed; all local links and assets resolve across 393 HTML pages.
Remote CI is separate and not claimed passed here.

## Next partition

Batch 07 (60–6f), 3,598 reviewed records. Recheck main and every open PR before
publishing; do not duplicate batch 06. Batches 07–16 are not included in this PR.
Leave this publication PR open for review; do not auto-merge.
