# Global Wind Database

Canonical JSONL lives in `records/`; projects, exact equipment configurations,
individual turbines and numerical curves share stable linked identities.

At batch `2026-11-07-0800`, the branch contains **8,328 projects** (8,327
non-group records), **566 equipment records**, **13,657 linked registry turbines**
and **two original numerical curves**, across **64 countries** and **66 equipment
manufacturer labels**. Merged main at `dbd83f04` has 8,323 projects and the same
other entity counts. This run adds five Spanish proposals/withdrawn applications,
with no equipment additions or existing-record enrichments. All new scopes remain
excluded from capacity totals. Earlier PRs were merged externally; this batch
starts a new review branch. See `research/latest.json` for publication context.

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

### Dated DNV register observations

The 2026-11-04-1635 batch reviews the complete `CC DNV-SE-0074` partition
whose object descriptions mention gearboxes in DNV's 20 April 2026 workbook.
Three existing exact gearbox identities receive dated register observations.
Applicants remain distinct from manufacturers. Certificate, design-evaluation
and manufacturing-evaluation statements are not interchangeable; the register
is not evidence of present validity or independently validated performance.
Unresolved identities, platform labels and oil statements remain in the ledger.
The offline adapter checks headers, date types and duplicate certificate IDs.

Ouroso's seven proposed 5,900 kW turbines yield a derived check of 41.3 MW.
No reported total MW is supplied by the reviewed notice, so no capacity scalar
is populated. The public-utility consultation does not establish construction
permission. El Almendro's solar decision remains deferred for wind identity
reconciliation. Both preceding records and capacity exclusions are preserved.

### Complementary certificate partition and withdrawn project

Batch `2026-11-04-1735` completes the DNV-SE-0074 register entries whose
object descriptions do not mention gearboxes. This text partition is not a
component classification: a gearbox identified only by its model code may
appear here. Three explicitly branded dry-type transformer identities and one
LM rotor blade are added; their model codes do not establish power, voltage or
blade length. Certificate applicants remain separate from manufacturer labels,
and the dated register does not establish present validity or operating performance.

BOE October 17 and 19 Series A/B are reviewed completely. Mistral's PEol-338
withdrawal is recorded separately from Nordés and from their former joint
administrative procedure. Its 106.4 MW application capacity is not installed
capacity and remains excluded from aggregate totals. El Páramo's extension and
Tesouro's wind/battery boundaries require further identity reconciliation.

### Hybrid proposals and dated construction permits

Batch `2026-11-04-1835` completes BOE October 15–16 Series A/B and the
Tesouro original wind construction permit crosswalk. The three Elawan Belinchón
wind farms are separate from their existing photovoltaic hosts. The environmental
notice reduces their combined design from ten turbines/72 MW to nine/64.8 MW;
Belinchón II's revised individual capacity and count remain null while both
observations and the removed B-10 position are retained. No aggregate project row
or guessed turbine model is added. Tesouro's 2024 authorization is dated evidence,
not proof of current operation; its 60 MW access permission is separate from the
50.4 MW authorized wind proposal and the later battery project. All four new
project scopes remain excluded from capacity totals.

### October planning notices and registry identities

Batch `2026-11-04-1935` reviews all Series A/B wind-mentioned titles for
October 1–3, 5–10 and 13–14, including the extra October 2 issue. It adds
Conca de Barberà I, Anoia y Segarra II and the revised Mudarra proposal.
Conca and Anoia retain dated historical construction permissions; Mudarra's
100 MW revision is a consultation, with the earlier 99.9 MW authorization
kept as a separate dated observation. All three remain excluded from sums.

Mudarra explicitly specifies ten EN-182 turbines at 7 MW and five at 6 MW,
with 182 m rotors and 120 m hubs. The two linked equipment configurations
are planning specifications, not evidence of installation, independent
performance validation or equivalence to the existing India-market model.
The 100 MW arithmetic check corroborates, but does not replace, reported MW.
No individual turbine records are inferred from property schedules.

The BOE adapter now defers an existing exact `gencat_expediente` or
`miteco_expediente` even when names change. A shared procedure requires scope
review; it never automatically merges farms or phases. A shared BOE notice
alone is not a project identifier. The source review retains sibling-farm
holds and the explicit Sinoma website reuse exclusion. The next daily
partition is September 28–30, alongside the recorded permit crosswalks.


