# PV catalogue data dictionary

Schema version: 1.0.0. All fields are nullable except the required record/provenance fields.

| Column | Type | Unit | Meaning |
| --- | --- | --- | --- |
| `record_id` | string | — | record_id; unknown is null, never an inferred value. |
| `entity_type` | string | — | entity_type; unknown is null, never an inferred value. |
| `name` | string | — | name; unknown is null, never an inferred value. |
| `manufacturer` | string | — | manufacturer; unknown is null, never an inferred value. |
| `model` | string | — | model; unknown is null, never an inferred value. |
| `variant` | string | — | variant; unknown is null, never an inferred value. |
| `country_code` | string | — | country_code; unknown is null, never an inferred value. |
| `region` | string | — | region; unknown is null, never an inferred value. |
| `locality` | string | — | locality; unknown is null, never an inferred value. |
| `status` | string | — | status; unknown is null, never an inferred value. |
| `technology` | string | — | technology; unknown is null, never an inferred value. |
| `market_scope` | string | — | market_scope; unknown is null, never an inferred value. |
| `product_url` | string | — | product_url; unknown is null, never an inferred value. |
| `datasheet_url` | string | — | datasheet_url; unknown is null, never an inferred value. |
| `source_release` | string | — | source_release; unknown is null, never an inferred value. |
| `source_date` | string | — | source_date; unknown is null, never an inferred value. |
| `location_accuracy` | string | — | location_accuracy; unknown is null, never an inferred value. |
| `commissioning_date` | string | — | commissioning_date; unknown is null, never an inferred value. |
| `decommissioning_date` | string | — | decommissioning_date; unknown is null, never an inferred value. |
| `mounting_type` | string | — | mounting_type; unknown is null, never an inferred value. |
| `tracker_type` | string | — | tracker_type; unknown is null, never an inferred value. |
| `module_orientation` | string | — | module_orientation; unknown is null, never an inferred value. |
| `drive_type` | string | — | drive_type; unknown is null, never an inferred value. |
| `power_supply` | string | — | power_supply; unknown is null, never an inferred value. |
| `cooling_method` | string | — | cooling_method; unknown is null, never an inferred value. |
| `insulation_method` | string | — | insulation_method; unknown is null, never an inferred value. |
| `ip_rating` | string | — | ip_rating; unknown is null, never an inferred value. |
| `enclosure_material` | string | — | enclosure_material; unknown is null, never an inferred value. |
| `surge_protection` | string | — | surge_protection; unknown is null, never an inferred value. |
| `connector_type` | string | — | connector_type; unknown is null, never an inferred value. |
| `grid_operator` | string | — | grid_operator; unknown is null, never an inferred value. |
| `substation` | string | — | substation; unknown is null, never an inferred value. |
| `currency` | string | — | currency; unknown is null, never an inferred value. |
| `capacity_basis` | string | — | capacity_basis; unknown is null, never an inferred value. |
| `quality_status` | string | — | quality_status; unknown is null, never an inferred value. |
| `notes` | string | — | notes; unknown is null, never an inferred value. |
| `created_at` | timestamp | — | UTC created_at. Creation is immutable; updates mean content changes; verification means source checked. |
| `updated_at` | timestamp | — | UTC updated_at. Creation is immutable; updates mean content changes; verification means source checked. |
| `last_verified_at` | timestamp | — | UTC last_verified_at. Creation is immutable; updates mean content changes; verification means source checked. |
| `aliases` | list_string | — | aliases; ordered unique strings. Equipment IDs link to canonical records. |
| `owners` | list_string | — | owners; ordered unique strings. Equipment IDs link to canonical records. |
| `developers` | list_string | — | developers; ordered unique strings. Equipment IDs link to canonical records. |
| `epc_contractors` | list_string | — | epc_contractors; ordered unique strings. Equipment IDs link to canonical records. |
| `operators` | list_string | — | operators; ordered unique strings. Equipment IDs link to canonical records. |
| `offtakers` | list_string | — | offtakers; ordered unique strings. Equipment IDs link to canonical records. |
| `certifications` | list_string | — | certifications; ordered unique strings. Equipment IDs link to canonical records. |
| `communication_protocols` | list_string | — | communication_protocols; ordered unique strings. Equipment IDs link to canonical records. |
| `module_record_ids` | list_string | — | module_record_ids; ordered unique strings. Equipment IDs link to canonical records. |
| `inverter_record_ids` | list_string | — | inverter_record_ids; ordered unique strings. Equipment IDs link to canonical records. |
| `tracker_record_ids` | list_string | — | tracker_record_ids; ordered unique strings. Equipment IDs link to canonical records. |
| `combiner_record_ids` | list_string | — | combiner_record_ids; ordered unique strings. Equipment IDs link to canonical records. |
| `sources` | list_string | — | sources; ordered unique strings. Equipment IDs link to canonical records. |
| `source_urls` | list_string | — | source_urls; ordered unique strings. Equipment IDs link to canonical records. |
| `field_sources_json` | json | — | field_sources_json: canonical JSON object (phases is a list); preserves nested/source-specific information. |
| `extensions_json` | json | — | extensions_json: canonical JSON object (phases is a list); preserves nested/source-specific information. |
| `phases_json` | json | — | phases_json: canonical JSON object (phases is a list); preserves nested/source-specific information. |
| `external_ids_json` | json | — | external_ids_json: canonical JSON object (phases is a list); preserves nested/source-specific information. |
| `bifacial` | bool | — | bifacial; null means unknown, not false. |
| `bipv` | bool | — | bipv; null means unknown, not false. |
| `hybrid` | bool | — | hybrid; null means unknown, not false. |
| `string_monitoring` | bool | — | string_monitoring; null means unknown, not false. |
| `dc_switch` | bool | — | dc_switch; null means unknown, not false. |
| `backtracking` | bool | — | backtracking; null means unknown, not false. |
| `pmax_stc_w` | float | W | pmax_stc_w; nameplate or reference rating as stated, not a simulation result. |
| `ptc_w` | float | W | ptc_w; nameplate or reference rating as stated, not a simulation result. |
| `pac_rated_w` | float | W | pac_rated_w; nameplate or reference rating as stated, not a simulation result. |
| `pdc_rated_w` | float | W | pdc_rated_w; nameplate or reference rating as stated, not a simulation result. |
| `startup_power_w` | float | W | startup_power_w; nameplate or reference rating as stated, not a simulation result. |
| `standby_power_w` | float | W | standby_power_w; nameplate or reference rating as stated, not a simulation result. |
| `voc_v` | float | V | voc_v; DC and AC ratings must not be interchanged. |
| `vmp_v` | float | V | vmp_v; DC and AC ratings must not be interchanged. |
| `system_voltage_max_v` | float | V | system_voltage_max_v; DC and AC ratings must not be interchanged. |
| `vdc_rated_v` | float | V | vdc_rated_v; DC and AC ratings must not be interchanged. |
| `vdc_max_v` | float | V | vdc_max_v; DC and AC ratings must not be interchanged. |
| `mppt_min_v` | float | V | mppt_min_v; DC and AC ratings must not be interchanged. |
| `mppt_max_v` | float | V | mppt_max_v; DC and AC ratings must not be interchanged. |
| `vac_rated_v` | float | V | vac_rated_v; DC and AC ratings must not be interchanged. |
| `isc_a` | float | A | isc_a; retain per-input versus aggregate context in extensions. |
| `imp_a` | float | A | imp_a; retain per-input versus aggregate context in extensions. |
| `idc_max_a` | float | A | idc_max_a; retain per-input versus aggregate context in extensions. |
| `string_current_max_a` | float | A | string_current_max_a; retain per-input versus aggregate context in extensions. |
| `output_current_max_a` | float | A | output_current_max_a; retain per-input versus aggregate context in extensions. |
| `fuse_rating_max_a` | float | A | fuse_rating_max_a; retain per-input versus aggregate context in extensions. |
| `efficiency_stc_pct` | float | % | efficiency_stc_pct; percentage 0–100, not fraction. |
| `efficiency_max_pct` | float | % | efficiency_max_pct; percentage 0–100, not fraction. |
| `efficiency_euro_pct` | float | % | efficiency_euro_pct; percentage 0–100, not fraction. |
| `bifaciality_pct` | float | % | bifaciality_pct; percentage 0–100, not fraction. |
| `power_tolerance_plus_pct` | float | % | power_tolerance_plus_pct; percentage 0–100, not fraction. |
| `annual_degradation_warranty_pct` | float | % | annual_degradation_warranty_pct; percentage 0–100, not fraction. |
| `first_year_degradation_warranty_pct` | float | % | first_year_degradation_warranty_pct; percentage 0–100, not fraction. |
| `slope_ns_max_pct` | float | % | slope_ns_max_pct; percentage 0–100, not fraction. |
| `slope_ew_max_pct` | float | % | slope_ew_max_pct; percentage 0–100, not fraction. |
| `gcr_min_pct` | float | % | gcr_min_pct; percentage 0–100, not fraction. |
| `gcr_max_pct` | float | % | gcr_max_pct; percentage 0–100, not fraction. |
| `gamma_pmax_pct_per_c` | float | %/degC | gamma_pmax_pct_per_c; relative temperature coefficient. |
| `beta_voc_pct_per_c` | float | %/degC | beta_voc_pct_per_c; relative temperature coefficient. |
| `alpha_isc_pct_per_c` | float | %/degC | alpha_isc_pct_per_c; relative temperature coefficient. |
| `alpha_isc_a_per_c` | float | A/degC | Absolute Isc temperature coefficient. |
| `beta_voc_v_per_c` | float | V/degC | Absolute Voc temperature coefficient. |
| `noct_c` | float | degC | noct_c; NOCT and NMOT are distinct; conditions belong in extensions. |
| `operating_temperature_min_c` | float | degC | operating_temperature_min_c; NOCT and NMOT are distinct; conditions belong in extensions. |
| `operating_temperature_max_c` | float | degC | operating_temperature_max_c; NOCT and NMOT are distinct; conditions belong in extensions. |
| `length_m` | float | m | length_m; orientation retained from OEM. |
| `width_m` | float | m | width_m; orientation retained from OEM. |
| `height_m` | float | m | height_m; orientation retained from OEM. |
| `area_m2` | float | m2 | Reference area reported by source; do not assume aperture versus total. |
| `weight_kg` | float | kg | Mass. |
| `cells_in_series` | int | — | cells_in_series; exact integer only. Approximate counts belong in extensions. |
| `cell_count` | int | — | cell_count; exact integer only. Approximate counts belong in extensions. |
| `mppt_count` | int | — | mppt_count; exact integer only. Approximate counts belong in extensions. |
| `strings_per_mppt` | int | — | strings_per_mppt; exact integer only. Approximate counts belong in extensions. |
| `input_count` | int | — | input_count; exact integer only. Approximate counts belong in extensions. |
| `output_count` | int | — | output_count; exact integer only. Approximate counts belong in extensions. |
| `module_count` | int | — | module_count; exact integer only. Approximate counts belong in extensions. |
| `inverter_count` | int | — | inverter_count; exact integer only. Approximate counts belong in extensions. |
| `tracker_count` | int | — | tracker_count; exact integer only. Approximate counts belong in extensions. |
| `commissioning_year` | int | — | commissioning_year; exact integer only. Approximate counts belong in extensions. |
| `product_warranty_years` | float | year | product_warranty_years; published standard warranty, regional options remain separate. |
| `performance_warranty_years` | float | year | performance_warranty_years; published standard warranty, regional options remain separate. |
| `structural_warranty_years` | float | year | structural_warranty_years; published standard warranty, regional options remain separate. |
| `drive_warranty_years` | float | year | drive_warranty_years; published standard warranty, regional options remain separate. |
| `tracking_min_deg` | float | degree | tracking_min_deg; angles in degrees; WGS84 coordinates and north-clockwise azimuth. |
| `tracking_max_deg` | float | degree | tracking_max_deg; angles in degrees; WGS84 coordinates and north-clockwise azimuth. |
| `tilt_deg` | float | degree | tilt_deg; angles in degrees; WGS84 coordinates and north-clockwise azimuth. |
| `azimuth_deg` | float | degree | azimuth_deg; angles in degrees; WGS84 coordinates and north-clockwise azimuth. |
| `latitude` | float | degree | Source-reported decimal degrees; coordinate datum and positional accuracy must be preserved, not assumed to be surveyed. |
| `longitude` | float | degree | Source-reported decimal degrees; coordinate datum and positional accuracy must be preserved, not assumed to be surveyed. |
| `wind_design_speed_m_s` | float | m/s | Rated wind speed; averaging interval, height and design code required in extensions. |
| `capacity_dc_mw` | float | MW | capacity_dc_mw; no guessed conversion between AC and DC. |
| `capacity_ac_mw` | float | MW | capacity_ac_mw; no guessed conversion between AC and DC. |
| `capacity_unspecified_mw` | float | MW | capacity_unspecified_mw; no guessed conversion between AC and DC. |
| `storage_power_mw` | float | MW | storage_power_mw; no guessed conversion between AC and DC. |
| `storage_energy_mwh` | float | MWh | storage_energy_mwh; expected generation is not a measured production series. |
| `expected_annual_generation_mwh` | float | MWh | expected_annual_generation_mwh; expected generation is not a measured production series. |
| `land_area_ha` | float | ha | Project site area. |
| `grid_voltage_kv` | float | kV | Grid connection voltage. |
| `capex` | float | — | Published capital cost in currency column; basis/year in extensions. |
| `cec_a_ref_v` | float | — | cec_a_ref_v; fitted SAM/CEC model parameter, not an OEM certified measurement. |
| `cec_il_ref_a` | float | — | cec_il_ref_a; fitted SAM/CEC model parameter, not an OEM certified measurement. |
| `cec_io_ref_a` | float | — | cec_io_ref_a; fitted SAM/CEC model parameter, not an OEM certified measurement. |
| `cec_rs_ohm` | float | — | cec_rs_ohm; fitted SAM/CEC model parameter, not an OEM certified measurement. |
| `cec_rsh_ref_ohm` | float | — | cec_rsh_ref_ohm; fitted SAM/CEC model parameter, not an OEM certified measurement. |
| `cec_adjust_pct` | float | — | cec_adjust_pct; fitted SAM/CEC model parameter, not an OEM certified measurement. |
| `sandia_c0_per_w` | float | — | sandia_c0_per_w; fitted SAM/CEC model parameter, not an OEM certified measurement. |
| `sandia_c1_per_v` | float | — | sandia_c1_per_v; fitted SAM/CEC model parameter, not an OEM certified measurement. |
| `sandia_c2_per_v` | float | — | sandia_c2_per_v; fitted SAM/CEC model parameter, not an OEM certified measurement. |
| `sandia_c3_per_v` | float | — | sandia_c3_per_v; fitted SAM/CEC model parameter, not an OEM certified measurement. |

