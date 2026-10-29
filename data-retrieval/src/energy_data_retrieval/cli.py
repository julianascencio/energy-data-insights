"""Command-line retrieval with explicit sources, date ranges and local checkpoints."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tomllib
from collections.abc import Iterator, Sequence
from dataclasses import asdict
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import cast

import pandas as pd

from energy_data_retrieval.sources.cen import CENClient, aggregate_units, normalize_registry
from energy_data_retrieval.sources.cen.client import CEN_HOSTS, REGISTRY_ENDPOINT
from energy_data_retrieval.sources.cen.history import (
    CEN_EXPORT_HOSTS,
    HistorySchema,
    import_history,
)
from energy_data_retrieval.sources.cmip6 import (
    CMIP6_DATA_HOSTS,
    CMIP6_INDEX_HOSTS,
    CMIP6Client,
    CMIP6Query,
    download_plan,
    load_plan,
    save_plan,
)
from energy_data_retrieval.sources.earthmover_era5 import NativeERA5Client
from energy_data_retrieval.sources.earthmover_era5.client import PINNED_SNAPSHOT
from energy_data_retrieval.sources.open_meteo import OpenMeteoClient, Site, WeatherProduct
from energy_data_retrieval.sources.open_meteo.client import OPEN_METEO_HOSTS
from energy_data_retrieval.sources.station import StationSchema, import_station
from energy_data_retrieval.storage import (
    Artifact,
    bounded_map,
    existing_artifact,
    fingerprint,
    sha256_file,
    write_parquet,
)
from energy_data_retrieval.transport import (
    HTTPClient,
    HTTPConfig,
    JSONValue,
    RetrievalError,
    array_value,
    atomic_bytes,
)


def _iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError("Use a date in YYYY-MM-DD form") from None


def _hostname(value: str) -> str:
    name = value.lower()
    if len(name) > 253 or not re.fullmatch(
        r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
        r"[a-z](?:[a-z0-9-]{0,61}[a-z0-9])?",
        name,
    ):
        raise argparse.ArgumentTypeError("Use a complete DNS hostname without a URL, port or path")
    return name


def _days(start: date, end: date) -> Iterator[date]:
    if start > end:
        raise ValueError("--start must be on or before --end")
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def _sites(path: Path) -> list[Site]:
    frame = (
        pd.read_parquet(path)
        if path.suffix.lower() in {".parquet", ".pq"}
        else pd.read_csv(path, dtype={"site_id": str})
    )
    if not {"site_id", "latitude", "longitude"}.issubset(frame.columns):
        raise ValueError("Sites CSV requires site_id, latitude, longitude")
    if frame["site_id"].isna().any() or frame["site_id"].duplicated().any():
        raise ValueError("Site IDs must be non-null and unique")
    return [
        Site(str(row.site_id), float(str(row.latitude)), float(str(row.longitude)))
        for row in frame.itertuples()
    ]


def _slug(site_id: str) -> str:
    readable = re.sub(r"[^A-Za-z0-9_-]", "_", site_id)[:48]
    return readable + "_" + hashlib.sha256(site_id.encode()).hexdigest()[:10]


def _emit(record: Artifact) -> None:
    print(json.dumps(asdict(record), sort_keys=True), flush=True)


def _json_object(value: object) -> dict[str, JSONValue]:
    # Round-trip ensures arbitrary pandas attrs cannot smuggle non-JSON values into provenance.
    return cast(dict[str, JSONValue], json.loads(json.dumps(value, allow_nan=False)))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    cmip6_search = commands.add_parser(
        "cmip6-search", help="Discover exact CMIP6 datasets and save a versioned download plan"
    )
    for option, destination in (
        ("model", "source_id"),
        ("experiment", "experiment_id"),
        ("member", "member_id"),
        ("table", "table_id"),
        ("variable", "variable_id"),
        ("grid", "grid_label"),
    ):
        cmip6_search.add_argument(f"--{option}", dest=destination, required=True)
    cmip6_search.add_argument("--institution", dest="institution_id")
    cmip6_search.add_argument("--activity", dest="activity_id")
    cmip6_search.add_argument("--version", help="Exact dataset version; default resolves latest")
    cmip6_search.add_argument(
        "--start-year", type=int, help="Select whole files overlapping these years; does not crop"
    )
    cmip6_search.add_argument(
        "--end-year", type=int, help="Inclusive final year for file selection"
    )
    cmip6_search.add_argument("--index", choices=("east", "west"), default="east")
    cmip6_search.add_argument("--page-size", type=int, default=20)
    cmip6_search.add_argument("--maximum-datasets", type=int, default=100)
    cmip6_search.add_argument("--maximum-files", type=int, default=1000)
    cmip6_search.add_argument("--output", type=Path, required=True, help="New JSON download plan")
    cmip6_download = commands.add_parser(
        "cmip6-download", help="Retrieve native CMIP6 NetCDF files from a saved, verified plan"
    )
    cmip6_download.add_argument("--plan", type=Path, required=True)
    cmip6_download.add_argument("--output", type=Path, required=True)
    cmip6_download.add_argument("--maximum-file-bytes", type=int, default=512 * 1024 * 1024)
    cmip6_download.add_argument("--maximum-total-bytes", type=int, default=2 * 1024**3)
    cmip6_download.add_argument(
        "--allow-host",
        action="append",
        type=_hostname,
        default=[],
        help="Explicitly allow an additional verified public ESGF data hostname; repeat as needed",
    )
    for command in (cmip6_search, cmip6_download):
        command.add_argument("--request-interval", type=float, default=0.25)
    for name, help_text in (
        ("cen-history", "Import a preserved hourly CEN bulk/Qlik CSV or XLSX export"),
        ("station-import", "Import explicitly mapped measured hourly station observations"),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("--input", type=Path, required=True)
        command.add_argument("--mapping", type=Path, required=True)
        command.add_argument(
            "--schema", type=Path, required=True, help="Explicit source TOML contract"
        )
        command.add_argument("--zip-member")
        command.add_argument("--output", type=Path, required=True)
    download = commands.add_parser("cen-download", help="Download a known public CEN export URL")
    download.add_argument("--url", required=True)
    download.add_argument("--output", type=Path, required=True)
    download.add_argument("--sha256", help="Optional independent expected source checksum")
    download.add_argument("--maximum-bytes", type=int, default=512 * 1024 * 1024)
    download.add_argument("--request-interval", type=float, default=0.25)
    registry = commands.add_parser("cen-registry", help="Retrieve public CEN plant metadata")
    registry.add_argument("--output", type=Path, required=True, help="New .parquet output path")
    generation = commands.add_parser("cen-generation", help="Retrieve CEN actual generation by day")
    generation.add_argument(
        "--unit-roster",
        type=Path,
        help="Verified site_id,unit_id CSV valid for the requested period",
    )
    generation.add_argument("--technology", default="Solar")
    generation.add_argument("--page-size", type=int, default=5000)
    weather = commands.add_parser(
        "open-meteo", help="Retrieve explicit ERA5 or archived IFS weather"
    )
    weather.add_argument(
        "--product", choices=[item.value for item in WeatherProduct], default="era5"
    )
    weather.add_argument("--chunk-days", type=int, default=31)
    weather.add_argument("--workers", type=int, default=2)
    weather.add_argument("--sites", type=Path, required=True)
    native = commands.add_parser(
        "era5-native", help="Retrieve a pinned native ERA5 Icechunk snapshot"
    )
    native.add_argument("--sites", type=Path, required=True)
    native.add_argument("--snapshot", default=PINNED_SNAPSHOT)
    native.add_argument("--chunk-hours", type=int, default=8736)
    for command in (generation, weather, native):
        command.add_argument("--start", type=_iso_date, required=True)
        command.add_argument("--end", type=_iso_date, required=True)
        command.add_argument(
            "--output", type=Path, required=True, help="Output partition directory"
        )
    for command in (registry, generation, weather):
        command.add_argument("--cache-directory", type=Path)
        command.add_argument("--request-interval", type=float, default=0.25)
    return parser


def _cmip6(args: argparse.Namespace) -> dict[str, object]:
    if args.command == "cmip6-search":
        if args.output.exists():
            raise ValueError("Download plan already exists; choose a new output path")
        query = CMIP6Query(
            source_id=args.source_id,
            experiment_id=args.experiment_id,
            member_id=args.member_id,
            table_id=args.table_id,
            variable_id=args.variable_id,
            grid_label=args.grid_label,
            institution_id=args.institution_id,
            activity_id=args.activity_id,
            version=args.version,
            start_year=args.start_year,
            end_year=args.end_year,
        )
        with HTTPClient(
            CMIP6_INDEX_HOSTS,
            config=HTTPConfig(minimum_interval_seconds=args.request_interval),
        ) as http:
            plan = CMIP6Client(
                http,
                index=args.index,
                page_size=args.page_size,
                maximum_datasets=args.maximum_datasets,
                maximum_files=args.maximum_files,
            ).search(query)
        save_plan(plan, args.output)
        return {
            "plan": str(args.output),
            "index": plan.index,
            "files": len(plan.files),
            "total_size_bytes": plan.total_size_bytes,
            "downloaded": False,
            "selection": "whole native files; no spatial or temporal cropping",
        }
    plan = load_plan(args.plan)
    with HTTPClient(
        CMIP6_DATA_HOSTS | frozenset(args.allow_host),
        config=HTTPConfig(
            maximum_response_bytes=args.maximum_file_bytes,
            minimum_interval_seconds=args.request_interval,
        ),
    ) as http:
        return download_plan(plan, args.output, http, maximum_total_bytes=args.maximum_total_bytes)


def _generation(args: argparse.Namespace, http: HTTPClient) -> None:
    client = CENClient.from_environment(http)
    client.page_size = args.page_size
    client.__post_init__()
    roster: dict[str, frozenset[str]] | None = None
    roster_hash: str | None = None
    if args.unit_roster:
        source = pd.read_csv(args.unit_roster, dtype=str)
        if (
            not {"site_id", "unit_id"}.issubset(source.columns)
            or source[["site_id", "unit_id"]].isna().any().any()
        ):
            raise ValueError("Unit roster requires non-null site_id and unit_id columns")
        roster = {
            str(site): frozenset(group["unit_id"]) for site, group in source.groupby("site_id")
        }
        roster_hash = sha256_file(args.unit_roster)
    for day in _days(args.start, args.end):
        request: dict[str, JSONValue] = {
            "source": "CEN",
            "date": day.isoformat(),
            "technology": args.technology,
            "time_convention": "America/Santiago interval start converted to UTC",
            "aggregation": "site" if roster is not None else "operating_unit",
            "roster_sha256": roster_hash,
        }
        output = args.output / f"generation_{day.isoformat()}.parquet"
        old = existing_artifact(output, fingerprint(request))
        if old is not None:
            _emit(old)
            continue
        day_result = client.generation_day(day, technology=args.technology)
        frame = (
            aggregate_units(day_result.units, roster) if roster is not None else day_result.units
        )
        exclusions_file = args.output / f"generation_{day.isoformat()}_exclusions.json"
        exclusions = day_result.exclusions.to_dict(orient="records")
        atomic_bytes(
            exclusions_file, json.dumps(exclusions, ensure_ascii=False, allow_nan=False).encode()
        )
        provenance = _json_object(
            {
                "requests": [asdict(record) for record in day_result.requests],
                "units_metadata": day_result.units.attrs,
                "aggregation_level": "site" if roster is not None else "operating_unit",
                "excluded_rows": len(day_result.exclusions),
                "exclusions_sha256": sha256_file(exclusions_file),
                "pagination_complete": True,
                "national_coverage_claimed": False,
                "energy_rule": "source mean MW times one elapsed hour",
            }
        )
        _emit(write_parquet(frame, output, request=request, provenance=provenance))


def _open_meteo(args: argparse.Namespace, http: HTTPClient) -> None:
    sites = _sites(args.sites)
    client = OpenMeteoClient(
        http,
        WeatherProduct(args.product),
        os.environ.get("OPEN_METEO_API_KEY"),
        args.chunk_days,
    )

    def jobs() -> Iterator[tuple[Site, date, date]]:
        if args.start > args.end:
            raise ValueError("--start must be on or before --end")
        for site in sites:
            current = args.start
            while current <= args.end:
                stop = min(args.end, current + timedelta(days=client.chunk_days - 1))
                yield site, current, stop
                current = stop + timedelta(days=1)

    def acquire(job: tuple[Site, date, date]) -> Artifact:
        site, start, end = job
        request = _json_object(
            {
                "source": "Open-Meteo",
                "product": client.product.value,
                "site": asdict(site),
                "start": start.isoformat(),
                "end": end.isoformat(),
                "time_convention": "UTC interval start",
            }
        )
        output = args.output / f"{_slug(site.site_id)}_{start}_{end}.parquet"
        old = existing_artifact(output, fingerprint(request))
        if old is not None:
            return old
        result = client.weather(site, start, end)
        provenance = _json_object(
            {
                "request": asdict(result.request),
                "metadata": result.frame.attrs,
                "cell_latitude": result.cell_latitude,
                "cell_longitude": result.cell_longitude,
            }
        )
        return write_parquet(result.frame, output, request=request, provenance=provenance)

    for record in bounded_map(acquire, jobs(), workers=args.workers):
        _emit(record)


def _native(args: argparse.Namespace) -> None:
    client = NativeERA5Client(args.snapshot, args.chunk_hours)

    def identity(
        site: Site,
        first_second: int,
        last_second: int,
        latitude: float,
        longitude: float,
    ) -> tuple[Path, dict[str, JSONValue]]:
        first = datetime.fromtimestamp(first_second, UTC).strftime("%Y%m%dT%H%MZ")
        last = datetime.fromtimestamp(last_second, UTC).strftime("%Y%m%dT%H%MZ")
        request = _json_object(
            {
                "source": "Earthmover ERA5",
                "snapshot_id": client.snapshot_id,
                "site": asdict(site),
                "first_interval": first,
                "last_interval": last,
                "cell_latitude": latitude,
                "cell_longitude": longitude,
            }
        )
        output = args.output / f"{_slug(site.site_id)}_{first}_{last}.parquet"
        return output, request

    def skip(
        site: Site,
        first_second: int,
        last_second: int,
        latitude: float,
        longitude: float,
    ) -> bool:
        output, request = identity(site, first_second, last_second, latitude, longitude)
        existing = existing_artifact(output, fingerprint(request))
        if existing is not None:
            _emit(existing)
            return True
        return False

    for result in client.iter_weather(
        _sites(args.sites), args.start, args.end, skip_partition=skip
    ):
        output, request = identity(
            result.site,
            int(result.frame["timestamp"].iloc[0].timestamp()),
            int(result.frame["timestamp"].iloc[-1].timestamp()),
            result.cell_latitude,
            result.cell_longitude,
        )
        _emit(
            write_parquet(
                result.frame,
                output,
                request=request,
                provenance=_json_object(
                    {"metadata": result.frame.attrs, "station_observations": False}
                ),
            )
        )


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command in {"cmip6-search", "cmip6-download"}:
        try:
            result = _cmip6(args)
        except (OSError, ValueError, RetrievalError) as error:
            parser.exit(2, f"CMIP6 retrieval failed: {error}\n")
        print(json.dumps(result, sort_keys=True, allow_nan=False))
        return 0
    if args.command in {"cen-history", "station-import"}:
        with args.schema.open("rb") as stream:
            settings = tomllib.load(stream)
        if args.command == "cen-history":
            record = import_history(
                args.input,
                args.mapping,
                args.output,
                HistorySchema(**settings),
                member=args.zip_member,
            )
        else:
            record = import_station(
                args.input,
                args.mapping,
                args.output,
                StationSchema(**settings),
                member=args.zip_member,
            )
        _emit(record)
        return 0
    if args.command == "cen-download":
        with HTTPClient(
            CEN_EXPORT_HOSTS,
            config=HTTPConfig(
                maximum_response_bytes=args.maximum_bytes,
                minimum_interval_seconds=args.request_interval,
            ),
        ) as http:
            downloaded = http.download_file(args.url, args.output, expected_sha256=args.sha256)
        print(json.dumps(asdict(downloaded), sort_keys=True))
        return 0
    if args.command == "era5-native":
        _native(args)
        return 0
    hosts = OPEN_METEO_HOSTS if args.command == "open-meteo" else CEN_HOSTS
    with HTTPClient(
        hosts,
        config=HTTPConfig(minimum_interval_seconds=args.request_interval),
        cache_directory=args.cache_directory,
    ) as http:
        if args.command == "cen-registry":
            response = http.get_json(REGISTRY_ENDPOINT)
            frame = normalize_registry(array_value(response.value))
            _emit(
                write_parquet(
                    frame,
                    args.output,
                    request={"source": "CEN registry", "endpoint": REGISTRY_ENDPOINT},
                    provenance=_json_object(
                        {"request": asdict(response.record), "dc_capacity_inferred": False}
                    ),
                )
            )
        elif args.command == "cen-generation":
            _generation(args, http)
        else:
            _open_meteo(args, http)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
