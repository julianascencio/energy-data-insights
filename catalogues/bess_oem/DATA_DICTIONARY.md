# BESS OEM data dictionary

Schema **1.0.0**. All 73 columns exist in Parquet; missing values are null.

| Column | Type | Unit | Meaning |
| --- | --- | --- | --- |
| `record_id` | string | — | Stable UUID5 from manufacturer, exact model and variant; retain ID through renames. |
| `entity_type` | string | — | BESS OEM product/configuration table. Allowed: `systems`. |
| `name` | string | — | Display label; manufacturer, model and variant. |
| `manufacturer` | string | — | Product brand or system supplier as cited; does not imply cell manufacture. |
| `model` | string | — | Exact source product name or model code, preserving case and punctuation. |
| `variant` | string | — | Explicit region, revision, configuration or rating distinguishing this row. |
| `product_family` | string | — | Source-reported family when an exact model code is available. |
| `capacity_scope` | string | — | Physical unit described: cabinet, enclosure, string or configured system; not project capacity. |
| `market_scope` | string | — | Explicit region/market for this variant; unknown is null. |
| `chemistry` | string | — | Source-reported battery chemistry; not inferred from supplier. |
| `cell_manufacturer` | string | — | Named cell OEM only when explicitly sourced for this product. |
| `cell_model` | string | — | Exact cell model when sourced. |
| `cooling` | string | — | Source-reported thermal management. |
| `form_factor` | string | — | Source enclosure or assembly format; e.g. 20-foot container. |
| `document_revision` | string | — | Revision/date printed on the principal specification; not the retrieval date. |
| `power_conditions` | string | — | Source test/temperature conditions and derating for power. |
| `energy_conditions` | string | — | Energy measurement conditions, including BOL/FAT when stated. |
| `efficiency_conditions` | string | — | RTE test conditions and exclusions; do not assume auxiliaries included. |
| `cycle_life_conditions` | string | — | Cycle-life test conditions and end-of-life threshold; not a warranty. |
| `warranty_conditions` | string | — | Contractual conditions; design life is not warranty. |
| `derating_notes` | string | — | Ambient temperature, altitude and other source-reported derating conditions. |
| `ingress_protection` | string | — | Scope-specific enclosure IP rating; not pack IP substituted for enclosure. |
| `fire_protection` | string | — | Source-described safety equipment; not independent safety verification. |
| `pcs_model` | string | — | Explicit integrated PCS model. |
| `ems` | string | — | Source-reported energy management platform. |
| `notes` | string | — | Editorial interpretation, uncertainty, exclusions and limitations. |
| `record_scope` | string | — | A documented configuration or configurable product family; never a fabricated option combination. Allowed: `configuration`, `family`. |
| `market_segment` | string | — | Source-supported application segment. Allowed: `utility`, `commercial_industrial`, `residential`, `multiple`. |
| `architecture` | string | — | Product boundary; PCS integration only when explicitly stated. Allowed: `ac_integrated`, `dc_block`, `battery_cabinet`, `flow_system`, `unspecified`. |
| `product_status` | string | — | Document classification, not confirmation of current commercial availability. Allowed: `documented`, `preliminary`, `historical_document`. |
| `quality_status` | string | — | Evidence status; manufacturer claims are not independently validated performance. Allowed: `source_backed`, `needs_review`. |
| `power_basis` | string | — | Electrical boundary for power_capacity_mw. Allowed: `ac`, `dc`, `unspecified`. |
| `power_rating_kind` | string | — | Whether the power value is rated, maximum or unspecified. Allowed: `rated`, `maximum`, `unspecified`. |
| `energy_basis` | string | — | Meaning of energy_capacity_mwh; unknown basis must be explicit. Allowed: `nominal`, `usable`, `peak`, `unspecified`. |
| `energy_boundary` | string | — | Electrical boundary for the energy rating. Allowed: `ac`, `dc`, `unspecified`. |
| `efficiency_boundary` | string | — | Boundary for the manufacturer-reported RTE. Allowed: `ac_ac`, `dc_dc`, `system_unspecified`, `unspecified`. |
| `efficiency_qualifier` | string | — | Qualifier attached to the RTE; preserve upper/lower bounds. Allowed: `reported`, `maximum`, `minimum`, `approximate`. |
| `energy_capacity_mwh` | float | MWh | Documented single-configuration energy; family ranges belong in extensions. |
| `power_capacity_mw` | float | MW | Reported active power only; never apparent power or an E/P-derived estimate. |
| `apparent_power_mva` | float | MVA | Reported apparent AC power, separate from active MW. |
| `duration_hours` | float | h | Source-reported duration, never inferred from mixed-basis E/P. |
| `cell_capacity_ah` | float | Ah | Source cell capacity. |
| `dc_voltage_nominal_v` | float | V | Nominal battery DC voltage. |
| `dc_voltage_min_v` | float | V | Minimum operating DC voltage. |
| `dc_voltage_max_v` | float | V | Maximum operating DC voltage. |
| `ac_voltage_v` | float | V | Single reported nominal AC voltage; alternatives remain in extensions. |
| `round_trip_efficiency_pct` | float | % | Manufacturer-reported RTE; boundary, qualifier and conditions are mandatory. |
| `depth_of_discharge_pct` | float | % | Source-supported depth of discharge. |
| `cycle_life` | float | cycles | Source-reported cycle life; requires test conditions. |
| `design_life_years` | float | years | Source-reported design life; does not imply warranty. |
| `warranty_years` | float | years | Warranty term only when explicitly stated with conditions. |
| `width_m` | float | m | Unit width as defined in the cited document. |
| `depth_m` | float | m | Unit depth as defined in the cited document. |
| `height_m` | float | m | Unit height as defined in the cited document. |
| `weight_kg` | float | kg | Unqualified/rated unit mass; maximum mass uses weight_max_kg. |
| `weight_max_kg` | float | kg | Documented upper mass bound; strict/approximate qualifier retained in extensions. |
| `altitude_max_m` | float | m | Reported altitude limit; derating conditions must remain attached. |
| `operating_temperature_min_c` | float | degC | Minimum ambient operating temperature; not internal cell temperature. |
| `operating_temperature_max_c` | float | degC | Maximum ambient operating temperature; preserve derating. |
| `pcs_included` | bool | — | Integrated PCS explicitly present or excluded. |
| `grid_forming` | bool | — | Manufacturer explicitly states grid-forming capability. |
| `black_start` | bool | — | Manufacturer explicitly states black-start capability. |
| `communication_protocols` | list_string | — | Source-listed protocols; interfaces are separate. |
| `communication_interfaces` | list_string | — | Physical/network interfaces. |
| `sources` | list_string | — | Registered exact source IDs. |
| `source_urls` | list_string | — | Derived sorted unique source URLs; never manually inferred. |
| `field_sources_json` | json | — | Per-field source-ID lists; wildcard attribution is forbidden. |
| `compliance_claims_json` | json | — | Manufacturer claims with status/scope; test methods such as UL 9540A are not product certifications. |
| `extensions_json` | json | — | Namespaced optional specifications, bounds and configuration ranges. |
| `conflicts_json` | json | — | Conflicting source assertions with evidence; requires needs_review. |
| `created_at` | timestamp | — | UTC date of database record creation, not product launch. |
| `updated_at` | timestamp | — | UTC date of last substantive record change. |
| `last_verified_at` | timestamp | — | UTC source-check date; not physical validation or proof of availability. |
