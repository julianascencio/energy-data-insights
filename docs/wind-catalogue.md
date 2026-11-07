# Global Wind Database

The Wind catalogue connects projects, exact equipment configurations, turbines and
numerical curves. Batch `2026-11-07-0800` contains **8,328 projects, 566 equipment
records, 13,657 linked turbines and two original numerical curves**, across
**64 countries and 66 equipment manufacturer labels**. Merged main at `dbd83f04`
contains 8,323 projects and the same equipment, turbine and curve counts.
This run adds five Spanish project records; it does not recount earlier batches.
These are catalogue counts, not a current operating census. Exact continuation
queues are in `catalogues/wind/research/latest.json`.

The nine complete BOE daily title partitions for July 6–11 and 13–15 contain six
notices: three revised proposals (Paucali, Arlo and Céfiro), two withdrawn proposals
(Arrebol and Lagunillas), two solar-only corrections excluded, and Desma held for
original wind-permit reconciliation. All five new project scopes remain excluded
from capacity totals. Céfiro retains reported 110.9 MW separately from the
17 × 6.525 = 110.925 MW fleet check. Shared evacuation and construction budgets
retain their own boundaries; planned fleets do not establish exact OEM revisions.

The final REPD structural review covers 137 ordinary cases and 79 exceptions.
The ordinary cursor ends at **2,137**, not 2,216; the latter includes the 79
exceptions. All 2,216 remain deferred physical identities. The adapter now accepts
explicit exception-reason partitions and screens documented BOE aliases before
addition. The shared viewer exposes sourced fleet checks, unknown checks and
reported zeros without changing capacity aggregation.

The complete 5,344-row Wind partition of WRI Global Power Plant Database v1.3.0
provides a historical discovery baseline. WRI stopped maintenance in early 2022.
The initial import enriched two identities with primary evidence; eleven
primary-source project records are added, including one aggregate and its two
phases. The initial batch contained 5,354 non-group project records. The baseline is not silently
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


## Östergötland and ENERCON continuation

The next complete partition (`0500 <= OMRID < 0600`) reviews 227 areas and
672 turbine rows. Independent count queries agree with every downloaded layer.
It adds 192 projects and 559 turbine children; 21 repeated-name scopes, 12 unnamed
areas and two existing identity/spatial candidates remain held (113 turbine rows).
All 5,810 preceding records and all six capacity-category totals remain unchanged.
The adapter now optionally verifies an independent source count, catching silent
truncation even when the response omits an exceeded-transfer-limit flag.

Three ENERCON August 2026 sheets describe four exact configurations: E-138 EP3 E3,
E-160 EP5 E3, E-175 EP5 E1 and E2. The E2 nominal 6,000/7,000 kW options remain
nested; no single rating is selected. Mode/height-dependent acoustic observations
also remain qualified metadata. Cold-climate packages stay distinct from normal
temperature limits, and design-life claims keep their IEC scope. Annual-yield
plots are not numerical power curves. See `enercon_technical_sheets_202608`.
All three originals downloaded successfully after web-reader errors; this was
not authentication failure or evidence of reuse restrictions.

Next Swedish partition: all Jönköping registry IDs (`0600 <= OMRID < 0700`).
The German Schleswig-Holstein named-farm reconciliation task remains pending.


## Schleswig-Holstein registry continuation

The complete MaStR Schleswig-Holstein partition contains 4,788 registered units
in 1,739 name groups, including the empty-name group. Conservative operator,
municipality, coordinate, alias and historical-catalogue screens accept 22 named
parks and 105 turbine children. The other 1,717 groups remain in the decision
ledger. Park names are not official farm identifiers. Stable unit registry IDs
anchor future reconciliation; ownership/name changes must not create new farms.
All 22 parks retain unknown farm lifecycle, partial fleet completeness and
unresolved aggregation scope. Unit status, commissioning dates and separate
gross/net kW are retained without substituting sums for reported farm capacity.
The offline `wind_catalogue.mastr.stage` adapter uses the pinned XML dictionary
and a complete state partition; its synthetic fixture tests alias collisions,
invalid scopes, replay identity and the distinction between unit and farm ratings.
See `mastr_full_export_20261103` and the 1235 decision ledger.

The ENERCON upgrade presentation adds exact E-82 E2 and E-103 EP2 model records
with their respective OM-YO-01 and OM02sBV optional modes. Base ratings and
geometry remain unknown because this source does not specify them. Yield claims
retain annual-average wind-speed and site-load-study conditions; they are not
measured operational performance. Graph-only curves remain deferred. The combined
August 2026 overview duplicates the four configurations already catalogued.
See `enercon_yield_modes_e82_e103`.

Next German partition: Niedersachsen, dictionary code 1408, after verification
against the original category 101 dictionary. Reconcile accepted Schleswig-Holstein
unit links and held groups separately from new state intake.


## Niedersachsen and integrated drivetrain components

The complete 9,034-unit MaStR state partition (code1408) contains3,046namegroups.
The adapter accepts73parks and366linked units;2,973groups remain held. State
selection is explicit and dictionary-checked; the default Schleswig-Holstein
API remains compatible. Previous records and all capacity summaries stay unchanged.

Winergy's historical HybridDrive table provides PZFG2456 and PZFG2535, each
rated3000kW, with2000/2500kNm torque and25/31tonnes assembly mass. These are
integrated two-stage gearbox/permanent-magnet generator assemblies, recorded
once per exact model. Original units and normalization are retained. Current
availability, specific turbine compatibility and absolute lifetime remain unknown.
PDF creation metadata2013-06-03 is not asserted as publication date. The peak
efficiency marketing claim lacks operating-point conditions and is not accepted
as normalized performance. See `winergy_hybriddrive_pzfg`, original PDF p2.

NGC's independent product page describes broad platforms without an exact model
rating table; no artificial configurations were generated from power ranges.
Next: Nordrhein-Westfalen (code1409,6,753units), Jönköping and exact component
configuration evidence.


## Nordrhein-Westfalen and exact yaw/pitch gearboxes

The complete6,753-unit MaStR partition(code1409) yields67parks and314linked
units from2,732namegroups;2,665groups remain held. All prior records and six
capacity summaries stay unchanged. Added state support preserves default APIs.

The original NGC regional archive PDF supplies seven exact SYW yaw-drive types
and seven SPT pitch-gearbox types. Rated-torque ranges, peak torque and gear
ratios remain distinct; stage-count options stay within each model. Generic
platform temperature, certification and turbine-compatibility claims are not
inherited. Physical pages9/10(printed08/09) were visually reviewed. Five SMG
platform columns remain held. See `ngc_wind_yaw_pitch_2022`. The German2024URL
returned404; the regional2022PDF downloaded successfully. This was not an
authentication or explicit reuse restriction. Winergy's unnamed6MW exhibition
configuration remains held for exact identity. No numerical curves added.


## Brandenburg, Jönköping and Bonfiglioli continuation

Brandenburg's complete5,334-unit partition yields22parks and183units, with
1,471namegroups deferred. Jönköping's151areas/902turbines yield109projects and
608units. All ten layers match independent source counts. Forty-two areas and
18orphan units remain held, covering294turbine rows. Both inventories retain
unresolved aggregation scope. All7,530preceding rows and capacity totals stay
unchanged. Exact query URLs and original response hashes are in the1535review.

Bonfiglioli R05_2 p14 provides nine distinct TW model names across13pitch/yaw
application rows. Each model keeps application-specific peak torque together,
including differing yaw/pitch values. These are OEM reference limits, not nominal
torque or independently validated performance. The19dimension rows on p15 use
T designations and remain held pending T/TW reconciliation. See
`bonfiglioli_wind_r05_2`. NGC2024original download returned404 while search and
opened reader show different editions; MPPY/MPPB import remains deferred.


## Sachsen-Anhalt, Kronoberg and ABB continuation

Complete state/county partitions yield64projects and433linked units. All8461prior
records remain byte-identical; capacity summaries unchanged.878German groups
and44Swedish areas (326units) remain held. New scopes are excluded from totals.

The complete15-row ABB2018RevA p10 table (`abb_wind_converters_2018_reva`)
preserves exact77LC/87LC types, including documented twin cabinets. Typical
generator kW is separate from generator/grid kVA and nominal side currents.
Dimensions, mass and flow retain the original per-cabinet expressions. Ratings
depend on selected options; historical specifications do not establish current
product lifecycle, turbine compatibility or independently validated performance.


