"""
Hydropower: worldwide historical coverage and evidence gaps
===========================================================

Rebuild the WRI Global Power Plant Database hydro partition offline as typed
Parquet and map its reported coordinates. CC BY 4.0 attribution: World Resources
Institute, GPPD v1.3.0 repository snapshot. WRI stopped maintenance in early 2022.
This is historical discovery coverage, not a current operating census or a
ranking of installed national capacity. 110 Norwegian records have reviewed
NVE lifecycle and technical enrichment; 335 US records carry dated 2025 EIA inventory.
Pumped storage is not inferred from names.
See the :doc:`interactive hydro viewer </hydro-database-viewer>` for source evidence.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import matplotlib.pyplot as plt
import pandas as pd

from energy_data_retrieval.hydro_catalogue import build_parquet, capacity_summary, load_records

ROOT = next(p for p in (Path.cwd(), *Path.cwd().parents) if (p / "catalogues/hydro").is_dir())
rows = load_records(ROOT / "catalogues/hydro")
with TemporaryDirectory() as folder:
    snapshot = Path(folder) / "snapshot"
    manifest = build_parquet(ROOT / "catalogues/hydro", snapshot)
    plants = pd.read_parquet(snapshot / "projects.parquet")
print("Canonical records:", len(plants), "Countries:", plants.country_code.nunique())
print("NVE-enriched operating records:", sum("nve-hydro-20261105" in r["sources"] for r in rows))
print(
    "EIA year-end 2025 enriched records:",
    sum(any(s.startswith("eia860-2025-hydro-") for s in r["sources"]) for r in rows),
)
print("Input fingerprint:", manifest["input_sha256"])
print("Reviewed installed generating MW:", capacity_summary(rows, "installed_capacity_mw"))
print("Pumping input MW (separate from generation):", capacity_summary(rows, "pumping_capacity_mw"))

fig, axes = plt.subplots(1, 2, figsize=(13, 5), layout="constrained")
located = plants.dropna(subset=["latitude", "longitude"])
axes[0].scatter(located.longitude, located.latitude, s=4, alpha=0.4, color="#087e8b")
axes[0].set(
    xlim=(-180, 180),
    ylim=(-60, 85),
    xlabel="Longitude [degrees]",
    ylabel="Latitude [degrees]",
    title="Reported plant locations · historical WRI inventory",
)
axes[0].grid(alpha=0.2)
plants.country_code.value_counts().head(15).sort_values().plot.barh(ax=axes[1], color="#087e8b")
axes[1].set(
    xlabel="Historical plant records",
    ylabel="Country code",
    title="Coverage leaders, not capacity market share",
)
fig.suptitle("Global hydro coverage · dated NVE/EIA updates · capacity scope unresolved")
plt.show()
