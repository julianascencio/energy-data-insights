# Global Wind Database

Canonical JSONL lives in `records/`; projects, exact equipment configurations,
individual turbines and numerical curves share stable linked identities.

The proposed branch contains 7,810 project records (7,809 non-group records),
266 exact equipment records, 13,633 registry turbine records and two original numerical
power curves, across 59 countries and eleven equipment manufacturer names.
Merged main at `6b38f9a4` contains 7,582 projects, 264 equipment records and 10,264 turbines
and two curves. These are catalogue counts, not an operating census.

The initial 5,344-row WRI import is historical. REPD lifecycle enrichment does
not resolve capacity scope; 2,216 other applications remain deferred. Swedish
registry areas and their explicit turbine children also stay outside project
capacity totals until physical phase/repowering scope is reconciled.

See [the evidence guide](../../docs/wind-catalogue.md),
[viewer source](../../docs/wind-database-viewer.rst),
[batch checkpoint](research/latest.json), [ranked backlog](research/backlog.json),
[source registry](sources.json), and
[schema](../../data-retrieval/src/energy_data_retrieval/wind_catalogue/schema.json).

```bash
uv run python -m energy_data_retrieval.wind_catalogue validate
uv run python -m energy_data_retrieval.wind_catalogue build --output artifacts/wind-v1
uv run python examples/database/plot_wind_catalogue.py
```

Use a fresh output path. Parquet is reproducibly generated, not committed; Sphinx
publishes it with the viewer. Unknown stays null. Parent totals, unresolved scopes
and overlapping generations are excluded from capacity summaries, which separate
lifecycle states. OEM curves and specifications are not operational validation.

The 2026-11-03 08:35 continuation adds 232 previously omitted procedural dates
to 114 linked UK projects, preserving all lifecycle and capacity fields. The first
200 unlinked applications remain deferred after structural review. Refusals and
later successful appeals are history, not contradictory current statuses.

The 09:35 Canadian continuation reviews all 327 NRCan project groups and enriches
117 existing identities with inventory fleet details; 210 remain deferred.
Lifecycle and all capacity exclusions remain unchanged. Individual turbines
and exact OEM records are not inferred from inventory model labels.

The 10:35 continuation processes all 89 land-based registry areas and 348 turbine
rows in Stockholm, Uppsala and Södermanland. It adds 72 named project identities
and 321 linked turbines; 17 areas and two orphan turbine rows remain deferred.
Seven current VENSYS technical sheets yield seven exact configurations. The
VENSYS 136 sound-power conflict remains null with both observations preserved.

The 11:35 increment adds 192 Östergötland project areas, 559 linked turbines and
four exact ENERCON configurations. Thirty-five areas remain held; no prior
record or capacity total changes. See the 1135 ledgers for source partitions.

The 12:35 increment adds 22 Schleswig-Holstein parks and 105 linked MaStR units
from a complete 4,788-unit state partition, plus two exact ENERCON models with
qualified optional yield modes. All 6,565 preceding records remain unchanged.
The 1,717 deferred name groups retain explicit decisions; accepted park scopes
remain excluded from capacity totals. See the 1235 ledgers.

The 13:35 increment reviews all9,034 Niedersachsen units, adding73parks and366
linked turbines;2,973namegroups remain held. Two exact Winergy integrated
gearbox-generator assemblies add component coverage. Capacity exclusions remain.

The14:35 increment adds67Nordrhein-Westfalen parks,314linked turbines and14NGC
yaw/pitch gearbox types. All6,753state units reviewed;2,665namegroups held.

The15:35 increment adds131projects and791turbines from complete Brandenburg and
Jönköping partitions, plus nine Bonfiglioli gearbox models. All prior rows remain.

The16:35 batch adds64projects,433turbines and15exact ABB converter types.

The17:35 batch adds168projects/918turbines and enriches15existing ABB models.

The18:35 batch adds83projects,369turbines and18exact ACU401inverters.

The 19:35 batch adds 52 projects, 188 turbines and 20 exact ACU configurations
from complete Mecklenburg-Vorpommern/Blekinge partitions and OEM type tables.
All 10,529 preceding records and six capacity totals remain unchanged.

The 20:35 batch adds 295 projects, 826 turbines and 24 exact ACUx10 configurations
from complete Rheinland-Pfalz/Skåne partitions and R04_0 frame7/8 tables.
All 10,789 preceding records and six capacity totals remain unchanged.


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

## French 2020–2021 cohort and India model register

The 08:35 continuation reviews all 238 French wind installations with industrial
service dates in 2020–2021 and reported installed ratings of at least 1 MW. The
complete 2,458-row national extract remains the identity-screening boundary:
18 named installations are added, 220 candidates held, and 2,220 rows outside
the selected cohort retained in the ledger. All new capacities remain excluded
until farm, phase and repowering boundaries are reconciled. A generic “Hangar”
label is quarantined; registry generating-group counts are not turbine counts.
The first 20 earlier deferred EICs were reviewed and remain unresolved.

All 30 entries of MNRE's ALMM-Wind list dated 20 August 2026 were manually
transcribed and checked against the original four-page PDF. The batch adds
27 exact equipment records and enriches the existing GE 3.8 MW-154m with
India-specific observations. Two Pioneer 750/57 tower-height entries share one
model record; the Vayona SG entry is held for manufacturer/model continuity.
Power and tower options are nested. Numeric ratings and diameters follow the
table even when model labels differ. Mixed-format certificate dates stay raw;
component expiry restrictions, outstanding issues and excluded boost modes
remain visible. Original certificates and current eligibility are not verified.
The source register contains the original checksum; the April association-hosted
list is a separate reviewed revision, not mixed into the August observations.

## French 2016–2019 installations and named turbine components

