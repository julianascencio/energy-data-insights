"""Recompute the attributed degradation gallery from small annual stress tables."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.colors import BoundaryNorm, ListedColormap
from shapely.geometry import shape

from energy_data_retrieval.storage import sha256_file
from energy_methods.country_boundaries import polygons
from energy_methods.degradation import DegradationParameters
from energy_methods.degradation_mapping import RATE_VARIABLES, STRESS_UNITS, map_degradation

TITLES = ("Hydrolysis", "Photodegradation", "Thermomechanical", "Combined rate")


def prepare_gallery(study_output: Path, destination: Path, boundaries: Path) -> Path:
    """Export a completed study's verified annual inputs; never download or invent data.

    Keep the complete original study outside Git. The small CSV bundle preserves
    every grid row, including ocean/missing rows, and records original hashes.
    ``boundaries`` is the existing attributed Natural Earth gallery GeoJSON.
    """
    original = json.loads((study_output / "manifest.json").read_text())
    if original.get("complete") is not True:
        raise ValueError("A completed degradation study is required")
    names = ("annual_stresses.nc", "degradation.nc", "parameters.json", "source_cells.csv")
    for name in names:
        if sha256_file(study_output / name) != original["outputs_sha256"][name]:
            raise ValueError(f"Study output checksum mismatch: {name}")
    destination.mkdir(parents=True, exist_ok=True)
    with xr.open_dataset(study_output / "annual_stresses.nc") as dataset:
        annual = dataset.load()
    with xr.open_dataset(study_output / "degradation.nc") as dataset:
        rates = dataset.load()
    annual.to_dataframe().reset_index().to_csv(
        destination / "degradation_stresses.csv", index=False
    )
    rates.to_dataframe().reset_index().to_csv(
        destination / "degradation_reference.csv", index=False
    )
    (destination / "degradation_parameters.json").write_bytes(
        (study_output / "parameters.json").read_bytes()
    )
    (destination / "degradation_source_cells.csv").write_bytes(
        (study_output / "source_cells.csv").read_bytes()
    )
    names = (
        "degradation_stresses.csv",
        "degradation_reference.csv",
        "degradation_parameters.json",
        "degradation_source_cells.csv",
    )
    manifest = {
        "format_version": 1,
        "created_at": original["created_at"],
        "description": "Real ERA5-derived annual stresses, 2016-2018; explicit mono-Si scenario",
        "scope": original["scope"],
        "study": {k: v for k, v in original["study"].items() if k != "parameters_path"},
        "stress_metadata": dict(annual.attrs),
        "result_metadata": {
            key: value.item() if isinstance(value, np.generic) else value
            for key, value in rates.attrs.items()
        },
        "variable_units": {name: STRESS_UNITS.get(name, "hours") for name in annual.data_vars},
        "land_cells": original["land_cells"],
        "valid_cells": original["valid_cells"],
        "masked_incomplete_cells": original["masked_incomplete_cells"],
        "hours_retrieved": original["hours_retrieved"],
        "source_software": original["software"],
        "references": original["references"],
        "original_manifest_sha256": sha256_file(study_output / "manifest.json"),
        "retrieval_manifest_sha256": original["retrieval_manifest_sha256"],
        "original_output_sha256": {
            name: original["outputs_sha256"][name]
            for name in (
                "annual_stresses.nc",
                "degradation.nc",
                "parameters.json",
                "source_cells.csv",
            )
        },
        "files": {name: sha256_file(destination / name) for name in names},
        "boundaries_sha256": sha256_file(boundaries),
        "attribution": {
            "weather": "Copernicus ERA5 via Open-Meteo, CC BY 4.0; modelled, not measured",
            "land_support": "CRU TS v4.10, Climatic Research Unit, UEA; ODbL-1.0 / DbCL",
            "outlines": "Natural Earth public-domain country outlines; visual context only",
        },
    }
    path = destination / "degradation_provenance.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    return path


def load_degradation_example(directory: Path) -> tuple[xr.Dataset, xr.Dataset, dict[str, Any]]:
    """Verify small fixtures, recompute rates and check against the archived run.

    Returns annual inputs, recalculated rates, and source/calibration metadata.
    Rates are %/year under the named scenario; missing grid cells remain missing.
    """
    metadata = json.loads((directory / "degradation_provenance.json").read_text())
    if metadata.get("format_version") != 1:
        raise ValueError("Unsupported degradation fixture format")
    for name, expected in metadata["files"].items():
        if Path(name).name != name or sha256_file(directory / name) != expected:
            raise ValueError(f"Degradation fixture checksum mismatch: {name}")
    if sha256_file(directory / "climate_world_boundaries.geojson") != metadata["boundaries_sha256"]:
        raise ValueError("Degradation boundary checksum mismatch")
    table = pd.read_csv(directory / "degradation_stresses.csv")
    if table.duplicated(["year", "lat", "lon"]).any():
        raise ValueError("Duplicate annual stress coordinates")
    annual = table.set_index(["year", "lat", "lon"]).to_xarray()
    annual.attrs = metadata["stress_metadata"]
    for name, units in STRESS_UNITS.items():
        annual[name].attrs["units"] = units
    parameters = DegradationParameters(
        **json.loads((directory / "degradation_parameters.json").read_text())
    )
    result = map_degradation(annual, parameters, aggregation="mean_stress")
    reference = (
        pd.read_csv(directory / "degradation_reference.csv").set_index(["lat", "lon"]).to_xarray()
    )
    result, reference = xr.align(result, reference, join="exact")
    for name in (*RATE_VARIABLES, "valid_year_count", "rate_class"):
        if not np.allclose(result[name], reference[name], rtol=1e-10, atol=1e-12, equal_nan=True):
            raise ValueError(f"Recalculation differs from archived study: {name}")
    result["land_mask"] = reference.land_mask
    result.attrs.update(metadata["result_metadata"])
    return annual, result, metadata


def plot_degradation_maps(
    rates: xr.Dataset, boundaries: Path, *, categorical: bool = False
) -> plt.Figure:
    """Plot mechanism rates or the classified total on the supplied regular grid.

    Colored rectangles are sample-centred footprints, not land polygons or an
    interpolation to the coast. Gray footprints mark incomplete land samples.
    """
    fig, axes = (
        plt.subplots(1, 1, figsize=(13, 6), layout="constrained")
        if categorical
        else (plt.subplots(2, 2, figsize=(15, 9), layout="constrained"))
    )
    document = json.loads(boundaries.read_text())
    step = float(rates.attrs["grid_step_degrees"])
    x = np.r_[rates.lon.values - step / 2, float(rates.lon[-1]) + step / 2]
    y = np.r_[rates.lat.values - step / 2, float(rates.lat[-1]) + step / 2]
    selected = (
        [("rate_class", "Combined rate categories")]
        if categorical
        else list(zip(RATE_VARIABLES, TITLES, strict=True))
    )
    for ax, (name, title) in zip(np.asarray(axes).ravel(), selected, strict=True):
        ax.set_facecolor("#eef3f7")
        missing = (rates.land_mask == 1) & rates.total_rate.isnull()
        ax.pcolormesh(
            x,
            y,
            np.ma.masked_where(~missing.values, np.ones(missing.shape)),
            cmap=ListedColormap(["#747d86"]),
            shading="flat",
        )
        if categorical:
            colors = plt.get_cmap("YlOrRd")(np.linspace(0.15, 0.95, 8))
            cmap = ListedColormap(colors)
            mesh = ax.pcolormesh(
                x,
                y,
                rates[name].where(rates[name] > 0),
                cmap=cmap,
                norm=BoundaryNorm(np.arange(0.5, 9.5), 8),
                shading="flat",
            )
            bar = fig.colorbar(mesh, ax=ax, orientation="horizontal", pad=0.09, ticks=range(1, 9))
            labels = json.loads(rates.rate_class.attrs["class_labels"])
            bar.ax.set_xticklabels([labels[str(i)] for i in range(1, 9)])
        else:
            mesh = ax.pcolormesh(
                x,
                y,
                rates[name],
                cmap="YlOrRd",
                vmin=0,
                vmax=max(float(rates[name].max()), 1e-12),
                shading="flat",
            )
            bar = fig.colorbar(mesh, ax=ax, orientation="horizontal", pad=0.09, shrink=0.9)
        bar.set_label("Scenario degradation rate (%/year)")
        for feature in document["features"]:
            for part in polygons(shape(feature["geometry"])):
                xy = np.asarray(part.exterior.coords)
                ax.plot(xy[:, 0], xy[:, 1], color="#526575", linewidth=0.4)
        ax.set(
            xlim=(-180, 180),
            ylim=(max(-90, y[0]), min(90, y[-1])),
            xlabel="Longitude (°)",
            ylabel="Latitude (°)",
            title=title,
        )
        ax.grid(alpha=0.15)
    valid = int(rates.total_rate.notnull().sum())
    land = int(rates.land_mask.sum())
    fig.suptitle(
        f"Climate degradation scenario | {rates.attrs['baseline_start_year']}-"
        f"{rates.attrs['baseline_end_year']}\n"
        f"{step:g}° sampling · {valid}/{land} complete land centres · gray = missing · "
        + ("0.2%/year classes" if categorical else "each mechanism has its own color scale"),
        fontsize=14,
    )
    return fig
