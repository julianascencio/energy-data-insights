"""Regenerate the small NOAA-derived, offline worldwide KGPV gallery fixture.

Run from the repository root. Raw NetCDF files stay under ignored artifacts/.
This is an example-specific preparation script, not a general NOAA provider.
"""

from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import os
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path

import httpx
import numpy as np
import pandas as pd
import xarray as xr

from energy_data_retrieval.transport import HTTPClient, HTTPConfig
from energy_methods.mapping import regrid

BASE = "https://downloads.psl.noaa.gov/Datasets/"
CLIMATOLOGY = "ncep.reanalysis.derived/surface_gauss/"
SOURCES = {
    "air": (
        CLIMATOLOGY + "air.2m.mon.ltm.1991-2020.nc",
        "c86a3c575010ca2c9414b24022361c43be6966dcdc62c821c1918e9c44ca9be9",
        964084,
    ),
    "prate": (
        CLIMATOLOGY + "prate.sfc.mon.ltm.1991-2020.nc",
        "35c390d9b82128925f960b8189992f3f617d131d8f4af4051dcd216d40825798",
        1155046,
    ),
    "dswrf": (
        CLIMATOLOGY + "dswrf.sfc.mon.ltm.1991-2020.nc",
        "5f9a176ba44d205541cb847d749fc7005cb594e8b4d35bf1aee67ac2e3c93be9",
        1041949,
    ),
    "land": (
        "ncep.reanalysis/surface_gauss/land.sfc.gauss.nc",
        "7da97a6d508a499302002891bb11e7c284d99019698cb89de1b5f5da37df3ca3",
        25213,
    ),
}
START, END = 1991, 2020
LATITUDE = np.arange(-87.5, 90, 5)
LONGITUDE = np.arange(-177.5, 180, 5)
MONTH_DAYS = xr.DataArray(
    [np.mean([calendar.monthrange(y, m)[1] for y in range(START, END + 1)]) for m in range(1, 13)],
    dims="month",
    coords={"month": np.arange(1, 13)},
)


def monthly_field(dataset: xr.Dataset, variable: str, units: str) -> xr.DataArray:
    """Validate January-December ordering, baseline, units and 30-year coverage."""
    if (
        dataset.sizes.get("time") != 12
        or dataset.time.attrs.get("climo_period") != "1991/01/01 - 2020/12/31"
        or dataset.time.attrs.get("units") != "hours since 1800-01-01 00:00:0.0"
        or dataset.time.attrs.get("interpreted_actual_range")
        != "0001/01/01 00:00:00 - 0001/12/01 00:00:00"
        or not np.array_equal(
            np.diff(dataset.time.values),
            24 * np.array([calendar.monthrange(1, m)[1] for m in range(1, 12)]),
        )
    ):
        raise ValueError("Expected January-December 1991-2020 monthly climatology")
    field = dataset[variable]
    if field.attrs.get("units") != units or field.dims != ("time", "lat", "lon"):
        raise ValueError(f"Unexpected units or dimensions for {variable}")
    if np.isinf(field).any():
        raise ValueError(f"Infinite values in {variable}")
    field = field.where(dataset.valid_yr_count == END - START + 1)
    return field.rename(time="month").assign_coords(month=np.arange(1, 13))


def convert_fields(
    air: xr.DataArray, rain_rate: xr.DataArray, solar_flux: xr.DataArray
) -> tuple[xr.DataArray, xr.DataArray, xr.DataArray]:
    """Convert rates using mean Gregorian month lengths over the fixed baseline.

    This is a climatological-month approximation, not the exact average of
    year-by-year totals: February rate/leap-year covariance is unavailable.
    Solar flux in [-0.1, 0) W/m² is clipped to zero; larger negatives fail.
    """
    air, rain_rate, solar_flux = xr.align(air, rain_rate, solar_flux, join="exact")
    if (rain_rate < 0).any() or (solar_flux < -0.1).any():
        raise ValueError("Negative rain or solar flux below the -0.1 W/m² tolerance")
    temperature = air.astype(float) - 273.15
    precipitation = rain_rate.astype(float) * MONTH_DAYS * 86400
    annual_ghi = (solar_flux.astype(float).clip(min=0) * MONTH_DAYS * 24 / 1000).sum(
        "month", skipna=False
    )
    return temperature, precipitation, annual_ghi


