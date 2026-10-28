"""Replayable interval-mean GHI transposition and training-only effective geometry.

Twelve solar-position substeps distribute hourly GHI proportional to positive
cos(true zenith), conserving its mean. Erbs at these synthetic substeps is an
explicit approximation; it does not reconstruct subhourly cloud variability.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import Literal

import numpy as np
import pandas as pd
import pvlib
from numpy.typing import ArrayLike

from energy_methods._arrays import FloatArray, aligned, epoch_ns, utc_index, vector


@dataclass(frozen=True, slots=True)
class Geometry:
    kind: Literal["fixed", "single_axis"] = "fixed"
    tilt_deg: float = 20.0
    azimuth_deg: float = 0.0
    axis_tilt_deg: float = 0.0
    axis_azimuth_deg: float = 0.0
    max_angle_deg: float = 60.0
    backtrack: bool = True
    gcr: float = 0.35

    def __post_init__(self) -> None:
        if self.kind not in {"fixed", "single_axis"}:
            raise ValueError("Only declared fixed and single-axis geometries are supported")
        if not 0 <= self.tilt_deg <= 90 or not -90 <= self.axis_tilt_deg <= 90:
            raise ValueError("Invalid surface or axis tilt")
        if not 0 <= self.azimuth_deg < 360 or not 0 <= self.axis_azimuth_deg < 360:
            raise ValueError("Azimuth is degrees clockwise from true north in [0,360)")
        if not 0 < self.max_angle_deg <= 90 or not 0 < self.gcr <= 1:
            raise ValueError("Invalid tracker rotation limit or ground coverage ratio")


@dataclass(frozen=True, slots=True)
class POAResult:
    poa_wm2: FloatArray
    solar_elevation_deg: FloatArray


@dataclass(frozen=True, slots=True)
class EffectivePOAFit:
    geometry: Geometry
    lag_hours: int
    training_correlation: float
    training_rows: int
    poa_wm2: FloatArray
    solar_elevation_deg: FloatArray
    training_end_utc: str

    def to_dict(self) -> dict[str, object]:
        """Small replay specification; arrays remain in the analysis table."""
        return {
            "geometry": asdict(self.geometry),
            "lag_hours": self.lag_hours,
            "training_correlation": self.training_correlation,
            "training_rows": self.training_rows,
            "training_end_utc": self.training_end_utc,
            "geometry_verified_as_built": False,
            "pvlib_version": pvlib.__version__,
            "substeps": 12,
            "decomposition": "erbs",
            "transposition": "haydavies",
            "lag_convention": "positive lag uses an earlier source-weather interval",
        }


DEFAULT_GEOMETRY = Geometry()


def _coordinates(latitude: float, longitude: float) -> None:
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("Finite WGS84 latitude and longitude are required")


def solar_elevation_midpoint(
    timestamps: pd.DatetimeIndex, latitude: float, longitude: float
) -> FloatArray:
    """Original resource evidence independent of fitting or available generation."""
    utc = utc_index(timestamps)
    _coordinates(latitude, longitude)
    if not len(utc):
        return np.empty(0, dtype=np.float64)
    solar = pvlib.solarposition.get_solarposition(
        utc + pd.Timedelta(minutes=30), latitude, longitude, method="nrel_numpy"
    )
    return np.asarray(solar["elevation"], dtype=np.float64)


@dataclass(frozen=True, slots=True)
class _PreparedIrradiance:
    """One bounded fit's weather-only intermediates, reused across geometries."""

    ghi: FloatArray
    true_zenith: FloatArray
    apparent_zenith: FloatArray
    solar_azimuth: FloatArray
    flat_ghi: FloatArray
    dni: FloatArray
    dhi: FloatArray
    dni_extra: FloatArray
    elevation: FloatArray
    substeps: int


