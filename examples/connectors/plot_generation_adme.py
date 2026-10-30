"""Uruguay: measured wind output and dispatch limits
=================================================

Read **169 native SCADA samples** from Cerro Grande wind farm (ADME central 7).
The complete real source file contains measured power and the operator's
generation limit as separate channels. Eight unavailable output readings remain
missing; they are not filled with zeros or forecasts.

Source: `ADME open-data instructions <https://www.adme.com.uy/datosabiertos.html>`_.
Download the :download:`original SCADA SAS file <data/generation_adme.sas>` and
:download:`capture manifest <data/generation_adme_provenance.json>`.
The gallery runs offline with the unchanged public source file.
"""

import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt

from energy_data_retrieval.sources.adme import parse_scada_sas

# %%
# 1. Verify a measured SCADA archive file
# -----------------------------------------
# ADME's PRONOS application links separate forecast and SCADA directories. This
# connector selects only the SCADA directory. Fresh acquisition is bounded and
# includes directory/file provenance::
#
#     from datetime import date
#     from energy_data_retrieval.sources.adme import ADME_HOSTS, ADMEClient
#     from energy_data_retrieval.transport import HTTPClient
#     with HTTPClient(ADME_HOSTS) as http:
#         result = ADMEClient(http).generation(date(2026, 10, 22), date(2026, 10, 27),
#                                              central_id=7)
#
# To find another plant's ID, select it in the official PRONOS page and inspect
# its ``central`` URL parameter. Six-day query chunks are checked against the
# actual coverage of each published rolling seven-day SCADA file.

directory = Path(globals().get("__file__", Path.cwd() / "plot_generation_adme.py")).resolve().parent
data = directory / "data"
manifest = json.loads((data / "generation_adme_provenance.json").read_text())
raw = (data / manifest["fixture"]).read_bytes()
if hashlib.sha256(raw).hexdigest() != manifest["fixture_sha256"]:
    raise ValueError("ADME capture differs from its provenance")
frame = parse_scada_sas(raw.decode("utf-8"), central_id=7)
print("Source:", manifest["source_url"])
print("Captured:", manifest["retrieved_at_utc"])

# %%
# 2. Parse native timestamps, actual power and missing sentinels
# ---------------------------------------------------------------
# SAS is tab-separated text with a six-line header. Its Excel/LibreOffice serial
# dates carry no offset; this example explicitly interprets local labels as
# America/Montevideo (UTC-03 on these dates), converts them to UTC, and preserves
# the labels. The source's below-10000 missing sentinels become NaN.
#
# GETOTMEDP.AV is measured MW. CONSIGNAP is a dispatch limit, not output.
# Additional wind and control channels remain in the normalized frame.

print("Actual power channel:", frame["power_series"].iloc[0])
print("Sampling seconds:", frame["sampling_seconds"].iloc[0])
print("Reported measurements:", frame["value"].count(), "missing:", frame["value"].isna().sum())

# %%
# 3. Plot output alongside the control limit
# --------------------------------------------
# This is a comparison of measured power with an operating instruction. The gap
# between a limit and output is not lost energy: available wind power and the
# reason for each control instruction require separate evidence. No interval
# energy or interval boundary is inferred from these sample labels.

fig, ax = plt.subplots(figsize=(10, 4.8), layout="constrained")
ax.plot(frame["timestamp"], frame["value"], label="Measured output", linewidth=2)
ax.plot(
    frame["timestamp"],
    frame["dispatch_limit_mw"],
    label="Dispatch limit (CONSIGNAP)",
    linestyle="--",
    color="#a63d40",
    linewidth=1.4,
)
ax.set(
    title="ADME Cerro Grande · original 169-sample SCADA file",
    xlabel="Native sample label interpreted in Montevideo time and converted to UTC",
    ylabel="Power (MW)",
)
ax.grid(alpha=0.2)
ax.legend()
plt.show()

# %%
# Reuse
# --------
# Credit Administración del Mercado Eléctrico (ADME), retain the native file and
# clock interpretation, and preserve missing-value meaning. This plant capture
# is not a national generation total or a forecast of future wind output.
