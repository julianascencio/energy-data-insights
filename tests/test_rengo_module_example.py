"""Offline evidence integrity and evaluation contracts, not field-accuracy claims."""

import copy
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from energy_analysis.module_counting.rengo import (
    evaluate_centres,
    export_rengo_study,
    run_rengo_study,
)

DATA = Path(__file__).resolve().parents[1] / "examples/analysis/data/rengo_modules"


def annotation():
    return {
        "matching_radius_pixels": 1.1,
        "regions": [
            {"id": "panels", "bounds_xyxy": [0, 0, 10, 10], "centres_xy": [[2, 2], [4, 2]]},
            {"id": "soil", "bounds_xyxy": [10, 0, 20, 10], "centres_xy": []},
        ],
    }


def test_matching_is_one_to_one_and_includes_false_positives_and_negatives():
    predicted = [[2, 2], [2.1, 2], [4.8, 2], [15, 5], [30, 30]]
    result = evaluate_centres(predicted, annotation())["total"]
    assert result == {
        "reference": 2,
        "predicted": 4,
        "matched": 2,
        "false_positives": 2,
        "missed": 0,
        "precision": 0.5,
        "recall": 1,
    }
    empty = evaluate_centres([], annotation())["total"]
    assert empty["precision"] is None and empty["recall"] == 0
    assert empty["missed"] == 2
    # Both are matchable only when the shared nearest reference is not assigned greedily.
    result = evaluate_centres([[3, 2], [1.5, 2]], annotation())["total"]
    assert result["matched"] == 2


def test_annotation_contract_rejects_overlap_duplicates_and_bad_coordinates():
    for change in ("overlap", "outside", "duplicate", "nonfinite", "radius", "id"):
        a = copy.deepcopy(annotation())
        if change == "overlap":
            a["regions"][1]["bounds_xyxy"] = [5, 0, 15, 10]
        if change == "outside":
            a["regions"][0]["centres_xy"] = [[20, 2]]
        if change == "duplicate":
            a["regions"][0]["centres_xy"] = [[2, 2], [2, 2]]
        if change == "nonfinite":
            a["regions"][0]["centres_xy"] = [[np.nan, 2]]
        if change == "radius":
            a["matching_radius_pixels"] = 0
        if change == "id":
            a["regions"][1]["id"] = "panels"
        with pytest.raises(ValueError):
            evaluate_centres([], a)


def test_pinned_pilot_keeps_scope_and_visual_audit_limits(tmp_path):
    study = run_rengo_study(DATA)
    assert study["advanced"].estimated_modules == 2055
    assert study["baseline"].estimated_modules is None
    assert study["manifest"]["whole_plant_image_count"] is None
    audit = study["audits"]["orientation_lattice"]["total"]
    assert audit["reference"] == 72 and audit["matched"] == 51
    assert audit["missed"] == 21 and audit["false_positives"] == 0
    assert "not blinded or held-out" in study["annotations"]["protocol"]
    assert study["advanced"].config.source_pixel_ratio > 1
    assert study["advanced"].rejected_tables
    exports = export_rengo_study(DATA, tmp_path / "export")
    summary = json.loads((exports / "audit.json").read_text())
    assert summary["whole_plant_image_count"] is None
    frame = pd.read_csv(exports / "lattice_candidates.csv")
    assert frame.status.eq("regular_candidate").sum() == summary["image_candidate_count"]
    assert frame.status.eq("excluded").any()
    geo = json.loads((exports / "lattice_candidates.geojson").read_text())
    assert len(geo["features"]) == len(frame)
    first = study["advanced"].cells[0]
    w, s, e, n = study["manifest"]["detail_capture"]["bbox"]
    x, y = first.vertices_xy[0]
    assert geo["features"][0]["geometry"]["coordinates"][0][0] == pytest.approx(
        [w + (x + 0.5) / 900 * (e - w), n - (y + 0.5) / 600 * (n - s)]
    )
    with pytest.raises(FileExistsError):
        export_rengo_study(DATA, exports)


def test_modified_annotation_is_rejected_before_counting(tmp_path):
    shutil.copytree(DATA, tmp_path / "inputs")
    (tmp_path / "inputs/visual_annotations.json").write_text("{}")
    with pytest.raises(ValueError, match="checksum"):
        run_rengo_study(tmp_path / "inputs")
