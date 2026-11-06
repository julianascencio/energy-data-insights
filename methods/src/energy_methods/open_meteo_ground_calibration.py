"""Ground-observation validation for Open-Meteo model output.

Works on aligned station/day pairs; never interprets gridded weather as observations.
For fitting, reuse energy_methods.weather_calibration.fit_monthly_bias.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from energy_methods.weather_calibration import fit_monthly_bias

OPERATIONS = {
    "temperature_c": "add",
    "relative_humidity_percent": "add",
    "wind_speed_ms": "multiply",
}


def evaluate_station_holdout(
    pairs: pd.DataFrame,
    coefficients: pd.DataFrame,
    *,
    validation_year: int,
    minimum_days: int = 20,
) -> pd.DataFrame:
    """Evaluate independent held-out daily observations, by variable and month.

    Reports every supported month, including worsening corrections. Does not
    extrapolate station skill to unobserved locations or hourly extremes.
    """
    if not 1 <= minimum_days <= 28:
        raise ValueError("minimum_days must be between 1 and 28")
    required = {"date", "variable", "observed", "modelled"}
    if not required.issubset(pairs.columns):
        raise ValueError(f"Missing pair columns: {sorted(required - set(pairs.columns))}")
    if not {"variable", "month", "value", "training_year"}.issubset(coefficients.columns):
        raise ValueError("Missing calibration parameter columns")
    dates = pd.to_datetime(pairs["date"], utc=True)
    data = pairs.loc[dates.dt.year == validation_year].copy()
    data["month"] = dates.loc[data.index].dt.month
    if data.duplicated(["date", "variable"]).any():
        raise ValueError("Duplicate station/date/variable pairs")
    if (coefficients.training_year == validation_year).any():
        raise ValueError("Validation year must be independent of training")
    records = []
    for variable, operation in OPERATIONS.items():
        subset = data.loc[data.variable == variable]
        params = coefficients.loc[coefficients.variable == variable]
        if params.month.duplicated().any():
            raise ValueError("Duplicate monthly calibration parameters")
        for month, sample in subset.groupby("month"):
            param = params.loc[params.month == month]
            if len(param) != 1:
                continue
            observed = pd.to_numeric(sample.observed, errors="coerce").to_numpy(float)
            raw = pd.to_numeric(sample.modelled, errors="coerce").to_numpy(float)
            valid = np.isfinite(observed) & np.isfinite(raw)
            if variable == "relative_humidity_percent":
                valid &= (observed >= 0) & (observed <= 100) & (raw >= 0) & (raw <= 100)
            if variable == "wind_speed_ms":
                valid &= (observed >= 0) & (raw >= 0)
            if valid.sum() < minimum_days:
                continue
            observed, raw = observed[valid], raw[valid]
            correction = float(param.value.iloc[0])
            adjusted = raw + correction if operation == "add" else raw * correction
            if variable == "relative_humidity_percent":
                adjusted = np.clip(adjusted, 0, 100)
            records.append(
                {
                    "variable": variable,
                    "month": int(sample["month"].iloc[0]),
                    "paired_days": int(valid.sum()),
                    "validation_year": validation_year,
                    "raw_rmse": float(np.sqrt(np.mean((raw - observed) ** 2))),
                    "corrected_rmse": float(np.sqrt(np.mean((adjusted - observed) ** 2))),
                    "raw_bias": float(np.mean(raw - observed)),
                    "corrected_bias": float(np.mean(adjusted - observed)),
                    "improved": bool(
                        np.mean((adjusted - observed) ** 2) < np.mean((raw - observed) ** 2)
                    ),
                }
            )
    return pd.DataFrame(
        records,
        columns=[
            "variable",
            "month",
            "paired_days",
            "validation_year",
            "raw_rmse",
            "corrected_rmse",
            "raw_bias",
            "corrected_bias",
            "improved",
        ],
    )


__all__ = ["evaluate_station_holdout"]
