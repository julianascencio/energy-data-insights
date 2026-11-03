# Global Wind Database

The Wind catalogue connects identifiable projects, exact equipment configurations,
individual turbines and numerical curves. This first branch adds **5,355 project
records in 59 countries, 30 turbine configurations from three manufacturer names,
and two original numerical power curves**. No individual turbine inventory has
yet been imported. These are proposed branch totals, not merged totals or a
worldwide operating census.

The complete 5,344-row Wind partition of WRI Global Power Plant Database v1.3.0
provides a historical discovery baseline. WRI stopped maintenance in early 2022.
Two identities receive additional primary evidence within this import; eleven
primary-source project records are added, including one aggregate and its two
phases. There are 5,354 non-group project records. The baseline is not silently
classified as current, operational, onshore or free of phase overlaps.

## Storage and reproduction

Canonical records are UTF-8 JSONL in `catalogues/wind/records/`, sharded below the
repository source-size limit. UUIDv5 identities use a frozen registry ID or reviewed
natural identity; mutable ratings are excluded. ISO alpha-3 countries, UTC
timestamps, nulls, source registry, field evidence and typed Parquet follow the
PV/BESS architecture. The shared snapshot encoder also preserves the Data Center
public API. Other catalogue source records are unchanged.

```bash
uv sync --locked --all-packages --group docs --python 3.13
uv run python -m energy_data_retrieval.wind_catalogue validate
uv run python -m energy_data_retrieval.wind_catalogue build --output artifacts/wind-v1
uv run python examples/database/plot_wind_catalogue.py
```

Snapshots are immutable, sorted, Zstandard Parquet with schema, source registry,
input fingerprint, table hashes, completeness and capacity summaries. Use a fresh
output directory. Do not commit generated Parquet; the documentation build
recreates it and the lossless viewer projections. Reproducibility is checked with
the locked PyArrow version, not promised across arbitrary encoder versions.

The staging adapter reads a locally acquired CSV without network access:

```bash
uv run python scripts/stage_wind_gppd.py --help
```

It processes every primary-fuel Wind row, retains excluded/deferred decisions,
rejects duplicate source IDs and preserves observed and modeled generation
separately. Synthetic offline fixtures test zero, null, malformed capacities and
identity collisions. Canonical rows include curated reconciliation after staging.

## Capacity, identity and performance rules

| Boundary | Representation and aggregation |
| --- | --- |
| Installed, commissioned, planned, awarded, export | Separate MW fields; never interchangeable or additive |
| Historical WRI nameplate | `historical_capacity_mw`, original observation year when available; otherwise snapshot year explicitly qualified |
| Groups and phases | Parent is `aggregate`; children retain stable `phase_id`; exclude parent totals |
| Unreviewed identity/scope | `aggregation_role=unresolved`; excluded even when filtered alone |
| Repowering | Stable generation and `replaces_record_id`; unresolved active generations share an excluded `overlap_group`; retired generations remain in their own lifecycle |
| Mixed fleets | Explicit manufacturer/model/count entries; unknown counts stay null; linked equipment only when exact |
| Count × rating | A derived consistency check; does not replace a reported capacity |
| Generation/resource | Kind, period, units, reporting boundary, source and locator; resource height required, nullable if unknown |
| Capacity factor | Not computed in this batch: usable capacity-time/partial commissioning boundaries are absent |
| Curves | Separate linked records with original numerical or digitized origin, air density, operating mode and source revision |

Operational evidence is dated, not a guarantee of current operation. Dumat Al
Jandal retains its 2019 announced/award evidence, while MacIntyre's latest reviewed
operator update establishes partial operation without a current commissioned MW.
Lake Turkana's installed scalar is withheld pending reconciliation of 310/310.25 MW. WindFloat Atlantic's
25 MW, Kincardine's 50 MW and Kallpa's 344 MW remain reported values despite
different count-times-rating checks. Greater Changhua 1 and 2a contribute only
their phase capacities; the 900 MW aggregate is excluded.

## Equipment and field evidence

Vestas' EnVentus, 4 MW and 2 MW portfolio tables and eleven Nordex Delta4000 model
pages are processed completely for the selected table/model batches. V236-15.0,
the documented V164-8.4 and V164-9.5 configurations, and V47-660/660-200 revision
943111.R4 complete the first equipment batch. Flexible Nordex operating ranges
remain qualified options; the malformed V136-4.2 nominal rating is withheld.
Hub-height choices do not create synthetic variants.

Every populated scientific field has source IDs plus evidence locator, confidence,
original value/unit or documented normalization. Source records retain revision,
publication date if available, retrieval date and byte availability. Midnight UTC
retrieval timestamps are explicitly date-normalized, not exact access times.
The WRI CSV checksum covers acquired original bytes. Rendered OEM/project pages
and the V47 PDF do not claim original-byte checksums. Public access is not a claim
of open licensing; only factual specifications are transcribed. The WRI-derived
partition is attributed under CC BY 4.0.

Broad schema coverage includes ownership shares, lifecycle dates, grid and offshore
infrastructure, resource observations, performance, investment, PPAs, permits,
dimensions, electrical/control details, environmental packages and certification
scope. Many fields are currently null. Component compatibility requires explicit
model-level evidence. Separate blade, gearbox, generator, converter, tower,
foundation and floating-platform models remain ranked research tasks; no generic
product families are counted as exact equipment records.

## Viewer, examples and continued research

The [Wind viewer](https://julianascencio.github.io/energy-data-insights/wind-database-viewer.html) reuses the existing map clusters,
filters, expandable records, source links, CSV export and completeness display.
Country, owner, manufacturer, exact model, lifecycle and technology categories and
numeric capacities are searchable. Capacity KPIs separate lifecycle states and
exclude unresolved overlap scopes. Generic capacity sum charts are disabled for
Wind Projects. Equipment statistics describe catalogue specifications, not market
share or verified operational performance.

The gallery covers country coverage, installed versus pipeline categories,
manufacturer/model distributions, rotor/specific-power and hub options, offshore
depth/foundations, and compatible original numerical power curves.

`catalogues/wind/research/latest.json` is the batch checkpoint;
`backlog.json` ranks exact remaining sources and offsets. Candidate-level JSONL
ledgers retain additions, within-import enrichment, duplicate candidates, exclusions
and field deferrals. The first USWTDB download failed with HTTP 403 in this
environment: this is an access failure, not evidence of authentication or a reuse
restriction. NREL's turbine-model archive was inspected but not ingested because
individual curve provenance/conditions require reconciliation.

Hourly continuation must inspect current main, compatible open PRs and the ledger,
resume unfinished partitions, acquire a nonblocking branch lock, and publish using
an expected-head check. Leave PRs open and unmerged; never overwrite another run.
