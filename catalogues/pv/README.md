# Global PV equipment and project catalogue

A growing, evidence-backed catalogue owned and maintained within Energy Data Insights,
created by ASVA Consulting. One row per OEM model/configuration, and one row per
project. **This is an initial research dataset, not a complete global inventory or
certification/compatibility service.** See [launch evidence](research/launch_summary.json)
and [research findings](research/launch_report.md).

The offline `pv_catalogue.nea.read_nea_pv_registrations` reader stages checksum-pinned
Chinese NEA monthly DOCX attachments for review. It requires an explicitly labelled
centralized-PV section, the exact five public columns, matching counts and unique
PPC project codes. Registered installed MW has an unspecified AC/DC basis;
registration and code digits do not establish operating status, dates or coordinates.
The June through September 2026 attachments stage 141 candidates. The
4 November 15:00 review links 19 registrations to existing projects, adding
registration context and six missing installed-MW values without changing
AC/DC ratings or lifecycle. Other candidates remain in review. The observed
overseas LA code form is staged with a country/scope warning; the listed Chinese
locality must not be assumed to be the generating site. Project, local-name and
phase reconciliation must precede upsert. See the
[NEA attribution notice](licenses/NEA_ATTRIBUTION_NOTICE.md).

The offline `pv_catalogue.dgeg.read_dgeg_page` reader validates checksum-pinned
Portugal DGEG CS polygon pages and stages only explicitly labelled photovoltaic
features. `group_dgeg_pages` preserves native blocks and kW/kVA values without
summing them, requires a separately reviewed ID inventory to prove source coverage,
and leaves every group unaccepted until site/phase review. The first complete
750-feature capture contains 617 PV polygons across 289 licensing processes; these
are not plant counts. No licence-to-operation, centroid or kVA-to-active-power
inference is made. See the [DGEG attribution notice](licenses/DGEG_CC_BY4_NOTICE.md).

The offline `pv_catalogue.rvo.read_rvo_workbook` reader stages checksum-pinned
RVO SDE subsidy decisions in bounded ground/water PV partitions. It requires the
explicit `Zon-PV` theme, excludes anonymised decisions entirely, and omits applicant,
address, postcode and geometry fields. Award references are cursors, not plant IDs.
Subsidy maxima are not capex, category MWp thresholds are not nameplate capacities,
and realisation flags are not current operating-status verification. The July 2026
source has 981 non-anonymised ground/water PV decisions; the first 100 remain
candidates, with zero accepted RVO plants. See the
[RVO reuse and attribution notice](licenses/RVO_REUSE_NOTICE.md).

The offline `pv_catalogue.nsw.read_nsw_project_page` reader stages checksum-pinned
departmental Planning Portal Project Details, retaining application IDs, decision
dates, local government areas and modification scope. It excludes submissions and
contacts, fails closed on ambiguous/schema-drifted identity fields, and never treats
a solar category or approval as positive PV or current operation. Canonical identity
review remains mandatory; modifications are not additional plants.

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

`australia.stage_aemo_exact_enrichment` also stages reviewed null-field fills
from a complete Generation Information worksheet. Each explicit decision pins
the existing record, DUID, survey ID, physical row and approved fields. It
requires a unique existing DUID (or one exact native phase DUID), a single
source unit at the site and an unambiguous canonical identity. Names alone,
multi-unit sites and mixed-technology sites do not qualify. Only explicit
aggregate nameplate AC/DC and financial-owner columns fill nulls; dispatch
capacity and forecast commercial-use dates remain separate observations.
Existing values and contexts are preserved, and disagreements are returned in
the review ledger. The [October workbook review](research/20261105T1327_aemo_review.json)
contains the accepted decisions and retained ownership differences. This is a
reviewed enrichment path, not an automatic unit-to-project discovery feed.

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

### Existing ODRE installed-power gaps

`pv_catalogue.odre.reviewed_installed_power_updates` stages missing
`capacity_unspecified_mw` from maximum active installed kW after an explicit
canonical-record-ID → EIC review. First call `read_odre_json` with pinned bytes.
The helper checks unique EICs across the complete canonical catalogue, a single
native GEM phase, individual PHOTV classification, cohort bounds and privacy labels.
It fails on already populated values. Pass its incoming rows to `upsert_records`;
there is no name-based acceptance or automatic creation of projects.

Existing `capacity_ac_mw`, `capacity_dc_mw`, their original `capacity_basis`,
statuses and nested evidence remain unchanged. The separate installed-power
column has unspecified AC/DC basis; it is not the grid-injection rating.
Differences between dated ratings stay in the review ledger, without choosing a
winner. The first installed-power partition and exact EIC/native-field locators
are in `research/20261104T0600_odre_capacity_review.json`.

