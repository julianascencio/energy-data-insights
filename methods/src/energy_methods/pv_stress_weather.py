"""POA-based temperature, UV and humidity models, 2021 study Eqs. 7-17.

All arrays must be finite. Filter night and missing observations explicitly
before calibration; these functions do not align timestamps or impute weather.
"""

from __future__ import annotations

from typing import Literal

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.optimize import least_squares

from energy_methods.degradation_weather import faiman_from_ghi
from energy_methods.pv_reliability import _finite

REFERENCE_IDS = ("ascencio_vasquez_2021_thesis", "kaaya_2021_uncertainties")


def _weather(temperature: ArrayLike, poa: ArrayLike) -> tuple[NDArray, NDArray]:
    t, g = np.broadcast_arrays(_finite(temperature, "temperature"), _finite(poa, "poa"))
    if np.any(t <= -273.15) or np.any(g < 0):
        raise ValueError("Invalid temperature or negative POA irradiance")
    return t, g


def ross_temperature(
    ambient_temperature_c: ArrayLike, poa_w_m2: ArrayLike, *, coefficient: float
) -> NDArray[np.float64]:
    """Equation 7, module °C; coefficient in °C m²/W is explicit."""
    t, g = _weather(ambient_temperature_c, poa_w_m2)
    if not np.isfinite(coefficient) or coefficient < 0:
        raise ValueError("Ross coefficient must be finite and nonnegative")
    return t + coefficient * g


def faiman_temperature(
    ambient_temperature_c: ArrayLike,
    poa_w_m2: ArrayLike,
    wind_speed_ms: ArrayLike,
    *,
    u0: float,
    u1: float,
) -> NDArray[np.float64]:
    """Equation 8, module °C using POA and wind at the calibration's height.

    Reuse the existing algebra with unity wind-height scaling. No GHI-to-POA
    substitution, wind-height conversion or site-independent coefficient fit.
    """
    t, g = _weather(ambient_temperature_c, poa_w_m2)
    wind = _finite(wind_speed_ms, "wind speed")
    return faiman_from_ghi(t, g, wind, u0=u0, u1=u1, module_height_m=10)


def linear_uv(poa_w_m2: ArrayLike, *, slope: float, intercept: float = 0) -> NDArray:
    """Equation 9, UV W/m². Outputs outside [0, POA] fail rather than clip."""
    g = _finite(poa_w_m2, "POA")
    if not np.isfinite([slope, intercept]).all():
        raise ValueError("UV coefficients must be finite")
    return _check_uv(g, slope * g + intercept)


def _check_uv(poa: NDArray, uv: NDArray) -> NDArray:
    if np.any(poa < 0) or not np.isfinite(uv).all() or np.any((uv < 0) | (uv > poa)):
        raise ValueError("UV model is outside its physical domain: require 0 <= UV <= POA")
    return uv


def wald_uv(
    poa_w_m2: ArrayLike, clearness_index: ArrayLike, *, a: float = 7.210, b: float = 2.365
) -> NDArray:
    """Equations 10-14, UV 280-400 nm in W/m²; kt clamped to [0.1, 0.7].

    The default is original Wald. Modified coefficients use ``a - b*kt``;
    negative b in Table 9 is retained, not silently sign-corrected.
    """
    g, kt = np.broadcast_arrays(_finite(poa_w_m2, "POA"), _finite(clearness_index, "kt"))
    if not np.isfinite([a, b]).all() or np.any(kt < 0):
        raise ValueError("Invalid UV coefficients or negative clearness index")
    kt = np.clip(kt, 0.1, 0.7)
    return _check_uv(g, g * ((a - b * kt) * 0.01 + (1.897 - 0.860 * kt) * 0.001))


