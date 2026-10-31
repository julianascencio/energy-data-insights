"""Continue the El Mirlo counting pilot using a pinned native Copernicus DSM crop."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from energy_analysis.module_counting.rengo import run_rengo_study
from energy_analysis.site_3d.pipeline import elevation_grid, footprints_from_count
from energy_data_retrieval.terrain import TerrainSource, read_terrain
from energy_methods.pv_site_3d import LocalSiteFrame, MountingParameters, build_pv_site_scene


def build_rengo_scene(
    counting_directory: str | Path, terrain_directory: str | Path
) -> dict[str, Any]:
    """Re-run the existing count; add declared terrain and mounting assumptions."""
    counting_directory, terrain_directory = Path(counting_directory), Path(terrain_directory)
    config = json.loads((terrain_directory / "scene_config.json").read_text())
    for name, checksum in config["sha256"].items():
        if hashlib.sha256((terrain_directory / name).read_bytes()).hexdigest() != checksum:
            raise ValueError(f"3D input checksum mismatch: {name}")
    if (
        hashlib.sha256((counting_directory / "rengo_study.json").read_bytes()).hexdigest()
        != config["counting_manifest_sha256"]
    ):
        raise ValueError("Counting study changed; review the 3D continuation")
    source = json.loads((terrain_directory / "terrain_provenance.json").read_text())
    spec = source["source"]
    descriptor = TerrainSource(
        spec["id"],
        spec["name"],
        spec["surface"],
        spec["vertical_datum"],
        tuple(spec["reference_ids"]),
    )
    window = read_terrain(terrain_directory / source["fixture"], descriptor)
    grid = elevation_grid(window)
    counting = run_rengo_study(counting_directory)
    bounds = tuple(counting["manifest"]["detail_capture"]["bbox"])
    lon, lat = (bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2
    centre_height = grid.sample([[lon, lat]])[0]
    if not np.isfinite(centre_height):
        raise ValueError("The scene origin has no terrain support")
    frame = LocalSiteFrame(lon, lat, float(np.floor(centre_height)))
    footprints = footprints_from_count(counting["advanced"], bounds)
    scene = build_pv_site_scene(
        footprints,
        grid,
        frame=frame,
        bounds_wgs84=bounds,
        mounting=MountingParameters(**config["mounting"]),
        display_grid_shape=tuple(config["display_grid_shape"]),
    )
    return {
        "scene": scene,
        "counting": counting,
        "terrain_window": window,
        "grid": grid,
        "terrain_source": source,
        "configuration": config,
    }
