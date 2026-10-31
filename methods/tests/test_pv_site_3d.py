"""Analytic geometry checks, independent of the Rengo image detector."""

import numpy as np
import pytest
from numpy.testing import assert_allclose

from energy_methods.pv_site_3d import (
    ElevationGrid,
    LocalSiteFrame,
    ModuleFootprint,
    MountingParameters,
    build_pv_site_scene,
)


@pytest.mark.parametrize("origin", [(-70.86, -34.45), (-16.42, 28.36), (150, -25)])
def test_local_frame_roundtrip_and_metric_axes(origin):
    frame = LocalSiteFrame(*origin)
    xy = np.array([[0, 0], [120, 0], [0, 80], [-120, -80]])
    ll = frame.unproject(xy)
    assert_allclose(frame.project(ll), xy, atol=1e-7)
    assert ll[1, 0] > origin[0] and ll[2, 1] > origin[1]
    with pytest.raises(ValueError, match="radius"):
        frame.unproject([[20_001, 0]])
    with pytest.raises(ValueError, match="radius"):
        frame.project([[origin[0] + 1, origin[1]]])


def test_geographic_bilinear_grid_has_no_extrapolation_or_nodata_infill():
    values = np.array([[0, 2, 4], [10, 12, 14], [20, 22, np.nan]])
    grid = ElevationGrid(values, (1, 0, 0, 0, -1, 3), "EPSG:4326", "test")
    assert_allclose(grid.sample([[0.5, 2.5], [1, 2], [1.5, 0.5]]), [0, 6, 22])
    assert np.isnan(grid.sample([[0.4, 2.5], [2, 1], [2.5, 0.5]])).all()
    values[0, 0] = 999
    assert grid.sample([[0.5, 2.5]])[0] == 0
    assert not grid.values_m.flags.writeable


def setup_plane():
    frame = LocalSiteFrame(-70.86, -34.45, 100)
    # Native 10 m grid whose centres span -50..50 in both local axes.
    x, y = np.meshgrid(np.arange(-50, 51, 10), np.arange(50, -51, -10))
    grid = ElevationGrid(
        100 + 0.03 * x + 0.02 * y,
        (10, 0, -55, 0, -10, 55),
        frame.crs.to_wkt(),
        "analytic test height",
    )
    footprints = [
        ModuleFootprint(
            str(i), table, frame.unproject(np.array([[x, 0], [x + 2, 0], [x + 2, 4], [x, 4]]))
        )
        for i, (x, table) in enumerate([(-10, "A"), (-8, "A"), (10, "B")])
    ]
    ll = frame.unproject([[-45, -45], [45, 45]])
    bounds = (ll[0, 0], ll[0, 1], ll[1, 0], ll[1, 1])
    return frame, grid, footprints, bounds


def test_projected_sampling_matches_an_analytic_plane():
    frame, grid, _, _ = setup_plane()
    xy = np.array([[0, 0], [1.2, 3.4], [-20, 10]])
    assert_allclose(
        grid.sample(frame.unproject(xy)), 100 + 0.03 * xy[:, 0] + 0.02 * xy[:, 1], atol=1e-8
    )


def test_projected_native_centres_survive_roundtrip_beside_nodata():
    frame, grid, _, _ = setup_plane()
    values = np.full_like(grid.values_m, np.nan)
    values[2, 8] = 0
    isolated = ElevationGrid(values, grid.transform, grid.crs, grid.vertical_datum)
    assert_allclose(isolated.sample(frame.unproject([[30, 30]])), [0])


def test_shared_table_planes_have_correct_slope_clearance_and_preserve_xy():
    frame, grid, footprints, bounds = setup_plane()
    scene = build_pv_site_scene(
        footprints,
        grid,
        frame=frame,
        bounds_wgs84=bounds,
        mounting=MountingParameters(20, 0, 0.8),
        table_mounting={"B": MountingParameters(10, 90, 1)},
        display_grid_shape=(11, 11),
    )
    for table_id, params in scene.table_mounting.items():
        modules = [m for m in scene.modules if m.table_id == table_id]
        vertices = np.concatenate([m.vertices_m for m in modules])
        intercepts = vertices[:, 2] - vertices[:, :2] @ params.gradient
        assert_allclose(intercepts, intercepts[0], atol=1e-9)
        clearance = np.concatenate([m.vertices_m[:, 2] - m.terrain_at_vertices_m for m in modules])
        assert clearance.min() == pytest.approx(params.minimum_clearance_m, abs=1e-8)
    assert_allclose(
        scene.modules[0].vertices_m[:, :2], frame.project(footprints[0].vertices_wgs84), atol=1e-8
    )
    a = scene.modules[0].vertices_m
    assert (a[2, 2] - a[1, 2]) / 4 == pytest.approx(-np.tan(np.radians(20)))
    b = scene.modules[2].vertices_m
    assert (b[1, 2] - b[0, 2]) / 2 == pytest.approx(-np.tan(np.radians(10)))
    for mesh in (scene.terrain, scene.module_mesh):
        tri = mesh.vertices_m[mesh.triangles]
        assert (np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])[:, 2] > 0).all()
    assert scene.input_module_count == len(scene.modules) == 3


def test_missing_terrain_rejects_a_module_without_filling_the_gap():
    frame, grid, footprints, bounds = setup_plane()
    values = grid.values_m.copy()
    values[4:7, 6:8] = np.nan  # table B only
    grid = ElevationGrid(values, grid.transform, grid.crs, grid.vertical_datum)
    scene = build_pv_site_scene(
        footprints, grid, frame=frame, bounds_wgs84=bounds, display_grid_shape=(11, 11)
    )
    assert len(scene.modules) == 2
    assert scene.rejected_modules == (
        {"id": "2", "table_id": "B", "reason": "missing_terrain_samples"},
    )
    assert np.isfinite(scene.terrain.vertices_m).all()
    assert len(scene.terrain.triangles) < 200
    with pytest.raises(ValueError, match="No module footprints"):
        build_pv_site_scene(footprints[2:], grid, frame=frame, bounds_wgs84=bounds)


@pytest.mark.parametrize(
    "change,match",
    [
        ({"maximum_modules": 2}, "maximum_modules"),
        ({"table_mounting": {"unknown": MountingParameters()}}, "Unknown table"),
        ({"display_grid_shape": (501, 500)}, "250000"),
        ({"bounds_wgs84": (1, 2, -1, 3)}, "bounds"),
    ],
)
def test_invalid_scene_configuration_fails(change, match):
    frame, grid, footprints, bounds = setup_plane()
    kwargs = {"frame": frame, "bounds_wgs84": bounds, **change}
    with pytest.raises(ValueError, match=match):
        build_pv_site_scene(footprints, grid, **kwargs)


def test_footprint_and_identity_checks():
    frame, grid, footprints, bounds = setup_plane()
    with pytest.raises(ValueError, match="unique"):
        build_pv_site_scene([footprints[0]] * 2, grid, frame=frame, bounds_wgs84=bounds)
    with pytest.raises(ValueError, match="convex"):
        ModuleFootprint("bad", "A", np.array([[0, 0], [1, 1], [0, 1], [1, 0]]))
    with pytest.raises(ValueError, match="tilt_degrees"):
        MountingParameters(90)
    with pytest.raises(ValueError, match="north-up"):
        ElevationGrid(np.ones((2, 2)), (1, 1, 0, 0, -1, 0), "EPSG:4326", "test")
