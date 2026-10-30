"""Hand-calculated thesis equations, boundaries, calendar and masking checks."""

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from energy_methods.weather_risk import (
    snow_loss_from_exposure,
    snow_risk_classes,
    soiling_rate_from_aod,
    soiling_risk_classes,
)
from energy_methods.weather_risk_mapping import annual_risk_inputs, map_weather_risks


def test_equations_and_explicit_boundary_extensions():
    np.testing.assert_allclose(
        soiling_rate_from_aod([0, 0.05, 0.106, 0.2, np.nan]),
        [0, 0.0324, 0.068688, 0.696, np.nan],
    )
    np.testing.assert_allclose(
        snow_loss_from_exposure([0, 0.1, 1, np.exp(4), np.exp(5), np.exp(10), np.nan]),
        [0, 0, 0, 0.1052, 0.1315, 6.9, np.nan],
    )
    assert snow_loss_from_exposure(np.exp(5 + 1e-8)) > 0.19  # Printed jump is retained.
    assert soiling_rate_from_aod(0.106 + 1e-8) > 0.072
    # The thesis fit is unbounded; extrapolation is not silently clipped to 100%.
    assert snow_loss_from_exposure(np.exp(30)) > 100


@pytest.mark.parametrize(
    "function",
    [soiling_rate_from_aod, snow_loss_from_exposure, soiling_risk_classes, snow_risk_classes],
)
@pytest.mark.parametrize("bad", [-0.001, np.inf, -np.inf])
def test_invalid_inputs_fail(function, bad):
    with pytest.raises(ValueError):
        function([0, bad, np.nan])


def test_five_classes_and_upper_inclusive_edges():
    for classify, edges in (
        (soiling_risk_classes, [0.05, 0.1, 0.2, 0.4]),
        (snow_risk_classes, [2, 4, 7, 10]),
    ):
        assert classify([np.nan, 0, *edges, edges[-1] + 0.01]).tolist() == [0, 1, 1, 2, 3, 4, 5]
        assert classify(np.array(edges) + 1e-7).tolist() == [2, 3, 4, 5]


def fields(year=2024):
    coords = {"lat": [40, 45], "lon": [0, 5]}
    daily = pd.date_range(f"{year}-01-01", f"{year + 1}-01-01", freq="D", inclusive="left")
    hourly = pd.date_range(f"{year}-01-01", f"{year + 1}-01-01", freq="h", inclusive="left")
    aod = xr.DataArray(
        np.full((len(daily), 2, 2), 0.2),
        dims=("time", "lat", "lon"),
        coords={**coords, "time": daily},
        attrs={"units": "1", "wavelength_nm": 550, "time_zone": "UTC"},
    )
    snow = xr.DataArray(
        np.full((len(hourly), 2, 2), 2.0),
        dims=("time", "lat", "lon"),
        coords={**coords, "time": hourly},
        attrs={"units": "cm", "snow_depth_kind": "physical_ground", "time_zone": "UTC"},
    )
    return aod, snow


def test_leap_year_sampling_and_missing_indicators_stay_independent():
    aod, snow = fields()
    aod[0, 0, 0] = np.nan
    snow[0, 1, 1] = np.nan
    annual = annual_risk_inputs(aod, snow, year=2024)
    assert annual.valid_aod_days[0, 0, 0] == 365
    assert annual.valid_snow_hours[0, 1, 1] == 8783
    assert annual.snow_depth_sum[0, 0, 0] == 2 * 8784
    assert annual.aod550_mean[0, 1, 1] == pytest.approx(0.2)
    maps = map_weather_risks(annual)
    assert maps.soiling_risk[0, 0] == 0 and maps.snow_risk[0, 0] > 0
    assert maps.soiling_risk[1, 1] > 0 and maps.snow_risk[1, 1] == 0


def test_incomplete_calendar_units_and_water_equivalent_are_rejected():
    aod, snow = fields()
    with pytest.raises(ValueError, match="complete"):
        annual_risk_inputs(aod.isel(time=slice(1, None)), snow, year=2024)
    with pytest.raises(ValueError, match="complete"):
        annual_risk_inputs(aod, snow.isel(time=slice(None, None, -1)), year=2024)
    with pytest.raises(ValueError, match="align"):
        annual_risk_inputs(aod, snow.assign_coords(lon=[0, 6]), year=2024)
    with pytest.raises(ValueError, match="units"):
        annual_risk_inputs(aod, snow.assign_attrs(units="m"), year=2024)
    with pytest.raises(ValueError, match="physical_ground"):
        annual_risk_inputs(aod, snow.assign_attrs(snow_depth_kind="water_equivalent"), year=2024)
    with pytest.raises(ValueError, match="wavelength"):
        annual_risk_inputs(aod.assign_attrs(wavelength_nm=500), snow, year=2024)


def test_multiyear_nonlinearity_and_strict_missing_years():
    aod, snow = fields(2023)
    first = annual_risk_inputs(aod, snow, year=2023)
    second = first.copy(deep=True).assign_coords(year=[2024])
    first.aod550_mean[:] = 0.05
    second.aod550_mean[:] = 0.2
    first.snow_depth_sum[:] = 0
    second.snow_depth_sum[:] = np.exp(10)
    combined = xr.concat([first, second], dim="year")
    result = map_weather_risks(combined)
    np.testing.assert_allclose(result.soiling_rate, (0.0324 + 0.696) / 2)
    np.testing.assert_allclose(result.snow_loss, 3.45)
    assert result.attrs["baseline_end_year"] == 2024
    combined.aod550_mean[1, 0, 0] = np.nan
    assert map_weather_risks(combined).soiling_risk[0, 0] == 0
    with pytest.raises(ValueError, match="consecutive"):
        map_weather_risks(combined.assign_coords(year=[2023, 2025]))
