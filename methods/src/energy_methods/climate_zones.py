"""Portable climate classifications and bounded, frozen cluster prediction.

Zero is always missing; positive IDs are local to a scheme/model version.
Distances and training-range flags are diagnostics, not probabilities.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import ArrayLike, NDArray

REFERENCE_IDS = ("ascencio_vasquez_2021_thesis",)


@dataclass(frozen=True)
class ClimateProvenance:
    """Caller-declared source support, retained in every result and fitted state."""

    source: str
    period: str
    resolution: str
    status: str = "application"

    def __post_init__(self) -> None:
        if any(not isinstance(v, str) or not v.strip() for v in vars(self).values()):
            raise ValueError("Source, period, resolution and status must be nonempty strings")


@dataclass(frozen=True)
class ClimateZones:
    """Class IDs, scientific codes, readable labels and source metadata."""

    scheme: str
    class_id: NDArray[np.int64]
    codes: tuple[str, ...]
    labels: tuple[str, ...]
    provenance: ClimateProvenance
    reference_ids: tuple[str, ...]
    outside_training_range: NDArray[np.bool_] | None = None

    def __post_init__(self) -> None:
        ids = np.asarray(self.class_id)
        if (
            not np.issubdtype(ids.dtype, np.integer)
            or len(self.codes) != len(self.labels)
            or not self.codes
            or self.codes[0] != ""
            or len(set(self.codes)) != len(self.codes)
            or np.any((ids < 0) | (ids >= len(self.codes)))
        ):
            raise ValueError("IDs must index a unique code/label catalogue starting with missing")
        copied = np.array(ids, dtype=np.int64, copy=True)
        copied.setflags(write=False)
        object.__setattr__(self, "class_id", copied)
        if self.outside_training_range is not None:
            outside = np.array(self.outside_training_range, dtype=bool, copy=True)
            if outside.shape != ids.shape:
                raise ValueError("Training-range flags must match class IDs")
            outside.setflags(write=False)
            object.__setattr__(self, "outside_training_range", outside)

    @property
    def zone(self) -> NDArray[np.str_]:
        """Scientific code for each cell; empty string means unclassified."""
        return np.asarray(self.codes)[self.class_id]


@dataclass(frozen=True)
class ClimateClusterModel:
    """Validated numerical state; no executable pickle or runtime estimator needed.

    Input columns must follow ``features`` and the recorded training convention.
    NaN prediction rows stay unclassified; infinity is rejected. Training bounds
    diagnose extrapolation but do not measure cluster confidence.
    """

    scheme: str
    features: tuple[str, ...]
    offset: NDArray[np.float64]
    scale: NDArray[np.float64]
    weights: NDArray[np.float64]
    centers: NDArray[np.float64]
    lower: NDArray[np.float64]
    upper: NDArray[np.float64]
    codes: tuple[str, ...]
    labels: tuple[str, ...]
    provenance: ClimateProvenance
    reference_ids: tuple[str, ...]
    settings: dict[str, Any]

    def __post_init__(self) -> None:
        d = len(self.features)
        if not d or len(set(self.features)) != d:
            raise ValueError("Feature names must be nonempty and unique")
        for name in ("offset", "scale", "weights", "centers", "lower", "upper"):
            value = np.array(getattr(self, name), dtype=float, copy=True)
            if not np.isfinite(value).all():
                raise ValueError("Model state must be finite")
            expected = (len(self.codes) - 1, d) if name == "centers" else (d,)
            if value.shape != expected:
                raise ValueError(f"Invalid {name} shape")
            value.setflags(write=False)
            object.__setattr__(self, name, value)
        if (
            np.any(self.scale <= 0)
            or np.any(self.weights < 0)
            or not np.any(self.weights > 0)
            or np.any(self.lower > self.upper)
            or len(self.codes) < 2
        ):
            raise ValueError("Invalid model scale, weights, bounds or cluster count")
        ClimateZones(
            self.scheme,
            np.array([], dtype=np.int64),
            self.codes,
            self.labels,
            self.provenance,
            self.reference_ids,
        )
        object.__setattr__(self, "settings", json.loads(json.dumps(self.settings, allow_nan=False)))

    def predict(self, values: ArrayLike, *, batch_size: int = 8192) -> ClimateZones:
        """Predict without refitting; memory is bounded by batch size by cluster count."""
        x = np.asarray(values, dtype=float)
        if x.ndim < 1 or x.shape[-1] != len(self.features) or np.isinf(x).any():
            raise ValueError("Expected finite/NaN feature rows in the recorded column order")
        if isinstance(batch_size, bool) or not isinstance(batch_size, int) or batch_size < 1:
            raise ValueError("batch_size must be a positive integer")
        shape = x.shape[:-1]
        flat = x.reshape(-1, len(self.features))
        ids = np.zeros(len(flat), dtype=np.int64)
        outside = np.zeros(len(flat), dtype=bool)
        for start in range(0, len(flat), batch_size):
            rows = flat[start : start + batch_size]
            good = np.isfinite(rows).all(axis=1)
            indices = np.flatnonzero(good) + start
            if not len(indices):
                continue
            transformed = (rows[good] - self.offset) / self.scale * self.weights
            distance = np.sum((transformed[:, None, :] - self.centers) ** 2, axis=2)
            ids[indices] = np.argmin(distance, axis=1) + 1
            outside[indices] = ((rows[good] < self.lower) | (rows[good] > self.upper)).any(axis=1)
        return ClimateZones(
            self.scheme,
            ids.reshape(shape),
            self.codes,
            self.labels,
            self.provenance,
            self.reference_ids,
            outside.reshape(shape),
        )

    def to_dict(self) -> dict[str, Any]:
        """JSON-compatible state including scaling, units/conventions and attribution."""
        result: dict[str, Any] = {"format_version": 1}
        for name, value in vars(self).items():
            result[name] = (
                value.tolist()
                if isinstance(value, np.ndarray)
                else vars(value).copy()
                if isinstance(value, ClimateProvenance)
                else value
            )
        return json.loads(json.dumps(result, allow_nan=False))

    @classmethod
    def from_dict(cls, state: dict[str, Any]) -> ClimateClusterModel:
        """Restore and validate a versioned numerical model."""
        data = dict(state)
        if data.pop("format_version", None) != 1:
            raise ValueError("Unsupported climate model format")
        data["provenance"] = ClimateProvenance(**data["provenance"])
        for name in ("features", "codes", "labels", "reference_ids"):
            data[name] = tuple(data[name])
        return cls(**data)


def validate_training(values: ArrayLike, features: int, clusters: int) -> NDArray[np.float64]:
    """Require explicit complete training rows and enough distinct locations."""
    x = np.asarray(values, dtype=float)
    if (
        isinstance(clusters, bool)
        or not isinstance(clusters, int)
        or clusters < 2
        or x.ndim != 2
        or x.shape[1] != features
        or not np.isfinite(x).all()
        or len(np.unique(x, axis=0)) < clusters
    ):
        raise ValueError("Training requires finite feature rows and at least K distinct rows")
    if np.any(np.std(x, axis=0) == 0):
        raise ValueError("Training features must have nonzero variance")
    return x


def class_target_rmse(
    zones: ClimateZones, target: ArrayLike, sample_weight: ArrayLike | None = None
) -> float:
    """Weighted within-class target dispersion, not held-out prediction accuracy.

    Compare on the same locations/period and also at equal class counts. Missing
    target values and class zero are excluded; no area weighting is inferred.
    """
    y = np.asarray(target, dtype=float)
    w = np.ones(y.shape) if sample_weight is None else np.asarray(sample_weight, dtype=float)
    if (
        y.shape != zones.class_id.shape
        or w.shape != y.shape
        or np.isinf(y).any()
        or not np.isfinite(w).all()
        or np.any(w < 0)
    ):
        raise ValueError("Targets and nonnegative finite weights must match the classifications")
    good = (zones.class_id > 0) & np.isfinite(y) & (w > 0)
    if not good.any():
        raise ValueError("No qualified target observations")
    total = 0.0
    for class_id in np.unique(zones.class_id[good]):
        mask = good & (zones.class_id == class_id)
        mean = np.average(y[mask], weights=w[mask])
        total += float(np.sum(w[mask] * (y[mask] - mean) ** 2))
    return float(np.sqrt(total / w[good].sum()))
