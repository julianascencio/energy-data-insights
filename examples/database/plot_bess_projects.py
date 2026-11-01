"""
Worldwide BESS projects: coverage, power, energy and evidence
=============================================================

Rebuild the committed worldwide battery project catalogue into typed Parquet,
then inspect coverage and source quality. These are real source-backed records,
not synthetic sites or an exhaustive market inventory. Status is a dated source
observation; a commissioning announcement does not establish live availability.

Run from a repository checkout with the workspace installed. No live API calls
or credentials are required. Explore the same records in the
:doc:`BESS viewer </bess-database-viewer>`.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import matplotlib.pyplot as plt
import pandas as pd

from energy_analysis.pv_database import field_profile, grouped_statistics
from energy_data_retrieval.bess_catalogue import build_parquet

ROOT = next(p for p in (Path.cwd(), *Path.cwd().parents) if (p / "catalogues/bess").is_dir())
with TemporaryDirectory() as folder:
    snapshot = Path(folder) / "bess"
    manifest = build_parquet(ROOT / "catalogues/bess", snapshot)
    projects = pd.read_parquet(snapshot / "projects.parquet")
    coverage = grouped_statistics(
        snapshot / "projects.parquet", "country_code", "energy_capacity_mwh"
    )
    completeness = field_profile(snapshot / "projects.parquet")

print(f"{len(projects)} projects in {projects['country_code'].nunique()} countries")
print("Input fingerprint:", manifest["input_sha256"])
print("Country counts and energy-field availability (all source dates/statuses):")
print(coverage[["records", "known", "missing"]].to_string())
print("Status observations; not live operating status:")
print(projects["status"].value_counts().to_string())

# %%
# A focused query keeps the conflicting owner/regulatory MW observations visible.
# Inspect conflicts_json before deciding which rating is appropriate for a study.
print("Chile projects and unresolved rating observations:")
print(
    projects.loc[
        projects["country_code"].eq("CHL"),
        [
            "name",
            "power_capacity_mw",
            "energy_capacity_mwh",
            "status_as_of",
            "quality_status",
            "conflicts_json",
            "source_urls",
        ],
    ].to_string(index=False)
)
print("Technical-field completeness:")
print(
    completeness.loc[
        [
            "power_capacity_mw",
            "energy_capacity_mwh",
            "chemistry",
            "latitude",
            "duration_hours",
            "battery_manufacturers",
            "round_trip_efficiency_pct",
        ]
    ].to_string()
)

# %%
# Plot project counts and paired ratings. Never use the PV or whole-site grid
# connection capacity in place of missing battery MW. Colour separates source
# status, and open conflict records are omitted from the capacity scatter.
fig, axes = plt.subplots(1, 2, figsize=(13, 9), layout="constrained")
projects["country_code"].value_counts().sort_values().plot.barh(ax=axes[0], color="#167d9a")
axes[0].set(
    xscale="log",
    xlabel="Project / plant records (log scale)",
    ylabel="Country",
    title="Catalogue coverage; not market share",
)
paired = projects.loc[
    projects["quality_status"].eq("source_backed")
    & projects["power_capacity_mw"].gt(0)
    & projects["energy_capacity_mwh"].gt(0)
]
for status, group in paired.groupby("status"):
    axes[1].scatter(
        group["power_capacity_mw"], group["energy_capacity_mwh"], label=status, alpha=0.8
    )
axes[1].set(
    xscale="log",
    yscale="log",
    xlabel="Reported battery power (MW)",
    ylabel="Reported battery energy (MWh)",
    title="Paired source ratings; unresolved conflicts excluded",
)
axes[1].legend(fontsize=8)
axes[1].grid(alpha=0.2)
fig.suptitle("Worldwide BESS catalogue · source observations, not market totals", fontweight="bold")
plt.show()

# %%
# The E/P ratio is not presented as guaranteed discharge duration: energy may be
# nominal or usable, and power may have an unspecified AC/DC basis. Capacities
# also have different status dates and phase scopes. Filter and reconcile these
# fields before any fleet sum, ranking, project comparison or market estimate.
