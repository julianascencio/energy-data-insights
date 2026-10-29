"""Weather-to-stress transformations from the 2019 degradation mapping study."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

REFERENCE_IDS = (
    "ascencio_vasquez_2021_thesis",
    "ascencio_vasquez_2019_degradation_mapping",
    "faiman_2008_temperature",
    "wald_2018_spectral",
    "huld_amillo_2015_performance",
)


def faiman_from_ghi(
    ambient_temperature_c: ArrayLike,
    ghi_wm2: ArrayLike,
    wind_speed_10m_ms: ArrayLike,
    *,
    u0: float = 26.9,
    u1: float = 6.2,
    module_height_m: float = 2,
) -> NDArray[np.float64]:
    """Module °C from the study's GHI-based Faiman Eq. 10 (open-rack c-Si).

    Wind is scaled from 10 m to module height with exponent 0.2 (Eq. 2).
    This is the publication's horizontal-irradiance approximation, not a POA model.
    NaN propagates; physically invalid inputs and infinite outputs fail.
    """
    if (
        not np.isfinite([u0, u1, module_height_m]).all()
        or u0 <= 0
        or u1 < 0
        or module_height_m <= 0
    ):
        raise ValueError("Faiman requires positive u0/height and nonnegative u1")
    temperature, ghi, wind = np.broadcast_arrays(
        *[
            np.asarray(value, dtype=float)
            for value in (ambient_temperature_c, ghi_wm2, wind_speed_10m_ms)
        ]
    )
    if any(np.isinf(value).any() for value in (temperature, ghi, wind)):
        raise ValueError("Weather cannot contain infinity")
    if np.any(temperature <= -273.15) or np.any(ghi < 0) or np.any(wind < 0):
        raise ValueError("Invalid temperature, irradiance or wind speed")
    result = temperature + ghi / (u0 + u1 * wind * (module_height_m / 10) ** 0.2)
    if np.isinf(result).any():
        raise ValueError("Module temperature overflow")
    return np.asarray(result, dtype=float)


def wald_uv_irradiance(ghi_wm2: ArrayLike, toa_wm2: ArrayLike) -> NDArray[np.float64]:
    """Estimate UVA+UVB (280-400 nm) in W/m², study Eqs. 5-8.

    kt is clamped to [0.1, 0.7]. Zero GHI with finite TOA returns zero.
    Positive GHI with zero TOA is unavailable (NaN), not fabricated nighttime UV.
    Missing inputs propagate. UV index and ERA5 UV to 440 nm are not inputs.
    """
    ghi, toa = np.broadcast_arrays(
        np.asarray(ghi_wm2, dtype=float), np.asarray(toa_wm2, dtype=float)
    )
    if np.isinf(ghi).any() or np.isinf(toa).any() or np.any(ghi < 0) or np.any(toa < 0):
        raise ValueError("GHI and TOA must be nonnegative finite values or NaN")
    kt = np.divide(ghi, toa, out=np.full(ghi.shape, np.nan), where=toa > 0)
    kt = np.clip(kt, 0.1, 0.7)
    result = ((1.897 - 0.860 * kt) * 1e-3 + (7.210 - 2.365 * kt) * 1e-2) * ghi
    return np.where((ghi == 0) & np.isfinite(toa), 0, result)
