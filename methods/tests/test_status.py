"""Recovered status boundaries, precedence and missing-hour persistence."""

import numpy as np
import pandas as pd
import pytest

from energy_methods.status import classify_status


def test_all_ten_states_with_fixed_expected_outcomes() -> None:
    actual = [np.nan, -1, 0, 0, 1, 0, 1, 7, 10, 13]
    expected = [10, 10, 10, 10, 10, np.nan, np.nan, 10, 10, 10]
    ghi = [500, 500, 0, 50, 50, 500, 500, 500, 500, 500]
    elevation = [30, 30, -10, 2, 2, 30, 30, 30, 30, 30]
    result = classify_status(
        actual,
        expected,
        ghi,
        elevation,
        training_scale_mwh=10,
        weather_supported=np.ones(10, dtype=bool),
    )
    assert result.codes.tolist() == list(range(10))
    assert result.assigned_iec_category == "INFORMATION UNAVAILABLE"
    assert result.confirmed_cause is False


def test_trace_resource_precedes_expected_and_training_support() -> None:
    result = classify_status(
        [0, 1e-5, 0, 0],
        [np.nan] * 4,
        [500, 500, np.nan, 2],
        [30, 30, 30, -1],
        weather_supported=np.zeros(4, dtype=bool),
    )
    assert result.codes.tolist() == [5, 5, 6, 3]


def test_absolute_envelope_and_exact_boundaries() -> None:
    result = classify_status(
        [7.49, 7.5, 12.5, 12.51],
        [10] * 4,
        [500] * 4,
        [30] * 4,
        training_scale_mwh=50,
        weather_supported=np.ones(4, dtype=bool),
    )
    assert result.codes.tolist() == [7, 8, 8, 9]
    np.testing.assert_allclose(result.envelope_lower_mwh, 7.5)
    np.testing.assert_allclose(result.envelope_upper_mwh, 12.5)


def test_asymmetric_band_disagreement_and_near_zero() -> None:
    result = classify_status(
        [7, 13, 10, 7, 0.1],
        [10] * 5,
        [500] * 5,
        [30] * 5,
        training_scale_mwh=10,
        weather_supported=np.ones(5, dtype=bool),
        band_lower_mwh=[0, 0, 11, 0, 0],
        band_upper_mwh=[20, 20, 20, 5, 20],
    )
    assert result.model_band_disagree.tolist() == [False, False, True, True, False]
    assert result.near_zero.tolist() == [False, False, False, False, True]


def test_persistence_breaks_on_status_change_and_missing_elapsed_hour() -> None:
    times = pd.date_range("2026-10-01", periods=7, freq="h", tz="UTC").delete(5)
    result = classify_status(
        [0, 0, 6, 6, 0, 0],
        [10] * 6,
        [500] * 6,
        [30] * 6,
        training_scale_mwh=10,
        weather_supported=np.ones(6, dtype=bool),
        timestamps=times,
    )
    assert result.codes.tolist() == [5, 5, 7, 7, 5, 5]
    assert result.run_hours.tolist() == [2, 2, 2, 2, 1, 1]
    assert result.persistent.tolist() == [True, True, True, True, False, False]


def test_support_must_be_boolean_and_empty_arrays_are_allowed() -> None:
    with pytest.raises(ValueError, match="boolean"):
        classify_status([1], [1], [500], [30], weather_supported=[np.nan])
    result = classify_status([], [], [], [])
    assert not len(result.codes)
