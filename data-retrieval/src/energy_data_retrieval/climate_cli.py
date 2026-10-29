"""GPCC/CRU TS retrieval commands; reusable climate algorithms live in methods."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from energy_data_retrieval.sources.cru_ts import (
    CRU_TS_HOSTS,
    VARIABLES,
    CRUTSClient,
    CRUTSRequest,
)
from energy_data_retrieval.sources.cru_ts import iter_monthly as cru_monthly
from energy_data_retrieval.sources.gpcc import GPCC_HOSTS, GPCCClient, GPCCRequest
from energy_data_retrieval.sources.gpcc import iter_monthly as gpcc_monthly
from energy_data_retrieval.storage import sha256_file
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, atomic_bytes

CLIMATE_COMMANDS = {"gpcc", "cru-ts"}


def add_climate_parsers(commands: argparse._SubParsersAction) -> None:
    for name in sorted(CLIMATE_COMMANDS):
        parser = commands.add_parser(name, help=f"Retrieve and process {name} monthly grids")
        parser.add_argument("--start-year", type=int, required=True)
        parser.add_argument("--end-year", type=int, required=True)
        parser.add_argument("--output", type=Path)
        parser.add_argument(
            "--bbox", type=float, nargs=4, metavar=("WEST", "SOUTH", "EAST", "NORTH")
        )
        parser.add_argument(
            "--plan-only", action="store_true", help="Print archive URLs without downloads"
        )
        parser.add_argument("--download-only", action="store_true")
        parser.add_argument("--maximum-download-mib", type=int, default=256)
        if name == "gpcc":
            parser.add_argument("--resolution", type=float, default=0.5)
            parser.add_argument("--end-month", type=int, default=12)
            parser.add_argument("--use-infilled", action="store_true")
        else:
            parser.add_argument("--variable", choices=sorted(VARIABLES), default="tmp")


def run_climate_command(args: argparse.Namespace) -> dict[str, object]:
    request = (
        GPCCRequest(args.start_year, args.end_year, args.resolution, args.end_month)
        if args.command == "gpcc"
        else CRUTSRequest(args.variable, args.start_year, args.end_year)
    )
    urls = request.urls()
    if args.plan_only:
        return {"source": args.command, "request": asdict(request), "urls": urls}
    if args.output is None:
        raise ValueError("--output is required unless --plan-only")
    output = Path(args.output)
    bbox = tuple(args.bbox) if args.bbox else None
    config = HTTPConfig(maximum_response_bytes=args.maximum_download_mib * 1024**2)
    raw = output / "raw"
    hosts = GPCC_HOSTS if isinstance(request, GPCCRequest) else CRU_TS_HOSTS
    with HTTPClient(hosts, config=config) as http:
        records = (
            GPCCClient(http).download(request, raw)
            if isinstance(request, GPCCRequest)
            else CRUTSClient(http).download(request, raw)
        )
    paths = [raw / url.rsplit("/", 1)[1] for url in urls]
    processed = []
    if not args.download_only:
        arrays = (
            gpcc_monthly(
                paths,
                start_year=args.start_year,
                end_year=args.end_year,
                bbox=bbox,
                use_infilled=args.use_infilled,
            )
            if isinstance(request, GPCCRequest)
            else cru_monthly(
                paths,
                variable=args.variable,
                start_year=args.start_year,
                end_year=args.end_year,
                bbox=bbox,
            )
        )
        directory = output / "processed"
        directory.mkdir(parents=True, exist_ok=True)
        for path, array in zip(paths, arrays, strict=True):
            if isinstance(request, GPCCRequest):
                array = array.where(
                    (array.time.dt.year < args.end_year) | (array.time.dt.month <= args.end_month),
                    drop=True,
                )
            target = directory / path.name.removesuffix(".gz")
            array.to_netcdf(target, engine="scipy")
            processed.append(
                {
                    "path": str(target),
                    "sha256": sha256_file(target),
                    "variable": str(array.name),
                    "units": array.attrs["units"],
                }
            )
    result = {
        "source": args.command,
        "request": asdict(request),
        "bbox": bbox,
        "downloads": [asdict(record) for record in records],
        "processed": processed,
        "infilled": bool(getattr(args, "use_infilled", False)),
        "data_license": (
            "DWD terms of use; cite resolution-specific GPCC DOI"
            if isinstance(request, GPCCRequest)
            else "ODbL-1.0; Database Contents License"
        ),
        "citation": (
            request.doi
            if isinstance(request, GPCCRequest)
            else "Harris et al. 2020, 10.1038/s41597-020-0453-3; CRU TS v4.10"
        ),
    }
    atomic_bytes(output / "manifest.json", json.dumps(result, indent=2, allow_nan=False).encode())
    return result
