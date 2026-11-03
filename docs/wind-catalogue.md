# Global Wind Database

The Wind catalogue connects identifiable projects, exact equipment configurations,
individual turbines and numerical curves. The proposed branch contains **5,355 project
records in 59 countries, 53 exact equipment records from six manufacturer names,
and two original numerical power curves** (51 turbine configurations, one blade and one converter). No individual turbine inventory has
yet been imported. These are proposed branch totals, not merged totals or a
worldwide operating census.

The complete 5,344-row Wind partition of WRI Global Power Plant Database v1.3.0
provides a historical discovery baseline. WRI stopped maintenance in early 2022.
The initial import enriched two identities with primary evidence; eleven
primary-source project records are added, including one aggregate and its two
phases. There are 5,354 non-group project records. The baseline is not silently
classified as current, operational, onshore or free of phase overlaps.

## REPD and OEM continuation (3 November 2026)

The complete **2,858-row REPD Q2 2026 wind partition** was reviewed against
WRI’s pinned `resources/GBR/matches_GBR.csv` crosswalk. **642 existing identities**
were substantively enriched (641 operational and one decommissioned observation).
These are dated registry claims published 3 August 2026, not a November operating
census. The other **2,216 applications are deferred**, with exact IDs and reasons
in `2026-11-03-0644-repd-decisions.jsonl`. No applications were silently added as
new farms, and no identities were merged using a name alone.

All 642 retain their original IDs, creation dates, historical observations and
`aggregation_role=unresolved`. Their new lifecycle evidence does **not** resolve
phase or repowering overlap: capacity summaries are unchanged. Applicant/operator
text remains qualified; grid X/Y and generic turbine height remain original values
until CRS and hub/tip definitions are established. The CSV’s capacity field is
interpreted with lifecycle, while CfD values stay distinct in support metadata.

The 22 added OEM records cover all 15 distinct models in the inspected Siemens
Gamesa onshore navigation/offshore portfolio, its explicitly announced APAC
SG 8.0-167 variant, the B81 blade, and all five models in GE Vernova’s current
3 MW/6 MW tables. B81 compatibility is explicitly sourced to the APAC announcement.
India/US variants, flexible modes, frequency-dependent hub/temperature options
and derating conditions remain within their documented configurations. Type
certification targets are not achieved certificates. GE noise values are retained
as qualified observations with scalar acoustics withheld because operating
conditions are incomplete. No new curves or individual turbines were added.

The REPD CSV, WRI crosswalk and all 16 OEM HTML captures have original-byte
SHA-256 checksums. The inspected Siemens Gamesa August 2026 overview PDF explicitly
prohibits reproduction; it is not ingested or redistributed. Independent public
product-page tables supply the accepted model facts.

```bash
uv run python scripts/stage_wind_repd.py REPD_Publication_Q2_2026.csv matches_GBR.csv \
  artifacts/repd-review --retrieved-at 2026-11-03T06:44:32Z
```

The adapter uses Windows-1252 for this source release, rejects identity collisions,
and records every selected wind entry. It stages enrichment only; it does not
authorize aggregation or overwrite existing primary lifecycle evidence. To
reproduce this iteration, use the pre-iteration catalogue at commit `054d13c`.

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
The initial WRI CSV checksum covers acquired original bytes. Initial rendered
OEM/project pages and the V47 PDF do not claim original-byte checksums; the
continuation’s original CSV and OEM HTML captures do. Public access is not a claim
of open licensing; only factual specifications are transcribed. The WRI-derived
partition is attributed under CC BY 4.0.

Broad schema coverage includes ownership shares, lifecycle dates, grid and offshore
infrastructure, resource observations, performance, investment, PPAs, permits,
dimensions, electrical/control details, environmental packages and certification
scope. Many fields are currently null. Component compatibility requires explicit
model-level evidence. Beyond the linked B81 blade, separate gearbox, generator, converter, tower,
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

## Administrative-name reconciliation and first converter

The next bounded review exhausted all 55 deferred changed-name REPD candidates.
Only removal of an administrative resubmission label, corroborated by the explicit
WRI registry crosswalk and unchanged reported capacity, can pass the opt-in adapter
rule. Extension, phase, repowering and revised-application words are retained.
Repeated names and replacement links remain held. Capacity aggregation exclusions
are preserved even after a successful lifecycle enrichment.

The first exact wind converter cabinet is ABB ACS880-77CC-6880A/5500A-7,
from hardware manual 3AXD50000813605 Rev A (22 December 2021), pp87–92.
Its grid-side active kW, generator typical kW and apparent kVA remain distinct.
Temperature/altitude derating and enclosure-only lifetime conditions are retained;
no turbine compatibility or optional-configuration combinations are inferred.
The complete ratings table contains one cabinet, not a 20-model equipment batch.

## Procedural history continuation