| `depth_m` | float | m | Enclosure depth as reported by OEM. |

## Source column crosswalk

SAM CEC mappings are executable in `pv_catalogue/sam.py`; EIA mappings are in `pv_catalogue/eia860.py`.
Reviewed DESNZ REPD mappings are in `pv_catalogue/repd.py`:

| REPD column | Canonical destination | Qualification |
| --- | --- | --- |
| Ref ID | `external_ids_json.repd_ref_id` | Stable project identity only after review of application/phase scope |
| Installed Capacity (MWelec) | `capacity_unspecified_mw` | AC/DC basis not inferred |
| Solar Site Area (sqm) | `land_area_ha` | Divide source square metres by 10,000; missing stays missing |
| Region / County | `region` / `locality` | Source administrative location |
| Country | `country_code=GBR`; native country in extensions | England/Wales/Scotland/Northern Ireland map to ISO GBR |
| Operational | `extensions_json.repd.operational_milestone_date` | Registry milestone, not independently verified commissioning |
| X-coordinate / Y-coordinate | `extensions_json.repd` | Native grid only; datum/accuracy not asserted |
| Operator (or Applicant) | omitted | Ambiguous role and possible personal information; no owner inference |

| Source | Native column | Canonical column |
| --- | --- | --- |
| CEC module | STC / PTC | pmax_stc_w / ptc_w |
| CEC module | I_sc_ref / V_oc_ref / I_mp_ref / V_mp_ref | isc_a / voc_v / imp_a / vmp_v |
| CEC module | alpha_sc / beta_oc / gamma_pmp | alpha_isc_a_per_c / beta_voc_v_per_c / gamma_pmax_pct_per_c |
| CEC module | a_ref / I_L_ref / I_o_ref / R_s / R_sh_ref / Adjust | cec_* model coefficients |
| CEC inverter | Paco / Pdco / Vac / Vdco | pac_rated_w / pdc_rated_w / vac_rated_v / vdc_rated_v |
| CEC inverter | C0 / C1 / C2 / C3 | sandia_c*_per_* model coefficients |
| CEC inverter | Mppt_low / Mppt_high | mppt_min_v / mppt_max_v |
| EIA solar | Nameplate Capacity (MW), OP/PV rows only | capacity_ac_mw, sum by Plant Code |
| EIA solar | DC Net Capacity (MW), OP/PV rows only | capacity_dc_mw, sum only when every unit is present |
| EIA solar | all native generator attributes | phases_json[].eia_solar |
| EIA plant | all nonempty plant attributes | extensions_json.eia_plant |

