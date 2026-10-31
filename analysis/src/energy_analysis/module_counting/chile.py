"""Reproducible Chilean site selection and explicitly qualified image-count attempts.

Registry maximum power, DC nameplate capacity, reported inventories and image
candidates are different measurements. None silently substitutes for another.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib.image as mpimg
import numpy as np
import pandas as pd
from pyproj import Geod
from shapely import intersects_xy
from shapely.geometry import shape

from energy_methods.pv_module_counting import ModuleCountingConfig, count_regular_pv_modules


def rank_operating_solar_sites(registry: pd.DataFrame) -> pd.DataFrame:
    """Rank positive CEN ``potencia_maxima`` values, retaining ties and unknown coordinates.

    The scope is CEN's operating ``Solares`` category (including solar thermal),
    not all private installations or a national ranking by DC module capacity.
    The two selected extrema are independently confirmed to be photovoltaic.
    """
    required = {"id", "nombre", "tipo_central_nombre", "estado", "potencia_maxima"}
    if not required.issubset(registry.columns):
        raise ValueError("Missing CEN registry columns")
    if registry.id.isna().any() or registry.id.duplicated().any():
        raise ValueError("Registry site IDs must be unique and non-null")
    power = pd.to_numeric(registry.potencia_maxima, errors="coerce")
    selected = registry.loc[
        registry.tipo_central_nombre.eq("Solares")
        & registry.estado.eq("EN_OPERACION")
        & np.isfinite(power)
        & power.gt(0)
    ].copy()
    selected["potencia_maxima"] = power.loc[selected.index]
    return selected.sort_values(["potencia_maxima", "id"]).reset_index(drop=True)


def verified_file(directory: Path, filename: str, checksums: dict[str, str]) -> Path:
    """Resolve a local fixture only after checking its pinned SHA-256."""
    path = directory / filename
    if hashlib.sha256(path.read_bytes()).hexdigest() != checksums[filename]:
        raise ValueError(f"Fixture checksum mismatch: {filename}")
    return path


def load_chile_study(directory: str | Path) -> tuple[dict[str, Any], pd.DataFrame]:
    """Load the dated selection manifest and hash-verified full registry projection."""
    directory = Path(directory)
    manifest = json.loads((directory / "chile_module_study.json").read_text())
    registry = pd.read_csv(
        verified_file(directory, manifest["registry_fixture"], manifest["sha256"])
    )
    ranking = rank_operating_solar_sites(registry)
    if len(ranking) != manifest["eligible_sites"]:
        raise ValueError("Registry selection changed; review the study")
    for key, edge in (("concon", ranking.iloc[0]), ("ceme1", ranking.iloc[-1])):
        if int(edge.id) != manifest["sites"][key]["registry_id"]:
            raise ValueError("Registry extrema changed; review site selection")
    return manifest, ranking


def audit_site_image(directory: str | Path, key: str) -> dict[str, Any]:
    """Attempt the Icor counter on a bounded, attributed Chilean static map.

    A source sampling gate prevents coarse basemap cells being called modules.
    No resampling, sharpening, extrapolation or use of reference inventory in
    detection occurs. Unresolved attempts retain ``None``, never zero.
    """
    directory = Path(directory)
    manifest, _ = load_chile_study(directory)
    site = manifest["sites"][key]
    capture = site["detail_capture"]
    path = verified_file(directory, capture["filename"], manifest["sha256"])
    rgb = mpimg.imread(path)[..., :3]
    west, south, east, north = capture["bbox_wgs84"]
    h, w = rgb.shape[:2]
    if (w, h) != tuple(capture["size"]):
        raise ValueError("Image dimensions disagree with the capture")
    # ArcGIS f=image can expand the bounding box to match the requested aspect.
    # These fixtures deliberately request matching degree/pixel aspect ratios.
    if not np.isclose((east - west) / (north - south), w / h, rtol=1e-8):
        raise ValueError("Ambiguous ArcGIS export extent; use a matching aspect ratio")
    geometry = shape(capture["scope"]["geometry"])
    if geometry.geom_type not in ("Polygon", "MultiPolygon") or not geometry.is_valid:
        raise ValueError("Image scope must be a valid polygon")
    x = west + (np.arange(w) + 0.5) * (east - west) / w
    y = north - (np.arange(h) + 0.5) * (north - south) / h
    mask = intersects_xy(geometry, x[None, :], y[:, None])
    if not mask.any():
        raise ValueError("Image does not intersect the supplied scope")
    geod = Geod(ellps="WGS84")
    sampling = max(
        geod.inv(west, (south + north) / 2, east, (south + north) / 2)[2] / w,
        geod.inv((west + east) / 2, south, (west + east) / 2, north)[2] / h,
        capture["service_sampling_m"],
        capture["source_resolution_m"],
    )
    config = ModuleCountingConfig(**site["counter_parameters"])
    shortest_side = site.get("documented_module_short_side_m")
    result = None
    if shortest_side is not None and shortest_side / sampling < config.minimum_pitch_pixels:
        status = "insufficient_source_sampling"
    else:
        result = count_regular_pv_modules(rgb, mask, config=config)
        status = "unresolved_grid" if result.estimated_modules is None else "unvalidated_candidates"
    return {
        "site": site["name"],
        "status": status,
        "image_candidate_count": None if result is None else result.estimated_modules,
        "whole_plant_image_count": None,
        "whole_plant_count_status": "not_established",
        "reported_inventory": site["reported_inventory"],
        "effective_sampling_m": sampling,
        "source": capture,
        "rejected_tables": [] if result is None else list(result.rejected_tables),
        "result": result,
        "rgb": rgb,
        "mask": mask,
    }


def export_chile_audit(directory: str | Path, destination: str | Path) -> Path:
    """Export both attempts without relabelling source inventories as image counts."""
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    manifest, ranking = load_chile_study(directory)
    ranking.to_csv(destination / "operating_solar_ranking.csv", index=False)
    summaries = []
    for key in ("ceme1", "concon"):
        attempt = audit_site_image(directory, key)
        result = attempt.pop("result")
        attempt.pop("rgb")
        attempt.pop("mask")
        if result is not None and result.cells:
            result.to_frame().to_csv(destination / f"{key}_image_candidates.csv", index=False)
        summaries.append(attempt)
    (destination / "count_audit.json").write_text(
        json.dumps({"study": manifest, "attempts": summaries}, indent=2, allow_nan=False) + "\n"
    )
    return destination
