"""
Data centers: geography, capacity completeness, cooling and equipment
=====================================================================

Rebuild the two connected JSONL catalogues into immutable Parquet. Four views
show coverage and missingness without treating campuses as additional buildings,
converting grid MW into IT MW, or equating accelerator limits with server input.
See the :doc:`interactive viewer </data-center-database-viewer>` for field evidence.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import shorten

import matplotlib.pyplot as plt
import pandas as pd

from energy_data_retrieval.data_center_catalogue import (
    build_parquet,
    capacity_summary,
    load_records,
)

ROOT = next(
    p for p in (Path.cwd(), *Path.cwd().parents) if (p / "catalogues/data_centers").is_dir()
)
with TemporaryDirectory() as folder:
    snapshot = Path(folder) / "data-centers"
    manifest = build_parquet(ROOT / "catalogues/data_centers", snapshot)
    projects = pd.read_parquet(snapshot / "projects.parquet")
    equipment = pd.read_parquet(snapshot / "equipment.parquet")

print("Input fingerprint:", manifest["input_sha256"])
print("Project scopes:", projects.record_scope.value_counts().to_dict())
print("Capacity summaries keep rating bases separate:")
rows = load_records(ROOT / "catalogues/data_centers")
for field in ("it_capacity_mw", "grid_capacity_mw", "facility_capacity_mw"):
    print(field, capacity_summary(rows, field))

# %%
# Geographic coverage: campus and facility counts remain visually distinct.
fig, axes = plt.subplots(2, 2, figsize=(15, 11), layout="constrained")
coverage = projects.groupby(["country_code", "record_scope"]).size().unstack(fill_value=0)
scope_colors = {"campus": "#a5c8d4", "facility": "#167d9a", "phase": "#b58a45"}
coverage.plot.barh(
    stacked=True, ax=axes[0, 0], color=[scope_colors[scope] for scope in coverage.columns]
)
axes[0, 0].set(
    xlabel="Catalogue records; not market share",
    ylabel="Country",
    title="Geographic coverage by scope",
)

# Keep one gallery execution block so all four axes are captured together.
# Count reported capacities; null is not zero, and the three MW boundaries differ.
fields = ["it_capacity_mw", "grid_capacity_mw", "facility_capacity_mw"]
completeness = pd.DataFrame(
    {"Reported": projects[fields].notna().sum(), "Unknown": projects[fields].isna().sum()}
)
completeness.index = ["IT", "Grid", "Facility"]
completeness.plot.barh(stacked=True, ax=axes[0, 1], color=["#167d9a", "#dedede"])
axes[0, 1].legend(loc="upper left", fontsize=9)
axes[0, 1].set(
    xlabel="Records (all scopes)",
    ylabel="Capacity boundary",
    title="Capacity completeness",
)

# Keep one gallery execution block so all four axes are captured together.
# Cooling descriptions preserve technologies; missing values remain an explicit group.
cooling = projects.cooling_technology.fillna("Unknown").value_counts().sort_values()
cooling.plot.barh(ax=axes[1, 0], color="#3d9c87")
axes[1, 0].set_yticklabels(
    [shorten(str(label), width=38, placeholder="…") for label in cooling.index], fontsize=8
)
axes[1, 0].set(
    xlabel="Records",
    ylabel="Reported description",
    title="Cooling coverage (abbreviated labels)",
)

# Keep one gallery execution block so all four axes are captured together.
# Like-for-like comparison: accelerator limits in W only. Do not include server kW.
gpus = equipment.loc[
    equipment.equipment_category.eq("gpu_accelerator") & equipment.accelerator_power_w.notna()
].sort_values("accelerator_power_w")
axes[1, 1].barh(gpus["name"], gpus.accelerator_power_w, color="#b58a45")
axes[1, 1].tick_params(axis="y", labelsize=8)
axes[1, 1].set(
    xlabel="Published maximum accelerator power (W)",
    title="GPU power limits; not measured draw",
)
print(
    equipment.loc[
        equipment.equipment_category.eq("server"), ["name", "input_power_kw", "power_conditions"]
    ].to_string(index=False)
)
print("Dell compatibility rows preserve accelerator limits separately from server input:")
print(
    equipment.loc[
        equipment.manufacturer.eq("Dell"),
        ["model", "variant", "accelerator_power_w", "input_power_kw", "power_conditions"],
    ]
    .sort_values(["model", "variant"])
    .to_string(index=False)
)
print("Exact UPS ratings keep kW, kVA and runtime/load conditions separate:")
print(
    equipment.loc[
        equipment.equipment_category.eq("ups"),
        [
            "name",
            "output_power_kw",
            "apparent_power_kva",
            "runtime_minutes",
            "runtime_load_kw",
        ],
    ]
    .sort_values(["apparent_power_kva", "name"])
    .to_string(index=False)
)
print("Rack PDU comparison uses only reported apparent-power rows:")
print(
    equipment.loc[
        equipment.equipment_category.eq("rack_pdu") & equipment.apparent_power_kva.notna(),
        ["name", "apparent_power_kva", "input_current_a", "temperature_max_c"],
    ]
    .sort_values(["apparent_power_kva", "name"])
    .to_string(index=False)
)
print("Generator comparison keeps Data Center Continuous kW and kVA separate:")
print(
    equipment.loc[
        equipment.equipment_category.eq("backup_generator"),
        ["model", "frequency_hz", "output_power_kw", "apparent_power_kva", "quality_status"],
    ]
    .sort_values(["frequency_hz", "output_power_kw", "model"])
    .to_string(index=False)
)
print("Galaxy VS comparisons retain exact SKU, kW/kVA and full-load efficiency conditions:")
print(
    equipment.loc[
        equipment.manufacturer.eq("Schneider Electric"),
        [
            "model",
            "output_power_kw",
            "apparent_power_kva",
            "efficiency_pct",
            "efficiency_conditions",
        ],
    ]
    .sort_values(["output_power_kw", "model"])
    .to_string(index=False)
)
print("STULZ CyberAir comparisons use net cooling at one explicit rating point:")
print(
    equipment.loc[
        equipment.manufacturer.eq("STULZ"),
        [
            "model",
            "variant",
            "cooling_capacity_kw",
            "input_power_kw",
            "airflow_m3_h",
            "cooling_rating_conditions",
        ],
    ]
    .sort_values(["variant", "cooling_capacity_kw", "model"])
    .to_string(index=False)
)
print("CDU comparison preserves approach temperatures, loop boundaries and quarantines:")
print(
    equipment.loc[
        equipment.equipment_category.eq("cdu"),
        [
            "manufacturer",
            "model",
            "cooling_capacity_kw",
            "input_power_kw",
            "liquid_flow_l_min",
            "cooling_rating_conditions",
            "quality_status",
        ],
    ]
    .sort_values(["manufacturer", "cooling_capacity_kw", "model"], na_position="last")
    .to_string(index=False)
)
print("Transformer comparison keeps kVA separate from table losses and active kW:")
print(
    equipment.loc[
        equipment.equipment_category.eq("transformer"),
        ["manufacturer", "variant", "apparent_power_kva", "weight_kg", "power_conditions"],
    ]
    .sort_values(["manufacturer", "apparent_power_kva", "variant"])
    .to_string(index=False)
)
print("Switchgear portfolio maxima remain observations, not nominal electrical inputs:")
print(
    equipment.loc[
        equipment.equipment_category.eq("switchgear"),
        ["manufacturer", "model", "variant", "input_voltage_v", "input_current_a"],
    ]
    .sort_values(["manufacturer", "model", "variant"])
    .to_string(index=False)
)
plt.show()
