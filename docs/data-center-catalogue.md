# Global Data Center Database

## Data Center Projects

The current continuation branch has 182 project records across 36 countries:
65 facilities, three phases and 114 explicitly scoped campus aggregates, from 13 operators.
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

## Data Center Equipment

The [equipment table](https://julianascencio.github.io/energy-data-insights/data-center-database-viewer.html?table=equipment)
has 640 exact models/configurations from NVIDIA, AMD, Carrier, CoolIT Systems, Cummins,
Daikin, Dell, Delta Electronics, Eaton, Envicool, Huawei Digital Power, Lenovo, Motivair by Schneider
Electric, Mitsubishi Electric, Fuji Electric, mtu, nVent HOFFMAN, Schneider Electric, Siemens,
STULZ, Supermicro, Toshiba and Vertiv. Current categories are GPU accelerators,
servers, UPS, rack PDUs, backup generators, chillers, coolant distribution units
and CRAC/CRAH precision air-conditioning equipment, transformers and switchgear.
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

See the [continuation report](../catalogues/data_centers/research/2026-11-03-report.md)
and [executed validation](../catalogues/data_centers/research/2026-11-03T1419-validation.json).
