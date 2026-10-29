"""Retrieve with energy_data_retrieval, model with energy_methods, retain run evidence."""

from __future__ import annotations

import json
import platform
from dataclasses import asdict
from datetime import UTC, date, datetime
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal, cast

import numpy as np
import pandas as pd
import xarray as xr

from energy_analysis.degradation.config import StudyConfig
from energy_data_retrieval.sources.cru_ts.client import CRUTSClient, CRUTSRequest, iter_monthly
from energy_data_retrieval.sources.open_meteo import OpenMeteoClient, Site
from energy_data_retrieval.storage import (
    bounded_map,
    existing_artifact,
    fingerprint,
    sha256_file,
    write_parquet,
)
from energy_data_retrieval.transport import HTTPClient, JSONValue, atomic_bytes
from energy_methods.degradation_mapping import (
    RATE_VARIABLES,
    STRESS_UNITS,
    annual_stresses,
    map_degradation,
)
from energy_methods.degradation_weather import faiman_from_ghi, wald_uv_irradiance
from energy_methods.mapping import cell_areas_km2, class_area_summary, write_geojson
from energy_methods.references import get_references

REFERENCE_IDS = (
    "ascencio_vasquez_2021_thesis",
    "ascencio_vasquez_2019_degradation_mapping",
    "kaaya_2019_degradation",
    "kaaya_2020_thesis",
    "faiman_2008_temperature",
    "wald_2018_spectral",
    "huld_amillo_2015_performance",
    "hersbach_2020_era5",
    "era5_single_levels",
    "open_meteo_historical_weather",
    "open_meteo_variable_definitions",
    "harris_2020_cru_ts",
    "cru_ts_410",
)


def _json(path: Path, value: object) -> None:
    atomic_bytes(path, json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False).encode())


def _request(site: Site, year: int) -> dict[str, JSONValue]:
    return {
        "schema": "degradation-weather-v1",
        "site_id": site.site_id,
        "latitude": site.latitude,
        "longitude": site.longitude,
        "year": year,
        "source": "Open-Meteo",
        "model": "era5",
        "include_degradation": True,
    }


def _partition(directory: Path, site: Site, year: int) -> Path:
    return directory / "open-meteo" / site.site_id / f"{year}.parquet"


def select_land_grid(mask: xr.DataArray, config: StudyConfig) -> xr.DataArray:
    """Nearest CRU cell support at requested centres, not fractional coastal land area."""
    result = mask.sel(
        lat=xr.DataArray(config.latitudes, dims="lat"),
        lon=xr.DataArray(config.longitudes, dims="lon"),
        method="nearest",
    ).assign_coords(lat=config.latitudes, lon=config.longitudes)
    result.name = "land_mask"
    result.attrs = {
        "source": "CRU TS v4.10 first selected monthly TMP validity",
        "meaning": "nearest source cell has data; coarse footprints are not land polygons",
    }
    return result.astype("int8")


def _sites(land: xr.DataArray) -> list[Site]:
    return [
        Site(f"cell_{row:03}_{col:03}", float(land.lat[row]), float(land.lon[col]))
        for row, col in zip(*np.nonzero(land.values), strict=True)
    ]


