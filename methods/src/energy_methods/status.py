"""IEC-informed observable operating screens; all operating causes unconfirmed.

Implements the recovered ASVA 2.0 decision order. Numerical thresholds are ASVA
engineering rules, not IEC requirements. IEC TS 63019:2019 information categories
must not be confused with confirmed plant availability or fault attribution.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike, NDArray

from energy_methods._arrays import BoolArray, FloatArray, IntArray, aligned, epoch_ns, utc_index


class OperatingState(IntEnum):
    MISSING_GENERATION = 0
    INVALID_GENERATION = 1
    NIGHT_NO_GENERATION = 2
    LOW_RESOURCE_NO_GENERATION = 3
    GENERATION_AT_LOW_RESOURCE = 4
    NO_GENERATION_WITH_RESOURCE = 5
    REFERENCE_UNAVAILABLE = 6
    GENERATION_BELOW_EXPECTED = 7
    GENERATION_MODEL_CONSISTENT = 8
    GENERATION_ABOVE_EXPECTED = 9


STATE_KEYS = tuple(state.name.lower() for state in OperatingState)
IEC_ASSIGNED_CATEGORY = "INFORMATION UNAVAILABLE"
IEC_ASSIGNED_CLAUSE = "5.18"


@dataclass(frozen=True, slots=True)
class StatusConfig:
    generation_epsilon_mwh: float = 1e-5
    minimum_solar_elevation_deg: float = 5.0
    minimum_ghi_wm2: float = 100.0
    minimum_effective_poa_wm2: float = 100.0
    night_maximum_solar_elevation_deg: float = 0.0
    night_maximum_ghi_wm2: float = 1.0
    model_relative_tolerance: float = 0.2
    model_absolute_tolerance_fraction_of_training_scale: float = 0.05
    minimum_expected_fraction_of_training_scale: float = 0.05
    near_zero_ratio: float = 0.05
    persistent_screening_run_minimum_hours: int = 2

    def __post_init__(self) -> None:
        numbers = [
            self.generation_epsilon_mwh,
            self.minimum_ghi_wm2,
            self.minimum_effective_poa_wm2,
            self.night_maximum_ghi_wm2,
            self.model_relative_tolerance,
            self.model_absolute_tolerance_fraction_of_training_scale,
            self.minimum_expected_fraction_of_training_scale,
            self.near_zero_ratio,
        ]
        if not np.isfinite(numbers).all() or min(numbers) < 0:
            raise ValueError("Screening thresholds must be finite and nonnegative")
        if (
            not -90
            <= self.night_maximum_solar_elevation_deg
            <= self.minimum_solar_elevation_deg
            <= 90
        ):
            raise ValueError("Solar elevation thresholds must be finite and ordered")
        if self.persistent_screening_run_minimum_hours < 2:
            raise ValueError("Persistence requires at least two consecutive hours")


@dataclass(frozen=True, slots=True)
class StatusResult:
    codes: NDArray[np.uint8]
    labels: NDArray[np.str_]
    envelope_lower_mwh: FloatArray
    envelope_upper_mwh: FloatArray
    band_state: NDArray[np.uint8]
    model_band_disagree: BoolArray
    near_zero: BoolArray
    persistent: BoolArray
    run_hours: IntArray
    assigned_iec_category: str = IEC_ASSIGNED_CATEGORY
    confirmed_cause: bool = False


def _optional_array(values: ArrayLike | None, n: int, name: str) -> FloatArray:
    result = np.full(n, np.nan) if values is None else np.asarray(values, dtype=np.float64)
    if result.shape != (n,):
        raise ValueError(f"{name} must match the observation length")
    return result


DEFAULT_CONFIG = StatusConfig()


def classify_status(
    actual_mwh: ArrayLike,
    expected_mwh: ArrayLike,
    ghi_wm2: ArrayLike,
    solar_elevation_deg: ArrayLike,
    *,
    poa_wm2: ArrayLike | None = None,
    training_scale_mwh: float | None = None,
    weather_supported: ArrayLike | None = None,
    band_lower_mwh: ArrayLike | None = None,
    band_upper_mwh: ArrayLike | None = None,
    timestamps: pd.DatetimeIndex | None = None,
    config: StatusConfig = DEFAULT_CONFIG,
) -> StatusResult:
    """Screen one site/reference in chronological order without filtering its energy.

    Pass timestamps to break persistence at missing elapsed hours. If omitted,
    rows are explicitly assumed to be consecutive one-hour intervals. Training
    scale is accepted-training Q95 (including zeros), not nameplate capacity.
    """
    actual, expected, ghi, elevation = aligned(
        actual_mwh,
        expected_mwh,
        ghi_wm2,
        solar_elevation_deg,
    )
    n = len(actual)
    poa = _optional_array(poa_wm2, n, "poa_wm2")
    lower_band = _optional_array(band_lower_mwh, n, "band_lower_mwh")
    upper_band = _optional_array(band_upper_mwh, n, "band_upper_mwh")
    support = (
        np.zeros(n, dtype=np.bool_)
        if weather_supported is None
        else np.asarray(
            weather_supported,
        )
    )
    if support.dtype != np.bool_ or support.shape != (n,):
        raise ValueError("weather_supported must be an aligned boolean array")
    utc = None if timestamps is None else utc_index(timestamps)
    if utc is not None and len(utc) != n:
        raise ValueError("Timestamps must match the observations")
    result = np.full(n, OperatingState.REFERENCE_UNAVAILABLE, dtype=np.uint8)
    valid = np.isfinite(actual) & (actual >= 0)
    result[np.isnan(actual)] = OperatingState.MISSING_GENERATION
    result[np.isinf(actual) | (np.isfinite(actual) & (actual < 0))] = (
        OperatingState.INVALID_GENERATION
    )
    resource_known = np.isfinite(ghi) & (ghi >= 0) & np.isfinite(elevation)
    resource_known &= np.abs(elevation) <= 90
    remaining = valid & resource_known
    trace = actual <= config.generation_epsilon_mwh
    night = remaining & (elevation <= config.night_maximum_solar_elevation_deg)
    night &= ghi <= config.night_maximum_ghi_wm2
    result[night & trace] = OperatingState.NIGHT_NO_GENERATION
    result[night & ~trace] = OperatingState.GENERATION_AT_LOW_RESOURCE
    remaining &= ~night
    resource = (ghi >= config.minimum_ghi_wm2) & (elevation > config.minimum_solar_elevation_deg)
    resource &= ~np.isfinite(poa) | (poa >= config.minimum_effective_poa_wm2)
    result[remaining & ~resource & trace] = OperatingState.LOW_RESOURCE_NO_GENERATION
    result[remaining & ~resource & ~trace] = OperatingState.GENERATION_AT_LOW_RESOURCE
    remaining &= resource
    # Zero output is observable with resource even without a usable expected model.
    result[remaining & trace] = OperatingState.NO_GENERATION_WITH_RESOURCE
    remaining &= ~trace
    scale_valid = training_scale_mwh is not None and np.isfinite(training_scale_mwh)
    scale = float(training_scale_mwh) if scale_valid and training_scale_mwh is not None else np.nan
    width = np.full(n, np.nan)
    if scale >= 0:
        width = np.maximum(
            config.model_relative_tolerance * expected,
            config.model_absolute_tolerance_fraction_of_training_scale * scale,
        )
        usable = remaining & np.isfinite(expected) & (expected >= 0) & support
        usable &= expected >= config.minimum_expected_fraction_of_training_scale * scale
        result[usable] = OperatingState.GENERATION_MODEL_CONSISTENT
        result[usable & (actual < expected - width)] = OperatingState.GENERATION_BELOW_EXPECTED
        result[usable & (actual > expected + width)] = OperatingState.GENERATION_ABOVE_EXPECTED
    envelope_valid = np.isfinite(expected) & (expected >= 0) & np.isfinite(width)
    lower_envelope = np.where(envelope_valid, expected - width, np.nan)
    upper_envelope = np.where(envelope_valid, expected + width, np.nan)
    band = np.zeros(n, dtype=np.uint8)
    band[~np.isfinite(actual)] = 4
    band_valid = np.isfinite(actual) & np.isfinite(lower_band) & np.isfinite(upper_band)
    band_valid &= lower_band <= upper_band
    band[band_valid] = 2
    band[band_valid & (actual < lower_band)] = 1
    band[band_valid & (actual > upper_band)] = 3
    disagree = ((result == 7) & (band == 3)) | ((result == 9) & (band == 1))
    disagree |= (result == 8) & np.isin(band, (1, 3))
    ratio = np.full(n, np.nan)
    np.divide(actual, expected, out=ratio, where=np.isfinite(expected) & (expected > 0))
    near_zero = (result == 7) & (actual > config.generation_epsilon_mwh)
    near_zero &= ratio < config.near_zero_ratio
    persistent, runs = np.zeros(n, dtype=np.bool_), np.ones(n, dtype=np.int64)
    if n:
        boundaries = result[1:] != result[:-1]
        if utc is not None:
            boundaries |= np.diff(epoch_ns(utc)) != 3_600_000_000_000
        starts = np.concatenate(([0], np.flatnonzero(boundaries) + 1))
        ends = np.concatenate((starts[1:], [n]))
        lengths = ends - starts
        runs = np.repeat(lengths, lengths).astype(np.int64)
        persistent = np.isin(result, (5, 7)) & (
            runs >= config.persistent_screening_run_minimum_hours
        )
    labels = np.asarray(STATE_KEYS, dtype=np.str_)[result]
    return StatusResult(
        result, labels, lower_envelope, upper_envelope, band, disagree, near_zero, persistent, runs
    )
