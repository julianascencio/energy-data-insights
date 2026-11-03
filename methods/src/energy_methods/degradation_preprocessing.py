"""Explicit time-series preparation for the 2021 degradation uncertainty study."""

from __future__ import annotations

import numpy as np
import pandas as pd

REFERENCE_IDS = ("ascencio_vasquez_2021_thesis", "kaaya_2021_uncertainties")


def _index(frame: pd.DataFrame) -> pd.DatetimeIndex:
    if not isinstance(frame.index, pd.DatetimeIndex) or frame.index.empty:
        raise ValueError("A nonempty DatetimeIndex is required")
    index = frame.index
    if index.hasnans or not index.is_monotonic_increasing or not index.is_unique:
        raise ValueError("Timestamps must be present, sorted and unique")
    if index.tz is None or str(index.tz) != "UTC":
        raise ValueError("Timestamps must be explicitly UTC")
    return index


def prepare_power_trend(
    frame: pd.DataFrame, *, age_origin: pd.Timestamp, window_months: int = 12
) -> pd.DataFrame:
    """Section 2.5 power screening and a declared monthly moving-average trend.

    Columns: power_w, poa_w_m2. Keep 800<=POA<=1200 W/m²; scale power to
    1000 W/m²; retain values within mean +/- 2 population standard deviations.
    Then monthly means and a centered full-window moving average; normalize by
    the maximum available trend. No temperature-to-STC correction is implied.
    Monthly aggregation, population SD and window length are repository choices.
    Centering uses future observations: use for retrospective analysis only and
    prepare a calibration interval separately from any holdout interval.

    Missing months remain missing; no interpolation across gaps. Ages retain
    their declared origin, even if the initial months have no usable records.
    Attrs report filter counts and choices. Cleaning, snow and reversible losses
    still need independent screening; this filter does not identify their cause.
    """
    index = _index(frame)
    if isinstance(window_months, bool) or not isinstance(window_months, int) or window_months < 1:
        raise ValueError("window_months must be a positive integer")
    origin = pd.Timestamp(age_origin)
    if pd.isna(origin) or origin.tz is None or str(origin.tz) != "UTC" or origin > index[0]:
        raise ValueError("age_origin must be UTC and no later than the first observation")
    values = frame[["power_w", "poa_w_m2"]].astype(float)
    if np.isinf(values.to_numpy()).any() or (values < 0).any().any():
        raise ValueError("Power and irradiance must be nonnegative, finite or missing")
    mask = values.notna().all(axis=1) & values.poa_w_m2.between(800, 1200)
    corrected = values.loc[mask, "power_w"] * 1000 / values.loc[mask, "poa_w_m2"]
    if len(corrected) < 2:
        raise ValueError("Too few valid clear-sky power observations")
    mean, sd = corrected.mean(), corrected.std(ddof=0)
    keep = (corrected - mean).abs() <= 2 * sd
    monthly = corrected.where(keep).resample("MS").mean()
    # A centered even-length window follows pandas' declared rolling convention.
    trend = monthly.rolling(window_months, center=True, min_periods=window_months).mean()
    if not trend.notna().any() or trend.max() <= 0:
        raise ValueError("No complete positive trend window remains")
    result = pd.DataFrame(
        {
            "monthly_power_w": monthly,
            "trend_power_w": trend,
            "normalized_power": trend / trend.max(),
        }
    )
    # Month-start labels can precede an origin inside that month; use mid-month
    # representative timestamps, and discard any row preceding the actual origin.
    result.index = result.index + pd.Timedelta(days=14)
    result = result.loc[result.index >= origin].copy()
    result["age_years"] = (pd.DatetimeIndex(result.index) - origin).total_seconds() / (
        365.25 * 86400
    )
    result.attrs = {
        "input_count": len(frame),
        "irradiance_selected_count": int(mask.sum()),
        "sigma_selected_count": int(keep.sum()),
        "window_months": window_months,
        "age_origin": origin.isoformat(),
        "normalization": "maximum available trend",
        "temperature_corrected": False,
        "retrospective_centered_window": True,
    }
    return result


def annual_stress_summary(frame: pd.DataFrame, *, year: int, cycles_per_year: float) -> dict:
    """Full UTC year of hourly interval-start weather to the paper's stresses.

    Columns: module_temperature_c, relative_humidity_percent, uv_irradiance_w_m2,
    poa_w_m2. Means and 5th/95th temperature percentiles use POA>0 records;
    UV dose integrates all hourly intervals, /1000 to kWh/m². Missing hours or
    values fail; no annualization of incomplete data. Nighttime UV must be zero.
    Cycle frequency is supplied independently, never inferred from record count.
    """
    index = _index(frame)
    expected = pd.date_range(
        f"{year}-01-01", f"{year + 1}-01-01", freq="h", tz="UTC", inclusive="left"
    )
    if not index.equals(expected):
        raise ValueError("A complete UTC year of hourly interval-start timestamps is required")
    names = ["module_temperature_c", "relative_humidity_percent", "uv_irradiance_w_m2", "poa_w_m2"]
    values = frame[names].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("All annual weather inputs must be finite; missing hours cannot be filled")
    t, rh, uv, poa = values.T
    if (
        np.any(t <= -273.15)
        or np.any((rh < 0) | (rh > 100))
        or np.any(uv < 0)
        or np.any(poa < 0)
        or np.any(uv > poa)
    ):
        raise ValueError("Invalid annual weather values")
    if not np.isfinite(cycles_per_year) or cycles_per_year < 0:
        raise ValueError("cycles_per_year must be finite and nonnegative")
    day = poa > 0
    if not day.any():
        raise ValueError("No daytime records")
    return {
        "module_temperature_mean_c": float(t[day].mean()),
        "module_temperature_upper_c": float(np.quantile(t[day], 0.95)),
        "module_temperature_lower_c": float(np.quantile(t[day], 0.05)),
        "relative_humidity_percent": float(rh[day].mean()),
        "uv_dose_kwh_m2": float(uv.sum() / 1000),
        "cycles_per_year": float(cycles_per_year),
    }