### Reviewed INHENERGY SI tables

The offline SI reader stages exact model columns from checksum-pinned OEM PDFs.
It checks the full publisher marker, crops the reviewed table at 72 dpi, then
requires the reviewed model order and complete power/current columns. This avoids
interleaving marketing text with shared table cells. Install Poppler locally.

```bash
uv run python scripts/stage_pv_inhenergy.py \
  --raw-dir /path/to/original-pdfs \
  --review catalogues/pv/research/20261104T1200_equipment_review.json \
  --output /tmp/inhenergy-reviewed.jsonl
```

Use the existing upsert API after identity and field review. Maximum PV access
power, maximum PV input power and rated AC output remain separate. Per-MPPT
currents are unsummed; table-wide merged cells are explicitly labelled. Standard
warranty, optional communications and strict bounds remain qualified. Conflicting
MPPT/cooling/dimension/standards assertions and unresolved merged weights stay in
the review ledger; no variants or certification eligibility are inferred.

### Danish municipal PV-plan review

`pv_catalogue.plandata.read_pv_plan_projection` stages a checksum-pinned, bounded
public WFS projection for review. It requires explicit PV-use code8135 and adopted
plan statusV, exact public fields and unique plan IDs. Geometry and unexpected
fields are rejected. The `19000101` sentinel stays flagged; adoption never becomes
commissioning. Planning capacity cells keep their native scope and unverified
units. This helper produces no canonical projects or automatic crosswalks.

The94-plan cohort and keyset cursor are recorded in
`research/20261104T1300_project_review.json`. Three manually reviewed associated-plan
observations use distinctive names/aliases and actual plan-polygon containment.
Source plant points retain their original accuracy; no capacities, lifecycle or
phases are overwritten. Other plans require original site/phase evidence before
acceptance. Review the separate layer-specific licence before installation-layer
feature requests; the general municipal CC BY4.0 grant does not license every
third-party layer on the map.

### Taipower station/site review

`pv_catalogue.taipower.read_taipower_sites` stages the checksum-pinned public
Taipower renewable-sites CSV (government dataset17141). It requires both the
exact solar technology label and an explicit photovoltaic station name, validates
technology-scoped station/site IDs, and returns complete station groups through
an integer station cursor. A station can contain separate roofs, sites or phases;
these groups are candidates, not canonical projects. Source addresses are excluded.

Installed kW stays native with AC/DC basis unresolved. Model labels do not become
OEM-verified equipment, application status does not become current operation, and
HTTP Last-Modified is not a plant-status date. No capacity sum, automatic crosswalk
or canonical upsert occurs. The initial 20:00 partition staged71PV sites in45
station groups with zero canonical acceptances. The later20:30manual review accepts
oneLongjingplant(station6,threebid/site rowsunder2nativephase labels) and qualifies
contextsfor2existingprojects;otherstation/plantboundariesremainunresolved. See
`research/20261104T2000_taipower_review.json` and its source-specific attribution.

`pv_catalogue.taipower.read_taipower_monthly` additionally stages checksum-pinned
station-month observations from dataset29938. Exact Gregorian periods, station
names and whole observation keys are required. Conflicting duplicate periods fail
closed unless an exact reviewed hold-key list is supplied; all observations for
those keys are withheld together. No preferred duplicate, month repair, annual
sum, AC/DC basis or plant boundary is inferred. Two historical June2016 conflict
groups remain held; six Q3 2026 observations support two manually reviewed named
station contexts. Those contexts are not plant/phase ID merges or rating updates.
The dated Taiwan review separates the source station scope from canonical plants.

The Longjing manual review checks complete source sites13/14/15, preserves the
first two construction bids under native phaseI and site15 under phaseII, and
excludes the unrelated CSC/ChinaSteel rooftop portfolio. Its September2026
reported6485.94kW becomes6.48594MW with basis unknown, without summing site values.
No coordinates or present operation are inferred. Tainan's214ha area and dated
20MW/20MWh storage use separately licensed government evidence; earlier proposed
15MW storage and incompatible forecast/rating scopes stay qualified. See
`research/20261104T2030_taiwan_review.json` and the updated attribution notice.

