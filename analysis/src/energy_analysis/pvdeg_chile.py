"""Native-grid Chile thermal screening using the shared PVDeg Arrhenius method."""

from __future__ import annotations

import hashlib
import json
from contextlib import ExitStack
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import Window

from energy_analysis.pvdeg_canary import MONTH_HOURS, write_stress_geotiff
from energy_methods.pvdeg import thermal_stress_index

REFERENCE_IDS = (
    "pvdeg_software",
    "chelsa_2021_climatologies",
    "karger_2017_chelsa",
    "natural_earth_countries",
)


def screen_monthly_rasters(
    paths: list[Path],
    *,
    module_offset_c: float = 20.0,
    activation_energy_kj_mol: float = 60.0,
    rows_per_batch: int = 128,
) -> tuple[np.ndarray, dict]:
    """Calculate native-grid exposure from twelve aligned encoded Kelvin bands.

    Preserve every source centre, applying nodata before scale/offset conversion.
    All twelve months are required per cell. Memory is bounded by a row batch
    plus one output raster. The constant air-to-module offset is a scenario.
    """
    if len(paths) != 12 or len(set(paths)) != 12:
        raise ValueError("Provide twelve distinct paths in January-December order")
    if type(rows_per_batch) is not int or rows_per_batch < 1:
        raise ValueError("rows_per_batch must be a positive integer")
    if not np.isfinite(module_offset_c) or not 0 <= module_offset_c <= 60:
        raise ValueError("Module-air offset must be in [0, 60] C")
    with ExitStack() as stack:
        sources = [stack.enter_context(rasterio.open(path)) for path in paths]
        first = sources[0]
        for month, source in enumerate(sources, 1):
            if (
                source.count != 1
                or source.crs != rasterio.crs.CRS.from_epsg(4326)
                or source.shape != first.shape
                or not np.allclose(source.transform, first.transform, atol=1e-10, rtol=0)
                or not np.allclose(source.res, (1 / 120, 1 / 120), atol=1e-10, rtol=0)
                or source.tags().get("variable_unit") != "K"
                or source.tags().get("month") != str(month)
                or source.tags().get("datetime") != "1981-2010"
                or source.nodata is None
                or not np.isfinite([source.scales[0], source.offsets[0]]).all()
                or source.scales[0] <= 0
            ):
                raise ValueError("Expected aligned native monthly CHELSA Kelvin grids")
        result = np.full(first.shape, np.nan, dtype=np.float32)
        for row in range(0, first.height, rows_per_batch):
            height = min(rows_per_batch, first.height - row)
            window = Window.from_slices((row, row + height), (0, first.width))
            temperatures = []
            for source in sources:
                values = source.read(1, window=window, masked=True).astype(float).filled(np.nan)
                temperatures.append(values * source.scales[0] + source.offsets[0] - 273.15)
            result[row : row + height] = thermal_stress_index(
                np.stack(temperatures) + module_offset_c,
                MONTH_HOURS,
                activation_energy_kj_mol=activation_energy_kj_mol,
            )
        return result, first.profile.copy()


def run_chile_study(directory: Path, output: Path | None = None) -> tuple[np.ndarray, dict, dict]:
    """Verify provenance, calculate the central scenario and optionally export GeoTIFF.

    Exports carry the assumed offset, activation energy, reference and baseline.
    The result is dimensionless relative exposure, not percent degradation/year.
    """
    manifest = json.loads((directory / "pvdeg_chile_provenance.json").read_text())
    records = manifest["months"]
    if [record["month"] for record in records] != list(range(1, 13)):
        raise ValueError("Manifest must contain ordered months 1-12")
    for record in [
        *records,
        {"file": manifest["boundary_file"], "sha256": manifest["boundary_sha256"]},
    ]:
        if (
            hashlib.sha256((directory / record["file"]).read_bytes()).hexdigest()
            != record["sha256"]
        ):
            raise ValueError("Input checksum differs from provenance")
    scenario = manifest["scenario"]
    if (
        scenario["reference_temperature_c"] != 25
        or scenario["humidity_exponent"] != 0
        or scenario["irradiance_exponent"] != 0
    ):
        raise ValueError("Unsupported reference or humidity/irradiance scenario")
    values, profile = screen_monthly_rasters(
        [directory / record["file"] for record in records],
        module_offset_c=scenario["module_offset_c"],
        activation_energy_kj_mol=scenario["activation_energy_kj_mol"],
    )
    if output is not None:
        write_stress_geotiff(output, values, profile)
        with rasterio.open(output, "r+") as target:
            target.update_tags(
                **{k: str(v) for k, v in scenario.items()},
                climate_period="1981-2010",
                pvdeg_version="0.7.4",
                coverage=manifest["coverage"],
            )
    return values, profile, manifest
