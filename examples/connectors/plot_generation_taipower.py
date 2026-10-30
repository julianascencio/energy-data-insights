"""Taiwan: a real Taipower generation snapshot
==============================================

Read a complete genuine Taipower JSON publication with asset output, technology
subtotals, status notes and storage-load rows. Values are **MW snapshots**.
The ten-minute refresh cadence does not establish a ten-minute averaging
interval, so this example does not integrate the values into energy.

The feed's display labels can describe units, plants or groups. Known group
labels and subtotals are distinguished from reported assets. Source:
`Taipower's official open dataset <https://data.gov.tw/en/datasets/8931>`_,
under Taiwan's Open Government Data License 1.0.

Download the :download:`real JSON <data/generation_taipower.json>` and
:download:`provenance <data/generation_taipower_provenance.json>` alongside this
script in a ``data/`` subdirectory. The example runs offline without a key.
"""

import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt

from energy_data_retrieval.sources.taipower import parse_generation

# %%
# 1. Verify and parse the original response
# -----------------------------------------
directory = (
    Path(globals().get("__file__", Path.cwd() / "plot_generation_taipower.py")).resolve().parent
)
data = directory / "data"
raw = (data / "generation_taipower.json").read_bytes()
manifest = json.loads((data / "generation_taipower_provenance.json").read_text())
if hashlib.sha256(raw).hexdigest() != manifest["fixture_sha256"]:
    raise ValueError("Taipower sample differs from its acquisition manifest")
payload = json.loads(raw)
assets = parse_generation(payload)
complete = parse_generation(payload, include_aggregates=True, include_storage_load=True)
print("Publication time:", payload["DateTime"], "Asia/Taipei")
print("Default asset rows:", len(assets), "; all reported rows:", len(complete))
print(complete.groupby(["aggregation", "flow"]).size())

# %%
# 2. Plot the provider's renewable subtotals as subtotals
# -------------------------------------------------------
# We select exactly one published subtotal per technology. We never add its
# children to the subtotal, which would double-count the same generation.
totals = complete.loc[complete.is_total & complete.technology.isin(["solar", "wind"])]
if len(totals) != 2:
    raise ValueError("The snapshot should have one solar and one wind subtotal")
fig, ax = plt.subplots(figsize=(7, 4), layout="constrained")
bars = ax.bar(totals.technology, totals.value, color=["#c48a28", "#096b76"])
ax.bar_label(bars, fmt="%.1f MW", padding=3)
ax.set(
    ylabel="Published net power (MW)", title="Real renewable-output snapshot (not interval energy)"
)
ax.margins(y=0.15)
plt.show()

# %%
# 3. Inspect individually reported assets and keep status notes
# -------------------------------------------------------------
# The plot uses numbered labels to avoid requiring a Chinese font. The printed
# table provides the exact original names and operating-status notes.
selected = assets.loc[assets.technology.eq("wind") & assets.value.notna()].nlargest(5, "value")
print(selected[["asset_id", "value", "capacity_mw", "source_status"]].to_string(index=False))
fig, ax = plt.subplots(figsize=(8, 4.5), layout="constrained")
labels = [f"Wind asset {index}" for index in range(1, len(selected) + 1)]
bars = ax.barh(labels, selected.value, color="#096b76")
ax.bar_label(bars, fmt="%.1f", padding=3)
ax.set(xlabel="Net power snapshot (MW)", title="Five reported wind assets with the largest output")
ax.invert_yaxis()
ax.margins(x=0.15)
plt.show()