PR #89 is merged. Main at `33eec838` contains 5,355 projects, 53 equipment records
and two curves. The next batch adds 232 dated planning/appeal events to 114
existing projects without changing lifecycle or capacity eligibility. The first
200 unlinked registry applications retain explicit identity holds and planning
references in the 0835 ledger. No exact 77LC/87LC rating table was obtained;
generic converter ranges and unrelated industrial drives were not imported.

## Canadian inventory reconciliation

The 2026-11-03 09:35 continuation reviews all 327 project-name groups from
7,841 original NRCan workbook rows. It enriches 117 existing Canadian project
identities with reported manufacturer/model, rating, rotor diameter, hub height
and commissioning groupings; 210 identities remain deferred.

Acceptance requires a unique normalized Canadian project name, all turbine
coordinates within 10 km of the historical project coordinate, project-capacity
agreement within 1% (0.1 MW minimum tolerance), and unique nonempty turbine IDs
within the source group. These are corroboration checks, not proof of phase or
repowering scope. All prior lifecycle fields, capacity values and aggregation
exclusions remain unchanged. Inventory counts and mixed fleets are retained in
`extensions_json.nrcan_inventory`; current fleet completeness remains unknown.
No individual turbine or exact OEM equipment record is inferred from this review.

The offline `wind_catalogue.canada.reconcile_group` adapter accepts decoded
source dictionaries. Original workbook units and commissioning strings are
retained. The source registry and decision ledger preserve the original checksum
and Excel-row locators. See `nrcan_wind_turbine_database_2026` in the citation
catalogue. The portal update date is not a commercial-operation date.


## Swedish registry areas, turbine inventory and VENSYS equipment

The 10:35 batch covers the complete `OMRID < '0500'` partition in the official
Vindbrukskollen MapServer: Stockholm, Uppsala and Södermanland. Layers 2 and 3
supply 89 development areas; layers 5–12 supply 348 georeferenced turbine rows.
Seventy-two named area identities and 321 explicit `VERKID` children are added.
Ten repeated municipality/name areas, five unnamed areas and two areas without
linked turbines remain deferred; two turbine rows lack a published parent area.
All ten pre-existing Swedish records are preserved. Names and proximity to any
existing Swedish project trigger reconciliation rather than automatic addition.

A registry area is a documented development scope, not proof of an independent
physical farm or repowering generation. Every new project retains unresolved
aggregation scope. `Uppfört` means physically erected: current operation remains
unknown. Permitted, dismantled and withdrawn states map only where explicit;
mixed states and refused applications keep raw history without a guessed current
lifecycle. Source dates, organizations, permit types, modeled annual production,
maximum turbine ratings and boundary polygons remain attached. Reported zero
annual production is preserved; zero dimensions and placeholder model/date
values become null in normalized fields, with originals retained.

Project map anchors use an explicitly identified linked turbine coordinate,
not an invented centroid. Turbine points are transformed by the source service
to EPSG:4326; positional accuracy remains unquantified. The viewer's turbine
table has parent IDs, model labels, dimensions, filters, clustered map and
inventory KPIs. Counts include proposed and historical records. Fleet composition
is partial; no inventory label is promoted to an exact OEM configuration.

The reusable offline adapter accepts complete source GeoJSON queries:

```bash
uv run python -m energy_data_retrieval.wind_catalogue.sweden \
  --input /path/to/downloaded-queries --source-prefix vbk-20261103 \
  --timestamp 2026-11-03T10:45:00Z \
  --output /tmp/vbk-staged.jsonl --ledger /tmp/vbk-decisions.jsonl
```

Use the exact ten query URLs and checksums in
`research/2026-11-03-1035-source-review.json`; save responses as
`vbk-layerN.geojson`. This staging command never modifies canonical data and
refuses output-file replacement. Existing IDs are held for explicit enrichment
review. To reproduce the accepted first partition, use the pre-batch catalogue
at `fc308ef3`; rerunning against the updated catalogue correctly holds its IDs.
See `vindbrukskollen_open_inventory_2026` in the citation catalogue. Both original
ZIP metadata files identify the inventory as CC0; background maps are separate.

All seven currently linked VENSYS product sheets were reviewed, with original
PDF checksums and p2 locators (`vensys_technical_sheets_2025`). Tower/IEC and grid
frequency options remain nested within each exact configuration. VENSYS 175
uses a medium-speed geared drivetrain; earlier direct-drive designs are not
silently generalized to it. Thermal derating conditions and acoustic mode
qualifications are retained. The VENSYS 136 PDF and undated webpage disagree on
sound power; the normalized scalar is null pending revision/mode reconciliation.
Numerical AEP tables retain unknown density/distribution and cannot substitute
for instantaneous power curves. Seven plotted curves are deferred, not digitized.

Germany's MaStR wind XML was acquired via verified HTTP206 ZIP byte ranges:
44,351 unit rows, plus both catalogue dictionaries. Member SHA-256 values are
recorded; a checksum for the undownloaded full archive is explicitly unavailable.
The next task is the complete Schleswig-Holstein named-farm partition after
catalogue-code verification and WRI reconciliation, not automatic turbine
clustering. See `mastr_full_export_20261103` and the ranked backlog.
