"""PVDeg-backed thermal exposure screening, independent of geography.

This dimensionless index is not a calibrated degradation rate or service life.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

REFERENCE_IDS = ("pvdeg_software",)


def thermal_stress_index(
    temperature_c: np.ndarray,
    duration_hours: np.ndarray,
    *,
    activation_energy_kj_mol: float = 60.0,
    reference_temperature_c: float = 25.0,
) -> np.ndarray:
    """Return duration-weighted Arrhenius exposure relative to a constant reference.

    Temperature has shape ``(time, ...)`` in Celsius; durations are positive
    hours of shape ``(time,)``. Missing temperatures invalidate the whole cell,
    rather than letting PVDeg silently skip missing periods. Infinity, Kelvin
    temperatures at/below zero, invalid durations and parameters raise ValueError.
    PVDeg 0.7.4 is imported lazily; install ``energy-methods[pvdeg]``.
    No irradiance or humidity effect is assumed (p=n=0). Activation energy is
    a scenario parameter, not a fitted material property.
    """
    values = np.asarray(temperature_c, dtype=float)
    hours = np.asarray(duration_hours, dtype=float)
    if values.ndim < 1 or values.shape[0] == 0 or hours.shape != (values.shape[0],):
        raise ValueError("Expected temperatures (time, ...) and matching duration_hours")
    if not np.isfinite(hours).all() or (hours <= 0).any():
        raise ValueError("Duration hours must be finite and positive")
    if np.isinf(values).any() or (values <= -273.15).any():
        raise ValueError("Temperatures must be Celsius above absolute zero or NaN")
    if (
        not np.isfinite([activation_energy_kj_mol, reference_temperature_c]).all()
        or not 0 < activation_energy_kj_mol <= 200
        or not -100 <= reference_temperature_c <= 150
    ):
        raise ValueError("Use activation energy in (0, 200] kJ/mol and reference in [-100, 150] C")
    from pvdeg import degradation

    shape = values.shape[1:]
    flat = values.reshape(values.shape[0], -1)
    valid = np.isfinite(flat).all(axis=0)
    output = np.full(flat.shape[1], np.nan)
    if valid.any():
        # ndarray weights broadcast along time; PVDeg then sums each cell column.
        weights = hours[:, None] / hours.sum()
        dose = degradation.arrhenius(
            temperature=pd.DataFrame(flat[:, valid]),
            elapsed_time=weights,
            Ea=activation_energy_kj_mol,
        )
        reference = degradation.arrhenius(
            temperature=pd.Series([reference_temperature_c]), Ea=activation_energy_kj_mol
        )
        output[valid] = np.asarray(dose) / float(reference)
    return output.reshape(shape)
