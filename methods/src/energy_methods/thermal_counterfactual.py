"""Comfort-event and paired intervention scoring, independent of predictor type."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

REFERENCE_IDS = ("galataud_2026_thermal_counterfactual",)


def comfort_time(
    minutes: ArrayLike,
    temperature: ArrayLike,
    *,
    threshold_c: float = 20.75,
    consecutive: int = 2,
    not_before_min: float | None = None,
) -> float | None:
    """First sustained heating-threshold crossing, linearly interpolated in minutes.

    Require ``consecutive`` samples at or above threshold. Return None if the
    event is right-censored by the horizon; never substitute the horizon as an
    observed event. If already comfortable at the first sample, return that
    sample's time (left-censored). Inputs must be finite and strictly ordered.
    ``not_before_min`` restricts scoring to samples at/after an eligibility
    time, reproducing the source's start-gated metric. This is a heating criterion,
    not a two-sided comfort band or cooling metric.
    """
    x, y = np.asarray(minutes, dtype=float), np.asarray(temperature, dtype=float)
    if (
        x.ndim != 1
        or y.shape != x.shape
        or x.size == 0
        or not np.isfinite(x).all()
        or not np.isfinite(y).all()
        or not np.isfinite(threshold_c)
        or not np.all(np.diff(x) > 0)
    ):
        raise ValueError("Times and temperatures must be finite, aligned, and ordered")
    if isinstance(consecutive, bool) or not isinstance(consecutive, int) or consecutive < 1:
        raise ValueError("consecutive must be a positive integer")
    if not_before_min is not None:
        if not np.isfinite(not_before_min):
            raise ValueError("not_before_min must be finite")
        eligible = x >= not_before_min
        x, y = x[eligible], y[eligible]
    for i in range(max(0, len(y) - consecutive + 1)):
        if np.all(y[i : i + consecutive] >= threshold_c):
            if i == 0:
                return float(x[0])
            return float(
                x[i - 1] + (x[i] - x[i - 1]) * (threshold_c - y[i - 1]) / (y[i] - y[i - 1])
            )
    return None


def paired_shift_error(
    predicted: float | None,
    reference: float | None,
    actual: float | None,
    actual_reference: float | None,
) -> float | None:
    """Predicted minus simulated change, in minutes; positive means overresponse.

    All four comfort events must be observed. Missing events remain censored.
    """
    values = (predicted, reference, actual, actual_reference)
    if any(v is None for v in values):
        return None
    array = np.asarray(values, dtype=float)
    if not np.isfinite(array).all():
        raise ValueError("Comfort times must be finite or None")
    return float(array[0] - array[1] - array[2] + array[3])