## Bayern, Kalmar and converter technical conditions

Complete Bayern1889-unit and Kalmar204-area/1330-unit partitions add168projects
and918linked turbines.823German groups,71Swedish areas and24orphan units remain
held. All new project scopes remain excluded; prior capacity totals unchanged.

ABB2018RevA p8 explicitly covers77LC/87LC and adds qualified series-level
operating/storage temperatures, cooling inlet limits, altitude, electrical
interfaces and optional limits to15existing models. All p10ratings remain.
Standard altitude1000m is separate from optional4000m; optional coolant55C is
not a standard limit. No independent performance/certification claim is added.
BMD R04_1 industrial identifiers remain held pending their wind-specific mapping.


## Baden-Württemberg, Gotland and ACU control inverters

Complete partitions add83projects and369turbines; all10059prior records and
capacity totals remain unchanged.514German groups,28Swedish areas and3orphan
units remain held. New project scopes stay excluded from capacity sums.

Bonfiglioli ACU VEC521R6 pp38–41 (`bonfiglioli_acu_vec521r6`) adds all18exact
ACU401type columns in sizes1–5. Motor shaft power, output current,60s/1s overload,
2kHz losses, dimensions and approximate mass retain boundaries. ACU401-22
keeps22A main-table and frequency-dependent23A/22.7A observations separately.
WIND R05_2 p13 supports Active Cube series yaw application, not exact turbine
compatibility. No artificial interface/cooling variants or performance claims.


## Mecklenburg-Vorpommern, Blekinge and completed ACU type tables

The 19:35 batch follows the merge of PR #101. From main `2fd691a7`, it adds
52 projects and 188 linked turbines across complete 2,741-unit German and
58-area/158-unit Swedish partitions. All 10,529 preceding records remain
unchanged. The 722 German groups and 25 Swedish areas covering 72 unit rows
retain explicit deferral decisions. No new project scope enters capacity totals.

Bonfiglioli VEC521R6 (`bonfiglioli_acu_vec521r6`) adds all 12 ACU 201 columns
on pages 35–37 and all eight remaining ACU 401 columns on pages 42–43.
The earlier backlog's size-8 reference was incorrect: page 44 contains derating
diagrams. A separate original document and model-identity review is required.

The records preserve switching-frequency current tables separately from headline
current, including ACU 201-19 and -22 discrepancies. ACU 201-15's single/two-phase
9.5 A limit is distinct from the 12.5 A main-table value. Overloads retain 60 s,
1 s and ten-minute recurrence boundaries. Three-phase-only, choke, thermal,
UL scope and conditional IP20 statements remain qualified. WIND R05_2 page 13
supports series-level yaw-drive application; it does not identify an installed
turbine interface. The gallery exposes those phase/frequency conditions.


## Rheinland-Pfalz, Skåne and ACUx10 frames

The 20:35 batch follows the merge of PR #106. Complete Rheinland-Pfalz and
Skåne inventories add 295 projects and 826 turbines. All 10,789 preceding
records and all six capacity totals remain unchanged. The 862 German name
groups, 519 Swedish areas and 26 orphan turbines retain explicit holds.
The Swedish partition includes prefix11 and confirms no returned rows there.

Bonfiglioli R04_0 (`bonfiglioli_acu_r04_0`) pages24–25 provide 24 exact
ACUx10 configurations: six frame7 and eighteen frame8 entries. Frame7/8
ACU410-51/-53 identities remain distinct, with different dimensions, mains
currents and peak limits. Frame7 ACU410-53 is liquid-cooled only. Neither
mechanical options nor brake-chopper choices create artificial records.

The six ACU610 voltage-row notes about600V-for-UL remain qualified observations;
the approval row supplies no claim. Scalar approval stays unknown. The gallery
shows frame/voltage/current boundaries. No ACUx01 replacement, turbine interface
or independently validated performance is inferred. The separately discovered
spindle application manual was excluded for its explicit reuse restriction.


## Hessen, Halland and remaining ACUx10 tables

The 21:35 continuation follows merged PR #111 and preserves the new gallery hierarchy.
Complete Hessen (1,807 units / 627 groups) and Halland (176 areas / 691 units)
partitions add 139 projects and 555 linked turbines. All 11,934 preceding records,
prior source entries and six capacity totals remain unchanged. All new scopes
remain excluded pending phase and repowering reconciliation. Holds cover 589
German groups and 75 Swedish areas plus two orphan units (306 turbine rows).
No country or manufacturer is newly counted.

Bonfiglioli R04_0 pages 19–23 (`bonfiglioli_acu_r04_0`) supply 34 exact
configurations: 12 ACU210 and 22 ACU410 columns. The source checksum was reverified
and all five tables visually reviewed. Input-phase ratings and column-specific
line-choke requirements stay distinct. Standard, coldplate and liquid dimensions
and brake options remain nested. ACU410-12 is explicit on page 21 despite its
omission from the nomenclature summary. Unclaimed approvals remain unknown.
Series yaw applicability is documented; turbine compatibility and independently
validated operational performance are not inferred. The gallery includes the new
230 V ACU210 entries.


## Thüringen, Västra Götaland and line chokes

This batch adds 618 projects, 2,030 turbines and 23 exact LCVS/LCVT line chokes.
Merged main at the iteration baseline contains 6,713 projects, 202 equipment,
5,745 turbines and two curves; proposed totals are 7,331 / 225 / 7,775 / 2.
All 12,662 preceding records and capacity totals are unchanged. Complete registry
partitions were reviewed; 371 German groups and 226 Swedish areas remain held.
Thirteen duplicated Swedish turbine IDs quarantine their entire parent scope.
Missing area boundaries remain null. All new project scopes are excluded from MW totals.

OEM pp52–56 preserve explicit inverter pairings and original dimension letters.
LCVT025 has conflicting inductance/loss rows; scalar values and the disputed
ACU410-23 pairing are held. No guessed correction or turbine compatibility is added.
The remaining 13 AL-suffix types are the next bounded equipment partition.


## Sachsen, Värmland and electrical components

The 23:35 increment adds 70 projects, 636 linked turbines and 28 exact equipment
types: 13 AL-suffix line chokes and 15 EMC filters. Proposed totals are 7,401
projects, 253 equipment, 8,411 turbines and two curves. Merged main at `7af547f9`
contains 6,713 / 202 / 5,745 / 2; PR #119 cumulatively adds 688 / 51 / 2,666 / 0.
All 15,333 records preceding this increment and all capacity totals are unchanged.
The completed Sachsen partition has 482 held groups; Värmland has 44 held areas
covering 734 turbine rows. All 70 accepted project scopes remain excluded from MW totals.

AL-choke current and dissipation depend on the printed inverter application;
common inductance and assembly dimensions stay on one exact component record.
Two choke-to-inverter links lack a frame identifier and remain held. One filter
application prints ACU210-12, which has no exact existing configuration; its label
is retained without an inferred alias. EMC class/cable conditions remain qualified,
and the general 480V heading is not silently applied to the ACU610 application.
Next: Saarland, Örebro and book-filter assembly tables pp62–63.


## Saarland, Örebro and braking resistors

The 4 November increment adds72projects288turbines11exactBRresistor types and
enriches12EMCfilters with assembly specifications (R04_0 pp62–65).
Saarland114groups andÖrebro25areas/166units remain held. New project scopes
remain excluded from MW totals. Two-resistor combinations retain quantity and
combination ratings within one component record; no artificial assembly model.
HLD110-500/42dimensions and thermal-switch assignments remain unknown.
All previous scalar ratings and creation timestamps are preserved.


## City states, Västmanland and Dalarna

The 4 November continuation adds 53 projects and 637 linked turbines, and
enriches 11 existing resistor records with legacy VEC501R0 electrical, thermal,
mass, terminal and original drawing observations. Current-revision claims are
not inferred. The 103 German groups and 47 Swedish areas held for identity
review remain in decision ledgers. All new project scopes stay excluded from
capacity totals; all previous values and creation timestamps are preserved.


## Gävleborg and offshore identity screening

The 4 November 02:35 increment adds 56 Gävleborg project areas and 928 linked
turbines from all 88 areas and 2,124 turbine observations. The remaining 32
areas/1,196 observations are held for identity/scope review. All 1,813 German EEZ
units were screened across 48 name groups; aliases and sub-array labels prevent
automatic farm additions. The existing E-82 E2 gains revision-qualified 08/2019
base-model specifications. Two restricted Bonfiglioli manuals are excluded.
No new project enters capacity totals; all prior specifications are preserved.


