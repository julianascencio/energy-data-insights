"""Offline continuation, georeferencing and portable export contracts."""

import json
import shutil
from pathlib import Path

import numpy as np
import pytest
from numpy.testing import assert_allclose

from energy_analysis.module_counting.rengo import export_rengo_study
from energy_analysis.site_3d import (
    export_site_scene,
    footprints_from_count,
    footprints_from_geojson,
)
from energy_analysis.site_3d.rengo import build_rengo_scene
from energy_methods.pv_site_3d import build_pv_site_scene

DATA = Path(__file__).resolve().parents[2] / "examples/analysis/data"


@pytest.fixture(scope="module")
def study():
    return build_rengo_scene(DATA / "rengo_modules", DATA / "rengo_3d")


def test_rengo_continuation_retains_scope_and_records_assumptions(study):
    scene = study["scene"]
    assert len(scene.modules) == scene.input_module_count == 2055
    assert len({m.table_id for m in scene.modules}) == 22
    assert not scene.rejected_modules
    assert scene.vertical_datum == "EGM2008"
    assert scene.frame.elevation_origin_m == 282
    assert study["terrain_window"].elevation_m.shape == (48, 47)
    assert study["counting"]["audits"]["orientation_lattice"]["total"]["matched"] == 51
    for params in scene.table_mounting.values():
        assert params.tilt_degrees == 20 and params.minimum_clearance_m == 0.8


def test_rengo_fixture_changes_require_review(tmp_path):
    target = tmp_path / "terrain"
    shutil.copytree(DATA / "rengo_3d", target)
    with (target / "el_mirlo_copernicus.tif").open("ab") as file:
        file.write(b"changed")
    with pytest.raises(ValueError, match="checksum mismatch"):
        build_rengo_scene(DATA / "rengo_modules", target)


def test_count_adapter_preserves_half_pixel_coordinates_and_table_ids(study):
    count = study["counting"]["advanced"]
    bounds = study["scene"].bounds_wgs84
    footprints = footprints_from_count(count, bounds)
    cell = next(c for c in count.cells if c.status != "excluded")
    first = footprints[0]
    assert first.id == cell.id and first.table_id == str(cell.table)
    west, south, east, north = bounds
    h, w = count.image_shape
    expected = [
        [west + (x + 0.5) / w * (east - west), north - (y + 0.5) / h * (north - south)]
        for x, y in cell.vertices_xy
    ]
    assert_allclose(first.vertices_wgs84, expected, atol=1e-12)
    assert len(footprints_from_count(count, bounds, include_review=False)) <= len(footprints)


def test_geojson_export_roundtrip_keeps_grouping(tmp_path, study):
    output = export_rengo_study(DATA / "rengo_modules", tmp_path / "count")
    geojson = json.loads((output / "lattice_candidates.geojson").read_text())
    actual = footprints_from_geojson(geojson)
    expected = footprints_from_count(study["counting"]["advanced"], study["scene"].bounds_wgs84)
    assert [f.id for f in actual] == [f.id for f in expected]
    assert [f.table_id for f in actual] == [f.table_id for f in expected]
    assert_allclose(actual[0].vertices_wgs84, expected[0].vertices_wgs84)


@pytest.mark.parametrize("problem", ["missing_id", "missing_table", "hole", "altitude"])
def test_geojson_does_not_guess_missing_structure(problem):
    ring = [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]
    feature = {
        "type": "Feature",
        "id": "one",
        "properties": {"table": "A"},
        "geometry": {"type": "Polygon", "coordinates": [ring]},
    }
    if problem == "missing_id":
        del feature["id"]
    elif problem == "missing_table":
        feature["properties"] = {}
    elif problem == "hole":
        feature["geometry"]["coordinates"].append(ring)
    else:
        feature["geometry"]["coordinates"] = [[[*xy, 3] for xy in ring]]
    with pytest.raises(ValueError):
        footprints_from_geojson({"type": "FeatureCollection", "features": [feature]})


def test_exports_have_valid_obj_indices_georeference_and_offline_viewer(tmp_path, study):
    original = study["scene"]
    footprints = footprints_from_count(study["counting"]["advanced"], original.bounds_wgs84)[:3]
    scene = build_pv_site_scene(
        footprints,
        study["grid"],
        frame=original.frame,
        bounds_wgs84=original.bounds_wgs84,
        display_grid_shape=(5, 5),
    )
    destination = export_site_scene(
        scene,
        tmp_path / "scene",
        title="<script>bad()</script>",
        attribution="<b>credit</b>",
        provenance={"test": "fixture"},
    )
    document = json.loads((destination / "scene.json").read_text())
    assert document["vertical_datum"] == "EGM2008"
    assert document["provenance"] == {"test": "fixture"}
    assert document["frame"]["elevation_origin_m"] == 282
    assert_allclose(document["modules"][0]["vertices_m"], scene.modules[0].vertices_m)
    lines = (destination / "site.obj").read_text().splitlines()
    vertices = [line for line in lines if line.startswith("v ")]
    faces = np.array(
        [[int(i) for i in line.split()[1:]] for line in lines if line.startswith("f ")]
    )
    assert faces.min() == 1 and faces.max() == len(vertices)
    assert len(faces) == len(scene.terrain.triangles) + 2 * len(scene.modules)
    assert sum(line.startswith("o module_") for line in lines) == len(scene.modules)
    viewer = (destination / "viewer.html").read_text()
    assert "<script>bad()</script>" not in viewer
    assert "&lt;script&gt;bad()&lt;/script&gt;" in viewer and "&lt;b&gt;credit&lt;/b&gt;" in viewer
    assert '<script src="' not in viewer and "Plotly.newPlot" in viewer
    assert "Vertical display x5" in viewer
    with pytest.raises(FileExistsError):
        export_site_scene(scene, destination)
