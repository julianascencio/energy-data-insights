"""Alberta: seven days of measured solar generation
=================================================

Read **336 real hourly observations** for Big Sky and Travers solar from AESO's
public historical CSD Generation archive. The native CSV retains fixed-MST and
MPT clock labels, output, capability, fuel and location fields. The gallery uses
the public historical capture and needs no API key.

Source: `AESO historical generation downloads
<https://www.aeso.ca/market/market-and-system-reporting/data-requests/historical-generation-data/>`_.
Download the :download:`native CSV selection <data/generation_aeso.csv>` and
:download:`capture manifest <data/generation_aeso_provenance.json>`.
"""

import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt

from energy_data_retrieval.sources.aeso import parse_generation_csv

# %%
# 1. Verify the original historical CSV rows
# --------------------------------------------
# The full public ZIP and extracted CSV are hashed in the manifest. The selected
# header and whole rows preserve original bytes, including CRLF line endings.
# For a new historical file, download a five-minute/hourly ZIP from AESO's public
# archive, extract its native CSV, and use the bounded local importer::
#
#     from pathlib import Path
#     from energy_data_retrieval.sources.aeso import AESO_HOSTS, AESOClient
#     from energy_data_retrieval.transport import HTTPClient
#     with HTTPClient(AESO_HOSTS) as http:
#         result = AESOClient(http).from_native_file(Path("CSD Generation (Hourly).csv"),
#                                                    interval_minutes=60)
#
# The archive's changing Box download redirects require this explicit download
# step. Local imports record a file hash and do not claim an HTTP request.

directory = Path(globals().get("__file__", Path.cwd() / "plot_generation_aeso.py")).resolve().parent
data = directory / "data"
manifest = json.loads((data / "generation_aeso_provenance.json").read_text())
raw = (data / manifest["fixture"]).read_bytes()
if hashlib.sha256(raw).hexdigest() != manifest["fixture_sha256"]:
    raise ValueError("AESO capture differs from its provenance")
frame = parse_generation_csv(raw.decode("utf-8-sig"), interval_minutes=60)
print("Source:", manifest["official_download_page"])
print("Captured:", manifest["retrieved_at_utc"], "native rows:", len(frame))

# %%
# 2. Keep net output, capability and clock conventions distinct
# -------------------------------------------------------------
# Native Volume is average generation in MW over the chosen interval. Maximum
# Capability and System Capability are separate operating attributes. Source
# Date (MST) is fixed UTC-07 year round; the MPT label remains unchanged in the
# result, allowing autumn repeated civil hours to remain distinct.

print(
    frame.groupby("Asset Name").agg(
        observations=("value", "size"), reported=("value", "count"), peak_mw=("value", "max")
    )
)

# %%
# 3. Compare a complete week of source measurements
# ---------------------------------------------------
# Source labels are converted to UTC without asserting a start/end boundary.
# Missing readings remain gaps and negative net values are not clipped.

fig, ax = plt.subplots(figsize=(10, 4.8), layout="constrained")
for asset, profile in frame.groupby("Asset Name"):
    ax.plot(profile["timestamp"], profile["value"], label=asset, linewidth=1.8)
ax.set(
    title="AESO hourly solar generation · fixed-MST dates 1-7 September 2026",
    xlabel="Published clock label converted to UTC",
    ylabel="Hourly mean generation (MW)",
)
ax.grid(alpha=0.2)
ax.legend()
plt.show()

# %%
# 4. Acquire a current snapshot with an AESO subscription
# --------------------------------------------------------
# The separate current-generation API requires an AESO account/subscription key.
# This is a runnable acquisition recipe, not a captured authenticated response::
#
#     import os
#     with HTTPClient(AESO_HOSTS) as http:
#         current = AESOClient(http).current_generation(
#             api_key=os.environ["AESO_API_KEY"], asset_ids=["TVS1"])
#
# The API key travels in a redacted secret header. The current endpoint returns
# net generation, capability and contingency reserve separately in MW; it does
# not supply historical intervals. Credit the Alberta Electric System Operator
# and follow AESO's source reuse terms.
