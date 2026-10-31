"""Independent synthetic inventories test counting decisions, not real-site accuracy."""

from dataclasses import replace

import numpy as np
import pytest
from scipy import ndimage

from energy_methods.pv_module_counting import (
    ModuleCountingConfig,
    count_regular_pv_modules,
    module_candidates_geojson,
)


def synthetic_inventory(*, missing=False, noise=0.0, slope=0.0):
    """Two synthetic framed tables: 16 x 5 and 20 x 5 modules, with known truth."""
    image = np.full((180, 260, 3), [0.45, 0.38, 0.27])
    for top, columns in ((25, 16), (100, 20)):
        left, rows, dx, dy = 25, 5, 10, 6
        image[top : top + rows * dy + 1, left : left + columns * dx + 1] = [0.20, 0.36, 0.44]
        image[top : top + rows * dy + 1 : dy, left : left + columns * dx + 1] = [0.85, 0.88, 0.90]
        image[top : top + rows * dy + 1, left : left + columns * dx + 1 : dx] = [0.85, 0.88, 0.90]
        if missing and top == 25:
            image[top + 2 * dy + 1 : top + 3 * dy, left + 4 * dx + 1 : left + 5 * dx] = [
                0.45,
                0.38,
                0.27,
            ]
    if slope:
        for x in range(image.shape[1]):
            image[:, x] = ndimage.shift(
                image[:, x], (slope * (x - 130), 0), order=1, mode="nearest"
            )
    if noise:
        image = np.clip(image + np.random.default_rng(10).normal(0, noise, image.shape), 0, 1)
    return image


@pytest.mark.parametrize("options", [{}, {"noise": 0.015}, {"slope": -0.04}])
def test_counts_independent_inventory_with_noise_and_shear(options):
    result = count_regular_pv_modules(synthetic_inventory(**options))
    assert result.estimated_modules == 180
    assert [(t.rows, t.columns) for t in result.tables] == [(5, 16), (5, 20)]
    assert result.regular_candidates == 180 and result.review_candidates == 0
    assert not result.rejected_tables
    assert len({c.id for c in result.cells}) == 180


def test_does_not_fill_in_missing_module_or_count_outside_scope():
    result = count_regular_pv_modules(synthetic_inventory(missing=True))
    assert result.estimated_modules == 179
    excluded = [c for c in result.cells if c.status == "excluded"]
    assert len(excluded) == 1 and excluded[0].id == "t01-r03-c005"
    assert excluded[0].reasons == ("insufficient_panel_colour",)
    mask = np.ones((180, 260), dtype=bool)
    mask[90:] = False
    result = count_regular_pv_modules(synthetic_inventory(), mask)
    assert result.estimated_modules == 80
    assert max(y for c in result.cells for _, y in c.vertices_xy) < 90


def test_blank_unframed_and_low_resolution_are_unresolved_not_zero():
    blank = np.full((180, 260, 3), 0.4)
    plain = blank.copy()
    plain[25:56, 25:186] = [0.2, 0.36, 0.44]
    small = ndimage.zoom(synthetic_inventory(), (0.1, 0.1, 1), order=1)
    for image in (blank, plain, small):
        result = count_regular_pv_modules(image)
        assert result.estimated_modules is None
        assert result.to_frame().empty
    assert count_regular_pv_modules(plain).rejected_tables


def test_limits_fail_explicitly_and_clipped_or_steep_tables_are_flagged():
    image = synthetic_inventory()
    with pytest.raises(ValueError, match="maximum_pixels"):
        count_regular_pv_modules(image, maximum_pixels=100)
    with pytest.raises(OverflowError, match="maximum_cells"):
        count_regular_pv_modules(image, maximum_cells=10)
    clipped = count_regular_pv_modules(image[:, 24:])
    assert clipped.estimated_modules is None
    assert {r["reason"] for r in clipped.rejected_tables} == {"clipped_image_edge"}
    steep = count_regular_pv_modules(synthetic_inventory(slope=0.2))
    assert steep.estimated_modules is None
    assert steep.rejected_tables


def test_uint8_and_georeference_half_pixel_offset():
    result = count_regular_pv_modules((synthetic_inventory() * 255).astype(np.uint8))
    assert result.estimated_modules == 180
    collection = module_candidates_geojson(result, (-2, 40, -1, 41))
    assert len(collection["features"]) == 180
    cell = result.cells[0]
    ring = collection["features"][0]["geometry"]["coordinates"][0]
    x, y = cell.vertices_xy[0]
    assert ring[0] == pytest.approx([-2 + (x + 0.5) / 260, 41 - (y + 0.5) / 180])
    assert ring[-1] == ring[0]
    assert collection["features"][0]["properties"]["status"] == "regular_candidate"
    with pytest.raises(ValueError, match="bounds_wgs84"):
        module_candidates_geojson(result, (1, 40, -1, 41))


@pytest.mark.parametrize(
    "image",
    [
        np.zeros((10, 10)),
        np.zeros((10, 10, 4)),
        np.zeros((10, 10, 3), dtype=np.int16),
        np.full((10, 10, 3), np.nan),
        np.full((10, 10, 3), 255.0),
    ],
)
def test_invalid_images_fail_at_boundary(image):
    with pytest.raises(ValueError):
        count_regular_pv_modules(image)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"blue_excess": np.nan},
        {"row_prominence": 0},
        {"minimum_table_pixels": True},
        {"minimum_pitch_pixels": 1},
        {"maximum_slope": 1},
        {"spacing_tolerance": -0.1},
    ],
)
def test_invalid_parameters(kwargs):
    with pytest.raises(ValueError):
        ModuleCountingConfig(**kwargs)


def test_mask_validation_and_pitch_gate():
    image = synthetic_inventory()
    for mask in (np.ones((180, 260)), np.zeros((180, 260), bool), np.ones((10, 10), bool)):
        with pytest.raises(ValueError, match="site_mask"):
            count_regular_pv_modules(image, mask)  # ty: ignore[invalid-argument-type]
    horizontal = replace(ModuleCountingConfig(), maximum_slope=0)
    assert count_regular_pv_modules(image, config=horizontal).estimated_modules == 180
    config = replace(ModuleCountingConfig(), minimum_pitch_pixels=8)
    result = count_regular_pv_modules(image, config=config)
    assert result.estimated_modules is None
    assert all(r["reason"] == "insufficient_pixel_pitch" for r in result.rejected_tables)