Do not equate series-connected cells with physical half-cell count. No automatic unit guesses or phase-to-project date promotion.

## ODRE reviewed PV register crosswalk (2026-08-31 snapshot)

The source-specific adapter requires pinned cohort and complete individual-PV
identity exports, plus a reviewed EIC ledger. EIC is a network installation ID;
possible sections and aggregates are held, never assumed to be separate plants.

| Native field | Catalogue treatment |
| --- | --- |
| `codeeicresourceobject` | Stable project identity seed and `external_ids_json.odre_eic`; exact row locator |
| `nominstallation` | Published installation name; anonymous entries excluded |
| `codetechnologie=PHOTV` | Explicit photovoltaic technology; generic solar insufficient |
| `puismaxinstallee` | Active installed kW / 1,000 → `capacity_unspecified_mw`; no AC/DC inference |
| `puismaxrac` | Maximum grid-injection kW in `extensions_json.odre`; not plant AC capacity |
| `datemiseenservice` | `commissioning_date`, registry industrial-service date |
| `dateraccordement` | Connection date in extensions; not substituted for commissioning |
| `regime=En service` | `operational_registry_snapshot` as of source snapshot date |
| `gestionnaire`, `postesource` | `grid_operator`, `substation` code when present; no owner assignment |
| `tensionraccordement` | Explicit numeric kV only → `grid_voltage_kv`; HTA/BT remain raw labels |
| Commune/region/implantation codes | Qualified administrative geography in extensions; no centroid coordinates |
| `nbgroupes` | Raw group count in extensions; not assumed exact inverter count |
| Rolling injected/produced energy | Measured kWh in extensions; period end installation-specific, not expected generation |

