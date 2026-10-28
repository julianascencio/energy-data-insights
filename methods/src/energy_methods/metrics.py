"""Energy-prediction metrics on matching finite nonnegative observations."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from energy_methods._arrays import aligned


@dataclass(frozen=True, slots=True)
class EnergyMetrics:
    """WAPE uses measured energy; score is not classification accuracy."""

    matched_hours: int
    actual_mwh: float
    expected_mwh: float
    mae_mwh: float | None
    rmse_mwh: float | None
    wape: float | None
    score_pct: float | None
    bias_pct: float | None


def energy_metrics(actual_mwh: ArrayLike, expected_mwh: ArrayLike) -> EnergyMetrics:
    """Retain reported zeros, exclude missing/negative pairs, never divide by zero."""
    actual, expected = aligned(actual_mwh, expected_mwh)
    valid = np.isfinite(actual) & np.isfinite(expected) & (actual >= 0) & (expected >= 0)
    actual, expected = actual[valid], expected[valid]
    actual_sum, expected_sum = float(actual.sum()), float(expected.sum())
    if not len(actual):
        return EnergyMetrics(0, 0.0, 0.0, None, None, None, None, None)
    residual = expected - actual
    wape = float(np.abs(residual).sum() / actual_sum) if actual_sum > 0 else None
    return EnergyMetrics(
        len(actual),
        actual_sum,
        expected_sum,
        float(np.abs(residual).mean()),
        float(np.sqrt(np.mean(residual**2))),
        wape,
        None if wape is None else 100.0 * (1.0 - wape),
        None if actual_sum <= 0 else 100.0 * float(residual.sum()) / actual_sum,
    )
