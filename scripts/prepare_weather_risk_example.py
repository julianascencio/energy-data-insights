"""Acquire real annual inputs for the offline worldwide soiling/snow gallery.

Run from the repository root. Reuse the reviewed KGPV land mask, sample each
land-cell centre, and retain public HTTP responses under ignored artifacts/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import asdict
from datetime import UTC, date, datetime
from pathlib import Path

import httpx
import numpy as np
import pandas as pd
import xarray as xr

from energy_data_retrieval.sources.nasa_power import NASAPowerClient
from energy_data_retrieval.sources.natural_earth import NATURAL_EARTH_HOSTS, NaturalEarthClient
from energy_data_retrieval.sources.open_meteo import Site
from energy_data_retrieval.sources.open_meteo.snow import OpenMeteoSnowClient
from energy_data_retrieval.storage import bounded_map
from energy_data_retrieval.transport import HTTPClient, HTTPConfig
from energy_methods.country_boundaries import load_country_boundaries, write_country_boundaries
from energy_methods.country_mapping import country_grid
from energy_methods.weather_risk_mapping import annual_risk_inputs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=2023)
    parser.add_argument("--region", choices=("world", "europe"), default="world")
    parser.add_argument(
        "--countries", nargs="+", help="Exact names, ISO codes or Natural Earth ADM0_A3 codes"
    )
    parser.add_argument(
        "--boundaries", type=Path, help="Local .shp or .geojson; otherwise acquire Natural Earth"
    )
    parser.add_argument("--boundary-scale", choices=("10m", "50m", "110m"), default="10m")
    parser.add_argument(
        "--resolution", type=float, help="Country grid spacing in degrees; default 0.5"
    )
    parser.add_argument("--bounds", type=float, nargs=4, metavar=("WEST", "SOUTH", "EAST", "NORTH"))
    parser.add_argument("--maximum-sites", type=int, default=500)
    parser.add_argument(
        "--plan-only",
        action="store_true",
        help="Resolve boundaries/counts without weather requests",
    )
    parser.add_argument(
        "--export-shp",
        action="store_true",
        help="Also export selected country shapefile companions",
    )
    parser.add_argument("--output", type=Path, default=Path("examples/analysis"))
    parser.add_argument("--cache", type=Path, default=Path("artifacts/weather-risk/http-cache"))
    parser.add_argument("--use-environment-proxy", action="store_true")
    args = parser.parse_args()
    if not 2001 <= args.year < datetime.now(UTC).year:
        raise ValueError("Choose a completed year from 2001 onward")
    if args.maximum_sites < 1:
        raise ValueError("maximum-sites must be positive")
    if not args.countries and any(
        (args.boundaries, args.resolution is not None, args.bounds, args.export_shp)
    ):
        raise ValueError("Boundary/resolution/bounds options require --countries")
    root = Path(__file__).resolve().parents[1]
    proxy = os.environ.get("HTTPS_PROXY") if args.use_environment_proxy else None
    selection = None
    if args.countries:
        if args.boundaries is None:
            with HTTPClient(
                allowed_hosts=NATURAL_EARTH_HOSTS,
                config=HTTPConfig(maximum_response_bytes=10_000_000),
                transport=httpx.HTTPTransport(proxy=proxy),
            ) as http:
                downloaded = NaturalEarthClient(http).download_countries(
                    args.cache.parent / "boundaries", scale=args.boundary_scale
                )
            boundary_path = downloaded.shapefile
            boundary_provenance = json.loads(downloaded.manifest.read_text())
        else:
            boundary_path = args.boundaries
            companions = [boundary_path]
            if boundary_path.suffix.lower() == ".shp":
                companions += [
                    boundary_path.with_suffix(suffix) for suffix in (".dbf", ".prj", ".shx", ".cpg")
                ]
            boundary_provenance = {
                "source": "caller-provided boundary file",
                "files_sha256": {
                    p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in companions
                    if p.exists()
                },
            }
        selection = load_country_boundaries(boundary_path, args.countries)
        spacing = args.resolution if args.resolution is not None else 0.5
        bounds = tuple(args.bounds) if args.bounds else None
        selected_grid = country_grid(selection, resolution=spacing, bounds=bounds)
        grid = (
            selected_grid.to_dataframe()
            .reset_index()
            .rename(columns={"country_mask": "in_country"})
        )
        grid["in_country"] = grid["in_country"].astype(int)
        mask_column, prefix = "in_country", "country_risk"
        mask_metadata = {
            "countries": list(selection.codes),
            "boundary_provenance": boundary_provenance,
            "requested_bounds": list(bounds) if bounds else None,
        }
        mask_description = (
            "Cells intersecting selected country polygons, including partial coastal cells."
        )
    else:
        mask_path = root / "examples/analysis/kgpv_worldwide_inputs.csv"
        mask_manifest = json.loads(
            (root / "examples/analysis/kgpv_worldwide_provenance.json").read_text()
        )
        if hashlib.sha256(mask_path.read_bytes()).hexdigest() != mask_manifest["fixture_sha256"]:
            raise ValueError("The reviewed land-mask fixture checksum has changed")
        grid = pd.read_csv(mask_path)[["lat", "lon", "is_land"]]
        if args.region == "world":
            grid = grid.loc[((grid.lat + 82.5) % 15 == 0) & ((grid.lon + 172.5) % 15 == 0)].copy()
            spacing = 15
        else:
            grid = grid.loc[grid.lat.between(37.5, 67.5) & grid.lon.between(-12.5, 32.5)].copy()
            spacing = 5
        mask_column, prefix = "is_land", "weather_risk"
        mask_metadata = {
            "land_mask_fixture_sha256": mask_manifest["fixture_sha256"],
            "land_mask_source": mask_manifest["sources"][-1],
        }
        mask_description = (
            "NOAA-derived nearest land mask from the reviewed KGPV fixture; coarse coastal cells."
        )
    sites = [
        Site(f"{lat:g}_{lon:g}", float(lat), float(lon))
        for lat, lon in grid.loc[grid[mask_column] == 1, ["lat", "lon"]].to_numpy(dtype=float)
    ]
    # CERES AOD has a 1-degree source grid. A finer country grid reuses those
    # samples explicitly instead of repeatedly querying the same source cell.
    aod_sites = {}
    for site in sites:
        lat = float(np.floor(site.latitude) + 0.5) if selection else site.latitude
        lon = float(np.floor(site.longitude) + 0.5) if selection else site.longitude
        aod_sites[site.site_id] = Site(f"{lat:g}_{lon:g}", lat, lon)
    unique_aod_sites = {site.site_id: site for site in aod_sites.values()}
    print(
        f"Plan: {len(sites)} snow sites; {len(unique_aod_sites)} unique AOD source samples; "
        f"{spacing}° grid"
    )
    if args.plan_only:
        return
    if len(sites) > args.maximum_sites:
        raise ValueError(
            "Plan exceeds --maximum-sites; reduce extent/resolution or explicitly raise the limit"
        )
    if selection:
        output_boundaries = write_country_boundaries(
            selection, args.output / f"{prefix}_boundaries.geojson"
        )
        mask_metadata["boundary_fixture_sha256"] = hashlib.sha256(
            output_boundaries.read_bytes()
        ).hexdigest()
        if args.export_shp:
            write_country_boundaries(selection, args.output / f"{prefix}_boundaries.shp")
    start, end = date(args.year, 1, 1), date(args.year, 12, 31)
    rows, records = [], []
    with HTTPClient(
        allowed_hosts=frozenset({"power.larc.nasa.gov", "archive-api.open-meteo.com"}),
        config=HTTPConfig(maximum_response_bytes=2_000_000, minimum_interval_seconds=0.5),
        cache_directory=args.cache,
        transport=httpx.HTTPTransport(proxy=proxy),
    ) as http:
        aod_client, snow_client = NASAPowerClient(http), OpenMeteoSnowClient(http)
        aod_chunks = {
            chunk.site.site_id: chunk
            for chunk in bounded_map(
                lambda site: aod_client.daily_aod(site, start, end),
                list(unique_aod_sites.values()),
                workers=2,
            )
        }

        def acquire(site: Site) -> tuple[dict[str, float | int], dict[str, object]]:
            aod = aod_chunks[aod_sites[site.site_id].site_id]
            snow = snow_client.hourly_depth(site, start, end)
            coords = {"lat": [site.latitude], "lon": [site.longitude]}
            daily = xr.DataArray(
                aod.frame.aod550.to_numpy()[:, None, None],
                dims=("time", "lat", "lon"),
                coords={**coords, "time": aod.frame.timestamp.dt.tz_localize(None).to_numpy()},
                attrs={
                    "units": "1",
                    "wavelength_nm": 550,
                    "time_zone": "UTC",
                    "source": aod.source,
                },
            )
            hourly = xr.DataArray(
                snow.frame.snow_depth_cm.to_numpy()[:, None, None],
                dims=("time", "lat", "lon"),
                coords={**coords, "time": snow.frame.timestamp.dt.tz_localize(None).to_numpy()},
                attrs={
                    "units": "cm",
                    "snow_depth_kind": "physical_ground",
                    "time_zone": "UTC",
                    "source": "Open-Meteo ERA5-Land physical ground snow depth",
                },
            )
            annual = annual_risk_inputs(daily, hourly, year=args.year)
            row = {"lat": site.latitude, "lon": site.longitude}
            row.update({str(name): float(annual[name].item()) for name in annual.data_vars})
            record = {
                "site_id": site.site_id,
                "requested_latitude": site.latitude,
                "requested_longitude": site.longitude,
                "snow_cell_latitude": snow.cell_latitude,
                "snow_cell_longitude": snow.cell_longitude,
                "aod_source": aod.source,
                "aod_sample_latitude": aod.site.latitude,
                "aod_sample_longitude": aod.site.longitude,
                "aod_request": asdict(aod.request),
                "snow_request": asdict(snow.request),
            }
            return row, record

        for row, record in bounded_map(acquire, sites, workers=2):
            rows.append(row)
            records.append(record)
            print(f"Prepared {len(rows)}/{len(sites)} selected cells", flush=True)
    frame = grid.merge(pd.DataFrame(rows), on=["lat", "lon"], how="left", validate="one_to_one")
    frame["year"] = args.year
    for name in ("valid_aod_days", "valid_snow_hours"):
        frame[name] = frame[name].fillna(0).astype(int)
    frame = frame.sort_values(["lat", "lon"])
    args.output.mkdir(parents=True, exist_ok=True)
    output = args.output / f"{prefix}_inputs.csv"
    frame.to_csv(output, index=False, float_format="%.8f", na_rep="", lineterminator="\n")
    manifest = {
        "description": "Real-data soiling/snow screening illustration; not the thesis rasters",
        "region": "countries" if selection else args.region,
        "year": args.year,
        "grid_degrees": spacing,
        **({"selected_cells": len(sites)} if selection else {"land_cells": len(sites)}),
        "units": {"aod550_mean": "1", "snow_depth_sum": "cm h"},
        "fixture_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        **mask_metadata,
        "preprocessing": [
            "NASA POWER unadjusted AOD_55, explicit UTC daily dates, annual mean; "
            "no daily-curve averaging.",
            "Open-Meteo explicit ERA5-Land physical snow depth in metres, "
            "converted to cm and summed hourly.",
            "Complete UTC year per indicator and cell; "
            "no gap filling or partial-year annualization.",
            "Nearest source samples at the requested grid centres; "
            "no area averaging or elevation downscaling.",
            mask_description,
            "Country grids reuse unique 1-degree NASA AOD samples; "
            "finer spacing adds no aerosol detail."
            if selection
            else "AOD queried at each selected grid centre.",
        ],
        "limitations": [
            "One year is a worked example, not a long-term climatological risk assessment.",
            "NASA POWER and ERA5-Land replace the thesis's ECMWF aerosol/ERA5 inputs explicitly.",
            "Source resolutions, aerosol biases and snow-depth overestimation affect results.",
            "No independent field validation, cleaning model, or structural snow-load estimate.",
        ],
        "reference_ids": [
            "ascencio_vasquez_2021_thesis",
            "cordero_2018_soiling",
            "ryberg_freeman_2017_snow",
            "nasa_power_aerosols",
            "open_meteo_historical_weather",
            "munoz_sabater_2021_era5_land",
            "natural_earth_countries" if selection else "noaa_psl_ncep_ncar_reanalysis_1",
        ],
        "requests": sorted(records, key=lambda record: str(record["site_id"])),
    }
    (args.output / f"{prefix}_provenance.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(frame)} cells to {output}")


if __name__ == "__main__":
    main()