The API schema and attached glossary disagree on whether produced energy includes
self-consumption, and on implantation-code geography. Both definition conflicts
remain documented; no canonical generated-energy total or precise location is
asserted from those fields. All accepted field evidence resolves to the exact EIC
object in the pinned export, with glossary/schema/licence hashes registered.

### Japan FIT review-only mapping

The offline `japan_fit.stage_fit_review` adapter exports held research candidates,
not canonical projects. The two workbook sheets join by FIT facility ID; a parcel
row is never counted as another project. Names, contacts and address strings are
omitted from review output. Exact normalized parcel equality only flags related
registration IDs for review; it does not merge plants.

| FIT source field | Review field | Interpretation |
| --- | --- | --- |
| 設備ID | `fit_facility_id` | Registration identity; not a demonstrated plant boundary |
| 発電設備区分 | `source_technology` | Exact solar label plus positive solar-cell output supports PV |
| 発電出力（kW） | `registered_generation_output_kw_basis_unspecified` | Registered kW; no AC/DC inference |
| 太陽電池の合計出力（kW） | `solar_cell_total_output_kw` | Separate published solar-cell output |
| 新規認定日 | `new_certification_date` | Certification, not commissioning |
| 運転開始予定日 | `planned_operation_date` | Forecast, including future dates |
| 運転開始報告年月 | `reported_operation_month` | Month precision retained; no invented day or current status |

