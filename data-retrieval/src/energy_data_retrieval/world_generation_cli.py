"""Bounded worldwide generation retrieval and imports of native measured exports."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import cast

from energy_data_retrieval.generation import GenerationResult
from energy_data_retrieval.sources.adme import ADME_HOSTS, ADMEClient
from energy_data_retrieval.sources.aeso import AESO_HOSTS, AESOClient
from energy_data_retrieval.sources.caiso import CAISO_HOSTS, CAISOClient
from energy_data_retrieval.sources.dkasc import DKASCClient
from energy_data_retrieval.sources.elexon import ELEXON_HOSTS, ElexonClient
from energy_data_retrieval.sources.emi import EMI_HOSTS, EMIClient
from energy_data_retrieval.sources.eskom import ESKOM_HOSTS, EskomClient
from energy_data_retrieval.sources.ieso import IESO_HOSTS, IESOClient
from energy_data_retrieval.sources.kpx import KPX_HOSTS, KPXClient
from energy_data_retrieval.sources.nist import NISTClient
from energy_data_retrieval.sources.ons import ONS_HOSTS, ONSClient
from energy_data_retrieval.sources.pvdaq import PVDAQ_HOSTS, PVDAQClient
from energy_data_retrieval.sources.rte import RTE_HOSTS, RTEClient
from energy_data_retrieval.sources.smard import SMARD_HOSTS, SMARD_TECHNOLOGIES, SMARDClient
from energy_data_retrieval.sources.taipower import TAIPOWER_HOSTS, TaipowerClient
from energy_data_retrieval.sources.tepco import TEPCO_HOSTS, TEPCOClient
from energy_data_retrieval.sources.xm import XM_HOSTS, XMClient
from energy_data_retrieval.storage import (
    existing_artifact,
    fingerprint,
    sha256_file,
    write_parquet,
)
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, JSONValue, RetrievalError

_DESCRIPTIONS = {
    "adme-generation": "Retrieve Uruguay ADME plant SCADA MW from public SAS archives",
    "aeso-generation": "Retrieve current Alberta asset net MW; reads AESO_API_KEY",
    "aeso-history": "Import an extracted native AESO CSD historical generation CSV",
    "caiso-generation": "Retrieve CAISO operational fuel-mix MW, including separate flow labels",
    "dkasc-import": "Import a downloaded DKASC five-minute average AC power CSV in kW",
    "elexon-generation": "Retrieve Elexon B1610 signed BM-unit half-hour metered MWh",
    "emi-generation": "Retrieve NZ EMI plant/connection half-hour injection in kWh",
    "eskom-generation": "Retrieve Eskom's latest hourly renewable MW export",
    "ieso-generation": "Retrieve IESO recent unit-level hourly MW XML reports",
    "kpx-generation": "Retrieve Korea regional market-traded solar MWh; reads KPX_API_KEY",
    "nist-import": "Import a downloaded NIST PV AC power CSV or native TOA5 export in kW",
    "ons-generation": "Retrieve Brazil ONS hourly verified plant generation in MW",
    "ons-solar-curtailment": "Retrieve ONS half-hour PV actual output and curtailment fields",
    "pvdaq-generation": "Retrieve a selected PVDAQ measured-power channel with explicit units",
    "pvdaq-metrics": "Retrieve PVDAQ system channel metadata to select power and units",
    "rte-generation": "Retrieve France RTE consolidated national half-hour generation MW",
    "smard-generation": "Retrieve German SMARD solar/wind quarter-hour generation MWh",
    "taipower-generation": "Retrieve one Taiwan Taipower current generation MW snapshot",
    "tepco-generation": "Retrieve Tokyo-area TEPCO half-hour average generation MW",
    "xm-generation": "Retrieve Colombia XM SIMEM hourly resource MWh, retaining native kWh",
}
WORLD_GENERATION_COMMANDS = frozenset(_DESCRIPTIONS)
_IMPORT_COMMANDS = frozenset({"aeso-history", "dkasc-import", "nist-import"})
_HOSTS = {
    "adme": ADME_HOSTS,
    "aeso": AESO_HOSTS,
    "caiso": CAISO_HOSTS,
    "elexon": ELEXON_HOSTS,
    "emi": EMI_HOSTS,
    "eskom": ESKOM_HOSTS,
    "ieso": IESO_HOSTS,
    "kpx": KPX_HOSTS,
    "ons": ONS_HOSTS,
    "pvdaq": PVDAQ_HOSTS,
    "rte": RTE_HOSTS,
    "smard": SMARD_HOSTS,
    "taipower": TAIPOWER_HOSTS,
    "tepco": TEPCO_HOSTS,
    "xm": XM_HOSTS,
}
_REQUEST_LIMITS = {
    "adme": 32,
    "caiso": 31,
    "elexon": 64,
    "emi": 24,
    "ieso": 31,
    "kpx": 100,
    "ons": 25,
    "pvdaq": 31,
    "rte": 64,
    "smard": 64,
    "tepco": 24,
    "xm": 31,
}
_ROW_LIMITS = {
    "adme": 100_000,
    "emi": 2_000_000,
    "eskom": 100_000,
    "kpx": 100_000,
    "taipower": 20_000,
}
_SOURCE_CLOCKS = {
    "adme": "America/Montevideo",
    "caiso": "America/Los_Angeles",
    "elexon": "UK settlement",
    "emi": "Pacific/Auckland",
    "eskom": "Africa/Johannesburg",
    "ieso": "fixed EST (UTC-05:00)",
    "kpx": "Asia/Seoul",
    "ons": "selected Brazilian source clock",
    "pvdaq": "selected system clock",
    "rte": "Europe/Paris",
    "smard": "Europe/Berlin",
    "tepco": "Asia/Tokyo",
    "xm": "America/Bogota",
}


def _date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError("Use YYYY-MM-DD") from None


def _positive(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("Use a positive integer") from None
    if number < 1:
        raise argparse.ArgumentTypeError("Use a positive integer")
    return number


def _provider_options(command: argparse.ArgumentParser, name: str) -> None:
    if name == "adme-generation":
        command.add_argument("--central-id", type=_positive, required=True)
        command.add_argument("--power-series", help="Exact measured SCADA channel if ambiguous")
        command.add_argument("--source-timezone", default="America/Montevideo")
    elif name == "aeso-generation":
        command.add_argument("--asset-id", action="append", help="Exact AESO asset ID; repeat")
    elif name == "aeso-history":
        command.add_argument(
            "--interval-minutes",
            type=int,
            choices=(5, 60),
            required=True,
            help="Identify the native export's averaging interval",
        )
    elif name == "dkasc-import":
        command.add_argument("--system-id", required=True)
        command.add_argument("--timestamp-column", required=True)
        command.add_argument("--timestamp-format", required=True, help="Explicit pandas format")
        command.add_argument("--power-column", required=True, help="Exact 5-Min-Avg kW channel")
    elif name == "elexon-generation":
        command.add_argument("--bm-unit", help="Exact published BM-unit identifier")
    elif name == "emi-generation":
        command.add_argument("--plant", action="append", help="Exact Gen_Code; repeat")
    elif name == "eskom-generation":
        command.add_argument("--url", help="Optional official Hourly_Generation CSV archive URL")
    elif name == "ieso-generation":
        command.add_argument("--unit-id", action="append", help="Exact reported unit ID; repeat")
    elif name == "kpx-generation":
        command.add_argument("--region", help="Exact Korean region name; default all returned")
        command.add_argument("--page-size", type=_positive, default=1000)
    elif name == "nist-import":
        command.add_argument("--array", choices=("ground", "roof", "canopy"), required=True)
        command.add_argument("--power-column", default="InvPAC_kW_Avg")
        command.add_argument("--timestamp-column", default="TIMESTAMP")
        command.add_argument(
            "--source-timezone", default="-05:00", help="Default fixed EST, without daylight saving"
        )
        command.add_argument(
            "--resolution", choices=("one-minute", "one-second"), default="one-minute"
        )
    elif name in {"ons-generation", "ons-solar-curtailment"}:
        command.add_argument("--plant-id", action="append", help="Exact ONS plant ID; repeat")
        command.add_argument("--source-timezone", default="America/Sao_Paulo")
        if name == "ons-generation":
            command.add_argument("--include-estimates", action="store_true")
    elif name.startswith("pvdaq-"):
        command.add_argument("--system-id", type=_positive, required=True)
        if name == "pvdaq-generation":
            command.add_argument("--power-column", required=True, help="Exact channel from metrics")
            command.add_argument("--unit", choices=("W", "kW", "MW"), required=True)
            command.add_argument(
                "--source-timezone",
                required=True,
                help="Explicit system clock; e.g. America/Denver or --source-timezone=-07:00",
            )
    elif name == "rte-generation":
        command.add_argument("--page-size", type=_positive, default=100)
    elif name == "smard-generation":
        command.add_argument(
            "--technology",
            action="append",
            choices=tuple(SMARD_TECHNOLOGIES),
            help="Repeat; default solar, wind_onshore, wind_offshore",
        )
    elif name == "taipower-generation":
        command.add_argument("--include-aggregates", action="store_true")
        command.add_argument("--include-storage-load", action="store_true")
    elif name == "tepco-generation":
        command.add_argument(
            "--include-flows",
            action="store_true",
            help="Also retain distinct storage/import/curtailment series",
        )
    elif name == "xm-generation":
        command.add_argument(
            "--version",
            choices=("TX1", "TX2", "TX3", "TX4", "TX5", "TXF", "TXR"),
            default="TXF",
            help="Exact settlement revision to retrieve",
        )
        command.add_argument("--resource-id", action="append", help="Exact resource ID; repeat")


def add_world_generation_parsers(
    commands: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Register explicit measured-generation products and local import commands."""
    for name, description in _DESCRIPTIONS.items():
        command = commands.add_parser(name, help=description, description=description)
        source = name.split("-", maxsplit=1)[0]
        command.add_argument(
            "--output",
            type=Path,
            required=True,
            help="New .parquet snapshot path; revisions require a new path",
        )
        command.add_argument(
            "--maximum-rows", type=_positive, default=_ROW_LIMITS.get(source, 1_000_000)
        )
        if name in _IMPORT_COMMANDS:
            command.add_argument(
                "--input",
                type=Path,
                required=True,
                help="Existing native provider export, not a generated template",
            )
            command.add_argument(
                "--maximum-input-bytes",
                type=_positive,
                default=(64 if source == "aeso" else 128) * 1024**2,
            )
        else:
            command.add_argument("--request-interval", type=float, default=0.5)
            command.add_argument("--maximum-response-bytes", type=_positive, default=64 * 1024**2)
            if source in _REQUEST_LIMITS and name != "pvdaq-metrics":
                command.add_argument(
                    "--maximum-requests", type=_positive, default=_REQUEST_LIMITS[source]
                )
            if source in _SOURCE_CLOCKS and name != "pvdaq-metrics":
                for boundary in ("start", "end"):
                    command.add_argument(
                        f"--{boundary}",
                        type=_date,
                        required=source != "eskom",
                        help=f"Inclusive {_SOURCE_CLOCKS[source]} source date",
                    )
        _provider_options(command, name)


