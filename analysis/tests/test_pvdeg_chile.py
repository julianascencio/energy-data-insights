"""Native-grid interpretation and missing-data tests with synthetic Kelvin fixtures."""

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from energy_analysis.pvdeg_chile import screen_monthly_rasters


def inputs(tmp_path):
    paths = []
    for month in range(1, 13):
        path = tmp_path / f"month_{month}.tif"
        values = np.full((3, 2), 27815, dtype="uint16")
        if month == 6:
            values[1, 1] = 65535
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            width=2,
            height=3,
            count=1,
            dtype="uint16",
            nodata=65535,
            crs="EPSG:4326",
            transform=from_origin(-71.0, -33.0, 1 / 120, 1 / 120),
        ) as out:
            out.write(values, 1)
            out.scales = (0.01,)
            out.update_tags(variable_unit="K", month=str(month), datetime="1981-2010")
        paths.append(path)
    return paths


def test_kelvin_scale_missing_and_batch_invariance(tmp_path):
    paths = inputs(tmp_path)
    one, profile = screen_monthly_rasters(paths, rows_per_batch=1)
    all_rows, _ = screen_monthly_rasters(paths, rows_per_batch=128)
    np.testing.assert_allclose(one, all_rows)
    assert one[0, 0] == pytest.approx(1.0)  # 5 C air plus 20 C = 25 C reference
    assert np.isnan(one[1, 1])
    assert profile["transform"].a == pytest.approx(1 / 120)


def test_month_order_and_alignment_rejected(tmp_path):
    paths = inputs(tmp_path)
    with pytest.raises(ValueError, match="aligned"):
        screen_monthly_rasters(paths[::-1])
    with rasterio.open(paths[-1], "r+") as out:
        out.transform = from_origin(-70.0, -33.0, 1 / 120, 1 / 120)
    with pytest.raises(ValueError, match="aligned"):
        screen_monthly_rasters(paths)


@pytest.mark.parametrize("kwargs", [{"module_offset_c": -1}, {"rows_per_batch": 0}])
def test_invalid_configuration(tmp_path, kwargs):
    with pytest.raises(ValueError):
        screen_monthly_rasters(inputs(tmp_path), **kwargs)
