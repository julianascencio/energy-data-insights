"""Temporal contracts, complete-year integration and no gap imputation."""

import numpy as np
import pandas as pd
import pytest

from energy_methods.degradation_preprocessing import annual_stress_summary, prepare_power_trend


def hourly_weather():
    index = pd.date_range("2024-01-01", "2025-01-01", inclusive="left", freq="h", tz="UTC")
    day = (index.hour >= 6) & (index.hour < 18)
    return pd.DataFrame(
        {
            "module_temperature_c": np.where(day, 30.0, 10.0),
            "relative_humidity_percent": np.where(day, 50.0, 80.0),
            "uv_irradiance_w_m2": np.where(day, 100.0, 0.0),
            "poa_w_m2": np.where(day, 1000.0, 0.0),
        },
        index=index,
    )


def test_annual_daytime_percentiles_and_leap_year_uv_integration():
    result = annual_stress_summary(hourly_weather(), year=2024, cycles_per_year=365)
    assert result["module_temperature_mean_c"] == 30
    assert result["module_temperature_lower_c"] == 30
    assert result["module_temperature_upper_c"] == 30
    assert result["relative_humidity_percent"] == 50
    assert result["uv_dose_kwh_m2"] == pytest.approx(366 * 12 * 100 / 1000)
    assert result["cycles_per_year"] == 365


def test_incomplete_duplicate_and_missing_weather_fail():
    frame = hourly_weather()
    for bad in [
        frame.iloc[1:],
        pd.concat([frame.iloc[:1], frame]),
        frame.assign(module_temperature_c=np.nan),
    ]:
        with pytest.raises(ValueError):
            annual_stress_summary(bad, year=2024, cycles_per_year=365)
    with pytest.raises(ValueError, match="UTC"):
        annual_stress_summary(frame.tz_localize(None), year=2024, cycles_per_year=365)


def test_power_filter_corrects_irradiance_but_not_temperature_and_preserves_age():
    index = pd.date_range("2020-01-01", periods=48, freq="MS", tz="UTC")
    frame = pd.DataFrame({"power_w": 90.0, "poa_w_m2": 900.0}, index=index)
    frame.loc[index[1], "power_w"] = 900  # sigma outlier
    frame.loc[index[2], "poa_w_m2"] = 700  # irradiance exclusion
    origin = pd.Timestamp("2019-01-01", tz="UTC")
    result = prepare_power_trend(frame, age_origin=origin, window_months=3)
    np.testing.assert_allclose(result.trend_power_w.dropna(), 100)
    np.testing.assert_allclose(result.normalized_power.dropna(), 1)
    assert result.age_years.min() > 1
    assert result.attrs["input_count"] == 48
    assert result.attrs["irradiance_selected_count"] == 47
    assert result.attrs["sigma_selected_count"] == 46
    assert result.attrs["temperature_corrected"] is False
    assert result.trend_power_w.isna().sum() >= 4


def test_power_gap_is_not_filled_and_bad_origins_fail():
    index = pd.date_range("2020-01-01", periods=48, freq="MS", tz="UTC")
    frame = pd.DataFrame({"power_w": 100.0, "poa_w_m2": 1000.0}, index=index).drop(index[20])
    result = prepare_power_trend(frame, age_origin=index[0], window_months=3)
    assert result.loc["2021-09-01":"2021-09-30", "trend_power_w"].isna().all()
    with pytest.raises(ValueError):
        prepare_power_trend(frame, age_origin=pd.Timestamp("2020-01-01"))
