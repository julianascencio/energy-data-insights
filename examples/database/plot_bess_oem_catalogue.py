"""
BESS OEM products: specifications, coverage and evidence
========================================================

Build the source-backed OEM catalogue offline, query product configurations and
inspect evidence completeness. This is a product research inventory, not a market
share ranking, independent performance test or procurement recommendation.

Explore the same rows in the :doc:`BESS OEM viewer </bess-oem-database-viewer>`.
Exact supplier/model/variant identity is separate from mutable specifications.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import matplotlib.pyplot as plt
import pandas as pd

from energy_analysis.pv_database import field_profile
from energy_data_retrieval.bess_oem_catalogue import build_parquet

ROOT = next(p for p in (Path.cwd(), *Path.cwd().parents) if (p / "catalogues/bess_oem").is_dir())
with TemporaryDirectory() as folder:
    snapshot = Path(folder) / "bess_oem"
    manifest = build_parquet(ROOT / "catalogues/bess_oem", snapshot)
    systems = pd.read_parquet(snapshot / "systems.parquet")
    completeness = field_profile(snapshot / "systems.parquet")

print(f"{len(systems)} records from {systems['manufacturer'].nunique()} suppliers")
print("Input fingerprint:", manifest["input_sha256"])
print("Configurations and families:")
print(systems.groupby(["manufacturer", "record_scope"]).size().unstack(fill_value=0).to_string())

# %%
# Model strings are not specifications: the ST225kWh model has a source-reported
# nominal capacity of 229 kWh. Other PowerTitan variants have separate dates and
# regional ratings. Inspect all evidence before selecting an engineering value.
columns = [
    "model",
    "variant",
    "energy_capacity_mwh",
    "energy_basis",
    "energy_boundary",
    "power_capacity_mw",
    "power_basis",
    "apparent_power_mva",
    "product_status",
]
print("Sungrow source variants:")
print(systems.loc[systems["manufacturer"].eq("Sungrow"), columns].to_string(index=False))
example = systems.loc[systems["model"].eq("ST225kWh-110kW-2h")].iloc[0]
print("Exact sources:", list(example["source_urls"]))
print("Per-field evidence:", example["field_sources_json"])

# %%
# A reproducible screening query uses only explicitly documented configurations,
# nominal DC energy and LFP chemistry. A size screen is not a compatibility check.
screen = systems.loc[
    systems["record_scope"].eq("configuration")
    & systems["product_status"].eq("documented")
    & systems["chemistry"].eq("LFP")
    & systems["energy_basis"].eq("nominal")
    & systems["energy_boundary"].eq("dc")
    & systems["energy_capacity_mwh"].ge(5)
]
print("Documented configurations with nominal DC energy >= 5 MWh and reported LFP:")
print(screen[["manufacturer", *columns]].to_string(index=False))

# %%
# Plot coverage rather than summing product capacities. Multiple generations and
# configurations do not represent installed systems. Families have no scalar MW/MWh.
fields = [
    "energy_capacity_mwh",
    "power_capacity_mw",
    "apparent_power_mva",
    "chemistry",
    "cooling",
    "round_trip_efficiency_pct",
    "cycle_life",
    "warranty_years",
]
fig, axes = plt.subplots(1, 2, figsize=(14, 10), layout="constrained")
coverage = systems.groupby(["manufacturer", "record_scope"]).size().unstack(fill_value=0)
coverage = coverage.reindex(coverage.sum(axis=1).sort_values().index)
coverage.plot.barh(stacked=True, color=["#167d9a", "#d59c39"], ax=axes[0])
axes[0].set(xlabel="Catalogue records", ylabel="", title="Supplier coverage; not market share")
axes[0].legend(title="Record scope", fontsize=8)
known = systems[fields].notna().sum()
pd.DataFrame({"Reported": known, "Unknown": len(systems) - known}).plot.barh(
    stacked=True, color=["#167d9a", "#dfe5e9"], ax=axes[1]
)
axes[1].set(xlabel="Records", ylabel="", title="Field coverage, including families")
fig.suptitle("BESS OEM research catalogue · product specifications with provenance")
plt.show()

# %%
# RTE conditions differ between products; do not rank percentages without matching
# boundary, qualifier, duty cycle and auxiliary-load treatment. MVA remains separate
# from active MW, and family ranges are available in extensions_json.
print("RTE claims and their qualifications:")
print(
    systems.loc[
        systems["round_trip_efficiency_pct"].notna(),
        [
            "manufacturer",
            "model",
            "round_trip_efficiency_pct",
            "efficiency_boundary",
            "efficiency_qualifier",
            "efficiency_conditions",
        ],
    ].to_string(index=False)
)
print("Technical-field completeness:")
print(completeness.loc[fields].to_string())
