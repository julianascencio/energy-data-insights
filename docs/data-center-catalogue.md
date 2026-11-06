# Global Data Center Database

## Data Center Projects

The current continuation branch has 644 project records across 45 countries:
513 facilities, three phases and 128 explicitly scoped campus aggregates, from 22 operators.
Coverage spans North America, Latin America, Europe, Africa, the Middle East and
Asia-Pacific. This is a research catalogue, not an operating-capacity census.

Use the [interactive viewer](https://julianascencio.github.io/energy-data-insights/data-center-database-viewer.html?table=projects)
for search, lifecycle/country/cooling filters, map and expandable field evidence.
The map includes operator-reported pins only; it never geocodes a city as a site.

`record_id`, `facility_id`, `campus_id`, `phase_id`, `parent_record_id`, aliases,
external identifiers and organization-role IDs preserve identity through changes.
Each row states `record_scope`, `capacity_scope`, `aggregation_role`, dated status
and whether its date is a publication/event date or retrieval of an undated page.
A campus may reference named children; phase rows require a phase ID. Links are
validated for missing parents, cycles and duplicate identities. Campus totals
and unresolved overlap groups never enter capacity sums, even under filtering.

Three independent columns represent IT load, utility connection and total
facility demand: `it_capacity_mw`, `grid_capacity_mw`, `facility_capacity_mw`.
Each requires its own basis (operational, construction, ultimate planned, design
maximum or unspecified). `capacity_summary` reports separate basis groups and
unknown/excluded counts. It never substitutes backup MW, battery MW/MWh or floor
area. Rated design IT at an operational site is not measured operating demand.

Event dates, areas, rack metrics, water, heat rejection and generation can be
stored directly or as typed observations with units and boundaries. PUE/WUE
observations require measured/design/target/unspecified kind and measurement
period (null when undisclosed). Investment observations preserve currency,
reference year and scope; performance observations must preserve precision,
workload and test conditions. `renewable_supply_json` explicitly separates
physical generation, contractual procurement and environmental claims.
Certificates require issuer, scope and validity evidence, not marketing badges.

The Green Mountain continuation processes the operator's complete current
seven-site portfolio. SVG-Rennesøy is an independent facility; TEL-Rjukan,
OSL-Enebakk, OSL-Hamar, LON-East, FRA-Mainz and SVG-Undheim are explicit
multi-building campus aggregates and remain excluded from capacity totals under
every filter. Only source-labelled IT capacity is normalized. Site power,
secured power, future power and cooling capacity remain separate observations,
and unnamed building counts do not create inferred child records.

The EcoDataCenter continuation adds the operator's three evidenced Swedish
establishments: Falun as an independent facility, and Borlänge and Smedjebacken
as campus aggregates excluded from every capacity total. Reported 80 MW, up-to
600 MW and immediate 150 MW statements retain their printed boundaries because
the sources do not identify them as IT, grid or total facility demand. Land,
renewable-electricity, PUE, permit and construction statements remain dated
observations; the announced Smedjebacken campus is not treated as permitted.

The European Commission JRC continuation adds the complete bounded 2024 Digital
Realty Spain and Sweden participant partition: ESP1--ESP4 and STO1--STO6. The
registry establishes exact data-centre identities and Code of Conduct adhesion,
but not current lifecycle, ownership, operation, capacity, locality or
certification. All ten records therefore remain lifecycle-unknown and
aggregation-unresolved, and are excluded from capacity totals under every
filter. The Commission page was available through the public indexed reader
while direct original retrieval was rejected; this is recorded as an access
failure, not a reuse restriction. The Commission CC BY 4.0 reuse notice is
captured and checksummed separately.

The next JRC partition processes all 35 displayed Equinix EMEA corporate rows
as 34 unique facility identities across 11 countries. The registry repeats
`The Netherlands: AM7, Amsterdam` verbatim; it is normalized once and the source
anomaly remains reviewable rather than becoming a duplicate facility. Bulgaria,
Italy, Poland, Switzerland and Türkiye are new country coverage. The registry
supports each site code, city and 2013 adhesion year, but it does not establish
current lifecycle, ownership, operation, physical aggregation, capacity or
certification. All 34 records therefore remain lifecycle-unknown and
aggregation-unresolved and are excluded from every capacity total.

The 2018 JRC continuation adds the complete displayed DxC Technology and
`Digital Reality` participant partitions: 11 UK identities and eight German,
Dutch and UK identities, respectively. The latter spelling is preserved exactly
as printed by the registry and is not silently normalized to a different owner
or operator. Apparent source spellings such as `Doxfrod Park` and `Winyard` also
remain reviewable rather than being corrected by inference. Adhesion year is an
observation, not commissioning, certification or deployment evidence. All 19
records remain lifecycle-unknown and aggregation-unresolved, with ownership,
operation and capacity quarantined; they are excluded from every capacity total.

The current U.S. facility continuation includes all 133 entries whose most recent
label year is 2026, all 50 from 2025, all 23 from 2024, all 31 from 2023, and
all 54 from 2019 through 2022 and all 46 from 2010 through 2018 in EPA's
complete 337-entry ENERGY STAR Certified Data Centers registry. The registry is
fully processed. Each remains an issuer-verified facility identity. The
2010-2025 partitions retain current
lifecycle as unknown because an earlier certification is not proof of current
operation. EPA
intentionally exposes only the state for security, so locality, address and
coordinates remain null even when address-like text appears inside the exact
public facility name. The source's unlabeled floor-space value and year-only
construction value remain bounded observations; neither is converted to square
metres or promoted to an event date. Owner and all 42 printed property-manager
relationships are retained, while operator, capacity, PUE and equipment remain
unknown. No registry entry remains unprocessed; future work should use later
issuer updates or independent planning, utility and lifecycle evidence.

## Data Center Equipment

The [equipment table](https://julianascencio.github.io/energy-data-insights/data-center-database-viewer.html?table=equipment)
has 2,774 exact models/configurations from NVIDIA, AMD, ABB, AIRSYS, AboveAir, ASUS, Ablerex Electronics, Ace Computers, ADI, Altos, Appleton Group / SolaHD, Baudouin, Borri,
Carrier, Cisco, CoolIT Systems, Cummins, CyberPower Systems, Daikin, Dell, Delta Electronics, Eaton, Envicool, Fujitsu, H3C, Hewlett Packard Enterprise, Hitachi Vantara, Huawei Digital Power, IBM, KAYTUS, Kehua Tech, KSTAR,
Legrand AV, Lenovo, Motivair by Schneider Electric, Makelsan, Nutanix, Panduit, SIEL, Tescom, Mitsubishi Electric, Fuji Electric, mtu,
nVent HOFFMAN, Oracle, Schneider Electric, Siemens,
STULZ, Supermicro, Toshiba, Vertiv, Volvo Penta, Para Systems / Minuteman Power Technologies,
Ingram Micro / V7, N1 Critical Technologies, Neuropower, Power Logic / KOSS,
Right Power Technology, Upsonic Power Systems, xFusion and ZTE. Current categories are GPU accelerators,
servers, UPS, rack PDUs, backup generators, chillers, coolant distribution units
and CRAC/CRAH precision air-conditioning equipment, transformers and switchgear.
The DOE CCMS CRAC continuation retains all 50 rows displayed on the first public
page: 36 AboveAir and 14 AIRSYS basic-model configurations. AIRSYS net-total
capacity and every row's rated airflow are unit-converted while the printed
Btu/h and SCFM values remain observations. AboveAir's displayed sensible values
exceed its displayed totals, so all 36 normalized cooling capacities remain null
with explicit conflicts. NSenCOP remains a ratio observation, and registry
listing is not treated as a DOE compliance determination or a deployment.
The DOE CCMS UPS continuation processes all 50 rows displayed on the first
public page: four ABB and 46 APC individual-model configurations. Exact
individual-model matching enriches 11 existing ENERGY STAR APC records and adds
39 new configurations without duplicating identities. Active W, apparent VA and
average load-adjusted efficiency remain separate and retain the lowest supported
input dependency mode. BN1500M2 and BN1500M2-CA keep normalized efficiency null
because ENERGY STAR reports 99.0% while current DOE CCMS reports 98.9%; both
dated issuer observations are preserved. Battery energy, runtime, frequency,
accessory combinations and deployment remain unknown.
The Schneider Galaxy
VS batch preserves exact commercial references, stated kW and kVA, battery-string
arrangements, full-load efficiency conditions and dimensions without calculating
battery energy or runtime.
The STULZ batches keep 30 fixed-speed R410A, 20 modulating-EC R410A and 23
populated fixed-speed R134a ASR/ALR configurations separate. They normalize net
sensible cooling only at the stated return-air/condensing/ESP rating point and
preserve total sensible cooling and component power as observations. Printed N/A
columns are excluded; refrigerant and compressor variants are never combined.
The Vertiv UPS continuation adds all 19 topology/rating rows printed for PowerUPS
6000 and four Trinergy CE ratings. Apparent kVA stays distinct from active kW;
family efficiency ranges, grouped dimensions and battery energy/runtime remain
unnormalized where the exact configuration table does not bind them.
The Carrier continuation adds all 28 AquaEdge 19DV rows at the two explicitly
published electrical variants. Cooling and input ratings retain the OEM's AHRI
water temperatures, fouling factors, pass count and water-side pressure.
The Cummins continuation adds 22 exact KTA50/QSK60 model-frequency rows with
explicit Data Center Continuous kW and kVA. Prime, standby and general continuous
ratings remain observations. Four conflicting non-DCC fields on three duplicated
QSK60 live-page rows are quarantined without discarding their matching DCC data.
The QSK50 continuation adds all eight exact model/frequency identities with a
populated Data Center Continuous rating. Five identities also retain the printed
prime, standby and general-continuous ratings and engine model; the three DCC-only
identities remain otherwise null. Repeated live-page rows are reconciled only
where their DCC values agree, and no family range is assigned to a model.
The mtu continuation adds all 20 Series 4000 model/frequency rows with an explicit
Data Center Continuous (3F) rating: 12 at 50 Hz and eight at 60 Hz. The brochures
report apparent kVA for these exact rows, so active kW remains null. Standby,
stationary-emergency and prime ratings, engine speed, shared voltage lists and
duty conditions remain bounded observations. Portfolio voltage choices are not
treated as selected windings, and the OEM Tier III/IV statement is not normalized
as an issuer-registry certification.
The Asian cooling continuation adds all 13 exact configurations in Huawei's
current NetCol8000-A and NetCol8000-C model tables plus ten Delta configurations:
four RowCool CW models, three GoCool CDUs and three explicitly documented in-rack
L2L configurations. Cooling-only and full/optional currents and weights remain
distinct. Alternate capacity points, multiple voltage choices, CFM observations
and exact water/air rating temperatures are preserved without synthesizing
options. OEM conformance statements are not issuer-registry certifications.
The Envicool continuation adds every exact model column in two official liquid-
cooling brochures: 13 direct-to-chip configurations and 13 single-phase or
phase-change immersion configurations. Heat-exchange capacity is normalized only
where the table labels it as such. IT-device power ranges, coolant alternatives,
facility-water minima and optional feeds remain observations rather than cooling
capacity, electrical input or synthesized orderable variants.
The Toshiba continuation adds all 23 capacity configurations displayed across
the four current three-phase UPS pages: six G9400 voltage/frequency variants,
seven G9000 ratings, five 4400 ratings and five 3000 TP kVA/kW ratings. Active
kW is normalized only for the 3000 TP rows where the OEM explicitly prints
kVA/kW. Family efficiency, battery compatibility, voltage/frequency choices,
module ratings and optional cabinets remain bounded observations; no runtime,
battery energy or parallel-system combination is inferred.
The Mitsubishi Electric continuation processes all 26 exact apparent/active
output pairs printed in the current eight-family UPS comparison table: four
7011B, five 1100A, four 1100B, five 9900AEGIS, three 9900B, two SUMMIT, one
9900CX and two 9900D ratings. The explicit kVA/kW pairs and single-valued family
input voltages are normalized. Family efficiency claims without load points,
ambiguous dimension/weight groupings, compatible battery types and optional
bypass, transformer, disconnect, communications or parallel equipment remain
observations rather than selected configurations. The page's broader 9900D
portfolio range does not create unprinted rating rows.
The Fuji Electric continuation processes the complete 20-column bounded current
portfolio review: three UPS7000HX-T3U, three UPS7300WX-T3U, ten UPS7400WX-T3U
and four voltage/UPM-specific UPS7500WX-T4 configurations. Active kW is populated
only where the OEM table explicitly prints kVA(kW) or kVA/kW. The two distinct
1000 kVA UPS7400 systems retain their three- versus four-UPM identities. Nominal
and maximum input current, output current, online/HE efficiency points, battery
interfaces, dimensions, weight and communications remain source-bound. Multi-
voltage and 50/60 Hz choices do not create synthesized ordered variants, and OEM
standards statements are not promoted to issuer-registry certifications.
The Daikin continuation processes all 27 nominal cooling columns across the 2026
EWAT-CZN, EWAT-CZP and EWAT-CZH tables. Each family retains nine exact sizes,
including separately labelled 040-MONO and 040-DUAL columns. Cooling output,
input power and water flow preserve the 12/7 degC water and 35 degC ambient
rating point. EER and IPLV remain ratios in observations; voltage, frequency,
dimensions, weight, hydronic choices and order-code suffixes are not inferred.
The Kehua continuation processes all 25 exact model columns across the current
KR11-RM, KR-RM, Eon, MY and KR33 tables. Apparent kVA and active kW are populated
only on the boundary printed by each family; selectable voltage/frequency ranges,
battery systems, external battery modules, distribution boxes and parallel options
remain observations. KR33 efficiency and weight stay null because the current
official English and Spanish tables disagree, while both observations and original
HTML checksums are preserved. The KR6000-RM and KR1110-RM input ranges also remain
unnormalized because the printed full-load upper bound exceeds the stated range.
The KSTAR continuation processes all 61 exact model columns in the current 2025
transformer-based UPS brochure: 23 GP800/MASTER/EPI columns and the complete
38-column EPOWER, EPOWER-L and EPOWER-H continuation. Apparent kVA and active kW
stay separate; voltage/frequency choices and shared efficiency, dimensions and
battery cells remain observations. The EPI 30K apparent-power scalar is
quarantined because its column prints 3 kVA beside 24 kW. EPOWER 6P/12P weight
alternatives remain observations unless the model suffix explicitly selects 12P;
the exact EPOWER-L and EPOWER-H model-column weights are retained without
synthesizing battery, communications or cabinet variants.
The Borri continuation processes all 25 exact rating columns in the current
INGENIO PLUS, INGENIO MAX, B9000FXS and B9600FXS tables. Published kVA and kW
remain separate, while voltage/frequency choices, family maximum efficiency,
battery autonomy and optional communications, parallel kits and transformers
remain observations. The INGENIO MAX 250 and 500 kVA weights stay null because
the current family page and January 2025 catalogue disagree; both dated values
remain preserved as conflicting observations.
The Baudouin continuation processes every row in the April 2025 Data Centre
Power rating card: 19 exact 50 Hz and 15 exact 60 Hz configurations. Engine
gross mechanical kWm, generator electrical kWe and generator apparent kVA stay
separate. Speed, aspiration and governor remain row-bound observations; no
alternator, voltage, emissions package, installation or deployment is inferred.
The Volvo Penta continuation processes all 22 populated model/frequency columns
in four current D8, D13 and D16 power-generation tables. Prime electrical kW and
kVA are normalized separately; standby electrical output and engine mechanical
kWm remain bounded observations. Blank TAD1640GE cells are excluded, and fuel,
emissions and cylinder statements do not establish a complete generator-set BOM,
issuer certification, site installation or deployment.
The non-overlapping Stage IIIA/Tier 3 continuation adds all 22 populated rows
from the current D8, D13 and D16 tables (six, ten and six). Explicit 50 Hz-only
and 60 Hz-only columns remain sparse: printed N/A cells do not become invented
configurations. The same active/apparent/mechanical and deployment boundaries
apply.
The Makelsan continuation processes every exact three-phase model column in the
reviewed LEVELUPS, LEVELUPS T3 and LEVELUPS T4 tables: 18, 11 and five rows.
Printed kVA and kW remain separate; the overlapping T3/T4 capacities remain
distinct transformer-based family identities. Selectable voltage/frequency,
family efficiency, battery cells, grouped cabinets and communications remain
observations rather than synthesized variants, battery energy or runtime.
The SIEL continuation processes all 27 exact UPS columns across three current brochures: nine Safepower S, ten Safepower Evo HF and eight Safepower Modular SPM cabinet configurations. S and Evo HF retain explicit kVA/kW pairs; SPM active kW remains null because the cabinet table prints only kVA. Merged dimensions, with/without-battery weights, module layouts, electrical choices, batteries, communications and parallel options remain observations and never create synthesized configurations or inferred runtime.
The Tescom continuation processes 22 exact rows across the current DS POWER
300HT, DS POWER 500--600 kVA, DS POWER SH and MTI250 tables. Every printed kVA
and kW value remains separate. Exact weights and unqualified cabinet dimensions
are normalized; battery-qualified DS POWER SH dimensions, module statements,
selectable electrical values, batteries and communications remain observations.
The ENERGY STAR continuation processes all 33 current certification entries for
Para Systems / Minuteman Power Technologies, all 22 entries for ADI, all 15
entries for Ablerex Electronics, all ten entries for Panduit, all seven entries
for Appleton Group / SolaHD, all seven entries for Legrand AV and all 26 entries
for Delta Electronics, all 135 entries for Cyber Power Systems, all 176 Eaton
Corporation entries and all 222 Schneider Electric entries in EPA dataset
`ifxy-2uty`, plus all 254 Vertiv Corporation entries and all 16 entries across
the eight residual partner partitions. The 923-row dataset is fully processed.
ADI's 11 W BOX and
11 UltraTech certifications remain distinct even where model names recur across
brands. Each entry retains its immutable ENERGY STAR ID, certification date,
active W, apparent VA, weighted and load-point efficiency, dimensions and
protocols. Tested-configuration, warranty and percentage-load runtime fields are
retained where reported. The four Ablerex MP modular entries explicitly report
those values as unavailable, so their normalized fields remain null; they are
not derived from the 11 AP entries. A normalized runtime is only a reported 100%
load value, paired with the exact W-to-kW conversion of that configuration's
active output. No battery energy, maximum configuration, output power factor or
deployment is inferred. The EPA-certified Legrand AV and Delta Electronics
entries are sourced from the public issuer dataset and do not reuse the
separately held OEM technical tables.
The Cyber Power Systems continuation retains all four reported brand identities
(CyberPower, amazonbasics, Amazon Basics and AmazonCommerical) without collapsing
certification IDs. Twenty-seven entries report a maximum tested configuration;
those model and output values remain separate observations while normalized kW
and kVA stay bound to the minimum tested configuration.
The Eaton continuation preserves all five source brand labels, including Tripp
Lite and Eaton variants, as issuer observations. Ten entries have no reported
minimum-tested identifier, eight have no runtime and six have no warranty; those
normalized fields remain null. Two reported maximum-tested configurations remain
separate observations rather than replacing minimum-configuration ratings.
The Schneider Electric continuation preserves the 162 `APC by Schneider Electric`
and 60 `Schneider Electric` brand observations across 222 immutable certification
identities. Thirty-two entries report runtime and warranty as unavailable; those
normalized fields remain null. Fifty-four entries retain their reported maximum-
tested configurations only as observations, while normalized ratings stay bound
to the minimum tested configuration.
The Vertiv continuation preserves five exact source brand labels across 254
immutable certification identities. All minimum configuration identifiers,
100%-load runtimes and warranties are reported. Seventy-five entries retain a
maximum tested model as a separate observation; 44 provide a maximum active-W
value and none provides maximum apparent VA, so absent maximum values remain
null. Normalized kW/kVA, runtime and efficiency stay bound to the minimum tested
configuration, and no battery energy or deployment is inferred.
The final ENERGY STAR continuation adds three Ingram Micro/V7, three N1
Critical Technologies, three Neuropower, two Mitsubishi Electric Power
Products, two Power Logic/KOSS and one each from Fuji Electric America, Right
Power Technology and Upsonic. Eight records report no full-load runtime and six
report no warranty, so those normalized fields remain null. The identical
maximum-model labels on one Mitsubishi and one Neuropower entry remain bounded
observations with no maximum W or VA. The Fuji certification retains its
reported 1,000 kW and 1,000 kVA minimum rating; the unbound maximum-W cell is
not normalized because no maximum configuration is identified.
The ENERGY STAR Enterprise Servers continuation processes all 20 Cisco Systems
entries in the complete 476-row EPA dataset snapshot. Each record retains the
immutable certification ID, model and form factor plus separately bounded low,
typical/single and high SERT configurations. CPU, installed-memory, storage,
PSU-nameplate, idle-power and workload-score observations are not combined into
a synthetic rated server input or rack power, and maximum supported memory is
not treated as installed memory. Three entries have a processor-socket count in
the model label that conflicts with the dataset's socket-count attribute; both
values remain in `conflicts_json`, the scalar is left null and the records remain
`needs_review`. Certification entries are exact issuer records, not deployments.
The Fujitsu continuation processes all 20 Fujitsu Limited entries from the same
registered snapshot. Each PRIMERGY certification remains a distinct immutable
issuer entry with exact model, form factor, socket attribute and separate low,
typical/single and high SERT test configurations. All 20 socket attributes are
internally consistent with their model labels. PSU nameplates, idle watts,
benchmark scores and maximum supported memory remain bounded observations rather
than rated server/rack input or installed memory; certifications are not treated
as deployments.
The xFusion continuation processes every one of the 31 xFusion Digital
Technologies entries in the same issuer snapshot. The exact 1158H, 1258H,
1288/1288H, 2158H, 2258/2258H, 2288/2288H, 2488H, 5298, 5885H and G-series
certification identities remain distinct even where model names repeat. Platform
socket count remains separate from the one-, two- or four-processor population
reported in each SERT configuration; `-1P` and `-2P` suffixes are not used to
overwrite the issuer socket attribute. Certification records remain issuer test
entries rather than deployments, and their PSU, idle-power, benchmark and
maximum-memory observations do not become server/rack input or installed memory.
The Nutanix and Hitachi Vantara continuation processes all 19 and 16 issuer
entries respectively. Eighteen Nutanix entries retain low-end, typical/single
and high-end SERT configurations; one Nutanix entry retains only its reported
typical/single configuration. Fifteen Hitachi entries report only a
typical/single configuration and HA835 G3 1P reports low-end plus typical/single.
Missing configuration tiers remain absent rather than being synthesized. Hitachi
`1P`/`2P`/`4P` model labels remain distinct from platform socket capacity and
tested installed-processor counts. PSU nameplates, idle watts, benchmark scores
and maximum supported memory remain observations rather than rated input,
installed memory or deployments.
The HPE continuation processes all 100 Hewlett Packard Enterprise issuer
entries across 89 model names, 71 rack servers, 21 blade entries and eight
tower/pedestal entries. Ninety-nine certifications retain low-end,
typical/single and high-end SERT configurations; the HPE ProLiant Compute DL110
Gen12 retains only its reported typical/single configuration. `1P`/`2P`/`4P`
model text remains identity and tested-population evidence rather than a
replacement for the issuer's platform socket attribute. Alletra, Apollo, Cray,
Edgeline, ProLiant, Superdome and Synergy certifications remain issuer test
entries, not deployments or evidence of rated server/rack input.
The Dell continuation processes all 123 Dell Inc. issuer entries across 44
exact model names: 92 rack-mount, 16 multi-node, nine tower/pedestal and six
half-chassis blade certifications. One hundred twenty entries retain low-end,
typical/single and high-end SERT configurations; E127S and the two E128S
certifications retain only their reported typical/single configuration. Exact
`-1P` configuration labels remain distinct from the issuer's two-socket platform
capacity, so neither platform sockets nor tested processor population is
inferred from model text. DELL and DELL EMC brands remain source observations;
certification entries are not deployments, installed-memory evidence or rated
server/rack input.
The Super Micro continuation processes all 49 Super Micro Computer, Inc. issuer
entries: 39 rack-mount and ten multi-node certifications across 48 model-name
strings. All entries retain low-end, typical/single and high-end SERT observations.
Only 14 print tier-specific configuration IDs; the other 35 retain those IDs as
unknown while preserving the reported CPU, memory, storage, PSU and benchmark
values. Two `Greater than 4` socket attributes remain exact observations with no
invented scalar socket count. Supermicro and Super Micro Computer, Inc. brand
labels remain source observations under the existing Supermicro OEM identity.
The Lenovo server-certification continuation processes all 45 Lenovo Group
Limited issuer entries: 35 rack-mount, five tower/pedestal and five half-chassis
blade certifications across 29 model names. All retain low-end, typical/single
and high-end SERT observations. Forty print all three tier-specific configuration
IDs; two print only low-end, one prints typical and high-end, and two print none.
Absent identifiers remain unknown while the reported tier-qualified CPU, memory,
storage, PSU and benchmark observations remain intact. The one-, two- and
four-socket platform attributes remain separate from tested processor population.
The residual server-certification continuation exhausts the remaining 30 entries
in the same 476-row issuer snapshot: nine IBM, eight Aivres Systems entries sold
under the KAYTUS brand, six ZTE, three Altos, three Oracle and one Ace Computers.
IBM, ZTE and Oracle retain their reported three-tier SERT observations except
IBM Power S1014, which reports only low-end and typical/single. KAYTUS, Altos and
Ace retain only the reported typical/single tier. Empty tiers and identifiers are
not synthesized. ZTE certification 4654814 is labeled R5300 G5 but prints R5300
G6 for the high-end configuration ID; both issuer observations are preserved and
configuration-identity inference remains quarantined. PSU nameplates, benchmark
scores, maximum supported memory and certification status remain bounded evidence,
not rated server/rack input, installed memory or deployment claims.
The DOE CCMS continuation adds every one of the first 50 displayed current
low-voltage dry-type transformer basic-model rows: 27 three-phase 15 kVA EATON
models, 15 three-phase 112.5 kVA models and eight single-phase 100 kVA models.
Exact basic-model identity, phase count, apparent kVA and represented efficiency
remain issuer-registry evidence. The displayed page omits the efficiency load/test
condition, so no generic efficiency scalar is normalized; kVA is not converted to
active kW and listing is not treated as a DOE compliance determination.
The independent medium-voltage dry-type continuation adds all 50 rows displayed
on its current DOE page: two Hitachi, two Hitran Corporation, four Howard
Industries, 23 JEI and 19 MGM basic models. Exact apparent kVA, phase count,
represented efficiency and BIL group rating remain bounded observations. BIL is
not treated as winding voltage, represented efficiency remains unnormalized
without a load/test condition, and no listing is promoted to a deployment or DOE
compliance determination.
The liquid-immersed transformer continuation adds all 50 rows displayed on the
current DOE basic-model page: 26 three-phase CMI configurations from 45 to
2,500 kVA and 24 single-phase configurations from 37.5 to 833 kVA. Exact model
strings are immutable identities; their numeric suffixes are not decoded into
winding voltage, dielectric fluid, temperature rise or ordered options. The
displayed table again omits efficiency load/test conditions, so represented
efficiency remains an observation and apparent kVA is never converted to active
kW. Direct source-byte access returned HTTP 403 and is recorded as an access
limitation rather than a reuse prohibition.
The Finnish permit continuation enriches four existing atNorth records from six
bounded municipal observations without adding duplicate phases. FIN02 now carries
decision 468/2026 and its public Sinimäentie 6a address. FIN04 retains the exact
40285 m2 and 18737 m2 building boundaries from permits 286-2025-165 and
286-2026-178 as observations rather than campus area, while the relationship
between the separately named FIN04A Phase 2 environmental case and the existing
July 2026 YIT phase remains quarantined. FIN05 keeps 60 MW phase IT load separate
from the municipality's 75 MW first-phase electrical demand, and its EUR 2 billion
operator investment separate from up-to-EUR 10 billion of possible customer-owned
server and installation investment.
The Nordic reconciliation continuation adds the previously omitted atNorth FIN03
facility as an operational Helsinki-metro identity without allocating the combined
FIN01/FIN03 3.2 MW observation to either site. It separates DEN01's Q4 2025
first-phase live milestone from the Q1 2026 campus-operational milestone and moves
DEN02 to permitted status from a dated local-plan approval while keeping its 60 MW
first-phase and up-to-500 MW campus statements unclassified. Municipal evidence for
SWE04 now binds the 200 MW phase-one grid connection to E.ON and keeps it separate
from 300 MW planned project power and 500 MW Hamre industrial-park capacity. The
conflicting H1 2028 and autumn 2028 commissioning targets remain quarantined.
The current permit reconciliation binds FIN04A Phase 2 to Kouvola permit
286-2025-384 and retains exact, separately scoped observations for FIN04A Phase 3
(286-2026-281), the FIN04B modification (286-2026-282) and FIN04C Phase 2
(286-2026-277). Their building areas are not promoted to campus or data-hall area,
and the generic YIT contract records are not assigned to a permit phase without an
official cross-reference. SWE04 additionally retains 1,200 MW of planned backup
combustion fuel input, two 130 kV line-project observations and a heat-reuse
development agreement. None is normalized as IT/grid capacity, commissioned
facility power or delivered heat; the line project's March 2029 completion target
does not resolve the facility commissioning conflict.
The liquid-cooling continuation adds all eight models in Motivair's CDU 2026
table and six exact nVent catalogue configurations. Motivair's four cooling
rating points, primary/secondary flows, pump head, dimensions, electrical options
and protocols remain model-bound. Its normalized cooling-capacity field is
quarantined because the row labels 25% propylene glycol while footnote 1 says
capacities use 100% water. nVent CDU40/CDU100 dry and filled SKUs stay separate;
CDU800 generation 3.2 US/Germany SKUs retain their shared 800 kW point and the
separate 575 kW GB200-NVL72 application rating.
The power-distribution continuation adds all 16 rows in Eaton's two current
7.2--12 kV dry-type transformer tables and all five variants on Siemens' current
NXAIR portfolio page. Transformer kVA is never converted to active kW; table
losses, impedance and noise remain bounded observations. Siemens voltage,
short-circuit current and continuous-current values are portfolio maxima, not
nominal inputs or ordered-panel configurations.
The compute-system continuation processes every supported checkmark in Dell's
October 2026 PowerEdge generation-specific compatibility tables: 33 exact 17th,
52 exact 16th and 23 exact 15th Generation server/accelerator pairings. The
accepted PDF is checksummed, and its printed revision/page locators correct the
earlier evidence transcription while stable record/source identities remain.
Per-accelerator maximum power and memory remain distinct from unknown server and
rack input; accelerator quantity and deployment are not inferred. The H100 NVL
350--400 W range remains an exact observation rather than a normalized scalar.
All 85 cells in the same document's Shipping tables are processed separately:
53 add documented configurations and 32 enrich exact existing pairs. Sixty-six
parenthesized quantities remain configuration-dependent OEM maximum observations,
not installed accelerator counts; 19 blank quantities remain null. Generic L4
shipping rows do not select HHHL or FHHL because the source explicitly withholds
platform-to-SKU association.
The Lenovo continuation processes all 20 rows explicitly marked Available in the
current ThinkSystem GPU comparison. Exact commercial part numbers or CTO feature
codes, option GPU counts, form factors, announcement dates, per-GPU memory,
bandwidth, TDP, interconnect, cooling and precision-labelled performance remain
source-bound. Option quantities are not deployments and per-GPU values are never
multiplied into board, server or rack input. The C3V2 H200 row's 700 W description
versus 350 W TDP conflict is quarantined, leaving normalized power null.

Never generate configurations by combining optional specification values. Model
punctuation and variant identifiers matter. Accelerator power limits, server
input and rack power are different quantities. Active kW is separate from kVA;
UPS runtime requires a stated load. Cooling capacity requires rating temperatures
and conditions; flow does not imply cooling kW. Nominal/usable battery energy,
state of charge, runtime and warranty conditions belong in explicit observations.
Memory values state their boundary (per GPU or aggregate system GPU memory).

`equipment_record_ids` joins disclosed installations only. There are no verified
model-to-facility installation links in this initial batch. Battery project and
product relationships use `bess_project_record_ids` and `bess_equipment_record_ids`
validated against existing catalogues; no competing battery records are created.

## Reproduce the snapshot

```bash
uv sync --locked --all-packages --group docs
uv run python -m energy_data_retrieval.data_center_catalogue validate
uv run python -m energy_data_retrieval.data_center_catalogue build --output artifacts/data-centers-v1
uv run python examples/database/plot_data_center_catalogue.py
```

Git stores canonical JSONL, sources, schema and research ledgers. The build creates
immutable Zstandard `projects.parquet` and `equipment.parquet`, with union typed
columns, UTC timestamps, nested JSON strings, sources, schema and deterministic
coverage/checksum manifest. All unknown columns are null in Parquet. Outputs use
new directories so published snapshots are never overwritten. The docs build
creates matching checksum-linked browser projections through the existing PV
analysis export API. No external data request is made during tests or docs builds.

```python
from pathlib import Path
import pandas as pd
from energy_data_retrieval.data_center_catalogue import load_records, capacity_summary

root = Path("catalogues/data_centers")
rows = load_records(root)
print(capacity_summary(rows, "it_capacity_mw"))
projects = pd.read_parquet("artifacts/data-centers-v1/projects.parquet")
equipment = pd.read_parquet("artifacts/data-centers-v1/equipment.parquet")
# Simulator inputs require explicit compatible boundaries; do not fill nulls.
server_inputs = equipment.loc[
    equipment.equipment_category.eq("server") & equipment.input_power_kw.notna(),
    ["record_id", "model", "input_power_kw", "power_conditions", "sources"],
]
print(server_inputs)
```

`datacenter-simulator` can consume these ordinary Parquet tables and stable IDs
without a change to that repository. Select source-backed fields, decode nested
JSON, preserve nulls and explicitly choose capacity basis before constructing a
simulation. This is an interchange example, not a claim that a simulator adapter
has been installed or tested in that separate repository.

## Evidence, rights and continued research

Every non-administrative field has registered source IDs and evidence detail,
including locator, confidence and normalized unit. Sources retain retrieval date,
publication date when known, revision and original-byte SHA-256 when retrievable.
Original copyrighted pages/PDFs are not redistributed. The current Motivair and
nVent tables were readable through the public web reader, while direct byte
requests returned HTTP 403. Eaton's indexed tables were complete but the original
page request timed out; the Siemens page returned an unsupported-content response
to the reader. These access failures and unavailable checksums are explicitly
registered without treating them as reuse prohibitions. Public access does not
imply an open licence. Explicit reuse restrictions remain separate.
Lenovo's official comparison HTML was captured and checksummed; its embedded
structured payload is parsed by a fail-closed offline adapter while the original
page is not redistributed. Supermicro's current certification table and both
front-I/O B200 product pages were captured and checksummed after the earlier
collateral URL returned HTML instead of a PDF. The complete B200/B300 table is
parsed offline; duplicate status rows collapse only when every hardware field
agrees.
Fuji Electric's current North American portfolio HTML, three exact PDF data
sheets and the current global UPS7500WX specification page were all captured and
checksummed. The older UPS7000HX exact table is accepted only because the current
portfolio independently lists that family; its printed ratings are not treated
as a claim that any optional upgrade path was ordered.

The upsert preserves creation dates and unchanged update dates. Conflicting
populated values are quarantined individually with both observations and dated
evidence; unrelated supported metadata survives. Resolving a conflict requires
review, not automatic selection of the larger/newer value.

The source-controlled [catalogue](https://github.com/julianascencio/energy-data-insights/tree/main/catalogues/data_centers)
contains a per-candidate decision ledger, source conditions, report, coverage
manifest and ranked backlog. Hourly continuation checks current main, open PRs and
these offsets before research. The targets of 50 projects and 20 exact models per
run never override identity, evidence or reuse requirements. NTT/PeeringDB bulk
sources remain on explicit reuse hold; OpenStreetMap fetch failures were access
problems and yielded no imported records.

## Nordic sites and coolant distribution units

The atNorth batch processes all 13 named sites in the current portfolio, plus
four separately documented buildings/phases linked to excluded campus parents.
Iceland and Norway are new coverage. Generic site/campus power remains a bounded
observation. FIN05 explicitly separates 230 MW gross planned capacity, up to
160 MW IT at campus level and 60 MW IT for its first phase; only the child
phase enters the ultimate-planned IT sum. FIN02's contractor reports 45 MW gross
capacity for the whole expanded facility, not the expansion alone.

The six-model current CoolIT CDU inventory retains cooling kW, electrical input,
approach temperature difference, flow/pressure conditions, redundancy and
protocols. Publicly linked AHx180/AHx240 brochures add dimensions, verified
visually. CHx3000's conflicting 45/50 °C ambient limits remain quarantined.
No compatible GPU rack is treated as a deployed or newly configured rack.

The completed CDU continuation covers Motivair's eight-model 2026 table and six
exact nVent HOFFMAN SKUs. Optional voltages were not expanded into invented products.
Older Motivair MCDU-30/MCDU-60 and nVent legacy CDU800 configurations remain
lifecycle candidates because they are absent from the selected current tables.

## Certified data-center storage configurations

The complete current EPA ENERGY STAR Data Center Storage exports contribute 120
exact issuer-certified configurations: 84 Block I/O and 36 File I/O entries.
Certification IDs, product/controller attributes, availability dates and each
reported test-configuration group remain reviewable observations. PSU nameplates
are not normalized as equipment or rack input; cache and device quantities are
test configurations rather than deployments; and workload-specific IOPS/W,
MiB/s/W and GB/W values are not collapsed into a generic efficiency percentage.
Five model names appear in both exports, but the records remain separate because
their Block I/O and File I/O certification identities and boundaries differ.

The official Block I/O CSV is 65,084 bytes with SHA-256
`2d1daab000dff286c0034b9144fa48a291acd58f4ace50a9514e1e9c3a659bc6`;
the File I/O CSV is 31,584 bytes with SHA-256
`fc55a7b3b62e2fe40d5e7d0f1cbaff6b7e727b76c7a5280ef401383dc27ff267`.

## Certified large network equipment

The complete EPA ENERGY STAR Large Network Equipment export contributes 96
exact issuer certifications: 91 switches and five routers from Extreme
Networks, Dell, Cisco and Huawei. Each certification retains its fixed/modular
classification, management characteristics, firmware, topology, compatible
chassis/modules, port and PoE facts and separate minimum, typical and maximum
test configurations.

Measured full-load, 30-percent-load and very-low-utilization watts retain the
printed port topology, throughput, utilization, voltage and frequency. They are
not generic rated device input or rack input. PSU outputs remain nameplates;
port, module, power-supply and PoE quantities are certification test facts, not
deployed inventory. The official 96-row, 223-column v3 CSV is 72,103 bytes with
SHA-256 `e769eedcef814b652ad6594b6cadb43b239e57e9250071a90cc133b07907e533`.

See the [continuation report](../catalogues/data_centers/research/2026-11-06-report.md)
and [executed validation](../catalogues/data_centers/research/2026-11-06T0958-validation.json).
