"""Explicit acquisition of actual generation with provider-native time semantics."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, replace
from datetime import date, datetime
from pathlib import Path
from typing import cast

from energy_data_retrieval.sources.aemo import AEMO_HOSTS, AEMOClient
from energy_data_retrieval.sources.eia import EIA_HOSTS, EIAClient
from energy_data_retrieval.sources.entsoe import ENTSOE_HOSTS, ENTSOEClient
from energy_data_retrieval.sources.ree import REE_HOSTS, REE_SYSTEMS, REEClient
from energy_data_retrieval.storage import existing_artifact, fingerprint, write_parquet
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, JSONValue

GENERATION_COMMANDS = frozenset(
    {
        "aemo-generation",
        "eia-generation",
        "eia-plant-generation",
        "ree-generation",
        "entsoe-generation",
    }
)


def _date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError("Use YYYY-MM-DD") from None


def _timestamp(value: str) -> datetime:
    try:
        stamp = datetime.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError(
            "Use an ISO timestamp with Z or an explicit UTC offset"
        ) from None
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise argparse.ArgumentTypeError("Timestamp must carry Z or an explicit UTC offset")
    return stamp


def add_generation_parsers(commands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register one named command for each generation product."""
    descriptions = {
        "aemo-generation": "Retrieve one archived NEM day of DUID-level SCADA MW",
        "eia-generation": "Retrieve EIA hourly MWh by balancing authority and fuel",
        "eia-plant-generation": "Retrieve EIA monthly plant generation by fuel and prime mover",
        "ree-generation": "Retrieve REData system generation MWh by technology",
        "entsoe-generation": "Retrieve ENTSO-E actual generation by type or published unit",
    }
    for name, description in descriptions.items():
        command = commands.add_parser(name, help=description, description=description)
        command.add_argument(
            "--output", type=Path, required=True, help="New .parquet snapshot path"
        )
        command.add_argument("--request-interval", type=float, default=0.5)
        command.add_argument("--maximum-response-bytes", type=int, default=64 * 1024**2)
        if name == "aemo-generation":
            command.add_argument(
                "--date", type=_date, required=True, help="NEM calendar day (UTC+10)"
            )
            command.add_argument(
                "--duid", action="append", help="Exact DUID; repeat to select units"
            )
            continue
        if name == "ree-generation":
            command.add_argument("--start", type=_date, required=True, help="Inclusive source date")
            command.add_argument("--end", type=_date, required=True, help="Inclusive source date")
            command.add_argument("--system", choices=[*REE_SYSTEMS, "ccaa"], default="national")
            command.add_argument("--geo-id", help="Community ID, only when --system ccaa")
            command.add_argument("--aggregation", choices=["day", "month", "year"], default="day")
            command.add_argument("--include-total", action="store_true")
            command.add_argument("--maximum-requests", type=int, default=32)
        elif name == "entsoe-generation":
            command.add_argument(
                "--start", type=_timestamp, required=True, help="Inclusive UTC boundary"
            )
            command.add_argument(
                "--end", type=_timestamp, required=True, help="Exclusive UTC boundary"
            )
            command.add_argument("--area", required=True, help="16-character EIC area code")
            command.add_argument("--psr-type", help="Optional production-type code, such as B16")
            command.add_argument("--per-unit", action="store_true", help="Use A73 instead of A75")
            command.add_argument(
                "--unit-id", help="Optional published unit EIC; requires --per-unit"
            )
            command.add_argument("--maximum-requests", type=int, default=366)
        else:
            command.add_argument("--fuel-type", action="append", help="Exact EIA fuel code; repeat")
            command.add_argument("--page-size", type=int, default=5000)
            command.add_argument("--maximum-pages", type=int, default=200)
            if name == "eia-generation":
                command.add_argument(
                    "--start",
                    type=_timestamp,
                    required=True,
                    help="Inclusive UTC hour-ending label",
                )
                command.add_argument(
                    "--end", type=_timestamp, required=True, help="Inclusive UTC hour-ending label"
                )
                command.add_argument("--respondent", action="append", required=True, help="BA code")
            else:
                command.add_argument("--start", required=True, help="Inclusive month, YYYY-MM")
                command.add_argument("--end", required=True, help="Inclusive month, YYYY-MM")
                command.add_argument("--plant-code", action="append", required=True)
                command.add_argument("--prime-mover", action="append")