def prepare_inputs(raw_directory: Path) -> tuple[pd.DataFrame, int]:
    """Read pinned source bytes and bilinearly sample continuous inputs at 5°."""
    datasets = {}
    for key, (relative, expected, _) in SOURCES.items():
        path = raw_directory / Path(relative).name
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Source checksum mismatch: {path.name}")
        with xr.open_dataset(path, decode_times=False) as dataset:
            datasets[key] = dataset.load()
    air = monthly_field(datasets["air"], "air", "degK")
    rain = monthly_field(datasets["prate"], "prate", "Kg/m^2/s")
    solar = monthly_field(datasets["dswrf"], "dswrf", "W/m^2")
    negative_count = int((solar < 0).sum())
    continuous = convert_fields(air, rain, solar)
    temperature, precipitation, annual_ghi = [
        regrid(field, LATITUDE, LONGITUDE) for field in continuous
    ]
    native_land = datasets["land"].land.isel(time=0, drop=True)
    if not np.isin(native_land.values, [0, 1]).all():
        raise ValueError("Expected a binary NOAA land mask")
    land = regrid(native_land, LATITUDE, LONGITUDE, method="nearest", categorical=True) == 1
    valid = (
        land
        & temperature.notnull().all("month")
        & precipitation.notnull().all("month")
        & annual_ghi.notnull()
    )
    data = xr.Dataset({"is_land": land.astype("uint8"), "annual_ghi": annual_ghi.where(valid)})
    for month in range(1, 13):
        data[f"t{month:02d}"] = temperature.sel(month=month, drop=True).where(valid)
        data[f"p{month:02d}"] = precipitation.sel(month=month, drop=True).where(valid)
    return data.to_dataframe().reset_index().sort_values(["lat", "lon"]), negative_count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=Path("artifacts/kgpv-worldwide/raw"))
    parser.add_argument("--output", type=Path, default=Path("examples/analysis"))
    parser.add_argument(
        "--use-environment-proxy", action="store_true", help="Explicitly use HTTPS_PROXY, if set"
    )
    args = parser.parse_args()
    proxy = os.environ.get("HTTPS_PROXY") if args.use_environment_proxy else None
    records = []
    with HTTPClient(
        allowed_hosts=frozenset({"downloads.psl.noaa.gov"}),
        config=HTTPConfig(maximum_response_bytes=2_000_000),
        transport=httpx.HTTPTransport(proxy=proxy),
    ) as client:
        for relative, checksum, size in SOURCES.values():
            record = client.download_file(
                BASE + relative,
                args.cache / Path(relative).name,
                expected_sha256=checksum,
                expected_size_bytes=size,
            )
            records.append(asdict(record))
    frame, clipped = prepare_inputs(args.cache)
    args.output.mkdir(parents=True, exist_ok=True)
    csv_path = args.output / "kgpv_worldwide_inputs.csv"
    frame.to_csv(csv_path, index=False, float_format="%.6f", na_rep="", lineterminator="\n")
    manifest = {
        "description": (
            "Derived 5-degree illustration; not the published KGPV map or an official NOAA product"
        ),
        "source": "NOAA PSL NCEP/NCAR Reanalysis 1",
        "source_url": "https://psl.noaa.gov/data/gridded/data.ncep.reanalysis.html",
        "data_policy_url": "https://psl.noaa.gov/data/help/",
        "baseline_start_year": START,
        "baseline_end_year": END,
        "grid_degrees": 5,
        "units": {"t": "degC", "p": "mm", "annual_ghi": "kWh m-2"},
        "mean_month_days": MONTH_DAYS.values.tolist(),
        "preprocessing": [
            "Require valid_yr_count=30 for every source month; no missing-value filling.",
            (
                "Temperature: K minus 273.15. Precipitation: kg m-2 s-1 times "
                "mean month days times 86400."
            ),
            (
                "Solar: clip [-0.1,0) W m-2 to zero; reject below -0.1; sum flux "
                "times mean month days times 24/1000."
            ),
            (
                "Month lengths averaged over 1991-2020; February rate/leap-year "
                "covariance is unavailable."
            ),
            (
                "Bilinearly interpolate continuous fields before classification; "
                "nearest-neighbour binary land mask."
            ),
            "Mask oceans and incomplete climate cells; blank CSV values mean missing, never zero.",
            (
                "Sample at 5-degree cell centres; no conservative area "
                "aggregation or coastal land-fraction weighting."
            ),
            (
                "Round CSV values to six decimal places; retain source files and "
                "checksums to reproduce preparation."
            ),
        ],
        "negative_solar_source_values_clipped": clipped,
        "land_cells": int(frame.is_land.sum()),
        "valid_land_cells": int(frame.annual_ghi.notna().sum()),
        "fixture_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
        "sources": records,
        "software": {p: version(p) for p in ("numpy", "pandas", "xarray", "scipy")},
    }
    (args.output / "kgpv_worldwide_provenance.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(frame)} grid cells to {csv_path} ({csv_path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