The offline `pv_catalogue.taiwan_private.read_taiwan_private_pv` reader validates
Taiwan Energy Administration's checksum-pinned private solar inventory. It checks
the exact caption and five public columns, preserves merged-cell origin rows,
native kW and ROC-year text, and stages bounded physical-row partitions. The
26 January 2026 content reports statistics through 31 December 2025: 787 solar
rows, with the first400 staged. Manual primary-source reviews associate rows1–10
with an existing Sungen phase aggregate and accept **one Daliao depot plant**
from row13. No plants are accepted from newly staged rows101–400. Daliao
commissioning-year evidence conflicts and remains unpopulated.
Repeated rows/phases, positive PV technology, company roles and AC/DC basis need
manual review. Row cursors are not native facility IDs. See the
[Taiwan inventory attribution](licenses/TAIWAN_ENERGY_PRIVATE_OGDL_NOTICE.md).

LIVOLTEK Hyper, HP3 D2/KL2 and HP2 L1P exact models retain region, battery,
PV, EPS and grid conditions separately. The 5 November review leaves disputed
Hyper width/height axes, HP2 MPPT upper bounds and battery currents, and a
suspicious shared KL2 output-current value unpopulated. See the dated
`research/20261105T0058_equipment_review.json` for both source observations.

Five exact DEGER trackers retain component IP ratings, module-load and module-area
bounds, conditional wind limits and source-specific drive/control conditions.
Contractual defect-liability periods are qualified separately from unrestricted
product or structural warranties. Beitou and Changxing rooftop plant identities
use independent primary city evidence; Changxing planned-opening and regulatory
commercial-year scopes remain distinct. See the dated 5 November 01:30 reviews.

The 5 November 03:00 review adds reconciled Afore SL/THP specifications, a
DEGER D18H tracker and two distinct Noark combiner architectures. Conflicting
PDF/live-table assertions stay in the dated equipment review. Uruguay ADME
Table10 contributes authorized UTE-grid injection limits and generating-agent
contexts to eight existing plants; these are not installed AC/DC ratings or
owner/operator assignments. Lucía's November environmental consultation adds
proposed modules/area while preserving its earlier DC rating. See
`research/20261105T0300_report.md` and the explicit additive-context resolutions.

### Research update — 5 November 2026, 04:00 UTC

200 existing Chinese projects gain directly reported historical sole corporate owners, operators and complete-phase evidence (600 substantive fields). Seventeen SAJ (existing canonical Guangzhou Sanjing manufacturer) and eleven EPEVER (new manufacturer) exact inverter models add469 canonical technical values plus qualified conditions. SAJ regional suffixes and duplicated PDF pages are excluded. EPEVER continuous AC watts, timed overload watts, battery-side charge currents and temperature-qualified PV open-circuit limits stay distinct. Native H×W×L dimensions map L to length, not assumed depth; generic warranty claims remain qualified context. No grid-export capability or current availability is inferred. See dated0400 review, source captures, coverage, validation and report; rights/access-limited Canadian and Solinteg candidates remain unaccepted.

### Research update — 5 November 2026, 05:00 UTC

Three historical Steca inverter-chargers and three distinct Antaisolar trackers are added. Twelve existing INHENERGY models gain60typed dimension/topology/string fields with nativeL/W/H axes preserved.211projects gain611historical party/reference fields. ARENA2018integerAC/mounting references remain historical contexts; scalar capacities, lifecycle and installed mounting are unchanged. Steca VA and efficiency bounds are not activeW/exact efficiencies. Tracker maxima/options remain project-dependent and component warranties stay separate. See dated0500review/audit/report and persistent source queue.

### Research update — 5 November 2026, 06:00 UTC

200 complete Chinese projects gain historical corporate owners, operators and phase-linked evidence (600 fields). Eleven exact Felicitysolar hybrid models add 155 canonical technical values plus qualified battery, PV, grid, backup, mechanical and environmental conditions. Backup watts do not establish grid rated active watts; per-tracker and battery currents remain separate. Unlabelled axes, warranty applicability, ambiguous string layouts and inconsistent full-load voltage limits stay qualified or held. Cáseda huerta rows remain separate from nearby Viscofan; the exact BON resolution endpoint returns 503. See the dated 06:00 source, project, equipment, identity, audit and validation ledgers.

### Research update — 5 November 2026, 07:00 UTC

Ten exact SRNE models add140 canonical technical values and qualified PV/battery/grid/load conditions. ASP link bytes are manualVer1.9 dated21August2026 despite the old filename. Battery-only efficiency, apparent peaks, typical transfer time, unlabelled axes and the HESP DC surge-class disagreement remain qualified or held.200projects gain600 historical corporate-party/context fields. Two battery busbars are excluded from PV combiners. NERSA's September2026 workbook is newly accessible through its public Registered entities category; reuse/identity/power scope remains unresolved and zero plants are accepted. See dated0700review, source captures, audit, coverage and report.

### Research update — 5 November 2026, 08:00 UTC