def _prepare_irradiance(
    utc: pd.DatetimeIndex,
    ghi: FloatArray,
    latitude: float,
    longitude: float,
    substeps: int,
) -> _PreparedIrradiance:
    offsets = ((np.arange(substeps) + 0.5) * 3_600_000_000_000 / substeps).astype(np.int64)
    subtime = pd.to_datetime((epoch_ns(utc)[:, None] + offsets).ravel(), utc=True)
    sun = pvlib.solarposition.get_solarposition(subtime, latitude, longitude, method="nrel_numpy")
    true_zenith = np.asarray(sun["zenith"], dtype=np.float64)
    cosine = np.maximum(np.cos(np.radians(true_zenith)), 0.0).reshape(len(utc), substeps)
    mean_cosine = cosine.mean(axis=1)
    disaggregated = np.zeros_like(cosine)
    valid_ghi = np.isfinite(ghi) & (ghi >= 0)
    np.divide(
        ghi[:, None] * cosine,
        mean_cosine[:, None],
        out=disaggregated,
        where=(valid_ghi & (mean_cosine > 0))[:, None],
    )
    flat_ghi = disaggregated.ravel()
    parts = pvlib.irradiance.erbs(
        flat_ghi, true_zenith, subtime, min_cos_zenith=0.065, max_zenith=87.0
    )
    return _PreparedIrradiance(
        ghi,
        true_zenith,
        np.asarray(sun["apparent_zenith"], dtype=np.float64),
        np.asarray(sun["azimuth"], dtype=np.float64),
        flat_ghi,
        np.asarray(parts["dni"], dtype=np.float64),
        np.asarray(parts["dhi"], dtype=np.float64),
        np.asarray(pvlib.irradiance.get_extra_radiation(subtime), dtype=np.float64),
        solar_elevation_midpoint(utc, latitude, longitude),
        substeps,
    )


def _project(prepared: _PreparedIrradiance, geometry: Geometry) -> POAResult:
    if geometry.kind == "fixed":
        tilt: float | FloatArray = geometry.tilt_deg
        azimuth: float | FloatArray = geometry.azimuth_deg
    else:
        tracking = pvlib.tracking.singleaxis(
            prepared.apparent_zenith,
            prepared.solar_azimuth,
            axis_tilt=geometry.axis_tilt_deg,
            axis_azimuth=geometry.axis_azimuth_deg,
            max_angle=geometry.max_angle_deg,
            backtrack=geometry.backtrack,
            gcr=geometry.gcr,
        )
        tilt = np.nan_to_num(np.asarray(tracking["surface_tilt"], dtype=np.float64))
        azimuth = np.nan_to_num(np.asarray(tracking["surface_azimuth"], dtype=np.float64))
    total = pvlib.irradiance.get_total_irradiance(
        surface_tilt=tilt,
        surface_azimuth=azimuth,
        solar_zenith=prepared.true_zenith,
        solar_azimuth=prepared.solar_azimuth,
        dni=prepared.dni,
        ghi=prepared.flat_ghi,
        dhi=prepared.dhi,
        dni_extra=prepared.dni_extra,
        model="haydavies",
        albedo=0.2,
    )
    poa = np.maximum(np.asarray(total["poa_global"], dtype=np.float64), 0.0)
    poa[prepared.true_zenith >= 90] = 0.0
    poa = poa.reshape(len(prepared.ghi), prepared.substeps).mean(axis=1)
    poa[~np.isfinite(prepared.ghi) | (prepared.ghi < 0)] = np.nan
    return POAResult(poa, prepared.elevation)


