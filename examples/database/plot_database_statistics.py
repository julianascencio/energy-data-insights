"""
Database statistics: size, schema and missing metadata
======================================================

Measure the actual Parquet files, rather than hard-coding launch counts.
Non-null coverage is not accuracy: the shared wide schema deliberately contains
fields that do not apply to every entity. Zero and false are reported values;
unknown values remain null. Run from a repository checkout, without API access.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import matplotlib.pyplot as plt

from energy_analysis.pv_database import field_profile, snapshot_overview
from energy_data_retrieval.pv_catalogue import build_parquet

ROOT = next(p for p in (Path.cwd(), *Path.cwd().parents) if (p / "catalogues/pv").is_dir())
with TemporaryDirectory() as folder:
    snapshot = Path(folder) / "snapshot"
    build_parquet(ROOT / "catalogues/pv", snapshot)
    overview = snapshot_overview(snapshot)
    module_fields = field_profile(snapshot / "modules.parquet")
    project_fields = field_profile(snapshot / "projects.parquet")

print("Snapshot statistics (actual files):")
print(overview.to_string())
print("Project field coverage, including missing values:")
print(project_fields.loc[["country_code", "capacity_ac_mw", "capacity_dc_mw", "latitude"]])

fig, axes = plt.subplots(1, 2, figsize=(12, 5), layout="constrained")
overview["rows"].plot.barh(ax=axes[0], color="#167d9a", logx=True)
axes[0].set(xlabel="Records (log scale)", ylabel="", title="Database inventory")
fields = ["pmax_stc_w", "efficiency_stc_pct", "bifacial", "weight_kg", "product_warranty_years"]
module_fields.loc[fields, "coverage_pct"].plot.barh(ax=axes[1], color="#d69536")
axes[1].set(xlim=(0, 100), xlabel="Non-null rows (%)", ylabel="", title="Module metadata coverage")
fig.suptitle("Parquet statistics — coverage is not a quality score", fontweight="bold")
plt.show()
