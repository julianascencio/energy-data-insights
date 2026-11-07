# Global Hydropower Database

The initial research batch contains **7,156 historical WRI plant records in 128
countries**, imported from the complete primary-fuel Hydro partition. This is a
discovery baseline, not 7,156 independently reverified operating plants. The WRI
repository stopped maintenance in early 2022. All initial rows have unknown
current status, unknown hydro subtype and unresolved aggregation scope.

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
See `DATA_DICTIONARY.md` for all typed fields.


The 6 November new-identity review adds **eight CEG-keyed Brazilian plants** to
that historical baseline: 7,164 total records in 128 countries. They carry 21
ONS generating-unit observations; five have independently reported installed
MW, three have turbine descriptors, and one has total reservoir volume.
These values remain excluded from additive totals while physical overlaps are
unresolved. The eight new records have no invented WRI IDs or map coordinates.
See `research/ons-new-20261106.json` for acceptance and held decisions.

The KenGen 2025 owner-report batch enriches all eight existing Kenyan identities
with **160 dated observations**: installed/effective MW and generated/sold GWh
for fiscal years ended June 2021–2025. These remain separate in
`observations_json`, with per-cell page, station, year, column and unit locators.
The primary report is registered as `kengen_annual_report_2025` in the formal
bibliography. Effective capacity is not substituted for operational or installed
capacity; sold energy is not generation. No current status is inferred.
Five additional named stations remain candidates for EPRA identity review.
Small Hydros and Hydro Total are excluded as overlapping aggregates, and Sosiani
has no numerical generation observation. The existing 7,164 records / 128
countries are unchanged; 1,503 historical identities now have enrichment.

```bash
pdftotext -layout /path/to/KenGen-2025.pdf /tmp/kengen-2025.txt
uv run python scripts/enrich_hydro_kengen.py --batch catalogues/hydro/research/kengen-2025-20261106.json --text /tmp/kengen-2025.txt
```

The optional text input rechecks the complete parsed table before any writes.
Changed table shape, year order, duplicate rows or changed accepted evidence
fail for review. Original PDF SHA-256 and access/reuse assessment are retained
in `sources.json`; downloaded source bytes stay outside Git.

Five KenGen owner-identified stations are now accepted: Sang’oro, Sagana, Mesco,
Wanjii and Gogo. They add 60 fiscal statistical entries (58 numeric, two missing),
bringing coverage to 7,169 records / 128 countries, including 13 Kenyan records.
Frozen catalogue accessions identify these records; they are not national licence
IDs. EPRA's PDF returned HTTP 503. The owner report and named portfolio sections
support identity independently of that unavailable registry. Current status,
coordinates and additive capacity remain unresolved. No old/replacement unit
ratings are summed. Replay with `scripts/accept_hydro_kengen_new.py`.

Twelve Kenyan records now retain owner technical assertions with per-field
locators, units, equipment boundaries and uncertainty. Original/replacement
unit groups are distinct; Gitaru's 85 MVA generators are not converted to MW.
Gogo's unqualified head is not promoted to gross/net head, and reservoir total
volumes are not usable volumes or energy storage. Owner commissioning statements
remain unresolved where historical dates differ. Turkwel's copied Gogo narrative
is rejected. These assertions do not change additive capacity KPIs or record
counts. Replay: `scripts/enrich_hydro_owner_technical.py`.

The Uganda ERA September 2026 inventory adds **32 reviewed station/phase
identities**, including Kisiizi Hospital, Kuluva Hospital and Bwindi. Coverage is
now **7,201 records in 128 countries**, with 38 Ugandan records. The complete
39-row hydro partition was reviewed: six potential existing-identity matches and
Swam remain held. Annex 3 of ERA's *Electricity Supply Industry State of the
Environment Report 2023* corroborates the accepted names. These sources are
registered as `uganda_era_capacity_2026` and `uganda_era_environment_2023`.

The accepted records retain **864 annual cells (265 numeric, 599 missing)** for
2000–2026. Reported zero remains zero; missing remains null. The 2026 column is
explicitly September, not year-end. Annual MW observations do not establish
current operation or additive physical scope. No coordinates, licence IDs,
pumping ratings or storage energy are inferred. Frozen catalogue accessions
remain stable across name corrections. Different numbered stations are separate
identities, with shared-infrastructure capacity unresolved.

```bash
uv run python scripts/accept_hydro_era.py --workbook /path/to/Installed-Generation-Capacity-as-at-September-2026.xlsx
```

Omit `--workbook` for offline replay of reviewed evidence. A supplied workbook
must reproduce the full parsed partition before writes. Checksummed original
files remain outside Git; only selected factual evidence is retained. No open
bulk-reuse licence was identified, so neither the workbook nor report is
redistributed. See `research/era-202609-reviewed.json` for decisions and
`research/era-202609-validation.json` for snapshot hashes and completeness.

