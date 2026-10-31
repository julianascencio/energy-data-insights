"""
Native satellite imagery with Orbital PV
========================================

Read real, attributed crops through Orbital PV's checksum-verified loader.
The Tenerife example demonstrates 10 m Sentinel-2 site context, calibrated red
reflectance and the separate 20 m scene classification. The Altadena example
demonstrates sub-metre WorldView imagery from a disaster-response open archive.
It does not identify a PV installation or assess damage at that location.

The highest-detail selection is scoped to this area, event and date range.
No interpolation, sharpening or overview read creates finer native detail.
The coloured display product and panchromatic analytical band are distinct.

Install Python 3.13, this package and the pinned Orbital PV integration; see the
`satellite imagery guide <https://julianascencio.github.io/energy-data-insights/_generated/guides/satellite-imagery.html>`_.
Download :download:`the complete example and native crops <satellite_imagery_examples.zip>`.
All execution here is offline; the explicit live capture script is
``scripts/prepare_satellite_imagery_samples.py``.

Credits: Orbital PV, Element 84 Earth Search and Copernicus Sentinel data (2026).
WorldView samples © Maxar/Vantor, CC BY-NC 4.0; cropped without resampling.
The imagery licence is separate from the repository's code licence.
"""

import json
from dataclasses import asdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap

from energy_data_retrieval.sources.orbitalpv_imagery import (
    describe_asset,
    load_satellite_image,
)

DATA = (
    Path(globals().get("__file__", Path.cwd() / "plot_satellite_imagery.py")).resolve().parent
    / "data"
)
manifest = json.loads((DATA / "imagery_provenance.json").read_text())
images = {
    row["fixture"]: load_satellite_image(str(DATA / row["fixture"])) for row in manifest["samples"]
}


def draw(ax, image, values, title, **kwargs):
    """Display native pixel centres in projected metres, without smoothing."""
    left, bottom, right, top = image.bounds
    extent = (0, right - left, 0, top - bottom)
    artist = ax.imshow(values, extent=extent, origin="upper", interpolation="nearest", **kwargs)
    ax.set(title=title, xlabel="East from crop edge (m)", ylabel="North from crop edge (m)")
    ax.set_facecolor("#e9edf1")
    return artist


def rgb(image):
    values = np.moveaxis(image.data.filled(0), 0, -1).astype(float) / 255
    alpha = (~np.ma.getmaskarray(image.data).any(axis=0)).astype(float)
    return np.dstack((values, alpha))


# %%
# Site context, reflectance and local scene quality
# -------------------------------------------------
# A low scene-wide cloud percentage does not guarantee a cloud-free site.
# Inspect the SCL layer at its native 20 m spacing. The red reflectance uses the
# provider's explicit scale and offset; RGB display bytes are not reflectance.
visual = images["imagery_tenerife_visual.tif"]
red = images["imagery_tenerife_red.tif"]
scl = images["imagery_tenerife_scl.tif"]
fig_sentinel, axes = plt.subplots(1, 3, figsize=(14, 5.4), layout="constrained")
draw(axes[0], visual, rgb(visual), "Sentinel-2 RGB · 10 m")
artist = draw(
    axes[1],
    red,
    red.reflectance()[0],
    "Surface red reflectance · 10 m",
    cmap="magma",
    vmin=0,
    vmax=0.4,
)
fig_sentinel.colorbar(artist, ax=axes[1], shrink=0.75, label="Unitless reflectance")
scl_colors = [
    "#000000",
    "#ff0000",
    "#444444",
    "#885522",
    "#228833",
    "#ddbb66",
    "#2266dd",
    "#999999",
    "#bbbbbb",
    "#ffffff",
    "#66ccff",
    "#ff99cc",
]
artist = draw(
    axes[2],
    scl,
    scl.data[0],
    "Scene classification · 20 m",
    cmap=ListedColormap(scl_colors),
    norm=BoundaryNorm(np.arange(-0.5, 12.5), 12),
)
fig_sentinel.colorbar(artist, ax=axes[2], shrink=0.75, ticks=range(12), label="Native SCL class")
fig_sentinel.suptitle("Icor area, Tenerife · Sentinel-2 site context", fontsize=17, weight="bold")
fig_sentinel.text(
    0.02,
    -0.035,
    (
        "Contains modified Copernicus Sentinel data (2026), processed by ESA; "
        "Earth Search distribution. Native pixels, no cloud masking."
    ),
    fontsize=9,
)
print("Sentinel scene:", visual.scene_id)
print("Red band resolution and metadata:", asdict(describe_asset(red.item_metadata, "red")))
print(
    "SCL class counts:",
    dict(zip(*np.unique(scl.data.compressed(), return_counts=True), strict=True)),
)

# %%
# Sub-metre satellite imagery: native detail versus display spacing
# -----------------------------------------------------------------
# The panchromatic image has one broad spectral band. A percentile stretch below
# changes screen contrast only; the saved uint16 values stay untouched. The RGB
# image is the provider's 8-bit pansharpened display product. Its finer output
# grid is not an improvement in the sensor's native sampling.
pan = images["imagery_altadena_pan_analytic.tif"]
colour = images["imagery_altadena_visual.tif"]
pan_info = describe_asset(pan.item_metadata, "pan_analytic")
colour_info = describe_asset(colour.item_metadata, "visual")
low, high = np.percentile(pan.data.compressed(), [2, 98])
fig_worldview, axes = plt.subplots(1, 2, figsize=(11, 6.5), layout="constrained")
draw(
    axes[0],
    pan,
    pan.data[0],
    (
        f"Panchromatic · declared GSD {pan_info.native_gsd_m:.2f} m\n"
        f"Native raster spacing {pan.transform[0]:.3f} m"
    ),
    cmap="gray",
    vmin=low,
    vmax=high,
)
draw(
    axes[1],
    colour,
    rgb(colour),
    (
        f"Provider pansharpened RGB\nDisplay grid {colour.transform[0]:.3f} m; "
        f"detail bound {colour_info.detail_limit_m:.2f} m"
    ),
)
fig_worldview.suptitle("Altadena · WorldView-3 · 8 January 2025", fontsize=17, weight="bold")
fig_worldview.text(
    0.02,
    -0.025,
    (
        "© Maxar/Vantor Open Data Program · CC BY-NC 4.0 · Event-limited coverage. "
        "Native crops; pan contrast stretched for display only."
    ),
    fontsize=9,
)
print("WorldView scene:", pan.scene_id)
print("Acquisition and licence provenance:", pan.item_metadata["properties"]["edi:open_data"])
print("Panchromatic resolution:", asdict(pan_info))
print("RGB display resolution:", asdict(colour_info))

# %%
# What to do with the result
# --------------------------
# Retain the TIFF and its ``.meta.json`` together. Use native georeferencing for
# overlays with surveyed PV footprints and the terrain connector; reproject
# explicitly when combining different grids. Inspect nodata, clouds, shadows,
# capture dates and positional uncertainty before tracing site features.
# Fine imagery supports visual interpretation of roofs, roads and array rows
# where visible. It does not by itself establish installed capacity, measured
# generation or degradation. Use PVGIS for resource/modelled yield and dated
# meter observations for performance; keep image-derived hypotheses separate.
plt.show()
