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

The `fullriver_terminal_case` extension retains exact-sheet terminal wording,
case material and a qualified flame-resistance claim. UL94-HB is a manufacturer
material-rating claim, not proof of product certification. Generic torque tables
are excluded unless applicable model-specific values are visually verified.

The `pylontech_force`, `pylontech_module` and `pylontech_unit` extensions retain
model-specific current classes and time limits, nominal/usable energy, charge and
discharge temperature ranges, strict altitude bounds and qualified life claims.
`module_record_id` links a stack to its exact module; named controllers do not
imply separately accepted controller records. Native dimension order is retained
when table axes are not explicit. Short-circuit A/ms is never operating current.

## November6 high-voltage and regional OEM observations

`extensions_json.pylontech_hv` retains the exact single-string/rack boundary,
module record ID/count, native energy rounding, charge/discharge current classes
and time limits, voltage bounds and qualified lifetime/efficiency claims.
PowerCube current rows lack an explicit unit; they remain native observations,
not normalized amperes or active power. Module-only facts do not inherit system IP.

`extensions_json.solarmd_specification` distinguishes cell supplier from module
manufacturer and records current/voltage limits, exact controller supply/contact
ratings, cycle conditions and charging-only efficiency. Logger supply/relay ratings
are never battery capacity. SS4083's power/C-rate inconsistency is quarantined in
`conflicts_json`; normalized power is null, other verified fields remain usable.

`solarmd_specification` also records exact SS70xx-05 module/rack relationships and
model-specific throughput-limited warranties. Unsuffixed historical models stay
separate. Charging efficiency, battery-only RTE and PCS conversion efficiency
have separate boundaries. Outdoor bundle cabinet weights are fully-loaded
observations, not exact configured-unit weights. Controller relay ratings are
not dielectric withstand ratings; BMU fuse/current limits are not PCS power.

`extensions_json.solarmd_legacy` preserves the unsuffixed SS7000 generation's
SS6143 module relationships, unspecified-class current rating, module-only usable
energy at0.3C, and exact-model warranty limits. Printed Rev1.0 is dated26April2024;
the April2025 URL path is not the revision. Charging efficiency is not RTE.

## Hubble exact warranties and Cube configurations

`extensions_json.hubble_warranty_20261106` separates the cell warranty's earlier-of
years/cycles limit from electronics coverage, strict battery-temperature conditions,
monitoring/registration requirements and remedy exclusions. These are public terms,
not a determination that a purchased unit qualifies. Conflicting three/five-year
HV100Ah monitoring fallback clauses remain in `conflicts_json`. Warranty cycles
do not overwrite design/test cycle life or imply retained capacity.

`extensions_json.hubble_cube` retains charge/discharge and AC/DC classes, exact
module/cell configuration, optional PV configurations and qualified mechanical,
efficiency and compliance observations. Unlabelled dimension axes and unresolved
IP54/IP55 or kW/kVA claims are not assigned normalized scalars. Marketing ten-year
battery claims do not establish applicability of the separate Cube V2 warranty.

### ATESS reviewed extensions

`extensions_json.atess` preserves product level, source section/column, distinct
AC/DC/rectifier ratings, current limits, conditional overloads, PV constraints,
conversion-efficiency boundary and OEM assertions with their qualifiers.
`native_formula_observations` records exact energy code/module count and explicit
source formula calculations; `module_record_id` links only the specifically named
component. Cluster cycle claims without test conditions remain qualified extension
observations, not warranty or normalized tested cycle life. Optional features do
not create models. IP66 battery-compartment protection does not replace system
IP55. IC418-800's printed AC range excludes its nominal voltage and remains a
conflict. Module/cluster mechanical and environmental boundaries remain separate.

`atess_battery` retains product level, explicit module/BPU counts, C-rates,
module/rack Ah, BMS and exact table locator. `module_record_id` connects only
VoltStack assemblies to their named module. BC55NPB has an unnamed, physically
different module; no link is inferred. Rack limits and protection are not module
limits. Published rounded ratings remain unchanged; arithmetic checks in
`conflicts_json` never become replacement specifications.

`intilion_scalepac` preserves exact enclosure counts, separately published usable
energy at 90% DoD, apparent-power upper bounds, approximate/strict mass qualifiers,
and time-versus-throughput warranty limits. The scalepac5 throughput `>` qualifier
is retained verbatim. Supplier role is system integrator, not cell manufacturer.
System-level RTE is not transferred to each tabulated enclosure configuration.

### INTILION i4, IAU and scalepac boundaries

`intilion_i4` represents the named two-container/one-PCS BESU. Example usable
AC energy at BOL remains customer-specific; internal container kWh is not
a complete-system energy scalar. PCS enclosure, inverter electrical limits,
peak conversion efficiency, transformer losses and switchgear fault ratings
retain component boundaries. MVA is never inferred MW. Optional IAU protocols
are not included hardware. Noise/design-life footnote ambiguity stays held.
`intilion_iau` represents the named supervisory controller, with no battery
energy/power assigned. Eight-BESU versus 64-BESU scaling claims remain in
conflicts; planned 24-ICU expansion is not current functionality.
`intilion_scalepac_grid` retains per-power-unit AC currents, not a sum across
a cabinet configuration. The 110%/minimum-ten-minute overload observation is
not a continuous active-power rating. No anonymous components become models.

### Renon configurations and ATESS impedance

`renon_specification` retains exact model column/page, module/string counts,
charge/discharge limits, EPS versus grid ratings, separate DC ports, approximate
mass/dimensions, thermal derating and explicit warranty limitations. CEC inverter
and peak DCDC conversion efficiency are not system RTE. Smart Matrix table kVA
and cover kW claims remain quarantined; no multi-container active power is inferred.
EBrick-IND's ambiguous cell-voltage labels, Ah/energy relationship and parallel
illustration/table counts remain native observations with conflict evidence.
R-CC01C00800 is an EMS communication cabinet; its 600 W air-conditioner rating is
not total auxiliary draw. Product relationships do not assign equipment to projects.

`atess_impedance_bms` adds model-column AC internal-resistance upper bounds in
milliohms, explicitly without test frequency/temperature, and the stated BMS
levels, BC55NPB LCD observations and protection functions. AC resistance is not
silently relabelled DC resistance; previous voltage/energy conflicts remain intact.
