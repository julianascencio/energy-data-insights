# Global PV equipment and project catalogue

A growing, evidence-backed catalogue owned and maintained within Energy Data Insights,
created by ASVA Consulting. One row per OEM model/configuration, and one row per
project. **This is an initial research dataset, not a complete global inventory or
certification/compatibility service.** See [launch evidence](research/launch_summary.json)
and [research findings](research/launch_report.md).

The source of truth is sorted, hash-sharded JSONL in `records/`. Five typed Parquet
snapshots are generated for efficient Python, Arrow, DuckDB and other analytical
workflows. Binary datasets are not committed to Git. Source records are sparse;
all registered columns exist in every generated Parquet table, with nulls for
unknown/not-applicable values. No account or API token is needed to rebuild.

```bash
uv sync --locked --all-packages
uv run python -m energy_data_retrieval.pv_catalogue validate
uv run python -m energy_data_retrieval.pv_catalogue build --output artifacts/pv-snapshot
```

## Layout

| Path | Purpose |
| --- | --- |
| `records/{entity}/{id-prefix}.jsonl` | Reviewable canonical records; stable ID and one entity per line |
| `sources.json` | Source ID → exact URL, publisher, retrieval time, license, revision/hash where available |
| `research/launch_quarantine.jsonl` | Ambiguous raw source rows excluded from accepted records |
| `research/launch_summary.json` | Launch counts and coverage, not a continuously updated total |
| `research/launch_report.md` | Research decisions, source comparisons and limitations |
| `RESEARCH_PROMPT.md` | Improved task specification and recurring research procedure |
| `DATA_DICTIONARY.md` | Column names, types, units and source crosswalk |
| `licenses/` | Required notices distributed with snapshots |

Every snapshot has `modules.parquet`, `inverters.parquet`, `trackers.parquet`,
`combiner_boxes.parquet`, `projects.parquet`, a source registry, the full schema,
license notices and `manifest.json` with hashes, row counts and field completeness.
Build outputs are immutable: use a fresh directory for each snapshot. The existing
GitHub Pages workflow publishes these downloadable files on successful main builds.

## Explore the database

