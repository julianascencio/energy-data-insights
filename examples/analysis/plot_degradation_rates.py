"""
Worldwide climate degradation rates
===================================

Recompute the combined rate and its three mechanisms from the saved 2016-2018
ERA5 study. These are **modelled scenario rates in %/year**, using published
mono-Si coefficients and explicit stress-processing assumptions. They are not
measured fleet degradation or a high-resolution reproduction of the thesis.

The grid samples land centres at **15° spacing**. Of 71 sampled land locations,
63 have complete inputs across all three years; eight stay missing. Colored
rectangles are coarse sample footprints, not uniform conditions across them.

Download the :download:`runnable bundle <degradation_examples.zip>` or
:download:`source and calibration provenance <degradation_provenance.json>`.
The :doc:`guide </_generated/guides/degradation-gallery>` explains regeneration,
attribution, regional mapping and scientific limits. This example runs offline.
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from energy_analysis.degradation.gallery import load_degradation_example, plot_degradation_maps
from energy_methods.degradation import DegradationParameters
from energy_methods.degradation_mapping import map_degradation

# %%
# Recompute from annual stresses
# ------------------------------
# The loader checks input hashes and recalculates every rate using the reusable
# methods package. It then checks the result against the original archived run.
# Temperature is module temperature; RH is percent; UV is the annual 280-400 nm
# dose. Missing inputs are never replaced with zero.

annual, rates, metadata = load_degradation_example(Path("."))
print(metadata["description"])
print(f"Valid land samples: {metadata['valid_cells']}/{metadata['land_cells']}")
print(f"Retrieved hourly location records: {metadata['hours_retrieved']:,}")
print(rates[["total_rate", "valid_year_count", "rate_class"]])
fig = plot_degradation_maps(rates, Path("climate_world_boundaries.geojson"))
plt.show()

# %%
# Read rate categories without hiding missing cells
# -------------------------------------------------
# The thesis mapping uses 0.2%/year bands. The combined expression is
# multiplicative: mechanism rates are not additive shares of the total.
# A number of 0.5 means 0.5%/year under this calibration, not 50%/year.

fig = plot_degradation_maps(rates, Path("climate_world_boundaries.geojson"), categorical=True)
plt.show()
print(
    f"Combined scenario range: {float(rates.total_rate.min()):.3f} to "
    f"{float(rates.total_rate.max()):.3f}%/year"
)

# %%
# Check an aggregation choice
# ---------------------------
# Evaluating the model at mean stresses differs from averaging annual rates.
# This sensitivity calculation makes that choice visible. It is not a statistical
# uncertainty interval and does not address uncertainty in the module calibration.


parameters = DegradationParameters(**json.loads(Path("degradation_parameters.json").read_text()))
annual_rate_average = map_degradation(annual, parameters, aggregation="mean_rate")
difference = annual_rate_average.total_rate - rates.total_rate
print("Maximum absolute aggregation difference (%/year):", float(np.abs(difference).max()))

# %%
# What to do with the map
# -----------------------
# Use it to screen climate-driven mechanisms and choose locations for more
# detailed studies. For a project, retrieve local hourly weather, specify mounting
# and module calibration, and compare the model with measured performance loss.
# Do not turn the coarse global sample nearest a site into a site degradation
# forecast or use this scenario directly as a warranty or lifetime estimate.
# The guide gives NetCDF/GeoJSON export commands and a regional-study workflow.
