"""
Wind: historical coverage, capacity boundaries and exact turbine specifications
===============================================================================

Rebuild the connected catalogue offline. Historical WRI coverage is not a current
operating census. Capacity charts exclude parent totals and unresolved scopes and
keep lifecycle states separate. Manufacturer specifications and calculated curves
are not independently validated field performance. See the
:doc:`interactive wind viewer </wind-database-viewer>` for field-level evidence.
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import matplotlib.pyplot as plt
import pandas as pd

from energy_analysis.wind_database import compatible_curves, specific_power_w_m2
from energy_data_retrieval.wind_catalogue import build_parquet, capacity_summary, load_records

ROOT = next(p for p in (Path.cwd(), *Path.cwd().parents) if (p / "catalogues/wind").is_dir())
rows = load_records(ROOT / "catalogues/wind")
with TemporaryDirectory() as folder:
    snapshot = Path(folder) / "wind"
    manifest = build_parquet(ROOT / "catalogues/wind", snapshot)
    projects = pd.read_parquet(snapshot / "projects.parquet")
    equipment = pd.read_parquet(snapshot / "equipment.parquet")
print("Input fingerprint:", manifest["input_sha256"])
print("Country-level coverage (includes historical and aggregate records):")
print(projects.groupby(["country_code", "aggregation_role"]).size().unstack(fill_value=0))
print("Technology coverage:", projects.technology.value_counts().to_dict())
print("Dated lifecycle versus aggregation scope (known status does not resolve overlap):")
print(projects.groupby(["status", "aggregation_role"]).size().unstack(fill_value=0))
print("Equipment categories (components are not turbines):")
print(equipment.groupby(["manufacturer", "equipment_category"]).size())

# Reported proposal MW stays independent of count times unit rating.
print("Fleet rating arithmetic checks; no installed MW or aggregation eligibility inferred")
for row in rows:
    check = json.loads(row.get("extensions_json") or "{}").get("fleet_rating_check")
    if check:
        print(row["name"], check, row["aggregation_role"])

# The NEM survey keeps mixed states and shared hybrid limits out of scalar totals.
print("AEMO wind-only survey sites: unknown geometry and excluded capacity scopes")
for row in rows:
    ext = json.loads(row.get("extensions_json") or "{}")
    if "capacity_by_aemo_status" in ext:
        print(row["name"], ext["capacity_by_aemo_status"], row["aggregation_role"])
# Registry unit evidence does not resolve farm boundaries or missing farm MW.
eia_projects = [
    row
    for row in rows
    if row["entity_type"] == "projects"
    and json.loads(row.get("extensions_json") or "{}").get("eia_annual_wind_partitions")
]
print(
    "EIA evidence: project counts, not capacity totals",
    {
        "projects": len(eia_projects),
        "unresolved_scope": sum(row["aggregation_role"] == "unresolved" for row in eia_projects),
        "unknown_installed_mw": sum(
            row.get("installed_capacity_mw") is None for row in eia_projects
        ),
    },
)
print("Published turbine power ratings require their measurement conditions")
print(
    equipment.loc[
        equipment.sources.apply(lambda v: "pnnl_small_wind_july2026" in v),
        ["model", "rated_power_kw", "rated_power_conditions", "rotor_diameter_m"],
    ]
)

# Published rotor geometry is independent of the digits in an OEM model name.
print("Goldwind complete named columns: geometry, power conditions and offered hubs")
print(
    equipment.loc[
        equipment.manufacturer.eq("Goldwind"),
        [
            "model",
            "rated_power_kw",
            "rotor_diameter_m",
            "swept_area_m2",
            "rated_power_conditions",
            "hub_height_options_json",
        ],
    ].to_string(index=False)
)
print("Hub options do not create model variants; no common-condition power curves inferred.")

# Announced modes and tower approvals remain dated options on the existing model.
print("Dated OEM product updates: modes and approval timing, not installed variants")
for row in rows:
    for update in json.loads(row.get("extensions_json") or "{}").get("oem_product_updates", []):
        print(row["name"], update["published_at"], update["operating_modes"])
        print(update["tower_configurations"], update["conditions"])

# Retrospective prototype and production facts retain dates and exact model links.
print("OEM historical observations: not current configuration or fleet retirement")
for row in rows:
    for observation in json.loads(row.get("extensions_json") or "{}").get(
        "oem_historical_observations", []
    ):
        print(row["model"], observation["published_at"], observation["boundary"])
        print(observation["facts"])

# Reference yields are hypothetical five-year energy, never farm generation.
reference_counts = {}
reference_unknown_rotor = 0
reference_corrections = 0
for row in rows:
    for observation in json.loads(row.get("extensions_json") or "{}").get(
        "reference_yield_observations", []
    ):
        for entry in observation["rows"]:
            reference_unknown_rotor += entry.get("rotor_diameter_m") is None
            reference_corrections += entry.get("corrected_at") is not None
            key = (observation["reference_site"], entry.get("withdrawn", False))
            reference_counts[key] = reference_counts.get(key, 0) + 1
print("FGW observation counts by reference site and withdrawn status:")
print(dict(sorted(reference_counts.items())))
print("Reference observations with unknown rotor diameter:", reference_unknown_rotor)
print("Dated reference-yield corrections, not commissioning:", reference_corrections)
print("Reference yields retain five-year kWh, hub/power settings and source notes.")
print(
    "Density, operating mode and gross/net boundary are unknown; no CF or performance comparison."
)

# Dated issuer listings retain expired and unknown status; options are not variants.
certification_status = {}
for row in rows:
    for observation in json.loads(row.get("extensions_json") or "{}").get(
        "certification_register_observations", []
    ):
        status = observation.get("registry_status", "unspecified")
        certification_status[status] = certification_status.get(status, 0) + 1
print(
    "Certification registry observations by stated status:",
    dict(sorted(certification_status.items())),
)
print("Unspecified status does not establish current validity; listed date is not commissioning.")

# Annual EIA unit states do not reconcile whole-farm repowering or hybrid scope.
print("EIA 2025 dated unit evidence: farm status/capacity exclusions remain unchanged")
for row in rows:
    for partition in json.loads(row.get("extensions_json") or "{}").get(
        "eia_annual_wind_partitions", []
    ):
        states = [unit["status_code"] for unit in partition["units"]]
        print(
            row["name"],
            partition["plant_code"],
            partition["year"],
            states,
            row["status"],
            row["aggregation_role"],
        )
print("Predominant models and representative heights are partial inventories, not exact fleets.")
# Compare observation counts within reporting years, never sum MW across years.
eia_years = {}
for row in rows:
    for partition in json.loads(row.get("extensions_json") or "{}").get(
        "eia_annual_wind_partitions", []
    ):
        counts = eia_years.setdefault(partition["year"], {})
        for unit in partition["units"]:
            state = unit["status_code"]
            counts[state] = counts.get(state, 0) + 1
print("Dated EIA generator observations by reporting year:", dict(sorted(eia_years.items())))

# Environmental declarations use modeled sites, not independently observed farms.
print("EPD lifetime scenarios: separate model, location, exposure and net-to-grid boundary")
for row in rows:
    declarations = json.loads(row.get("extensions_json") or "{}").get(
        "environmental_product_declarations", []
    )
    for declaration in declarations:
        for scenario in declaration["scenarios"]:
            print(
                row["model"],
                scenario["location"],
                scenario["reference_service_life_years"],
                "years",
                scenario["value"],
                scenario["unit"],
                scenario["kind"],
                scenario["boundary"],
                declaration["source_id"],
            )
print("No scenario total, capacity factor, operating project or comparable curve is inferred.")

# Procedural decisions can concern solar or auxiliary equipment, not the wind farm.
print("BOE decision scope: wind lifecycle and capacity boundaries remain separate")
for row in rows:
    procedure = json.loads(row.get("extensions_json") or "{}").get("boe_procedure")
    if procedure:
        print(
            row["name"],
            "decision target",
            procedure["decision_target"],
            "decision date",
            procedure["decision_date"],
            "wind status",
            row["status"],
            "status date",
            row["status_as_of"],
            "installed MW",
            row.get("installed_capacity_mw"),
            "planned MW",
            row.get("planned_capacity_mw"),
            "aggregation",
            row["aggregation_role"],
            "quarantined fields",
            sorted(json.loads(row.get("conflicts_json") or "{}")),
        )

# Follow only disclosed applications; component power is not turbine power.
by_id = {row["record_id"]: row for row in rows}
print("Explicit component applications and their conditions (not deployed fleets):")
for row in rows:
    for link in json.loads(row.get("compatibility_json") or "[]"):
        print(row["name"], "→", by_id[link["equipment_record_id"]]["name"], link["conditions"])

# Regional regulatory entries retain raw certificate dates and restrictions.
# Inclusion is not a current certificate or permission-to-operate conclusion.
print("India ALMM observations: dated listing, not verified current eligibility")
for row in rows:
    almm = json.loads(row.get("extensions_json") or "{}").get("mnre_almm_india")
    if almm:
        for entry in almm["rows"]:
            print(
                row["model"],
                "entry",
                entry["row"],
                "listed kW",
                entry["ratings_kw"],
                "hub options m",
                entry["hub_heights_m"],
                "certificate date as printed",
                entry["certificate_validity_raw"],
                "outstanding issue",
                entry["outstanding_issue"],
                "restriction",
                entry["remarks"],
            )

# French registry EICs describe network installations. A dated operating state
# and two reported ratings do not establish non-overlapping whole-farm scope.
french_registry = projects.loc[
    projects.external_ids_json.fillna("").str.contains('"odre_eic"', regex=False)
]
if not french_registry.empty:
    print("French network installations: dated capacity observations, excluded from totals")
    print(
        french_registry[
            [
                "name",
                "region",
                "status_as_of",
                "installed_capacity_mw",
                "export_capacity_mw",
                "aggregation_role",
            ]
        ].to_string(index=False)
    )
    print("No surveyed coordinates inferred from French administrative geography.")

# %%
# Geographic counts describe this catalogue. Missing status is never operational.
fig, axes = plt.subplots(2, 2, figsize=(15, 11), layout="constrained")
projects.country_code.value_counts().head(15).sort_values().plot.barh(ax=axes[0, 0])
axes[0, 0].set(title="15 most represented countries; historical baseline", xlabel="Records")
capacities = []
for field in ("installed_capacity_mw", "commissioned_capacity_mw", "planned_capacity_mw"):
    summary = capacity_summary(rows, field)
    print(field, summary)
    for status, value in summary["by_status"].items():
        capacities.append(
            {
                "category / dated lifecycle": f"{field.split('_')[0]} / {status}",
                "Reported MW": value["reported_mw"],
            }
        )
pd.DataFrame(capacities).set_index("category / dated lifecycle").plot.barh(
    ax=axes[0, 1], legend=False, color="#198c92"
)
axes[0, 1].set(title="Reviewed scope only; categories are not additive", xlabel="Reported MW")
equipment.manufacturer.value_counts().sort_values().plot.barh(ax=axes[1, 0], color="#ad8050")
axes[1, 0].set(title="Exact equipment configurations; not deployed market share", xlabel="Records")
fields = ["installed_capacity_mw", "planned_capacity_mw", "turbine_count", "rotor_diameter_m"]
pd.DataFrame(
    {"Known": projects[fields].notna().sum(), "Unknown": projects[fields].isna().sum()}
).plot.barh(stacked=True, ax=axes[1, 1], color=["#198c92", "#dedede"])
axes[1, 1].set(title="Completeness across all project scopes", xlabel="Records")

# %%
# Scalar ratings exclude flexible ranges and unresolved values. Hub options remain
# one list per configuration; no artificial model expansion is performed.
fig, axes = plt.subplots(1, 2, figsize=(14, 6), layout="constrained")
comparable = equipment.loc[
    equipment.equipment_category.eq("wind_turbine")
    & equipment.rated_power_kw.notna()
    & equipment.rotor_diameter_m.notna()
    # These source ratings are power at 11 m/s, not nameplate densities.
    & ~equipment.sources.apply(
        lambda ids: any(
            source in ids for source in ("pnnl_small_wind_july2026", "sdwind_sd12_20261104")
        )
    )
]
for manufacturer, group in comparable.groupby("manufacturer"):
    values = [
        specific_power_w_m2(p, d)
        for p, d in zip(group.rated_power_kw, group.rotor_diameter_m, strict=True)
    ]
    axes[0].scatter(group.rotor_diameter_m, values, label=manufacturer)
axes[0].set(
    xlabel="Published rotor diameter (m)",
    ylabel="Derived nameplate W/m²",
    title="Specific power; not measured energy yield",
)
axes[0].legend(fontsize="small", ncol=2)
print("Exact model and hub-height options:")
print(
    equipment[["manufacturer", "model", "variant", "hub_height_options_json"]].to_string(
        index=False
    )
)
offshore = projects.loc[
    projects.technology.isin(["fixed_bottom_offshore", "floating_offshore"])
    & projects.aggregation_role.ne("aggregate")
]
print("Offshore foundations and water-depth ranges; unknown remains unknown:")
print(
    offshore[["name", "foundation_type", "water_depth_min_m", "water_depth_max_m"]].to_string(
        index=False
    )
)
depth = offshore.loc[offshore.water_depth_min_m.notna()]
axes[1].barh(depth.name, depth.water_depth_min_m, color="#198c92", label="Minimum reported")
axes[1].barh(
    depth.name,
    depth.water_depth_max_m - depth.water_depth_min_m,
    left=depth.water_depth_min_m,
    color="#9acdcc",
    label="Reported range",
)
axes[1].set(xlabel="Water depth (m)", title="Offshore depth; only reported ranges")
axes[1].legend()
print("Published mixed-fleet models (counts can remain unknown):")
for row in rows:
    if row.get("fleet_json"):
        print(row["name"], json.loads(row["fleet_json"]))

# %%
# Reported Canadian inventory composition is separate from OEM specifications and
# from a current operating census. Unknown manufacturers remain explicit.
inventory_counts = {}
for row in rows:
    inventory = json.loads(row.get("extensions_json") or "{}").get("nrcan_inventory")
    if inventory:
        for group in inventory["fleet_groups"]:
            manufacturer = group.get("Manufacturer") or "Unknown"
            inventory_counts[manufacturer] = (
                inventory_counts.get(manufacturer, 0) + group["inventory_count"]
            )
if inventory_counts:
    fig, ax = plt.subplots(figsize=(10, 5), layout="constrained")
    pd.Series(inventory_counts).sort_values().plot.barh(ax=ax, color="#198c92")
    ax.set(
        xlabel="Reported inventory turbine rows in reconciled project groups",
        ylabel="Reported manufacturer",
        title="Canadian inventory composition · snapshot, not current operating fleet",
    )

# %%
# Swedish registry turbine states include proposals and historical equipment.
# "Uppfört" means physically erected, not independently verified operation.
swedish = [r for r in rows if r["entity_type"] == "turbines" and r.get("country_code") == "SWE"]
if swedish:
    inventory = pd.DataFrame(
        {
            "Registry state": json.loads(r["extensions_json"])["source_fields"]["STATUS"],
            "Reported manufacturer": r.get("manufacturer") or "Unknown",
        }
        for r in swedish
    )
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), layout="constrained")
    for ax, field in zip(axes, inventory.columns, strict=True):
        inventory[field].value_counts().sort_values().plot.barh(ax=ax, color="#198c92")
        ax.set(title=field, xlabel="Registry turbine records; all lifecycle states")
    print("Swedish project coverage by reported county:")
    print(projects.loc[projects.country_code.eq("SWE"), "region"].fillna("Unknown").value_counts())
    print("Swedish linked project identities:", len({r["project_record_id"] for r in swedish}))
    print("Inventory maximum ratings are not summed into installed project MW.")

# %%
# The two original numerical tables share density, pitch mode, turbulence,
# averaging period and manufacturer-calculated basis. Digitized curves are rejected.
curves = [r for r in rows if r["entity_type"] == "curves"]
assert compatible_curves(curves), "Curve conditions differ; separate comparisons required"
fig, ax = plt.subplots(figsize=(10, 5), layout="constrained")
for curve in curves:
    points = pd.DataFrame(json.loads(curve["curve_points_json"]))
    ax.plot(points.wind_speed_m_s, points.value, marker=".", label=curve["name"])
ax.set(
    xlabel="Hub-height rotor-normal wind speed (m/s)",
    ylabel="Calculated power (kW)",
    title="Original V47 numerical tables · 1.225 kg/m³ · standard pitch · TI 10%",
)
ax.legend()
print("Curve conditions:", curves[0]["curve_conditions"])
plt.show()

# %%
# German registry gross/net ratings and lifecycle observations stay at unit scope.
german = [r for r in rows if r["entity_type"] == "turbines" and r.get("country_code") == "DEU"]
if german:
    states = pd.Series(
        [json.loads(r["extensions_json"]).get("decoded_lifecycle") or "Unknown" for r in german]
    )
    fig, ax = plt.subplots(figsize=(10, 5), layout="constrained")
    states.value_counts().sort_values().plot.barh(ax=ax, color="#198c92")
    ax.set(
        title="German registered units by reported lifecycle",
        xlabel="Selected named-park inventory records; not a current operating census",
    )
    print("German linked parks:", len({r["project_record_id"] for r in german}))
    print("Gross/net kW remain separate source fields; no farm MW is inferred.")

# %%
# Registry geography and integrated component ratings retain their own boundaries.
print("German project coverage by state; includes unresolved/historical scopes:")
print(projects.loc[projects.country_code.eq("DEU"), "region"].fillna("Unknown").value_counts())
print("Integrated gearbox-generator specifications; not turbine performance:")
print(
    equipment.loc[
        equipment.manufacturer.eq("Winergy"),
        ["model", "rated_power_kw", "rated_power_conditions", "mass_kg"],
    ]
)

# %%
# Exact yaw/pitch gearboxes are component types, not installed turbine fleets.
ngc = equipment.loc[equipment.manufacturer.eq("NGC")]
if not ngc.empty:
    print("NGC gearbox envelopes; rated torque and peak torque remain distinct:")
    for _, component in ngc.iterrows():
        spec = json.loads(component.extensions_json)
        if "rated_torque_range_kNm" not in spec:
            print(component.model, "Torque and speed-ratio specifications unknown")
            continue
        print(
            component.model,
            spec["function"],
            spec["rated_torque_range_kNm"],
            spec["peak_torque_kNm"],
            "kNm",
            spec["speed_ratio_range"],
        )

# %%
print("Bonfiglioli peak torque by application; reference values, not nominal ratings:")
for _, component in equipment.loc[equipment.manufacturer.eq("Bonfiglioli")].iterrows():
    specs = json.loads(component.extensions_json)
    if "peak_torque_Nm_by_application" in specs:
        print(component.model, specs["peak_torque_Nm_by_application"], "Nm")

# %%
print("ABB historical converter ratings: typical generator kW; generator/grid kVA")
for _, component in equipment.loc[equipment.manufacturer.eq("ABB")].iterrows():
    specs = json.loads(component.extensions_json or "{}")
    if "typical_generator_rating_kw" in specs:
        print(
            component.model,
            specs["typical_generator_rating_kw"],
            specs["generator_apparent_power_kva"],
            specs["grid_apparent_power_kva"],
        )

# %%
print("ABB coolant inlet limits; standard and optional limits remain separate:")
for _, component in equipment.loc[equipment.manufacturer.eq("ABB")].iterrows():
    conditions = json.loads(component.extensions_json or "{}").get("series_technical_conditions")
    if conditions:
        print(
            component.model,
            conditions["coolant_inlet_temperature_c"],
            conditions["optional_limits"],
        )

# %%
print("ACU motor-side current; 60s and 1s overload limits, not turbine output:")
for _, component in equipment.loc[
    equipment.model.fillna("").str.startswith(("ACU 201-", "ACU 401-"))
].iterrows():
    specs = json.loads(component.extensions_json)
    print(component.model, specs["output_current_table_a"], specs["overload_current_a"])

# %%
print("ACU input-phase limits and switching-frequency observations:")
for _, component in equipment.loc[equipment.model.fillna("").str.startswith("ACU 201-")].iterrows():
    specs = json.loads(component.extensions_json)
    print(component.model, specs["switching_frequency_current_a"])
    if "single_two_phase_max_output_current_a" in specs:
        print("Single/two-phase maximum A:", specs["single_two_phase_max_output_current_a"])


# %%
print("ACUx10 frame-specific catalogue ratings; no turbine performance inference:")
for _, component in equipment.loc[
    equipment.model.fillna("").str.startswith(("ACU 210-", "ACU 410-", "ACU 510-", "ACU 610-"))
].iterrows():
    specs = json.loads(component.extensions_json)
    print(
        component.model,
        "frame",
        specs["size"],
        "mains V",
        specs["rated_mains_voltage_v"],
        "motor A",
        specs["output_current_table_a"],
        "overload A",
        specs["overload_current_a"],
        "cooling options",
        specs["mechanical_options"],
    )

# %%
# Exact line-choke pairings are component compatibility, not turbine performance.
for component in rows:
    if component.get("equipment_category") == "line_choke":
        specs = json.loads(component["extensions_json"])
        print(
            component["model"],
            "nominal A",
            specs["nominal_current_a"],
            "inductance mH",
            specs["inductance_mh"],
            "dissipation W",
            specs["power_dissipation_w"],
            "documented inverter pairings",
            len(json.loads(component["compatibility_json"])),
        )

# %%
# Application-specific choke ratings and qualified filter ratings stay separate.
for component in rows:
    if component.get("equipment_category") not in {"line_choke", "emc_filter"}:
        continue
    specs = json.loads(component["extensions_json"])
    if "application_observations" in specs:
        print(component["model"], "application ratings", specs["application_observations"])
    if component["equipment_category"] == "emc_filter":
        print(
            component["model"],
            "rated A",
            specs["rated_current_a"],
            "leakage mA",
            specs["leakage_current_ma"],
            "catalogue dissipation W",
            specs["power_dissipation_w"],
            "conditions",
            specs["technical_conditions"],
        )

# %%
# Braking duty is conditional on drive rating, not wind-turbine generation.
for component in rows:
    if component.get("equipment_category") == "braking_resistor":
        specs = json.loads(component["extensions_json"])
        print(
            component["model"],
            specs["resistance_ohm"],
            "ohm",
            specs["continuous_rated_power_w"],
            "W",
            specs["application_observations"],
        )

# %%
# Legacy resistor revisions are displayed separately from current specifications.
for component in rows:
    specs = json.loads(component.get("extensions_json") or "{}")
    if "legacy_vec501_r0_observations" in specs:
        print(component["model"], "legacy VEC501R0 only", specs["legacy_vec501_r0_observations"])

# %%
# Optional monitoring links retain the OEM's series and revision boundary.
# A documented interface does not establish that an accessory is installed.
by_id = {row["record_id"]: row for row in rows}
for component in rows:
    for link in json.loads(component.get("compatibility_json") or "[]"):
        target = by_id[link["equipment_record_id"]]
        if target.get("equipment_category") == "control":
            print(
                component["model"],
                "optional monitor",
                target["model"],
                link["conditions"],
                "evidence",
                link["source_id"],
                link["locator"],
            )

# ONS rows may represent turbine groups. Count evidence, never infer farm totals.
ons_snapshots = [
    snapshot
    for row in rows
    if row["entity_type"] == "projects"
    for snapshot in json.loads(row.get("extensions_json") or "{}").get(
        "ons_wind_unit_snapshots", []
    )
]
ons_units = [unit for snapshot in ons_snapshots for unit in snapshot["units"]]
print(
    "ONS daily evidence; unit rows are not individual turbines or farm capacity totals",
    {
        "snapshots": len(ons_snapshots),
        "unit_observations": len(ons_units),
        "unknown_nominal_mw": sum(u["reported_nominal_mw"] is None for u in ons_units),
        "reported_zero_nominal_mw": sum(u["reported_nominal_mw"] == 0 for u in ons_units),
    },
)

# Count reported ONS state labels per snapshot; these are not capacity totals.
ons_state_evidence = {}
for snapshot in ons_snapshots:
    states = {u["original"].get("id_estado") for u in snapshot["units"]}
    for state in sorted(states, key=lambda v: v or ""):
        label = state or "Unknown state"
        ons_state_evidence[label] = ons_state_evidence.get(label, 0) + 1
print(
    "ONS state coverage: snapshot counts, not installed MW",
    dict(sorted(ons_state_evidence.items())),
)

# Deduplicate project/state pairs across unit rows and daily snapshots.
ons_project_states = set()
for row in rows:
    if row["entity_type"] != "projects":
        continue
    for snapshot in json.loads(row.get("extensions_json") or "{}").get(
        "ons_wind_unit_snapshots", []
    ):
        for unit in snapshot["units"]:
            ons_project_states.add(
                (row["record_id"], unit["original"].get("id_estado") or "Unknown")
            )
if ons_project_states:
    state_counts = pd.Series([state for _, state in sorted(ons_project_states)]).value_counts()
    fig, ax = plt.subplots(figsize=(8, 4))
    state_counts.sort_index().plot.bar(ax=ax, color="#3d718e")
    ax.set(
        title="ONS project evidence by reported state",
        ylabel="Projects with evidence",
        xlabel="Reported state",
    )
    ax.text(
        0,
        -0.28,
        "One project/state pair; no current fleet or capacity total inferred.",
        transform=ax.transAxes,
        fontsize=9,
    )
    fig.tight_layout()


# Separate dated registry categories, with unknowns visible and no MW aggregation.
siga_observations = [
    observation
    for row in rows
    if row["entity_type"] == "projects"
    for observation in json.loads(row.get("extensions_json") or "{}").get("epe_siga_snapshots", [])
]
if siga_observations:
    categories = ["authorized_mw", "inspected_mw", "physical_guarantee_mw"]
    counts = pd.DataFrame(
        {
            label: {
                "Positive reported": sum(
                    o["normalized_power"][label] is not None and o["normalized_power"][label] > 0
                    for o in siga_observations
                ),
                "Reported zero": sum(o["normalized_power"][label] == 0 for o in siga_observations),
                "Unknown": sum(o["normalized_power"][label] is None for o in siga_observations),
            }
            for label in categories
        }
    ).T
    fig, ax = plt.subplots(figsize=(9, 4))
    counts.plot.barh(stacked=True, ax=ax, color=["#3d718e", "#e7ab54", "#9a9a9a"])
    dates = sorted({o["observation_date"] for o in siga_observations})
    ax.set(
        title="SIGA reported category completeness — " + ", ".join(dates),
        xlabel="Registry observations; not summed MW",
        ylabel="",
    )
    ax.text(
        0,
        -0.3,
        "Physical guarantee is not installed capacity; unresolved scope exclusions remain.",
        transform=ax.transAxes,
        fontsize=9,
    )
    fig.tight_layout()


# Counts of linked projects by dated state partition, not a national inventory.
if siga_observations:
    state_projects: dict[tuple[str, str], set[str]] = {}
    for row in rows:
        if row["entity_type"] != "projects":
            continue
        for observation in json.loads(row.get("extensions_json") or "{}").get(
            "epe_siga_snapshots", []
        ):
            key = (observation["original"]["sigufprincipal"], observation["observation_date"])
            state_projects.setdefault(key, set()).add(row["record_id"])
    keys = sorted(state_projects)
    fig, ax = plt.subplots(figsize=(9, 3.5))
    ax.barh(
        [f"{state} · {date}" for state, date in keys],
        [len(state_projects[k]) for k in keys],
        color="#3d718e",
    )
    ax.set(
        title="SIGA evidence linked to existing projects",
        xlabel="Distinct linked projects per state and date",
    )
    ax.text(
        0,
        -0.32,
        "Selected state partitions only; unmatched identities held. "
        "No capacity eligibility change.",
        transform=ax.transAxes,
        fontsize=9,
    )
    fig.tight_layout()

# Exact table columns, with ranges plotted as options rather than installations.
oem_columns = [
    observation
    for row in rows
    if row["entity_type"] == "equipment"
    for observation in json.loads(row.get("extensions_json") or "{}").get(
        "oem_table_observations", []
    )
    if observation["source_id"] in row["sources"]
]
if oem_columns:
    fig, ax = plt.subplots(figsize=(9, 4))
    for observation in oem_columns:
        values = observation["values"]
        diameter = values["rotor_diameter_m"]
        low, high = values["hub_height_range_m"]
        ax.plot([diameter, diameter], [low, high], color="#3d718e", alpha=0.5)
        ax.scatter([diameter, diameter], [low, high], s=12, color="#3d718e")
    ax.set(
        title="Windey 2022 exact-model tables: published hub options",
        xlabel="Explicit rotor diameter (m)",
        ylabel="Published hub-height option range (m)",
    )
    ax.text(
        0,
        -0.3,
        f"{len(oem_columns)} reviewed model columns; overlapping options are not installations. "
        "Density and operating mode unknown; no performance comparison.",
        transform=ax.transAxes,
        fontsize=8,
    )
    fig.tight_layout()


# Review completeness is separate from the number of successfully linked farms.
epe_reviews = []
for ledger in sorted((ROOT / "catalogues/wind/research").glob("*-epe-review.json")):
    report = json.loads(ledger.read_text())
    if report.get("complete_selected_partition") and report.get("all_reviewed_candidates"):
        state = report["all_reviewed_candidates"][0]["original"]["sigufprincipal"]
        epe_reviews.append(
            {"State": state, "Linked": report["enriched"], "Identity held": report["deferred"]}
        )
if epe_reviews:
    review_counts = pd.DataFrame(epe_reviews).set_index("State").sort_index()
    fig, ax = plt.subplots(figsize=(9, 6))
    review_counts.plot.barh(stacked=True, ax=ax, color=["#3d718e", "#9a9a9a"])
    ax.set(
        title="Complete selected SIGA partitions: identity review outcomes",
        xlabel="Registry entries; not MW",
    )
    fig.tight_layout()

# A complete empty ID query is distinct from an unqueried state or missing data.
coverage_audits = sorted((ROOT / "catalogues/wind/research").glob("*-epe-coverage.json"))
if epe_reviews and coverage_audits:
    audit = json.loads(coverage_audits[-1].read_text())
    empty_states = ", ".join(audit["result"]["empty_states"])
    fig.text(
        0.02,
        0.01,
        f"Explicit empty layer partitions: {empty_states}.\n"
        "Empty registry query is not zero wind capacity. Held identities remain excluded.",
        fontsize=8,
    )
    fig.tight_layout(rect=(0, 0.08, 1, 1))


# Lender design envelopes stay out of scalar geometry and fleet distributions.
print("Source/revision-qualified design envelopes; not selected or installed turbines:")
for row in rows:
    envelopes = json.loads(row.get("extensions_json") or "{}").get("design_envelopes", [])
    for envelope in envelopes:
        print(row["name"], envelope["revision"], envelope["locator"])
        print(
            "Proposed rotor/hub ranges (m):",
            envelope["rotor_diameter_range_m"],
            envelope["hub_height_range_m"],
        )
        print("Scalar rotor/hub remain:", row.get("rotor_diameter_m"), row.get("hub_height_m"))
        print(envelope["conditions"])


# %%
# Dated OEM supply awards do not select regional equipment configurations.
print("OEM supply announcements; not installed fleet distributions:")
for row in projects.to_dict("records"):
    for award in json.loads(row.get("extensions_json") or "{}").get("supply_awards", []):
        print(row["name"], award["published_at"], award["manufacturer"], award["model_mentioned"])
        print(award["identity_basis"], award["configuration_status"])
        print("Installed turbine count remains:", row.get("turbine_count"))

# %%
# A common administrative procedure does not establish a common physical farm.
print("Former joint administrative procedures; capacity additivity not established:")
for row in rows:
    relation = json.loads(row.get("extensions_json") or "{}").get("relationships", {})
    if relation.get("relationship_type") == "former_joint_administrative_procedure":
        print(row["name"], relation["related_project_name"], relation["former_procedure"])
        print("Separated:", relation["separated_date"], "aggregation:", row["aggregation_role"])


# Numeric consistency is a review screen, not independent performance validation.
print("OEM exact tables: reported cells, withheld scalars and unknown revisions")
for row in rows:
    table = json.loads(row.get("extensions_json") or "{}").get("oem_numeric_table")
    if table:
        print(
            row["model"],
            "revision",
            table["revision"],
            "original bytes",
            table["original_bytes_available"],
            "area m2",
            row.get("swept_area_m2"),
            "cut-out m/s",
            row.get("cut_out_m_s"),
            "held",
            sorted(json.loads(row.get("conflicts_json") or "{}")),
        )
print("Floating prototype depth: floater and anchors are different boundaries")
for row in rows:
    design = json.loads(row.get("extensions_json") or "{}").get("environmental_design")
    if design and "floater_seabed_elevation_m" in design:
        print(
            row["name"],
            "floater seabed elevation m",
            design["floater_seabed_elevation_m"],
            "datum",
            design["vertical_reference"],
            "anchor approximate depth m",
            design["anchor_approx_depth_m"],
            "capacity role",
            row["aggregation_role"],
        )

# Operator MW boundaries and date precision stay separate from installed capacity.
print("Dated operator observations: contracted/gross MW, not additive installed capacity")
for row in rows:
    for observation in json.loads(row.get("extensions_json") or "{}").get(
        "operator_portfolio_observations", []
    ):
        facts = observation["facts"]
        print(
            row["name"],
            observation["as_of"],
            facts.get("status", "unknown"),
            facts["capacity_basis"],
            facts["capacity_mw"],
            facts["cod"],
            facts["cod_precision"],
            facts["count_times_rating_check"],
            row["aggregation_role"],
        )
print("Unknown exact models remain unknown; dated ownership does not overwrite earlier shares.")