## Västernorrland continuation

The 03:35 batch reviews 97 areas and 2,177 linked/orphan turbine observations,
adding 55 projects and 847 turbines. Forty-two areas and 117 orphan turbines
remain held; no project capacity is inferred. All previous records are unchanged.
The reusable quarantine helper now rejects missing IDs before grouping, so
missing identities cannot be silently hidden as duplicate conflicts.


## Jämtland and converter monitoring

The 04:35 batch reviews all 138 Jämtland areas and 1,729 turbine observations,
adding 69 projects and 784 linked turbines. The remaining 69 areas and 945
turbines are deferred; no project capacity is inferred. ABB system description
3AXD50000022022 Rev C (2020-04-27), pp. 13–14 and 24–25, supplies separately
dated system interfaces for 15 existing exact converters and explicitly names
the optional NETA-21 monitor. Its record and compatibility links preserve that
series/revision boundary; historical ratings are unchanged. Detailed monitor
limits remain unknown after an HTTP 403 download failure. Catalogue claims
are manufacturer documentation, not independently validated performance.


## Västerbotten continuation

All 130 areas and 2,316 turbine observations were reviewed; 67 projects and
916 linked turbines were accepted. The remaining 63 areas/1,400 turbines
remain deferred. Capacity totals are unchanged. NETA-21 gains separately
qualified Rev Q (2026-09-18) technical-table observations, pp.225–226;
contradictory temperature endpoints are retained without a normalized scalar,
and joint NETA/NEXA interface descriptions do not infer per-device allocation.


## Norrbotten and monitoring extensions

All 68 Norrbotten areas and 2,566 turbine observations were reviewed;
37 projects and 822 linked turbines were accepted, with 31 areas/1,744 turbines
held. Capacity totals remain unchanged. ABB Rev Q pp.21–24 resolve named
NETA-21 connector assignments and explicitly connect the optional NEXA-21
extension. No direct turbine compatibility or joint-table limits are inferred.
The Marne E103 appendix is excluded for its explicit reuse restriction.

## French network installations and Swedish residual check

The 07:35 iteration checks all 2,458 EOLIE rows in the official ODRE snapshot
of 31 August 2026 against national names/communes and existing French records.
The bounded cohort covers installations with industrial-service dates from
2022 and reported installed capacity of at least 1 MW. Thirty-four named
onshore installations pass the conservative identity screen. All retain
unresolved farm/phase/repowering scope and remain excluded from capacity totals.
Installed and maximum grid-injection ratings are separate observations.
Network groups are not turbine counts, HTA/HTB are not numeric voltages, and
administrative communes are not surveyed project coordinates. Native rolling
energy values retain their reporting-boundary limitations; no capacity factors
are calculated. See the dated decision ledger for every screened row.

All ten selected Swedish land layers return zero records for null IDs or
OMRID >= 2600, completing that partition scan. Deferred identities and offshore
coverage still require separate work. USWTDB alternate downloads returned
HTTP errors; no authentication or reuse prohibition is inferred.

The complete GE 4.2 MW-117m table adds one exact equipment configuration;
its published 4.23 MW nameplate is preserved separately from the model label.
Frequency-specific hub options stay nested, and the inadequately qualified
noise range is not promoted to a scalar sound-power value. The Vestas 4 MW
brochure is excluded under its explicit final-page reuse restriction.

## Regulatory decisions and hybrid boundaries

The BOE adapter reviews Series A notices mentioning wind, including decisions
about associated solar plants or auxiliary supplies. It requires complete
reviewed selections and checksummed originals before staging records. Its
synthetic offline tests reject title-based capacity inference, missing notices,
duplicate identities and cancellation of a wind farm from a solar decision.

The Spanish continuation adds five project identities from four complete daily
title partitions and two supplemental notices. Final and superseded proposals,
withdrawals, conditional environmental declarations and construction permits
remain distinct. Conflicting geometry and electrical fields stay null with
original observations retained. Unknown operating status is not converted to
zero capacity. All new farm/phase scopes remain excluded from capacity totals.

The shared viewer's expandable metadata exposes `boe_procedure` and field
sources; the offline Wind example prints decision target, dated wind status,
capacity categories and exclusions. A solar/auxiliary decision cannot be read as
a wind commissioning event. The BOE partitions are not a national wind census.


## NEM survey and small-wind certification batch

Batch `2026-11-04-2135` adds 67 projects and nine exact equipment models.
AEMO's October 30 workbook supplies the complete wind partition with survey IDs
below 2000: 158 generating-unit rows at 125 survey sites. Sixty-six distinct
sites are added; 59 name/alias/phase candidates are held for explicit crosswalks.
All new scopes remain excluded from capacity totals. Eight explicitly named
phases receive stable group links without additive parent rows. Individual
turbines and exact deployed models remain unknown. NEM coverage excludes
Western Australia and the Northern Territory; NSW1 includes ACT.

Reported unit aggregate AC nameplates are never multiplied by turbine counts.
Mixed lifecycle observations remain separated, shared hybrid-site dispatch limits
do not become wind capacity, and forecast commercial-use dates do not become COD.
The 24–26 September BOE partition adds El Tabaibal (ER150053), whose public-utility
modification establishes neither current operation nor a normalized capacity category.

The complete PNNL July 2026 table supports nine exact small-wind models, eight
manufacturer/applicant labels, and power at 11 m/s under standard sea-level
conditions. These are dated certification observations, not nominal model ratings
or independently validated field performance. Acoustic limits at 60 m are kept
separate from sound power; unknown rotor geometry precludes specific-power
comparisons. No numerical curves were available from this table.

The separate ICC-SWCC directory is excluded because its linked terms explicitly
restrict extraction and redistribution. AEMO's workbook downloaded successfully
although its landing page returned HTTP 403. These are distinct access/reuse outcomes.
The equipment target of 20 was not met; no unsupported variants were added.

See `research/2026-11-04-2135-source-review.json`, the AEMO candidate and decision
ledgers, and the PNNL transcription. Next: AEMO survey IDs 2000–2999, then
3000 and above; BOE September 21–23; OEM configuration documents for EOX S-16
and KW20/KW30. Prior reconciliation holds remain queued.


## NEM survey IDs 2000–2999 and small-wind OEM specifications

Batch `2026-11-04-2235` reviews all 111 survey sites in this half-open partition:107 additions and four deferrals. All additions remain excluded from capacity totals. Three explicitly named phases retain stable group IDs, including Goyder South1B linked to the earlier1A family. Twenty sites contain21 generating-block count placeholders; their physical turbine counts stay null, while original counts and reported AC capacities remain reviewable. Wooroora/Chalumbin lifecycle and Clarke Creek/Baldon phase scope remain held.

Five exact equipment models are added:SD3,SD3EX,SD6+,SD12 and the Powersync25 inverter. Existing Excel15 and SD6 identities gain geometry and qualified technical observations without replacing PNNL power at11m/s. SD3EX3/2.5kW observations conflict, so its scalar is null. SD6+ power depends on unspecified inverter settings. Powersync25 factory20kW,table23kW and field-adjusted25kW limits are separate. Nominal and11m/s ratings are excluded from a common nameplate-density comparison. No graph is silently digitized.

Kodair pages were acquired but excluded under explicit republication terms. Eocycle page/PDF returned403; this is a download failure, not an authentication or reuse finding. Complete source decisions, count quarantine IDs, checksums and exact continuation partitions are in the batch research files. The20-equipment target was not met; no variants were invented.


## Final NEM partition, local BOE reconciliation and Goldwind tables

Batch `2026-11-04-2335` adds32projects and15exact equipment models, and enriches one historical project and two existing equipment records. Branch totals are8,168projects (8,167non-group),372equipment,13,633turbines and two numerical curves across59countries. The full AEMO October2026 wind selection is exhausted:269sites/309units,198accepted identities and71deferred. This final33-site partition adds25sites, holds eight overlapping identities, and quarantines twelve count placeholders; all accepted survey scopes remain excluded from capacity totals. BullawahStage2 shares the existing Stage1 family identifier.

