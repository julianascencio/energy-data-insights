"""Colombia: hourly actual generation with one settlement revision
===============================================================

Read **72 real plant-hour observations** from XM's SIMEM actual-generation
dataset 055A4D. Three resources and one complete Colombian source day are
selected from revision **TXF**. Selecting one revision prevents the same
plant-hour from being counted repeatedly across settlement versions.

Source: `XM SIMEM Generación real
<https://www.simem.co/datadetail/055a4d5f-3616-45e3-9bcd-1d3e3a4a47bd>`_.
Download the :download:`captured JSON <data/generation_xm.json>` and
:download:`capture manifest <data/generation_xm_provenance.json>`.
The example runs entirely offline with source observations, without a key.
"""

import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt

from energy_data_retrieval.sources.xm import parse_generation

# %%
# 1. Verify the selected native API response
# --------------------------------------------
# Metadata and complete source records are retained. The manifest records the
# original response hash and documents record selection/JSON reserialization.
# For a fresh bounded API retrieval, outside the offline gallery::
#
#     from datetime import date
#     from energy_data_retrieval.sources.xm import XM_HOSTS, XMClient
#     from energy_data_retrieval.transport import HTTPClient
#     with HTTPClient(XM_HOSTS) as http:
#         result = XMClient(http).generation(date(2024, 6, 1), date(2024, 6, 1),
#                                           version="TXF", resource_ids=["TPUY"])

directory = Path(globals().get("__file__", Path.cwd() / "plot_generation_xm.py")).resolve().parent
data = directory / "data"
manifest = json.loads((data / "generation_xm_provenance.json").read_text())
raw = (data / manifest["fixture"]).read_bytes()
if hashlib.sha256(raw).hexdigest() != manifest["fixture_sha256"]:
    raise ValueError("XM capture differs from its provenance")
frame = parse_generation(json.loads(raw), version="TXF")
print("Source:", manifest["source_url"])
print("Captured:", manifest["retrieved_at_utc"], "revision:", frame.attrs["selected_version"])

# %%
# 2. Preserve the physical unit and explicit revision
# ----------------------------------------------------
# GReal is energy measured at generation boundaries, supplied as kWh for each
# hour. The normalized value is MWh; original kWh remains in ``source_value``.
# Native FechaHora labels use Colombia's UTC-05 clock and are converted to UTC
# without shifting the provider's label convention. Null stays missing.
#
# SIMEM may publish TX1-TX5, TXF and TXR for the same hour. An unavailable TXF
# raises an error instead of silently selecting a provisional version. The
# separate dataset E17D25 contains daily estimates/schedules and is not used.

print(
    frame.groupby("unit_id").agg(
        observations=("value", "size"), reported=("value", "count"), energy_mwh=("value", "sum")
    )
)
print("Native unit:", frame["source_unit"].unique(), "normalized unit:", frame["unit"].unique())

# %%
# 3. Plot measured energy for the three generation resources
# -----------------------------------------------------------
# Resource identifiers are retained as published. Values are hourly energy;
# this chart does not relabel them as instantaneous MW or nameplate capacity.

fig, ax = plt.subplots(figsize=(9, 4.8), layout="constrained")
for resource, profile in frame.groupby("unit_id"):
    ax.plot(profile["timestamp"], profile["value"], marker=".", label=resource, linewidth=2)
ax.set(
    title="XM actual generation · 1 June 2024 · revision TXF",
    xlabel="Published source hour label converted to UTC",
    ylabel="Hourly generation (MWh)",
)
ax.grid(alpha=0.2)
ax.legend(title="CodigoPlanta")
plt.show()

# %%
# Reuse
# --------
# Credit XM / SIMEM and record dataset ID, plant identifiers, retrieval date and
# settlement revision. Comparing revisions can measure settlement corrections;
# combining them as additional generation would double count the same period.
