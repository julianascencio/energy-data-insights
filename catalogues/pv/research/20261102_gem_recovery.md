# GEM global PV recovery, 2 November 2026

Recovered the validated reconstruction from the interrupted working files.
This is a reproducible reconstruction from the original GEM February 2026
provider workbook, reconciled with main `ecedd9dde26a9f09940b94b5a722e40108387cd4`.
It is not the exact earlier 57,534-project/CEC enrichment patch.

## Results

56,605 new project/location records, 8,297 pre-existing projects retained unchanged.
Prepared union: **64,902 projects across 198 countries/territories**, and 88,958
records across the five PV tables. Equipment counts and existing metadata are unchanged.
The historical 659-module/19,429-enrichment work and additional Australian source
imports are not claimed recovered by these project PRs.

103,940 source phase rows are grouped into 94,491 GEM locations. 37,886 locations
are held, with overlapping reason counts in `20261102_gem_review.json`. Only explicit
PV is admitted; no national distributed-solar aggregates. All native phase evidence
is retained. Entire locations containing TZ or WKSL identifiers are withheld.
US locations are held for EIA crosswalks. Existing names/aliases and coordinates
within 2 km are screened without automatically merging or overwriting any record.
Repeated normalized names across GEM locations are held. These screens are deliberately
conservative, not proof of exhaustive global deduplication. Anonymous source names
and historical source errors remain possible; GEM naming is not independently surveyed.

Mixed status, capacity rating and incomplete phase capacities produce no scalar
capacity total. Start-year forecasts do not become actual commissioning dates.
Operating status is a dated GEM statement. Coordinates retain the source precision;
missing/conflicting group coordinates remain null. Country mappings are explicit,
including user-assigned XKX for Kosovo. Phase source IDs, ownership, capacity units,
research dates and native status are retained in `phases_json`.

## Independent PR batches

The immutable UUID prefix divides canonical project shards without overlap. Shared
importer/source/attribution changes are identical in all 16 PRs so each is valid
on its own. Merging identical common changes should not duplicate records. Each PR
preserves all baseline records in the shards it modifies. Other ongoing research
may still touch these shards and require reconciliation before merge.

| Batch | Prefixes | Added projects |
|---|---|---:|
| 1 | 00–0f | 3,542 |
| 2 | 10–1f | 3,597 |
| 3 | 20–2f | 3,582 |
| 4 | 30–3f | 3,666 |
| 5 | 40–4f | 3,488 |
| 6 | 50–5f | 3,552 |
| 7 | 60–6f | 3,598 |
| 8 | 70–7f | 3,551 |
| 9 | 80–8f | 3,550 |
| 10 | 90–9f | 3,424 |
| 11 | a0–af | 3,561 |
| 12 | b0–bf | 3,483 |
| 13 | c0–cf | 3,439 |
| 14 | d0–df | 3,551 |
| 15 | e0–ef | 3,546 |
| 16 | f0–ff | 3,475 |

These are prepared snapshot counts. The live site updates only after the respective
PRs merge and the main documentation workflow succeeds.

## Validation

- 1,546 Python tests passed; five optional-dependency tests skipped in the initial run.
- 16 new synthetic boundary tests cover phase grouping, restricted lineage, explicit
  PV, US crosswalks, mixed capacity/status, duplicate IDs, overlap holds and source hashes.
- All 56,605 incoming records reproduced exactly from the pinned original workbook.
- Every pre-existing record preserved byte-for-byte as parsed canonical data.
- All 88,958 canonical records validated, including field provenance.
- Five typed Zstandard Parquet tables rebuilt outside Git; projects count 64,902.
- Ruff, format, ty, repository hygiene and citation checks passed.
- Viewer logic and strict documentation checks are recorded in the PR validation section.

Replay with `scripts/stage_pv_gem.py` and the committed review ledger. The source is
pinned to provider commit `06587e9b6c4e332e646347f6e62af54b10df5ef3`, SHA-256
`99f44fd162faff436cbc7c1edf7a8a486c4e32746a9786778362ca4688d39959`.
The accepted-ID digest prevents silent changes when existing identities advance.
No original workbook or generated binary is committed.
