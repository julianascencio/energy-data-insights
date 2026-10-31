"""
Four PV climate schemes across mainland Chile
=============================================

Compare native source points whose centers fall within the existing contiguous
Chile mainland contour. The four classifications retain different periods and
resolutions. This is not a common-period accuracy benchmark.

See the :doc:`method and source guide </_generated/guides/climate-comparison>`.
Download the :download:`complete runnable comparison bundle <climate_examples.zip>`
or :download:`provenance manifest <climate_provenance.json>`.
The bundle includes all three scripts, CSV inputs, model JSON and map context.
Run from its extracted directory after installing the workspace. No network
requests or model fits occur during gallery execution.
"""

from pathlib import Path

import matplotlib.pyplot as plt

from energy_analysis.climate_comparison.plotting import load_study, plot_comparison

frames, model = load_study(Path("."), "chile")
fig = plot_comparison(Path("."), "chile")
plt.show()

# %%
# Inspect the classes behind the colors
# -------------------------------------
# JRC labels describe this saved model's centroid POA irradiation and module
# temperature. They are not numbered equivalents of another scheme's classes.
# Published ML21 codes denote climate families and their published subtypes.
# PVCZ T1-T10 and H1-H5 are separate thermal and specific-humidity bands.

for code, label in zip(model.codes[1:], model.labels[1:], strict=True):
    print(f"{code}: {label}")
for name, frame in frames.items():
    print(f"{name}: {len(frame):,} source rows in the downloaded regional sample")
