# Global Hydropower Database

The initial research batch contains **7,156 historical WRI plant records in 128
countries**, imported from the complete primary-fuel Hydro partition. This is a
discovery baseline, not 7,156 independently reverified operating plants. The WRI
repository stopped maintenance in early 2022. The initial rows retain historical capacity; 110 Norwegian identities now have
NVE-backed current status and technical metadata. Aggregation scope remains
unresolved for all records.

Data attribution: World Resources Institute, Global Power Plant Database v1.3.0
repository snapshot, CC BY 4.0. Source commit, checksum, licence and retrieval
time are in `sources.json`; per-field provenance and original upstream links
are retained on every row. Upstream plant links have not been independently
reverified. Name matching never proves identity or pumped-storage technology.

## Reproduce

```bash
uv run python scripts/stage_hydro_gppd.py /path/to/global_power_plant_database.csv /tmp/hydro-stage --retrieved-at YOUR_UTC_TIMESTAMP
uv run python -m energy_data_retrieval.hydro_catalogue validate
uv run python -m energy_data_retrieval.hydro_catalogue build --output artifacts/hydro-v1
uv run python examples/database/plot_hydro_catalogue.py
```

Reviewable JSONL is canonical. The shared snapshot writer builds deterministic,
typed Zstandard Parquet; generated binaries stay outside Git and publish with
Pages. The shared browser viewer offers a clustered world map, category/numeric
filters, all schema fields, evidence details and CSV/Parquet downloads.

## Scientific boundaries

Historical capacity is separate from installed, operational and planned MW.
Pumping electrical input is separate from generating output. Usable storage MWh
is never inferred from reservoir volume. Missing data is not zero. Reported and
modeled annual generation observations remain separate, with periods and units.
When a source omits capacity year, 2021 is only a dataset-vintage marker; the
actual observation year remains unknown in `extensions_json`.

Only reviewed independent/child scopes without unresolved overlap enter capacity
summaries. Summaries separate lifecycle and technology, and historical totals
also separate vintage. Parent complexes are excluded even after filtering. All
launch records are excluded from current capacity totals, which display Unknown.
Country charts show record counts, not national market shares or capacity ranks.

## Continuation

Use the persistent `research/backlog.json`, coverage manifest and decision ledger.
Reconcile registry IDs and dated operator/regulator evidence before enriching
status, technology, hydraulic metadata or scope. Preserve creation dates and
use the existing conflict-quarantining upsert API. Reuse the open hydro PR; refresh
remote refs before writing and never overwrite concurrent PV/BESS/Wind work.
See the published snapshot schema for every field and unit.

## Norway official registry staging (5 November 2026)