The staged Tottori cohort is at least 1 MW registered generation output. Its
September 2026 snapshot includes a June 2026 paper-filing lag. A named-project
crosswalk, phase/parcel reconciliation and field-specific evidence are still
required before canonical acceptance. No canonical schema columns were added.

### Pakistan NEPRA corporate directory: review only

`nepra.stage_nepra_review` emits research candidates, never canonical assets.

| Native field | Review output | Limitation |
| --- | --- | --- |
| Corporate `h6` heading | `corporate_heading` | Legal-name marker required; not owner or project name |
| Plant Detail / Plant Type | `native_fields`, `explicit_pv_description` | Generic Solar alone does not prove PV |
| Gross Capacity | Native string | No AC/DC assignment or arithmetic from module counts |
| Licence No. | Native string, duplicate flag | Licence is not a reconciled plant boundary |
| Official licence/decision links | `documents` | Transfer decision is not current ownership evidence |

Whitespace is normalized; source misspellings, units and malformed numbers are
not repaired. Source checksum, official HTTPS host and structural checks are
mandatory. Copyright/reuse and portfolio/site identity reviews remain outstanding;
33 staged observations in the dated review represent zero accepted projects.

### AC photovoltaic combiner platforms

Suntree SHLX-AC4/1, AC6/1 and AC8/1 collect inverter AC outputs. Their
`input_count` is the explicitly reported number of incoming AC circuits, not a
DC module-string count. `vac_rated_v` uses the table's rated working voltage;
maximum AC input voltage, input-current ratings, customizable surge values and
material options stay source-qualified in extensions. No DC ratings, fuse
configuration or DC-switch flag is inferred. Dimensions explicitly print mm
and W×H×D; canonical width/height/length map to W/H/D. Enclosure IP65 and cable
grade IP65/IP66 remain distinct. The generic model-key 650 V option and exact
table 690 V maximum remain unresolved; no canonical maximum is selected. The
working-temperature table omits a unit, so its native interval is retained without
assuming Celsius. Named configurable platforms do not expand into material/voltage
permutation records. Historical source availability is not current model availability.

### REPD construction lifecycle scope

`reviewed_repd_records` defaults to the existing operational ground-mounted scope.
Construction or pre-construction requires explicit `reviewed_status="Under Construction"` or `"Awaiting Construction"` in the reviewed
ledger/API call; `stage_pv_repd.py` passes that value and rejects other unreviewed
lifecycle scopes. Stable IDs remain based on Ref ID, so lifecycle changes do not
create another project. Existing populated statuses cannot be overwritten by upsert.

| Source value | Canonical/research mapping | Boundary |
| --- | --- | --- |
| Under Construction status | `under_construction_registry_snapshot` | Historical quarter status, not current progress or operation |
| Under Construction date | `extensions.repd.construction_start_milestone_date` | Registry milestone, not commissioning/forecast completion |
| Operational date in a construction row | Held as contradictory | No silent downgrade or milestone choice |
| Blank construction date | null evidence value | No fabricated day or construction year |
| Installed Capacity (MWelec) | `capacity_unspecified_mw` | No AC/DC inference |
| Native grid X/Y | Source-qualified extensions only | No canonical WGS84 coordinates derived |

The full source identity screen still applies across all solar applications.
Cross-catalogue name/alias and conservative geometry screens hold possible matches;
they never merge projects automatically. Applicant/contact/address fields remain
omitted. A reviewed ledger is required before upsert; candidates are not accepted.

Awaiting-construction scope maps to `awaiting_construction_registry_snapshot` and
rejects populated construction or operational milestones. An explicit
`held_fields_by_ref_id` ledger may withhold `land_area_ha` while retaining the native
source assertion and review note. Other fields/unknown Ref IDs are rejected, so a
field hold cannot drop identity or silently override scope. Whitestones Ref17707
uses this mechanism for the unresolved registry-versus-owner area discrepancy.


## Reviewed Madrid municipal inventory and ODRE enrichment

`pv_catalogue/madrid.py` preserves municipal `Código Ayto` as
`external_ids_json.madrid_building_code`; `Número` remains a source locator and never
an identity key. `Potencia KWp /1000` maps to `capacity_dc_mw`, `Puesta en servicio`
to the source industrial-service date, and the published Latitud/Longitud to building
points with datum and positional accuracy explicitly unspecified. `Superficie` has
no defined array/site basis and remains native evidence. Administrative assignment
is not PV ownership/operator; installer labels and street addresses are omitted.
Repeated building/name and proximity flags are unresolved site/phase holds, never
fuzzy merges. `active_municipal_inventory_snapshot` is a historical source status.

`reviewed_odre_enrichments` fills only missing `grid_operator`, `substation` and
`commissioning_date` from native `gestionnaire`, `postesource`, `datemiseenservice`.
Evidence records exact EIC, GEM phase, date/native values and scope. Existing facts
are not overwritten; disagreements remain `unresolved_assertions_not_applied` and
in the dated review. Unique source EIC, unique canonical target and complete
single-phase scope are mandatory; multiple EIC connections targeting one selected
project require scope review. No capacity, owner, status or location is inferred.


## Catalonia named ground PV crosswalk

