# Global Data Center Database

## Data Center Projects

The current open-branch catalogue has 123 project records across 23 countries:
53 facilities and 70 explicitly scoped campus aggregates, from eight operators.
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
has 123 exact models/configurations from NVIDIA, AMD, Eaton, Schneider Electric,
STULZ and Vertiv. Current categories are GPU accelerators, servers, UPS, rack PDUs,
coolant distribution units and CRAC/precision air-conditioning equipment.
Switchgear, transformers, generators and additional cooling categories are
supported by schema and ranked in the continuation backlog. The Schneider Galaxy
VS batch preserves exact commercial references, stated kW and kVA, battery-string
arrangements, full-load efficiency conditions and dimensions without calculating
battery energy or runtime.
The STULZ batch keeps 30 fixed-speed R410A ASR/ALR configurations separate,
normalizes net sensible cooling only at the stated return-air/condensing/ESP
rating point, and preserves total sensible cooling and component power as
observations. R134a and modulating variants are not combined with these rows.

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
publication date when known, revision and original-byte SHA-256. All accepted
sources were fetched successfully; original copyrighted pages/PDFs are not
redistributed. Public access does not imply an open licence. Access failures and
explicit reuse restrictions are recorded separately.

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
