"""
Canary Islands: nine PVDeg degradation-mechanism maps
=====================================================

This complements the :doc:`100 m thermal map <plot_pvdeg_canary>` with
**hourly-weather mechanism screening** at eleven locations across eight islands.
PVGIS supplies modeled TMY irradiance, humidity, temperature and wind, selected
from 2005-2023. Every result below is recomputed offline with PVDeg 0.7.4.

The maps cover thermal, damp-heat, broadband light-assisted and combined stress;
module-surface, front/back encapsulant and backsheet moisture; and solder fatigue.
They are **scenario metrics, not annual power loss or remaining lifetime**.
Do not add the metrics together: they have different units and overlapping physics.

Markers show the actual sampling locations. The coastlines use the existing
100 m climate masks for context only. No humidity/irradiance downscaling or spatial
interpolation is performed. These are not 100 m degradation predictions.
See the :doc:`guide </_generated/guides/pvdeg-canary>` for parameters, coverage,
missing mechanisms and reproducible input acquisition. Inputs and metadata are
available in the repository's ``examples/analysis/pvdeg_canary_weather`` directory.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.colors import ListedColormap
from rasterio.plot import plotting_extent
from rasterio.warp import transform

from energy_analysis.pvdeg_mechanisms import METRICS, analyze_manifest

# %%
# Calculate every mechanism using hashed hourly inputs
# ------------------------------------------------------
results = analyze_manifest(Path("pvdeg_canary_weather"))
print(results.round(3).to_string(index=False))
print("Weather: modeled PVGIS TMY; material / module parameters: scenarios")
print("No calibrated annual degradation rate, UV damage, PID or LeTID prediction")
x, y = transform("EPSG:4326", "EPSG:32628", results.longitude.tolist(), results.latitude.tolist())

# %%
# Nine separate maps with their own units
# ----------------------------------------
# Numbered sites can be identified in the following table. Gray land is context,
# not a computed degradation surface. Color is only assigned to sampled points.
land = []
for path in sorted(Path(".").glob("pvdeg_canary_*.tif")):
    with rasterio.open(path) as dataset:
        mask = dataset.read(1, masked=True)
        land.append(
            (
                np.ma.array(np.ones(mask.shape), mask=mask.mask),
                plotting_extent(mask, dataset.transform),
            )
        )
for group in (list(METRICS)[:3], list(METRICS)[3:6], list(METRICS)[6:]):
    fig, axes = plt.subplots(3, 1, figsize=(12, 15), layout="constrained")
    for ax, key in zip(axes, group, strict=True):
        title, unit, cmap = METRICS[key]
        ax.set_facecolor("#edf6fb")
        for mask, extent in land:
            ax.imshow(
                mask, extent=extent, cmap=ListedColormap(["#d4dbdf"]), interpolation="nearest"
            )
        artist = ax.scatter(
            x, y, c=results[key], cmap=cmap, s=100, edgecolors="black", linewidths=0.6, zorder=3
        )
        for i, (east, north) in enumerate(zip(x, y, strict=True), start=1):
            ax.annotate(
                str(i),
                (east, north),
                xytext=(5, 7),
                textcoords="offset points",
                fontsize=8,
                zorder=4,
            )
        ax.set(
            xlim=(160000, 690000),
            ylim=(3040000, 3290000),
            title=f"{title} · hourly TMY scenario · sampled sites",
            xlabel="UTM 28N easting (m)",
            ylabel="UTM 28N northing (m)",
        )
        fig.colorbar(artist, ax=ax, label=unit, shrink=0.9)

# %%
# Site comparison and interpretation
# ------------------------------------
# The exposure ratios use 60 kJ/mol and a constant 25 C / 50% RH / 1000 W/m²
# reference. The light term uses broadband POA, not a UV spectrum. Moisture
# uses upstream EVA W001 / PET W017 defaults. Solder fatigue uses the upstream
# hourly calibration; it is not a percentage of failed joints or module power.
fig, ax = plt.subplots(figsize=(12, 6), layout="constrained")
ax.axis("off")
columns = ["thermal", "damp_heat", "photothermal", "combined", "solder_fatigue"]
labels = [f"{i}. {name}" for i, name in enumerate(results.name, start=1)]
table = ax.table(
    cellText=results[columns].round(3).to_numpy(),
    rowLabels=labels,
    colLabels=["Thermal", "Damp heat", "Light + heat", "Combined", "Fatigue (kPa)"],
    loc="center",
    cellLoc="center",
)
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 1.7)
ax.set_title("Site lookup · exposure ratios and solder-fatigue scenario metric", pad=25)
plt.show()
