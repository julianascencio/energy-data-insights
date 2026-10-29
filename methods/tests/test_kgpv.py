"""Independent synthetic checks against 2019 Fig. A1, Table 4 and Kottek Eq. 2.1."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from energy_methods.climatology import monthly_climatology
from energy_methods.kgpv import ZONE_CODES, classify_kgpv, map_kgpv
from energy_methods.kgpv_cli import main
from energy_methods.mapping import class_area_summary, regrid, write_geojson


@pytest.mark.parametrize(
    "temperature,rain,expected",
    [
        ([10.0] * 12, 0.0, "F"),  # Polar has priority even with no rain.
        ([25.0] * 12, 0.0, "B"),
        ([25.0] * 12, 30.0, "C"),  # P=360, Pth=64: 320 < 360 <= 640.
        ([25.0] * 12, 100.0, "A"),
        ([18.0] * 12, 100.0, "A"),  # Explicit resolution of exact-18 gap.
        ([17.0] * 12, 100.0, "D"),
        ([-3.0] + [20.0] * 11, 100.0, "E"),
        ([-2.99] + [20.0] * 11, 100.0, "D"),
    ],
)
def test_tp_precedence(temperature: list[float], rain: float, expected: str) -> None:
    result = classify_kgpv(temperature, np.full(12, rain), 1700.0, 30.0)
    assert result.tp_zone.item() == expected


@pytest.mark.parametrize(
    "annual,expected", [(320.0, "B"), (320.01, "C"), (640.0, "C"), (640.01, "A")]
)
def test_aridity_equalities(annual: float, expected: str) -> None:
    assert classify_kgpv(np.full(12, 25.0), np.full(12, annual / 12), 1700, 30).tp_zone == expected


def test_seasonal_two_thirds_and_hemispheres() -> None:
    rain = np.full(12, 10.0)
    rain[3:9] = 20.0  # Exactly 2/3 falls Apr-Sep.
    result = classify_kgpv(np.full((2, 12), 20.0), np.tile(rain, (2, 1)), [1700, 1700], [30, -30])
    np.testing.assert_allclose(result.precipitation_threshold_mm, [68, 40])


@pytest.mark.parametrize(
    "ghi,zone",
    [(1130.0, "L"), (1130.01, "M"), (1560.0, "M"), (1560.01, "H"), (2070.0, "H"), (2070.01, "K")],
)
def test_irradiation_boundaries(ghi: float, zone: str) -> None:
    assert classify_kgpv(np.full(12, 25.0), np.full(12, 100.0), ghi, 0).irradiation_zone == zone


@pytest.mark.parametrize(
    "t,p,codes",
    [
        ([25.0] * 12, 100.0, ["AH", "AH", "AH", "AK"]),
        ([25.0] * 12, 0.0, ["BH", "BH", "BH", "BK"]),
        ([25.0] * 12, 30.0, ["CH", "CH", "CH", "CK"]),
        ([15.0] * 12, 100.0, ["DL", "DM", "DH", "DH"]),
        ([-5.0] + [15.0] * 11, 100.0, ["EL", "EM", "EM", "EM"]),
        ([0.0] * 12, 100.0, ["FL", "FL", "FL", "FL"]),
    ],
)
def test_all_24_table4_merges(t: list[float], p: float, codes: list[str]) -> None:
    result = classify_kgpv(np.tile(t, (4, 1)), np.full((4, 12), p), [1000, 1300, 1800, 2200], 30)
    assert result.zone.tolist() == codes


def test_missing_and_invalid_inputs() -> None:
    t = np.full((3, 12), 25.0)
    p = np.full((3, 12), 100.0)
    t[0, 0] = np.nan
    p[1, 5] = np.nan
    result = classify_kgpv(t, p, [1700, 1700, np.nan], 0)
    assert result.class_id.tolist() == [0, 0, 0]
    assert result.raw_zone.tolist() == ["", "", ""]
    with pytest.raises(ValueError, match="negative"):
        classify_kgpv(np.full(12, 25.0), np.full(12, -1.0), 1700, 0)
    with pytest.raises(ValueError, match="shape"):
        classify_kgpv(np.full(11, 25.0), np.full(11, 1.0), 1700, 0)


def monthly(name: str = "temperature_c", units: str = "degC") -> xr.DataArray:
    return xr.DataArray(
        np.ones((24, 2, 2)),
        dims=("time", "lat", "lon"),
        coords={
            "time": pd.date_range("2000-01-01", periods=24, freq="MS"),
            "lat": [0.0, 1.0],
            "lon": [10.0, 11.0],
        },
        name=name,
        attrs={"units": units},
    )


def test_streaming_climatology_equal_weight_and_coverage() -> None:
    data = monthly()
    data.values[12:] = 3
    data.values[0, 0, 0] = np.nan
    result = monthly_climatology([data[:7], data[7:]], start_year=2000, end_year=2001)
    assert np.isnan(result.temperature_c.sel(month=1).values[0, 0])
    assert result.temperature_c.sel(month=2).values[0, 0] == 2
    assert result.valid_years.sel(month=1).values[0, 0] == 1
    relaxed = monthly_climatology([data], start_year=2000, end_year=2001, minimum_valid_years=1)
    assert relaxed.temperature_c.sel(month=1).values[0, 0] == 3
    with pytest.raises(ValueError, match="Incomplete baseline"):
        monthly_climatology([data[:-1]], start_year=2000, end_year=2001)
    with pytest.raises(ValueError, match="Overlapping"):
        monthly_climatology([data, data], start_year=2000, end_year=2001)


def climate_inputs() -> tuple[xr.DataArray, xr.DataArray, xr.DataArray]:
    t = monthly_climatology([monthly() * 20], start_year=2000, end_year=2001).temperature_c
    t.attrs["units"] = "degC"
    p = t.copy(data=np.full(t.shape, 100.0)).rename("precipitation_mm")
    p.attrs["units"] = "mm"
    ghi = t.isel(month=0, drop=True).copy(data=np.full((2, 2), 1700.0)).rename("annual_ghi_kwh_m2")
    ghi.attrs["units"] = "kWh m-2"
    return t, p, ghi


def test_map_alignment_metadata_and_netcdf(tmp_path: Path) -> None:
    t, p, ghi = climate_inputs()
    result = map_kgpv(t, p, ghi)
    assert (result.kgpv_zone == "AH").all()
    result.to_netcdf(tmp_path / "map.nc", engine="scipy")
    with xr.open_dataset(tmp_path / "map.nc") as saved:
        assert saved.kgpv_zone.values.tolist() == [["AH", "AH"], ["AH", "AH"]]
        assert saved.attrs["baseline_start_year"] == 2000
    with pytest.raises(ValueError, match="align"):
        map_kgpv(t, p.assign_coords(lon=[10.0, 12.0]), ghi)
    ghi.attrs["baseline_end_year"] = 2020
    with pytest.raises(ValueError, match="same baseline"):
        map_kgpv(t, p, ghi)


def test_mapping_linear_plane_categorical_and_geojson(tmp_path: Path) -> None:
    field = xr.DataArray(
        [[0.0, 2.0], [2.0, 4.0]], dims=("lat", "lon"), coords={"lat": [0.0, 2.0], "lon": [0.0, 2.0]}
    )
    assert regrid(field, [1.0], [1.0]).item() == 2.0
    assert np.isnan(regrid(field, [3.0], [3.0])).item()
    with pytest.raises(ValueError, match="Categorical"):
        regrid(field, [1.0], [1.0], categorical=True)
    assert regrid(field, [0.1], [0.1], categorical=True, method="nearest").item() == 0
    layer = field.copy(data=[[0, 1], [2, 2]])
    write_geojson(layer, tmp_path / "map.geojson", nodata=0, labels={1: "AH", 2: "AK"})
    features = json.loads((tmp_path / "map.geojson").read_text())["features"]
    assert len(features) == 3
    assert features[0]["geometry"]["coordinates"][0] == [
        [1.0, -1.0],
        [3.0, -1.0],
        [3.0, 1.0],
        [1.0, 1.0],
        [1.0, -1.0],
    ]
    assert set(class_area_summary(layer)) == {1, 2}
    with pytest.raises(ValueError, match="maximum_features"):
        write_geojson(layer, tmp_path / "too-big.json", maximum_features=1)


def test_cli_end_to_end_synthetic(tmp_path: Path) -> None:
    t = monthly() * 20
    t.attrs["units"] = "degC"
    p = monthly("precipitation_mm", "mm") * 100
    p.attrs["units"] = "mm"
    t.to_netcdf(tmp_path / "temperature.nc")
    p.to_netcdf(tmp_path / "precipitation.nc")
    ghi = climate_inputs()[2]
    ghi.to_netcdf(tmp_path / "ghi.nc")
    assert (
        main(
            [
                "--temperature",
                str(tmp_path / "temperature.nc"),
                "--precipitation",
                str(tmp_path / "precipitation.nc"),
                "--annual-ghi",
                str(tmp_path / "ghi.nc"),
                "--start-year",
                "2000",
                "--end-year",
                "2001",
                "--geojson",
                "--output",
                str(tmp_path / "result"),
            ]
        )
        == 0
    )
    manifest = json.loads((tmp_path / "result/manifest.json").read_text())
    assert len(manifest["inputs"]) == 3
    assert set(manifest["area_km2"]) == {"AH"}
    assert len(ZONE_CODES) == 13
