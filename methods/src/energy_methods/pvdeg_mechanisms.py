"""PVDeg mechanism screening from complete hourly module stress histories.

All outputs are scenario exposure or material-model metrics, not measured power
loss. In particular, broadband light-assisted exposure is not spectral UV damage.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

REFERENCE_IDS = ("pvdeg_software",)


def relative_arrhenius_exposure(
    temperature_c: pd.Series,
    humidity_pct: pd.Series,
    irradiance_w_m2: pd.Series,
    *,
    humidity_exponent: float = 1.0,
    irradiance_exponent: float = 0.0,
    activation_energy_kj_mol: float = 60.0,
) -> float:
    """Hourly exposure relative to constant 25 C, 50% RH and 1000 W/m2.

    Requires aligned, finite hourly series. Exponents and activation energy are
    explicit screening assumptions; no calibrated degradation prefactor is used.
    A ratio of two means twice the model exposure, not twice the power loss.
    """
    arrays = [temperature_c, humidity_pct, irradiance_w_m2]
    if any(not isinstance(x, pd.Series) for x in arrays):
        raise ValueError("Inputs must be pandas Series")
    index = temperature_c.index
    if (
        not isinstance(index, pd.DatetimeIndex)
        or index.tz is None
        or len(index) < 2
        or any(not x.index.equals(index) for x in arrays)
        or not (index.to_series().diff().iloc[1:] == pd.Timedelta(hours=1)).all()
    ):
        raise ValueError("Expected aligned timezone-aware hourly series")
    if not all(np.isfinite(x).all() for x in arrays):
        raise ValueError("Missing or infinite stress inputs are not supported")
    if (
        (temperature_c <= -273.15).any()
        or not humidity_pct.between(0, 100).all()
        or (irradiance_w_m2 < 0).any()
    ):
        raise ValueError("Invalid Celsius, percent humidity or irradiance")
    params = [activation_energy_kj_mol, humidity_exponent, irradiance_exponent]
    if not np.isfinite(params).all() or not 0 < params[0] <= 200 or min(params[1:]) < 0:
        raise ValueError("Expected positive Ea <= 200 kJ/mol and nonnegative exponents")
    from pvdeg import degradation

    kwargs = {"Ea": params[0], "n": params[1], "p": params[2]}
    dose = degradation.arrhenius(
        temperature=temperature_c, RH=humidity_pct, irradiance=irradiance_w_m2, **kwargs
    )
    reference = degradation.arrhenius(
        temperature=pd.Series([25.0]),
        RH=pd.Series([50.0]),
        irradiance=pd.Series([1000.0]),
        **kwargs,
    )
    return float(dose / (len(index) * reference))