The NVE all-assets API was processed completely: 2,010 source rows yielded
1,977 generating candidates and 33 pump-only exclusions, with no parsing
quarantines. **110 candidates now enrich existing WRI identities; none add new plant IDs.**
The existing 291 Norwegian WRI identities require an explicit registry crosswalk;
name equality is not proof of identity. Candidate facts and decisions persist in
`catalogues/hydro/research/nve-20261105/`, alongside the original-response checksum.
Attribution: Norwegian Water Resources and Energy Directorate (NVE), NLOD;
[NVE source and field documentation](https://api.nve.no/doc/vannkraftdatabase/).

```bash
uv run python scripts/stage_hydro_nve.py nve-response.json /tmp/nve-stage --retrieved-at 2026-11-05T08:45:58Z
```

The importer stages generating MW, owner/operator, basin, lifecycle, gross head
(at NVE's 67% filling reference), maximum turbine flow and normal-period
1991–2020 annual generation. The latter is modeled normal production, not a
measured annual observation. Price area is not a physical grid connection.
Commissioning strings remain raw metadata until date precision is reviewed.
Pumped capability does not establish pure/mixed subtype or pumping input MW.
Coordinates, reservoir energy and precise dates are not inferred.

`research/market-ranking-202603.json` records GEM's March 2026 top-ten operating
hydropower capacity ranking and a separate pumped-storage ranking. The named
metric is operating generating nameplate MW for facilities of at least 30 MW;
it is not an all-size national inventory. Pumped capacity is a subset, never an
addition to the hydropower ranking. Source sheet URLs and row locators accompany
the factual summary. GEM bulk-file access and reuse review remain outstanding.


## Reviewed Norwegian identity enrichment

On 5 November 2026, 110 existing WRI records were linked to NVE registry IDs
through an explicitly reviewed crosswalk: unique exact names, NVE API/map ID
agreement, points within 250 metres and matching current API/map capacity and
operating state. No fuzzy names or spatial proximity alone trigger a merge.
The crosswalk and selected official map evidence are retained under `research/`.
Map data attribution: NVE, NLOD; https://www.nve.no/kart/kartdata/.

Enrichment preserves UUIDs, creation dates, historical capacities and generation
observations. Current generating MW, status, owners/operators, basin, head,
maximum turbine flow and normal-period generation retain separate provenance.
Differences between historical and current ratings are not attributed to
uprating. All 110 remain excluded from capacity sums pending scope review.
The remaining 1,867 NVE candidates are not additional accepted plants.

Replay `uv run python scripts/enrich_hydro_nve.py` from the repository root.
Reapplying the same evidence leaves update timestamps and JSONL bytes unchanged.


## US EIA annual generator inventory

The final 2025 EIA-860 plant-code partition 1–500 enriches 173 existing plant
identities with 369 distinct generating-unit observations. The reported
nameplate sum is 13,153 MW **at year-end 2025**, not live 2026 capacity.
All accepted plants have only HY/OP generator rows in the Operable sheet.
The other 43 hydro-containing plants are held: 37 mixed technology/state,
four missing existing identities and two name discrepancies. No fuzzy merges
or inferred new plants are accepted.

The WRI upstream importer explicitly encodes EIA plant codes in USA-prefixed
identities; exact names and coordinates independently confirm this partition.
Existing UUIDs, creation dates, historical capacity and generation are preserved.
Generator IDs, statuses, nameplate and seasonal MW, operating month/year and
reported unit metadata remain in `extensions_json.eia_hydro_annual_inventory`
with workbook/sheet/row provenance. Seasonal capacity is not nameplate power.
Generator count is not turbine count. The HY code does not establish reservoir,
run-of-river or diversion subtype. Pumping MW and energy storage remain unknown.
All aggregation roles remain unresolved, including split reporting facilities;
these annual observations therefore do not enter global capacity sums.

Source: U.S. Energy Information Administration, final 2025 EIA-860 release,
retrieved 5 November 2026. Public-domain reuse policy and original ZIP/workbook
checksums are in the source registry. The importer is
`energy_data_retrieval.hydro_catalogue.eia.parse_partition`; replay the committed
bounded evidence using `uv run python scripts/enrich_hydro_eia.py`.
The next reviewed partition, plant codes 501–1000, adds **78 enrichments and
179 generator observations**, with 3,462.0 MW of year-end 2025 nameplate capacity.
Its 31 holds comprise 14 coordinate discrepancies, 11 mixed technology/state
cases, four name discrepancies and two missing historical identities. These
holds remain outside accepted records. Combined EIA coverage is 251 identities
and 548 generators; catalogue coverage remains 7,156 records / 128 countries.

Replay the second partition with:

```bash
uv run python scripts/enrich_hydro_eia.py --batch catalogues/hydro/research/eia-2025-0501-1000.json
```

Next partition: EIA plant codes 1001–1500, then rotate to Brazil ANEEL SIGA.
The source backlog retains Norway, other regions and all unresolved identities.


## EIA continuation and Brazil source rotation

The 5 November 2026 continuation covers plant codes 1001–1500 and 1501–2000:
**84 existing plants enriched**, 370 generator observations, and 2,397.6 MW
at year-end 2025. Thirteen plants remain held (nine mixed technology/state
and four missing existing identities); none are automatically created. Combined
EIA coverage is 335 identities and 918 generators, with 87 holds. UUIDs,
creation dates and historical observations remain unchanged; all capacity scopes
remain unresolved and excluded from global totals.

```bash
uv run python scripts/enrich_hydro_eia.py --batch catalogues/hydro/research/eia-2025-1001-1500.json
uv run python scripts/enrich_hydro_eia.py --batch catalogues/hydro/research/eia-2025-1501-2000.json
```

Next regional work is Brazil: SIGA metadata is accessible under ODbL but its
CSV and official datastore API returned HTTP 503. The independent ONS
[capacity inventory](https://dados.ons.org.br/dataset/capacidade-geracao)
reports generating-unit nominal MW for ONS-dispatched operation classes, not
a census of every small plant. Its publisher identifies CC-BY reuse with
attribution. Identity, unit/plant aggregation and date interpretation must be
reviewed before acceptance. EIA resumes at codes 2001–2500 afterward.


## Brazil ONS exact registry enrichment

On 5 November 2026, the first 100 sorted ONS hydro CEG identifiers yielded
**78 existing plant enrichments and 289 generating-unit observations**. Sixteen
name discrepancies and six missing historical identities remain held. WRI's
Brazil importer explicitly derives its numeric plant ID from the CEG code;
acceptance additionally requires exact names allowing only case/whitespace
normalization. No fuzzy matching or new plant creation is performed.

CEG IDs, reported owners/operators, unit equipment IDs, nominal MW and raw
test/operation/deactivation dates are retained with CSV row locators. The ONS
dictionary defines `val_potenciaefetiva` as nominal unit MW. These unit facts
do not establish complete plant installed capacity or current lifecycle:
plant status, coordinates, historical capacity and aggregation roles remain
unchanged. Historical owner evidence is retained before updating owner names.
Pumping power, storage energy and hydraulic subtype are not inferred.

Attribution: Operador Nacional do Sistema Elétrico (ONS), CC-BY per publisher;
normalization/grouping and the WRI identity crosswalk are our transformations.
Original CSV, dictionary and WRI importer checksums are in the source registry.
The CSV lacks the optional `id_ons` dictionary field; no value is invented.

```bash
uv run python scripts/enrich_hydro_ons.py
```

Next: remaining 80 sorted ONS hydro CEGs after the saved partition cursor,
followed by the outstanding alias/identity cases. Total coverage stays at
7,156 historical plant records in 128 countries, now with 523 enriched identities.


## Completed ONS partition review

The remaining 80 sorted CEGs add **53 existing Brazilian plant enrichments and
289 unit observations**. Twenty-four name discrepancies and three missing
historical identities remain held. Across the complete 180-CEG ONS hydro
inventory, 131 identities are enriched with 578 unit observations and 49
identities remain held (40 name discrepancies and nine missing identities).
The catalogue now contains 576 enriched identities; plant/country counts and
capacity aggregation rules are unchanged.

The refreshed CSV checksum differs, but all 819 hydro unit facts match the
previous download when row locators are excluded. The prior partition's
observations and timestamps are preserved; the new source registry entry
pins the new bytes and row locators. The drift comparison is retained in
`research/ons-20261105-source-drift.json`.

```bash
uv run python scripts/enrich_hydro_ons.py --batch catalogues/hydro/research/ons-20261105-0101-0180.json
```

Next regional partition: the Indian CEA September 2026 station list. Its
official archive metadata is reviewed; original-file acquisition, reuse
assessment, identity reconciliation and phase/pumped-storage scope review
remain outstanding. No Indian candidates have been accepted in this run.


## EIA 2001–3000 continuation and India reuse review

The next two EIA code partitions enrich **122 existing US plants with 330
generator observations**, dated 31 December 2025. The 34 holds comprise
29 mixed technology/state cases, four missing historical identities and one
name discrepancy. Full held plant/unit evidence is retained for review; it
is not accepted catalogue data. EIA now covers 457 identities and 1,248
generator observations, with 121 cumulative holds. Worldwide coverage stays
at 7,156 records in 128 countries, with 698 cumulatively enriched identities.
All capacity aggregation scopes remain unresolved.

The offline preparation utility validates the archive against a registered
SHA-256 and writes accepted/held decisions without changing canonical records.
It refuses different existing review files and duplicate registry identities;
existing capacity conflicts are held. Download the official EIA archive
separately, register its checksum/retrieval timestamp, then prepare a bounded
review with explicit `--year`, `--first`, `--last`, `--reviewed-at`, `--sha256`,
`--archive` and `--output` arguments to `scripts/prepare_hydro_eia.py`.
After reviewing decisions, reproduce the committed enrichments with:

```bash
uv run python scripts/enrich_hydro_eia.py --batch catalogues/hydro/research/eia-2025-2001-2500.json
uv run python scripts/enrich_hydro_eia.py --batch catalogues/hydro/research/eia-2025-2501-3000.json
```

The Indian CEA September 2026 original PDF was acquired, but its published
[copyright policy](https://cea.nic.in/api/websitepolicy/pdf/view/en/2) requires
prior permission. No CEA plant data is imported or redistributed. The review
ledger pins the report and policy checksums. The data.gov.in generation
catalogue returned no original resource and displayed a testing notice.

An independent alternative, IHA's [India Hydropower Database](https://energydata.info/en/dataset/india-hydropower-database),
was acquired under its published CC BY 4.0 terms. Its 182 historical rows
include 110 matched stations, 40 cascade assets, 20 unmatched rows, seven
non-hydro rows and five construction/stalled rows. These are **unaccepted
candidates**, not 182 additional plants. Attribution: International Hydropower
Association, 2019 release; published temporal coverage 1917–2015. Do not infer
current status from those historical labels or turn reservoir volume into
storage energy. The CSV requires Windows-1252 decoding and distinguishes
station coordinates from dam/reservoir coordinates.

Next regional partition: the first 100 matched-station IHA rows sorted by
numeric source ID, with explicit identity, phase and coordinate review.
`research/india-source-review-20261105.json` records acquisition, reuse and
scope findings. EIA resumes at plant codes 3001–3500 afterward.


## IHA India historical identity review

The first 100 matched-station candidates (numeric source-ID order) yield 12
explicitly reviewed enrichments and 88 identity/phase/location holds. Exact
names, historical capacity and station coordinates within 0.001 degree per
axis support the accepted crosswalks; dam coordinates are never substituted.
The complete 182-row original also includes 72 rows in other asset classes,
including seven non-hydro rows. No new plants are created.

Added IHA IDs, river metadata and immutable historical raw observations with
CSV row locators and source references. Owner, lifecycle, generating capacity,
coordinates and aggregation roles remain unchanged. Reservoir volume is not
converted to storage energy. IHA 2019 labels do not establish current operation.
CC BY 4.0 attribution: International Hydropower Association, India Hydropower
Database, 2019 release; crosswalk review and normalization are our changes.

```bash
uv run python scripts/enrich_hydro_iha.py
```

Coverage remains 7,156 records / 128 countries, with 710 enriched identities.
Next: the ten remaining matched-station rows, then Africa rotation; 88 held
identities retain complete evidence for later review.


## India completion, EIA continuation and Africa discovery

The last ten IHA matched-station candidates yield one accepted Koldam
enrichment and nine holds. All 110 matched rows are now reviewed: 13 enriched
and 97 held. Lower Periyar's coordinates disagree substantially and are not
overwritten. Historical river and raw evidence do not establish current status.

EIA codes 3001–3500 add 77 existing identities and 260 generator observations,
with 14 holds (13 mixed technology/state and one name discrepancy). EIA totals
are 534 identities / 1,508 generators / 135 holds. Overall coverage remains
7,156 records in 128 countries, with 788 enriched identities.

```bash
uv run python scripts/enrich_hydro_iha.py --batch catalogues/hydro/research/iha-india-2019-0101-0110.json
uv run python scripts/enrich_hydro_eia.py --batch catalogues/hydro/research/eia-2025-3001-3500.json
```

African discovery acquired the original RePP Africa workbook. Its hosting
metadata says CC0 but its Info sheet says CC BY-SA 4.0; reuse remains under
review and no African records are accepted or redistributed. The source
review ledger records checksums, structural counts and access attempts.
An independent African Hydropower Atlas v2.1 successor is the next target.
Its spreadsheet, field units, original evidence and identity boundaries need
review before import; modeled generation must stay separate from measurements.

The IHA parser now rejects shifted/truncated CSV rows. EIA preparation parses
the exact bytes whose checksum was verified, avoiding a second file read.

The AHA v2.1 spreadsheet has now been acquired and checksummed under its
CC BY 4.0 resource terms. Its Overview label says v1.0 despite its filename;
a v2.2 successor is linked by the repository. Compare these releases before
reviewing the first 100 spatial/technical rows. No African plant data is
accepted in this batch.


## African Hydropower Atlas v2.3 historical enrichment

Compared v2.1, v2.2 and the latest linked v2.3 successor (file modified
2024-02-14). The full 670-row spatial/technical sheet yields 26 explicitly
reviewed existing identities across 18 African countries; 644 candidates
remain held for identity, scope or source review. No new plants are created.
Names, country, historical capacity and coordinates within 0.01 degree per
axis support the crosswalks; shared-plant flags exclude automatic acceptance.
Moukoukoulou's duplicate COD/COG identities and Imboulou's country discrepancy
remain held. Matching rules never establish aggregate/phase independence.

River and basin metadata and immutable historical observations are added.
Capacity, coordinates, lifecycle and aggregation roles remain unchanged.
Model outputs (including energy per unit volume and storage available) are
excluded. Retained raw flow, filling time and availability values may be
modeled and are not promoted to canonical measurements. Reservoir volume
is never converted into energy. Model channel/reservoir IDs are not official
plant registry IDs. Unknown canonical measurements remain null.

Attribution: Sebastian Sterl and Charles J. Chawanda, African Hydropower Atlas
v2.3, CC BY 4.0. Crosswalk review and normalization are our changes. The source
registry pins the resource URL, retrieval time, release date and checksum;
`research/aha-v23-reviewed.json` preserves row locators and original source
columns, while `aha-version-review.json` records version comparisons.
The workbook Overview label is stale; the resource and checksum identify the
release. Historical status labels do not establish present-day operation.

```bash
uv run python scripts/enrich_hydro_aha.py
```

Coverage remains 7,156 historical records / 128 countries, now with 814
enriched identities. The gallery reports the AHA count separately. All plant
aggregation scopes remain unresolved, so these records do not contribute to
a verified worldwide generating-MW total. Next: EIA final-2025 plant codes
3501–4000; targeted African alias/scope review and Oceania discovery follow.


## EIA final-2025 codes 3501–4000

Reacquired the official ZIP on 2026-11-05T20:40:13Z; its checksum matches the
previously reviewed final-2025 release. Reviewed 109 hydro-bearing plant IDs:
**92 existing identities enriched, 17 held, no new plants**. Retained 280
generator observations with official IDs, operators, nameplate/seasonal MW,
reported commissioning dates and year-end-2025 status. Holds: {'mixed_technology_or_state': 15, 'coordinate_review': 1, 'missing_existing_id': 1}.
Pumped/mixed and non-OP units remain unaccepted by this conventional-hydro
partition. Historical status is not promoted to current operation; capacity
aggregation remains unresolved and excluded from worldwide totals.

```bash
uv run python scripts/enrich_hydro_eia.py --batch catalogues/hydro/research/eia-2025-3501-4000.json
```

The replay command also accepts `--root` for isolated catalogue copies.
Coverage: 7,156 records / 128 countries / 906 enriched identities; EIA totals
626 plants / 1788 units / 152 holds. Created timestamps and prior
observations are preserved. Snapshot checksums and completeness are recorded
in `research/eia-2025-3501-4000-validation.json`.

Next regional partition is New Zealand's official dispatched-generation
fleet. The old EMI/new EA portals show differing CSV dates, and the listing
includes formerly dispatched plants. Verify the original and reuse terms
before accepting any records. EIA resumes at codes 4001–4500 afterward.


## New Zealand dispatch review and EIA 4001–4500

Acquired Electricity Authority's 2 July 2026 dispatched-generation CSV under
CC BY 4.0 (attribution: Electricity Authority, New Zealand; extraction is our
change). The listing prose has a stale filename. All 157 rows were read;
68 hydro observations for 42 names remain **held**, with no NZ canonical
additions. Historical effective intervals and multiple connection points
must not become duplicate plants or summed generating MW. Benmore's 540 MW
historical and split 270 MW entries illustrate this risk. Sentinel dates
1899/9999 are retained raw, never interpreted as commissioning/retirement.
The parser rejects duplicate intervals, malformed rows and invalid ratings.

```bash
uv run python scripts/stage_hydro_nz.py /path/to/20260702_DispatchedGenerationPlant.csv --output /tmp/nz-candidates.json
uv run python scripts/enrich_hydro_eia.py --batch catalogues/hydro/research/eia-2025-4001-4500.json
```

EIA codes 4001–4500 add 44 existing US identities and 129 generator
observations; two candidates remain held. Fresh ZIP checksum matches the
reviewed final-2025 release. Dates, operators, generating/seasonal ratings
and registry IDs remain dated observations, not live operation. Coverage is
7,156 records / 128 countries / 950 enriched identities. EIA totals: 670
plants / 1917 unit observations / 154 holds. Aggregation scopes remain
unresolved and excluded from totals. Next: explicit NZ identity/interval
review; EIA resumes at 4501–5000. Source, candidate and validation ledgers
retain resumable decisions and deterministic snapshot hashes.


## Reviewed NZ identities and EIA continuation

Explicit owner/WRI/EA identity reviews accept Aratiatia and Aviemore, retaining
CSV rows 14 and 15 and their dispatch connection identifiers. Mercury's station
page corroborates Aratiatia's 78 MW; Meridian's station page corroborates
Aviemore's 220 MW. Each has a single EA row and matching historical WRI rating.
Owner pages are used only for limited factual corroboration, with no page
text or imagery redistributed; EA observations retain CC BY 4.0 attribution.
Scalar lifecycle, capacity, coordinates and aggregation roles remain unchanged.
Dispatch UnitCode is not treated as a physical generator ID. The 1899/9999
sentinels remain raw. Sixty-six observations for 40 other names remain held;
Clyde's differing rating bases and Benmore's split connections need review.

```bash
uv run python scripts/enrich_hydro_nz.py
uv run python scripts/enrich_hydro_eia.py --batch catalogues/hydro/research/eia-2025-5501-10000.json
```

EIA ranges 4501–5000 and 5001–5500 have no hydro-bearing operable plants.
The next populated range, 5501–10000, yields 158 existing identities enriched,
388 generator observations and 44 held plants. Empty ranges are persisted as
completed cursors. All observations remain dated to year-end 2025, not live
operation. Coverage is 7,156 records / 128 countries / 1,110 enriched identities.
EIA totals: 828 identities / 2305 generator observations / 198 holds.
No generating-MW total is promoted while aggregation scopes remain unresolved.
Next: remaining NZ identity/interval review; EIA resumes at 10001–15000.


## EIA 10001–15000 and Tuai owner review

EIA final-2025 codes 10001–15000 enrich **99 existing US identities** with
**212 generator observations**. Fifteen candidates remain held: {'missing_existing_id': 4, 'mixed_technology_or_state': 10, 'coordinate_review': 1}.
Namespaced IDs, operators, generating/seasonal MW and unit dates retain original
workbook row locators. Reused source bytes were checksum-verified and reparsed.
No new plants, inferred pumping ratings or current-operation claims are added.
EIA cumulative coverage is 927 identities / 2517 generators / 213 holds.

Tuai is explicitly linked to EA CSV row 140 using Genesis's FY2024 integrated
report, printed page 41. It reports 60 MW, consistent with the historical WRI
record and EA dispatch observation. The potential 6 MW efficiency benefit is
qualified by footnote 1: available only below the station's 60 MW maximum.
It must not become an inferred 66 MW rating. Only the dispatch identity and
immutable observation are accepted. The downloaded report checksum, title,
version, locator and limited-factual-reuse assessment are retained; report text
and images are not redistributed. NZ now has three enriched identities; 65
observations covering 39 other names remain held. Benmore's six 93 MW units,
552 MW maximum output and historical 540/270 MW dispatch rows have different
bases and remain unresolved; no sum or scalar capacity promotion is made.

```bash
uv run python scripts/enrich_hydro_eia.py --batch catalogues/hydro/research/eia-2025-10001-15000.json
uv run python scripts/enrich_hydro_nz.py --batch catalogues/hydro/research/nz-tuai-20261105.json
```

Both replay commands now reject duplicate/missing reviewed identities and
validate every transformation before writing any shard. Conflicts preserve
all files; successful replay remains idempotent. This is not an I/O transaction.
Coverage: 7,156 historical records / 128 countries / 1,210 enriched identities.
All unresolved scopes remain excluded from generating-MW totals. Next regional
batch: first 50 remaining Norwegian WRI identities sorted by WRI ID, with
explicit NVE/owner corroboration; EIA resumes at 15001–20000.


## Norwegian review and EIA 50001–55000 (6 November 2026)

The first 50 unresolved Norwegian WRI identities (WRI1002991–WRI1003149,
sorted by WRI ID) remain held. Fresh NVE registry and map responses retain
checksums, exact-name candidate rows and geometry. Names are not identity proof:
duplicated names, spatial offsets and different station/development ratings
need explicit corroboration. Statkraft's Norwegian Adamselv and Aura pages
confirm ratings of 50 and 290 MW, respectively; WRI reports historical 60 and
352 MW. These comparisons do not resolve physical scope or justify overwriting
coordinates. No Norwegian canonical facts were accepted in this partition.
NVE data retain NLOD attribution; owner checks use limited facts only.

The new `scripts/screen_hydro_nve.py` stages bounded review partitions and
rejects truncated map responses and replacement of differing review files.
It never accepts or fuzzy-merges candidates. Resume with `--offset 50 --limit 50`
and original `--api`, `--gis`, `--reviewed-at` and `--output` arguments.

EIA codes 15001–20000 and 20001–50000 contain no hydro-bearing operable plants;
these empty partitions are complete. Codes 50001–55000 enrich **171 existing
US plants** with **396 generator observations**; 41 candidates remain held.
Evidence includes official IDs, operators, generating and seasonal MW, unit
dates and year-end 2025 status. This is not live operation. Original archive
checksum and parsed workbook rows were verified. Replay with:

```bash
uv run python scripts/enrich_hydro_eia.py --batch catalogues/hydro/research/eia-2025-50001-55000.json
```

Coverage is 7,156 historical records / 128 countries / 1,381 enriched identities.
EIA totals: 1,098 identities / 2913 units / 254 holds. Aggregation scopes
remain unresolved and excluded from capacity totals. Next: Norwegian rows
51–100 for explicit review; EIA resumes at 55001–60000.


## Stable Norwegian review cursor and EIA 55001–60000

Norwegian identities 51–100, WRI1003150–WRI1003313, were screened against the
checksum-verified 6 November NVE API/map captures. All 50 remain held; the first
100 screened identities are not accepted enrichments. Statkraft's Norwegian
pages report Grytten at 144 MW and Kvilldal at 1,240 MW. Historical WRI ratings
and Grytten's two potentially related names require explicit alias/scope review.
Owner facts remain review evidence only, with URLs, titles, retrieval dates,
locators and limited-factual-reuse assessment; no copied text or imagery.

The screener now supports an exclusive stable `--after-wri-id` cursor. An
accepted earlier identity can disappear from the unresolved list without
shifting the continuation boundary. Offsets remain supported but cannot be
combined with a stable cursor. Regression tests verify this case.

```bash
uv run python scripts/screen_hydro_nve.py --api /path/to/nve.json --gis /path/to/map.json --after-wri-id WRI1003313 --limit 50 --reviewed-at YOUR_UTC_TIMESTAMP --output /tmp/next-nve-review.json
uv run python scripts/enrich_hydro_eia.py --batch catalogues/hydro/research/eia-2025-55001-60000.json
```

EIA codes 55001–60000 enrich 61 existing US identities with 119 generator
observations; 11 plants remain held. Added IDs, operators, generating/seasonal
MW and unit dates retain year-end 2025 status, not live operation. The original
archive checksum and source rows were verified; no new archive retrieval is
claimed. Coverage: 7,156 historical records / 128 countries / 1,442 enriched
identities. EIA totals: 1,159 identities / 3032 generators / 265 holds.
No unresolved capacity enters global totals. Next: Norwegian identities after
WRI1003313 (101–150), followed by EIA 60001–65000.


## EIA tail and Norwegian pumping-power review — 6 November 2026

EIA codes 60001–65000 enrich 16 existing US identities with 27 generator
observations. Seven plants remain held; codes 65001–99999 contain ten further
held plants and no accepted matches. The code scan now reaches 99999, which is
not a claim of complete US plant coverage. Unmatched official IDs and mixed or
pumped facilities still need explicit identity and scope review. Registry IDs,
operators, generating/seasonal MW and unit dates retain year-end 2025 semantics.
Coverage is 7,156 historical records / 128 countries / 1,458 enriched identities;
EIA contributes 1,175 identities, 3059 units and 282 held plants.

Norwegian candidates 101–150 (after WRI1003313 through WRI1003515) remain held.
The first 150 screened candidates are separate from the 110 previously accepted
NVE enrichments. Statkraft reports Saurdal at 640 MW generating capacity with
four units, two reversible. Its 14 March 2025 filing reports 320 MW existing
pumping capacity and proposes 640 MW. The proposal does not establish present
operation. Mauranger's owner rating is 250 MW, compared with 307 MW in the
historical record. Dated owner facts, source locators and reuse assessments are
retained in the review ledger; canonical values are unchanged.

The NVE screener optionally accepts `--api-source-id` and `--gis-source-id`
together. It verifies both captures against registered SHA-256 hashes before
screening and records the source IDs. Existing invocations remain supported;
registry verification is recommended for published research. Tests cover
changed API and GIS captures and ensure rejection leaves no output ledger.

```bash
uv run python scripts/enrich_hydro_eia.py --batch catalogues/hydro/research/eia-2025-60001-65000.json
uv run python scripts/screen_hydro_nve.py --api /path/to/nve.json --gis /path/to/map.json --api-source-id nve-hydro-20261106 --gis-source-id nve-gis-20261106 --after-wri-id WRI1003515 --limit 50 --reviewed-at YOUR_UTC_TIMESTAMP --output /tmp/next-nve-review.json
```

Next: Norwegian candidates after WRI1003515 and remaining Brazilian ONS
inventory; retain EIA holds for explicit identity/pumped-storage review.


## ONS state and dispatch metadata — 6 November 2026

All 180 ONS hydro CEGs had already been screened. A fresh CSV download confirms
no changed unit facts for the 131 accepted plants (row positions are not facts).
The retained evidence now supplies structured `extensions_json.ons_dispatch_metadata`
for state code/name, electrical subsystem code/name and dispatch modality.
Each value retains source ID and CSV row; multiple values remain explicit sets.
Unknown fields are empty sets. A subsystem is not an exact grid connection.
Original unit observations, lifecycle, capacities and aggregation roles are unchanged.
This enriches 131 existing records in Brazil; it adds no newly enriched identities:
coverage remains 7,156 historical records / 128 countries / 1,458 enriched identities.
The ONS source page describes nominal generating-unit MW and CC-BY reuse;
`val_potenciaefetiva` must be interpreted using that dictionary, not its name alone.

```bash
uv run python scripts/enrich_hydro_ons_dispatch.py --batch catalogues/hydro/research/ons-dispatch-20261106.json
```

The next 50 Norwegian candidates were screened with registered source hashes;
all remain held. Continuation is after `WRI1003631` (201–250). The Brazilian backlog
is corrected: 49 retained holds require explicit identity/scope review; there is
no unprocessed partition in this 180-CEG capacity inventory.


## Explicit Brazilian registry-alias review — 6 November 2026

Thirty-five prior ONS holds are resolved through recorded, individually reviewed
CEG/WRI registry crosswalks and single-name historical, abbreviated or state-qualified
aliases. The importer still rejects name differences by default. An explicit review
must match record UUID, original name, CEG and every source unit name; no fuzzy
matching is used. The canonical name remains unchanged and the ONS name becomes
an alias. Original hold ledgers remain immutable; the new resolution ledger
supersedes only these 35 decisions. Five multi-powerhouse groups and nine missing
identities remain held. Copel's 18 November 2024 primary-source description also
corroborates Foz do Areia, Segredo and Salto Caxias aliases; proposed expansions
are not accepted as current operating capacity.

The batch adds 150 dated unit observations, CEG IDs, owners/operators, aliases and
state/subsystem/dispatch metadata. Plant capacity, lifecycle and aggregation scope
are not inferred. Coverage is 7,156 records / 128 countries / 1,493 enriched identities;
ONS contributes 166 identities and 728 unit observations. Source reuse and row
locators remain those of the original checksum-pinned ONS captures.

```bash
uv run python scripts/enrich_hydro_ons_aliases.py --batch catalogues/hydro/research/ons-aliases-20261106.json
```

The Norwegian continuation after `WRI1003631` returns zero rows: the remaining-identity
scan is exhausted. The 200 screened holds remain unresolved, separate from 110
accepted NVE identities. Next: five ONS multi-powerhouse groups, then nine missing
identities; do not repeat the exhausted scan.