| Source field | Treatment | Qualification |
| --- | --- | --- |
| `sol_licitud`, `nom` | Reviewed identity; new records use `external_ids_json.catalonia_application_id` | Shared applications and reapplications held; existing IDs preserved |
| `pot_ncia_mw` | New records: `capacity_unspecified_mw`; existing records: dated native observation | Nominal MW is not automatically AC or DC; municipal rows are not summed |
| `superf_cie_ha` | New records: `land_area_ha`; existing records: native observation | Plant-wide area; conflicting and zero cells held |
| `municipi`, municipal/comarca codes, `vegueria`, municipal area | Administrative geography in extensions | No plant coordinates derived; municipal areas remain separate |
| `estat`, environmental procedure/decision/date | Dated native administrative observation in extensions | Authorization is not physical construction or commissioning |
| `sol_licitant` | Omitted | Applicant/promoter not assigned as current owner; personal details excluded |
| Dataset `rowsUpdatedAt` | `extensions_json.catalonia_planning_observation.source_updated_at` | Source update time, not a newly verified physical lifecycle event |

## Victron BlueSolar current-model factual extract (4 November 2026)

Exact `Article Number` is the model identity, with the stated series retained.
Top-table PMPP, VMPP, IMPP, Voc and Isc map to the STC electrical fields; the
footnote specifies 1,000 W/m², 25°C and AM1.5. Maximum series fuse rating, net
mass, series-connected cells, maximum system voltage, temperature coefficients,
reported temperature range and warranty durations use existing columns. The
negative tolerance bound and the 10-year/25-year retained-output thresholds stay
in extensions; no annual degradation rate is derived.

Three dimensions stay in source order in extensions because axes are not labelled.
`Frame` describes a frame, not an enclosure. Reported efficiency stays native
because the reference area is unspecified. Cable/connector merged cells were
reviewed visually: no cable on the accepted 30/40/55W entries; 900mm/MC4 on the
accepted >=95W entries. No physical cell count is inferred from series count.
The two 235W configurations have conflicting lower-table headers; the 20W
short-circuit-current outlier also remains held. No old discontinued configurations
are substituted for current models. Source-specific rights assessment and pinned
PDF bytes are registered; only attributed factual values are redistributed.

## LSP parallel-combiner factual extract (4 November 2026)

The accepted exact 1,000 V models are SLP-2/1-1000V, SLP-3/1-1000V,
SLP-4/2-1000V and SLP-9/3-1000V. Their respective input/output counts are
2/1, 3/1, 4/2 and 9/3; wiring diagrams explicitly combine parallel strings.
Table identifier spacing is retained as aliases. No configurable permutations
are generated. Six independent-circuit passthrough boxes remain scope-held;
the 600 V voltage sibling is deferred. The 1,500 V sixteen-input page has an
SLP heading versus FLP model-number conflict and remains identity-held.

General maximum voltage, explicit counts and temperature range use existing
columns. W×H×D enclosure millimetres map to width/height/depth in metres;
polycarbonate and IP65 retain enclosure scope. Only single-output current is
normalized: multiple-output maximum-current scope remains native, without
summing circuits. Changeable input short-circuit current is not fixed operating
string current. Supplied fuse-link current is not maximum permissible fuse rating.
Humidity, unqualified altitude, impact resistance, cable entries, component
models/ratings and component standards labels remain source-qualified extensions.
Component claims are not whole-assembly certification; output MPPT diagram labels
are not an inverter MPPT count. No generic FAQ warranty is assigned.

The undated catalogue is checksum-pinned; its PDF metadata date is not a publication,
release or availability date. The source register records the legal publisher,
reviewed rights assessment and exact page/model/field locators. Copyright is
retained; only selected independently reviewed factual parameters are redistributed,
with no open-content grant, full PDF, images or marketing prose claimed.

## Envertech microinverter tables (4 November 2026)

Thirteen exact base models use physical page 2 of the checksum-pinned OEM sheets.
Printed connector options on pages 2/4/6 are grouped within the base model; no
suffix, nominal-voltage or connector permutations are generated. Common DC voltage,
MPPT voltage bounds, continuous AC current, peak conversion efficiency, temperature,
W×H×D dimensions, isolation, standard warranty and IP rating use existing columns.
Single-input DC current retains its printed scope. Multiplied input currents stay
native; no aggregate current or MPPT count is inferred from panel count.

`pac_rated_w` carries explicitly printed maximum continuous active W, with that
basis in `extensions_json.envertech_datasheet`. EVT800SE, EVT1600SE and EVT1800SE
have VA-only tables: their active W stays null. EVT2000SE's active W has a separate
field source from the family table, alongside the dedicated sheet's apparent VA.
Nominal 220/230 V and 50/60 Hz options, frequency/operating-voltage ranges, Isc scope,
MPPT tracking efficiency, humidity, branch limits by cable size, optional 20-year
warranty and OEM compliance labels remain qualified native facts. A `<100 mW`
night-consumption bound is an upper-exclusive 0.1 W bound, not exact standby power.
MPPT efficiency is not conversion efficiency; claims are not verified certification.

EVT500/800/1000 weights and branch/communication options vary by connector page;
canonical weight stays null and page-specific values remain native. No current
availability date or exact nominal AC-voltage choice is asserted. EVT560's printed
600 W rating is retained in review for clarification, without substituting a value
from its model number. No schema change or full document/table layout is included.