214 complete Chinese PV projects gain642 historical corporate owner/operator/context fields, exhausting the strict sole-owner/direct-operator partition. Fifteen exact KEMAPOWER CB combiner defaults add146 canonical technical values plus qualified mechanical, humidity, protection and per-way conditions. Multi-output currents are not summed; CB93 retains its explicit three outputs and CB101-1 its literal model spelling. DWH tuples remain raw qualified values pending axis confirmation. Q3 prior-consent rights and CHINT/Noark identity/configuration holds prevent acceptance from those tables. NERSA discovery remains rights/identity/power-scope held. See dated0800 reviews, manifests, audit, validation and source queue.

### Research update — 5 November 2026, 09:00 UTC

200 complete Chinese projects gain 400 historical operator/context fields without assigning owners or changing capacity/lifecycle. Seventeen KEMAPOWER ST and SAKO hybrid inverter models add 295 canonical technical values plus qualified grid, EPS, battery, PV, mechanical, environmental and warranty claims. Per-MPPT current/power vectors are not summed; maximum PV power is not rated Pdc; VA is not active W. SP-D revision conflicts, ST PV maximum/RS485 discrepancies, SAKO unlabelled axes and Isc scope remain held. Riello is rights-held; Catalunya/DGEG full inventories are not downloaded again. See dated0900 review/audit/coverage/report and resumable queue.

### Research update — 5 November 2026, 10:00 UTC

200 complete Chinese project identities gain 400 historical operator/evidence fields. Ten exact inverters (six Morningstar industrial SureSine and four SAKO) plus six Weidmüller fireman combiners add 202 canonical technical values and qualified conditions. No new projects, modules or trackers. Battery DC is not PV input; DC rated voltage is not maximum; per-MPPT/string currents are not summed. Conditional power, warranty, dimension, model-code and selector-output discrepancies remain held. See dated1000 reviews, audit, coverage and resumable source queue; no new adapter or untested feed integration claimed.

### MaStR solar-unit review staging

`energy_data_retrieval.pv_catalogue.mastr.read_mastr_solar_units` reads a bounded
physical-row partition from an extracted, checksum-pinned `EinheitenSolar.xml`.
It returns native unit/location/EEG IDs, network-review codes and separate native
power observations. Names, operator identifiers and addresses are omitted. Resume
`start_row` only against the same source checksum; reconcile duplicates across
partitions before any catalogue import. It performs no download, project upsert,
unit aggregation, AC/DC assignment or reviewed-status inference. The allocated
inverter-power definition lacks an explicit unit in the inspected row and remains
native. Tests use synthetic fixtures; no live export partition is integrated.

### Research update — 5 November 2026, 11:55 UTC

200 complete Chinese identities gain historical corporate operators and phase-linked
evidence. Ten exact Imagine Instruments combiner models cover four fused/breaker
families; arbitrary fuse variants are not expanded. Current, fuse inclusion,
temperature-unit and unlabelled-axis conflicts remain held. OEM warranty is a generic
three-year limited sale-term claim from purchase, not a measured lifetime. See dated
1155 reviews, preservation, source captures, snapshots and the resumable backlog.

### NSW planning tracker review

The offline `pv_catalogue.nsw.read_nsw_renewable_tracker` reader checks pinned HTML,
its explicit table as-of date, the complete summary/detail inventory, card headers
and Australian-format approval dates. Duplicate names remain separate candidates.
The 6 August 2026 tracker contains 93 Solar Farm cards, including 16 under assessment;
that publisher category alone does not prove PV. The 5 November 16:09 review enriches
23 existing positively identified PV projects after manual identity review. Native
planning capacities, storage, statuses and regional location labels remain qualified
historical context, with no nameplate, operating-status or coordinate inference.
Existing non-null contexts are held rather than overwritten. Source attribution is
in `licenses/NSW_DPHI_CC_BY4_NOTICE.md`; third-party reports/submissions are excluded.

The offline `pv_catalogue.nrcan.read_nrcan_mpi` reader checks checksum-pinned
NRCan Major Projects Inventory workbooks before staging. It rejects an embedded
publication restriction even when portal metadata advertises an open licence.
The 2025 workbook retrieved on 5 November 2026 has this conflict: no rows are
staged or accepted. A corrected release still needs independent reuse review.
Synthetic boundary tests cover headers, four-digit identifiers, duplicate IDs,
classification, cost types and inference/privacy limits. Generic `Solar` does
not prove PV; proponents are not owners, historical status is not current
operation, and approximate native CAD-million estimates are not verified capex.
Hidden vendor sheets, geometry and coordinates are excluded from staged output.
