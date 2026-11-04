"""Connect canonical weather tables to PVDeg's weather-column conventions."""

from __future__ import annotations

import numpy as np
import pandas as pd


def to_pvdeg_weather(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate UTC weather and return a copy suitable for PVDeg weather workflows.

    Required columns: temp_air (C), relative_humidity (%), wind_speed (m/s),
    ghi, dni, dhi (W/m2). No interpolation, inferred humidity or unit conversion.
    Use the existing PVGIS connector for acquisition; this adapter is offline.
    """
    columns = ["temp_air", "relative_humidity", "wind_speed", "ghi", "dni", "dhi"]
    if not isinstance(frame.index, pd.DatetimeIndex) or frame.index.tz is None:
        raise ValueError("Weather requires a timezone-aware DatetimeIndex")
    if frame.empty or not frame.index.is_unique or not frame.index.is_monotonic_increasing:
        raise ValueError("Weather timestamps must be nonempty, unique and increasing")
    if missing := set(columns) - set(frame.columns):
        raise ValueError(f"Missing PVDeg weather columns: {sorted(missing)}")
    result = frame.loc[:, columns].astype(float).copy()
    if not np.isfinite(result.to_numpy()).all():
        raise ValueError("Weather cannot contain missing or infinite values")
    if (
        not result.temp_air.between(-100, 100).all()
        or not result.relative_humidity.between(0, 100).all()
        or (result[["wind_speed", "ghi", "dni", "dhi"]] < 0).any().any()
    ):
        raise ValueError("Weather values violate Celsius, humidity or nonnegative bounds")
    result.index = frame.index.tz_convert("UTC")
    result.attrs = {**frame.attrs, "adapter": "PVDeg weather conventions; no gap filling"}
    return result
