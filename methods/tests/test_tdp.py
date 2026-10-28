"""Pooled empirical profiles, independent month gates and reported-zero retention."""

import numpy as np
import pandas as pd
import pytest

from energy_methods.tdp import TDPConfig, analyze_tdp


def test_avg_pools_original_hours_instead_of_annual_quantiles() -> None:
    times = pd.date_range("2024-01-01", periods=15 * 24, freq="h", tz="UTC").append(
        pd.date_range("2025-01-01", periods=30 * 24, freq="h", tz="UTC")
    )
    frame = pd.DataFrame(
        {
            "site_id": "synthetic",
            "timestamp": times,
            "actual_mwh": np.repeat([1.0, 3.0], [15 * 24, 30 * 24]),
        }
    )
    result = analyze_tdp(frame)
    assert result.avg["n"].eq(45).all()
    assert result.avg["p50"].eq(3).all()
    assert result.avg["p90"].eq(3).all()
    assert result.y2y.groupby("year")["p50"].first().tolist() == [1.0, 3.0]
    assert (
        result.coverage.loc[0, "positive_flat_screen"] == "unavailable_no_complete_solar_elevation"
    )


def test_positive_flat_screen_retains_zero_days_and_rejects_incomplete_days() -> None:
    times = pd.date_range("2026-01-01", periods=17 * 24, freq="h", tz="UTC")
    hours = np.asarray(times.hour)
    daylight = (hours >= 7) & (hours <= 18)
    output = np.maximum(np.sin((hours - 6) / 12 * np.pi), 0)
    output[:24] = np.where(daylight[:24], 5.0, 0.0)
    output[24:48] = 0
    output[48] = np.nan
    frame = pd.DataFrame(
        {
            "site_id": "synthetic",
            "timestamp": times,
            "actual_mwh": output,
            "solar_elevation_deg": np.where(daylight, 30, -20),
        }
    )
    result = analyze_tdp(frame)
    audit = result.coverage.iloc[0]
    assert audit["positive_flat_days_removed"] == 1
    assert audit["flat_zero_days_retained"] == 1
    assert audit["qualified_days"] == 15
    assert audit["qualified_hours"] == 360
    assert result.avg["n"].eq(15).all()


def test_month_gate_is_applied_before_multi_year_pooling() -> None:
    times = pd.date_range("2024-01-01", periods=14 * 24, freq="h", tz="UTC").append(
        pd.date_range("2025-01-01", periods=14 * 24, freq="h", tz="UTC")
    )
    frame = pd.DataFrame({"site_id": "synthetic", "timestamp": times, "actual_mwh": 0.0})
    result = analyze_tdp(frame)
    assert result.avg["n"].eq(0).all()
    assert result.avg["p50"].isna().all()
    assert result.avg["raw_n"].eq(28).all()
    assert result.avg["raw_p50"].eq(0).all()


def test_zero_only_month_and_negative_ambient_temperature_are_valid() -> None:
    times = pd.date_range("2026-01-01", periods=16 * 24, freq="h", tz="UTC")
    frame = pd.DataFrame(
        {"site_id": "synthetic", "timestamp": times, "actual_mwh": 0.0, "temperature_c": -5.0}
    )
    zeros = analyze_tdp(frame)
    assert zeros.avg["p50"].eq(0).all()
    assert zeros.coverage.loc[0, "qualified_hours"] == 384
    weather = analyze_tdp(
        frame,
        TDPConfig(value_column="temperature_c", nonnegative=False, screen_positive_flat=False),
    )
    assert weather.avg["p50"].eq(-5).all()


def test_fixed_offset_is_applied_before_year_and_month_grouping() -> None:
    times = pd.date_range("2026-01-01T00:00Z", periods=4, freq="h")
    frame = pd.DataFrame({"site_id": "synthetic", "timestamp": times, "actual_mwh": 1.0})
    result = analyze_tdp(
        frame,
        TDPConfig(
            utc_offset_hours=-4, min_useful_days=1, min_hours_per_day=4, min_bin_observations=1
        ),
    )
    assert set(result.y2y["year"]) == {2025}
    assert set(result.y2y["month"]) == {12}
    assert result.y2y.loc[result.y2y["n"] > 0, "hour"].tolist() == [20, 21, 22, 23]


def test_duplicate_and_naive_timestamps_are_rejected() -> None:
    frame = pd.DataFrame(
        {
            "site_id": ["synthetic"] * 2,
            "timestamp": pd.to_datetime(["2026-01-01Z".replace("Z", "T00:00Z")] * 2),
            "actual_mwh": [0, 0],
        }
    )
    with pytest.raises(ValueError, match="unique"):
        analyze_tdp(frame)
    frame["timestamp"] = pd.date_range("2026-01-01", periods=2, freq="h")
    with pytest.raises(ValueError, match="timezone-aware"):
        analyze_tdp(frame)
