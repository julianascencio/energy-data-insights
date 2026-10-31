"""Chile's smallest registered operating solar plant: Concón
=========================================================

PMGD PFV Concón (CEN ID 2082) is the minimum positive ``potencia_maxima`` among
the **757 operating solar entries in the 2026-10-31 CEN snapshot**: 0.1 MW.
This is not a claim about every small private, net-billing or off-grid system
in Chile. The installer reports 118 kWp DC; that is not the registry power field.

The same experimental counter used for Icor is attempted on real imagery.
It returns **no resolved module count**, not zero modules. Glare and unresolved
frame lines prevent a defensible inventory; no capacity-to-module conversion
or manually supplied row count is used to fill the gap.

Download :download:`both offline Chile examples and audit exports
<chile_module_counting.zip>`. See the :doc:`evidence and reproduction guide
<../../_generated/guides/chile-module-counting>`.
"""

import json
from dataclasses import replace
from pathlib import Path

import matplotlib.pyplot as plt

from energy_analysis.module_counting.chile import audit_site_image, load_chile_study
from energy_methods.pv_module_counting import count_regular_pv_modules

HERE = Path(globals().get("__file__", Path.cwd() / "example.py")).resolve().parent
DATA = HERE / "data/chile_modules"
manifest, ranking = load_chile_study(DATA)
audit = audit_site_image(DATA, "concon")
print(ranking[["id", "nombre", "potencia_maxima"]].head(6).to_string(index=False))
print(
    json.dumps(
        {k: audit[k] for k in ("status", "image_candidate_count", "whole_plant_image_count")},
        indent=2,
    )
)

# %%
# 1. Review the inspection scope and actual optical evidence
# ----------------------------------------------------------
# The rectangle encloses the visible array-like structures; it is manually
# selected and is not an operator-validated boundary. The registry point lies
# elsewhere in the industrial site. The source metadata probe reports a
# 2026-07-02 acquisition, 0.34 m source resolution and 0.3 m service sampling.
# These metadata describe one probe, not guaranteed uniform coverage of the image.
# No sharpening or synthetic detail is introduced.
fig, axes = plt.subplots(1, 3, figsize=(16, 6), layout="constrained")
for ax in axes[:2]:
    ax.imshow(audit["rgb"], interpolation="nearest")
    ax.contour(audit["mask"], levels=[0.5], colors=["#00d8eb"], linewidths=1)
    ax.set_axis_off()
axes[0].set_title("Concón · inspection scope in cyan")
axes[1].set(xlim=(170, 410), ylim=(400, 115), title="Native-pixel zoom · glare obscures frames")
smallest = ranking.head(6).iloc[::-1]
axes[2].barh(
    smallest.nombre.str.replace("PMGD PFV ", "", regex=False),
    smallest.potencia_maxima * 1000,
    color="#1d8794",
)
axes[2].set(
    xlabel="CEN maximum-power field (kW)", title="Six smallest positive operating solar entries"
)
axes[2].tick_params(axis="y", labelsize=8)
fig.suptitle("Concón: 100 kW registry entry · automatic module count unresolved", fontsize=17)
fig.text(
    0.02,
    0.015,
    "© 2026 Esri and its licensors · Esri, Vantor, Earthstar Geographics, "
    "GIS User Community. All rights reserved.",
    fontsize=8,
)
fig.set_layout_engine("constrained", rect=(0, 0.06, 1, 0.94))

# %%
# 2. Check that minor parameter changes do not manufacture a count
# ----------------------------------------------------------------
# This small sensitivity check is not an accuracy assessment. Each unresolved
# run remains None. A future non-null result would still need visual review and
# held-out labelled modules before being treated as a reliable count.
result = audit["result"]
attempts = []
for blue in (0.005, 0.01, 0.025):
    trial = count_regular_pv_modules(
        audit["rgb"], audit["mask"], config=replace(result.config, blue_excess=blue)
    )
    attempts.append({"blue_excess": blue, "image_candidates": trial.estimated_modules})
print(json.dumps(attempts, indent=2))

# %%
# 3. Preserve the evidence gap
# ----------------------------
# No independent module inventory has been retrieved for this plant. Obtain an
# as-built module schedule or a glare-free orthophoto/UAV survey. The installer
# photographs confirm the PV technology but do not show every module unobscured;
# they are linked in the guide, not substituted for a full-site measurement.
plt.show()
