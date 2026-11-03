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
axes[0].legend()
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
for _, component in equipment.loc[equipment.model.fillna("").str.startswith("ACU 401-")].iterrows():
    specs = json.loads(component.extensions_json)
    print(component.model, specs["output_current_table_a"], specs["overload_current_a"])
