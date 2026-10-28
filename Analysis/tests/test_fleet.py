"""Regression tests for energy accounting and coverage, independent of model fitting."""

import numpy as np
import pandas as pd
import pytest

from energy_analysis.chile_fleet.fleet import ComparisonConfig, compare_site, summarize_fleet


def test_zeros_missing_negatives_and_reference_coverage() -> None:
    frame = pd.DataFrame({"actual_mwh": [0, np.nan, -2, 12], "expected_mwh": [10, 20, 30, 10]})
    result = compare_site(frame)
    assert result["matched_actual_mwh"] == 12
    assert result["matched_expected_mwh"] == 20
    assert result["reference_energy_coverage"] == pytest.approx(20 / 70)
    assert result["reported_zero_hours"] == 1
    assert result["negative_or_infinite_actual_hours"] == 1
    assert result["comparison_supported"] is False
    assert result["deviation_pct"] is None


def test_site_net_gaps_do_not_equal_hourly_gaps() -> None:
    first = compare_site(pd.DataFrame({"actual_mwh": [0, 30], "expected_mwh": [10, 10]}))
    second = compare_site(pd.DataFrame({"actual_mwh": [0, 0], "expected_mwh": [4, 6]}))
    absent = compare_site(pd.DataFrame({"actual_mwh": [np.nan], "expected_mwh": [5]}))
    summary = summarize_fleet(pd.DataFrame([first, second, absent]))
    assert summary["registry_records"] == 3
    assert summary["comparable_records"] == 2
    assert summary["matched_actual_mwh"] == summary["matched_expected_mwh"] == 30
    assert summary["site_excess_mwh"] == summary["site_shortfall_mwh"] == 10
    assert summary["hourly_shortfall_mwh"] == summary["hourly_excess_mwh"] == 20


def test_zero_reference_and_empty_site_are_unscorable() -> None:
    for frame in (
        pd.DataFrame({"actual_mwh": [0.0], "expected_mwh": [0.0]}),
        pd.DataFrame({"actual_mwh": [], "expected_mwh": []}),
    ):
        assert compare_site(frame)["comparison_supported"] is False


def test_exact_tolerance_boundary_is_inside() -> None:
    for actual in [8, 12]:
        result = compare_site(pd.DataFrame({"actual_mwh": [actual], "expected_mwh": [10]}))
        assert result["performance_group"] == "within_tolerance"


def test_weather_averages_are_over_valid_hours_with_negative_temperature_valid() -> None:
    frame = pd.DataFrame(
        {
            "actual_mwh": [1, 1, 1],
            "expected_mwh": [1, 1, 1],
            "temperature_c": [-5, 5, np.nan],
            "wind_speed_ms": [-1, 2, 4],
        }
    )
    result = compare_site(frame)
    assert result["temperature_c_average"] == 0
    assert result["wind_speed_ms_average"] == 3
    assert result["wind_speed_ms_valid_hours"] == 2


@pytest.mark.parametrize("coverage,tolerance", [(np.nan, 0.2), (0.8, np.nan), (1.1, 0.2), (0.8, 1)])
def test_invalid_comparison_configuration(coverage: float, tolerance: float) -> None:
    with pytest.raises(ValueError):
        ComparisonConfig(coverage, tolerance)
