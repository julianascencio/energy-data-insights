"""Offline El Mirlo pilot with a transparent, small visual-annotation audit."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import matplotlib.image as mpimg
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist
from shapely import intersects_xy
from shapely.geometry import Polygon, box

from energy_analysis.module_counting.chile import verified_file
from energy_methods.pv_lattice_counting import LatticeCountingConfig, count_lattice_pv_modules
from energy_methods.pv_module_counting import count_regular_pv_modules


def evaluate_centres(predicted: Any, annotations: dict[str, Any]) -> dict[str, Any]:
    """One-to-one centre matches inside each labelled region, including negatives.

    Maximise the number of pairs within the fixed radius before minimising their
    distances. Region membership uses half-open pixel bounds. No estimates outside
    those regions contribute to these local diagnostic precision/recall values.
    """
    points = np.asarray(predicted, dtype=float).reshape(-1, 2)
    radius = annotations["matching_radius_pixels"]
    if not np.isfinite(points).all() or not np.isfinite(radius) or radius <= 0:
        raise ValueError("Centres and positive matching radius must be finite")
    summaries: list[dict[str, Any]] = []
    shapes = []
    identifiers = set()
    for region in annotations["regions"]:
        if region["id"] in identifiers:
            raise ValueError("Annotation region IDs must be unique")
        identifiers.add(region["id"])
        bounds = np.asarray(region["bounds_xyxy"], dtype=float)
        if bounds.shape != (4,) or not np.isfinite(bounds).all():
            raise ValueError("Invalid annotation bounds")
        x0, y0, x1, y1 = bounds
        if x0 >= x1 or y0 >= y1:
            raise ValueError("Annotation bounds must have positive area")
        geometry = box(x0, y0, x1, y1)
        if any(geometry.intersection(other).area > 0 for other in shapes):
            raise ValueError("Annotation regions must not overlap")
        shapes.append(geometry)
        truth = np.asarray(region["centres_xy"], dtype=float).reshape(-1, 2)
        if not np.isfinite(truth).all() or len(np.unique(truth, axis=0)) != len(truth):
            raise ValueError("Annotation centres must be finite and unique")

        def within(array: Any, region_bounds: Any = bounds) -> Any:
            x0, y0, x1, y1 = region_bounds
            return (
                (array[:, 0] >= x0) & (array[:, 0] < x1) & (array[:, 1] >= y0) & (array[:, 1] < y1)
            )

        if not within(truth).all():
            raise ValueError("Annotation centre outside its region")
        selected = points[within(points)]
        matched = 0
        distances = []
        if len(selected) and len(truth):
            distance = cdist(selected, truth)
            cost = np.where(distance <= radius, distance / (radius * (min(distance.shape) + 1)), 1)
            rows, cols = linear_sum_assignment(cost)
            distances = distance[rows, cols][distance[rows, cols] <= radius].tolist()
            matched = len(distances)
        summaries.append(
            {
                "region": region["id"],
                "reference": len(truth),
                "predicted": len(selected),
                "matched": matched,
                "false_positives": len(selected) - matched,
                "missed": len(truth) - matched,
                "matched_distances_pixels": distances,
            }
        )
    totals: dict[str, Any] = {
        key: sum(s[key] for s in summaries)
        for key in ("reference", "predicted", "matched", "false_positives", "missed")
    }
    totals["precision"] = totals["matched"] / totals["predicted"] if totals["predicted"] else None
    totals["recall"] = totals["matched"] / totals["reference"] if totals["reference"] else None
    return {"matching_radius_pixels": radius, "regions": summaries, "total": totals}


def run_rengo_study(directory: str | Path) -> dict[str, Any]:
    """Run the frozen counter configurations on hash-pinned imagery and annotations."""
    directory = Path(directory)
    manifest = json.loads((directory / "rengo_study.json").read_text())
    for name in manifest["sha256"]:
        verified_file(directory, name, manifest["sha256"])
    capture = manifest["detail_capture"]
    rgb = mpimg.imread(directory / capture["filename"])[..., :3]
    h, w = rgb.shape[:2]
    if [w, h] != capture["size"]:
        raise ValueError("Image dimensions disagree with the capture")
    west, south, east, north = capture["bbox"]
    if not np.isclose((east - west) / (north - south), w / h):
        raise ValueError("Ambiguous ArcGIS export extent")
    polygon = Polygon(capture["scope_pixel_polygon"])
    if not polygon.is_valid or polygon.area <= 0:
        raise ValueError("Invalid inspection scope")
    mask = intersects_xy(polygon, np.arange(w)[None, :], np.arange(h)[:, None])
    annotations = json.loads((directory / manifest["annotation_fixture"]).read_text())
    config = LatticeCountingConfig(**manifest["parameters"])
    advanced = count_lattice_pv_modules(rgb, mask, config=config)
    baseline = count_regular_pv_modules(rgb, mask)
    audits = {}
    for name, result in (("original_defaults", baseline), ("orientation_lattice", advanced)):
        frame = result.to_frame()
        xy = frame.loc[frame.status.ne("excluded"), ["x_pixel", "y_pixel"]].to_numpy()
        audits[name] = evaluate_centres(xy, annotations)
    return {
        "manifest": manifest,
        "rgb": rgb,
        "mask": mask,
        "annotations": annotations,
        "advanced": advanced,
        "baseline": baseline,
        "audits": audits,
    }


def export_rengo_study(directory: str | Path, destination: str | Path) -> Path:
    """Export candidate geometry, all exclusions and the scoped visual comparison."""
    study = run_rengo_study(directory)
    result = study["advanced"]
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    result.to_frame().to_csv(destination / "lattice_candidates.csv", index=False)
    study["baseline"].to_frame().to_csv(destination / "original_candidates.csv", index=False)
    west, south, east, north = study["manifest"]["detail_capture"]["bbox"]
    h, w = result.image_shape
    features = []
    for cell in result.cells:
        ring = [
            [west + (x + 0.5) / w * (east - west), north - (y + 0.5) / h * (north - south)]
            for x, y in cell.vertices_xy
        ]
        features.append(
            {
                "type": "Feature",
                "id": cell.id,
                "geometry": {"type": "Polygon", "coordinates": [[*ring, ring[0]]]},
                "properties": {"status": cell.status, "reasons": list(cell.reasons)},
            }
        )
    (destination / "lattice_candidates.geojson").write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": features,
                "properties": {
                    "interpretation": (
                        "Image candidates in a partial inspection block; not surveyed modules"
                    )
                },
            },
            allow_nan=False,
        )
        + "\n"
    )
    summary = {
        "site": study["manifest"]["site"],
        "image_candidate_count": result.estimated_modules,
        "original_default_candidate_count": study["baseline"].estimated_modules,
        "whole_plant_image_count": None,
        "audit_interpretation": study["annotations"]["protocol"],
        "annotations": study["annotations"],
        "audits": study["audits"],
        "tables": [asdict(t) for t in result.tables],
        "rejected_tables": list(result.rejected_tables),
        "manifest": study["manifest"],
    }
    (destination / "audit.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    return destination