## Electra bounded installation-index reader

`pv_catalogue.electra.read_electra_csv` requires independently pinned CSV and
HTML search-result captures. It verifies the echoed explicit `Fotovoltaica`,
region and minimum net-power filters, the result count, exact five-column schema,
sequence, unique `INSTALACIONID` and regional scope. `AUTOID` is only a sequence
locator. The query's threshold is not a capacity observation. Initial unfiltered
responses must never be treated as a PV export.

This reader produces candidates only. The filtered index lacks individual power,
dates and phase details; its live revision is unknown, while the global files show
27 January 2026. Registration is not proof of operation. Repeated names, existing
names and exact namespaced registry IDs add review flags, never automatic merges.
All 75 Canarias candidates remain held for whole-plant/phase, privacy, power and
freshness review. Review output stores IDs/reasons without installation names,
holders, contacts or addresses. No Electra record is upserted as a project.

## Navarra IDENA operating and permitting inventories (4 November 2026)

`pv_catalogue.navarra` verifies pinned ZIP bytes, embedded layer-specific CC BY4
and panel-power definitions, exact DBF fields, row framing and positive finite
power. It discards PROMOTOR before returning candidates. Operating and permitting
layers have separate schemas and titles; neither establishes current operation.
FEATURE is nonunique and never a project ID. A reviewed unique single EXPEDIENTE
case is the canonical identity; repeated and grouped cases remain held.

Panel-sum MW fills DC capacity with its exact basis. Explicit trailing kV in grid
connection text can fill grid voltage, without converting it into power or owner
information. Source service-year text stays native because its generic dictionary
scope is insufficient for a normalized commissioning date. Insertion date is not
commissioning; calculated polygon area is not accepted as land area. No polygon
centroid, exact point, promoter, private owner/contact or inferred live status is
populated. Full geometry and original documents stay outside Git.

Both incoming layers, canonical names/aliases/native-language phase names and
review-only spatial candidates were screened. Overlapping polygons, generic or
related names, repeated/grouped cases and phase ambiguity remain review flags,
never automatic merges. Cierzo II gains only missing grid voltage after exact-name,
one-phase, regional and actual-polygon review. Its existing AC rating/status are
preserved; the different source panel rating remains in review.

## INHENERGY SI and Viscofan evidence boundaries

`pv_catalogue.inhenergy` parses only exact reviewed SI columns from pinned PDFs.
`pac_rated_w` is explicitly rated active AC output; maximum output and the two
distinct PV input/access limits remain qualified native observations. A shared
cell can apply to every model only when it spans the full reviewed table.
Partially merged current, cooling and weight rows retain the `table_*` prefix;
reviewed scalar mappings are recorded separately. Native L/W/H axes are preserved
without an assumed width/depth remapping. Less-than bounds are not scalar values.

The Viscofan BOE notice adds explicitly stated panel MWp, module/inverter counts
and an estimated PV-plus-evacuation EUR budget at its 2025 application stage.
Cost year, scope and design conditions travel in extensions. Its installed-power
heading and kVA total do not replace the existing AC rating. Internal30kV and
existing66kV grid links stay separately scoped. Publication is not commissioning,
operation or authorization; private addresses and signatory details are omitted.

## Danish planning and Hypontech exact editions

Danish `planid` identifies an administrative plan. Explicit use8135 proves the
plan permits PV; it does not prove an individual generating asset exists. Native
adoption/update dates, source plan status and planned capacity cells are distinct
from project operation/commissioning/capacity. Associated municipal-plan evidence
can be retained in extensions after a reviewed crosswalk without allocating mixed
wind/PV capacity or changing project identity.

Hypontech exact model punctuation/suffixes are retained. Active rated W and maximum
apparent VA remain separate; regional voltage/frequency choices and unspecific
input-current scope stay native. Strict consumption/efficiency bounds are not
converted into exact scalar values. Optional interfaces/connectors/monitoring/AFCI
and unknown warranties/certification eligibility remain qualified. A malformed
apparent-power cell is not repaired from a model number or expected ratio.

## Portugal DGEG staging crosswalk

`pv_catalogue.dgeg` stages CS ArcGIS polygons, never automatic plant records.
`objectid` and `inspireid` identify source polygons; `processo` is a licensing
process that may contain several blocks/sub-parks. Native `potencia_geradorkw`
is generator kW with AC/DC basis unresolved. `potencia_instaladakva` and
`potencia_ligacaokva` are apparent kVA, not active MW. Repeated park/block values
are not summed. Licence states are retained without an operating-status inference.
Source geometry and owner/private fields are omitted from staged outputs.

Reviewed associations may fill a missing `extensions_json` context through the
existing upsert API, with exact process/polygon references and field source maps.
They do not replace phases, populate scalar ratings, or resolve unknown plant
boundaries. Unreviewed groups remain candidates even when source coverage is complete.

## RVO SDE decisions and qualified OEM tables

