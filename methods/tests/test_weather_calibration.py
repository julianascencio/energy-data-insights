"""Bias recovery, train/holdout separation and unsupported spatial predictions."""

import numpy as np
import pandas as pd
import pytest

from energy_methods.weather_calibration import correct_hourly, fit_monthly_bias, spatial_weights


def test_known_bias_and_holdout_isolation():
    dates = pd.date_range("2022-01-01", "2023-12-31")
    data = pd.DataFrame(
        {
            "date": dates,
            "variable": "temperature_c",
            "modelled": 10.0,
            "observed": np.where(dates.year == 2022, 13.0, 99.0),
        }
    )
    fitted = fit_monthly_bias(data, year=2022)
    assert len(fitted) == 12
    np.testing.assert_allclose(fitted.value, 3)
    data.loc[data.date.dt.month == 4, "observed"] = np.nan
    assert fit_monthly_bias(data, year=2022).empty


def test_spatial_support_and_exclusion():
    w = spatial_weights(np.array([[0, 0], [10000, 0]]), np.array([[5000, 0], [200000, 0]]))
    np.testing.assert_allclose(w, [[0.5, 0.5], [0, 0]])
    with pytest.raises(ValueError):
        spatial_weights(np.array([[np.nan, 0]]), np.array([[0, 0]]))


def test_hourly_bounds_and_irradiance_preservation():
    weather = pd.DataFrame(
        {
            "temperature_c": [10.0],
            "relative_humidity_percent": [98.0],
            "wind_speed_ms": [3.0],
            "ghi_wm2": [100.0],
        },
        index=pd.date_range("2023-01-01", periods=1, tz="UTC"),
    )
    result = correct_hourly(
        weather,
        {
            "temperature_c": np.ones(12) * 2,
            "relative_humidity_percent": np.ones(12) * 5,
            "wind_speed_ms": np.ones(12) * 2,
        },
    )
    assert result.iloc[0].to_dict() == {
        "temperature_c": 12.0,
        "relative_humidity_percent": 100.0,
        "wind_speed_ms": 6.0,
        "ghi_wm2": 100.0,
    }
    assert result.attrs["rh_clipped_hours"] == 1
    assert weather.iloc[0].temperature_c == 10
