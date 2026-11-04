# Global Wind Database

The Wind catalogue connects projects, exact equipment configurations, turbines and
numerical curves. At batch `2026-11-04-2335`, the proposed continuation contains
**8,168 projects, 372 equipment records, 13,633 linked turbines and two original
numerical curves**, across **59 countries and 54 manufacturer labels**. Labels
are not a reconciled corporate-entity count. Merged main at `7c31c06a` contains
7,948 projects, 337 equipment records, 13,633 turbines and two curves.
These are catalogue counts, not a current operating census. Subsequent totals
are recorded in `catalogues/wind/research/latest.json`.

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
