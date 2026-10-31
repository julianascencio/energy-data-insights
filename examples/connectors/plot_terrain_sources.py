"""Native terrain: SRTM, Copernicus, IGN and USGS
===============================================

Inspect **real, attributed terrain crops**: SRTM and Copernicus at approximately
30 m, IGN's 5 m WCS in Tenerife, and a separate USGS 1 m lidar project in Colorado.
The gallery runs entirely offline and uses every native pixel in each crop.
These are different products and vertical references, not a terrain-change map.

Download :download:`the script, four GeoTIFF crops and provenance <terrain_examples.zip>`
together. See the :doc:`terrain connector guide <../../_generated/guides/terrain>`
for live acquisition, coverage checks and a complete site metadata lookup.
"""

# %%
# 1. Verify the captured bytes and inspect product metadata
# -----------------------------------------------------------------------------------------------
# The manifest records the upstream downloads and each derived crop. Pixel size
# is neither positional accuracy nor survey date. White cells mean missing data;
# zero metres is a valid height. Native vertical datums are never converted here.

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator, ScalarFormatter

from energy_data_retrieval.terrain import TerrainSource, describe_terrain, read_terrain

DATA = (
    Path(globals().get("__file__", Path.cwd() / "plot_terrain_sources.py")).resolve().parent
    / "data"
)
manifest = json.loads((DATA / "terrain_provenance.json").read_text())
windows = []
for sample in manifest["samples"]:
    path = DATA / sample["fixture"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == sample["fixture_sha256"]
    source = TerrainSource(
        **(sample["source"] | {"reference_ids": tuple(sample["source"]["reference_ids"])})
    )
    window = read_terrain(path, source)
    windows.append(window)
    metadata = describe_terrain(path, source)
    print(source.name)
    print(json.dumps(asdict(metadata), indent=2))
    print(f"Valid elevation cells: {np.isfinite(window.elevation_m).mean():.1%}\n")

# %%
# 2. Plot native elevation grids with explicit units and places
# -----------------------------------------------------------------------------------------------
# Each panel uses its own native axes and colour scale. The first three cover the
# same requested Tenerife site box with native enclosing cell edges. The fourth
# is a different place: Colorado. No interpolation is used for display, and no
# subtraction or blending across vertical references is performed.

titles = [
    "SRTMGL1 · 1 arcsecond (~30 m)",
    "Copernicus GLO-30 · ~30 m",
    "IGN MDT WCS · 5 m",
    "USGS 3DEP project · 1 m",
]
fig, axes = plt.subplots(2, 2, figsize=(13, 11), layout="constrained")
fig.suptitle("Terrain at its native sampling", fontsize=22, weight="bold")
for ax, window, sample, title in zip(axes.flat, windows, manifest["samples"], titles, strict=True):
    west, south, east, north = window.metadata.bounds
    geographic = window.metadata.horizontal_unit == "degree"
    divisor = 1 if geographic else 1000
    im = ax.imshow(
        window.elevation_m,
        origin="upper",
        interpolation="none",
        cmap="terrain",
        extent=(west / divisor, east / divisor, south / divisor, north / divisor),
        aspect=1 / np.cos(np.deg2rad(28.25)) if geographic else "equal",
    )
    datum = {
        "srtm": "EGM96",
        "copernicus_dem": "EGM2008",
        "ign_terrain": "local official heights",
        "usgs_3dep": "NAVD88 (CONUS)",
    }[window.metadata.source.id]
    ax.set_title(f"{title}\n{sample['place']} · {datum}", fontsize=12, loc="left", pad=10)
    ax.set_xlabel("Longitude (degrees)" if geographic else "Easting (km)")
    ax.set_ylabel("Latitude (degrees)" if geographic else "Northing (km)")
    for axis in (ax.xaxis, ax.yaxis):
        axis.set_major_locator(MaxNLocator(4))
        axis.set_major_formatter(ScalarFormatter(useOffset=False))
    fig.colorbar(im, ax=ax, shrink=0.78, label="Elevation (m)", pad=0.03)
fig.supxlabel(
    "Native pixels · independent colour scales · missing cells stay missing · "
    "vertical datums differ",
    fontsize=10,
)
plt.show()

# %%
# 3. Attach the terrain evidence to one site
# -----------------------------------------------------------------------------------------------
# This is the same latitude/longitude ordering used by the climate and PVGIS
# guides. A None result means no valid terrain height, not zero elevation. Keep
# product metadata and original request hashes alongside the site record.

site = {"latitude": 28.25, "longitude": -16.65}
site_record = {"site": site, "terrain": []}
for sample, window in zip(manifest["samples"][:3], windows[:3], strict=True):
    site_record["terrain"].append(
        {
            "elevation_m": window.sample(**site),
            "metadata": asdict(window.metadata),
            "source_request": sample["request"],
        }
    )
print(json.dumps(site_record, indent=2))

# %%
# 4. Use the result in an energy study
# -----------------------------------------------------------------------------------------------
# Check coordinates and valid terrain first. Choose DTM versus DSM deliberately,
# and obtain a wider surrounding area for horizon calculations. Project angular
# grids before computing metric slopes, and reconcile vertical references before
# comparing heights. This small crop does not resolve all PV shading obstacles.
# Terrain metadata can be joined with the single-site climate lookup; it does not
# supply climate classifications or an observed module degradation rate.
#
# Sources and exact notices are retained in the bundled provenance. Copernicus:
# produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence
# and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA;
# all rights reserved. IGN: geographic information from IGN Spain, CC BY 4.0.
# SRTM: NASA/USGS, via ESA SNAP. USGS 3DEP: public domain.