The complete September21–23 BOEA/B daily partition yields Ferromolín PEol-1023:27planned MW, six proposed turbine positions, five separate reserve locations and a qualified material-execution budget. A separate2024BOE local inventory within10km of Martelilla yields six additions and one CortijoI historical-record reconciliation. The eight-entry list totals214.07MW arithmetically versus the reported214.04MW; the regional total is not imported. Castella expansion remains held. CortijoI40.8MW and its1.2MW expansion are distinct excluded scopes; PNE42MW and14turbines are not assigned to either. None is presented as a current operating census.

Goldwind2025Q3 provides15explicit turbine columns, including table-reported165.8m and183.5m rotor diameters. Generator/converter voltages,50/60Hz choices, hub options, design life, operating/survival temperatures and environmental declaration claims retain their separate meanings. No unnamed component models or numerical curves are invented. SD3EX now retains three incompatible ratings3.2/3/2.5kW with a null scalar. Powersync25 gains exactPS25-240-1B identity, trip thresholds, enclosure and installation limits; conflicting inrush/fuse statements remain qualified. The viewer distinguishes offered hub options from scalar heights and unknowns.

The50-project and20-equipment objectives were not met:33projects and17equipment were substantively changed. Completed source partitions, field holds and original-byte hashes are in the research ledgers. No repeated source imports or synthetic variants pad those counts.

## Polish project reconciliation and original environmental declarations

Batch `2026-11-04-2435` adds six Polish projects and enriches the historical
Karcino record. All seven queued Polish references have now received detail-page
review. Legnica's 2026 sale is separate from its planned 2030 commissioning.
Kuślin and Krzęcin II retain 2020 project-company, auction, permit and electrical
scopes alongside later launch observations. Proposed layout IDs are not installed
turbine records. Karcino's 2009 historical year and 2010 developer launch remain
separate; the owner confirms Karcino and Karścino are different acquired assets.
All six additions and the enriched historical scope remain excluded from totals.

Original EPDITALY0508 and EPDITALY0852 declarations enrich seven existing Goldwind
models. The recurring adapter pins original bytes, requires the complete explicit
model set and preserves all earlier evidence and creation timestamps. Four swept
areas and one design-life scalar are null pending revision reconciliation. Blade
labels without explicit model allocation and unnamed components remain nested.
No compatibility is inferred from a list's order or similar model codes.

Ten modeled lifetime-generation scenarios retain their individual turbine,
net-to-grid boundary, location and 20/25-year exposure. Egypt and Tanzania are
exemplary LCA sites, not new operating projects. The viewer and offline example
show these scenarios without summing them, deriving capacity factors or calling
EPD verification independently validated turbine performance. No new curves.

All September 17–19 BOE A/B indexes were reviewed: zero wind notices. Hargraves'
primary developer page was acquired, but its three AEMO identities remain held
without an explicit registry crosswalk. Next: September 14–16 BOE issues, the
Wimmera stage boundary, Jasna's exact installed fleet, and original Goldwind
revision/type-certificate evidence. See the dated research ledgers for hashes,
field locators and unresolved observations.

## Dated EIA generator observations

The complete final-2025 EIA wind **Retired and Canceled** tab contains 172 rows
across 129 plant codes. It is not a complete historical retirement census.
58 existing U.S. project identities receive 82 dated generator observations;
71 identities remain deferred, including five code matches with name/location
discrepancies. Whole-farm status, historical capacity, repowering boundaries and
aggregation exclusions remain unchanged. The canonical extension retains row
locators, original quantities, month/year dates, net seasonal versus nameplate
MW, representative heights and predominant model labels. Those labels do not
create exact OEM equipment or individual turbine records.

`wind_catalogue.eia.parse_retired_partition` verifies original workbook hashes,
reporting year, headers, wind prime movers, statuses and unique identities.
`enrich_retired_partition` requires an explicit reviewed crosswalk plus matching
WRI-encoded EIA code, normalized name and coordinates. Replaying a source
revision is idempotent; changing it under the same source ID is rejected.
The shared project viewer reports unit observations independently of farm
lifecycle and current capacity. The deterministic gallery prints their reporting
year and unchanged scope exclusions.

EIA's workbook calls its speed field “Design Wind Speed”; its instructions ask
for representative annual average speed. Both descriptions are retained, with
measurement method, dates and height unknown. No measured/design performance
comparison or capacity factor is inferred. Sources: final-2025 EIA-860 and the
pinned WRI U.S. importer/identity helper (`eia860_2025`, `wri_usa_identity`).

The EIA adapter also accepts an inclusive `operable_range=(low, high)` plant-code
partition. The complete 1–60999 range is reviewed; 61000–61999 is next. Operating,
out-of-service and standby generator observations remain distinct in the shared
viewer and existing deterministic example. None establishes whole-farm current
operation, reconciles repowering, or promotes predominant model labels to exact
OEM equipment. The original final-2025 workbook bytes are reused and rechecked.

The 52000–55999 continuation reviewed all 61 plants / 67 generator rows in four
complete numerical partitions, including the empty 53000–53999 partition. It
adds dated evidence to 53 existing projects and holds eight unresolved identities.
The adapter rejects identical unit observations imported through overlapping
source aliases. Distinct tabs and revised observations remain separate. Viewer
cards separate reporting years; `windEiaSummary(rows, year)` can select one year
without treating absent observations as zero generating capacity.

The complete 56000–56999 partition adds evidence to 298 existing projects from
307 reviewed plants / 363 generator rows; nine identities remain held. Revised
source observations can retain changed and unchanged units together without
overwriting prior observations. Identical whole-plant partitions remain rejected
when submitted under a second source alias.

The complete final-2025 Operable 57000–57999 partition reviews 266 plants and
290 generator rows: 258 existing project identities enriched and eight deferred.
Reported generator observations do not change farm capacity or lifecycle totals.


The complete final-2025 Operable 58000–58999 partition reviews 143 plants and
173 generator rows: 132 existing projects enriched and 11 unresolved identities
held. Original generator nameplates, seasonal net capacities, predominant model
labels, representative hub heights and grid context retain their source rows and
units. No whole-farm status, scalar capacity or aggregation eligibility changes.

A dated Nordex announcement adds the N175/6.X 7.3 MW mode and German tower
observations to the existing equipment identity (`nordex_n175_update_20260422`).
The 162.5 m hybrid tower was under development on 22 April 2026, with approval
scheduled for Q2; this is not evidence that approval or delivery occurred.
The same announcement reports Max Bögl's 179 m tower approval on 21 April.
These options remain in `extensions_json.oem_product_updates`; prior scalar
specifications and provenance are preserved. The shared viewer counts dated
updates and models without this evidence. The offline example prints the modes,
tower conditions and dates without creating model variants or assuming installed
compatibility. No common-condition numerical curve or independently validated
performance is established by the announcement.

The complete final-2025 Operable 59000–59999 partition reviews 105 plants and
114 generator rows: 95 existing projects enriched and ten identities deferred.
All prior scalar facts, source observations and capacity exclusions remain unchanged.

The complete final-2025 Operable 60000–60999 partition reviews 75 plants and
85 generator rows: 70 existing projects enriched and five identities held.
The queued V82 archive power/Ct table remains deferred: its metadata labels it
theoretical, provides no reference links and omits air density and operating mode.
No conditions are reverse-engineered from Cp and no OEM curve is added.

The complete final-2025 Operable 61000–61999 partition reviews 85 plants and
100 generator rows: 67 existing projects enriched and 18 identities held.
Jasna gains a dated mixed-fleet observation: 22 V126 turbines reported at
3.45 MW and 17 at 3.3 MW. The arithmetic check is separate from reported
132 MW, and no exact OEM revision or individual turbine identity is inferred.
March 2021 commissioning-in-progress remains distinct from the prior launch label.

The complete final-2025 Operable 62000–63999 partitions review 146 plants and
161 generator rows: 36 existing projects enriched and 110 identities held.
Karcino gains the operator's dated history: turbine installation began in 2009
and commissioning occurred in 2010. The historical WRI conflict remains visible.
The operator's 120 GWh/year statement has no named observation year or method;
it is not used to calculate capacity factor or presented as measured output.


### Reviewed OEM history tables

The `wind_catalogue.history.stage_history` adapter accepts a reviewed factual
transcription plus checksum-matched original bytes and a complete expected row
inventory. It preserves printed rating ranges, dated remarks and tower options
inside one type record. Explicit rating versions remain distinct; inferred
Cartesian variants are rejected by the review workflow. Existing models and
contradictory type/rating/unit rows remain in the decision ledger for separate
revision review. An OEM history table does not independently validate performance
or establish present-day availability. The November 5 Nordex transcription and
all 46 decisions are retained under `catalogues/wind/research/`.

