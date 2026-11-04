"""Reanalyse Foobot's published EnergyPlus/Timestral outputs, without refitting."""

from __future__ import annotations

import numpy as np
import pandas as pd

from energy_data_retrieval.foobot import ThermalPanel
from energy_methods.thermal_counterfactual import comfort_time, paired_shift_error


def score_panels(panels: tuple[ThermalPanel, ...]) -> pd.DataFrame:
    """Recompute T1 errors and T2 paired shifts using each morning's T2 zero offset.

    T1 and T2 forecasts have different issue times, so T1 is never used as the
    counterfactual reference. Rows with missed targets retain NaN timing errors.
    The frame includes every panel and explicit event-observation flags.
    """
    if not panels:
        raise ValueError("At least one morning is required")
    keys = [(p.date, p.test, p.offset) for p in panels]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate panel keys")
    times = {
        key: (
            comfort_time(
                p.minutes, p.truth, threshold_c=p.threshold, not_before_min=float(p.offset)
            ),
            comfort_time(
                p.minutes, p.median, threshold_c=p.threshold, not_before_min=float(p.offset)
            ),
        )
        for key, p in zip(keys, panels, strict=True)
    }
    rows = []
    for key, p in zip(keys, panels, strict=True):
        truth, prediction = times[key]
        shift = None
        if p.test == "T2":
            baseline = (p.date, "T2", 0)
            if baseline not in times:
                raise ValueError("Missing paired T2 baseline")
            base_truth, base_prediction = times[baseline]
            shift = paired_shift_error(prediction, base_prediction, truth, base_truth)
        rows.append(
            {
                "date": p.date,
                "test": p.test,
                "offset_min": p.offset,
                "temperature_mae_c": float(np.mean(np.abs(np.array(p.median) - p.truth))),
                "truth_met_min": truth,
                "prediction_met_min": prediction,
                "truth_observed": truth is not None,
                "prediction_observed": prediction is not None,
                "timing_error_min": None
                if truth is None or prediction is None
                else prediction - truth,
                "shift_error_min": shift,
                "unrestricted_prediction_met_min": comfort_time(
                    p.minutes, p.median, threshold_c=p.threshold
                ),
            }
        )
    return pd.DataFrame(rows)


def sensitivity_ratios(scores: pd.DataFrame) -> pd.DataFrame:
    """Fit comfort time vs offset per complete T2 day; omit censored/flat truth days.

    No imputation, regression on incomplete schedules, or ratios with near-zero
    simulated sensitivity. Return counts through one row per day and valid flag.
    """
    rows = []
    for date, group in scores[scores["test"] == "T2"].groupby("date"):
        valid = (
            len(group) == 5
            and set(group.offset_min) == {-60, -30, 0, 30, 60}
            and group[["truth_met_min", "prediction_met_min"]].notna().all().all()
        )
        actual = prediction = ratio = float("nan")
        if valid:
            actual = float(np.polyfit(group.offset_min, group.truth_met_min, 1)[0])
            prediction = float(np.polyfit(group.offset_min, group.prediction_met_min, 1)[0])
            valid = abs(actual) > 1e-8
            if valid:
                ratio = prediction / actual
        rows.append(
            {
                "date": date,
                "valid": bool(valid),
                "truth_slope": actual,
                "prediction_slope": prediction,
                "sensitivity_ratio": ratio,
            }
        )
    return pd.DataFrame(rows)
