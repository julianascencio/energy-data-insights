"""Canary hourly-weather mechanism atlas; no spatial interpolation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from energy_data_retrieval.pvdeg import to_pvdeg_weather
from energy_methods.pvdeg_mechanisms import relative_arrhenius_exposure

REFERENCE_IDS = ("pvdeg_software", "pvgis_5_api")
METRICS = {
    "thermal": ("Thermal exposure", "Relative exposure", "magma"),
    "damp_heat": ("Damp-heat / hydrolysis stress", "Relative exposure (n=1)", "YlGnBu"),
    "photothermal": ("Broadband light + heat stress", "Relative exposure (p=1); not UV", "inferno"),
    "combined": ("Light + moisture + heat stress", "Relative exposure (n=p=1)", "plasma"),
    "surface_rh": ("Module surface moisture", "Mean RH (%)", "Blues"),
    "front_rh": ("Front encapsulant moisture", "Mean RH (%), EVA W001", "Blues"),
    "back_rh": ("Back encapsulant moisture", "Mean RH (%), EVA / PET", "Blues"),
    "backsheet_rh": ("Backsheet moisture", "Mean RH (%), PET W017", "Blues"),
    "solder_fatigue": ("Solder fatigue", "PVDeg damage metric (kPa)", "cividis"),
}


def analyze_weather(weather: pd.DataFrame, location: dict[str, Any]) -> dict[str, float]:
    """Run nine PVDeg stress/material metrics for a complete 8760-hour TMY.

    Fixed 28-degree south-facing, open-rack glass/polymer module; SAPM temperature
    with 10 m wind. Surface RH is capped at saturation for the stress calculation;
    moisture-model RH is retained as returned. PVDeg's EVA/PET defaults and initial
    moisture state are scenarios, not fitted Canary module properties.
    """
    from pvdeg import fatigue, humidity, spectral
    from pvlib import solarposition, temperature

    weather = to_pvdeg_weather(weather)
    expected = pd.date_range("2023-01-01", periods=8760, freq="h", tz="UTC")
    if not weather.index.equals(expected):
        raise ValueError("Expected complete 2023 calendar axis for the modeled TMY")
    lat, lon = float(location["latitude"]), float(location["longitude"])
    altitude = float(location["elevation"])
    offset = float(location["irradiance_time_offset"])
    if not np.isfinite([lat, lon, altitude, offset]).all() or not -1 <= offset <= 1:
        raise ValueError("Invalid location or irradiance time offset")
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ValueError("Invalid coordinates")
    # PVGIS irradiance applies at an offset from each hourly weather timestamp.
    sun = solarposition.get_solarposition(
        weather.index + pd.Timedelta(hours=offset), lat, lon, altitude=altitude
    )
    sun.index = weather.index
    meta = {"latitude": lat, "longitude": lon, "altitude": altitude, "tz": "UTC"}
    poa = spectral.poa_irradiance(
        weather,
        meta,
        sol_position=sun,
        surface_tilt=28,
        surface_azimuth=180,
        albedo=0.25,
        sky_model="isotropic",
    )
    irradiance = poa["poa_global"]
    parameters = temperature.TEMPERATURE_MODEL_PARAMETERS["sapm"]["open_rack_glass_polymer"]
    module = temperature.sapm_module(
        irradiance,
        weather.temp_air,
        weather.wind_speed,
        a=parameters["a"],
        b=parameters["b"],
    )
    cell = temperature.sapm_cell_from_module(module, irradiance, parameters["deltaT"])
    moisture = humidity.module(
        weather,
        meta,
        poa=poa,
        temp_module=module,
        backsheet_thickness=0.3,
        back_encap_thickness=0.46,
    )
    if not np.isfinite(moisture.to_numpy()).all():
        raise ValueError("PVDeg returned nonfinite moisture results")
    surface = moisture.RH_surface_outside.clip(upper=100)
    results = {}
    for name, n, p in [
        ("thermal", 0, 0),
        ("damp_heat", 1, 0),
        ("photothermal", 0, 1),
        ("combined", 1, 1),
    ]:
        results[name] = relative_arrhenius_exposure(
            module,
            surface,
            irradiance,
            humidity_exponent=n,
            irradiance_exponent=p,
        )
    for name, column in [
        ("surface_rh", "RH_surface_outside"),
        ("front_rh", "RH_front_encap"),
        ("back_rh", "RH_back_encap"),
        ("backsheet_rh", "RH_backsheet"),
    ]:
        results[name] = float(moisture[column].mean())
    # Fixed UTC days for a reproducible TMY comparison; no DST shifts.
    results["solder_fatigue"] = float(fatigue.solder_fatigue(weather, meta, temp_cell=cell))
    if not np.isfinite(list(results.values())).all():
        raise ValueError("PVDeg returned nonfinite mechanism metrics")
    return results


def analyze_manifest(directory: Path) -> pd.DataFrame:
    """Verify fixture hashes and recompute each site's metrics offline."""
    manifest = json.loads((directory / "manifest.json").read_text())
    rows = []
    for site in manifest["sites"]:
        path = directory / site["file"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != site["sha256"]:
            raise ValueError(f"Weather fixture differs from provenance: {path.name}")
        frame = pd.read_csv(path, index_col="time")
        frame.index = pd.to_datetime(frame.index, utc=True)
        location = site["inputs"]["location"]
        rows.append(
            {
                "name": site["name"],
                "longitude": location["longitude"],
                "latitude": location["latitude"],
                **analyze_weather(frame, location),
            }
        )
    return pd.DataFrame(rows)
