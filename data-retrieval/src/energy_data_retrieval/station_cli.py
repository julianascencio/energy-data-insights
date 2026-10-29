"""Command-line acquisition for AEMET, DWD and SURFRAD station products."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path

from energy_data_retrieval.sources.aemet import AEMET_HOSTS, AEMETClient, daily_chunks
from energy_data_retrieval.sources.dwd import DWD_HOSTS, DWDClient
from energy_data_retrieval.sources.surfrad import STATION_IDS, SURFRAD_HOSTS, SURFRADClient
from energy_data_retrieval.storage import Artifact
from energy_data_retrieval.transport import HTTPClient, HTTPConfig

STATION_COMMANDS = frozenset(
    {
        "aemet-stations",
        "aemet-daily",
        "aemet-recent",
        "dwd-stations",
        "dwd-solar",
        "surfrad-stations",
        "surfrad-observations",
    }
)


def _date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError("Use a date in YYYY-MM-DD form") from None


def _aemet_station(value: str) -> str:
    if not re.fullmatch(r"[A-Z0-9]{3,6}", value):
        raise argparse.ArgumentTypeError("Use the exact uppercase AEMET catalogue station ID")
    return value


def _dwd_station(value: str) -> str:
    if not re.fullmatch(r"\d{5}", value, flags=re.ASCII):
        raise argparse.ArgumentTypeError("Use the five-digit DWD station ID, including zeros")
    return value


def _folder(station: str) -> str:
    """Preserve source identifier distinctions in a lowercase directory name."""
    return station.lower() + "_" + hashlib.sha256(station.encode()).hexdigest()[:10]


def _emit(artifact: Artifact) -> None:
    print(json.dumps(asdict(artifact), sort_keys=True), flush=True)


def add_station_parsers(commands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Attach explicit native station products to the shared retrieval CLI."""
    descriptions = {
        "aemet-stations": "Retrieve the AEMET daily-climate station inventory",
        "aemet-daily": "Retrieve historical AEMET daily station climate data",
        "aemet-recent": "Snapshot the latest AEMET station observations (rolling 12 hours)",
        "dwd-stations": "Retrieve the DWD hourly solar station catalogue",
        "dwd-solar": "Retrieve native DWD hourly solar station observations",
        "surfrad-stations": "Retrieve the NOAA SURFRAD station catalogue",
        "surfrad-observations": "Retrieve native daily NOAA SURFRAD radiation files",
    }
    for name, description in descriptions.items():
        command = commands.add_parser(name, help=description)
        command.add_argument("--output", type=Path, required=True)
        command.add_argument(
            "--request-interval", type=float, default=1.6 if name.startswith("aemet-") else 0.25
        )
        mib = 128 if name.startswith("dwd-") else 8 if name.startswith("surfrad-") else 64
        command.add_argument("--maximum-response-bytes", type=int, default=mib * 1024**2)
        if name in {"aemet-stations", "dwd-stations"}:
            command.add_argument(
                "--bbox", type=float, nargs=4, metavar=("WEST", "SOUTH", "EAST", "NORTH")
            )
        if name.startswith("aemet-"):
            command.add_argument("--maximum-rows", type=int, default=100_000)
        if name in {"aemet-daily", "aemet-recent"}:
            command.add_argument("--station", type=_aemet_station, required=True)
        if name == "dwd-stations":
            command.add_argument("--maximum-stations", type=int, default=10_000)
        if name == "dwd-solar":
            command.add_argument("--station", type=_dwd_station, required=True)
            command.add_argument("--maximum-rows", type=int, default=1_000_000)
            command.add_argument("--maximum-archive-members", type=int, default=128)
            command.add_argument("--maximum-uncompressed-bytes", type=int, default=512 * 1024**2)
        if name == "surfrad-observations":
            command.add_argument("--station", choices=STATION_IDS, required=True)
            command.add_argument("--maximum-rows", type=int, default=1440)
        if name in {"aemet-daily", "dwd-solar", "surfrad-observations"}:
            command.add_argument("--start", type=_date, required=True)
            command.add_argument("--end", type=_date, required=True)
        if name in {"aemet-daily", "surfrad-observations"}:
            command.add_argument(
                "--maximum-days", type=int, default=3660 if name == "aemet-daily" else 366
            )


def run_station_command(args: argparse.Namespace) -> None:
    """Acquire selected snapshots; completed partitions verify before requesting data."""
    if args.command.startswith("aemet-"):
        hosts = AEMET_HOSTS
    elif args.command.startswith("dwd-"):
        hosts = DWD_HOSTS
    else:
        hosts = SURFRAD_HOSTS
    with HTTPClient(
        hosts,
        config=HTTPConfig(
            minimum_interval_seconds=args.request_interval,
            maximum_response_bytes=args.maximum_response_bytes,
        ),
    ) as http:
        if args.command.startswith("aemet-"):
            _aemet(args, http)
        elif args.command.startswith("dwd-"):
            _dwd(args, http)
        else:
            _surfrad(args, http)


def _aemet(args: argparse.Namespace, http: HTTPClient) -> None:
    client = AEMETClient.from_environment(
        http,
        maximum_rows=args.maximum_rows,
        maximum_days=getattr(args, "maximum_days", 3660),
    )
    if args.command == "aemet-stations":
        bbox = tuple(args.bbox) if args.bbox is not None else None
        _emit(client.retrieve_stations(args.output, bbox=bbox))
    elif args.command == "aemet-recent":
        _emit(client.retrieve_recent(args.station, args.output))
    else:
        for start, end in daily_chunks(args.start, args.end, maximum_days=args.maximum_days):
            output = args.output / _folder(args.station) / f"daily_{start}_{end}.parquet"
            _emit(client.retrieve_daily(args.station, start, end, output))


def _dwd(args: argparse.Namespace, http: HTTPClient) -> None:
    client = DWDClient(
        http,
        maximum_rows=getattr(args, "maximum_rows", 1_000_000),
        maximum_stations=getattr(args, "maximum_stations", 10_000),
        maximum_archive_members=getattr(args, "maximum_archive_members", 128),
        maximum_uncompressed_bytes=getattr(args, "maximum_uncompressed_bytes", 512 * 1024**2),
    )
    if args.command == "dwd-stations":
        bbox = tuple(args.bbox) if args.bbox is not None else None
        _emit(client.retrieve_stations(args.output, bbox=bbox))
    else:
        _emit(client.retrieve(args.station, args.start, args.end, args.output))


def _surfrad(args: argparse.Namespace, http: HTTPClient) -> None:
    maximum_days = getattr(args, "maximum_days", 366)
    client = SURFRADClient(
        http, maximum_rows=getattr(args, "maximum_rows", 1440), maximum_days=maximum_days
    )
    if args.command == "surfrad-stations":
        _emit(client.retrieve_stations(args.output))
        return
    if args.start > args.end or (args.end - args.start).days + 1 > maximum_days:
        raise ValueError("SURFRAD date range must be ordered and fit within --maximum-days")
    current = args.start
    while current <= args.end:
        output = args.output / args.station / f"observations_{current}.parquet"
        _emit(client.retrieve(args.station, current, output))
        if current == args.end:
            break
        current += timedelta(days=1)
