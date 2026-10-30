"""Offline reference maps with native points, explicit coverage and separate legends."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap, to_hex, to_rgb
from matplotlib.patches import Patch
from shapely import intersects_xy
from shapely.geometry import shape

from energy_analysis.canary_kgpv.plotting import COLORS as KGPV_COLORS
from energy_analysis.climate_comparison.prepare import digest
from energy_data_retrieval.sources.jrc_climate.client import read_catalogue as read_jrc
from energy_data_retrieval.sources.ml21.client import read_catalogue as read_ml21
from energy_data_retrieval.sources.pvcz.client import read_catalogue as read_pvcz
from energy_methods.climate_zones import ClimateClusterModel
from energy_methods.country_boundaries import load_country_boundaries, polygons
from energy_methods.kgpv import ZONE_CODES as KGPV_CODES
from energy_methods.ml21 import PUBLISHED_CODES

REGIONS = {
    "world": (-180, -60, 180, 85),
    "chile": (-76.5, -56.5, -66, -17),
    "canary": (-18.5, 27.5, -13.4, 29.6),
}


def load_study(directory: Path, region: str) -> tuple[dict[str, pd.DataFrame], ClimateClusterModel]:
    """Verify this region's source subsets and frozen JRC model before plotting."""
    if region not in REGIONS:
        raise ValueError("Choose world, chile or canary")
    manifest = json.loads((directory / "climate_provenance.json").read_text())
    filenames = [f"climate_{source}_{region}.csv" for source in ("jrc", "ml21", "pvcz")]
    filenames.append("climate_jrc_model.json")
    for name in filenames:
        if digest(directory / name) != manifest["files"][name]:
            raise ValueError(f"Climate example checksum mismatch: {name}")
    for name, expected in manifest.get("context_files", {}).items():
        relevant = (
            (region == "world" and name.startswith("climate_world"))
            or (region == "chile" and name.startswith("kgpv_chile"))
            or (region == "canary" and name.startswith("kgpv_canary"))
        )
        if relevant and digest(directory / name) != expected:
            raise ValueError(f"Climate context checksum mismatch: {name}")
    frames = {
        name: reader(directory / f"climate_{name}_{region}.csv")
        for name, reader in (("jrc", read_jrc), ("ml21", read_ml21), ("pvcz", read_pvcz))
    }
    model = ClimateClusterModel.from_dict(
        json.loads((directory / "climate_jrc_model.json").read_text())
    )
    ids = model.predict(frames["jrc"][["G", "Tw"]].to_numpy()).class_id
    if not np.array_equal(ids, frames["jrc"].jrc_class.to_numpy()):
        raise ValueError("Stored JRC labels differ from frozen model predictions")
    return frames, model


def _pvcz_colors() -> np.ndarray:
    # Thermal hue follows cool to warm; increasing humidity raises saturation.
    hues = plt.get_cmap("coolwarm")(np.linspace(0.05, 0.95, 10))[:, :3]
    return np.concatenate([1 - (1 - hues) * saturation for saturation in np.linspace(0.35, 1, 5)])


