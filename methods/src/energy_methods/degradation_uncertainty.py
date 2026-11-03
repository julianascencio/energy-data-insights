"""Explicit physical-rate conventions for the 2021 PV uncertainty study.

The paper omits A_N and C_N for Table 5 and mixes rate/dose unit descriptions.
No universal calibration or implicit conversion to a lifetime coefficient is
provided. Every calibrated rate must declare its scale to fractional year^-1.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from energy_methods.degradation import (
    BOLTZMANN_EV_K,
    DegradationParameters,
    _evaluate_degradation_rates,
)

REFERENCE_IDS = ("ascencio_vasquez_2021_thesis", "kaaya_2021_uncertainties")


def _scale(value: float) -> None:
    if not np.isfinite(value) or value <= 0:
        raise ValueError("rate_scale_to_year_inverse must be finite and positive")


@dataclass(frozen=True, slots=True)
class PhysicalRate:
    """Native calibrated numerical rate and explicit fractional/year conversion.

    ``mechanisms`` holds raw hydrolysis, photo and thermal values when available.
    The multiplicative total is not a sum and its components are not shares.
    """

    raw_rate: NDArray[np.float64]
    annual_fractional_rate: NDArray[np.float64]
    rate_scale_to_year_inverse: float
    mechanisms: tuple[NDArray[np.float64], ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class StressRateParameters:
    """Equation 1 coefficients, including mandatory calibration and unit scale.

    beta0 carries the calibration's units. beta1 is activation energy in eV;
    beta2, beta3, beta4 are nonnegative powers of daily temperature range,
    daytime UV irradiance (W/m²) and daily RH (percent), respectively.
    """

    beta0: float
    beta1: float
    beta2: float
    beta3: float
    beta4: float
    rate_scale_to_year_inverse: float
    calibration_source: str

    def __post_init__(self) -> None:
        coefficients = [self.beta0, self.beta1, self.beta2, self.beta3, self.beta4]
        if not np.isfinite(coefficients).all() or min(coefficients) < 0:
            raise ValueError("Stress-rate coefficients must be finite and nonnegative")
        _scale(self.rate_scale_to_year_inverse)
        if not isinstance(self.calibration_source, str) or not self.calibration_source.strip():
            raise ValueError("calibration_source is required")


def stress_rate(
    *,
    daily_maximum_temperature_c: ArrayLike,
    daily_temperature_range_c: ArrayLike,
    daily_daytime_uv_w_m2: ArrayLike,
    daily_relative_humidity_percent: ArrayLike,
    parameters: StressRateParameters,
) -> PhysicalRate:
    """Equation 1 (Bala), evaluated on daily inputs, without hidden aggregation.

    Annual integrated UV dose is NOT a substitute for daytime irradiance.
    Missing input masks the paired result; infinities and invalid finite values
    fail. The caller must declare any subsequent daily/annual aggregation.
    """
    maximum, delta, uv, rh = np.broadcast_arrays(
        *[
            np.asarray(v, dtype=float)
            for v in (
                daily_maximum_temperature_c,
                daily_temperature_range_c,
                daily_daytime_uv_w_m2,
                daily_relative_humidity_percent,
            )
        ]
    )
    values = (maximum, delta, uv, rh)
    if any(np.isinf(v).any() for v in values):
        raise ValueError("Stress inputs cannot contain infinity")
    if np.any(maximum <= -273.15) or np.any(delta < 0) or np.any(uv < 0):
        raise ValueError("Invalid temperature, range or UV irradiance")
    if np.any((rh < 0) | (rh > 100)):
        raise ValueError("RH must be between 0 and 100 percent")
    missing = np.logical_or.reduce([np.isnan(v) for v in values])
    maximum, delta, uv, rh = [np.where(missing, np.nan, v) for v in values]
    p = parameters
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            raw = (
                p.beta0
                * np.exp(-p.beta1 / (BOLTZMANN_EV_K * (maximum + 273.15)))
                * delta**p.beta2
                * uv**p.beta3
                * rh**p.beta4
            )
            annual = raw * p.rate_scale_to_year_inverse
    except FloatingPointError as error:
        raise ValueError("Stress-rate overflow; check calibration and units") from error
    return PhysicalRate(np.asarray(raw), np.asarray(annual), p.rate_scale_to_year_inverse)


def combined_rate_2021(
    *,
    module_temperature_mean_c: ArrayLike,
    module_temperature_upper_c: ArrayLike,
    module_temperature_lower_c: ArrayLike,
    relative_humidity_percent: ArrayLike,
    uv_dose_kwh_m2: ArrayLike,
    cycles_per_year: ArrayLike,
    parameters: DegradationParameters,
    rate_scale_to_year_inverse: float,
) -> PhysicalRate:
    """Equations 3-6, retaining the printed (273 + delta T)**theta term.

    Reuses the mapping kernel's input validation and Arrhenius equations, but
    does NOT change the existing 2019 mapping API. The 273 offset is a printed
    empirical expression, not a physical conversion of a temperature difference.
    Celsius-to-kelvin in Arrhenius terms uses 273.15. A_N, cycles/year and unit
    conversion are mandatory; Table 5 alone is not an executable calibration.
    A scale of 0.01 means native numerical %/year, 1 means fractional/year.
    Neither is inferred from the supplied parameters.
    """
    _scale(rate_scale_to_year_inverse)
    rates = _evaluate_degradation_rates(
        module_temperature_mean_c=module_temperature_mean_c,
        module_temperature_upper_c=module_temperature_upper_c,
        module_temperature_lower_c=module_temperature_lower_c,
        relative_humidity_percent=relative_humidity_percent,
        uv_dose_kwh_m2=uv_dose_kwh_m2,
        cycles_per_year=cycles_per_year,
        parameters=parameters,
        thermal_range_offset=273.0,
    )
    try:
        with np.errstate(over="raise", invalid="raise"):
            annual = rates.total * rate_scale_to_year_inverse
    except FloatingPointError as error:
        raise ValueError("Rate conversion overflow") from error
    return PhysicalRate(
        rates.total,
        annual,
        rate_scale_to_year_inverse,
        (rates.hydrolysis, rates.photodegradation, rates.thermomechanical),
    )
