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
