"""Screen hourly renewable output per MW; not a dispatch or damage model."""

import numpy as np
import pandas as pd


def wind_capacity_factor(speed_ms: np.ndarray, cut_out_ms: float = 25.0) -> np.ndarray:
    """Generic cubic turbine: cut-in 3, rated 12, cut-out 25 m/s by default.

    Input is hub-height speed, never gust speed. No restart hysteresis is modelled.
    """
    speed = np.asarray(speed_ms, dtype=float)
    if not np.isfinite(speed).all() or (speed < 0).any():
        raise ValueError("Wind must be finite and nonnegative")
    if not np.isfinite(cut_out_ms) or cut_out_ms <= 12:
        raise ValueError("Cut-out must exceed rated speed (12 m/s)")
    cf = np.clip((speed**3 - 3**3) / (12**3 - 3**3), 0, 1)
    return np.where(speed >= cut_out_ms, 0, cf)


def storm_energy(frame: pd.DataFrame, baseline_wind_ms: float = 8.0) -> pd.DataFrame:
    """Hourly MWh per MW versus clear-sky solar and assumed steady wind.

    Required columns: timestamp (UTC start), ghi_wm2, clear_ghi_wm2,
    wind_ms (120 m endpoint-averaged). Each row represents exactly one hour.
    PV is a horizontal irradiance proxy with fixed performance ratio 0.8;
    no tilt, thermal response, curtailment, storage or outages are represented.
    """
    if frame.empty:
        raise ValueError("At least one complete hour is required")
    time = pd.DatetimeIndex(pd.to_datetime(frame.timestamp, utc=True))
    if time.hasnans or (
        len(time) > 1 and not np.all((time[1:] - time[:-1]) == pd.Timedelta(hours=1))
    ):
        raise ValueError("Timestamps must be unique, sorted and hourly without gaps")
    values = frame[["ghi_wm2", "clear_ghi_wm2", "wind_ms"]].to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Incomplete or invalid weather; missing hours cannot count as zero")
    result = frame.copy()
    result["pv_mwh_per_mw"] = np.clip(values[:, 0] / 1000 * 0.8, 0, 1)
    result["pv_reference_mwh_per_mw"] = np.clip(values[:, 1] / 1000 * 0.8, 0, 1)
    result["wind_mwh_per_mw"] = wind_capacity_factor(values[:, 2])
    result["wind_reference_mwh_per_mw"] = wind_capacity_factor(np.array([baseline_wind_ms]))[0]
    for technology in ("pv", "wind"):
        result[f"{technology}_delta_mwh_per_mw"] = (
            result[f"{technology}_mwh_per_mw"] - result[f"{technology}_reference_mwh_per_mw"]
        )
    return result