`pv_catalogue.rvo` keeps subsidy decisions separate from canonical generating
plants and their phases. `Referentie` is an exact award identifier, not a plant
identifier. `Thema` must explicitly say `Zon-PV`; generic `Zon` does not suffice.
Anonymised decisions are excluded entirely, and applicant/address/postcode/locality
fields and geometry do not enter staging. Maximum subsidy is a financial ceiling,
not capex or an actual payment. The workbook has no individual nameplate-capacity
column; category MWp thresholds must not populate ratings. Source realisation flags
and native in-use years do not establish present-day operation. No implicit join to
an older viewer snapshot or interpretation of its conflicting field aliases occurs.

Hopewind HSNV tables preserve per-MPPT currents and DC-input layouts as native
context. Page-one current/efficiency discrepancies remain field holds, not repaired
values. Apparent maximum kVA is not active kW; bounded weights are not exact mass.
OMCO Origin One-In-Portrait is one mechanical model with alternative controller
packages. Optional backtracking is not assumed installed; total tracking range does
not create unstated endpoints. Module/length bounds, pose-dependent dimensions,
typical drive counts and an unqualified advertised wind speed stay in context.
Published structural/drive warranty durations use their respective columns; control,
motor and damper terms remain separate. No legacy controller protocols are blended.

### Taipower public station/site candidate scope

The checksum-enforced Taipower reader stages CSV record numbers and native station
and site IDs. IDs are scoped to the explicit solar/PV technology. A dash station
cell is resolved only within an exactly named group having an explicit unique ID;
there is no positional forward fill or automatic plant identity. Source addresses
and portal contact details are excluded. The initial71site rows/45station groups were candidates. The20:30manual review
reconciles station6asoneLongjingplantwith2nativephases, andqualifiescontextsfor
2existingprojects. Otherstation/phaseboundariesremaininreview.

| Native field | Review representation and limit |
| --- | --- |
| `裝置容量(瓩)/Installed Capacity(kW)` | Native site kW in candidate context; AC/DC unestablished, no aggregate or canonical rating |
| `申設狀態/Application Status` | Native administrative label; not current operation or a dated lifecycle scalar |
| `型號/Model` | Native source equipment label; not an OEM-verified model or equipment assignment |
| Station name and IDs | Exact-name station grouping only; whole-plant/phase identity unresolved |
| CSV HTTP Last-Modified | Retrieval metadata only; not the dataset-effective or operating-status date |

Government dataset17141 explicitly declares Taiwan Open Government Data License
v1.0. Retain the Taipower attribution and licence URL in source metadata; do not
inherit that licence for unrelated OEM documents or private material.

### Taipower station-month evidence

Dataset29938 reports Gregorian year/month, a native station name, installed kW,
monthly generation kWh and an average unit daily-energy value. The average's
formula and denominator are not independently established, so it remains native
rather than a PR/efficiency scalar. Installed kW does not establish AC/DC basis.
Named stations can change their site/phase coverage between months.

The monthly reader validates the entire pinned source before selecting a bounded
period/name partition. Duplicate station-periods fail closed unless their exact
keys have been explicitly reviewed; all contradictory rows are then retained in
review and excluded together. It never repairs the year/month or chooses a value.
The Q3 2026 review associates two named stations with existing projects using
reviewed native names, owner/operator and administrative context. It preserves
site rows and monthly observations as qualified extensions, without changing
canonical capacity, lifecycle, coordinates, phase IDs or equipment links. The
214ha Tainan land-area field uses separately licensed city-government evidence.

Taiwan private solar inventory candidates retain `company_native`,
`plant_name_native`, `locality_native`, `installed_kw_native`,
`commercial_year_roc_native` and `cell_origin_rows` outside canonical records.
The source's merged company/name/year cells are expanded with physical origins;
repeated blocks are never summed or merged automatically. Native solar labels do
not prove every row's PV technology, and no company-role, AC/DC, exact-date or
current-status mapping is automatic. Physical staging cursors do not count accepted plants; dated manual reviews distinguish candidates, phase associations and accepted whole projects.

SWELECT Nexora exact-model records use base STC rows only. Rear-gain scenarios
are contextual, not extra models or STC efficiency. NOCT, bifaciality and weight
tolerances, absolute-watt power binning and measurement uncertainty remain in
`extensions_json`. Generic 35A fuse ratings do not populate a maximum-fuse scalar.
Exact applicable Rev04 warranty scope and commencement conditions accompany
12/30-year durations and 1% first-year / 0.4% subsequent annual degradation terms.

The 5 November Daliao depot record uses explicit primary photovoltaic/licence
evidence and one regulator plant row. Its ROC103/104 commercial-year disagreement
remains qualified context; neither commissioning date nor current status is inferred.
Registry company associations do not automatically populate owners/operators.

TBB RiiO Sun II and Hoymiles MIT fields retain PV versus battery input, per-tracker
versus aggregate current, inverter versus charger efficiency and apparent VA versus
active W. Explicit maximum W is not promoted to continuous rated active power.
Unlabelled dimension axes, bounds, optional communications and source-specific
transfer times remain in extensions. Published standards are OEM claims.

LIVOLTEK hybrid records keep per-tracker vectors, EPS peak duration, nominal
voltage alternatives and battery limits in qualified extensions. HP2 combined
W/VA nominal rows do not establish an unambiguous active-power scalar. Conflicting
MPPT upper bounds, battery currents and Hyper dimension axes remain null; a
merged KL2 current cell spanning unequal power models is held for clarification.