EIA registry-site additions require independent identity review before staging.
All generator observations remain nested with their original annual boundaries;
missing farm capacity stays null. The shared viewer and offline example show
unknown installed farm MW and unresolved aggregation scopes separately.


## Dated OEM history and identity review (5 November, 09:10 batch)

The 56 new US sites come from exactly 142 saved EIA identity holds, with 86
remaining deferred. Generic words no longer dominate name screening. Existing
IDs, aliases, geodesic proximity and candidate-to-candidate proximity are reviewed
separately. A clear screening result does not establish a physical farm boundary;
all additions retain unknown farm lifecycle and capacities, with unresolved
aggregation scope. The final-2025 Operable workbook scan is exhausted: 1,573
rows, maximum plant code 69,327, no residual code at or above 70,000.

Nordex's dated 12 June 2025 retrospective supplies 31 exact-model enrichments.
Prototype pitch and generator details apply to those prototypes. Discontinued
production is a dated OEM claim and says nothing about installed-fleet retirement.
The shared viewer counts these observations separately from current configuration
fields, and the deterministic gallery prints their dates and boundaries.

The hash-pinned transcription adapter requires an explicit ID/manufacturer/model/
rating crosswalk and complete reviewed mapping. Identical replay preserves update
timestamps; changing the same source observation is rejected. Scalar facts and
creation timestamps are unchanged. The N175 narrative's 200 m maximum and the
undated table's 199 m maximum remain separate observations. The N27 type/rating
reversal and N169 printed-unit conflict remain deferred after reviewing independent
dated OEM articles. A lone AW77/1300 narrative mention is held for original
specification evidence. No new numerical curves or installed model variants are
inferred from this history.

## Published reference yields and saved EIA holds (5 November, 09:45 batch)

Exactly 110 saved EIA holds from plant codes 62000–63999 were reviewed: 52 new
registry sites and 58 remaining identity holds. The 36 previously enriched sites
were not counted again. All new farm capacities and lifecycle states remain
unknown and excluded from totals. Oregon PUC's UM1401 report confirms one shared
LGIA involving Orchard Windfarm I, 2, 3 and 4; it does not supply the EIA crosswalk
or resolve their physical boundaries, so those four candidates remain held.

FGW's current index supplies complete Nordex tables for the old and new reference
sites: 110 and 70 rows respectively. They add 16 explicitly printed types/revisions
and enrich 24 existing equipment records. Hubs and power settings stay nested,
including 173 accepted row observations; seven N27 rows remain in the conflict
ledger. Five withdrawn N149 yields are retained alongside replacements with the
publisher's withdrawal and replacement dates. Three missing rotor cells stay null.
Existing scalar specifications are unchanged when reference-table geometry differs.

The offline `wind_catalogue.reference_yield.stage_reference_yields` adapter checks
original-byte hashes, complete row inventories, explicit record-ID crosswalks,
positive finite quantities and restriction notes. Identical replay preserves
creation and update timestamps; changed observations under the same source ID
are rejected. Original decimal-comma/thousands-dot strings remain reviewable.

FGW defines these quantities as calculated five-year energy in kWh. They describe
hypothetical reference sites, not measured plant generation. Old-site logarithmic
and new-site Hellmann profiles are kept separate; density, operating mode and
gross/net boundary remain unknown. No annual generation, capacity factor or
numerical power/Ct curve is inferred. The shared viewer and deterministic gallery
show counts by reference site, withdrawn observations and missing evidence without
summing yields or presenting an unsupported performance comparison. Paid reference
certificates are separate from the freely readable published tables.

## Korean certificate configurations and Salinas III proposal (5 November, 14:35)

The remaining 55 rows of the checksum-pinned KNREC register are now reviewed:
23 certificate-scoped equipment configurations are added and 32 rows await
revision crosswalks or conflict resolution. Together with the prior two HTq rows,
all 57 registry rows have a recorded disposition. Multiple power and hub values
remain options within one record, never Cartesian variants. Printed expired
notes are retained; blank status does not establish current certification validity.
The shared viewer and offline gallery distinguish these registry observations
from independent performance validation. Six new OEM labels retain original
Korean company names without inferring corporate succession.

BOE daily indexes for 14–16 September 2026, including both Series A and B and
any linked extra issues, yield one new wind-only proposal: Hibridación FV-PEol
Salinas III (PEol-FV-313). Its reported 36 MW planned capacity, eight explicitly
identified proposed turbines, 118 m hubs, 163 m rotors, 30 kV underground
collection and EUR 39,576,856.27 material-execution budget are source-qualified.
The budget price year is unknown. Existing PV capacity and the proposed hybrid
total are separate observations. Public consultation establishes neither approval
nor installation. The eight annex turbine IDs link to the proposed parent, with
unknown coordinates. The named base V163 model is recorded as a relationship;
an exact equipment-configuration link remains unset because the planned 118 m
hub differs from the existing OEM page's published hub options. Private landholder
names are not copied. Taraguilla's paragraph-number correction was already
retained and is counted as duplicate evidence, not an enrichment.

REPD offsets 600–800 received structural review only: all 200 applications remain
identity holds, with no claim that original permit contents have been reviewed.
No capacity aggregation exclusion is lifted. All earlier records and creation
timestamps remain unchanged. See the dated KNREC, BOE and REPD decision ledgers
in `catalogues/wind/research`; the continuation cursors are in `backlog.json`.

### Brazil: dated ONS unit evidence

The first 100 lexically sorted wind CEGs in the ONS daily file retrieved on
2026-11-05 contain 66 exact historical WRI identifier/name matches and 34 identity
holds. The WRI Brazil importer explicitly encodes the six-digit numeric CEG
component as `BRA` plus seven digits. The adapter additionally requires one
historical identity, exact name agreement after case/whitespace normalization,
and no competing CEG version anywhere in the file. Missing identities stay held.

The source dictionary calls `val_potenciaefetiva` **nominal generating-unit MW**.
Unit rows may represent turbine groups. Nested observations retain the original
values, owner/operator, state, subsystem, operation modality, release-for-test,
release-for-commercial-operation and deactivation dates. Missing dates remain
null; retrieval and metadata modification dates are not observation dates.
No unit count becomes a turbine count, release date becomes farm commissioning,
or unit MW becomes whole-farm installed capacity. All 66 historical aggregation
and lifecycle exclusions remain. The shared viewer and offline gallery count
unit evidence and distinguish missing nominal ratings from reported zeros.

This is an ONS-dispatched-unit partition (modalities I/II-A/II-B/II-C), not a
current operating census of Brazilian wind farms. Original CSV/dictionary hashes,
per-row locators, candidate decisions and the next exact CEGs are in the source
registry and `research/2026-11-05-1510-ons-review.json`. The daily source has no
historical archive guarantee; continuation must use the pinned bytes or explicitly
record a replacement snapshot and reassess partition boundaries.

The next five complete 100-CEG partitions (offsets100–599 of the same pinned
snapshot) add 99 existing-project enrichments and retain 401 identity holds.
The first600CEGs are now reviewed; no source release or lifecycle is silently
advanced. Adjacent-partition tests ensure complete multi-unit CEG groups are
neither split nor duplicated. The gallery also reports source-state coverage
as snapshot counts, never as installed capacity.

The final 482 CEGs (offsets 600–1081) add 175 project enrichments and retain 307
identity holds. The pinned scan is now complete: 1,082 CEGs reviewed, 340 matched
historical projects and 742 unresolved identities. Completion describes this
source partition only. The resume auditor rejects gaps, overlaps, incomplete
terminal groups and changes of source hash or retrieval version. The viewer and
gallery count each project once per reported state across its observations;
unknown geography remains visible and no current fleet distribution is implied.

### Goldwind Americas 2.5 MW tables

The complete English three-model and Spanish two-model tables support three
explicit models: GW 100/2500, GW 109/2500 and GW 121/2500. Shared table cells are
applied only to their printed columns. Spanish edition details remain nested,
with their own provenance and units, because option/revision equivalence is not
established. Hub choices are not expanded into additional models.

