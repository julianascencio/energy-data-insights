# Worldwide BESS projects

The first BESS section contains **37 named battery energy storage projects across
22 countries**, supported by **30 primary sources**. This is a curated starting
catalogue, not an exhaustive global inventory. It includes electrochemical
batteries (including vanadium flow), not pumped hydro, compressed air or thermal
storage. BESS equipment catalogues can follow in a later schema version.

## Storage and usage

- Reviewable UTF-8 JSONL under `records/projects/<country>.jsonl` is canonical.
- `sources.json` registers the publisher, URL, retrieval date, publication date
  where known, access method, evidence notes and source-license qualification.
- The packaged [schema](../../data-retrieval/src/energy_data_retrieval/bess_catalogue/schema.json)
  defines 60 typed, nullable columns. Extra metadata goes in `extensions_json`.
- Parquet with Zstandard is rebuilt offline; list fields remain lists, numeric
  fields retain their units, timestamps are UTC and all-null fields stay typed.
- `manifest.json` fingerprints the canonical rows, schema and sources and records
  the output file hash, countries, row count and completeness of each field.
- Browser JSON is a derived projection of the exact Parquet file; the viewer
  verifies its checksum. Neither browser JSON nor CSV is a second source of truth.

```bash
uv sync --locked --all-packages --group docs
uv run python -m energy_data_retrieval.bess_catalogue validate
uv run python -m energy_data_retrieval.bess_catalogue build --output artifacts/bess-v1
uv run python examples/database/plot_bess_projects.py
```

```python
import pandas as pd

bess = pd.read_parquet("artifacts/bess-v1/projects.parquet")
print(
    bess.loc[
        bess.country_code.eq("CHL"),
        [
            "name",
            "power_capacity_mw",
            "energy_capacity_mwh",
            "status",
            "status_as_of",
            "quality_status",
            "conflicts_json",
            "source_urls",
        ],
    ]
)
```

The [BESS viewer](https://julianascencio.github.io/energy-data-insights/bess-database-viewer.html)
and [database gallery](https://julianascencio.github.io/energy-data-insights/auto_examples/database/index.html)
are rebuilt after a successful main documentation deployment. Browse filters,
all metadata, source links and dates; export filtered CSV, record JSON or Parquet.

## Meaning of a row

One row represents a named project with an explicit `capacity_scope`. Separate
named facilities have separate IDs. A multistage project can retain phases in
`phases_json`; its total must not appear alongside overlapping phase rows.
Collie includes Stages 1 and 2 once. The original and Two Yllikkälä facilities
are separate named installations. Four Lithuanian parks are four rows, without
an additional fleet-total row. Hazelwood reports the operating first stage's
capacity and records the unfinished extension in phase metadata.

`power_capacity_mw` is battery power; `energy_capacity_mwh` is stored energy.
`grid_connection_capacity_mw` is a different field. Neither PV MW nor grid
connection MW may fill missing battery power. `power_basis` and `energy_basis`
are explicit, often `unspecified`. Reported discharge hours are not synthesized
from an E/P ratio. The catalogue is not a simulation parameter library: usable
energy, efficiency, degradation and dispatch limits need additional evidence.

## Dates, evidence and conflicts

`created_at` records first insertion; `updated_at` records substantive edits;
`last_verified_at` means access to source evidence, not live operation. The
source's `access_method` distinguishes an opened page from an indexed excerpt.
`status_as_of` and `status_date_basis` distinguish dated announcements from
access to undated pages. An inauguration or publication date is not automatically
COD. Planned dates do not promote a project to operational.

Every populated factual field has explicit source IDs in `field_sources_json`.
Country codes and status labels are normalized from source descriptions; capacity
scope and unspecified rating bases are editorial interpretations of that evidence.
The initial records are AI-assisted transcriptions of primary-source facts and
need ongoing review. Numeric precision does not imply independent verification.

Conflicts are retained in `conflicts_json` with both source observations and a
`needs_review` flag. This batch preserves conflicting Coya/Tamaya power ratings
and Jurong Island energy ratings. It does not select a universal engineering
rating from a marketing announcement. See [research notes](research/launch_report.md).

## Contribution contract

1. Prefer regulator/system-operator registries, owner pages and OEM/EPC releases.
   Reuse an existing source registration when appropriate; record access method.
2. Reconcile name, locality, aliases, external IDs and phase scope before adding a
   row. Stable IDs use original country/locality/name, never mutable capacities.
3. Fill only supported fields. Unknown is null, never zero, an assumed chemistry,
   a guessed manufacturer, a city-centroid coordinate or an inferred COD.
4. Retain creation time. Change update time only for substantive edits; refresh
   verification time after checking evidence. Retain previous observations in Git
   and unresolved discrepancies in `conflicts_json`.
5. Edit records on an isolated branch. Validate, rebuild and run relevant tests
   before submitting the next batch as a reviewable PR. Conflicting populated
   fields require an explicit evidence-backed edit; no automatic overwrite.
6. Add every new source to the repository reference registry and regenerate
   citation exports. Do not bundle copyrighted articles, datasheets or imagery.

No blanket open-data license is asserted for third-party material. These files
contain small factual transcriptions and attribution; source terms still apply.
No new scheduled job is configured by this contribution.
