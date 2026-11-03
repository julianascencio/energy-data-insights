"""Optional local connector to Mistral AI's Timestral forecasting models.

Timestral is model inference, so it belongs in ``energy_methods`` rather than
the public-observation retrieval package. Inputs must have equally spaced time
steps in a consistent unit. No resampling, unit conversion or interpolation is
performed here. NaN marks missing data; infinity is rejected.

Reference: https://github.com/mistralai/timestral (Apache-2.0 inference code;
model weights have their own Modified MIT licence). No weights are bundled.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from itertools import pairwise
from numbers import Integral
from pathlib import Path
from typing import Protocol, cast

import numpy as np
from numpy.typing import ArrayLike

from energy_methods._arrays import FloatArray, immutable

TIMESTRAL_SOURCE_REVISION = "a534bdbd244d64f3d9d743f46c7bf6fc330ed4ff"
TIMESTRAL_INSTALL = (
    "pip install git+https://github.com/mistralai/timestral.git@" + TIMESTRAL_SOURCE_REVISION
)


class ForecastBackend(Protocol):
    """Minimal upstream interface; allows offline contract tests without PyTorch."""

    def forecast(self, context: FloatArray, prediction_length: int, **kwargs: object) -> object:
        """Return an object with ``quantiles`` and ``quantile_levels`` attributes."""
        ...


@dataclass(frozen=True, slots=True)
class TimestralForecast:
    """CPU NumPy forecasts in the input unit, shaped (batch, variates, horizon, Q).

    Quantiles describe the model's predictive distribution, not calibrated
    confidence bounds. ``median`` is the 0.5 quantile, not the expected value.
    Arrays are copied and frozen, and invalid model output is rejected.
    """

    quantiles: FloatArray
    quantile_levels: tuple[float, ...]

    def __post_init__(self) -> None:
        values = immutable(self.quantiles)
        levels = tuple(float(level) for level in self.quantile_levels)
        if (
            not levels
            or not all(np.isfinite(level) and 0 < level < 1 for level in levels)
            or any(a >= b for a, b in pairwise(levels))
            or 0.5 not in levels
        ):
            raise ValueError("Quantile levels must increase strictly within (0, 1) and include 0.5")
        if values.ndim != 4 or 0 in values.shape or values.shape[-1] != len(levels):
            raise ValueError("Quantiles must have shape (batch, variates, horizon, levels)")
        if not np.isfinite(values).all() or (np.diff(values, axis=-1) < 0).any():
            raise ValueError("Model quantiles must be finite and non-crossing")
        object.__setattr__(self, "quantiles", values)
        object.__setattr__(self, "quantile_levels", levels)

    def quantile(self, level: float) -> FloatArray:
        """Select an exact model probability level without interpolating it."""
        if level not in self.quantile_levels:
            raise ValueError(f"Unsupported quantile {level}; choose from {self.quantile_levels}")
        return self.quantiles[..., self.quantile_levels.index(level)]

    @property
    def median(self) -> FloatArray:
        """Return the median, shaped (batch, variates, horizon)."""
        return self.quantile(0.5)


def _positive_integer(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return int(value)


def _numeric(values: ArrayLike, name: str) -> FloatArray:
    result = np.array(values, dtype=np.float64, copy=True)
    if np.isinf(result).any():
        raise ValueError(f"{name} must contain finite values or NaN, not infinity")
    return result


class TimestralConnector:
    """Lazy, reusable local inference with optional CPU/GPU model loading.

    Constructing this object never loads packages or downloads weights. The first
    valid ``forecast`` call loads Timestral and caches the forecaster. Install the
    official package using ``TIMESTRAL_INSTALL``. This is not a Mistral chat API:
    no Mistral API key is needed. Use a model commit ``revision`` for reproducible
    Hub downloads, or a local checkpoint directory with ``local_files_only=True``.

    Args:
        model_id: Official Hub ID (5M, 28M, 123M or 209M) or local checkpoint path.
        device: Upstream PyTorch device, e.g. ``cpu`` or ``cuda``.
        revision: Hugging Face checkpoint revision, distinct from the code revision.
        cache_dir: Optional Hugging Face cache path.
        local_files_only: Refuse network downloads; missing cache files are errors.
        max_context: Maximum recent steps passed to the model, at most 32,768.
        forecaster: Optional preloaded upstream-compatible backend.
    """

    def __init__(
        self,
        model_id: str | Path = "mistralai/Timestral-5M",
        *,
        device: str = "cpu",
        revision: str | None = None,
        cache_dir: str | Path | None = None,
        local_files_only: bool = False,
        max_context: int = 32768,
        forecaster: ForecastBackend | None = None,
    ) -> None:
        self.max_context = _positive_integer(max_context, "max_context")
        if self.max_context > 32768:
            raise ValueError("max_context cannot exceed Timestral's trained 32768 steps")
        if not str(model_id).strip():
            raise ValueError("model_id must not be empty")
        self.model_id = str(model_id)
        self.device = device
        self.revision = revision
        self.cache_dir = cache_dir
        self.local_files_only = local_files_only
        self._forecaster = forecaster

    def _load(self) -> ForecastBackend:
        if self._forecaster is None:
            try:
                module = import_module("timestral")
            except ImportError as exc:
                raise ImportError(
                    "Timestral inference needs the optional official package and PyTorch. "
                    f"Install with: {TIMESTRAL_INSTALL}"
                ) from exc
            self._forecaster = cast(
                ForecastBackend,
                module.TimestralForecaster.from_pretrained(
                    self.model_id,
                    device=self.device,
                    revision=self.revision,
                    cache_dir=self.cache_dir,
                    local_files_only=self.local_files_only,
                    max_context=self.max_context,
                ),
            )
        assert self._forecaster is not None
        return self._forecaster

    def forecast(
        self,
        context: ArrayLike,
        prediction_length: int,
        *,
        observation_mask: ArrayLike | None = None,
        past_covariates: ArrayLike | None = None,
        known_covariates: ArrayLike | None = None,
        categorical_past_covariates: ArrayLike | None = None,
        categorical_known_covariates: ArrayLike | None = None,
        symmetric_averaging: bool = True,
        clip_nonnegative: bool = True,
    ) -> TimestralForecast:
        """Forecast uniformly spaced context without training or future target data.

        ``context`` is (T,), (B, T) or (B, V, T); **2D means independent
        univariate series**, not one multivariate series. Use (1, V, T) for that.
        ``observation_mask`` must be boolean and exactly match the input shape.
        Covariates are (B, C, T) for past-only and (B, C, T + horizon) for known
        future values. Numeric category codes use the same shapes. Only supply
        covariates actually available at forecast time (e.g. calendars or archived
        weather forecasts, never subsequently observed weather).

        Long context and covariates are trimmed together, preserving the whole
        horizon. Each target must have an observed value in the retained window.
        Errors propagate: there is no synthetic or persistence fallback.
        """
        horizon = _positive_integer(prediction_length, "prediction_length")
        x = _numeric(context, "context")
        shape = x.shape
        if x.ndim not in (1, 2, 3) or 0 in shape:
            raise ValueError("context must be nonempty (T,), (B, T) or (B, V, T)")
        mask = np.isfinite(x)
        if observation_mask is not None:
            user_mask = np.asarray(observation_mask)
            if user_mask.shape != shape or user_mask.dtype != np.bool_:
                raise ValueError("observation_mask must be boolean and exactly match context shape")
            mask &= user_mask
        if x.ndim == 1:
            x, mask = x[None, None, :], mask[None, None, :]
        elif x.ndim == 2:
            x, mask = x[:, None, :], mask[:, None, :]
        batch, variates, length = x.shape
        start = max(0, length - self.max_context)
        x, mask = x[..., start:], mask[..., start:]
        if not mask.any(axis=-1).all():
            raise ValueError("Each target needs an observed value in the retained context")
        kwargs: dict[str, object] = {
            "observation_mask": mask,
            "symmetric_averaging": symmetric_averaging,
            "clip_nonnegative": clip_nonnegative,
        }
        for name, value, future in (
            ("past_covariates", past_covariates, False),
            ("known_covariates", known_covariates, True),
            ("categorical_past_covariates", categorical_past_covariates, False),
            ("categorical_known_covariates", categorical_known_covariates, True),
        ):
            if value is None:
                continue
            cov = _numeric(value, name)
            expected = length + horizon if future else length
            if cov.ndim != 3 or cov.shape[0] != batch or cov.shape[-1] != expected:
                raise ValueError(f"{name} must have shape ({batch}, covariates, {expected})")
            kwargs[name] = cov[..., start:]
        raw = self._load().forecast(x, prediction_length=horizon, **kwargs)
        values = getattr(raw, "quantiles", None)
        # Upstream returns torch tensors, potentially on CUDA. Keep torch optional
        # at import time and transfer predictions (never the whole model) to CPU.
        if hasattr(values, "detach"):
            values = values.detach().cpu().numpy()
        result = TimestralForecast(
            np.asarray(values, dtype=np.float64), tuple(getattr(raw, "quantile_levels", ()))
        )
        if result.quantiles.shape[:3] != (batch, variates, horizon):
            raise ValueError("Model output does not match requested batch, variates and horizon")
        return result
