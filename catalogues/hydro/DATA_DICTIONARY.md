# Hydropower data dictionary

Schema version 1.0.0. Unknown values are null or omitted. All populated factual fields require provenance.

| Field | Type | Unit | Meaning |
|---|---|---|---|
| record_id | string |  | Stable UUID; retain through renames and changes in capacity. |
| name | string |  | Identifiable facility, phase or exact equipment name. |
| capacity_scope | string |  | Physical boundary and configuration covered by reported ratings. |
| notes | string |  | Review notes; no unsupported technical facts. |
| country_code | string |  | ISO alpha-3 country code. |
| location_accuracy | string |  | Precision and method of public coordinates. |
| parent_record_id | string |  | Optional parent project UUID in this catalogue. |
| overlap_group | string |  | Stable group for overlapping capacity observations. |
| status_date_basis | string |  | Publication date or dated retrieval of undated evidence. |
| entity_type | string |  | Connected catalogue table. |
| record_scope | string |  | Physical identity granularity. |
| aggregation_role | string |  | Only independent or child records can contribute to sums. Aggregate and unresolved scopes are excluded even if filtered children are absent. |
| status | string |  | Last evidenced project lifecycle; a portfolio listing alone does not establish operation. |
| quality_status | string |  | Evidence qualification; does not certify a facility or product. |
| created_at | timestamp |  | UTC timestamp; updated_at changes only on substantive data/evidence changes. |
| updated_at | timestamp |  | UTC timestamp; updated_at changes only on substantive data/evidence changes. |
| last_verified_at | timestamp |  | UTC timestamp; updated_at changes only on substantive data/evidence changes. |
| status_as_of | string |  | ISO date; only precise reported dates, never a forecast treated as achieved. |
| aliases | list_string |  | Explicit evidenced values; linked IDs refer to existing canonical records. |
| sources | list_string |  | Explicit evidenced values; linked IDs refer to existing canonical records. |
| source_urls | list_string |  | Explicit evidenced values; linked IDs refer to existing canonical records. |
| owner_names | list_string |  | Explicit evidenced values; linked IDs refer to existing canonical records. |
| operator_names | list_string |  | Explicit evidenced values; linked IDs refer to existing canonical records. |
| developer_names | list_string |  | Explicit evidenced values; linked IDs refer to existing canonical records. |
| external_ids_json | json |  | Namespace to exact public identifier. |
| field_sources_json | json |  | Map each populated factual column to registered source IDs. No wildcard evidence. |
| evidence_json | json |  | Field-level locator, units, publication date/revision and confidence; keys match field_sources_json. |
| estimates_json | json |  | Derived estimates with method and uncertainty, never substituted into reported columns. |
| conflicts_json | json |  | Quarantined field observations and source dates/boundaries; unresolved numeric fields must be null. |
| extensions_json | json |  | Extra documented metadata with units and conditions. |
| latitude | float | degrees | Public source coordinate; no inferred centroids. |
| longitude | float | degrees | Public source coordinate; no inferred centroids. |
| technology | string |  | technology |
| observations_json | json |  | observations json |
| installed_capacity_mw | float | MW | Reported capacity at its explicit boundary; never substituted from turbine ratings. |
| planned_capacity_mw | float | MW | Reported capacity at its explicit boundary; never substituted from turbine ratings. |
| historical_capacity_mw | float | MW | Reported capacity at its explicit boundary; never substituted from turbine ratings. |
| capacity_reference_year | int |  | capacity reference year |
| turbine_count | int |  | turbine count |
| pumping_capacity_mw | float | MW | Electrical input in pumping mode |
| operational_capacity_mw | float | MW | Dated operational generating capacity |
| storage_capacity_mwh | float | MWh | Explicitly reported usable electrical storage; never reservoir volume |
| gross_head_m | float | m | Gross hydraulic head |
| net_head_m | float | m | Net hydraulic head |
| design_flow_m3_s | float | m3/s | Design hydraulic flow |
| reservoir_volume_m3 | float | m3 | Total reservoir volume |
| usable_reservoir_volume_m3 | float | m3 | Usable reservoir volume |
| river | string |  | Reported river |
| basin | string |  | Reported river basin |
| dam_name | string |  | Reported dam |
| reservoir_name | string |  | Reported reservoir |
| turbine_type | string |  | Reported turbine type |
| turbine_model | string |  | Exact reported turbine model |
| manufacturer | string |  | Reported turbine manufacturer |
| commissioning_date | string |  | Reported commissioning date and precision |
| refurbishment_date | string |  | Reported refurbishment date and precision |
| grid_connection | string |  | Reported grid connection |
| cost_observations_json | json |  | Costs with currency, year and basis |
| environmental_constraints | string |  | Publicly documented constraints |
| cross_catalogue_links_json | json |  | Reviewed links to other catalogue identities |