def airmass_uv(poa_w_m2: ArrayLike, air_mass: ArrayLike, *, coefficients: ArrayLike) -> NDArray:
    """Equation 15: POA times a fourth-degree polynomial in air mass.

    Five coefficients ordered m0..m4 are required. Air mass must be >=1;
    extrapolation producing a UV fraction outside [0,1] fails.
    """
    g, am = np.broadcast_arrays(_finite(poa_w_m2, "POA"), _finite(air_mass, "air mass"))
    c = _finite(coefficients, "coefficients")
    if c.shape != (5,) or np.any(am < 1):
        raise ValueError("Five coefficients and air mass >= 1 are required")
    return _check_uv(g, g * np.polynomial.polynomial.polyval(am, c))


def buck_vapour_pressure(temperature_c: ArrayLike) -> NDArray:
    """Equation 17 saturation vapour pressure, kPa, with ice/water branches.

    Values 0.61115/0.61121 are kPa despite the nomenclature's Pa label.
    The documented operating domain here is -80..60 °C; no extrapolation.
    """
    t = _finite(temperature_c, "temperature")
    if np.any((t < -80) | (t > 60)):
        raise ValueError("Buck temperature must be within -80 to 60 degrees C")
    ice = 0.61115 * np.exp((23.036 - t / 333.70) * t / (279.82 + t))
    water = 0.61121 * np.exp((18.678 - t / 234.84) * t / (257.14 + t))
    return np.where(t < 0, ice, water)


def buck_relative_humidity(ambient_temperature_c: ArrayLike, dewpoint_c: ArrayLike) -> NDArray:
    """Equation 16, percent; reject dewpoint above ambient instead of clipping."""
    ambient, dewpoint = np.broadcast_arrays(
        _finite(ambient_temperature_c, "ambient"), _finite(dewpoint_c, "dewpoint")
    )
    if np.any(dewpoint > ambient):
        raise ValueError("Dewpoint cannot exceed ambient temperature")
    return 100 * buck_vapour_pressure(dewpoint) / buck_vapour_pressure(ambient)


def fit_temperature_model(
    ambient_temperature_c: ArrayLike,
    poa_w_m2: ArrayLike,
    measured_module_c: ArrayLike,
    *,
    model: Literal["ross", "faiman"],
    wind_speed_ms: ArrayLike | None = None,
) -> dict[str, float]:
    """Least-squares coefficients on a declared calibration interval only.

    Equal one-dimensional shapes, positive POA, and an identifiable design are
    required. Evaluate errors on another year; do not mix train and test records.
    """
    t, g, measured = [
        _finite(v, name)
        for v, name in (
            (ambient_temperature_c, "ambient"),
            (poa_w_m2, "POA"),
            (measured_module_c, "module temperature"),
        )
    ]
    if t.ndim != 1 or t.shape != g.shape or t.shape != measured.shape or t.size < 3:
        raise ValueError("Calibration requires matching vectors with at least three observations")
    _weather(t, g)
    if np.any(g <= 0) or np.any(measured <= -273.15):
        raise ValueError("Calibration requires positive POA and physical module temperatures")
    if model == "ross":
        coefficient = float(np.dot(g, measured - t) / np.dot(g, g))
        if coefficient < 0:
            raise ValueError("Calibration produces a negative Ross coefficient")
        return {"coefficient": coefficient}
    if model != "faiman" or wind_speed_ms is None:
        raise ValueError("Choose ross or faiman; faiman requires wind speed")
    wind = _finite(wind_speed_ms, "wind")
    if wind.shape != t.shape or np.any(wind < 0) or np.ptp(wind) == 0:
        raise ValueError("Faiman requires matching, nonnegative, varying wind speed")
    result = least_squares(
        lambda p: faiman_temperature(t, g, wind, u0=p[0], u1=p[1]) - measured,
        [25.0, 6.0],
        bounds=([1e-6, 0], [np.inf, np.inf]),
        ftol=1e-12,
        gtol=1e-12,
        xtol=1e-12,
    )
    if not result.success or np.linalg.matrix_rank(result.jac) < 2:
        raise ValueError("Faiman calibration failed or is not identifiable")
    return {"u0": float(result.x[0]), "u1": float(result.x[1])}