def transpose_ghi(
    timestamps: pd.DatetimeIndex,
    ghi_wm2: ArrayLike,
    latitude: float,
    longitude: float,
    geometry: Geometry = DEFAULT_GEOMETRY,
    *,
    substeps: int = 12,
) -> POAResult:
    """Transpose one-hour mean GHI without consulting any generation observations."""
    utc = utc_index(timestamps)
    ghi = vector(ghi_wm2, "ghi_wm2")
    if len(utc) != len(ghi):
        raise ValueError("GHI and timestamps must align")
    _coordinates(latitude, longitude)
    if not isinstance(substeps, int) or not 1 <= substeps <= 60:
        raise ValueError("substeps must be an integer in [1,60]")
    if not len(utc):
        return POAResult(np.empty(0, dtype=np.float64), np.empty(0, dtype=np.float64))
    return _project(_prepare_irradiance(utc, ghi, latitude, longitude, substeps), geometry)


def shift_weather(values: ArrayLike, lag_hours: int) -> FloatArray:
    """Shift a regular hourly feature array without circular wrap or gap filling."""
    source = vector(values, "weather")
    if not isinstance(lag_hours, int):
        raise ValueError("lag_hours must be an integer")
    result = np.full(len(source), np.nan)
    if abs(lag_hours) >= len(source) and lag_hours != 0:
        return result
    if lag_hours > 0:
        result[lag_hours:] = source[:-lag_hours]
    elif lag_hours < 0:
        result[:lag_hours] = source[-lag_hours:]
    else:
        result[:] = source
    return result


def fit_effective_poa(
    timestamps: pd.DatetimeIndex,
    ghi_wm2: ArrayLike,
    actual_mwh: ArrayLike,
    latitude: float,
    longitude: float,
    *,
    training_end: pd.Timestamp,
    candidates: Sequence[Geometry],
    lag_hours: Sequence[int] = (-2, -1, 0, 1, 2),
    min_samples: int = 48,
) -> EffectivePOAFit:
    """Choose a bounded geometry/lag bank using training-only Pearson correlation.

    Holdout labels are never read by the objective. Shifted training weather is
    also restricted to source timestamps within the training interval. Correlation
    does not establish true racking geometry or causal time alignment.
    """
    utc = utc_index(timestamps, regular_hourly=True)
    ghi, actual = aligned(ghi_wm2, actual_mwh)
    if len(utc) != len(ghi) or min_samples < 3 or not candidates or not lag_hours:
        raise ValueError("Aligned hourly inputs, nonempty candidates and >=3 samples are required")
    cutoff = pd.Timestamp(training_end)
    if cutoff.tzinfo is None:
        raise ValueError("training_end must be timezone-aware")
    cutoff = cutoff.tz_convert("UTC")
    if any(not isinstance(lag, int) or abs(lag) > 24 for lag in lag_hours):
        raise ValueError("Integer weather lags must be within +/-24 hours")
    train = np.asarray(utc <= cutoff) & np.isfinite(actual) & (actual >= 0)
    train &= np.isfinite(ghi) & (ghi >= 100)
    _coordinates(latitude, longitude)
    if not len(utc):
        raise ValueError("Effective POA fitting requires observations")
    prepared = _prepare_irradiance(utc, ghi, latitude, longitude, 12)
    best: EffectivePOAFit | None = None
    # Candidate count is finite; expensive solar calculations are independent of labels.
    for geometry in candidates:
        projection = _project(prepared, geometry)
        for lag in lag_hours:
            shifted = shift_weather(projection.poa_wm2, lag)
            source_within_training = np.asarray(utc - pd.Timedelta(hours=lag) <= cutoff)
            usable = train & source_within_training & np.isfinite(shifted) & (shifted > 0)
            count = int(usable.sum())
            if count < min_samples or np.std(actual[usable]) <= 0 or np.std(shifted[usable]) <= 0:
                continue
            correlation = float(np.corrcoef(shifted[usable], actual[usable])[0, 1])
            if not np.isfinite(correlation):
                continue
            if best is None or correlation > best.training_correlation:
                best = EffectivePOAFit(
                    geometry,
                    lag,
                    correlation,
                    count,
                    shifted,
                    projection.solar_elevation_deg,
                    cutoff.isoformat(),
                )
    if best is None:
        raise ValueError("Insufficient varying training data for effective POA fitting")
    return best
