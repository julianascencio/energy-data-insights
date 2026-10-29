"""Location-based candidates and bounded evidence for existing gridded sources.

Documented global coverage is a discovery hint, not a data-availability check.
Only an explicit sample request resolves an Open-Meteo cell and one UTC day of
values. A CMIP6 catalogue plan establishes dataset/file identity, not the presence
of a variable at a point on its native grid.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict
from datetime import date
from typing import cast

from energy_data_retrieval.sources.cmip6 import CMIP6Plan
from energy_data_retrieval.sources.cmip6.client import REFERENCE_IDS as CMIP6_REFERENCE_IDS
from energy_data_retrieval.sources.earthmover_era5.client import PINNED_SNAPSHOT
from energy_data_retrieval.sources.open_meteo import OpenMeteoClient, Site, WeatherProduct
from energy_data_retrieval.transport import HTTPClient, JSONValue, RetrievalError

_THESIS = "ascencio_vasquez_2021_thesis"
_OPEN_METEO_VARIABLES = (
    "shortwave_radiation",
    "temperature_2m",
    "wind_speed_10m",
    "wind_gusts_10m",
)
_OUTPUT_VARIABLES = ("ghi_wm2", "temperature_c", "wind_speed_ms", "gust_ms")
_PRODUCTS = {
    "open_meteo_era5": WeatherProduct.ERA5,
    "open_meteo_ifs": WeatherProduct.IFS,
}


def _coordinates(latitude: object, longitude: object) -> tuple[float, float]:
    if any(
        isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value)
        for value in (latitude, longitude)
    ):
        raise ValueError("Latitude and longitude must be finite numbers")
    lat, lon = float(cast(float, latitude)), float(cast(float, longitude))
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ValueError("WGS84 latitude/longitude out of range")
    return lat, lon


def _json_object(value: object) -> dict[str, JSONValue]:
    return cast(dict[str, JSONValue], json.loads(json.dumps(value, allow_nan=False)))


def _date(value: object, label: str) -> date:
    if type(value) is not date:
        raise ValueError(f"{label} must be a calendar date, without a time or timezone")
    return value


def _base(latitude: float, longitude: float) -> dict[str, JSONValue]:
    return {
        "requested_latitude": latitude,
        "requested_longitude": longitude,
        "geographic_status": "documented_coverage",
        "geographic_scope": "global",
        "availability_status": "not_checked",
        "cell_latitude": None,
        "cell_longitude": None,
        "coverage_start": None,
        "coverage_end": None,
        "temporal_status": "not_requested",
    }


def grid_datasets(
    latitude: float,
    longitude: float,
    *,
    start: date | None = None,
    end: date | None = None,
) -> list[dict[str, JSONValue]]:
    """Describe only integrated products; perform no network or file reads.

    Optional inclusive dates annotate compatibility with documented coverage. Unknown
    coverage is retained explicitly, and a documented overlap never verifies actual
    values or recent availability. Snapshot dates and CMIP6 grid coordinates are not
    inferred from a generic product's headline coverage.
    """
    latitude, longitude = _coordinates(latitude, longitude)
    if (start is None) != (end is None):
        raise ValueError("start and end must be supplied together")
    if start is not None and end is not None:
        start, end = _date(start, "start"), _date(end, "end")
        if start > end:
            raise ValueError("start must be on or before end")
    location: dict[str, JSONValue] = {
        "site_id": "location",
        "latitude": latitude,
        "longitude": longitude,
    }
    common_notes: list[JSONValue] = [
        "Modelled data; geographic coverage does not establish available values at this point.",
        "No data downloaded and no nearest grid cell inferred during candidate discovery.",
    ]
    rows: list[dict[str, JSONValue]] = []
    for product, title, kind, reference in (
        (
            WeatherProduct.ERA5,
            "Open-Meteo ERA5 reanalysis",
            "reanalysis",
            "open_meteo_historical_weather",
        ),
        (
            WeatherProduct.IFS,
            "Open-Meteo archived ECMWF IFS forecasts",
            "archived_forecast",
            "open_meteo_historical_forecast",
        ),
    ):
        era5 = product == WeatherProduct.ERA5
        references: list[JSONValue] = [_THESIS, reference, "open_meteo_variable_definitions"]
        if era5:
            references.extend(("hersbach_2020_era5", "era5_single_levels"))
        rows.append(
            _base(latitude, longitude)
            | {
                "source": "open_meteo",
                "dataset_id": f"open_meteo_{product.value}",
                "title": title,
                "data_kind": kind,
                "spatial_resolution": (
                    "0.25 degrees, documented ERA5 grid"
                    if era5
                    else "ECMWF IFS model and archive vintage dependent"
                ),
                "temporal_resolution": "hourly API output",
                "supported_variables": list(_OPEN_METEO_VARIABLES),
                "output_variables": list(_OUTPUT_VARIABLES),
                "coverage_start": "1940-01-01" if era5 else None,
                "access": {
                    "route": "public HTTPS or optional customer API",
                    "credential": "OPEN_METEO_API_KEY for the customer route",
                    "optional_dependencies": [],
                },
                "reference_ids": references,
                "retrieval": {
                    "command": "open-meteo",
                    "parameters": {"product": product.value},
                    "site": location.copy(),
                    "required_inputs": ["sites", "start", "end", "output"],
                },
                "notes": [
                    *common_notes,
                    "Nearest-cell selection disables elevation downscaling.",
                    (
                        "Latest ERA5 availability is delayed and must be checked with the provider."
                        if era5
                        else "Forecast models and archive coverage change with model vintage."
                    ),
                ],
            }
        )
    rows.append(
        _base(latitude, longitude)
        | {
            "source": "earthmover_era5",
            "dataset_id": "earthmover_era5",
            "title": "Native ERA5 in a pinned Earthmover Icechunk snapshot",
            "data_kind": "reanalysis",
            "spatial_resolution": "0.25 degrees, documented ERA5 grid",
            "temporal_resolution": "hourly",
            "supported_variables": ["t2m", "u10", "v10", "ssrd", "fg10"],
            "output_variables": list(_OUTPUT_VARIABLES),
            "snapshot_id": PINNED_SNAPSHOT,
            "access": {
                "route": "anonymous public S3",
                "credential": None,
                "optional_dependencies": ["energy-data-retrieval[era5-native]"],
            },
            "reference_ids": [
                _THESIS,
                "hersbach_2020_era5",
                "era5_single_levels",
                "earthmover_icechunk_era5",
            ],
            "retrieval": {
                "command": "era5-native",
                "parameters": {"snapshot": PINNED_SNAPSHOT},
                "site": location.copy(),
                "required_inputs": ["sites", "start", "end", "output"],
            },
            "notes": [
                *common_notes,
                "Open the pinned snapshot to verify its coordinate axes and time coverage.",
                "Both endpoints of every requested hourly interval must exist in that snapshot.",
                "The current public catalogue's headline dates do not establish snapshot coverage.",
            ],
        }
    )
    rows.append(
        _base(latitude, longitude)
        | {
            "source": "cmip6",
            "dataset_id": "cmip6",
            "title": "CMIP6 model/experiment/member/variable selection",
            "data_kind": "climate_model",
            "geographic_status": "point_coverage_unverified",
            "geographic_scope": "selected model and native grid dependent",
            "selection_status": "required",
            "spatial_resolution": "model and native grid dependent",
            "temporal_resolution": "selected CMIP6 table and native calendar dependent",
            "supported_variables": [],
            "output_variables": [],
            "access": {
                "route": "public ESGF STAC metadata and approved native HTTPS assets",
                "credential": None,
                "optional_dependencies": [],
            },
            "reference_ids": list(CMIP6_REFERENCE_IDS),
            "retrieval": {
                "command": "cmip6-search",
                "parameters": {},
                "required_inputs": [
                    "model",
                    "experiment",
                    "member",
                    "table",
                    "variable",
                    "grid",
                    "output",
                ],
            },
            "notes": [
                "Latitude/longitude alone does not select a CMIP6 dataset or ensemble member.",
                "Inspect native coordinates, variable masks and calendars for point coverage.",
                "A catalogue plan selects whole files; it does not crop a point or grid cell.",
            ],
        }
    )
    if start is not None and end is not None:
        for row in rows:
            row.update(requested_start=start.isoformat(), requested_end=end.isoformat())
            row["temporal_status"] = "not_checked"
            if row["dataset_id"] == "open_meteo_era5":
                first = date(1940, 1, 1)
                row["temporal_status"] = (
                    "outside_documented_coverage"
                    if end < first
                    else "partly_outside_documented_coverage"
                    if start < first
                    else "within_documented_start_only"
                )
    return rows


def verify_open_meteo(
    http: HTTPClient,
    candidates: list[dict[str, JSONValue]],
    *,
    day: date,
) -> list[dict[str, JSONValue]]:
    """Probe at most the two integrated Open-Meteo products for one UTC day.

    The existing adapters request the extra endpoint needed for interval alignment.
    Each successful sample reports null counts; a partial sample never establishes
    complete availability. Failed providers do not discard other results, and raw
    exception messages are excluded from the report. The public route is used; no
    credentials are read from the environment.
    """
    day = _date(day, "day")
    if day == date.max:
        raise ValueError("day must permit the following day's interval endpoint")
    rows = [_json_object(row) for row in candidates]
    selected: list[tuple[dict[str, JSONValue], WeatherProduct, Site]] = []
    seen: set[str] = set()
    for row in rows:
        identifier = row.get("dataset_id")
        if not isinstance(identifier, str) or identifier not in _PRODUCTS:
            continue
        if identifier in seen:
            raise ValueError("Open-Meteo sample candidates must have unique dataset IDs")
        seen.add(identifier)
        latitude, longitude = _coordinates(
            row.get("requested_latitude"), row.get("requested_longitude")
        )
        selected.append((row, _PRODUCTS[identifier], Site("location", latitude, longitude)))
    for row, product, site in selected:
        row.update(cell_latitude=None, cell_longitude=None)
        sample: dict[str, JSONValue] = {
            "date": day.isoformat(),
            "scope": "one UTC day only; other dates and complete dataset availability unchecked",
            "complete": False,
        }
        row["sample"] = sample
        try:
            chunk = OpenMeteoClient(http, product, chunk_days=1).weather(site, day, day)
            latitude, longitude = _coordinates(chunk.cell_latitude, chunk.cell_longitude)
            counts = {name: int(chunk.frame[name].notna().sum()) for name in _OUTPUT_VARIABLES}
            missing = {name: len(chunk.frame) - count for name, count in counts.items()}
            row.update(cell_latitude=latitude, cell_longitude=longitude)
            row["availability_status"] = (
                "verified_sample" if any(counts.values()) else "empty_sample"
            )
            sample.update(
                rows=len(chunk.frame),
                non_null_counts=_json_object(counts),
                missing_counts=_json_object(missing),
                complete=not any(missing.values()),
                request=_json_object(asdict(chunk.request)),
            )
        except (RetrievalError, ValueError, OverflowError) as error:
            row["availability_status"] = "provider_error"
            sample.update(
                error="The provider sample could not be retrieved or validated.",
                error_type=type(error).__name__,
            )
    return rows


def cmip6_plan_candidates(
    plan: CMIP6Plan, latitude: float, longitude: float
) -> list[dict[str, JSONValue]]:
    """Summarize an existing validated catalogue plan without reading native files.

    Use a plan returned by ``CMIP6Client.search`` or ``load_plan``. The requested point
    is context only and was not an ESGF search filter. Selected native file labels,
    provider metadata and citation links remain intact; point coverage stays unknown.
    """
    latitude, longitude = _coordinates(latitude, longitude)
    rows: list[dict[str, JSONValue]] = []
    plan_sha256 = plan.sha256
    for dataset in plan.datasets:
        identifier = dataset["id"]
        files = [file for file in plan.files if file.dataset_id == identifier]
        if not files:
            continue
        row = _base(latitude, longitude) | {
            "source": "cmip6",
            "dataset_id": identifier,
            "title": " / ".join(
                (plan.query.source_id, plan.query.experiment_id, plan.query.variable_id)
            ),
            "data_kind": "climate_model",
            "geographic_status": "point_coverage_unverified",
            "geographic_scope": "selected model and native grid dependent",
            "availability_status": "catalogue_verified",
            "selection_status": "selected",
            "spatial_resolution": "inspect selected NetCDF native coordinate arrays",
            "temporal_resolution": "selected CMIP6 table and native calendar dependent",
            "temporal_status": "whole_file_selection_only",
            "supported_variables": [plan.query.variable_id],
            "output_variables": [],
            "selection": _json_object(asdict(plan.query)),
            "plan_sha256": plan_sha256,
            "index": plan.index,
            "discovered_at_utc": plan.created_at_utc,
            "selected_files": [
                _json_object(asdict(file) | {"relative_path": file.relative_path}) for file in files
            ],
            "provider_properties": dataset.get("properties"),
            "provider_links": dataset.get("links", []),
            "reference_ids": list(CMIP6_REFERENCE_IDS),
            "access": {
                "route": "approved native HTTPS assets from the saved ESGF plan",
                "credential": None,
                "optional_dependencies": [],
            },
            "retrieval": {
                "command": "cmip6-download",
                "parameters": {},
                "required_inputs": ["plan", "output"],
            },
            "notes": [
                "This point was not an ESGF catalogue search filter.",
                "Catalogue verification establishes metadata; file contents remain unchecked.",
                "Native coordinates, masks and calendar must be inspected before point extraction.",
                "Whole-file overlap by year does not establish complete requested-date coverage.",
            ],
        }
        rows.append(_json_object(row))
    return rows
