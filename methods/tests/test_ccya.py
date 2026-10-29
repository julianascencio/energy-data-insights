"""Independent synthetic CCYA checks; no Bolzano reproduction is claimed."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_allclose

from energy_methods.ccya import CCYAConfig, fit_ccya, fit_site_adaptation


def climate(start: int, years: int = 2, *, days_360: bool = False) -> pd.DataFrame:
    """Exactly repeating synthetic seasonality; calendar lengths are explicit."""
    index = pd.period_range(f"{start}-01", periods=12 * years, freq="M")
    month = index.month.to_numpy()
    return pd.DataFrame(
        {
            "ghi_wm2": 50.0 + 10 * month,
            "temperature_c": 2.0 + month,
            "days": 30 if days_360 else index.days_in_month,
        },
        index=index,
    )


def calibration() -> tuple[pd.DataFrame, pd.DataFrame]:
    # 2017-2018 are nonleap. Observed GHI=2*x+10; observed T=1.5*x+5.
    modelled = climate(2017)
    assert isinstance(modelled.index, pd.PeriodIndex)
    measured = modelled.copy()
    measured["ghi_wm2"] = 2 * modelled["ghi_wm2"] + 10
    measured["temperature_c"] = 1.5 * modelled["temperature_c"] + 5
    # Seasonal yield efficiency varies by month, testing twelve separate responses.
    measured["dc_yield_kwh_kwp"] = (
        modelled["ghi_wm2"] * (0.02 + modelled.index.month.to_numpy() / 1000) * measured["days"]
    )
    return measured, modelled


def test_site_adaptation_recovers_known_affine_map() -> None:
    fit = fit_site_adaptation([1, 2, 3, 4], [7, 9, 11, 13])
    assert fit.slope == pytest.approx(2)
    assert fit.intercept == pytest.approx(5)
    assert_allclose(fit.predict([0, 5]), [5, 15])
    assert fit.support([0, 1, 4, 5, np.nan]).tolist() == [False, True, True, False, False]


@pytest.mark.parametrize(
    ("x", "y"),
    [
        ([1, 1, 1], [1, 2, 3]),
        ([1, 2, 3], [3, 2, 1]),
        ([1, 2], [1, 2]),
        ([1, 2, 3], [1, np.nan, 3]),
        ([1, 2, 3], [1, 2]),
        ([[1, 2, 3]], [[1, 2, 3]]),
    ],
)
def test_site_adaptation_rejects_unsupported_pairs(x: list, y: list) -> None:
    with pytest.raises(ValueError):
        fit_site_adaptation(x, y)


def test_unchanged_climate_preserves_monthly_yield_and_has_zero_gain() -> None:
    measured, historical = calibration()
    model = fit_ccya(measured, historical)
    result = model.project(climate(2021), scenario="synthetic/model/member")
    assert_allclose(result.monthly["combined_kwh_kwp"], measured["dc_yield_kwh_kwp"])
    assert_allclose(result.monthly["temperature_factor"], 1)
    assert_allclose(result.annual["combined_cumulative_gain_p50_pct"], 0, atol=1e-12)
    assert_allclose(result.annual["combined_cumulative_ratio_p50_pct"], 100)
    assert not result.monthly["outside_calibration_support"].any()
    assert result.annual["combined_rolling_mean_kwh_kwp"].isna().all()


def test_warming_uses_adapted_temperature_without_double_counting_baseline() -> None:
    measured, historical = calibration()
    model = fit_ccya(measured, historical)
    future = climate(2021)
    future["temperature_c"] += 2
    result = model.project(future, scenario="synthetic/warming")
    # Climate-model +2 C becomes +3 C after the known site-adaptation slope 1.5.
    assert_allclose(result.monthly["temperature_factor"], 1 - 0.0045 * 3)
    assert_allclose(result.annual["combined_cumulative_gain_p50_pct"], -1.35)
    assert_allclose(result.annual["irradiance_cumulative_gain_p50_pct"], 0, atol=1e-12)


def test_brightening_and_ross_heating_are_separate() -> None:
    measured, historical = calibration()
    model = fit_ccya(measured, historical)
    future = climate(2021)
    original_ghi = future["ghi_wm2"].to_numpy().copy()
    future["ghi_wm2"] *= 1.1
    result = model.project(future, scenario="synthetic/brightening")
    assert_allclose(result.monthly["irradiance_kwh_kwp"], measured["dc_yield_kwh_kwp"] * 1.1)
    # The adapted GHI change is 2*(0.1*raw GHI), not 0.1*(2*raw GHI+10).
    assert_allclose(result.monthly["temperature_factor"], 1 - 0.0045 * 0.03 * 0.2 * original_ghi)
    assert_allclose(result.annual["irradiance_cumulative_gain_p50_pct"], 10)
    assert result.monthly["outside_calibration_support"].all()


def test_linear_degradation_and_cumulative_denominator_use_operating_year_count() -> None:
    measured, historical = calibration()
    model = fit_ccya(measured, historical)
    result = model.project(climate(2021), scenario="synthetic", degradation_per_year=0.01)
    assert_allclose(result.monthly["power_factor"], [1] * 12 + [0.99] * 12)
    assert_allclose(result.annual["combined_cumulative_gain_p50_pct"], [0, -0.5], atol=1e-12)
    older = model.project(
        climate(2021), scenario="synthetic/aged", degradation_per_year=0.01, age_at_start_years=5
    )
    assert_allclose(older.annual["combined_cumulative_gain_p50_pct"], [-5, -5.5])


def test_custom_power_curve_and_combined_accounting() -> None:
    measured, historical = calibration()
    model = fit_ccya(measured, historical)
    future = climate(2021)
    future["temperature_c"] += 2
    power = pd.Series([0.98] * 12 + [0.95] * 12, index=future.index)
    result = model.project(future, scenario="synthetic", power_factors=power)
    base = result.monthly["irradiance_kwh_kwp"]
    assert_allclose(result.monthly["irradiance_power_kwh_kwp"], base * power)
    assert_allclose(result.monthly["combined_kwh_kwp"], base * power * 0.9865)
    assert result.metadata["power_model"] == "supplied_monthly"
    with pytest.raises(ValueError, match="either"):
        model.project(future, scenario="s", power_factors=power, degradation_per_year=0.01)
    with pytest.raises(ValueError, match="exactly"):
        model.project(future, scenario="s", power_factors=power.iloc[::-1])
    power.iloc[0] = np.nan
    with pytest.raises(ValueError, match="Power-retention"):
        model.project(future, scenario="s", power_factors=power)


def test_historical_percentiles_are_nonexceedance_and_do_not_pool_scenarios() -> None:
    measured, historical = calibration()
    first_year = measured.iloc[:12]["dc_yield_kwh_kwp"].sum()
    assert isinstance(measured.index, pd.PeriodIndex)
    measured["dc_yield_kwh_kwp"] *= np.where(measured.index.year == 2018, 2, 1)
    model = fit_ccya(measured, historical)
    result = model.project(climate(2021), scenario="synthetic")
    for label, multiplier in [("p10", 1.1), ("p50", 1.5), ("p90", 1.9)]:
        assert_allclose(result.annual[f"measured_{label}_kwh_kwp"], first_year * multiplier)
    assert (result.annual["combined_cumulative_gain_p10_pct"] > 0).all()
    assert (result.annual["combined_cumulative_gain_p90_pct"] < 0).all()


def test_native_calendar_days_control_energy_and_rolling_window() -> None:
    measured, historical = calibration()
    model = fit_ccya(measured, historical, config=CCYAConfig(rolling_years=2))
    result = model.project(climate(2021, days_360=True), scenario="synthetic/360_day")
    expected = sum((50 + 10 * m) * (0.02 + m / 1000) * 30 for m in range(1, 13))
    assert_allclose(result.annual["combined_kwh_kwp"], expected)
    assert np.isnan(result.annual["combined_rolling_mean_kwh_kwp"].iloc[0])
    assert result.annual["combined_rolling_mean_kwh_kwp"].iloc[1] == pytest.approx(expected)
    # Gregorian leap-day energy is preserved, without changing the monthly fit.
    leap = model.project(climate(2020, years=1), scenario="synthetic/leap")
    base = measured.iloc[:12]["dc_yield_kwh_kwp"].sum()
    assert leap.annual["combined_kwh_kwp"].iloc[0] == pytest.approx(base + 70 * 0.022)
    # Historical model and measured calendars need not have equal month lengths.
    native = historical.copy()
    native["days"] = 30
    other = fit_ccya(measured, native)
    assert_allclose(other.daily_yield_per_ghi, model.daily_yield_per_ghi)


def test_ten_year_trailing_window_requires_ten_complete_years() -> None:
    measured, historical = calibration()
    model = fit_ccya(measured, historical)
    result = model.project(climate(2020, years=12, days_360=True), scenario="synthetic")
    rolling = result.annual["irradiance_rolling_mean_kwh_kwp"]
    assert rolling.iloc[:9].isna().all()
    assert_allclose(rolling.iloc[9:], result.annual["irradiance_kwh_kwp"].iloc[0])


def test_fitted_state_is_independent_and_serializable() -> None:
    measured, historical = calibration()
    model = fit_ccya(measured, historical)
    before = model.to_dict()
    measured.loc[:, "dc_yield_kwh_kwp"] = 1
    assert model.to_dict() == before
    json.dumps(before, allow_nan=False)
    with pytest.raises(ValueError, match="read-only"):
        model.daily_yield_per_ghi[0] = 0
    exported = model.to_dict()
    coefficients = exported["daily_yield_per_ghi"]
    assert isinstance(coefficients, list)
    coefficients[0] = -999
    assert model.daily_yield_per_ghi[0] > 0


@pytest.mark.parametrize("column", ["ghi_wm2", "temperature_c", "days", "dc_yield_kwh_kwp"])
@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
def test_missing_values_are_never_zero_filled(column: str, bad: float) -> None:
    measured, historical = calibration()
    measured[column] = measured[column].astype(float)
    measured.loc[measured.index[0], column] = bad
    with pytest.raises(ValueError, match="missing or infinite"):
        fit_ccya(measured, historical)


def test_incomplete_duplicate_unsorted_and_nonmonthly_inputs_fail() -> None:
    measured, historical = calibration()
    for bad in (measured.iloc[1:], measured.iloc[::-1], pd.concat([measured, measured.iloc[:1]])):
        with pytest.raises(ValueError):
            fit_ccya(bad, historical)
    timestamped = measured.copy()
    assert isinstance(timestamped.index, pd.PeriodIndex)
    timestamped.index = timestamped.index.to_timestamp()
    with pytest.raises(ValueError, match="PeriodIndex"):
        fit_ccya(timestamped, historical)
    with pytest.raises(ValueError, match="overlap"):
        fit_ccya(measured, climate(2016))
    with pytest.raises(ValueError, match="Insufficient"):
        fit_ccya(measured.iloc[:12], historical.iloc[:12])


def test_bad_units_zero_resource_and_nonphysical_weather_fail() -> None:
    measured, historical = calibration()
    for column, value in [
        ("ghi_wm2", -1),
        ("dc_yield_kwh_kwp", -1),
        ("temperature_c", -274),
        ("days", 27),
        ("days", 30.5),
    ]:
        bad = measured.astype(float).copy()
        bad.loc[bad.index[0], column] = value
        with pytest.raises(ValueError):
            fit_ccya(bad, historical)
    bad_calendar = measured.copy()
    bad_calendar.loc[bad_calendar.index[0], "days"] = 28
    with pytest.raises(ValueError, match="calendar"):
        fit_ccya(bad_calendar, historical)
    assert isinstance(historical.index, pd.PeriodIndex)
    historical.loc[historical.index.month == 1, "ghi_wm2"] = 0
    with pytest.raises(ValueError, match="positive modelled GHI centroid"):
        fit_ccya(measured, historical)
    measured, historical = calibration()
    measured["dc_yield_kwh_kwp"] = 0
    with pytest.raises(ValueError, match="annual yield"):
        fit_ccya(measured, historical)


def test_reported_zero_monthly_yield_is_retained() -> None:
    measured, historical = calibration()
    assert isinstance(measured.index, pd.PeriodIndex)
    measured.loc[measured.index.month == 1, "dc_yield_kwh_kwp"] = 0
    model = fit_ccya(measured, historical)
    result = model.project(climate(2021), scenario="synthetic")
    assert result.monthly.loc["2021-01", "combined_kwh_kwp"] == 0


def test_projection_rejects_calibration_leakage_and_impossible_factors() -> None:
    measured, historical = calibration()
    model = fit_ccya(measured, historical)
    with pytest.raises(ValueError, match="after the calibration"):
        model.project(historical, scenario="synthetic")
    for rate in [-0.01, 1.1, np.nan, np.inf]:
        with pytest.raises(ValueError):
            model.project(climate(2021), scenario="synthetic", degradation_per_year=rate)
    with pytest.raises(ValueError, match="Power-retention"):
        model.project(climate(2021, years=3), scenario="synthetic", degradation_per_year=0.75)
    future = climate(2021)
    future["temperature_c"] = 1000
    with pytest.raises(ValueError, match="Temperature multiplier"):
        model.project(future, scenario="synthetic")
    with pytest.raises(ValueError, match="identifier"):
        model.project(climate(2021), scenario=" ")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"gamma_per_c": 0.45},
        {"ross_c_m2_w": -1},
        {"gamma_per_c": np.nan},
        {"rolling_years": 0},
        {"rolling_years": 1.5},
        {"min_calibration_years": True},
    ],
)
def test_invalid_config_fails(kwargs: dict) -> None:
    with pytest.raises(ValueError):
        CCYAConfig(**kwargs)
