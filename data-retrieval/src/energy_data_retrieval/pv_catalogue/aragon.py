"""Offline Aragón operating-PV discovery; GIS features are not canonical plants."""

from __future__ import annotations

import json
import math
from typing import Any

from .sam import verify_sha256

FIELDS = {"objectid", "nombre", "promotor", "potencia_placas_mwp", "potencia_inversior_mwp"}


def read_aragon_geojson(content: bytes, *, sha256: str) -> list[dict[str, Any]]:
    """Pin schema/IDs/ratings; retain ambiguous inverter MWp without AC inference."""
    verify_sha256(content, sha256)
    if len(content) > 20_000_000:
        raise ValueError("Aragón export exceeds reviewed size limit")
    document = json.loads(content)
    if not isinstance(document, dict) or document.get("type") != "FeatureCollection":
        raise ValueError("Aragón FeatureCollection required")
    features = document.get("features")
    if not isinstance(features, list):
        raise ValueError("Aragón features must be a list")
    seen = set()
    rows = []
    for feature in features:
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            raise ValueError("Invalid Aragón feature")
        row = feature.get("properties")
        if not isinstance(row, dict) or set(row) != FIELDS:
            raise ValueError("Aragón property schema changed")
        identifier = row["objectid"]
        if (
            isinstance(identifier, bool)
            or not isinstance(identifier, int)
            or identifier <= 0
            or identifier in seen
        ):
            raise ValueError("Invalid or duplicate Aragón GIS feature ID")
        seen.add(identifier)
        if not isinstance(row["nombre"], str) or not row["nombre"].strip():
            raise ValueError("Aragón name missing")
        for key in ("potencia_placas_mwp", "potencia_inversior_mwp"):
            value = row[key]
            if value is not None and (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value < 0
            ):
                raise ValueError("Invalid Aragón power assertion")
        geometry = feature.get("geometry")
        if not isinstance(geometry, dict) or geometry.get("type") not in {
            "Polygon",
            "MultiPolygon",
        }:
            raise ValueError("Aragón polygon geometry required")
        rows.append(
            {
                "gis_feature_id": identifier,
                "source_name": row["nombre"].strip(),
                "panel_peak_mwp_as_reported": row["potencia_placas_mwp"],
                "inverter_power_mwp_as_reported": row["potencia_inversior_mwp"],
                "geometry_type": geometry["type"],
                "identity_status": "review_only_not_accepted",
                "coordinate_scope": (
                    "Projected-looking geometry; CRS not declared; no lat/lon or centroid inferred"
                ),
                "rating_scope": "Inverter field is labelled MWp; no AC capacity inferred",
                "identity_scope": (
                    "GIS feature ID is not a national plant ID; phases/aggregates require review"
                ),
            }
        )
    return rows
