"""Array and timestamp validation shared by numerical methods."""

from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike, NDArray

type FloatArray = NDArray[np.float64]
type BoolArray = NDArray[np.bool_]
type IntArray = NDArray[np.int64]


def vector(values: ArrayLike, name: str) -> FloatArray:
    """Convert without flattening malformed inputs or replacing missing data."""
    result = np.asarray(values, dtype=np.float64)
    if result.ndim != 1:
        raise ValueError(f"{name} must be a one-dimensional array")
    return result


def aligned(*arrays: ArrayLike) -> tuple[FloatArray, ...]:
    """Require equally sized one-dimensional numerical arrays."""
    result = tuple(vector(value, f"array {i}") for i, value in enumerate(arrays))
    if len({len(value) for value in result}) > 1:
        raise ValueError("Arrays must have equal lengths")
    return result


def utc_index(timestamps: pd.DatetimeIndex, *, regular_hourly: bool = False) -> pd.DatetimeIndex:
    """Reject ambiguous naive times and duplicates; preserve actual elapsed time."""
    result = pd.DatetimeIndex(timestamps)
    if result.tz is None:
        raise ValueError("Timestamps must be timezone-aware; naive local times are ambiguous")
    if result.hasnans or result.has_duplicates or not result.is_monotonic_increasing:
        raise ValueError("Timestamps must be finite, unique and increasing")
    result = result.tz_convert("UTC").as_unit("ns")
    if (
        regular_hourly
        and len(result) > 1
        and np.any(np.diff(epoch_ns(result)) != 3_600_000_000_000)
    ):
        raise ValueError("This method requires consecutive one-hour intervals")
    return result


def immutable(values: ArrayLike) -> FloatArray:
    """Freeze fitted numerical coefficients independently of caller-owned arrays."""
    result = np.array(values, dtype=np.float64, copy=True)
    result.flags.writeable = False
    return result


def epoch_ns(timestamps: pd.DatetimeIndex) -> IntArray:
    """UTC nanoseconds without reliance on pandas internal index attributes."""
    return timestamps.to_numpy(dtype="datetime64[ns]").astype(np.int64)
