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

## NEPRA corporate directory: review-only staging

`nepra.stage_nepra_review` parses a pinned official corporate distributed-generation
HTML directory offline. It returns zero accepted canonical records. The mixed
solar/thermal directory includes portfolios, licence transfers and unspecified
gross capacity. Its copyright notice provides no open bulk-reuse grant. Establish
reuse rights and reconcile licence/site boundaries before accepting any project.

```python
from pathlib import Path
from energy_data_retrieval.pv_catalogue.nepra import stage_nepra_review

review = stage_nepra_review(
    Path("/path/to/pinned-nepra-directory.html").read_bytes(),
    sha256="42bc4e2df46808689c81c37c8310c35b7d2972590212ea0391a6e6c575f53e3f",
    source_url="https://nepra.org.pk/licensing/Generation%20Distributed%20Generation.php",
)
assert review["accepted_canonical_records"] == 0
```

The adapter retains native corporate licence/capacity spellings, qualifies explicit
PV separately from generic solar, flags duplicate licences, and rejects unreviewed
structure changes. Contact fields, noncorporate headings and external links are
omitted. Same-company licences remain separate observations. Raw HTML and full
staging output stay outside Git; the dated review commits counts and native licence
identifiers only. No current operation, ownership, AC/DC or plant boundary is inferred.

## Reviewed UK construction entries

REPD now supports an explicitly reviewed ground-mounted construction cohort. The
existing operational default remains unchanged. For a construction ledger, set
`"reviewed_status": "Under Construction"` or `"Awaiting Construction"` alongside the pinned source checksum,
snapshot date and individually accepted Ref IDs, then use the existing offline
`stage_pv_repd.py` and upsert commands. The adapter keeps construction milestones
separate from commissioning/operation, rejects contradictory operational dates and
unreviewed lifecycle scopes, and preserves stable identities. A planning application
is not automatically a new plant: cross-source duplicates and phase/site boundaries
remain review requirements. See the dictionary and dated review for held candidates.

## Reproduce reviewed municipal PV and exact-EIC enrichments

The offline Madrid adapter checks the entire pinned CSV against incoming building
codes/names/pins and existing Spanish identities. `Código Ayto` identifies a building,
not a national plant; the CSV sequence is only a locator. Repeated buildings and
nearby pins are held for site/phase review, never merged. Published kWp is MWdc after
unit conversion. Building coordinates retain unknown datum/accuracy; undefined
surface and installer/administrative labels do not become land area or EPC/owners.
The active status is a dated municipal inventory assertion. Attribution ships in
`licenses/MADRID_PV_NOTICE.md`.

```bash
uv run python scripts/stage_pv_madrid.py --input /raw/madrid.csv \
  --review catalogues/pv/research/20261103T0000_madrid_review.json \
  --catalogue /baseline/catalogues/pv --output /tmp/madrid-reviewed.jsonl
```

Use the pinned pre-acceptance baseline named in the review ledger, with its source
registry augmented by the immutable current source entry. Replays emit proposals;
acceptance requires the usual upsert and validation. The public source's current
export and coverage dates are recorded separately from its landing-page update.

The ODRE staging CLI also accepts review `mode: enrichment` (default remains `new`).
It checks the full national identity export, all canonical phase/external EICs and
an explicit reviewed EIC allowlist. Only missing grid operator, substation and
registry industrial-service date in one complete canonical phase are filled.
Multiple source connections targeting one project, ambiguous/aggregate/private
identities, future dates and existing extensions require review. Populated facts
are preserved and differing native assertions retained as unresolved evidence.
Replay against the ledger's pinned pre-enrichment baseline, then use upsert.

## Aragón operating-PV discovery

`pv_catalogue.aragon.read_aragon_geojson` and `scripts/stage_pv_aragon.py` verify a
pinned resource319 FeatureCollection and stage review-only metadata. This stage
assigns no canonical project IDs and performs no upsert. The GIS feature ID is not
a national plant ID. Projected-looking polygons without a declared CRS do not
become latitude/longitude or centroids, and the native inverter field labelled
MWp does not become AC capacity. Promoter names are omitted from staged output.

```bash
uv run python scripts/stage_pv_aragon.py --input /raw/aragon319.json \
  --sha256 <reviewed-source-sha256> --output /tmp/aragon-review-only.jsonl
```

Reconcile site/phase identities and source revision before accepting fields. CSV
and GeoJSON export agreement is a source consistency check, not identity approval.

To screen the Swiss SFOE production register offline, use
`scripts/stage_pv_swiss.py --input ARCHIVE --sha256 HASH --output REVIEW.jsonl`.
The output is for review only. It uses the source's PV code and exact parent
links, keeps kW without inferring AC or DC, and excludes addresses, building
identifiers and coordinates. Details may describe orientation or array splits
as well as extensions; do not count them as independent projects.

### Australian major power stations

The [November 2026 station review](research/20261103T1000_ga_review.json)
pins the complete Geoscience Australia Major Power Stations layer response
and the AEMO October Generation Information workbook. It lists the reviewed
GA GlobalID, worksheet row and DUID for each accepted station or locality
fill. Keep both raw files outside Git. For a fresh revision, review identity,
nearby projects, native spatial confidence, technology and whole-site survey
scope before generating a new decision ledger. An exact name or nearby pin
alone is insufficient.

On a checkout preceding the reviewed additions, stage the ledger with:

```bash
uv run python -m energy_data_retrieval.pv_catalogue.australia \
  /path/to/ga.json /path/to/aemo.xlsx \
  catalogues/pv/research/20261103T1000_ga_review.json catalogues/pv \
  /path/to/australia-staged.jsonl
```

Register the two immutable source entries before passing the staged JSONL
to the standard `upsert` command. The adapter emits only accepted decisions;
it does not write the catalogue. An AEMO site with multiple survey rows
requires separate review. GA points retain their native GDA2020 reference;
GA's unspecified generation rating is never used as AC or DC capacity.

### Catalonia named PV review staging

The Catalonia adapter handles dataset `ggx8-jkp4` (named ground-mounted PV
above 100 kW). It groups application/name pairs across municipalities without
summing repeated plant capacity or area, omits applicants, and flags shared IDs,
reapplications, expansions, zero capacities and conflicting cells. It produces
review candidates only. A unique application is not automatically a whole plant;
compare the full extract and existing catalogue before using the upsert API.
Nominal MW has no inferred AC/DC basis; administrative authorization does not
establish physical construction. Operating coverage is limited to commissioning
after November 2019. The September 2026 review decisions and source hashes are in
`research/20261104T0400_catalonia_review.json`.

```bash
uv run python scripts/stage_pv_catalonia.py \
  --input /path/to/catalonia.json --metadata /path/to/catalonia-meta.json \
  --sha256 df4f9164d0c047ee4b7fd63477699e0c5622cf045880670ab66aa9f6cd10eef5 \
  --metadata-sha256 833b7caede748e43918fa227197ceb20689e4cf762d4768e7616b1caf1af0d7e \
  --expected-rows 358 --output /tmp/catalonia-review.json
```

Check metadata `rowsUpdatedAt` before resuming saved partitions. An unchanged
monthly snapshot does not require another complete export. Source-specific
Catalonia attribution and last-update notice travel with the snapshots.
