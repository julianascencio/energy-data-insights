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