Original reported swept areas and diameter-based checks are retained separately;
uncertain area scalars remain null. GW 109/2500 also retains the English static
10.5 m/s and Spanish unqualified 10.2 m/s observations with a null canonical rated
wind speed. Neither brochure resolves the Korean certificate's 107.5 m rotor
crosswalk. The five plotted power curves are graph-only, with density stated but
mode unresolved; no numerical curve, compatibility claim or independently
validated performance is inferred. See the 1735 OEM decision ledger and source
registry for checksums, exact page/column locators and continuation tasks.

### Dated EPE-hosted SIGA and Spanish proposal observations

The 2026-11-05 continuation reviews the complete **381-entry Bahia wind
partition** of EPE's hosted SIGA layer, whose dataset date is **2026-01-13**.
Repeated object-ID queries agreed before and after all pages were acquired.
Sixty-eight entries enrich existing projects through a unique WRI-encoded CEG
identity plus exact name; 313 identities remain deferred. The original CEG
spelling is retained, with only numeric suffix padding compared. The layer's
misleading date-typed `idenucleoceg` field is not used as an identifier.

Authorized kW, inspected kW and physical-guarantee kW are normalized separately
to MW inside dated observations. Physical guarantee is not installed capacity.
Original lifecycle text, operating-entry date, permit term, ownership text,
municipality and registry-point coordinates remain qualified by their source.
Coordinate decimal precision is not positional accuracy. None of these
observations changes canonical capacity, lifecycle or aggregation eligibility.
The shared viewer and deterministic gallery show category completeness,
including reported zeros and unknown values, without summing incompatible MW.
This successful public EPE ArcGIS download is independent of the earlier
ANEEL CSV HTTP 503 failure; neither failure implies authentication or a reuse ban.

BOE Series A/B issues of 10–12 September 2026 yield two proposed Salinas wind
modules, each 36 MW with eight individually identified planned turbines, and
the archived 144 MW Alto Cabrera application. Proposed wind MW, existing solar
MW and combined hybrid MW remain separate. Alto Cabrera's whole-project status
is unknown: dismissal of application PEol-382 does not establish the fate of
all possible iterations or appeals. Salinas electrical length/conductor
inconsistencies and the unresolved 118 m OEM hub configuration are retained.
The solar-only environmental notice remains an identity hold, and the generic
cadastral notice is excluded. Private landholder names are not imported.

Four exact Goldwind 1.5 MW brochure models are added, and two existing 2.5 MW
models receive separate digital-English edition observations. The latter
explicitly distinguishes survival from operating temperature. Printed rotor
areas and earlier rated-speed disagreements remain qualified observations;
unresolved scalars stay null. Six graph-only curves are deferred, with no
numerical points or synthetic variants created. These are manufacturer
specifications, not independently validated performance.