def retrieve(config: StudyConfig, directory: Path, http: HTTPClient, *, workers: int = 2) -> Path:
    """Acquire/checksum raw inputs, restart from valid Parquet partitions; no model calls."""
    directory.mkdir(parents=True, exist_ok=True)
    request = CRUTSRequest("tmp", config.start_year, config.start_year)
    cru_dir = directory / "cru-ts"
    records = CRUTSClient(http).download(request, cru_dir)
    paths = [cru_dir / url.rsplit("/", 1)[1] for url in request.urls()]
    months = next(
        iter_monthly(
            paths, variable="tmp", start_year=config.start_year, end_year=config.start_year
        )
    )
    mask = months.isel(time=0, drop=True).notnull().rename("land_mask").astype("int8")
    mask.attrs = {
        "source": "CRU TS v4.10",
        "mask_month": str(months.time.values[0]),
        "license": "ODbL-1.0; Database Contents License",
        "attribution": "Climatic Research Unit, University of East Anglia",
    }
    mask.to_netcdf(directory / "land_mask_native.nc", engine="scipy")
    land = select_land_grid(mask, config)
    land.to_netcdf(directory / "land_mask.nc", engine="scipy")
    sites = _sites(land)
    if not sites:
        raise ValueError("No land cells in this study grid")
    client = OpenMeteoClient(http, chunk_days=366, include_degradation=True)
    total = len(sites) * (config.end_year - config.start_year + 1)

    def fetch(job: tuple[Site, int]) -> dict[str, object]:
        site, year = job
        path = _partition(directory, site, year)
        identity = _request(site, year)
        artifact = existing_artifact(path, fingerprint(identity))
        if artifact is None:
            chunk = client.weather(site, date(year, 1, 1), date(year, 12, 31))
            provenance = cast(
                dict[str, JSONValue],
                {
                    "request_record": asdict(chunk.request),
                    "weather_metadata": dict(chunk.frame.attrs),
                    "cell_latitude": chunk.cell_latitude,
                    "cell_longitude": chunk.cell_longitude,
                },
            )
            artifact = write_parquet(chunk.frame, path, request=identity, provenance=provenance)
        return {
            "path": str(path.relative_to(directory)),
            "sha256": artifact.sha256,
            "rows": artifact.rows,
        }

    jobs = (
        (site, year) for site in sites for year in range(config.start_year, config.end_year + 1)
    )
    completed = []
    print(f"Retrieving {len(sites)} land centres, {total} cell-years", flush=True)
    for item in bounded_map(fetch, jobs, workers=workers):
        completed.append(item)
        print(f"Retrieved {len(completed)}/{total}: {item['path']}", flush=True)
    manifest = {
        "source": "Open-Meteo explicit ERA5, nearest cells, no elevation downscaling",
        "cru_requests": [asdict(record) for record in records],
        "land_mask_sha256": sha256_file(directory / "land_mask.nc"),
        "native_mask_sha256": sha256_file(directory / "land_mask_native.nc"),
        "partitions": sorted(completed, key=lambda row: str(row["path"])),
    }
    _json(directory / "retrieval_manifest.json", manifest)
    return directory / "retrieval_manifest.json"


def _cell_stresses(frame: pd.DataFrame, site: Site, year: int, config: StudyConfig) -> xr.Dataset:
    """Translate normalized retrieval columns to the existing methods' hourly schema."""
    if not frame.site_id.eq(site.site_id).all() or not frame.duration_hours.eq(1).all():
        raise ValueError("Retrieved site ID or one-hour interval duration mismatch")
    time = pd.DatetimeIndex(frame.timestamp)
    if time.tz is None or str(time.tz) != "UTC":
        raise ValueError("Retrieved timestamps must be timezone-aware UTC")
    temperature = faiman_from_ghi(
        frame.temperature_c,
        frame.ghi_wm2,
        frame.wind_speed_ms,
        u0=config.u0,
        u1=config.u1,
        module_height_m=config.module_height_m,
    )
    # Preserve raw provider values; invalid TOA is unavailable, never clipped to zero.
    uv = wald_uv_irradiance(frame.ghi_wm2, frame.toa_wm2.where(frame.toa_wm2 >= 0))
    weather = xr.Dataset(
        coords={
            "time": time.tz_localize(None).to_numpy(dtype="datetime64[ns]"),
            "lat": [site.latitude],
            "lon": [site.longitude],
        },
        attrs={"time_zone": "UTC", "source": "Open-Meteo ERA5; GHI-Faiman and Wald UV"},
    )
    for name, values, units in (
        ("module_temperature_c", temperature, "degC"),
        ("relative_humidity_percent", frame.relative_humidity_percent.to_numpy(), "%"),
        ("uv_irradiance_w_m2", uv, "W m-2"),
    ):
        weather[name] = xr.DataArray(
            values[:, None, None], dims=("time", "lat", "lon"), attrs={"units": units}
        )
    days = (date(year + 1, 1, 1) - date(year, 1, 1)).days
    result = annual_stresses(weather, year=year, cycles_per_year=days * config.cycles_per_day)
    result["negative_toa_hours"] = (
        ("year", "lat", "lon"),
        np.array([[[int((frame.toa_wm2 < 0).sum())]]], dtype="int32"),
    )
    result["positive_ghi_zero_toa_hours"] = (
        ("year", "lat", "lon"),
        np.array(
            [
                [
                    [
                        np.count_nonzero(
                            (frame.ghi_wm2.to_numpy() > 0) & (frame.toa_wm2.to_numpy() == 0)
                        )
                    ]
                ]
            ],
            dtype="int32",
        ),
    )
    return result