def _json(value: object) -> dict[str, JSONValue]:
    return cast(dict[str, JSONValue], json.loads(json.dumps(value, allow_nan=False)))


def run_generation_command(args: argparse.Namespace) -> dict[str, JSONValue]:
    """Write a source-specific snapshot and manifest; reuse only matching outputs.

    Credentials are read only from the environment by the selected provider and
    are never accepted as CLI arguments or included in the output identity.
    To retrieve revisions, use a new output path, preserving the earlier snapshot.
    """
    if args.output.suffix.lower() != ".parquet":
        raise ValueError("Generation output must use a .parquet filename")
    if args.command == "entsoe-generation" and args.unit_id and not args.per_unit:
        raise ValueError("--unit-id requires --per-unit")
    request: dict[str, JSONValue] = {"schema_version": 1}
    for key, value in vars(args).items():
        if key in {"output", "request_interval", "maximum_response_bytes"}:
            continue
        request[key] = value.isoformat() if isinstance(value, (date, datetime)) else value
    previous = existing_artifact(args.output, fingerprint(request))
    if previous is not None:
        return _json(asdict(previous))
    prefix = args.command.split("-", maxsplit=1)[0]
    hosts = {"aemo": AEMO_HOSTS, "eia": EIA_HOSTS, "ree": REE_HOSTS, "entsoe": ENTSOE_HOSTS}
    with HTTPClient(
        hosts[prefix],
        config=HTTPConfig(
            minimum_interval_seconds=args.request_interval,
            maximum_response_bytes=args.maximum_response_bytes,
        ),
    ) as http:
        if prefix == "aemo":
            aemo = AEMOClient(http).generation_day(args.date, duids=args.duid)
            frame, records = aemo.frame, (aemo.request,)
        elif prefix == "eia":
            client = replace(
                EIAClient.from_environment(http),
                page_size=args.page_size,
                maximum_pages=args.maximum_pages,
            )
            if args.command == "eia-generation":
                eia = client.hourly_generation(
                    args.start, args.end, respondents=args.respondent, fuel_types=args.fuel_type
                )
            else:
                eia = client.monthly_generation(
                    args.start,
                    args.end,
                    plant_codes=args.plant_code,
                    fuel_types=args.fuel_type,
                    prime_movers=args.prime_mover,
                )
            frame, records = eia.frame, eia.requests
        elif prefix == "ree":
            ree = REEClient(http, maximum_requests=args.maximum_requests).generation(
                args.start,
                args.end,
                time_trunc=args.aggregation,
                system=args.system,
                geo_id=args.geo_id,
                include_total=args.include_total,
            )
            frame, records = ree.frame, ree.requests
        else:
            entsoe_client = replace(
                ENTSOEClient.from_environment(http), maximum_requests=args.maximum_requests
            )
            if args.per_unit:
                entsoe = entsoe_client.generation_by_unit(
                    args.area, args.start, args.end, psr_type=args.psr_type, unit_id=args.unit_id
                )
            else:
                entsoe = entsoe_client.generation_by_type(
                    args.area, args.start, args.end, psr_type=args.psr_type
                )
            frame, records = entsoe.data, entsoe.requests
    artifact = write_parquet(
        frame,
        args.output,
        request=request,
        provenance=_json(
            {"requests": [asdict(record) for record in records], "metadata": frame.attrs}
        ),
    )
    return _json(asdict(artifact))
