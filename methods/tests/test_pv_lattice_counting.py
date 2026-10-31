"""Known synthetic inventories test geometry; real-site accuracy is not asserted."""

from dataclasses import replace

import numpy as np
import pytest
from scipy import ndimage

from energy_methods.pv_lattice_counting import LatticeCountingConfig, count_lattice_pv_modules


def inventory(*, angle=0, missing=False, noise=0):
    """Two independent two-row inventories: 32 + 40 modules, with bright frames."""
    background = [0.45, 0.38, 0.27]
    image = np.full((230, 300, 3), background)
    for y, columns in ((40, 16), (140, 20)):
        x, dx, dy = 40, 10, 14
        image[y : y + 2 * dy + 1, x : x + columns * dx + 1] = [0.20, 0.36, 0.44]
        image[y : y + 2 * dy + 1 : dy, x : x + columns * dx + 1] = [0.85, 0.88, 0.9]
        image[y : y + 2 * dy + 1, x : x + columns * dx + 1 : dx] = [0.85, 0.88, 0.9]
        if missing and y == 40:
            image[y + 1 : y + dy, x + 4 * dx + 1 : x + 5 * dx] = background
    if angle:
        image = np.stack(
            [ndimage.rotate(image[..., c], angle, order=1, cval=background[c]) for c in range(3)],
            axis=-1,
        )
    if noise:
        image = np.clip(image + np.random.default_rng(18).normal(0, noise, image.shape), 0, 1)
    return image


@pytest.mark.parametrize("angle", [0, 90, -35, 22, 180])
def test_known_two_row_inventory_and_orientation(angle):
    result = count_lattice_pv_modules(inventory(angle=angle))
    assert result.estimated_modules == 72
    assert len(result.tables) == 2
    assert not result.rejected_tables
    assert len(set(result.to_frame().id)) == len(result.cells)
    for cell in result.cells:
        assert all(
            0 <= x < result.image_shape[1] and 0 <= y < result.image_shape[0]
            for x, y in cell.vertices_xy
        )


def test_noise_missing_module_and_scope_are_not_filled():
    assert count_lattice_pv_modules(inventory(noise=0.015)).estimated_modules == 72
    result = count_lattice_pv_modules(inventory(missing=True))
    assert result.estimated_modules == 71
    assert result.to_frame().query('status == "excluded"').reasons.str.contains("colour").all()
    mask = np.ones((230, 300), bool)
    mask[100:] = False
    assert count_lattice_pv_modules(inventory(), mask).estimated_modules == 32


def test_blank_unframed_and_oversampled_sources_are_unresolved():
    image = np.full((230, 300, 3), [0.45, 0.38, 0.27])
    for framed in (False, True):
        if framed:
            image[40:69, 40:201] = [0.20, 0.36, 0.44]
        result = count_lattice_pv_modules(image)
        assert result.estimated_modules is None
        assert result.to_frame().empty
    cfg = LatticeCountingConfig(source_pixel_ratio=4)
    result = count_lattice_pv_modules(inventory(), config=cfg)
    assert result.estimated_modules is None
    assert {r["reason"] for r in result.rejected_tables} == {"insufficient_source_pitch"}


def test_limits_and_clipped_geometry():
    with pytest.raises(ValueError, match="maximum_pixels"):
        count_lattice_pv_modules(inventory(), maximum_pixels=10)
    with pytest.raises(OverflowError, match="maximum_cells"):
        count_lattice_pv_modules(inventory(), maximum_cells=10)
    result = count_lattice_pv_modules(inventory()[:, 50:])
    assert result.estimated_modules is None
    assert {r["reason"] for r in result.rejected_tables} == {"clipped_image_edge"}
    a = count_lattice_pv_modules((inventory() * 255).astype(np.uint8))
    assert a.estimated_modules == 72


@pytest.mark.parametrize(
    "kwargs",
    [
        {"minimum_chroma": np.nan},
        {"minimum_cell_contrast": 0},
        {"source_pixel_ratio": 0.5},
        {"minimum_component_pixels": True},
        {"minimum_source_pitch": 2},
        {"maximum_pitch_pixels": 200},
        {"frame_prominence": -1},
    ],
)
def test_invalid_parameters(kwargs):
    with pytest.raises(ValueError):
        LatticeCountingConfig(**kwargs)


def test_invalid_inputs_and_explicit_high_contrast_abstention():
    for image in (
        np.zeros((20, 20)),
        np.zeros((20, 20, 4)),
        np.full((20, 20, 3), np.nan),
        np.zeros((20, 20, 3), dtype=np.int16),
    ):
        with pytest.raises(ValueError):
            count_lattice_pv_modules(image)
    for mask in (np.ones((230, 300)), np.zeros((230, 300), bool), np.ones((30, 30), bool)):
        with pytest.raises(ValueError, match="site_mask"):
            count_lattice_pv_modules(inventory(), mask)  # ty: ignore[invalid-argument-type]
    result = count_lattice_pv_modules(
        inventory(), config=replace(LatticeCountingConfig(), frame_prominence=0.99)
    )
    assert result.estimated_modules is None
