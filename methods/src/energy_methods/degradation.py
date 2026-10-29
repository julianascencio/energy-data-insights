"""Climate-driven PV degradation: thesis Eqs. 3.14-3.17 and Section 6.4.

Calibration is mandatory and module-specific. Rates use the numerical percent
per year convention of the 2019 mapping paper, not fractional loss per year.
These are climate degradation indicators, not observed performance loss rates.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

REFERENCE_IDS = (
    "ascencio_vasquez_2021_thesis",
    "ascencio_vasquez_2019_degradation_mapping",
    "kaaya_2019_degradation",
)
BOLTZMANN_EV_K = 8.62e-5  # Publication value, deliberately retained for reproducibility.


@dataclass(frozen=True, slots=True, kw_only=True)
class DegradationParameters:
    """One calibration, including its numerical normalization and provenance.

    Activation energies are in eV; n, x and theta are positive exponents.
    Prefactors and a_n must be fitted together using RH in percent, UV dose in
    kWh/m²/year, temperatures in kelvin, cycles/year, and rates in %/year.
    No generic c-Si calibration or normalization is silently substituted.
    """

    a_h: float
    a_p: float
    a_tm: float
    e_h: float
    e_p: float
    e_tm: float
    n: float
    x: float
    theta: float
    a_n: float
    calibration_id: str
    calibration_source: str

    def __post_init__(self) -> None:
        for name in ("a_h", "a_p", "a_tm", "e_h", "e_p", "e_tm", "n", "x", "theta", "a_n"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{name} must be a finite number")
            if not np.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and nonnegative")
            if name in {"n", "x", "theta", "a_n"} and value == 0:
                raise ValueError(f"{name} must be positive")
        for name in ("calibration_id", "calibration_source"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required")

    def to_dict(self) -> dict[str, object]:
        """Return a portable, JSON-serializable calibration record."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DegradationRates:
    """Nonnegative mechanism and combined rates, all in %/year; NaN is missing."""

    hydrolysis: NDArray[np.float64]
    photodegradation: NDArray[np.float64]
    thermomechanical: NDArray[np.float64]
    total: NDArray[np.float64]


def degradation_rates(
    *,
    module_temperature_mean_c: ArrayLike,
    module_temperature_upper_c: ArrayLike,
    module_temperature_lower_c: ArrayLike,
    relative_humidity_percent: ArrayLike,
    uv_dose_kwh_m2: ArrayLike,
    cycles_per_year: ArrayLike,
    parameters: DegradationParameters,
) -> DegradationRates:
    """Evaluate Eqs. 3.14-3.17 on broadcastable annual climate stresses.

    Temperature inputs are °C (converted to K only inside Arrhenius terms).
    RH is 0-100 percent, UV is annual integrated dose in kWh/m², and cycling
    frequency is cycles/year. Upper/lower temperatures must bound the mean.
    Their aggregation and RH's effective/ambient interpretation must match the
    calibration; this function does not infer either from weather.

    Missing any input makes all four outputs NaN at that position. Invalid
    finite values, infinities, overflow and negative combined rates raise.
    The total is A_N * product(1 + k_i) - 1 exactly as printed, including the
    subtraction OUTSIDE the normalization. It is not the sum of mechanisms.
    """
    mean, upper, lower, rh, uv, cycles = np.broadcast_arrays(
        *[
            np.asarray(value, dtype=float)
            for value in (
                module_temperature_mean_c,
                module_temperature_upper_c,
                module_temperature_lower_c,
                relative_humidity_percent,
                uv_dose_kwh_m2,
                cycles_per_year,
            )
        ]
    )
    inputs = (mean, upper, lower, rh, uv, cycles)
    if any(np.isinf(value).any() for value in inputs):
        raise ValueError("Climate stresses cannot contain infinity")
    if any(np.any(value <= -273.15) for value in (mean, upper, lower)):
        raise ValueError("Module temperatures must be above absolute zero")
    if np.any((lower > mean) | (mean > upper)):
        raise ValueError("Lower <= mean <= upper module temperature is required")
    if np.any((rh < 0) | (rh > 100)):
        raise ValueError("Relative humidity must be in percent between 0 and 100")
    if np.any(uv < 0) or np.any(cycles < 0):
        raise ValueError("UV dose and cycles per year must be nonnegative")
    missing = np.logical_or.reduce([np.isnan(value) for value in inputs])
    # Mask all inputs together: a missing cell must not cause incidental overflow.
    mean, upper, lower, rh, uv, cycles = [np.where(missing, np.nan, v) for v in inputs]
    p = parameters
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            humidity = rh**p.n
            hydrolysis = p.a_h * humidity * np.exp(-p.e_h / (BOLTZMANN_EV_K * (mean + 273.15)))
            photo = (
                p.a_p
                * uv**p.x
                * (1 + humidity)
                * np.exp(-p.e_p / (BOLTZMANN_EV_K * (mean + 273.15)))
            )
            thermal = (
                p.a_tm
                * (upper - lower) ** p.theta
                * cycles
                * np.exp(-p.e_tm / (BOLTZMANN_EV_K * (upper + 273.15)))
            )
            # log1p/expm1 retain tiny rates when A_N == 1.
            total = np.expm1(
                np.log(p.a_n) + np.log1p(hydrolysis) + np.log1p(photo) + np.log1p(thermal)
            )
    except FloatingPointError as error:
        raise ValueError("Degradation calculation overflow; check calibration and units") from error
    if np.any(total < 0):
        raise ValueError("Calibration a_n produces negative total degradation; do not clip it")
    return DegradationRates(
        *(np.asarray(value, dtype=float) for value in (hydrolysis, photo, thermal, total))
    )
