"""A clearer Chilean pilot: module candidates near Rengo
===========================================================

El Mirlo, CEN site 2253, is about **5.1 km south of a rounded Rengo centre**,
in Malloa. Six nearby sites were screened for visible frames. The selected
southern inspection block has a clear two-axis lattice in real Esri imagery;
the metadata probe reports **14 January 2024 / 0.31 m source resolution**.

An orientation-aware counter combines PCA rectification, autocorrelation,
observed frame peaks and local colour/contrast checks. It supports two-row
tables that the original Icor configuration cannot resolve. It returns
**2,055 candidates in this partial block**, with exclusions rather than infill.

The small visual audit matches **51 of 72 reference centres (70.8%)**, with
no extra detections in the labelled regions. These are single-assistant visual
annotations on the development image, **not independent human ground truth or
held-out accuracy**. Initial seam-versus-centre misclicks were corrected by
re-inspecting raw pixels; both annotation versions are retained. The remainder
of the 2,055 candidates has not been individually validated.

Download :download:`the runnable example, images, annotations and audit exports
<rengo_module_counting.zip>`. Read the :doc:`method and evidence limits
<../../_generated/guides/rengo-module-counting>` before using the counts.
"""

import json
from dataclasses import replace
from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PolyCollection
from matplotlib.patches import Rectangle

from energy_analysis.module_counting.rengo import run_rengo_study
from energy_methods.pv_lattice_counting import count_lattice_pv_modules

HERE = Path(globals().get("__file__", Path.cwd() / "example.py")).resolve().parent
DATA = HERE / "data/rengo_modules"
study = run_rengo_study(DATA)
result = study["advanced"]
manifest = study["manifest"]
accepted = [c.vertices_xy for c in result.cells if c.status != "excluded"]
excluded = [c.vertices_xy for c in result.cells if c.status == "excluded"]
credit = manifest["attribution"]
print(
    json.dumps(
        {
            "site": manifest["site"]["name"],
            "partial_block_candidates": result.estimated_modules,
            "whole_plant_image_count": None,
            "original_counter": study["baseline"].estimated_modules,
            "visual_audit": study["audits"]["orientation_lattice"]["total"],
        },
        indent=2,
    )
)

# %%
# 1. Locate the block and review the automatic result
# ---------------------------------------------------------
# Cyan denotes accepted candidates, not certified assets. The block is a manually
# defined inspection area within the plant. It does not cover every module.
# The source is slightly oversampled: delivered pixels are 0.245 x 0.296 m.
# The counter applies the 0.31 m source limit, not just the delivered pixel size.
fig, axes = plt.subplots(1, 2, figsize=(15, 7), layout="constrained")
overview = manifest["overview_capture"]
w, s, e, n = overview["bbox"]
axes[0].imshow(mpimg.imread(DATA / overview["filename"]), extent=(w, e, s, n))
capture = manifest["detail_capture"]
w, s, e, n = capture["bbox"]
axes[0].add_patch(Rectangle((w, s), e - w, n - s, fill=False, ec="#00d8eb", lw=1.8))
axes[0].set_title("El Mirlo · image extent in cyan")
axes[0].set(xlabel="Longitude", ylabel="Latitude")
axes[0].ticklabel_format(useOffset=False, style="plain")
axes[0].tick_params(axis="x", rotation=25)
axes[1].imshow(study["rgb"], interpolation="nearest")
axes[1].add_collection(
    PolyCollection(accepted, facecolors="none", edgecolors="#00e6d8", linewidths=0.25)
)
axes[1].contour(study["mask"], levels=[0.5], colors=["white"], linewidths=0.8)
axes[1].set_axis_off()
axes[1].set_title(f"{result.estimated_modules:,} candidates · {len(result.tables)} resolved tables")
fig.suptitle("Near Rengo: a useful candidate-counting pilot", fontsize=18)
fig.text(0.02, 0.01, credit, fontsize=8)
fig.set_layout_engine("constrained", rect=(0, 0.05, 1, 0.94))

