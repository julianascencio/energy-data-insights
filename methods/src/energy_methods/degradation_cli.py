"""Map the thesis's climate degradation mechanisms from annual stress grids."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Sequence
from pathlib import Path

import xarray as xr

from energy_methods.degradation import REFERENCE_IDS, DegradationParameters
from energy_methods.degradation_mapping import (
    RATE_VARIABLES,
    kgpv_degradation_summary,
    map_degradation,
)
from energy_methods.mapping import class_area_summary, write_geojson
from energy_methods.references import get_references


def _digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stresses", nargs="+", type=Path, required=True, help="Annual NetCDF grids"
    )
    parser.add_argument("--parameters", type=Path, required=True, help="Module calibration JSON")
    parser.add_argument("--aggregation", choices=("mean_stress", "mean_rate"), required=True)
    parser.add_argument(
        "--region", choices=("global", "europe"), default="global", help="Bin scheme"
    )
    parser.add_argument(
        "--kgpv", type=Path, help="Exactly aligned kgpv.nc for area-weighted summaries"
    )
    parser.add_argument(
        "--geojson", action="store_true", help="Export each layer; max 100,000 cells"
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        record = json.loads(args.parameters.read_text(encoding="utf-8"))
        if not isinstance(record, dict):
            raise ValueError("Parameters must be a JSON object")
        parameters = DegradationParameters(**record)
        batches = []
        for path in args.stresses:
            with xr.open_dataset(path) as data:
                batches.append(data.load())
        conventions = {str(data.attrs.get("stress_convention", "")) for data in batches}
        if len(conventions) != 1:
            raise ValueError("Annual files must use the same stress_convention")
        annual = xr.concat(batches, dim="year", join="exact", combine_attrs="drop_conflicts")
        annual = annual.sortby("year")
        annual.attrs["source"] = json.dumps([str(path) for path in args.stresses])
        result = map_degradation(
            annual, parameters, aggregation=args.aggregation, region=args.region
        )
        summary = None
        if args.kgpv:
            with xr.open_dataset(args.kgpv) as data:
                kgpv = data.kgpv_class.load()
                kgpv.attrs = {**data.attrs, **kgpv.attrs}
                summary = kgpv_degradation_summary(result, kgpv)
        labels = {
            int(key): value
            for key, value in json.loads(result.rate_class.attrs["class_labels"]).items()
        }
        areas = class_area_summary(result.rate_class)
        args.output.mkdir(parents=True, exist_ok=True)
        result.to_netcdf(args.output / "degradation.nc", engine="scipy")
        if summary is not None:
            summary.to_netcdf(args.output / "degradation_by_kgpv.nc", engine="scipy")
        if args.geojson:
            for name in RATE_VARIABLES:
                write_geojson(result[name], args.output / f"{name}.geojson")
            write_geojson(
                result.rate_class, args.output / "rate_class.geojson", nodata=0, labels=labels
            )
        inputs = [*args.stresses, args.parameters, *([args.kgpv] if args.kgpv else [])]
        reference_ids = [*REFERENCE_IDS, *(["ascencio_vasquez_2019_kgpv"] if args.kgpv else [])]
        manifest = {
            "method": dict(result.attrs),
            "parameters": parameters.to_dict(),
            "region": args.region,
            "inputs": [{"path": str(path), "sha256": _digest(path)} for path in inputs],
            "class_area_km2": {labels[key]: value for key, value in areas.items()},
            "references": [reference.as_dict() for reference in get_references(reference_ids)],
        }
        (args.output / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8"
        )
    except (ValueError, TypeError, OSError, KeyError) as error:
        parser.exit(2, f"Degradation mapping failed: {error}\n")
    print(args.output / "degradation.nc")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
