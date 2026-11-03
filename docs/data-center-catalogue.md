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
has 280 exact models/configurations from NVIDIA, AMD, Carrier, CoolIT Systems, Cummins, Eaton,
Motivair by Schneider Electric, nVent HOFFMAN, Schneider Electric, Siemens, STULZ and Vertiv. Current categories are GPU accelerators,
servers, UPS, rack PDUs, backup generators, chillers, coolant distribution units
and CRAC/precision air-conditioning equipment, transformers and switchgear.
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
and [executed validation](../catalogues/data_centers/research/2026-11-03T1119-validation.json).
