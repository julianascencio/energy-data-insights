"""Plan and download native CDS data without putting credentials in arguments."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import date
from pathlib import Path

from energy_data_retrieval.sources.cds import CDSClient, CDSRequest, era5_requests
from energy_data_retrieval.sources.cds.client import MAX_REQUEST_BYTES

CDS_COMMANDS = {"cds-retrieve", "cds-era5"}


def add_cds_parsers(commands: argparse._SubParsersAction) -> None:
    for name in sorted(CDS_COMMANDS):
        parser = commands.add_parser(name, help="Plan or retrieve native Copernicus CDS files")
        parser.add_argument("--output", type=Path)
        parser.add_argument(
            "--plan-only", action="store_true", help="No credentials or network used"
        )
        parser.add_argument("--maximum-download-mib", type=int, default=1024)
        parser.add_argument("--timeout-seconds", type=int, default=60)
        parser.add_argument("--attempts", type=int, default=3)
        if name == "cds-retrieve":
            parser.add_argument("--dataset", required=True, help="CDS catalogue dataset slug")
            parser.add_argument(
                "--request", type=Path, required=True, help="Selection-only JSON file"
            )
        else:
            parser.add_argument("--start", required=True, help="Inclusive YYYY-MM-DD")
            parser.add_argument("--end", required=True, help="Inclusive YYYY-MM-DD")
            parser.add_argument("--variables", nargs="+", required=True)
            parser.add_argument(
                "--area",
                nargs=4,
                type=float,
                required=True,
                metavar=("NORTH", "WEST", "SOUTH", "EAST"),
            )
            parser.add_argument("--monthly-means", action="store_true")
            parser.add_argument("--data-format", choices=("grib", "netcdf"), default="grib")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON request key")
        result[key] = value
    return result


def run_cds_command(args: argparse.Namespace) -> dict[str, object]:
    if args.command == "cds-retrieve":
        with args.request.open("rb") as stream:
            raw = stream.read(MAX_REQUEST_BYTES + 1)
        if len(raw) > MAX_REQUEST_BYTES:
            raise ValueError("CDS JSON request exceeds 1 MiB")
        selection = json.loads(raw, object_pairs_hook=_unique_object)
        requests = (CDSRequest(args.dataset, selection),)
    else:
        requests = era5_requests(
            date.fromisoformat(args.start),
            date.fromisoformat(args.end),
            variables=args.variables,
            area=tuple(args.area),
            monthly_means=args.monthly_means,
            data_format=args.data_format,
        )
    client = CDSClient(
        timeout_seconds=args.timeout_seconds,
        attempts=args.attempts,
        maximum_download_bytes=args.maximum_download_mib * 1024**2,
    )
    if args.plan_only:
        return {"source": "cds", "submitted": False, "requests": [r.as_dict() for r in requests]}
    if args.output is None:
        raise ValueError("--output is required unless --plan-only")
    records = []
    for request in requests:
        result = client.download(request, args.output)
        records.append(
            {**asdict(result), "path": str(result.path), "manifest_path": str(result.manifest_path)}
        )
    return {"source": "cds", "complete": True, "artifacts": records}