ERA Annex 3 now enriches those 32 Ugandan identities with 128 dated entries:
commissioning (including the literal decade `1950s` and two unknowns), capacity,
grid connection and lifecycle group. The joint construction/licensed category
is not split into an invented status. All entries describe the 2023 report,
not current operation. Karuma's 400 MW report value and subsequent 600 MW remain
separate vintages. Kuluva's 1995 main-text and 2023 Annex commissioning statements
remain unresolved; no canonical commissioning date is overwritten. Replay with
`scripts/enrich_hydro_era_report.py`. The parser covers 59 rows on printed
pages 287–289; 27 other rows remain candidates, including 21 construction/licensed
identities. The refreshed original PDF checksum is unchanged.

The remaining 21 named projects in ERA Annex 3's 2023 construction/licensed
partition are now accepted as stable identities, bringing coverage to **7,222
records / 128 countries**, including 59 Ugandan records. Twenty-one reported
project MW observations remain dated 2023; seven corroborating UECCC procurement
ratings retain original kW and 29 September 2020 dates. Neither is current
installed capacity. The combined lifecycle group remains unresolved, as do
physical overlaps. No coordinates, official licence IDs or commissioning dates
are invented. The ORIO programme aggregate is excluded.

Source `ueccc_orio_tender_2020` corroborates seven names; differing ratings are
retained separately. Rushobe/Kisonko are additional candidates, not automatic
aliases of Warugo/Nyahuka. Six older ERA identity matches and Swam remain held.
Replay: `scripts/accept_hydro_era_planned.py --text /path/to/report-layout.txt`.
Omit `--text` for offline reviewed-evidence replay. See the new acceptance and
validation ledgers. Next research partition rotates to Asian national inventories.

The Nepal DoED >1 MW construction-licence batch reviews source rows 1–100:
**82 new identities**, 18 held for duplicate names or potential historical
phase/scope overlap. Coverage becomes **7,304 records / 128 countries**, including
94 Nepal records. The complete 262-row source was parsed for duplicate IDs and
names; acceptance review stops at row 100. Next partition is rows 101–200.

Records retain full licence numbers (including leading zeros), licensed MW,
rivers, source promoters, districts, raw issue/validity dates and four coordinate
bounds. Licence membership does not establish current construction or operation.
Source calendar dates are not converted; bounding boxes never become plant points.
Unknown current status and physical aggregation remain unresolved, so these
ratings stay excluded from additive capacity KPIs. Promoters are not asserted
owners/operators. The contact/address column is omitted. Source attribution:
`nepal_doed_construction_hydro_2026`; no open bulk-reuse licence is assumed.
Replay: `scripts/accept_hydro_doed.py --html /path/to/doed-table.html`;
omit `--html` for offline reviewed-evidence replay.


## Nepal continuation: 7 November 2026

The second DoED partition reviews **S No 101–200**, accepting **91 licensed
project identities** and retaining **9 identity/scope holds**. Together with the
previous partition, 173 DoED identities are accepted and 27 candidates remain
held. Coverage is **7,395 records across 128 countries**, including **185 Nepal
records**. The 7,304 prior canonical records and their timestamps are unchanged.

The new capture reproduces all 262 normalized source rows. Its HTML checksum
changed, so both capture checksums and retrieval times remain registered.
The page explicitly says *Updated on — October 15, 2026*: new licensed-MW
observations use **2026-10-15**, with individual measurement vintage unknown.
This does not convert the raw licence issue/expiry calendar strings or establish
current construction/operation. No licensed MW enters installed-capacity totals.

Reviews compare full licence IDs, names, promoters, rivers, districts and source
bounds. Separately named/licensed Daraudi B/C, Hongu and Budhi Gandaki projects
retain distinct identities; shared infrastructure and aggregate capacity remain
unresolved. Rolwaling's repeated name under licences 396/516 remains held, as do
three explicit cascades and five historical-name/scope candidates. No fuzzy merge,
parent link, plant centroid, pumping rating or storage energy is inferred.

```bash
uv run python scripts/accept_hydro_doed.py --batch catalogues/hydro/research/doed-20261107-0101-0200.json --html /path/to/doed-20261107.html
```

Omit `--html` for offline replay. With HTML, the capture checksum, full normalized
inventory and page date must match. The importer also checks that partition
decisions are exhaustive/disjoint, each decision reproduces the source row, and
accepted names are not duplicated elsewhere in the full inventory. Both previous
and new partitions replay without changing accepted records. Checksums and field
completeness are in `research/doed-20261107-0101-0200-validation.json`.

Attribution remains Nepal's Department of Electricity Development,
`nepal_doed_construction_hydro_2026`. No open bulk-reuse licence is asserted;
source-specific rights are not replaced by the repository software licence.
Next: **DoED S No 201–262**, retaining all existing holds, then rotate back to
African Hydropower Atlas Existing candidates after Excel row 242.
