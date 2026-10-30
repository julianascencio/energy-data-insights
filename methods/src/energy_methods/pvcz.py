"""Karin, Jones and Jain (2019) PVCZ thresholds and Arrhenius stress.

Table I: ten temperature zones by five specific-humidity zones. This is a
stressor classification, not a predicted degradation rate or lifetime.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.special import logsumexp

from energy_methods.climate_zones import ClimateProvenance, ClimateZones

REFERENCE_IDS = ("ascencio_vasquez_2021_thesis", "karin_2019_pvcz")
TEMPERATURE_THRESHOLDS_C = (14.0, 19.0, 24.0, 29.0, 34.0, 39.0, 44.0, 49.0, 54.0)
HUMIDITY_THRESHOLDS_G_KG = (3.0, 4.1, 5.9, 10.5)
ZONE_CODES = ("", *(f"T{t}:H{h}" for h in range(1, 6) for t in range(1, 11)))


def _interval_label(value: int, edges: tuple[float, ...], unit: str) -> str:
    if value == 1:
        return f"<{edges[0]:g} {unit}"
    if value == len(edges) + 1:
        return f"≥{edges[-1]:g} {unit}"
    return f"{edges[value - 2]:g}-<{edges[value - 1]:g} {unit}"


ZONE_LABELS = (
    "Unclassified",
    *(
        f"Module stress {_interval_label(t, TEMPERATURE_THRESHOLDS_C, '°C')}; "
        f"humidity {_interval_label(h, HUMIDITY_THRESHOLDS_G_KG, 'g/kg')}"
        for h in range(1, 6)
        for t in range(1, 11)
    ),
)


def equivalent_temperature(
    temperature_c: ArrayLike, *, activation_energy_ev: float = 1.1, duration_hours: ArrayLike = 1.0
) -> NDArray[np.float64]:
    """Arrhenius-equivalent °C over the last axis, weighted by interval duration.

    Supply module temperatures including nights. Any missing interval makes its
    result missing; there is no gap filling. A time series with explicit missing
    rows is required to represent gaps. Duration cannot reveal omitted rows.
    """
    temperature = np.asarray(temperature_c, dtype=float)
    if temperature.ndim < 1 or temperature.shape[-1] == 0:
        raise ValueError("A nonempty time axis is required")
    dt = np.broadcast_to(np.asarray(duration_hours, dtype=float), temperature.shape)
    if (
        not np.isfinite(activation_energy_ev)
        or activation_energy_ev <= 0
        or np.isinf(temperature).any()
        or np.any(temperature <= -273.15)
        or not np.isfinite(dt).all()
        or np.any(dt <= 0)
    ):
        raise ValueError("Positive activation energy/durations and physical temperatures required")
    a = activation_energy_ev / 8.617333262145e-5  # Boltzmann constant in eV/K
    mean_log = logsumexp(-a / (temperature + 273.15) + np.log(dt), axis=-1)
    mean_log -= np.log(np.sum(dt, axis=-1))
    return np.asarray(-a / mean_log - 273.15)


def classify_pvcz(
    equivalent_temperature_c: ArrayLike,
    specific_humidity_g_kg: ArrayLike,
    *,
    provenance: ClimateProvenance,
) -> ClimateZones:
    """Apply fixed published boundaries; equality enters the warmer/wetter class.

    Humidity is specific humidity (g/kg), never relative humidity (%). Positive
    IDs are the upstream zero-based PVCZ ID + 1, leaving zero for missing inputs.
    Use the reference 1.1 eV equivalent temperature for the published scheme.
    """
    t, h = np.broadcast_arrays(
        np.asarray(equivalent_temperature_c, dtype=float),
        np.asarray(specific_humidity_g_kg, dtype=float),
    )
    if (
        np.isinf(t).any()
        or np.isinf(h).any()
        or np.any(t <= -273.15)
        or np.any((h < 0) | (h > 1000))
    ):
        raise ValueError("Physical temperature and specific humidity in g/kg required")
    good = np.isfinite(t) & np.isfinite(h)
    ids = np.where(
        good,
        np.searchsorted(TEMPERATURE_THRESHOLDS_C, t, side="right")
        + 10 * np.searchsorted(HUMIDITY_THRESHOLDS_G_KG, h, side="right")
        + 1,
        0,
    )
    return ClimateZones(
        "pvcz-2019", ids.astype(np.int64), ZONE_CODES, ZONE_LABELS, provenance, REFERENCE_IDS
    )