def _json(value: object) -> dict[str, JSONValue]:
    return cast(dict[str, JSONValue], json.loads(json.dumps(value, allow_nan=False)))


def _local_result(args: argparse.Namespace) -> GenerationResult:
    if args.command == "nist-import":
        return NISTClient(maximum_rows=args.maximum_rows).read_export(
            args.input,
            array=args.array,
            power_column=args.power_column,
            timestamp_column=args.timestamp_column,
            source_timezone=args.source_timezone,
            resolution=args.resolution,
        )
    if args.command == "dkasc-import":
        return DKASCClient(maximum_rows=args.maximum_rows).read_export(
            args.input,
            system_id=args.system_id,
            power_column=args.power_column,
            timestamp_column=args.timestamp_column,
            timestamp_format=args.timestamp_format,
        )
    # The AESO importer shares a client with the current API, but issues no HTTP requests.
    with HTTPClient(AESO_HOSTS) as http:
        return AESOClient(http, maximum_rows=args.maximum_rows).from_native_file(
            args.input,
            interval_minutes=args.interval_minutes,
            maximum_bytes=args.maximum_input_bytes,
        )


def _remote_result(args: argparse.Namespace, http: HTTPClient) -> GenerationResult:
    name = args.command
    if name == "adme-generation":
        return ADMEClient(
            http, maximum_requests=args.maximum_requests, maximum_rows=args.maximum_rows
        ).generation(
            args.start,
            args.end,
            central_id=args.central_id,
            power_series=args.power_series,
            source_timezone=args.source_timezone,
        )
    if name == "aeso-generation":
        key = os.environ.get("AESO_API_KEY", "")
        if not key.strip():
            raise ValueError("Set AESO_API_KEY to your AESO API subscription key")
        return AESOClient(http, maximum_rows=args.maximum_rows).current_generation(
            api_key=key,
            asset_ids=args.asset_id,
        )
    if name == "caiso-generation":
        return CAISOClient(
            http, maximum_requests=args.maximum_requests, maximum_rows=args.maximum_rows
        ).generation(args.start, args.end)
    if name == "elexon-generation":
        return ElexonClient(
            http, maximum_requests=args.maximum_requests, maximum_rows=args.maximum_rows
        ).generation(
            args.start,
            args.end,
            bm_unit=args.bm_unit,
        )
    if name == "emi-generation":
        return EMIClient(
            http, maximum_requests=args.maximum_requests, maximum_rows=args.maximum_rows
        ).generation(
            args.start,
            args.end,
            plants=args.plant,
        )
    if name == "eskom-generation":
        return EskomClient(http, maximum_rows=args.maximum_rows).generation(
            args.start,
            args.end,
            url=args.url,
        )
    if name == "ieso-generation":
        return IESOClient(
            http, maximum_requests=args.maximum_requests, maximum_rows=args.maximum_rows
        ).generation(
            args.start,
            args.end,
            unit_ids=args.unit_id,
        )
    if name == "kpx-generation":
        return KPXClient.from_environment(
            http,
            maximum_requests=args.maximum_requests,
            maximum_rows=args.maximum_rows,
            page_size=args.page_size,
        ).solar_generation(args.start, args.end, region=args.region)
    if name in {"ons-generation", "ons-solar-curtailment"}:
        client = ONSClient(
            http, maximum_requests=args.maximum_requests, maximum_rows=args.maximum_rows
        )
        if name == "ons-solar-curtailment":
            return client.solar_curtailment(
                args.start,
                args.end,
                plant_ids=args.plant_id,
                source_timezone=args.source_timezone,
            )
        return client.generation(
            args.start,
            args.end,
            plant_ids=args.plant_id,
            source_timezone=args.source_timezone,
            include_estimates=args.include_estimates,
        )
    if name in {"pvdaq-generation", "pvdaq-metrics"}:
        pvdaq = PVDAQClient(
            http,
            maximum_requests=getattr(args, "maximum_requests", 1),
            maximum_rows=args.maximum_rows,
        )
        if name == "pvdaq-metrics":
            return pvdaq.metrics(args.system_id)
        return pvdaq.generation(
            args.system_id,
            args.start,
            args.end,
            power_column=args.power_column,
            unit=args.unit,
            source_timezone=args.source_timezone,
        )
    if name == "rte-generation":
        return RTEClient(
            http,
            maximum_requests=args.maximum_requests,
            maximum_rows=args.maximum_rows,
            page_size=args.page_size,
        ).generation(
            args.start,
            args.end,
        )
    if name == "smard-generation":
        return SMARDClient(
            http, maximum_requests=args.maximum_requests, maximum_rows=args.maximum_rows
        ).generation(
            args.start,
            args.end,
            technologies=args.technology or ("solar", "wind_onshore", "wind_offshore"),
        )
    if name == "taipower-generation":
        return TaipowerClient(http, maximum_rows=args.maximum_rows).latest(
            include_aggregates=args.include_aggregates,
            include_storage_load=args.include_storage_load,
        )
    if name == "tepco-generation":
        return TEPCOClient(
            http, maximum_requests=args.maximum_requests, maximum_rows=args.maximum_rows
        ).generation(
            args.start,
            args.end,
            include_flows=args.include_flows,
        )
    if name == "xm-generation":
        return XMClient(
            http, maximum_requests=args.maximum_requests, maximum_rows=args.maximum_rows
        ).generation(
            args.start,
            args.end,
            version=args.version,
            resource_ids=args.resource_id,
        )
    raise ValueError("Unsupported worldwide generation command")