Sources: [EPE SIGA layer](https://gisepeprd2.epe.gov.br/arcgis/rest/services/Hosted/SIGA_Eolica_Solar/FeatureServer/0),
[Goldwind 1.5 MW original](https://www.goldwindamericas.com/sites/default/files/Goldwind-Brochure-1.5-Web.pdf),
[Goldwind 2.5 MW digital original](https://www.goldwindamericas.com/sites/default/files/GW%202S%20MW-ENG-DIGITAL.pdf),
[Alto Cabrera notice](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-19045),
[Salinas II notice](https://www.boe.es/diario_boe/txt.php?id=BOE-B-2026-29433) and
[Salinas I notice](https://www.boe.es/diario_boe/txt.php?id=BOE-B-2026-29434).
Full bibliographic metadata and stable source identifiers are in the reference catalogue.

### Rio Grande do Norte continuation and bounded OEM review

The complete **317-entry Rio Grande do Norte** EPE wind partition is now reviewed.
The before/after ID inventories agree, and both response pages are complete.
**107 existing projects** gain dated observations; **210 identities remain held**
(200 missing or nonunique historical matches and 10 ID/name disagreements).
The dataset date remains **2026-01-13**, distinct from retrieval on 2026-11-05.
Authorized capacity, inspected capacity and physical guarantee remain separate
observations. All six eligible capacity summaries are unchanged. Suspicious
source operation dates, including Macau's 1900 date, stay in the original
observations and are not promoted to commissioning milestones.

The adapter now rejects a CEG revision change against prior EPE evidence even
when the project has no scalar ANEEL identifier. A real two-row RN fixture tests
separate capacity categories, reported zero and the suspicious date boundary.
The shared viewer and deterministic gallery show distinct linked projects by
state and dataset date, with unresolved identities and aggregation exclusions
visible. This is selected evidence coverage, not a current operating census.

Three exact Windey model records are added: **WD200-7700 (Saudi 60 Hz)**,
**WD220-10000**, and **WD225-9000**. Their explicitly reported unit ratings are
7.7 MW, 10 MW and 9,000 kW respectively. Detailed configurations are partial;
rotor diameters are not inferred from model names. Twelve OEM case cards and
two further announcements remain queued for project, revision or certificate
crosswalks. The Saudi configuration is not assigned to the Ethiopian proposal.
No numerical curves or independently validated performance are added.

Bachmann's component tables and case study are excluded under its explicit
prior-consent reuse terms. Delta's proposed PDF redirects to a terms-verification
page with an internal-use restriction; the original PDF was not acquired.
Ingeteam's two historical document links redirect to homepage HTML. These are
recorded separately from authentication or HTTP download failures. Windey's
large-image timeouts were resolved, with all four original image checksums saved
in the review ledger. The equipment target was not met by inventing variants.

This run adds **0 projects, 3 equipment records, 0 individual turbines and
0 curves**, and enriches **107 projects**. Branch totals are **8,294 projects,
489 equipment records, 13,657 turbines and 2 curves** across 59 countries and
64 equipment-manufacturer labels. The next registry batch is the complete
EPE **CE** partition; previously completed BA/RN and ONS partitions stay closed.

Sources: [EPE SIGA layer](https://gisepeprd2.epe.gov.br/arcgis/rest/services/Hosted/SIGA_Eolica_Solar/FeatureServer/0),
[Windey product cases](https://windeyenergy.com/en/product_show?id=19),
[Windey Saudi announcement](https://windeyenergy.com/en/news_show?id=210).
Decisions and original-byte checksums are in
`2026-11-05-1935-epe-review.json` and `2026-11-05-1935-oem-review.json`.

The November 5 20:35 continuation reviews all 103 Ceará EPE wind entries,
linking 53 existing identities and holding 50 for a historical/phase crosswalk.
The dated categories do not change capacity eligibility. BA and RN partitions
are already complete; the next complete EPE partition is RS.

The Windey June 2022 English brochure contributes 31 exact models and one
historical observation for the existing WD225-9000. PDF pages 7, 8 and 12
(printed 09/10, 11/12 and 19/20) contain 32 explicit columns; pages 9–11 remain
queued. The checksum-pinned `oem_tables` adapter consumes visually reviewed
columns and rejects missing, reordered or duplicate identities. Generator RPM
and converter kVA stay separate from rotor RPM and turbine kW. Temperature,
cut-out and hub-height ranges remain options; the viewer and gallery expose
these without claiming installed configurations or validated performance.

### Complete Rio Grande do Sul partition and remaining Windey columns

The November 5 21:35 continuation reviews all **80** EPE-hosted SIGA wind
entries for Rio Grande do Sul. Stable before/after OBJECTID queries and the
complete response agree. **67 existing projects** gain dated native registry
observations; **13 identities remain held**. No projects, individual turbines,
capacity eligibility or lifecycle claims are inferred. All six capacity
summaries, including unknown and excluded counts, remain unchanged.

The remaining Windey brochure tables on PDF pages **9, 10 and 11** (printed
13/14, 15/16 and 17/18) add **35 exact models**. All **67 printed model columns**
on PDF pages 7–12 have now been reviewed across two batches. The prior source
registry and original-byte checksum remain intact; the new review ledger records
expanded locators and visual transcription. These are historical specifications,
not independent performance validation or installed project configurations.

Column boundaries matter: WD164-3600 states a converter range of 47.5–51.5 Hz,
while the other 34 newly reviewed columns state 47.5–52.5 Hz. WD172-5500's
80.5 m blade length is retained as printed, without replacing it using another
172 m rotor model. Generator kW/RPM, converter grid-side/turbine-side kVA and A,
component mass/dimensions, hub-height options and operating conditions remain
separate observations. Exact component model IDs, density, operating mode,
warranty, certification identifiers and numerical curves remain unknown.

The offline adapter now rejects malformed component quantities and vectors.
Small attributed fixtures exercise column-specific values and unit boundaries.
The shared viewer counts usable converter rating pairs separately from missing
ones, rejects malformed hub ranges, and explicitly separates component quantities
from turbine ratings. The gallery dynamically displays the reviewed model count.
The next complete EPE partition is **PI**; the next OEM/project work is the
AfDB Aysha I original ESIA and exact phase crosswalk recorded in the backlog.

### Piauí registry continuation

The November 5 22:35 batch reviews the complete 126-entry EPE Piauí wind
partition, with stable before/after object IDs and original response checksums.
Thirty-six existing identities receive dated registry observations; ninety
remain held. No current operating status, new farm or capacity eligibility is
inferred. The existing state-coverage gallery and viewer now include Piauí.

Replay the reviewed ledger without changing the catalogue:

```bash
uv run python scripts/replay_wind_epe.py catalogues/wind/research/2026-11-05-2235-epe-review.json
```

The command rejects changed observations or changed identity decisions. Next is
the complete Pernambuco (PE) partition. Independent Aysha I follow-up located
IFC project 49251 and obtained the operator-hosted ESIA original; detailed phase
and equipment reconciliation remains pending. No equipment is added from model
names or marketing claims, and no completed Windey table is rescanned.

### Pernambuco, Paraíba and Santa Catarina continuation

The November 5 23:35 iteration reviews three complete EPE-hosted SIGA wind
partitions dated January 13, 2026: Pernambuco 46 entries (31 linked, 15 held),
Paraíba 42 (12 linked, 30 held), and Santa Catarina 18 (10 linked, eight held).
It enriches 53 existing projects with separately qualified registry observations.
No project, turbine, equipment or curve is added. All capacity summaries and
historical baseline exclusions remain unchanged. The 50-project objective is
met; the 20-equipment objective is not met.

The shared viewer now counts unresolved scope and unknown lifecycle among
projects with SIGA evidence. The deterministic gallery compares linked versus
held identities for complete selected state partitions. Neither chart represents
a current national operating inventory. Completed states are not rescanned.

Original response verification is optional and read-only:

```bash
uv run python scripts/replay_wind_epe.py catalogues/wind/research/2026-11-05-2335-epe-review.json --originals /path/to/original-responses
```

This verifies SHA-256 for every retained response, reparses both ID queries and
all pages, and compares the complete candidate transcription before replaying
accepted records and decisions. Missing files, changed bytes, drifting IDs and
changed transcriptions fail. Original bytes stay outside Git; URLs, hashes and
review decisions are committed.

Independent Aysha I research found unresolved dated capacity observations:
IFC's August ESRS reports 300 MW; its October investment disclosure reports
300.3 MW; MIGA's portfolio identifies 306 MW. MIGA portfolio Phase II is not the
Aysha II wind farm. IFC describes a May ESIA but lists a June attachment; that
original attachment remains unavailable for revision comparison. These are
research holds, not canonical capacity replacements or exact equipment links.
IFC HTML HTTP 403 and missing attachment links are access limitations, not
assertions of authentication or reuse restrictions. Next: Maranhão's complete
EPE partition and the exact IFC June ESIA attachment/phase crosswalk.

### Completing the captured EPE roster

The November 6 00:35 batch reviews MA (16 entries) and MG, PR, RJ, SE and SP
(one each). Two existing projects gain dated registry evidence (RJ and SE);
19 identities remain held. Thirteen remaining states return explicit empty ID
lists. A separate null/unknown-state query is empty. Two national ID queries
agree on 1,134 entries, exactly matching the disjoint union of all 27 reviewed
state partitions. Across this captured layer, 386 entries are linked and 748
are held. This establishes source membership coverage, not a current Brazilian
operating census or completeness of all Brazilian wind assets. No capacity
eligibility changes; the 50-project and 20-equipment objectives are not met.

```bash
uv run python scripts/replay_wind_epe_coverage.py catalogues/wind/research/2026-11-06-0035-epe-coverage.json --originals /path/to/original-responses
```

The coverage check verifies reviewed candidate IDs, original query checksums,
explicit empty states, disjoint partitions and matching national rosters.
Missing/null/error/truncated responses are unknown, never zero. The offline
fixture preserves an actual empty AC response. The gallery lists these empty
partitions separately; the viewer distinguishes valid source registry points
from absent coordinates, without borrowing historical WRI points or treating
coordinate precision as positional accuracy.

BOE September 7–9, all discovered Series A/B issues, yields two held notices:
[Viento de Sellía parcel correction](https://www.boe.es/diario_boe/txt.php?id=BOE-B-2026-29194)
and [Colladillo/Cabeza de Mesá solar hybridization](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-18893).
Neither supplies an accepted wind identity crosswalk or complete turbine inventory.
Original notice and index checksums are retained. Exact IFC June ESIA and
WD230-11500 certificate searches did not locate the requested originals; prior
announcements are not counted again. Next: BOE September 4–6 and the saved MA
Delta 3 identity/phase crosswalks. Completed EPE partitions stay closed.

### September 4–5 BOE modification and repowering decisions

The November 6 01:35 continuation adds Alcocero de Mola's revised 78 MW
proposal and the separately authorized 5 MW Boyal I and Boyal II replacement
generations. All three remain excluded from capacity totals. Environmental
clearance alone does not establish construction permission; repowering
permission does not establish replacement operation. Boyal's historical 4.5 MW
units, proposed 5 MW units, 4.5 MW grid access and reported 15 MW transformer
active-power limit remain distinct. No anonymous turbine children or exact
installed OEM configurations are inferred.

The original Alcocero notice reports 197.92 m tip height versus 197.5 m from
hub plus radius, and 1,371 m of line versus 1,370 m of listed segments. Both
observations are preserved. Boyal II repeats a Boyal I AESA reference; no permit
identity is silently corrected. September 6 returned HTTP 404 and is not a
completed empty issue. Next daily partition: September 1–3. The saved Delta 3
crosswalk remains held after the original ANEEL notice returned HTTP 403;
this is not evidence of authentication or a reuse restriction.

### Complete daily issue replay

`review_daily_indexes` verifies all discovered ordinary and extraordinary issue
URLs before returning Series A/B wind-title candidates. Missing issues fail even
when the default page has no candidates; identical notice aliases are deduplicated
and conflicting titles are rejected. This is title-scan completeness, not a wind
project census. The September 1–3, 2026 scan includes both September 2 issues and
returns no candidates. See `2026-11-06-0235-review.json` for source hashes and the
separate, unresolved Wimmera survey/permit phase review.

### Original refusal history and permit envelopes

The August 27–29 and 31, 2026 BOE batch enriches Satrebares from its original
refusal notice (BOE-A-2026-18277), preserving the later geography correction.
Application/hearing dates, the received grid-access expiry notice and electrical
proposal observations do not describe installed assets. The adapter rejects
operational, permitted or retired status inferred from an application refusal.
The Valdepero solar and Frontones battery notices are not new wind capacity.
Wimmera's acquired PA2000877-2 permit provides upper/lower dimensional limits,
not exact turbine configurations or AEMO phase allocations. Its amendment date
is May 14, 2026; May 19 is the attachment filename date. See the 0335 review ledger.


### Construction authorization and proposed equipment

The 6 November continuation adds Somaloma–Las Quemadas from
BOE-B-2026-27717: authorized capacity remains planned capacity, separately from
grid access and commissioning. The offline adapter rejects operating status
inferred solely from construction authorization. The proposed fleet is complete
as a model/count observation, not an individual-turbine or as-built inventory.
Permit rotor diameter and OEM product geometry remain separately scoped pending
an exact revision crosswalk; no synthetic hub-height configurations are created.


The Peñaflor consultation records only the wind proposal's 49.5 MW. Its solar
partner's 113.42 MW and shared grid permission are separate observations; the
works estimate has an unknown price year. Unknown lifecycle status cannot bypass
the adapter's prohibition on treating consultation MW as installed capacity.


Assessment design envelopes are source/revision-qualified observations, separate
from scalar rotor diameter, hub height and selected turbine count. The shared
viewer reports envelope coverage alongside unknown and reported-zero scalar
geometry. The gallery shows the original ranges and conditions. Aysha I's June
2026 lender envelope does not establish an OEM configuration; conflicting ESIA
ratings and financing-capacity observations remain unresolved. No range endpoints
are multiplied into synthetic variants.

A BOE environmental decision can require turbine removals. The reviewed adapter
rejects original or arithmetically reduced scalar fleet/capacity values when the
notice imposes removals; the revised design needs separate review. Maira Delta
and Gamma retain their original proposals, explicit removal lists and labelled
arithmetic checks, with final capacity/count null. Final environmental curtailment
conditions are project constraints, not OEM cut-in speed specifications.

The November 6 07:35 batch completes BOE August 6–8 discovery across all
available daily issues. Pasama and Aquarii are withdrawn wind applications;
Taraguilla is an unchanged previously recorded project. The three solar-hybrid
refusals remain wind-identity review candidates, without cancelling their wind
plants or transferring solar MW. Pasama’s former joint procedure with Cerro de
Magaña does not establish a parent/phase relationship.

Aysha I now retains Windey’s August 19 supply-award announcement alongside the
June lender design envelopes. The WD200-7700 mention does not select the Saudi
60 Hz equipment configuration already in the catalogue. The shared viewer and
executable gallery display dated awards separately from installed fleets.
The OEM’s prospective 1,189 GWh/year is a modeled project observation with
unspecified gross/net boundary and calendar period; no capacity factor is
computed. Exact configuration, turbine count and conflicting project MW remain
unresolved. Specifications and announcements are not independently validated
performance.

The November 6 08:35 batch completes BOE August 3–5 and adds Cerro de Magaña
under PEol-898. Its former joint administrative procedure with Pasama does not
establish a parent, a phase or additive capacity. The 50.1 MW withdrawn proposal
stays excluded from capacity totals. Body and title locality differences remain
explicit; no coordinates or OEM equipment are inferred.

The pinned REPD Q2 2026 candidate partition 800–999 has been structurally reviewed.
All 200 identities remain held pending original permit and physical-site
crosswalks. These are application observations, not 200 additional farms.


## Floating prototype and OEM numeric tables (6 November, 09:35 UTC)

The complete discovered BOE July 30–31/August 1 A/B partition yields WHEEL's
preliminary authorization and San Jorge's refused wind application. Neither is
installed capacity. Two solar decisions remain held for wind identity crosswalks.
WHEEL is linked to its exact PLOCAN pilot substructure configuration, supported
by the original 2025 environmental decision and 2026 authorization. Floater
seabed elevation (−90 m, Port of Las Palmas datum), approximate 100 m anchor
depth and 70 m minimum selection criterion remain different quantities.
Construction authorization is expressly conditional; port fabrication is not
proof of installed offshore operation. The shared PLOCAN 15 MW grid access is
not added to the prototype's 6 MW design. ELICAN is a shared terminal, not an
inferred parent or phase. No exact turbine model was supplied in these notices.

All eleven exact types in SANY's global English navigation were reviewed.
Ten models are added; SI-16840 is held against the existing India configuration
pending a revision and legal-entity crosswalk. The numerical table adapter
requires a complete explicit model list, units, source and locator, and preserves
missing cells. Three inconsistent cells remain null: SI-16850 cut-out speed,
and SI-18572/SI-19580 swept area. Circular-area arithmetic is a labelled check,
never a replacement specification. Generator voltage is not grid voltage;
operating and survival temperatures are separate. IEC claims are not verified
certificates; specifications are not independently validated performance.

The OEM's original endpoints returned HTTP 508 with empty bodies. Public indexed
OEM tables supplied the evidence; original-byte checksums, publication dates and
revisions remain unavailable. No authentication or reuse restriction is inferred
from the failure. Unnamed blade and generator platform ranges are held. The
independent South African IPP inventory returned HTTP 404 after a login redirect;
no login was attempted and no inventory was imported. REPD saved candidates
1000:1200 were structurally reviewed: all 200 remain held for original permits.

The shared viewer exposes OEM table completeness and withheld fields. The offline
gallery distinguishes floating design depth boundaries and prints the retained
OEM conflicts. Next: BOE July 27–29, REPD 1200:1400, and exact SANY corrections.

### 6 November continuation: empty discovery partitions and restricted originals

The July 27–29 BOE Series A/B title partitions are complete with no wind-title
candidates. This does not establish that no wind projects existed on those dates.
REPD saved candidates 1200–1399 were structurally reviewed against the pinned
release; all 200 remain application-to-farm identity holds.

The original SANY *Product Family, April 2025* brochure was acquired and
checksummed, but its explicit copying restriction excludes its specifications
from this intake. This is an explicit reuse exclusion, not an HTTP or
authentication failure. The three existing SANY scalar conflicts and the
SI-16840 regional configuration crosswalk remain unresolved. No projects,
equipment, turbine instances or numerical curves were added in this continuation.
See `catalogues/wind/research/2026-11-06-1035-review.json` for source identifiers,
checksums and next partitions.


## Operator portfolio and BOE continuation (6 November, 11:35 UTC)

The complete 20-row operational wind subset in Masdar’s 15 July 2024 offering
circular was reviewed against the catalogue: nine new projects, three historical
observation enrichments, and eight identity holds. The portfolio date is
31 March 2024. It is not a current operating census. Contracted MW (pp154–155)
and gross reported MW (p166) remain separate nested quantities; neither becomes
installed capacity. Turbine count × rating is a labeled arithmetic check. The
source’s fleet-average footnote is preserved and does not identify an exact model.
No equipment configurations were inferred from OEM names or ratings.

Dumat’s 2022-07-01 commercial operation date and March 2024 ownership are retained
alongside its original 2019 award observations. London Array’s final-turbine
installation and Hywind’s first-export milestones are not relabeled full COD.
Month-only African CODs retain month precision. Existing scalar facts, IDs,
creation dates and capacity exclusions are unchanged. The shared viewer shows
dated portfolio coverage, missing exact models and capacity boundaries.

BOE July 23–25 contains one accepted wind application: Revilla-Vallejera Hib,
40.5 MW proposed, linked by procedure PFot-ALM-044-EOL. Its operational PV/BESS
host and shared grid capacity are excluded. Two source reference coordinates
remain in ETRS89 UTM zone 30N with metre precision; neither is a farm centroid or
an individual turbine inventory. FV Monclues is a solar-only authorization and
remains excluded from new wind projects. REPD offsets1400:1600 received structural
review only: all200 identities still need original permits.

Continuation: BOE July20–22; REPD1600:1800; eight named Masdar registry crosswalks
in the review ledger. The same circular’s Zarafshan/Baltic Eagle construction rows
are a separate unprocessed partition. Full original documents are not redistributed;
SHA-256 and page locators are recorded in the source registry and review ledger.


## Construction and environmental decisions (6 November,12:35 UTC)

Masdar’s two construction-table wind rows from its July2024 circular are now
represented: Zarafshan and Baltic Eagle. They describe March2024 construction,
not present operation. Zarafshan’s2025 table forecast conflicts with its2026
narrative forecast; both remain dated observations and no COD scalar is assigned.
Baltic Eagle’s minority-stake financing is not total project investment.

BOE July20–22 yields one negative environmental decision for two wind proposals,
Escuderos I andIV. Their21.6/28.8MW and V172 geometry are original proposed designs.
The negative DIA is neither construction permission nor an inferred final
administrative cancellation. PV hosts and shared grid infrastructure are excluded.
All four records remain excluded from additive capacity totals. No equipment
variant is manufactured from project ratings or optional hub configurations.

The operator adapter now requires a reported lifecycle before staging a row.
A regression fixture checks that construction and conflicting forecasts cannot
become operation or commissioning. REPD1600:1800 was structurally reviewed only;
all200 original-permit identity holds remain. Next: BOE July16–18, REPD1800:2000,
and later Zarafshan/Baltic Eagle milestone and rating-revision reconciliation.

### July 16–18 notice and REPD continuation

The 6 November 2026 13:35 review completed all discovered BOE issues for
16–18 July. Notices BOE-B-2026-24346 and BOE-B-2026-24461 concern solar
hybrid applications; La Herrada and Torozos B/C remain wind identity holds.
Solar, wind and hybrid capacities are not interchangeable. REPD saved
candidate offsets 1800:2000 were structurally reviewed, with all 200 held
pending original permits. The offline parser now rejects extra or missing
CSV cells before recording a reviewed partition, including malformed rows
outside the selected slice. No project, equipment or capacity total changed.
The dated review ledger records the original Baltic Eagle installation
release and its unresolved date/rating revision crosswalk.
