"""
Chile: native-resolution PVDeg thermal-stress map
====================================================================================================

Run PVDeg on real CHELSA v2.1 monthly temperature climatology (1981-2010).
The native **30-arcsecond grid** is about 927 m north-south, with east-west
spacing varying with latitude. It is not upsampled to an artificial 100 m grid.
Continental Chile includes Chiloe, Tierra del Fuego and coastal archipelagos;
Pacific oceanic islands and Antarctica are outside this study.

Colors show **relative thermal exposure**, not annual degradation or lifetime.
The +20 C module-air offset and 60 kJ/mol activation energy are assumptions.
Monthly means cannot resolve hourly heating; humidity and irradiance effects
are disabled. See the :doc:`guide </_generated/guides/pvdeg-chile>`.

Offline inputs: :download:`provenance <pvdeg_chile_provenance.json>`,
:download:`boundary <pvdeg_chile_boundary.geojson>` and monthly temperatures
:download:`01 <pvdeg_chile_tas_01.tif>`, :download:`02 <pvdeg_chile_tas_02.tif>`,
:download:`03 <pvdeg_chile_tas_03.tif>`, :download:`04 <pvdeg_chile_tas_04.tif>`,
:download:`05 <pvdeg_chile_tas_05.tif>`, :download:`06 <pvdeg_chile_tas_06.tif>`,
:download:`07 <pvdeg_chile_tas_07.tif>`, :download:`08 <pvdeg_chile_tas_08.tif>`,
:download:`09 <pvdeg_chile_tas_09.tif>`, :download:`10 <pvdeg_chile_tas_10.tif>`,
:download:`11 <pvdeg_chile_tas_11.tif>`, :download:`12 <pvdeg_chile_tas_12.tif>`.
Download these beside the Python script, or use the gallery ZIP.
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.colors import Normalize
from rasterio.features import geometry_mask
from rasterio.plot import plotting_extent
from shapely.geometry import shape

from energy_analysis.pvdeg_canary import MONTH_HOURS
from energy_analysis.pvdeg_chile import run_chile_study
from energy_methods.country_boundaries import polygons
from energy_methods.pvdeg import thermal_stress_index

# %%
# Verify inputs and execute PVDeg in bounded batches
# --------------------------------------------------
values, profile, manifest = run_chile_study(Path("."))
geometry = shape(json.loads(Path(manifest["boundary_file"]).read_text()))
land = geometry_mask(
    [geometry], out_shape=values.shape, transform=profile["transform"], invert=True
)
valid = np.isfinite(values)
print(
    f"Valid land cells: {valid.sum():,}; missing climate inside boundary: {(land & ~valid).sum():,}"
)
print("Native 30 arcseconds, 1981-2010 modeled climatology; no site-level accuracy claim.")
print("Scenario: air +20 C, Ea=60 kJ/mol, reference=25 C; relative thermal exposure only.")


def panel(ax, bounds, title):
    """Render original cells with a shared fixed color scale and geographic outline."""
    west, south, east, north = bounds
    # Slice before plotting: small regional figures need not render the full rectangle.
    window = rasterio.windows.from_bounds(*bounds, transform=profile["transform"])
    row0 = max(0, int(np.floor(window.row_off)))
    row1 = min(values.shape[0], int(np.ceil(window.row_off + window.height)))
    col0 = max(0, int(np.floor(window.col_off)))
    col1 = min(values.shape[1], int(np.ceil(window.col_off + window.width)))
    tile = values[row0:row1, col0:col1]
    transform = rasterio.windows.transform(
        rasterio.windows.Window(col0, row0, col1 - col0, row1 - row0), profile["transform"]
    )
    ax.set_facecolor("#eaf2f7")
    # Missing climate on land is gray; ocean is transparent.
    land_tile = land[row0:row1, col0:col1]
    ax.imshow(
        np.ma.masked_where(~land_tile, np.ones(tile.shape)),
        extent=plotting_extent(tile, transform),
        cmap="Greys",
        vmin=0,
        vmax=3,
    )
    artist = ax.imshow(
        np.ma.masked_invalid(tile),
        extent=plotting_extent(tile, transform),
        cmap="magma",
        norm=Normalize(0, 5),
        interpolation="nearest",
    )
    for polygon in polygons(geometry):
        x, y = polygon.exterior.xy
        ax.plot(x, y, color="#244252", lw=0.35)
    ax.set(
        xlim=(west, east),
        ylim=(south, north),
        title=title,
        xlabel="Longitude (degrees)",
        ylabel="Latitude (degrees)",
    )
    ax.set_aspect(1 / np.cos(np.deg2rad((south + north) / 2)))
    return artist


# %%
# Continental Chile, including southern islands
# -----------------------------------------------
fig, axes = plt.subplots(1, 3, figsize=(13, 10), layout="constrained")
regions = [
    ((-73, -30, -66, -17.4), "Northern Chile"),
    ((-76, -42, -68, -30), "Central Chile"),
    ((-76, -56, -66, -42), "Southern Chile and Tierra del Fuego"),
]
for ax, (bounds, title) in zip(axes, regions, strict=True):
    artist = panel(ax, bounds, title)
fig.colorbar(
    artist, ax=axes, shrink=0.75, label="Thermal exposure relative to constant 25 °C", extend="max"
)
fig.suptitle("Chile · PVDeg thermal screening · native ~1 km climate grid", fontsize=16)

# %%
# Atacama and the Santiago-Rengo corridor
# ----------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(12, 8), layout="constrained")
panel(axes[0], (-71, -27, -67, -21), "Atacama: coastal-to-Andean gradient")
artist = panel(axes[1], (-72.3, -35.5, -69.5, -32.5), "Central Chile: Santiago and Rengo")
axes[1].plot(-70.86, -34.41, "o", color="cyan", markeredgecolor="black", ms=5)
axes[1].annotate("Rengo", (-70.86, -34.41), xytext=(6, 5), textcoords="offset points")
fig.colorbar(artist, ax=axes, label="Relative thermal exposure", extend="max")

# %%
# Compare scenario assumptions at six real source cells
# -------------------------------------------------------
sites = {
    "San Pedro": (-68.2, -22.9),
    "Atacama": (-69.5, -24.5),
    "Rengo": (-70.86, -34.41),
    "Temuco": (-72.6, -38.74),
    "Coyhaique": (-72.07, -45.57),
    "Tierra del Fuego": (-69, -53.5),
}
air = []
for record in manifest["months"]:
    with rasterio.open(record["file"]) as source:
        encoded = np.array([x[0] for x in source.sample(list(sites.values()))], dtype=float)
        encoded[encoded == source.nodata] = np.nan
        air.append(encoded * source.scales[0] + source.offsets[0] - 273.15)
air = np.stack(air)
fig, axes = plt.subplots(1, 2, figsize=(12, 5), layout="constrained")
for energy in (40, 60, 80):
    axes[0].plot(
        list(sites),
        thermal_stress_index(air + 20, MONTH_HOURS, activation_energy_kj_mol=energy),
        "o-",
        label=f"{energy} kJ/mol",
    )
for offset in (0, 20, 40):
    axes[1].plot(
        list(sites),
        thermal_stress_index(air + offset, MONTH_HOURS),
        "o-",
        label=f"Air + {offset} °C",
    )
for ax, title in zip(
    axes, ("Activation-energy sensitivity", "Module-temperature sensitivity"), strict=True
):
    ax.set(title=title, ylabel="Relative thermal exposure")
    ax.tick_params(axis="x", rotation=35)
    ax.legend()
    ax.grid(alpha=0.2)
plt.show()
