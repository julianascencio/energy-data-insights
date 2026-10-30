"""Plot class rasters with bounded display reads and explicit missing-data colors."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import rasterio
from matplotlib.axes import Axes
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.image import AxesImage
from rasterio.enums import Resampling
from rasterio.windows import Window, from_bounds

COLORS = (
    "#27864a",
    "#a9cf55",
    "#d97927",
    "#edbd57",
    "#b44a42",
    "#ec9c85",
    "#265a90",
    "#5399be",
    "#89c9cf",
    "#79559d",
    "#b399c6",
    "#c8d0d7",
)
OCEAN_COLOR = "#eef5fa"
MISSING_COLOR = "#535d66"


def plot_tile(
    path: Path,
    ax: Axes,
    *,
    bounds: tuple[float, float, float, float] | None = None,
    maximum_display_pixels: int = 2_000_000,
    outline: bool = True,
) -> AxesImage:
    """Read only a bounded display view; original TIFF pixels remain unchanged.

    Native categorical values and display overviews use nearest-neighbour
    selection, never smoothing. The outline is the climate-input footprint,
    not a survey coastline. Gray identifies land lacking a complete input set.
    """
    if type(maximum_display_pixels) is not int or maximum_display_pixels < 1:
        raise ValueError("maximum_display_pixels must be a positive integer")
    with rasterio.open(path) as source:
        full = Window.from_slices((0, source.height), (0, source.width))
        if bounds is None:
            window = full
        else:
            if not np.isfinite(bounds).all() or bounds[0] >= bounds[2] or bounds[1] >= bounds[3]:
                raise ValueError("bounds must be west,south,east,north")
            requested = from_bounds(*bounds, transform=source.transform)
            window = requested.round_offsets().round_lengths().intersection(full)
        factor = max(1, math.sqrt(window.width * window.height / maximum_display_pixels))
        height = max(1, int(window.height / factor))
        width = max(1, int(window.width / factor))
        data = source.read(
            (1, 2), window=window, out_shape=(2, height, width), resampling=Resampling.nearest
        )
        west, south, east, north = source.window_bounds(window)
    classes, land = data
    display = np.where((land == 1) & (classes == 0), 13, classes)
    display = np.ma.masked_where(land != 1, display)
    cmap = ListedColormap([OCEAN_COLOR, *COLORS, MISSING_COLOR])
    norm = BoundaryNorm(np.arange(-0.5, 14.5), cmap.N)
    extent = (west, east, south, north)
    image = ax.imshow(
        display,
        origin="upper",
        extent=extent,
        cmap=cmap,
        norm=norm,
        interpolation="nearest",
        rasterized=True,
    )
    if outline and land.any() and not land.all() and min(land.shape) > 1:
        ax.contour(
            land, levels=[0.5], colors=["#445c6a"], linewidths=0.35, origin="upper", extent=extent
        )
    ax.set_facecolor(OCEAN_COLOR)
    ax.set_aspect(1 / np.cos(np.deg2rad((south + north) / 2)))
    ax.set(xlabel="Longitude (°)", ylabel="Latitude (°)")
    ax.grid(alpha=0.13, linewidth=0.5)
    return image