### ONS state and dispatch metadata

`extensions_json.ons_dispatch_metadata` exposes `id_estado`, `nom_estado`,
`id_subsistema`, `nom_subsistema` and `nom_modalidadeoperacao` from reviewed unit
observations. Each contains distinct `values` and `evidence` entries with
`value`, `source_id` and original CSV `row`. Empty values mean unreported;
multiple values are preserved, not silently collapsed. These describe the
reported state, electrical subsystem and dispatch modality at the source
observation, not an exact connection point or present operating status.


### Reviewed ONS components

`extensions_json.ons_components` links stable UUIDv5 `component_id` values to
`parent_record_id`, reported powerhouse `name`, `generating_unit_ids` (ONS
equipment IDs), and `source_ids`. The relationship is `powerhouse_of`; the role
`excluded_component_evidence` prevents interpreting components as additional
plants or capacity totals. Scope rationale and reported technical context live
in `ons_component_review`, with a primary `scope_source_id` and locator.


### New ONS identities

`extensions_json.ons_new_identity_review` records the full CEG, source name,
explicit acceptance rationale and collision screen. UUIDv5 uses the immutable
`ANEEL-CEG` namespace and complete CEG; historical WRI identifiers are never
fabricated. Nested source retrieval timestamps differ from acceptance time.
Reviewed plant facts use their own source IDs and locators in field evidence.
`deferred_capacity_review`, when present, retains differing reported plant and
unit ratings outside canonical capacity totals until their bases are reconciled.

### AHA field provenance

`extensions_json.aha_field_provenance` contains one observation per populated
reviewed technical column: `column`, `value`, `unit`, `basis`, `source_id`,
`excel_row`, `upstream_reference`, `fallback_reference`,
`upstream_independently_verified` and `uncertainty`. Zero values are retained;
missing references are null. Dataset model references are not official registry
IDs. These observations never automatically populate current capacity, storage
energy, operating flow or commissioning fields.

KenGen report observations retain `installed_capacity_mw`,
`effective_capacity_mw`, `annual_generation_gwh` and `sold_energy_gwh` as distinct
nested fields. `period` names the fiscal year ending June 30, not a calendar
year. Values are owner-reported, with original tokens and unquantified source
uncertainty. A dash maps to null; zero remains zero. These dated observations do
not fill current operational capacity or status and are not added to map KPIs.

Owner-reviewed accessions use the `reviewed-accession` UUID namespace. The frozen
accession is retained in `extensions_json`; `external_ids_json` stays empty until
an official registry identifier is verified. A later rename or capacity change
must preserve this accession. Name normalization only detects insertion conflicts.

`extensions_json.kengen_technical_assertions` holds keyed owner assertions with
value, unit, basis, locator and uncertainty. Equipment dictionaries identify
original/replacement groups and explicitly labelled `each_mva` versus `each_mw`.
Linked upstream/downstream stations use canonical record IDs; they are flow
relationships, not parent/child capacities. These source assertions are not
current canonical ratings or resolved historical dates.

### Uganda ERA annual capacity evidence

`observations_json` entries from `uganda-era-capacity-202609` use
`field=installed_capacity_mw`, `unit=MW`, explicit year/September-2026 periods,
and Excel cell plus station locators. Null source cells are retained, distinct
from explicit zero. These are dated reported statistics, not canonical current
installed/operational MW or pumping input. `extensions_json.era_inventory`
retains the source station label and grid/mini-hydro section;
`era_identity_review` holds the frozen catalogue accession, reviewed aliases and
Annex 3 identity locator. Accessions are not national licence identifiers.
`aggregation_role=unresolved` excludes these records from additive capacity KPIs.

`extensions_json.era_2023_assertions.facts` preserves the ERA Annex 3 commissioning,
capacity, grid and lifecycle columns with per-column locators and a 2023 basis.
A decade remains a decade, missing commissioning remains null, and the combined
construction/licensed group remains combined. Canonical current fields are not
inferred from this historical table.
