# Global PV equipment and project database

Five evidence-backed tables cover modules, inverters, trackers, combiner boxes and
projects. Each row has a stable ID, standardized metadata, source references,
creation/update/verification times and an extension field. This is a growing
research catalogue: the launch includes 21,605 modules, 2,344 inverters, 5 trackers,
3 combiners and 7,320 projects across 11 countries. Most projects come from the
United States EIA-860 inventory; global project coverage is still highly uneven.

[Catalogue guide and update contract](../catalogues/pv/README.md),
[data dictionary](../catalogues/pv/DATA_DICTIONARY.md),
[expanded research prompt](../catalogues/pv/RESEARCH_PROMPT.md), and
[launch research evidence](../catalogues/pv/research/launch_report.md).

## Interactive viewer and runnable statistics

Open the [interactive database viewer](https://julianascencio.github.io/energy-data-insights/database-viewer.html)
or the [Database gallery](https://julianascencio.github.io/energy-data-insights/auto_examples/database/index.html).
Search and filter every published row, select columns, sort, inspect evidence,
compare groups and export filtered CSVs. The viewer is regenerated from the exact
published Parquet files on each documentation build. Browser JSON projections
are derived assets; Parquet and canonical JSONL remain the data formats of record.

Runnable offline examples cover table counts and sizes, all-column completeness,
country coverage, equipment queries and separate AC/DC capacity summaries. The
reusable `energy_analysis.pv_database` functions work on local Parquet snapshots.
Unknown values remain null; reported partial sums are not total installed capacity.

## Download and storage choice

The successful main documentation build publishes Parquet datasets:
[modules](https://julianascencio.github.io/energy-data-insights/datasets/pv/modules.parquet),
[inverters](https://julianascencio.github.io/energy-data-insights/datasets/pv/inverters.parquet),
[trackers](https://julianascencio.github.io/energy-data-insights/datasets/pv/trackers.parquet),
[combiner boxes](https://julianascencio.github.io/energy-data-insights/datasets/pv/combiner_boxes.parquet),
[projects](https://julianascencio.github.io/energy-data-insights/datasets/pv/projects.parquet),
[manifest](https://julianascencio.github.io/energy-data-insights/datasets/pv/manifest.json),
[source registry](https://julianascencio.github.io/energy-data-insights/datasets/pv/sources.json), and
[SAM notice](https://julianascencio.github.io/energy-data-insights/datasets/pv/licenses/SAM-BSD-3-Clause.txt).

**Parquet + Zstandard** provides typed nullable columns, compression and efficient
column reads. `sources` and `source_urls` remain native lists, and timestamps are
UTC Arrow timestamps. Nested variable metadata is canonical JSON in designated
columns, keeping the wide row stable as new source fields appear. Git stores
reviewable JSONL; every binary snapshot is reproducible from it. CSV and Excel are
poor canonical choices for heterogeneous nested sources and reliable nullable types.

```bash
uv run python -m energy_data_retrieval.pv_catalogue validate
uv run python -m energy_data_retrieval.pv_catalogue build --output artifacts/pv-v1
```

```python
import pandas as pd

modules = pd.read_parquet(
    "artifacts/pv-v1/modules.parquet",
    columns=["record_id", "manufacturer", "model", "pmax_stc_w", "bifacial", "source_urls"],
)
print(modules.loc[modules["bifacial"].eq(True) & modules["pmax_stc_w"].ge(600)].head())

projects = pd.read_parquet("artifacts/pv-v1/projects.parquet")
print(
    projects.loc[
        projects["country_code"].eq("CHL"), ["name", "capacity_dc_mw", "capacity_ac_mw", "sources"]
    ]
)
```

For optional SQL analysis, DuckDB can query those Parquet files directly without a
server. It is not a required dependency. Always distinguish country coverage and
OEM coverage from current market availability, and keep capacity bases separate.

## Launch research and known limits

The SAM/CEC module library was pinned by Git revision and SHA-256, not read from an
unversioned moving URL. Its June 2026 module data contains 36 repeated model names
with conflicting parameters: all 72 raw rows are quarantined. Case-sensitive OEM
suffixes remain distinct and are candidates for further review, not auto-merging.

EIA report-year 2025 provides 7,309 operating PV plant IDs. The adapter joins plant
metadata to OP/PV generator records, keeps generator attributes in `phases_json`,
and sums nameplate AC and net DC separately. Missing unit capacities produce a
null total. Plant dates and angles are not guessed from the first generator.
Non-PV equipment at a mixed facility does not enter PV totals. Topaz is explicitly
reconciled with its OEM/owner-sourced project row, leaving 7,320 unique projects
including 11 additional projects outside the USA.

The Topaz owner describes 550 MW without an AC/DC basis, while the EIA generators
sum to 585.9 MWac. Both are retained with their source and a review flag; they are
not silently equated. Historical source dates are retained. `last_verified_at`
means source access, not confirmation of live operation or current certification.

OEM tracker/combiner specifications are sparse where configuration-specific
technical sheets are gated. No contact forms were submitted. Coordinates outside
the EIA sample are left null where no sufficiently supported location was found.
GEM, WRI, CEN, ANEEL and UK REPD were reviewed as expansion candidates; they are
not claimed as imported datasets here. Their filtering, licensing, chronology and
project/phase distinctions need dedicated handling.

## Updating and extending

The [research specification](../catalogues/pv/RESEARCH_PROMPT.md) defines the regional
rotation, source hierarchy, provenance, null handling and conflict process. New
research accumulates on an open `[PV database]` PR; after that PR closes or merges,
the next substantive batch starts a new one. Recurring PRs remain open for review.
Scheduling is supplied by the user's automation, not an unauthenticated GitHub cron.

New metadata should reuse one of the 148 canonical columns. Use a namespaced
extension for unclassified metadata, then promote it through a versioned schema
change when a stable definition is established. Code, schema and records are
validated in CI; Pages exports the validated Parquet snapshot after merge.

### Bounded ODRE batches

The offline ODRE staging ledger supports an inclusive `minimum_kw` and exclusive
`maximum_kw`. Omitting both retains the original >=10 MW scope. The minimum must
be at least 1000 kW; invalid or reversed bounds fail closed. The complete national
individual-PV identity export is still mandatory, including names below the selected
capacity band. Neither capacity selection nor a reviewed ID overrides aggregate,
phase, privacy, existing-identity or shared-commune holds. See the reviewed
`catalogues/pv/research/20261102T0000_odre_review.json` 5–10 MW batch.