def plot_comparison(directory: Path, region: str = "world") -> plt.Figure:
    """Four independent schemes; point colors are not interchangeable across panels.

    Chile includes only sample centers within the existing contiguous-mainland
    polygon. Display markers do not represent fine-resolution climate pixels.
    Canary outlines are reduced existing climate-raster footprints, not surveys.
    """
    frames, model = load_study(directory, region)
    boundary = None
    if region == "chile":
        boundary = load_country_boundaries(
            directory / "kgpv_chile_mainland.geojson", "CHL"
        ).geometry
        frames = {
            name: frame.loc[intersects_xy(boundary, frame.lon, frame.lat)].copy()
            for name, frame in frames.items()
        }
    jrc_colors = plt.get_cmap("turbo")(np.linspace(0.05, 0.95, len(model.codes) - 1))
    family_colors = {
        "Tro": "#159455",
        "Des": "#d46b1d",
        "Mou": "#8b5eb0",
        "Tem": "#b28a08",
        "Col": "#286cb0",
        "Pol": "#627580",
    }
    ml_colors = []
    for code in PUBLISHED_CODES[1:]:
        base = np.array(to_rgb(family_colors[code[:3]]))
        ml_colors.append(1 - (1 - base) * (0.40 + int(code[-1]) * 0.12))
    pvc_colors = _pvcz_colors()
    specs = [
        (
            "KGPV · published reference",
            frames["ml21"],
            "kgpv_zone",
            KGPV_CODES[1:],
            KGPV_COLORS,
            "Original labels carried in the ML21 workbook",
        ),
        (
            "JRC · documented refit",
            frames["jrc"],
            "jrc_class",
            tuple(range(1, len(model.codes))),
            jrc_colors,
            "2005-2023 · native 0.1° · fixed global centroids",
        ),
        (
            "ML21 · published reference",
            frames["ml21"],
            "ml21_zone",
            PUBLISHED_CODES[1:],
            ml_colors,
            "Mixed source climatologies · native 0.5°",
        ),
        (
            "PVCZ · published reference",
            frames["pvcz"],
            "pvcz_labeled",
            tuple(f"T{t}:H{h}" for h in range(1, 6) for t in range(1, 11)),
            pvc_colors,
            "2010-2018 · native 0.25° · rounded CSV coordinates",
        ),
    ]
    fig = plt.figure(figsize=(15, 13) if region != "chile" else (14, 13), layout="constrained")
    grid = fig.add_gridspec(2, 2) if region != "chile" else fig.add_gridspec(1, 4)
    for index, (title, frame, column, codes, colors, caption) in enumerate(specs):
        cell = grid[index // 2, index % 2] if region != "chile" else grid[0, index]
        inner = cell.subgridspec(2, 1, height_ratios=[4.5, 1.9] if region != "chile" else [8, 3])
        ax, legend_ax = fig.add_subplot(inner[0]), fig.add_subplot(inner[1])
        ax.set_facecolor("#f4f7f9")
        if region == "world":
            document = json.loads((directory / "climate_world_boundaries.geojson").read_text())
            for feature in document["features"]:
                for part in polygons(shape(feature["geometry"])):
                    xy = np.asarray(part.exterior.coords)
                    ax.plot(xy[:, 0], xy[:, 1], color="#b1bdc4", linewidth=0.25, zorder=1)
        elif boundary is not None:
            for part in polygons(boundary):
                for ring in (part.exterior, *part.interiors):
                    xy = np.asarray(ring.coords)
                    ax.plot(xy[:, 0], xy[:, 1], color="#71818b", linewidth=0.5)
        else:
            _canary_outline(directory, ax)
        ids = frame[column].map({code: i for i, code in enumerate(codes)})
        good = ids.notna()
        ax.scatter(
            frame.loc[good, "lon"],
            frame.loc[good, "lat"],
            c=ids[good],
            cmap=ListedColormap(colors),
            vmin=-0.5,
            vmax=len(codes) - 0.5,
            s=3 if region == "world" else 7 if region == "chile" else 28,
            marker="s" if region == "world" else "o",
            linewidths=0,
            zorder=2,
        )
        if not good.any():
            ax.text(
                0.5,
                0.5,
                "No source observations\nin this region",
                transform=ax.transAxes,
                ha="center",
                va="center",
                color="#4c6170",
                fontsize=13,
            )
        west, south, east, north = REGIONS[region]
        ax.set(
            xlim=(west, east), ylim=(south, north), xlabel="Longitude (°)", ylabel="Latitude (°)"
        )
        if region != "world":
            ax.set_aspect(1 / np.cos(np.deg2rad((south + north) / 2)))
        ax.set_title(
            f"{title}\n{int(good.sum()):,} displayed source points", fontsize=11, loc="left"
        )
        ax.grid(alpha=0.15)
        legend_ax.axis("off")
        if index == 3:
            key = legend_ax.inset_axes((0.1, 0.26, 0.8, 0.48))
            key.imshow(
                np.arange(50).reshape(5, 10),
                cmap=ListedColormap(pvc_colors),
                origin="lower",
                vmin=-0.5,
                vmax=49.5,
                aspect="auto",
            )
            key.set(
                xticks=np.arange(10),
                xticklabels=[f"T{i}" for i in range(1, 11)],
                yticks=np.arange(5),
                yticklabels=[f"H{i}" for i in range(1, 6)],
            )
            key.tick_params(labelsize=6 if region == "chile" else 8, length=0)
        else:
            labels = model.codes[1:] if index == 1 else codes
            legend_ax.legend(
                [
                    Patch(
                        facecolor=to_hex(
                            color
                            if isinstance(color, str)
                            else (float(color[0]), float(color[1]), float(color[2]))
                        )
                    )
                    for color in colors
                ],
                [str(label) for label in labels],
                loc="center",
                ncol=2 if region == "chile" else 5 if index == 1 else 4,
                frameon=False,
                fontsize=8,
                handlelength=1,
                columnspacing=0.7,
            )
        legend_ax.text(
            0.5,
            0.02,
            caption.replace(" · ", "\n") if region == "chile" else caption,
            transform=legend_ax.transAxes,
            ha="center",
            va="bottom",
            fontsize=8,
        )
    title_region = {
        "world": "Global reference samples",
        "chile": "Contiguous mainland Chile",
        "canary": "Canary Islands: coarse-source coverage",
    }[region]
    fig.suptitle(
        f"Four views of PV climate | {title_region}\n"
        "Different source periods and objectives; no cross-scheme accuracy ranking",
        fontsize=16,
    )
    return fig


def _canary_outline(directory: Path, ax: plt.Axes) -> None:
    import rasterio
    from rasterio.enums import Resampling

    for path in sorted(directory.glob("kgpv_canary_*.tif")):
        with rasterio.open(path) as source:
            land = source.read(2, out_shape=(250, 250), resampling=Resampling.nearest)
            west, south, east, north = source.bounds
        if land.any() and not land.all():
            ax.contour(
                land,
                levels=[0.5],
                colors=["#9caab3"],
                linewidths=0.5,
                origin="upper",
                extent=(west, east, south, north),
            )
