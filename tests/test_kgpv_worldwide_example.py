"""Scientific conversion and integrity checks for the offline global example."""

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from energy_methods.kgpv import map_kgpv
from energy_methods.mapping import cell_areas_km2

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "prepare_kgpv_worldwide", ROOT / "scripts/prepare_kgpv_worldwide.py"
)
assert spec is not None and spec.loader is not None
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


def test_rate_conversion_calendar_and_negative_solar_policy():
    months = {"month": np.arange(1, 13)}
    air = xr.DataArray(np.full(12, 273.15), dims="month", coords=months)
    rain = xr.full_like(air, 1 / 86400)  # one mm/day
    solar = xr.full_like(air, 100)  # 100 W/m² all year
    temperature, precipitation, ghi = prepare.convert_fields(air, rain, solar)
    np.testing.assert_allclose(temperature, 0)
    assert float(precipitation.sel(month=2)) == pytest.approx(28 + 8 / 30)
    assert float(precipitation.sum()) == pytest.approx(365 + 8 / 30)
    assert float(ghi) == pytest.approx(100 * 24 * (365 + 8 / 30) / 1000)
    solar[0] = -0.05
    assert float(prepare.convert_fields(air, rain, solar)[2]) == pytest.approx(
        float(ghi) - 100 * 24 * 31 / 1000
    )
    solar[0] = -0.2
    with pytest.raises(ValueError, match="Negative"):
        prepare.convert_fields(air, rain, solar)
    solar[0] = np.nan
    assert np.isnan(prepare.convert_fields(air, rain, solar)[2])
    rain[0] = -1
    with pytest.raises(ValueError, match="Negative"):
        prepare.convert_fields(air, rain, solar)


def test_source_baseline_units_month_order_and_coverage():
    time = np.r_[0, np.cumsum([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30])] * 24
    source = xr.Dataset(
        {
            "air": (("time", "lat", "lon"), np.full((12, 2, 2), 280.0), {"units": "degK"}),
            "valid_yr_count": (("time", "lat", "lon"), np.full((12, 2, 2), 30)),
        },
        coords={"time": time, "lat": [0, 1], "lon": [0, 1]},
    )
    source.time.attrs = {
        "climo_period": "1991/01/01 - 2020/12/31",
        "units": "hours since 1800-01-01 00:00:0.0",
        "interpreted_actual_range": "0001/01/01 00:00:00 - 0001/12/01 00:00:00",
    }
    source.valid_yr_count[0, 0, 0] = 29
    field = prepare.monthly_field(source, "air", "degK")
    assert np.isnan(field[0, 0, 0])
    assert float(field[0, 1, 1]) == 280
    with pytest.raises(ValueError, match="units"):
        prepare.monthly_field(source, "air", "degC")
    with pytest.raises(ValueError, match="climatology"):
        prepare.monthly_field(source.isel(time=slice(None, None, -1)), "air", "degK")
    source.time.attrs["climo_period"] = "1981/01/01 - 2010/12/31"
    with pytest.raises(ValueError, match="climatology"):
        prepare.monthly_field(source, "air", "degK")


def test_fixture_integrity_global_grid_ocean_mask_and_classifier():
    path = ROOT / "examples/analysis/kgpv_worldwide_inputs.csv"
    manifest = json.loads((ROOT / "examples/analysis/kgpv_worldwide_provenance.json").read_text())
    assert hashlib.sha256(path.read_bytes()).hexdigest() == manifest["fixture_sha256"]
    table = pd.read_csv(path).set_index(["lat", "lon"]).to_xarray()
    np.testing.assert_array_equal(table.lat, np.arange(-87.5, 90, 5))
    np.testing.assert_array_equal(table.lon, np.arange(-177.5, 180, 5))
    assert int(table.is_land.sum()) == manifest["land_cells"]
    months = xr.IndexVariable("month", np.arange(1, 13))
    temperature = xr.concat([table[f"t{m:02d}"] for m in range(1, 13)], dim=months)
    precipitation = xr.concat([table[f"p{m:02d}"] for m in range(1, 13)], dim=months)
    ghi = table.annual_ghi
    for field, units in ((temperature, "degC"), (precipitation, "mm"), (ghi, "kWh m-2")):
        field.attrs = {"units": units, "baseline_start_year": 1991, "baseline_end_year": 2020}
        assert field.where(table.is_land == 0).isnull().all()
    classes = map_kgpv(temperature, precipitation, ghi).kgpv_class
    assert int((classes > 0).sum()) == manifest["valid_land_cells"]
    assert (classes.where(table.is_land == 0, 0) == 0).all()
    assert set(np.unique(classes)).issubset(set(range(13)))
    # Complete spherical coverage, with smaller polar cells than equatorial ones.
    areas = cell_areas_km2(classes)
    assert float(areas.sum()) == pytest.approx(4 * np.pi * 6371.0088**2)
    assert float(areas[0, 0]) < float(areas[18, 0])
