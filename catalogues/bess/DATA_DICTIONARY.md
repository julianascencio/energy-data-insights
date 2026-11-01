# BESS data dictionary

Schema version **1.0.0**; 60 typed nullable columns. Unknown is null.

| Column | Type | Unit | Meaning |
| --- | --- | --- | --- |
| `record_id` | string | — | Stable UUID chosen from original country, locality and name; never changed by a rename or capacity update. |
| `entity_type` | string | — | Catalogue entity; projects only in version 1. Allowed: `projects`. |
| `name` | string | — | Named battery project, not the entire solar or wind facility. |
| `country_code` | string | — | ISO 3166-1 alpha-3 country code. |
| `region` | string | — | Source-reported administrative region. |
| `locality` | string | — | Source-reported locality; not a geocoded coordinate. |
| `location_accuracy` | string | — | Accuracy and basis of source-reported coordinates. |
| `capacity_scope` | string | — | Exact project, phases or expansion represented by the numeric capacities. Prevents project/phase double counting. |
| `status` | string | — | Last source-supported status, not a live operational assessment. Allowed: `announced`, `permitted`, `under_construction`, `commissioning`, `operational`, `partially_operational`, `suspended`, `retired`, `cancelled`, `unknown`. |
| `status_as_of` | string | — | Date supporting status; for undated live project pages, date accessed. Does not imply COD. |
| `status_date_basis` | string | — | Whether status_as_of is a dated publication or access to an undated project page. Allowed: `publication_date`, `accessed_undated_page`. |
| `power_basis` | string | — | Electrical basis for reported battery power. Unspecified is never silently converted to AC. Allowed: `ac`, `dc`, `unspecified`. |
| `energy_basis` | string | — | Reported energy basis. Nominal, usable and unspecified are not interchangeable. Allowed: `nominal`, `usable`, `unspecified`. |
| `connection_type` | string | — | Explicit grid or microgrid connection; null if not sourced. Allowed: `grid_connected`, `off_grid`, `microgrid`. |
| `configuration` | string | — | Standalone, co-located generation or microgrid when supported. Allowed: `standalone`, `co_located_solar`, `co_located_wind`, `co_located_hybrid`, `microgrid`. |
| `chemistry` | string | — | Battery chemistry only where explicitly reported; flow batteries are included. |
| `commercial_operation_date` | string | — | Confirmed commercial operation date, if known to the day; never an inauguration date by default. |
| `expected_operation_date` | string | — | Source-stated planned operation date, if known to the day; never automatically promotes project status. |
| `grid_operator` | string | — | Named system or network operator. |
| `substation` | string | — | Named connection substation. |
| `battery_model` | string | — | Reported battery product/model. |
| `pcs_model` | string | — | Reported power conversion system model. |
| `currency` | string | — | ISO 4217 currency for capex. |
| `capex_scope` | string | — | What the reported capital expenditure includes. |
| `quality_status` | string | — | Source-backed research record or unresolved field conflict. Allowed: `source_backed`, `needs_review`. |
| `notes` | string | — | Editorial limitations, exclusions and interpretation notes. |
| `aliases` | list_string | — | Other names for this same project. |
| `owners` | list_string | — | Reported project owners; ownership shares belong in extensions. |
| `developers` | list_string | — | Reported project developers. |
| `operators` | list_string | — | Reported operating entities. |
| `epc_contractors` | list_string | — | Reported engineering, procurement and construction contractors. |
| `integrators` | list_string | — | Reported BESS integration suppliers. |
| `battery_manufacturers` | list_string | — | Reported cell or battery suppliers, without inferring from integrator. |
| `pcs_manufacturers` | list_string | — | Reported power conversion suppliers. |
| `applications` | list_string | — | Reported grid services or use cases. |
| `sources` | list_string | — | Source registry IDs used by this record. |
| `source_urls` | list_string | — | Derived sorted unique URLs from sources.json. |
| `power_capacity_mw` | float | MW | Reported BESS power only; excludes PV power and site interconnection rating. |
| `energy_capacity_mwh` | float | MWh | Reported battery stored-energy capacity for capacity_scope. |
| `duration_hours` | float | h | Source-reported discharge duration; not calculated from mixed-basis ratings. |
| `charging_power_mw` | float | MW | Separately reported charging rating. |
| `grid_connection_capacity_mw` | float | MW | Whole-site grid connection limit, distinct from BESS power. |
| `co_located_solar_mw` | float | MW | Reported co-located PV capacity; basis described in extensions/notes. |
| `co_located_wind_mw` | float | MW | Reported co-located wind capacity. |
| `round_trip_efficiency_pct` | float | % | Source-reported round-trip efficiency; boundary and conditions in extensions. |
| `grid_voltage_kv` | float | kV | Reported grid connection voltage. |
| `capex` | float | — | Capital expenditure in currency; scope must be documented. |
| `design_life_years` | float | years | Source-reported design/operating life, not inferred warranty. |
| `latitude` | float | degrees | Source-reported WGS84 latitude; no city-centroid substitutes. |
| `longitude` | float | degrees | Source-reported WGS84 longitude; no city-centroid substitutes. |
| `commercial_operation_year` | int | — | Actual COD year when exact date is not available. |
| `container_count` | int | — | Reported count of battery containers, not cells or racks. |
| `field_sources_json` | json | — | JSON object mapping each populated factual field to source IDs; no wildcard evidence. |
| `phases_json` | json | — | JSON list of documented phase metadata; phases are not also separate rows for this same scope. |
| `external_ids_json` | json | — | JSON object of namespaced registry IDs for cross-source deduplication. |
| `extensions_json` | json | — | JSON object of additional namespaced metadata that has not been standardized. |
| `conflicts_json` | json | — | JSON object of conflicting source observations with source IDs; requires needs_review. |
| `created_at` | timestamp | — | UTC date/time this record was first added. |
| `updated_at` | timestamp | — | UTC date/time of the latest substantive edit. |
| `last_verified_at` | timestamp | — | UTC source-access time; not proof of current operational availability. |