# %%
# 2. Compare raw pixels, reference centres and predicted boundaries
# -----------------------------------------------------------------------
# White circles are approximate visual reference centres. Cyan boxes are
# accepted detections; orange boxes are excluded cells. Both rows show the same
# original pixels with nearest-neighbour display. No sharpening is applied.
# The lower strip omits the ambiguous hardware/shadow band from scoring.
fig, axes = plt.subplots(2, 3, figsize=(16, 7), layout="constrained")
views = [(346, 298, 408, 321), (199, 429, 267, 453), (519, 170, 587, 191)]
names = [
    "Central strip · 24 references",
    "Lower strip · 22 references",
    "Eastern strip · 26 references",
]
for col, (bounds, title) in enumerate(zip(views, names, strict=True)):
    x0, y0, x1, y1 = bounds
    for row in range(2):
        ax = axes[row, col]
        ax.imshow(study["rgb"], interpolation="nearest")
        ax.set(xlim=(x0, x1), ylim=(y1, y0))
        ax.set_axis_off()
        ax.set_title(title if row == 0 else "References + detections / exclusions", fontsize=11)
        if row:
            ax.add_collection(
                PolyCollection(accepted, facecolors="none", edgecolors="#00e6d8", linewidths=1)
            )
            ax.add_collection(
                PolyCollection(excluded, facecolors="none", edgecolors="#ffad42", linewidths=0.8)
            )
            for region in study["annotations"]["regions"]:
                points = np.asarray(region["centres_xy"])
                if len(points):
                    ax.scatter(
                        *points.T, s=18, facecolors="none", edgecolors="white", linewidths=0.7
                    )
    if col == 1:
        for ax in axes[:, col]:
            ax.axvspan(232, 240, color="black", alpha=0.5)
fig.suptitle(
    "51 of 72 visually marked modules matched · 21 missed · no extra detections in scored regions",
    fontsize=16,
)
fig.text(
    0.02,
    0.01,
    credit + "\nSame-image exploratory audit; annotations require human review.",
    fontsize=8,
)
fig.set_layout_engine("constrained", rect=(0, 0.07, 1, 0.94))

# %%
# 3. Report local improvement without calling it field accuracy
# -------------------------------------------------------------------
# Matching is one-to-one within two delivered pixels. Two additional negative
# regions contain no reference modules and no detections. The original method
# returns None for this scope: the bar at zero denotes zero *matched detections*,
# not a claim that the site contains zero modules.
fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
names = ["Original defaults", "Orientation + lattice"]
matched = [
    study["audits"][k]["total"]["matched"] for k in ("original_defaults", "orientation_lattice")
]
ax.barh(names, matched, color=["#81919d", "#087f8c"])
ax.axvline(72, color="#ef9c42", ls="--", label="72 visual reference centres")
for y, value in enumerate(matched):
    ax.text(value + 1, y, f"{value} / 72", va="center")
ax.set(
    xlim=(0, 83),
    xlabel="Matched detections in the annotated regions",
    title="Local diagnostic comparison · same image, same scope",
)
ax.legend(loc="lower right")

# %%
# 4. Check sensitivity and keep the unresolved parts visible
# ----------------------------------------------------------------
# A small parameter change alters candidate counts. This is a screening method;
# neither these counts nor the visual spot-check establish a whole-site total.
# Fixed parameters and complete rejection reasons are in the download.
sensitivity = []
for prominence in (0.012, 0.015, 0.018):
    trial = count_lattice_pv_modules(
        study["rgb"], study["mask"], config=replace(result.config, frame_prominence=prominence)
    )
    sensitivity.append(
        {"frame_prominence": prominence, "partial_block_candidates": trial.estimated_modules}
    )
print(json.dumps({"sensitivity": sensitivity, "rejected_tables": result.rejected_tables}, indent=2))
plt.show()