def run_world_generation_command(args: argparse.Namespace) -> dict[str, JSONValue]:
    """Publish immutable Parquet plus a checksum/provenance manifest.

    Matching snapshots can be reused without network or credentials. File imports
    also fingerprint the native bytes before reuse, so changing a file in place
    cannot silently return an older result. Tokens never enter the request identity.
    """
    if args.command not in WORLD_GENERATION_COMMANDS:
        raise ValueError("Unsupported worldwide generation command")
    if args.output.suffix.lower() != ".parquet":
        raise ValueError("Generation output must use a .parquet filename")
    manifest = args.output.with_suffix(args.output.suffix + ".json")
    if args.output.is_symlink() or manifest.is_symlink():
        raise ValueError("Generation output and manifest must not be symbolic links")
    request: dict[str, JSONValue] = {"schema_version": 1}
    for key, value in vars(args).items():
        if key in {"output", "request_interval", "maximum_response_bytes"}:
            continue
        if isinstance(value, date):
            value = value.isoformat()
        elif isinstance(value, Path):
            value = str(value.resolve())
        request[key] = value
    importing = args.command in _IMPORT_COMMANDS
    if importing:
        if not args.input.is_file():
            raise ValueError("--input must identify an existing native provider export file")
        if not 1 <= args.maximum_input_bytes <= 128 * 1024**2:
            raise ValueError("maximum_input_bytes must be in 1..134217728 (128 MiB)")
        if args.input.stat().st_size > args.maximum_input_bytes:
            raise ValueError("Native export exceeds maximum_input_bytes")
        request["input_sha256"] = sha256_file(args.input)
        request["input_size_bytes"] = args.input.stat().st_size
    previous = existing_artifact(args.output, fingerprint(request))
    if previous is not None:
        return _json(asdict(previous))
    if importing:
        result = _local_result(args)
        actual_checksum = result.frame.attrs.get(
            "input_sha256", result.frame.attrs.get("local_file_sha256")
        )
        if actual_checksum != request["input_sha256"]:
            raise RetrievalError(
                "Native export changed while importing; choose a stable input file"
            )
    else:
        source = args.command.split("-", maxsplit=1)[0]
        with HTTPClient(
            _HOSTS[source],
            config=HTTPConfig(
                minimum_interval_seconds=args.request_interval,
                maximum_response_bytes=args.maximum_response_bytes,
            ),
        ) as http:
            result = _remote_result(args, http)
    provenance = _json(
        {
            "requests": [asdict(record) for record in result.requests],
            "metadata": result.frame.attrs,
        }
    )
    artifact = write_parquet(result.frame, args.output, request=request, provenance=provenance)
    return _json(asdict(artifact))
