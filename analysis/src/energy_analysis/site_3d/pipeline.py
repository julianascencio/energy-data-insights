"""Adapters from attributed terrain and image/GeoJSON candidates into 3D methods."""

from __future__ import annotations

from typing import Any

import numpy as np

from energy_data_retrieval.terrain import TerrainWindow, validate_bounds
from energy_methods.pv_lattice_counting import LatticeCount
from energy_methods.pv_module_counting import ModuleCount
from energy_methods.pv_site_3d import ElevationGrid, ModuleFootprint


def elevation_grid(window: TerrainWindow) -> ElevationGrid:
    """Preserve decoded heights, exact native transform, CRS and vertical datum."""
    t = window.transform
    return ElevationGrid(
        window.elevation_m,
        (t.a, t.b, t.c, t.d, t.e, t.f),
        window.metadata.crs,
        window.metadata.source.vertical_datum,
    )


def footprints_from_count(
    result: ModuleCount | LatticeCount,
    bounds_wgs84: tuple[float, float, float, float],
    *,
    include_review: bool = True,
) -> tuple[ModuleFootprint, ...]:
    """Georeference accepted image quadrilaterals with the half-pixel convention.

    Review candidates can be explicitly omitted. Excluded cells are never lifted.
    Table IDs remain attached, ensuring shared planes across adjacent modules.
    Bounds must describe the original north-up EPSG:4326 image's outer edges.
    """
    validate_bounds(bounds_wgs84)
    west, south, east, north = bounds_wgs84
    h, w = result.image_shape
    footprints = []
    for cell in result.cells:
        if cell.status == "excluded" or (cell.status == "review_candidate" and not include_review):
            continue
        ll = np.array(
            [
                [west + (x + 0.5) / w * (east - west), north - (y + 0.5) / h * (north - south)]
                for x, y in cell.vertices_xy
            ]
        )
        footprints.append(ModuleFootprint(cell.id, str(cell.table), ll))
    return tuple(footprints)


def footprints_from_geojson(
    collection: dict[str, Any],
    *,
    table_property: str = "table",
) -> tuple[ModuleFootprint, ...]:
    """Read explicitly identified quadrilateral Polygon features in WGS84.

    A feature must have an ID and a table property. Holes, multipolygons and
    altitude coordinates fail explicitly. Features marked ``excluded`` are
    omitted. A table polygon is not automatically divided into modules.
    """
    if collection.get("type") != "FeatureCollection":
        raise ValueError("Require a GeoJSON FeatureCollection")
    footprints = []
    for feature in collection["features"]:
        properties = feature.get("properties") or {}
        if properties.get("status") == "excluded":
            continue
        geometry = feature["geometry"]
        if geometry.get("type") != "Polygon" or len(geometry["coordinates"]) != 1:
            raise ValueError("Require Polygon footprints without holes")
        ring = np.asarray(geometry["coordinates"][0], dtype=float)
        if ring.shape != (5, 2) or not np.array_equal(ring[0], ring[-1]):
            raise ValueError("Require a closed four-corner WGS84 ring without altitude")
        if feature.get("id") is None or properties.get(table_property) is None:
            raise ValueError("Every footprint needs a feature ID and table property")
        footprints.append(
            ModuleFootprint(str(feature["id"]), str(properties[table_property]), ring[:-1])
        )
    return tuple(footprints)