def _run(config: StudyConfig, directory: Path, output: Path, *, reports: bool) -> None:
    """Write a complete run into a private staging directory."""
    parameters = config.parameters()
    retrieval_path = directory / "retrieval_manifest.json"
    retrieval = json.loads(retrieval_path.read_text())
    for name, key in (
        ("land_mask.nc", "land_mask_sha256"),
        ("land_mask_native.nc", "native_mask_sha256"),
    ):
        if sha256_file(directory / name) != retrieval[key]:
            raise ValueError("Land mask checksum mismatch")
    with xr.open_dataset(directory / "land_mask.nc") as ds:
        land = ds.land_mask.load()
    if not np.array_equal(land.lat, config.latitudes) or not np.array_equal(
        land.lon, config.longitudes
    ):
        raise ValueError("Saved retrieval grid differs from study configuration")
    coordinates = {
        "year": np.arange(config.start_year, config.end_year + 1),
        "lat": land.lat,
        "lon": land.lon,
    }
    shape = (len(coordinates["year"]), len(land.lat), len(land.lon))
    annual = xr.Dataset(
        {
            name: (("year", "lat", "lon"), np.full(shape, np.nan), {"units": units})
            for name, units in STRESS_UNITS.items()
        },
        coords=coordinates,
    )
    annual["valid_hour_count"] = (("year", "lat", "lon"), np.zeros(shape, dtype="int32"))
    annual["positive_ghi_zero_toa_hours"] = xr.zeros_like(annual.valid_hour_count)
    annual["negative_toa_hours"] = xr.zeros_like(annual.valid_hour_count)
    expected_partitions = {row["path"]: row for row in retrieval["partitions"]}
    if len(expected_partitions) != len(retrieval["partitions"]):
        raise ValueError("Duplicate partition in retrieval manifest")
    inputs = []
    cells = []
    for site in _sites(land):
        selected_cells = set()
        for year in range(config.start_year, config.end_year + 1):
            path = _partition(directory, site, year)
            artifact = existing_artifact(path, fingerprint(_request(site, year)))
            if artifact is None:
                raise ValueError(f"Missing retrieved weather: {path}")
            relative = str(path.relative_to(directory))
            if expected_partitions.pop(relative, None) != {
                "path": relative,
                "sha256": artifact.sha256,
                "rows": artifact.rows,
            }:
                raise ValueError("Partition differs from retrieval manifest")
            frame = pd.read_parquet(path)
            stresses = _cell_stresses(frame, site, year, config)
            for name in (
                *STRESS_UNITS,
                "valid_hour_count",
                "positive_ghi_zero_toa_hours",
                "negative_toa_hours",
            ):
                annual[name].loc[{"year": year, "lat": site.latitude, "lon": site.longitude}] = (
                    stresses[name].item()
                )
            annual.attrs.update(stresses.attrs)
            metadata_path = path.with_suffix(".parquet.json")
            metadata = json.loads(metadata_path.read_text())
            selected_cells.add(
                (metadata["provenance"]["cell_latitude"], metadata["provenance"]["cell_longitude"])
            )
            inputs.append(
                {
                    "path": str(path),
                    "sha256": artifact.sha256,
                    "rows": artifact.rows,
                    "metadata_sha256": sha256_file(metadata_path),
                }
            )
        if len(selected_cells) != 1:
            raise ValueError("Provider selected different native cells across years")
        actual_lat, actual_lon = selected_cells.pop()
        cells.append(
            {
                "site_id": site.site_id,
                "latitude": site.latitude,
                "longitude": site.longitude,
                "source_latitude": actual_lat,
                "source_longitude": actual_lon,
            }
        )
    if expected_partitions:
        raise ValueError("Retrieval manifest contains extra partitions outside this study")
    annual.attrs["source"] = (
        "Open-Meteo ERA5; normalized endpoint means; GHI-Faiman; Wald 280-400 nm UV"
    )
    annual.attrs["weather_processing"] = json.dumps(
        {
            "u0": config.u0,
            "u1": config.u1,
            "module_height_m": config.module_height_m,
            "cycles_per_day": config.cycles_per_day,
            "negative_toa_policy": "unavailable; raw values retained; no zero clipping",
        }
    )
    result = map_degradation(
        annual,
        parameters,
        aggregation=cast(Literal["mean_stress", "mean_rate"], config.aggregation),
    )
    result["land_mask"] = land
    result.attrs.update(
        study_name=config.name,
        grid_step_degrees=config.step_degrees,
        spatial_interpretation=(
            "nearest ERA5 sample at each CRU-supported centre; not area-averaged climate"
        ),
        reference_ids=" ".join(REFERENCE_IDS),
    )
    output.mkdir(parents=True, exist_ok=True)
    annual.to_netcdf(output / "annual_stresses.nc", engine="scipy")
    result.to_netcdf(output / "degradation.nc", engine="scipy")
    table = result.to_dataframe().reset_index()
    table.to_csv(output / "map_cells.csv", index=False)
    pd.DataFrame(cells).to_csv(output / "source_cells.csv", index=False)
    for name in RATE_VARIABLES:
        write_geojson(result[name], output / f"{name}.geojson")
    labels = {int(k): v for k, v in json.loads(result.rate_class.attrs["class_labels"]).items()}
    write_geojson(result.rate_class, output / "rate_class.geojson", nodata=0, labels=labels)
    areas = cell_areas_km2(result.total_rate)
    valid = result.total_rate.notnull()
    valid_area = float(areas.where(valid, 0).sum())
    statistics = {}
    for name in RATE_VARIABLES:
        layer = result[name]
        statistics[name] = {
            "minimum": float(layer.min()) if valid.any() else None,
            "maximum": float(layer.max()) if valid.any() else None,
            "footprint_area_weighted_mean": float((layer.fillna(0) * areas).sum()) / valid_area
            if valid_area
            else None,
        }
    manifest = {
        "created_at": datetime.now(UTC).isoformat(),
        "software": {
            "python": platform.python_version(),
            **{
                name: version(name)
                for name in (
                    "energy-analysis",
                    "energy-methods",
                    "energy-data-retrieval",
                    "numpy",
                    "pandas",
                    "xarray",
                    "matplotlib",
                    "scipy",
                    "pyarrow",
                )
            },
        },
        "study": {**asdict(config), "parameters_path": str(config.parameters_path)},
        "parameters": parameters.to_dict(),
        "parameters_sha256": sha256_file(config.parameters_path),
        "retrieval_manifest_sha256": sha256_file(retrieval_path),
        "inputs": inputs,
        "land_cells": int(land.sum()),
        "valid_cells": int(valid.sum()),
        "masked_incomplete_cells": int(((land == 1) & ~valid).sum()),
        "positive_ghi_zero_toa_hours": int(annual.positive_ghi_zero_toa_hours.sum()),
        "negative_toa_hours": int(annual.negative_toa_hours.sum()),
        "hours_retrieved": sum(int(item["rows"]) for item in inputs),
        "statistics": statistics,
        "class_footprint_area_km2": class_area_summary(result.rate_class),
        "scope": (
            "Published coefficients with explicit aggregation/cycling assumptions; "
            "screening scenario, not site-specific prediction or original thesis reproduction"
        ),
        "references": [reference.as_dict() for reference in get_references(REFERENCE_IDS)],
    }
    _json(output / "manifest.json", manifest)
    _json(output / "parameters.json", parameters.to_dict())
    if reports:
        from energy_analysis.degradation.reports import generate_report

        with xr.open_dataset(directory / "land_mask_native.nc") as ds:
            generate_report(result, ds.land_mask.load(), manifest, output / "reports")
    manifest["complete"] = True
    manifest["outputs_sha256"] = {
        str(path.relative_to(output)): sha256_file(path)
        for path in sorted(output.rglob("*"))
        if path.is_file() and path.name != "manifest.json"
    }
    _json(output / "manifest.json", manifest)


def run(config: StudyConfig, directory: Path, output: Path, *, reports: bool = True) -> Path:
    """Offline analysis of saved inputs; publish atomically and refuse output reuse."""
    directory, output = directory.resolve(), output.resolve()
    if output.exists():
        raise FileExistsError(f"Output already exists: {output}")
    if output.is_relative_to(directory) or directory.is_relative_to(output):
        raise ValueError("Data and output directories must be separate")
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".degradation-", dir=output.parent) as temporary:
        stage = Path(temporary) / "run"
        _run(config, directory, stage, reports=reports)
        stage.rename(output)
    return output / "degradation.nc"