Batch `2026-11-04-2035` reviews all September 28–30 Series A/B wind mentions,
including both September 30 issues. Satrebares retains its refused application
and corrected geography; Vientos del Cid I retains its 78 MW proposal and
approximate original CRS coordinates; Alsa retains its new 18 MW proposal,
four documented proposed turbine positions and dated annulment/reapplication
history. Alsa's inconsistent printed annulled-instrument date remains unresolved.
The Castillo Garcimuñoz storage notice is held for wind identity/scope review.
All three new projects remain excluded from capacity totals.


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

### EIA 2025 nonoperable wind partition (2026-11-04 follow-on)

The final 2025 EIA-860 wind workbook's complete **Retired and Canceled** tab
contains 172 generator rows across 129 plant codes: 102 retired, 54 canceled and
16 indefinitely postponed/no-longer-in-resource-plan rows. This annual tab is
**not a comprehensive historical retirement census**. Its reporting cutoff is
31 December 2025; the final release was published 10 September 2026.

58 existing U.S. historical projects receive 82 dated unit observations (62 RE,
20 CN), registry plant codes, predominant manufacturer/model labels,
representative hub heights, original wind-speed fields, operating/retirement
month and year, and plant/grid context. WRI's original importer explicitly
encodes EIA plant codes; accepted matches also require agreeing names and
coordinates. Five code matches with name/location discrepancies and 66 other
plant identities remain deferred in the complete decision ledger. No plant
status, capacity total or aggregation eligibility changes. Units are generator
aggregations, not necessarily individual physical turbines. Predominant model
labels are not exact OEM configurations or complete mixed-fleet inventories.

The adapter preserves original units and source rows. Summer/winter net MW stay
separate from nameplate MW. Feet normalize to metres by 0.3048. Wind speed uses
0.44704 m/s per mph, but the workbook's “Design Wind Speed” heading differs from
the instructions' representative annual-average wording; measurement method,
dates and height remain unknown. No resource comparison or capacity factor is
inferred. The shared viewer counts dated unit observations separately from
whole-project status; the offline gallery demonstrates the same distinction.

Together with the preceding Polish/EPD checkpoint, this iteration adds six
projects, enriches 59 projects and seven exact equipment records, and adds no
new equipment models, turbines or curves. The equipment target was not met;
unnamed components and predominant registry labels were not converted into
invented configurations. See `research/2026-11-04-2535-eia-decisions.json` for
all 129 decisions and `research/latest.json` for exact continuation partitions.

Batch `2026-11-05-0835` starts from merged main `aa842b95` (PR #153 was
merged externally). The first checkpoint adds eight EIA registry sites and
substantively enriches historical Krzęcin 6 MW with owner and regulator evidence:
8,182 projects versus 8,174 on that main; equipment/turbine/curve totals unchanged.
All 150 plants / 158 generator rows in Operable codes 64000–69999 were reviewed;
142 identities remain deferred. Generator ratings remain nested observations,
not farm capacity totals. The viewer and offline example distinguish unknown
installed MW from zero and unresolved aggregation scopes. See the latest
checkpoint for subsequent equipment research and validation results.

The second checkpoint processes every row of the six-page Nordex OEM history
table: 46 rows yield 33 new exact types, nine existing-model revision holds and
three conflicting-rating/unit holds. The repeated AW77/1500 tower observation
stays nested; S46 and N155 rating ranges do not generate synthetic variants.
N27/150 and N27/250 contradictory printed ratings are not silently corrected.
Krzęcin 6 MW and Krzęcin II 19.2 MW now have supported type/rating links to S77
and N117 respectively; installed revisions and options remain unknown. The
undated table's production headings do not establish current availability.


