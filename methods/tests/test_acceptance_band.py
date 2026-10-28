"""Training-only envelope and physically meaningful PR boundary regressions."""

import json

import numpy as np
import pytest

from energy_methods.acceptance_band import (
    AcceptanceBandConfig,
    BandFitUnavailable,
    fit_acceptance_band,
    performance_ratio,
    pr_acceptance_mask,
)


def test_band_has_frozen_irradiance_only_bounds_and_no_extrapolation() -> None:
    rng = np.random.default_rng(20261028)
    poa = np.repeat(np.arange(25.0, 1275.1, 50.0), 40)
    actual = 0.008 * poa * (1 - 0.0001 * poa) + rng.normal(0, 0.08, len(poa))
    actual = np.maximum(actual, 0)
    fitted = fit_acceptance_band(poa, actual)
    probe = np.array([-1, 0, 500, 800, 1301, np.nan])
    low, high = fitted.bounds(probe)
    assert np.isnan(low[[0, 1, 4, 5]]).all()
    assert np.isfinite(low[[2, 3]]).all()
    assert np.all(low[[2, 3]] <= high[[2, 3]])
    midpoint = (low + high) / 2
    assert fitted.mask(probe, midpoint).tolist() == [False, False, True, True, False, False]
    assert not fitted.mask(probe, midpoint + 1000).any()
    np.testing.assert_array_equal(fitted.bounds(probe)[0], low)
    json.dumps(fitted.to_dict(), allow_nan=False)
    with pytest.raises(ValueError, match="read-only"):
        fitted.lower_coefficients[0] = 0


def test_missing_bins_are_unsupported_even_inside_global_domain() -> None:
    rng = np.random.default_rng(12)
    poa = np.repeat(np.arange(25.0, 1275.1, 50.0), 40)
    keep = (poa < 500) | (poa >= 600)
    actual = np.maximum(0, poa[keep] * 0.01 + rng.normal(0, 0.1, keep.sum()))
    fitted = fit_acceptance_band(poa[keep], actual)
    lower, upper = fitted.bounds([525, 575])
    assert np.isnan(lower).all() and np.isnan(upper).all()


def test_unsupported_band_is_an_explicit_failure() -> None:
    with pytest.raises(BandFitUnavailable, match="Positive"):
        fit_acceptance_band([100, 200, 300], [0, 0, 0])
    with pytest.raises(BandFitUnavailable, match="populated"):
        fit_acceptance_band([100, 200, 300], [1, 2, 3])
    with pytest.raises(ValueError, match="bin width"):
        AcceptanceBandConfig(bin_width_wm2=np.nan)


def test_pr_units_duration_unknown_capacity_and_inclusive_boundaries() -> None:
    pr = performance_ratio(
        [5, 10, 0, -1, 5, 5], [1000, 1000, 1000, 1000, 0, 1000], [10, 10, 10, 10, 10, np.nan]
    )
    np.testing.assert_allclose(pr[:3], [0.5, 1.0, 0.0])
    assert np.isnan(pr[3:]).all()
    assert pr_acceptance_mask(pr).tolist() == [True, True, False, False, False, False]
    assert float(performance_ratio(2.5, 500, 10, interval_hours=0.5)) == 1.0
    with pytest.raises(ValueError, match="ordered"):
        pr_acceptance_mask(pr, 1, 0.5)
