"""
PV equipment and project catalogue: query, compare and audit
============================================================

Run from a checkout of Energy Data Insights. This offline example reads the
committed canonical database, produces typed Parquet snapshots in a temporary
folder, and projects only the fields needed for each query. The initial EIA-heavy
project distribution is shown explicitly rather than described as complete global
coverage. Sources and limitations are in ``catalogues/pv/sources.json``.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import matplotlib.pyplot as plt
import pandas as pd

from energy_data_retrieval.pv_catalogue import build_parquet

ROOT = next(p for p in (Path.cwd(), *Path.cwd().parents) if (p / "catalogues/pv").is_dir())

with TemporaryDirectory() as folder:
    snapshot = Path(folder) / "snapshot"
    manifest = build_parquet(ROOT / "catalogues/pv", snapshot)
    modules = pd.read_parquet(
        snapshot / "modules.parquet", columns=["manufacturer", "model", "pmax_stc_w", "bifacial"]
    )
    projects = pd.read_parquet(
        snapshot / "projects.parquet",
        columns=[
            "name",
            "country_code",
            "capacity_ac_mw",
            "capacity_dc_mw",
            "latitude",
            "longitude",
            "source_urls",
        ],
    )

print("Accepted rows:", {k: v["rows"] for k, v in manifest["tables"].items()})
print("Bifacial modules >=600 W:")
print(modules.loc[modules["bifacial"].eq(True) & modules["pmax_stc_w"].ge(600)].head())
print("Chile project metadata and sources:")
print(projects.loc[projects["country_code"].eq("CHL")].to_string(index=False))

fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), layout="constrained")
counts = {k.replace("_", " "): v["rows"] for k, v in manifest["tables"].items()}
axes[0].barh(list(counts), list(counts.values()), color="#167d9a")
axes[0].set_xscale("log")
axes[0].set_xlabel("Accepted records (log scale)")
axes[0].set_title("Five tables; uneven maturity")
for i, value in enumerate(counts.values()):
    axes[0].text(value, i, f" {value:,}", va="center", fontsize=9)
country_counts = projects["country_code"].value_counts().sort_values()
axes[1].barh(country_counts.index, country_counts.values, color="#d69536")
axes[1].set_xscale("log")
axes[1].set_xlabel("Project records (log scale)")
axes[1].set_title("Country coverage — US registry dominates")
fig.suptitle("PV catalogue: sourced data, explicit coverage gaps", fontweight="bold")
plt.show()
