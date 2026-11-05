"""Seasonal station bias correction with explicit temporal and spatial support."""

from __future__ import annotations

import numpy as np
import pandas as pd

VARIABLES = ("temperature_c", "relative_humidity_percent", "wind_speed_ms")


def fit_monthly_bias(pairs: pd.DataFrame, *, year: int, minimum_days: int = 20) -> pd.DataFrame:
    """Fit monthly additive T/RH bias and multiplicative wind bias on one year.

    Pairs contain date, variable, observed, modelled. Temperature represents
    the daily min/max midpoint on both sides. RH and wind are daily means.
    Missing pairs are excluded; all twelve months must meet minimum_days for
    a variable to be supported. No validation-year observations enter fitting.
    """
    if not 1 <= minimum_days <= 28:
        raise ValueError("minimum_days must be between 1 and 28")
    data = pairs.copy()
    dates = pd.to_datetime(data["date"], errors="raise")
    data = data.loc[dates.dt.year == year].copy()
    if data.duplicated(["date", "variable"]).any():
        raise ValueError("Duplicate date-variable pairs")
    data["month"] = pd.to_datetime(data["date"]).dt.month
    records = []
    for variable in VARIABLES:
        subset = data.loc[data.variable == variable].copy()
        valid = np.isfinite(subset[["observed", "modelled"]].to_numpy(dtype=float)).all(axis=1)
        subset = subset.loc[np.asarray(valid, dtype=bool)]
        if variable == "relative_humidity_percent":
            subset = subset.loc[subset.observed.between(0, 100) & subset.modelled.between(0, 100)]
        elif variable == "wind_speed_ms":
            subset = subset.loc[(subset.observed >= 0) & (subset.modelled >= 0)]
        months = []
        for month in range(1, 13):
            sample = subset.loc[subset.month == month]
            if len(sample) < minimum_days:
                break
            if variable == "wind_speed_ms":
                if sample.modelled.mean() < 0.1:
                    break
                value = float(sample.observed.mean() / sample.modelled.mean())
            else:
                value = float((sample.observed - sample.modelled).mean())
            months.append(
                {
                    "variable": variable,
                    "month": month,
                    "value": value,
                    "training_days": len(sample),
                    "training_year": year,
                    "operation": "multiply" if variable == "wind_speed_ms" else "add",
                    "parameter_unit": {
                        "temperature_c": "degC",
                        "relative_humidity_percent": "percentage_points",
                        "wind_speed_ms": "dimensionless",
                    }[variable],
                }
            )
        if len(months) == 12:
            records.extend(months)
    return pd.DataFrame(
        records,
        columns=[
            "variable",
            "month",
            "value",
            "training_days",
            "training_year",
            "operation",
            "parameter_unit",
        ],
    )


def spatial_weights(
    station_xy: np.ndarray, target_xy: np.ndarray, *, radius_m: float = 75000, neighbours: int = 4
) -> np.ndarray:
    """IDW weights in a metric CRS, nearest four stations within 75 km.

    Zeros mean unsupported. This does not infer terrain representativeness.
    A 1 km distance floor avoids singularities; targets are processed in rows.
    """
    stations, targets = np.asarray(station_xy, float), np.asarray(target_xy, float)
    if (
        stations.ndim != 2
        or targets.ndim != 2
        or stations.shape[1] != 2
        or targets.shape[1] != 2
        or not np.isfinite(stations).all()
        or not np.isfinite(targets).all()
        or radius_m <= 0
        or neighbours < 1
    ):
        raise ValueError("Finite XY coordinates, positive radius and neighbour count required")
    distance = np.linalg.norm(targets[:, None, :] - stations[None, :, :], axis=2)
    weights = np.zeros_like(distance)
    for i, row in enumerate(distance):
        selected = np.argsort(row)[:neighbours]
        selected = selected[row[selected] <= radius_m]
        weights[i, selected] = 1 / np.maximum(row[selected], 1000) ** 2
    total = weights.sum(axis=1, keepdims=True)
    return np.divide(weights, total, out=weights, where=total > 0)


def correct_hourly(weather: pd.DataFrame, monthly: dict[str, np.ndarray]) -> pd.DataFrame:
    """Apply declared monthly parameters; retain hourly variability and irradiance.

    All three variables require twelve finite parameters. T/RH are additive;
    wind is multiplicative. RH is physically bounded and clipping is counted.
    This is monthly bias adjustment, not hourly error or extreme calibration.
    """
    result = weather.copy()
    if not isinstance(result.index, pd.DatetimeIndex) or result.index.tz is None:
        raise ValueError("Timezone-aware hourly index required")
    month = result.index.month.to_numpy() - 1
    for variable in VARIABLES:
        values = np.asarray(monthly[variable], float)
        if values.shape != (12,) or not np.isfinite(values).all():
            raise ValueError("Twelve finite monthly parameters required per variable")
        if variable == "wind_speed_ms":
            if (values < 0).any():
                raise ValueError("Negative wind correction")
            result[variable] *= values[month]
        else:
            result[variable] += values[month]
    rh = result.relative_humidity_percent
    result.attrs["rh_clipped_hours"] = int(((rh < 0) | (rh > 100)).sum())
    result["relative_humidity_percent"] = rh.clip(0, 100)
    return result