The [Database example gallery](https://julianascencio.github.io/energy-data-insights/auto_examples/database/index.html)
contains runnable queries and statistics. The
[interactive viewer](https://julianascencio.github.io/energy-data-insights/database-viewer.html)
loads all records from checksum-linked Parquet projections, with search, filters,
column selection, grouped charts, provenance inspection and filtered CSV exports.
Both update during each documentation build. The generated browser assets are
not a second editable data store.

## Record and update contract

- `record_id`: stable UUID5 from the entity identity, independent of ratings and dates.
  Model case and punctuation are preserved: `B` and `b` can mean different variants.
  Renames and OEM acquisitions require alias review, not a new identity by default.
- Equipment: exact manufacturer + model, with explicit regional/voltage/hardware
  variant where known. A family with configurable ratings is marked as such; do not
  create fictional purchasable combinations from separate options.
- Projects: national registry ID when available; otherwise reviewed country,
  locality and original project name. Capacity expansions/phases remain nested in
  `phases_json`; do not count both a park and its phases in capacity totals.
- `created_at` is database creation, **not** OEM launch or plant commissioning.
  `updated_at` changes when record contents/evidence change. `last_verified_at`
  means the cited source was checked, not that a physical plant was inspected or
  an old manufacturer document re-certified. All are UTC timestamps.
- `sources` is a list of registry IDs. Generated `source_urls` is a list of actual
  URLs. `field_sources_json` maps field → source ID; `*` provides the default source
  for fields without an override. With multiple sources, changed fields must cite
  their specific source. Registry metadata preserves the exact document/revision.
- Unknown stays null. Zero and false mean explicitly reported zero/false. Never
  replace a populated value with missing input. Conflicting populated values enter
  a review queue and leave the existing record unchanged.
- AC, DC, unspecified MW, active W and apparent kVA remain distinct. Relative
  `%/degC` and absolute `A/degC`/`V/degC` temperature coefficients remain distinct.
  Numeric lower/upper bounds and approximations belong in `extensions_json` until
  dedicated qualified columns exist. Source conditions must travel with ratings.
- No fabricated equipment-to-project assignments or precise coordinates. Equipment
  model references are UUID lists; populate them only with direct project evidence.

## Adding evidence safely

Register the source first. Prepare complete incoming JSONL records using the
existing column dictionary. For an established entity, reuse its ID. Then run:

```bash
uv run python -m energy_data_retrieval.pv_catalogue upsert \
  --input /path/to/verified-records.jsonl --now 2026-11-01T08:00:00Z \
  --output artifacts/pv-conflicts.json
```

This fills missing fields and emits conflicts; it does not automatically adjudicate
changed ratings, ownership or plant status. Resolve a conflict in a reviewed PR,
retaining the superseded assertion in research evidence or Git history. Repeated
unchanged observations preserve `updated_at`; avoid committing verification-only
churn every hour. Add new sources/records and actual corrections instead.

For the SAM adapter, download the exact `sources.json` URL and verify its registered
SHA-256; `import-sam` does this before parsing. The parser preserves all nonempty
native columns either in typed canonical fields or `extensions_json`.

```bash
uv run python -m energy_data_retrieval.pv_catalogue import-sam \
  --input '/path/to/CEC Modules.csv' --entity-type modules \
  --source-id sam_cec_modules_20261031 --now 2026-11-01T08:00:00Z \
  --output artifacts/sam-quarantine.json
```

Do not reuse this old source ID for a different revision. Add a new immutable source
entry, hash and access time. `write_records` is a full-snapshot, single-writer
operation, not a multi-user database transaction. Work in an isolated branch;
push without force and rebase/revalidate if another writer advances it.

## Reviewed registry batches

The REPD adapter requires a checksum-pinned extract and an explicit reviewed-ID
ledger. It screens identities against the full solar extract, including revised
and non-operating applications. Nearby sites, aliases, reapplications and phases
are flagged for review, never automatically merged or counted as separate plants.

```bash
uv run python scripts/stage_pv_repd.py \
  --input /path/to/REPD_Publication_Q2_2026.csv \
  --review catalogues/pv/research/20261101T0856_repd_review.json \
  --output /tmp/reviewed-repd.jsonl
```

Then use the existing `upsert` command and validate. Staging is offline, refuses
changed source bytes and existing name/ID conflicts, and creates a new output
file. Read the ledger and [research backlog](research/source_backlog.json) before
selecting another partition. Recheck the official publication for revisions;
never reuse a prior source ID for new bytes. The accepted REPD records preserve
native planning references, grid coordinates and milestone dates. They do not
infer owner/operator roles, AC/DC basis, WGS84 coordinates or live operation.
Private applicant fields and addresses are omitted. Required DESNZ attribution
is included in `licenses/` and travels with generated snapshots.

The ODRE adapter similarly requires a pinned capacity cohort (>=10 MW by default) and a complete
individual-PV identity export. It screens all names, shared >=1 MW administrative
communes, phase markers, anonymized entries and prior catalogue aliases. These
are conservative review flags, not automatic merges or proof of plant boundaries.

```bash
uv run python scripts/stage_pv_odre.py \
  --input /path/to/france_large.json \
  --identities /path/to/france_identities.json \
  --review catalogues/pv/research/20261101T0928_odre_review.json \
  --output /tmp/reviewed-odre.jsonl
```

A ledger may explicitly set `minimum_kw` (inclusive, at least 1000 kW) and
`maximum_kw` (exclusive); omitted bounds preserve the >=10 MW default. Bounds
do not relax the national identity/privacy screen. The 5–10 MW ledger is
`research/20261102T0000_odre_review.json`.

Then use `upsert` and validate. The reviewed ledger is specific to the pinned
2026-08-31 snapshot. Required ODRE attribution travels with snapshots. The adapter
preserves unspecified AC/DC basis and registry dates; administrative geography and
rolling measured energy retain their source limitations in extensions.

### Japan FIT review staging

The Japan FIT prefectural workbook adapter stages **review candidates only**.
Facility registrations and parcel-sheet rows are not automatically separate plants.
It checks pinned bytes, Japanese headers, IDs, dates and capacities; retains month
precision; and flags shared parcels without exporting personal names, business
addresses, phone numbers or parcel addresses. Positive solar-cell output supports
PV classification. Certification and planned operation never become operating
status. The portal warns that paper filings lag its snapshot.

```bash
uv run python scripts/stage_pv_japan_fit.py \
  --input /path/to/tottori.xlsx \
  --sha256 ac10084eda5f0d1ee6f54c56ac25d7a0f2dbe0f4c3ef7113016111861c730749 \
  --source-id japan_fit_tottori_20261101T1106 \
  --snapshot-date 2026-09-30 --prefecture 鳥取県 \
  --output /tmp/tottori-review.json
```

The command deliberately cannot ingest canonical records. Review named-project
crosswalks, nearby parcels, phases and existing identities first, then use the
catalogue's existing upsert API with independently accepted records. Recheck the
portal's snapshot, terms and download link before selecting another prefecture.
The [FIT attribution notice](licenses/JAPAN-FIT-NOTICE.md) documents reuse terms.

## Schema evolution and scaling

The packaged `schema.json` is authoritative. Reuse a matching canonical column;
source-specific or uncertain fields go into namespaced `extensions_json`. Promote
frequent fields to nullable columns in a reviewed schema change, bump the version,
update the dictionary, add validation/crosswalk tests and rebuild all tables. Never
change the meaning or unit of an existing column in place. Deprecated columns need
an explicit migration, not silent dropping. A minor version may add nullable fields;
renames, removals and type/unit changes require a major version and migration.

Parquet is the analytical format, not an update-in-place transactional database.
JSONL + Git is deliberate for transparent incremental PR review at this scale.
Use Arrow column projection/filtering; query Parquet directly using DuckDB when
available. Avoid one tiny Parquet file per entity record. If multiple concurrent
writers or hundreds of millions of assertions become necessary, move the canonical
store to PostgreSQL or a transactional table format while retaining Parquet exports.

Data-source licenses apply independently of the repository's software license.
The source registry and retained notices travel with exports. OEM documents are
linked, not redistributed. No logos, product photographs or complete datasheets
are copied. GEM's TZ-tagged CC BY-NC records and ODbL databases are not silently
relicensed into this catalogue.

## GEM global project batches

The February 2026 GEM source is imported in 16 independent UUID-prefix batches.
Each batch changes a disjoint set of canonical project shards, allowing independent
review and merge. Counts are in `research/20261102_gem_summary.json`; they describe
the prepared 16-batch union, not a claim that every batch is already merged.
Rebuild the catalogue to count the records actually present in a checkout.

The offline adapter groups native phase rows by **GEM location ID**. All native
phase attributes survive in `phases_json`, including external IDs, ownership,
research dates, lifecycle status, coordinate precision and storage/hydrogen flags.
Source-reported anticipated start years never become actual commissioning dates.
US projects require an EIA crosswalk and are held. Mixed/non-explicit PV, restricted
source lineage, ambiguous names and matches within 2 km of existing projects are
held without automatic merges. These conservative screens can exclude distinct
neighboring plants and cannot guarantee that every remaining cross-source duplicate
has been detected. Kosovo uses the explicitly user-assigned code XKX.

```bash
uv run python scripts/stage_pv_gem.py \
  --input /path/to/Global-Solar-Power-Tracker-February-2026.xlsx \
  --review catalogues/pv/research/20261102_gem_review.json \
  --output /tmp/reproduced-gem.jsonl
```

The checksum and accepted-identity digest must match. Updated source bytes or new
non-GEM catalogue identities require fresh review. The staging command emits the
complete reviewed batch; apply only the intended UUID-prefix partition. All source
terms and transformations are recorded in `licenses/GEM-CC-BY-4.0-NOTICE.md`.
