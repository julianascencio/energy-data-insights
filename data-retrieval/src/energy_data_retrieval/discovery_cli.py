"""Command-line entry point for station and grid discovery by coordinates."""

from __future__ import annotations

import argparse
import json
from contextlib import nullcontext
from datetime import date
from pathlib import Path

from energy_data_retrieval.discovery import (
    DISCOVERY_HOSTS,
    STATION_SOURCES,
    find_sources,
    save_discovery,
)
from energy_data_retrieval.sources.cmip6 import load_plan
from energy_data_retrieval.transport import HTTPClient, HTTPConfig


def _day(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError("Use a date in YYYY-MM-DD form") from None


def add_discovery_parser(commands: argparse._SubParsersAction) -> None:
    parser = commands.add_parser(
        "discover", help="Find nearby stations and gridded datasets from latitude/longitude"
    )
    parser.add_argument("--latitude", type=float, required=True)
    parser.add_argument("--longitude", type=float, required=True)
    parser.add_argument("--radius-km", type=float, default=100.0)
    parser.add_argument("--limit", type=int, default=20, help="Maximum stations across all sources")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument(
        "--station-source",
        choices=STATION_SOURCES,
        action="append",
        help="Repeat to select sources",
    )
    selection.add_argument("--grid-only", action="store_true", help="Skip station catalogues")
    parser.add_argument(
        "--catalogue",
        action="append",
        default=[],
        metavar="SOURCE=PATH",
        help="Reuse a verified station Parquet snapshot with its original coverage scope",
    )
    parser.add_argument("--offline", action="store_true", help="Use only supplied local catalogues")
    parser.add_argument(
        "--probe-date",
        type=_day,
        help="Verify one UTC day from the two Open-Meteo products; requires network access",
    )
    parser.add_argument(
        "--cmip6-plan", type=Path, help="Add exact datasets from a saved CMIP6 plan"
    )
    parser.add_argument("--output", type=Path, help="New JSON snapshot; default prints full JSON")
    parser.add_argument("--cache-directory", type=Path, help="Public HTTP response cache")
    parser.add_argument("--request-interval", type=float, default=1.6)
    parser.add_argument("--maximum-response-bytes", type=int, default=64 * 1024**2)


def run_discovery_command(args: argparse.Namespace) -> None:
    paths: dict[str, Path] = {}
    for entry in args.catalogue:
        source, separator, raw_path = entry.partition("=")
        if not separator or source not in STATION_SOURCES or not raw_path or source in paths:
            raise ValueError("Each --catalogue requires a distinct supported SOURCE=PATH")
        paths[source] = Path(raw_path)
    if args.offline and args.probe_date is not None:
        raise ValueError("--probe-date cannot be used with --offline")
    if args.output is not None and (args.output.exists() or args.output.is_symlink()):
        raise ValueError("Discovery snapshot already exists; choose a new output path")
    plan = load_plan(args.cmip6_plan) if args.cmip6_plan is not None else None
    selected = () if args.grid_only else tuple(args.station_source or STATION_SOURCES)
    network = not args.offline and (
        any(source not in paths for source in selected) or args.probe_date is not None
    )
    context = (
        HTTPClient(
            DISCOVERY_HOSTS,
            config=HTTPConfig(
                minimum_interval_seconds=args.request_interval,
                maximum_response_bytes=args.maximum_response_bytes,
            ),
            cache_directory=args.cache_directory,
        )
        if network
        else nullcontext(None)
    )
    with context as http:
        result = find_sources(
            args.latitude,
            args.longitude,
            radius_km=args.radius_km,
            limit=args.limit,
            station_sources=selected,
            catalogues=paths,
            http=http,
            probe_date=args.probe_date,
            cmip6_plan=plan,
        )
    if args.output is None:
        print(json.dumps(result.as_dict(), indent=2, allow_nan=False))
    else:
        save_discovery(result, args.output)
        print(
            json.dumps(
                {
                    "output_path": str(args.output),
                    "status": result.status,
                    "stations": len(result.stations),
                    "grid_datasets": len(result.grids),
                    "source_status": {
                        item["source"]: item["status"] for item in result.source_status
                    },
                },
                sort_keys=True,
            )
        )
