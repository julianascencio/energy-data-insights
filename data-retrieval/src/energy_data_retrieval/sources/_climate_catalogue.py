"""Shared validation of explicitly downloaded climate reference tables."""

from __future__ import annotations

import numpy as np
import pandas as pd


def validate_catalogue(
    frame: pd.DataFrame, numeric_columns: tuple[str, ...], *, rounded_locations: bool = False
) -> pd.DataFrame:
    """Preserve missing measurements, but reject invalid locations and infinities."""
    required = ("lat", "lon", *numeric_columns)
    if not set(required) <= set(frame):
        raise ValueError(f"Missing climate catalogue columns: {sorted(set(required) - set(frame))}")
    result = frame.copy()
    for column in required:
        result[column] = pd.to_numeric(result[column], errors="raise")
    xy = result[["lat", "lon"]].to_numpy(dtype=float)
    if (
        not np.isfinite(xy).all()
        or np.any(np.abs(xy[:, 0]) > 90)
        or np.any(np.abs(xy[:, 1]) > 180)
        or (not rounded_locations and result.duplicated(["lat", "lon"]).any())
        or np.isinf(result[list(numeric_columns)].to_numpy(dtype=float)).any()
    ):
        raise ValueError("Climate catalogue has duplicate/invalid locations or infinite values")
    return result
