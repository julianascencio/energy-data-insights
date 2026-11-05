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
