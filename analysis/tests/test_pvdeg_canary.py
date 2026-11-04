import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from energy_analysis.pvdeg_canary import screen_climate_tile, write_stress_geotiff


def test_scaled_raster_and_export(tmp_path):
    path = tmp_path / "climate.tif"
    data = np.full((12, 2, 2), 500, dtype="int16")
    data[2, 0, 0] = -32768
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        count=12,
        width=2,
        height=2,
        dtype="int16",
        nodata=-32768,
        crs="EPSG:32628",
        transform=from_origin(300000, 3100000, 100, 100),
    ) as ds:
        ds.write(data)
        ds.scales = (0.01,) * 12
        ds.update_tags(units="degC")
    result, profile = screen_climate_tile(path)
    assert np.isnan(result[0, 0])
    assert result[1, 1] == pytest.approx(1)
    output = tmp_path / "map.tif"
    write_stress_geotiff(output, result, profile)
    with rasterio.open(output) as ds:
        assert ds.read(1, masked=True).mask[0, 0]
        assert ds.res == (100, 100)
