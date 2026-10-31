"""
Project coverage: countries, reported capacity and unknowns
===========================================================

Country counts describe this evolving catalogue, not the world's installed PV.
Report AC and DC separately and keep unknown capacities visible. Reported sums
include only known values; complete sums stay null if any project in a group
has missing capacity. Neither quantity resolves overlap between project phases,
source dates or operating statuses; filter and audit those before market analysis.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import matplotlib.pyplot as plt

from energy_analysis.pv_database import grouped_statistics
from energy_data_retrieval.pv_catalogue import build_parquet

ROOT = next(p for p in (Path.cwd(), *Path.cwd().parents) if (p / "catalogues/pv").is_dir())
with TemporaryDirectory() as folder:
    snapshot = Path(folder) / "snapshot"
    build_parquet(ROOT / "catalogues/pv", snapshot)
    ac = grouped_statistics(snapshot / "projects.parquet", "country_code", "capacity_ac_mw")
    dc = grouped_statistics(snapshot / "projects.parquet", "country_code", "capacity_dc_mw")

print("AC capacity (MWac); reported sums are partial when missing > 0:")
print(ac.to_string())
print("DC capacity (MWdc); never added to AC capacity:")
print(dc.to_string())

fig, axes = plt.subplots(1, 2, figsize=(12, 5.5), layout="constrained")
ac["records"].sort_values().plot.barh(ax=axes[0], color="#167d9a", logx=True)
axes[0].set(xlabel="Project records (log scale)", ylabel="Country", title="Catalogue coverage")
coverage = (100 * ac["known"] / ac["records"]).rename("AC reported").to_frame()
coverage["DC reported"] = 100 * dc["known"] / dc["records"]
coverage.plot.barh(ax=axes[1], color=["#167d9a", "#d69536"])
axes[1].set(xlim=(0, 100), xlabel="Projects with reported capacity (%)", ylabel="Country")
axes[1].set_title("Capacity completeness, separate bases")
fig.suptitle("Project database: geographic bias and missing capacity", fontweight="bold")
plt.show()
