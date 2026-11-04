"""An audited search and chronological solar-generation forecasting case.

June selected the plant; June/July selected the Timestral size and inputs.
August is the final evaluation period. Saved neural forecasts are real inference,
bound to the exact context; other models are fitted again on every replay.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from energy_analysis.forecast_benchmark import (
    MODELS,
    benchmark_scores,
    run_forecast_benchmark,
)
from energy_methods.timestral import TimestralConnector

REFERENCE_IDS = (
    "ascencio_vasquez_2020_modelling",
    "ons_pv_curtailment",
    "mistralai_2026_timestral",
)
CASE_MODELS = (*MODELS, "Daily mean", "Daily median")
MODEL_ID = "mistralai/Timestral-28M"
MODEL_REVISION = "49b26409ac87b5935539a5d8ffe7f397b720db47"
PLANT_ID = "RNMB06"
HOLDOUT_START = pd.Timestamp("2024-08-01 03:00:00", tz="UTC")


def run_solar_case(
    directory: str | Path, *, connector: TimestralConnector | None = None
) -> pd.DataFrame:
    """Reproduce the frozen case; do not search or optimize on the final holdout.

    Generation context and calibration span 14 days. If a same-clock resource
    reading is absent throughout that window, weather-dependent models may use
    older, pre-issue measurements. If accepted calibration power has zero Q95,
    retain the last informative calibration for all three fitted comparators.
    These safeguards keep every holdout label, including the sensor-data gap.
    """
    predictions = run_forecast_benchmark(
        directory,
        connector=connector,
        technologies=("solar",),
        seasonal_baselines=True,
        timestral_covariates="target_only",
        extend_resource_history=True,
        retain_informative_fit=True,
    )
    if set(predictions["plant_id"]) != {PLANT_ID}:
        raise ValueError("The frozen case is Mendubim VI (RNMB06)")
    predictions["period"] = np.where(
        predictions["timestamp"] < HOLDOUT_START, "Development", "August holdout"
    )
    expected = pd.date_range("2024-06-15 03:00", periods=78 * 48, freq="30min", tz="UTC")
    if set(predictions["timestamp"]) != set(expected):
        raise ValueError("The case must retain every June 15-August 31 forecast label")
    return predictions


def solar_case_scores(predictions: pd.DataFrame) -> pd.DataFrame:
    """Separate selection dates from the final month; score identical model keys."""
    if set(predictions["period"]) != {"Development", "August holdout"}:
        raise ValueError("Both development and holdout periods are required")
    return pd.concat(
        [
            benchmark_scores(frame, models=CASE_MODELS).assign(period=period)
            for period, frame in predictions.groupby("period", sort=True)
        ],
        ignore_index=True,
    )


def daily_errors(predictions: pd.DataFrame) -> pd.DataFrame:
    """Daily MAE for every model, after checking common and complete coverage."""
    solar_case_scores(predictions)
    frame = predictions.assign(error_mw=np.abs(predictions.prediction_mw - predictions.actual_mw))
    sizes = frame.groupby(["model", "issue_time"]).size()
    if not sizes.eq(48).all():
        raise ValueError("Every daily issue must include all 48 forecast leads")
    return frame.groupby(["period", "issue_time", "model"], as_index=False)[["error_mw"]].mean()
