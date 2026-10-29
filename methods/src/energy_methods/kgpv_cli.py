"""Build a KGPV map from processed monthly grids and an explicit annual GHI grid."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Iterator, Sequence
from pathlib import Path

import xarray as xr

from energy_methods.climatology import monthly_climatology
from energy_methods.kgpv import ZONE_CODES, map_kgpv
from energy_methods.mapping import class_area_summary, regrid, write_geojson


def _batches(paths: list[Path], variable: str) -> Iterator[xr.DataArray]:
    for path in paths:
        with xr.open_dataset(path) as ds:
            data = ds[variable].load()
            data.attrs["source_file"] = str(path)
            yield data


def _digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--temperature", type=Path, nargs="+", required=True)
    parser.add_argument("--precipitation", type=Path, nargs="+", required=True)
    parser.add_argument("--annual-ghi", type=Path, required=True)
    parser.add_argument("--ghi-variable", default="annual_ghi_kwh_m2")
    parser.add_argument("--start-year", type=int, required=True)
    parser.add_argument("--end-year", type=int, required=True)
    parser.add_argument("--minimum-valid-years", type=int)
    parser.add_argument(
        "--regrid", action="store_true", help="Bilinearly align continuous inputs to CRU grid"
    )
    parser.add_argument("--geojson", action="store_true", help="Also export at most 100,000 cells")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        temperature = monthly_climatology(
            _batches(args.temperature, "temperature_c"),
            start_year=args.start_year,
            end_year=args.end_year,
            minimum_valid_years=args.minimum_valid_years,
        )
        precipitation = monthly_climatology(
            _batches(args.precipitation, "precipitation_mm"),
            start_year=args.start_year,
            end_year=args.end_year,
            minimum_valid_years=args.minimum_valid_years,
        )
        with xr.open_dataset(args.annual_ghi) as ds:
            ghi = ds[args.ghi_variable].load()
        t = temperature.temperature_c
        p = precipitation.precipitation_mm
        if args.regrid:
            p = regrid(p, t.lat.values, t.lon.values)
            ghi = regrid(ghi, t.lat.values, t.lon.values)
        result = map_kgpv(t, p, ghi)
        args.output.mkdir(parents=True, exist_ok=True)
        temperature.to_netcdf(args.output / "temperature_climatology.nc", engine="scipy")
        precipitation.to_netcdf(args.output / "precipitation_climatology.nc", engine="scipy")
        result.to_netcdf(args.output / "kgpv.nc", engine="scipy")
        if args.geojson:
            write_geojson(
                result.kgpv_class,
                args.output / "kgpv.geojson",
                nodata=0,
                labels=dict(enumerate(ZONE_CODES)),
            )
        manifest = {
            "method": dict(result.attrs),
            "start_year": args.start_year,
            "end_year": args.end_year,
            "minimum_valid_years": args.minimum_valid_years,
            "regridding": "linear" if args.regrid else "exact alignment",
            "inputs": [
                {"path": str(path), "sha256": _digest(path)}
                for path in [*args.temperature, *args.precipitation, args.annual_ghi]
            ],
            "area_km2": {
                ZONE_CODES[k]: v for k, v in class_area_summary(result.kgpv_class).items()
            },
        }
        (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False))
    except (ValueError, OSError, KeyError) as error:
        parser.exit(2, f"KGPV mapping failed: {error}\n")
    print(args.output / "kgpv.nc")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
