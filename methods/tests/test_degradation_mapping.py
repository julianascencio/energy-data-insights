"""Synthetic mapping checks: complete-year integration, geographic areas and CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from energy_methods.degradation import DegradationParameters
from energy_methods.degradation_mapping import (
    RATE_UNITS,
    RATE_VARIABLES,
    STRESS_UNITS,
    annual_stresses,
    degradation_classes,
    kgpv_degradation_summary,
    map_degradation,
)


@pytest.fixture
def parameters() -> DegradationParameters:
    # Zero activation energies intentionally isolate RH/cycle/UV and area behavior.
    return DegradationParameters(
        a_h=0.00004,
        a_p=0.0000008,
        a_tm=0.000001,
        e_h=0,
        e_p=0,
        e_tm=0,
        n=2,
        x=1,
        theta=1,
        a_n=1,
        calibration_id="synthetic-map",
        calibration_source="Test fixture only",
    )


@pytest.fixture
def annual() -> xr.Dataset:
    coords = {"year": [2016, 2017, 2018], "lat": [0.0, 60.0], "lon": [0.0, 60.0]}
    result = xr.Dataset(attrs={"stress_convention": "Synthetic prepared annual stresses"})
    for (name, units), value in zip(STRESS_UNITS.items(), [20, 40, 0, 50, 100, 365], strict=True):
        result[name] = xr.DataArray(
            np.full((3, 2, 2), value, dtype=float),
            dims=("year", "lat", "lon"),
            coords=coords,
            attrs={"units": units},
        )
    return result


@pytest.fixture
def hourly() -> xr.Dataset:
    time = pd.date_range("2016-01-01", "2017-01-01", freq="h", inclusive="left")
    coords = {"time": time, "lat": [0.0, 60.0], "lon": [0.0, 60.0]}
    result = xr.Dataset(attrs={"time_zone": "UTC", "source": "Synthetic hourly climate"})
    for name, values, units in (
        ("module_temperature_c", np.tile(np.arange(24), 366), "degC"),
        ("relative_humidity_percent", np.full(len(time), 50), "%"),
        ("uv_irradiance_w_m2", np.full(len(time), 10), "W m-2"),
    ):
        result[name] = xr.DataArray(
            np.broadcast_to(values[:, None, None], (len(time), 2, 2)).astype(float).copy(),
            dims=("time", "lat", "lon"),
            coords=coords,
            attrs={"units": units},
        )
    return result


def test_leap_year_uv_integral_and_daily_extrema(hourly) -> None:
    result = annual_stresses(hourly, year=2016, cycles_per_year=366)
    assert result.year.item() == 2016
    np.testing.assert_allclose(result.module_temperature_mean_c, 11.5)
    np.testing.assert_allclose(result.module_temperature_upper_c, 23)
    np.testing.assert_allclose(result.module_temperature_lower_c, 0)
    np.testing.assert_allclose(result.relative_humidity_percent, 50)
    np.testing.assert_allclose(result.uv_dose_kwh_m2, 87.84)  # 366 * 24 * 10 / 1000
    np.testing.assert_allclose(result.cycles_per_year, 366)
    assert (result.valid_hour_count == 8784).all()
    for name, units in STRESS_UNITS.items():
        assert result[name].attrs["units"] == units
    assert "Repository aggregation" in result.attrs["stress_convention"]


def test_missing_hour_masks_whole_cell_year_but_keeps_counts(hourly) -> None:
    hourly.uv_irradiance_w_m2[0, 0, 0] = np.nan
    result = annual_stresses(hourly, year=2016, cycles_per_year=366)
    assert result.valid_hour_count[0, 0, 0] == 8783
    for name in STRESS_UNITS:
        assert np.isnan(result[name][0, 0, 0])
        assert np.isfinite(result[name][0, 1, 1])


@pytest.mark.parametrize(
    "mutation", ["gap", "duplicate", "end-labels", "wrong-year", "three-hourly"]
)
def test_incomplete_or_ambiguous_time_axes_fail(hourly, mutation) -> None:
    if mutation == "gap":
        hourly = hourly.isel(time=slice(1, None))
    elif mutation == "duplicate":
        time = hourly.time.values.copy()
        time[1] = time[0]
        hourly = hourly.assign_coords(time=time)
    elif mutation == "end-labels":
        hourly = hourly.assign_coords(time=hourly.time + np.timedelta64(1, "h"))
    elif mutation == "wrong-year":
        hourly = hourly.assign_coords(time=hourly.time + np.timedelta64(366, "D"))
    else:
        hourly = hourly.isel(time=slice(None, None, 3))
    with pytest.raises(ValueError, match="complete UTC year"):
        annual_stresses(hourly, year=2016, cycles_per_year=365)


def test_hourly_units_time_zone_and_invalid_data_fail(hourly) -> None:
    with pytest.raises(ValueError, match="time_zone"):
        annual_stresses(
            hourly.assign_attrs(time_zone="Europe/Ljubljana"), year=2016, cycles_per_year=366
        )
    hourly.uv_irradiance_w_m2.attrs["units"] = "J m-2"
    with pytest.raises(ValueError, match="units"):
        annual_stresses(hourly, year=2016, cycles_per_year=366)
    hourly.uv_irradiance_w_m2.attrs["units"] = "W m-2"
    hourly.relative_humidity_percent[0, 0, 0] = 101
    with pytest.raises(ValueError, match="Invalid hourly"):
        annual_stresses(hourly, year=2016, cycles_per_year=366)


def test_map_preserves_rates_units_years_and_calibration(annual, parameters) -> None:
    result = map_degradation(annual, parameters, aggregation="mean_stress")
    np.testing.assert_allclose(result.hydrolysis_rate, 0.1)
    np.testing.assert_allclose(result.photodegradation_rate, 0.20008)
    np.testing.assert_allclose(result.thermomechanical_rate, 0.0146)
    np.testing.assert_allclose(result.total_rate, 1.1 * 1.20008 * 1.0146 - 1)
    assert (result.valid_year_count == 3).all()
    assert result.attrs["baseline_start_year"] == 2016
    assert result.attrs["baseline_end_year"] == 2018
    assert json.loads(result.attrs["calibration"]) == parameters.to_dict()
    for name in RATE_VARIABLES:
        assert result[name].attrs["units"] == RATE_UNITS


def test_average_stresses_and_average_rates_are_distinct(annual, parameters) -> None:
    annual.relative_humidity_percent.values[:] = np.array([20, 50, 80])[:, None, None]
    stress = map_degradation(annual, parameters, aggregation="mean_stress")
    rate = map_degradation(annual, parameters, aggregation="mean_rate")
    np.testing.assert_allclose(stress.hydrolysis_rate, 0.1)
    np.testing.assert_allclose(rate.hydrolysis_rate, 0.124)  # mean(400,2500,6400)*0.00004
    assert (rate.total_rate > stress.total_rate).all()


@pytest.mark.parametrize("aggregation", ["mean_stress", "mean_rate"])
def test_missing_annual_values_not_filled_and_valid_year_count(
    annual, parameters, aggregation
) -> None:
    annual.relative_humidity_percent[0, 0, 0] = np.nan
    annual.uv_dose_kwh_m2[:, 1, 1] = np.nan
    result = map_degradation(annual, parameters, aggregation=aggregation)
    assert result.valid_year_count[0, 0] == 2
    assert result.valid_year_count[1, 1] == 0
    for name in RATE_VARIABLES:
        assert np.isnan(result[name][0, 0])
        assert np.isnan(result[name][1, 1])
        assert np.isfinite(result[name][0, 1])
    assert result.rate_class[0, 0] == 0


@pytest.mark.parametrize(
    "years", [[2016, 2018, 2019], [2016, 2016, 2017], [2018, 2017, 2016], [2016.0, 2017.0, 2018.0]]
)
def test_annual_years_must_be_consecutive_unique_integer(annual, parameters, years) -> None:
    with pytest.raises(ValueError, match="Years"):
        map_degradation(annual.assign_coords(year=years), parameters, aggregation="mean_stress")


def test_invalid_annual_values_cannot_hide_in_means(annual, parameters) -> None:
    annual.relative_humidity_percent[0, 0, 0] = -1
    with pytest.raises(ValueError, match="humidity"):
        map_degradation(annual, parameters, aggregation="mean_stress")


def test_grid_normalization_units_and_assumptions(annual, parameters) -> None:
    reordered = annual.assign_coords(lon=[0, 300]).isel(lat=[1, 0])
    result = map_degradation(reordered, parameters, aggregation="mean_stress")
    np.testing.assert_array_equal(result.lon.values, [-60, 0])
    np.testing.assert_array_equal(result.lat.values, [0, 60])
    annual.attrs.clear()
    with pytest.raises(ValueError, match="stress_convention"):
        map_degradation(annual, parameters, aggregation="mean_stress")
    annual.attrs["stress_convention"] = "synthetic"
    annual.uv_dose_kwh_m2.attrs["units"] = "W m-2"
    with pytest.raises(ValueError, match="units"):
        map_degradation(annual, parameters, aggregation="mean_stress")


def test_thesis_bins_boundaries_nodata_and_overflow() -> None:
    values = xr.DataArray(
        [0, 0.2, 0.4, 0.6, 0.8, 1, 1.2, 1.4, 1.4001, np.nan], attrs={"units": RATE_UNITS}
    )
    global_map = degradation_classes(values, region="global")
    np.testing.assert_array_equal(global_map.values, [1, 1, 2, 3, 4, 5, 6, 7, 8, 0])
    np.testing.assert_array_equal(
        degradation_classes(values, region="europe").values, [1, 1, 2, 3, 4, 5, 5, 5, 5, 0]
    )
    assert json.loads(global_map.attrs["class_labels"])["8"] == ">1.4"
    with pytest.raises(ValueError, match="units"):
        degradation_classes(values.assign_attrs(units="year-1"), region="global")
    with pytest.raises(ValueError, match="nonnegative"):
        degradation_classes(xr.DataArray([-0.1], attrs={"units": RATE_UNITS}), region="global")


def test_kgpv_summary_uses_cell_area_and_exact_alignment(annual, parameters) -> None:
    result = map_degradation(annual, parameters, aggregation="mean_stress")
    for name in RATE_VARIABLES:
        result[name].values[:] = [[1, 1], [3, 3]]
    kgpv = xr.full_like(result.rate_class, 1)
    summary = kgpv_degradation_summary(result, kgpv)
    # Equatorial band -30..30 has twice the area of 30..90.
    assert summary.total_rate.sel(kgpv_zone="AH") == pytest.approx(5 / 3)
    assert summary.valid_cell_count.sel(kgpv_zone="AH") == 4
    assert summary.valid_area_km2.sel(kgpv_zone="AH") > 0
    assert np.isnan(summary.total_rate.sel(kgpv_zone="AK"))
    assert summary.valid_area_km2.sel(kgpv_zone="AK") == 0
    with pytest.raises(ValueError, match="align"):
        kgpv_degradation_summary(result, kgpv.assign_coords(lon=[1, 61]))
    with pytest.raises(ValueError, match="KGPV class"):
        kgpv_degradation_summary(result, kgpv.astype(float) + 0.5)
    result.hydrolysis_rate[0, 0] = np.nan
    kgpv[1, 1] = 0
    summary = kgpv_degradation_summary(result, kgpv)
    assert summary.valid_cell_count.sel(kgpv_zone="AH") == 2


@pytest.mark.integration
def test_cli_netcdf_geojson_manifest_and_kgpv(tmp_path: Path, annual, parameters) -> None:
    source = tmp_path / "stresses.nc"
    calibration = tmp_path / "parameters.json"
    climate = tmp_path / "kgpv.nc"
    output = tmp_path / "output"
    annual.to_netcdf(source, engine="scipy")
    calibration.write_text(json.dumps(parameters.to_dict()), encoding="utf-8")
    grid = xr.full_like(annual.module_temperature_mean_c.isel(year=0, drop=True), 1).rename(
        "kgpv_class"
    )
    climate_dataset = grid.to_dataset()
    climate_dataset.attrs.update(baseline_start_year=1991, baseline_end_year=2020)
    climate_dataset.to_netcdf(climate, engine="scipy")
    command = [
        sys.executable,
        "-m",
        "energy_methods.degradation_cli",
        "--stresses",
        str(source),
        "--parameters",
        str(calibration),
        "--aggregation",
        "mean_stress",
        "--kgpv",
        str(climate),
        "--geojson",
        "--output",
        str(output),
    ]
    run = subprocess.run(command, capture_output=True, text=True, check=False)
    assert run.returncode == 0, run.stdout + run.stderr
    with xr.open_dataset(output / "degradation.nc") as result:
        xr.testing.assert_allclose(
            result, map_degradation(annual, parameters, aggregation="mean_stress")
        )
        assert result.total_rate.attrs["units"] == RATE_UNITS
    with xr.open_dataset(output / "degradation_by_kgpv.nc") as summary:
        assert summary.sizes["kgpv_zone"] == 12
        metadata = json.loads(summary.attrs["kgpv_metadata"])
        assert int(metadata["baseline_start_year"]) == 1991
        assert int(metadata["baseline_end_year"]) == 2020
    manifest = json.loads((output / "manifest.json").read_text())
    assert len(manifest["inputs"]) == 3
    assert all(len(record["sha256"]) == 64 for record in manifest["inputs"])
    assert manifest["references"][0]["id"] == "ascencio_vasquez_2021_thesis"
    assert manifest["parameters"] == parameters.to_dict()
    for name in (*RATE_VARIABLES, "rate_class"):
        geojson = json.loads((output / f"{name}.geojson").read_text())
        assert len(geojson["features"]) == 4
    annual.relative_humidity_percent.attrs["units"] = "1"
    annual.to_netcdf(source, engine="scipy")
    failed = subprocess.run(command, capture_output=True, text=True, check=False)
    assert failed.returncode == 2
    assert "units" in failed.stderr