The next two complete ODRE service-date cohorts contain 607 installations of at
least 1 MW. National name/commune and existing-identity screening accepts 52;
555 remain deferred. All 52 retain unresolved aggregation scope. This does not
turn historical WRI observations into a current operating census.

Nine complete manufacturer component disclosures linked by the August 2026 MNRE
list, plus all three rows of the June 2026 ALMM-WTC list, add 25 exact blade,
gearbox and generator models. Nine existing turbines gain dated component
observations. The 66 reviewed source rows include 43 without exact model codes;
those generic tower, generator and bearing descriptions remain in the ledger,
not as synthetic equipment. Multiple manufacturing sites and applications stay
on one model. The EF0953A 3,560 kW rating is mechanical; the listed turbine's
3,000/3,150 kW rating has a separate boundary. Blade type numbers do not supply
missing blade lengths. List inclusion does not establish current certification.

The checksum-verified component adapter consumes reviewed transcriptions with
complete document row sets. The gallery and equipment viewer follow explicit
component/turbine applications in both directions with their conditions and
source locators. They do not infer compatibility from common suppliers.

## French residual installations and gearbox drawing revisions

The complete 57-row missing-date/sub-1-MW residual partition adds eight named
installations and holds 49. The full 2,458-row national inventory still screens
names and communes; unknown service dates remain unknown, missing/nonpositive
ratings are held, and all new scopes remain excluded from capacity totals.
All dated cohorts and residual rows are now reviewed; identity reconciliation
is the next task, not repeated bulk discovery.

The original S144 TC-240121 Rev.2 certificate's complete two-option gearbox
table adds drawing-qualified ratio evidence to EF0953A. The distinct
SMG282ADT113-0209 candidate is held rather than merged into SMG282CDT175-0136.
These are historical configuration observations with maintenance/design-change
conditions, not independent current-certification or performance verification.

## S144 component configuration continuation

The retained TC-240121 Rev.2 original supplies five exact component identities:
SB70 (SB70S1), SMG282ADT113-0209, SG055D06, WF1000-06L0270-CPN-A and HWDFM0693150.
The complete selected component sections are recorded with explicit S144 links.
Generator alternative manufacturers stay nested; no duplicate factory models
are created. Tower drawing options remain observations rather than inferred
commercial model variants. Bearing, coupling and structural identities remain
held for category/assembly reconciliation. Historical certification conditions
are not current eligibility or independent operational-performance validation.

## Spanish regulatory decisions: bounded daily review

The 2026-11-04-1335 batch reviews every Series A wind-mentioned title in the
BOE daily indexes for 20 October and 2–4 November 2026 (five notices), plus the
Taraguilla withdrawal and its correction. Five project identities are added:
Las Quinientas wind module, Taraguilla, Nordés, Pinta y Guindalera and Herrera
de los Navarros. This is a bounded regulatory review, not a Spanish plant census.

The offline `wind_catalogue.boe` adapter selects complete title partitions and
stages reviewed facts only after original-byte checksum and completeness checks.
It does not extract capacity or operating status from a title. Solar decisions
cannot cancel wind farms; environmental conditions alone do not establish
construction authorization. Existing identities are held for reconciliation.

Las Quinientas retains the final five-turbine, 33 MW proposal separately from
its earlier 72.6 MW design and 72 MW access observation. Its inconsistent rotor
figures remain quarantined. Taraguilla retains the 30/33 kV and destination
conflicts; the subsequent correction changes section numbering only. Nordés
is a withdrawn application, separate from Mistral despite their former joint
processing. Pinta y Guindalera retains the 100 to 103.5 MW proposal revision;
its 2026 auxiliary supply permission is not a commissioning event. Herrera's
35 MW existing wind installation stays separate from the proposed 21 MW solar
addition. Its precise operating lifecycle remains unknown.

All five farm/phase scopes remain excluded from capacity totals. Los Campillos
is deferred because the reviewed rejection concerns its solar hybrid. Incidental
Mistral, Cerrato VI and Las Majas VIIB mentions remain research candidates.
No equipment record is added: exact Bonfiglioli drawing searches found only the
already processed certificate. See the dated transcription, source review and
decision ledger; the next daily partitions are 21–23 October 2026.

## Paired extension decisions

The 1435 continuation completes BOE Series A wind-mentioned titles for
21–23 October 2026: four notices and five project scopes. It adds the separately
reported 11 MW Coll del Moro and Torre Madrina extensions, Valiente II and
Valentina's withdrawn wind hybrid. Existing farms and proposed extensions are
not combined. El Páramo remains held against two historical same-name identities.
The adapter supports several explicitly reviewed project scopes in one notice,
retaining separate phase IDs and shared original-source evidence. Solar ratings,
public-utility declarations and proposed capacities do not establish wind output
or commissioning. All four new records remain excluded from capacity totals.
Exact supplier searches produced no new primary OEM sheet; no new equipment is
claimed. Next daily BOE partitions: 26–28 October 2026.


### BOE hybrid consultations and multiple daily issues

The 2026-11-04-1535 batch reviews all Series A/B wind-title notices for
26–31 October, including both issues 267 and 268 on 28 October. The default
BOE daily URL can show only an extraordinary issue. `issue_urls` discovers
same-day alternatives; every returned issue must be fetched before claiming
partition completeness. `select_wind_notices(..., series="B")` explicitly
selects announcements; the default remains Series A.

Olmedilla is a proposed wind module, not commissioned capacity. Los Pedreros'
existing wind capacity is retained as a qualified observation from a storage
consultation. Neither record enters capacity totals. Hybrid regulatory
capacity, PV, battery and flywheel ratings remain separate. Romeral is held
for reconciliation with its historical name candidate. These bounded results
do not meet the 50-project/20-equipment research targets.
