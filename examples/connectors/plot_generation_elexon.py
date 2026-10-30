"""Great Britain: real BM-unit settlement energy
=============================================

Read a complete **48-period metered day** for Elexon BM unit ``T_SUTBS-1`` on
1 October 2026. These are native B1610 **MWh per half-hour**, including negative
net demand. They are settlement data, not live SCADA. The identifier alone does
not establish the unit's technology, rated capacity or plant availability.

Source: `Elexon B1610 metered-volume explanation
<https://www.elexon.co.uk/bsc/article/bsc-insight-how-to-get-more-detailed-metered-volume-data-from-our-insights-solution/>`_.
Download the :download:`native response <data/generation_elexon.json>` and
:download:`capture manifest <data/generation_elexon_provenance.json>`.
This example runs offline with no API key.
"""

import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt

from energy_data_retrieval.sources.elexon import normalize_generation

# %%
# 1. Verify the exact public response
# -----------------------------------
# API access is public. A fresh acquisition, not executed by the gallery::
#
#     from datetime import date
#     from energy_data_retrieval.sources.elexon import ELEXON_HOSTS, ElexonClient
#     from energy_data_retrieval.transport import HTTPClient
#     with HTTPClient(ELEXON_HOSTS) as http:
#         result = ElexonClient(http).generation(
#             date(2026, 10, 1), date(2026, 10, 1), bm_unit="T_SUTBS-1"
#         )

directory = (
    Path(globals().get("__file__", Path.cwd() / "plot_generation_elexon.py")).resolve().parent
)
data = directory / "data"
manifest = json.loads((data / "generation_elexon_provenance.json").read_text())
capture = manifest["files"][0]
raw = (data / capture["file"]).read_bytes()
if hashlib.sha256(raw).hexdigest() != capture["sha256"]:
    raise ValueError("Elexon capture differs from its provenance")
print("Source:", capture["source_url"])
print("Retrieved:", capture["retrieved_at_utc"])

# %%
# 2. Preserve settlement periods, revisions and signed quantities
# ----------------------------------------------------------------
# The parser derives UTC interval starts from UK settlement dates and periods.
# It handles 46/48/50-period civil days and validates the published UTC end label.
# Elexon publishes this product after about five working days and revises it
# through settlement runs. The capture below contains the SF run, not a forecast.

frame = normalize_generation(json.loads(raw))
print(
    frame[
        ["unit_id", "settlement_date", "settlement_period", "value", "unit", "settlement_run"]
    ].head()
)
print("Reported periods:", frame.settlement_period.nunique())
print("Missing quantities:", frame.value.isna().sum())

# %%
# 3. Plot native half-hour energy
# -------------------------------
# Negative quantities remain visible. The source's generic psrType is not used
# to assign a fuel. Period labels preserve the civil-day context, and the values
# are not divided or multiplied by the interval length.

fig, ax = plt.subplots(figsize=(9, 4.5), layout="constrained")
ax.plot(frame.settlement_period, frame.value, color="#257c79", marker=".")
ax.axhline(0, color="#555555", linewidth=0.8)
ax.set(
    xlabel="UK settlement period",
    ylabel="Net metered energy (MWh / half-hour)",
    title="Elexon T_SUTBS-1 · reported settlement energy · 1 October 2026",
)
ax.grid(alpha=0.2)
plt.show()

# %%
# Interpretation
# ----------------
# Positive and negative intervals can be summarized separately. This is only
# the selected BM unit and day, not the whole British generation system. No
# weather-normalized expected-power or performance claim is implied.

print("Positive reported energy (MWh):", frame.loc[frame.value.gt(0), "value"].sum(min_count=1))
print("Negative reported energy (MWh):", frame.loc[frame.value.lt(0), "value"].sum(min_count=1))
