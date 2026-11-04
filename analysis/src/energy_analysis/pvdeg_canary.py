"""Canary Islands thermal screening from monthly climate normals and PVDeg."""

from __future__ import annotations

import calendar
from pathlib import Path

import numpy as np
import rasterio

from energy_methods.pvdeg import thermal_stress_index

REFERENCE_IDS = ("pvdeg_software", "canaryclim_2025_data", "patino_2023_canaryclim")
MONTH_HOURS = np.array([calendar.monthrange(2001, m)[1] * 24 for m in range(1, 13)])


def screen_climate_tile(
    path: Path, *, module_offset_c: float = 20.0, activation_energy_kj_mol: float = 60.0
) -> tuple[np.ndarray, dict]:
    """Return relative exposure and raster profile from 12 scaled Celsius bands.

    The constant module-air offset is a scenario, not a thermal model. Monthly
    means cannot resolve daytime peaks or diurnal Arrhenius exposure.
    """
    if not np.isfinite(module_offset_c) or not 0 <= module_offset_c <= 60:
        raise ValueError("Module-air offset must be between 0 and 60 C")
    with rasterio.open(path) as source:
        if source.count != 12 or source.tags().get("units") != "degC":
            raise ValueError("Expected 12 monthly Celsius bands with explicit units")
        raw = source.read(masked=True).astype(float).filled(np.nan)
        values = raw * np.array(source.scales)[:, None, None]
        values += np.array(source.offsets)[:, None, None]
        profile = source.profile.copy()
    result = thermal_stress_index(
        values + module_offset_c,
        MONTH_HOURS,
        activation_energy_kj_mol=activation_energy_kj_mol,
    )
    return result, profile


def write_stress_geotiff(path: Path, values: np.ndarray, profile: dict) -> None:
    """Export a dimensionless screening map preserving the input georeferencing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    profile = {**profile, "count": 1, "dtype": "float32", "nodata": -9999.0}
    with rasterio.open(path, "w", **profile) as target:
        target.write(np.where(np.isfinite(values), values, -9999).astype("float32"), 1)
        target.update_tags(units="1", evidence="modeled thermal screening; not annual degradation")
