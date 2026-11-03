"""Strict numerical contracts shared by tabular forecasting regressors."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from energy_methods._arrays import FloatArray, vector


def feature_matrix(features: ArrayLike, columns: int | None = None) -> FloatArray:
    """Require explicit finite (observations, features) arrays without reshaping."""
    values = np.asarray(features, dtype=np.float64)
    if values.ndim != 2 or not all(values.shape) or not np.isfinite(values).all():
        raise ValueError("Features must be a nonempty finite two-dimensional matrix")
    if columns is not None and values.shape[1] != columns:
        raise ValueError("Prediction feature count differs from the fitted feature order")
    return values


def training_arrays(
    features: ArrayLike, target: ArrayLike, min_samples: int
) -> tuple[FloatArray, FloatArray]:
    """Validate matching training rows; callers explicitly choose their own partition."""
    x = feature_matrix(features)
    y = vector(target, "target")
    if len(y) != len(x) or len(y) < min_samples or not np.isfinite(y).all():
        raise ValueError("Training targets must be finite, aligned and meet min_samples")
    return x, y


def feature_labels(names: tuple[str, ...] | None, columns: int) -> tuple[str, ...]:
    labels = tuple(f"x{i}" for i in range(columns)) if names is None else tuple(names)
    if len(labels) != columns or len(set(labels)) != columns or any(not x for x in labels):
        raise ValueError("Feature names must be unique, nonempty and match the matrix columns")
    return labels
