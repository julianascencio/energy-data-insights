"""Radiometric closure, lag boundaries and holdout-label independence."""

import numpy as np
import pandas as pd
import pytest

from energy_methods.poa import (
    Geometry,
    fit_effective_poa,
    shift_weather,
    solar_elevation_midpoint,
    transpose_ghi,
)


def test_horizontal_plane_conserves_hourly_ghi() -> None:
    times = pd.date_range("2026-01-15T14:00Z", periods=4, freq="h")
    ghi = np.array([500.0, 700.0, 800.0, 650.0])
    result = transpose_ghi(times, ghi, -33.5, -70.6, Geometry(tilt_deg=0))
    np.testing.assert_allclose(result.poa_wm2, ghi, rtol=1e-12, atol=1e-10)
    np.testing.assert_allclose(
        result.solar_elevation_deg, solar_elevation_midpoint(times, -33.5, -70.6)
    )


def test_missing_ghi_stays_missing_and_night_is_not_extrapolated() -> None:
    times = pd.date_range("2026-01-15T02:00Z", periods=4, freq="h")
    result = transpose_ghi(times, [50, 0, np.nan, -1], -33.5, -70.6)
    assert result.poa_wm2[:2].tolist() == [0, 0]
    assert np.isnan(result.poa_wm2[2:]).all()
    np.testing.assert_allclose(shift_weather([1, 2, 3], 1), [np.nan, 1, 2], equal_nan=True)
    np.testing.assert_allclose(shift_weather([1, 2, 3], -1), [2, 3, np.nan], equal_nan=True)


def test_effective_geometry_and_lag_are_independent_of_holdout_labels() -> None:
    times = pd.date_range("2026-01-01", periods=12 * 24, freq="h", tz="UTC")
    elevation = solar_elevation_midpoint(times, -33.5, -70.6)
    ghi = np.maximum(np.sin(np.radians(elevation)), 0) * 950
    geometry = Geometry(tilt_deg=25, azimuth_deg=0)
    projection = transpose_ghi(times, ghi, -33.5, -70.6, geometry).poa_wm2
    actual = shift_weather(projection, 1) * 0.008
    cutoff = times[8 * 24 - 1]
    candidates = [Geometry(tilt_deg=0), geometry]
    first = fit_effective_poa(
        times, ghi, actual, -33.5, -70.6, training_end=cutoff, candidates=candidates, min_samples=24
    )
    changed = actual.copy()
    changed[times > cutoff] = np.linspace(1e7, 1e10, int((times > cutoff).sum()))
    second = fit_effective_poa(
        times,
        ghi,
        changed,
        -33.5,
        -70.6,
        training_end=cutoff,
        candidates=candidates,
        min_samples=24,
    )
    assert first.geometry == second.geometry == geometry
    assert first.lag_hours == second.lag_hours == 1
    assert first.training_correlation == second.training_correlation
    np.testing.assert_array_equal(first.poa_wm2, second.poa_wm2)


def test_irregular_timestamps_cannot_be_shifted_as_adjacent_hours() -> None:
    times = pd.date_range("2026-01-01", periods=50, freq="h", tz="UTC").delete(10)
    with pytest.raises(ValueError, match="consecutive"):
        fit_effective_poa(
            times,
            np.ones(49) * 500,
            np.ones(49),
            -33.5,
            -70.6,
            training_end=times[-1],
            candidates=[Geometry()],
        )