Batch `2026-11-05-0910` resumes PR #158 at `9d697427`: 56 new US onshore
registry sites across 20 states, with no farm capacity totals enabled. Exactly
142 saved identity holds were reviewed; 86 remain. A geodesic distance screen
includes existing sites and candidates within the same cohort, while distinctive
name and alias checks ignore generic legal/site words. These are review flags,
not automatic identity decisions. The original final-2025 EIA Operable sheet
has 1,573 generator rows and maximum plant code 69,327; the residual range
above 69,999 is empty, completing the partition scan. Individual turbine
inventories, exact predominant-model configuration links and whole-farm
capacities are not inferred. All previous records and six capacity totals are
preserved. The equipment manufacturer count is 57 labels; inventory turbine
labels are now reported separately in `latest.json`.


The OEM continuation adds dated history to 31 existing exact types using Nordex's
12 June 2025 article: early stall/drivetrain controls, Südwind pitch control,
Gamma/Delta maintenance designs, AW prototype and dated production-status facts,
and later blade/mode/hub observations. The 18 February 2025 N27 account and
22 July 2024 N169 announcement were also reviewed. The two N27 table ratings and
N169 printed unit remain held, as does a lone AW77/1300 narrative mention.
Specifications remain OEM statements; no independent performance validation is
claimed. `oem_historical_observations` keeps dates, boundaries and field provenance
without replacing supported scalar specifications.

Batch `2026-11-05-0945` resumes PR #158 at `1786ce89`. It adds 52 US registry
sites from 110 saved EIA holds; 58 remain. Four Orchard candidates remain held
after primary Oregon PUC shared-interconnection evidence because their registry
and physical boundaries still need reconciliation. All six capacity totals stay
unchanged. Current main's Hydropower addition was incorporated and both sectors'
shared-viewer functions preserved.

FGW's current-index Nordex tables (110 old-site rows, 70 new-site rows) add
16 exact printed types/revisions and enrich 24 existing equipment records.
The 173 accepted observations retain five-year modeled kWh, hub and power settings,
reference-site conditions, original strings and restriction notes. Five withdrawn
values remain alongside replacements. Seven N27 rows are held for the prior
OEM rating conflict; three missing rotor cells remain null. No inferred installed
compatibility, synthetic variants, capacity factors or numerical curves are added.
See the batch transcription and decision ledgers in `research/` and the current
counts and executed checks in `latest.json` and `validation.json`.

The 2026-11-05 Vestas FGW old-reference-site batch reviews all 103 numerical
rows across four pages. It adds 29 explicitly printed configurations and enriches
V47-660/200 kW. Hub-height choices stay nested; missing rotor diameters remain
unknown, including in the viewer's observation completeness count. Two HTq
rows await revision mapping, and the V66 reduced-power contact notice supplies
no numerical data. These five-year modeled reference yields are neither measured
production nor numerical power curves. The newer reference-site table remains
a separate queued partition. See `research/2026-11-05-1135-fgw-review.json`.

The subsequent new-reference-site Vestas table has 114 numerical rows: 109
accepted observations across five new configurations and sixteen enriched
records, with five HTq revision mappings deferred. Four withdrawn observations
retain their 8 July 2026 decision date alongside replacements; three corrected
observations retain 14 September 2026. These dates describe reference-result
revisions, not equipment commissioning. Density and blank rotor cells stay
unknown. The shared viewer and deterministic example count dated corrections.

The checksum-pinned REPD review adapter stages saved unlinked candidates in
ledger order without importing farms. Offsets 200–399 retain all 200 identity
holds, including 160 permit references and 33 explicit replacement references.
Primary permit contents still need review; application status never becomes
farm status through this staging step. Next structural partition: 400–599.

The 2026-11-05-1335 review adds one Korean certificate-scoped V126 HTq configuration. Its two reported power modes remain nested; current certificate validity and FGW equivalence are unknown. A second HTq entry has inconsistent class labels and remains held. REPD saved offsets400–599 were structurally reviewed; all200 remain identity holds, with no farm capacity or lifecycle assignments.

The 5 November 14:35 batch adds 23 Korean certificate configurations, one Spanish
wind-module proposal and eight planned turbines. Branch totals: 8,291 projects,
479 equipment, 13,641 turbines and two curves. KNREC's full 57-row register now
has review decisions; 32 remaining-row candidates and the earlier HTq conflict
remain held. REPD's next structural-review cursor is 800; BOE's next dates are
10–12 September 2026. The shared viewer distinguishes expired/unspecified issuer
listings without asserting current validity. All capacity exclusions are retained.
