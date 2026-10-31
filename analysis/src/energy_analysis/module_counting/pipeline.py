"""Verify the image receipt and geographic scope before running the grid counter."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.image as mpimg
import numpy as np
from numpy.typing import NDArray
from shapely import intersects_xy
from shapely.geometry import shape

from energy_methods.pv_module_counting import (
    ModuleCount,
    ModuleCountingConfig,
    count_regular_pv_modules,
)


@dataclass(frozen=True)
class ImageModuleStudy:
    """Exact input provenance, masked RGB image and unvalidated candidate inventory."""

    result: ModuleCount
    rgb: NDArray[Any]
    site_mask: NDArray[np.bool_]
    source_metadata: dict[str, Any]
    site_feature: dict[str, Any]
    bounds_wgs84: tuple[float, float, float, float]


def count_rendered_site(
    image_path: str | Path,
    site_feature: dict[str, Any],
    *,
    config: ModuleCountingConfig | None = None,
) -> ImageModuleStudy:
    """Count a bounded site in an Orbital PV WMS 1.1.1 EPSG:4326 PNG capture.

    The unchanged ``.png.meta.json`` receipt must match the image checksum.
    No native-resolution/capture-date assumption is made from output dimensions.
    The supplied polygon determines scope; this function does not identify plants.
    """
    path = Path(image_path)
    metadata = json.loads(path.with_suffix(path.suffix + ".meta.json").read_text())
    if hashlib.sha256(path.read_bytes()).hexdigest() != metadata["sha256"]:
        raise ValueError("Source image checksum mismatch")
    request = metadata.get("request", {})
    if (
        metadata.get("product_kind") != "rendered_display"
        or request.get("SRS") != "EPSG:4326"
        or request.get("VERSION") != "1.1.1"
    ):
        raise ValueError("Expected a rendered WMS 1.1.1 EPSG:4326 image receipt")
    west, south, east, north = map(float, metadata["bbox_wgs84"])
    if not np.isfinite([west, south, east, north]).all() or not (
        -180 <= west < east <= 180 and -90 <= south < north <= 90
    ):
        raise ValueError("Invalid image geographic bounds")
    if [float(v) for v in request["BBOX"].split(",")] != [west, south, east, north]:
        raise ValueError("Image bounds disagree with the original request")
    rgb = mpimg.imread(path)
    if rgb.ndim != 3 or rgb.shape[2] not in (3, 4):
        raise ValueError("Expected an RGB/RGBA PNG")
    h, w = rgb.shape[:2]
    if (request["HEIGHT"], request["WIDTH"]) != (h, w):
        raise ValueError("Image dimensions disagree with the receipt")
    geometry = shape(site_feature["geometry"])
    if (
        geometry.geom_type not in ("Polygon", "MultiPolygon")
        or not geometry.is_valid
        or geometry.is_empty
    ):
        raise ValueError("Site scope must be a valid nonempty polygon")
    lon = west + (np.arange(w) + 0.5) / w * (east - west)
    lat = north - (np.arange(h) + 0.5) / h * (north - south)
    mask = intersects_xy(geometry, lon[None, :], lat[:, None])
    if rgb.shape[2] == 4:
        mask &= rgb[..., 3] == 1  # Partly transparent pixels have unknown colour.
    rgb = rgb[..., :3]
    result = count_regular_pv_modules(rgb, mask, config=config)
    return ImageModuleStudy(result, rgb, mask, metadata, site_feature, (west, south, east, north))
