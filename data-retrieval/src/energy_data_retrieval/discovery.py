"""Discover nearby station candidates and gridded products for one location."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import cast

import pandas as pd

from energy_data_retrieval.grid_discovery import (
    cmip6_plan_candidates,
    grid_datasets,
    verify_open_meteo,
)
from energy_data_retrieval.sources.cmip6 import CMIP6Plan
from energy_data_retrieval.sources.open_meteo.client import OPEN_METEO_HOSTS
from energy_data_retrieval.spatial import MAX_NEARBY_STATIONS, nearby_stations
from energy_data_retrieval.station_discovery import (
    STATION_DISCOVERY_HOSTS,
    STATION_SOURCES,
    load_station_catalogue,
)
from energy_data_retrieval.transport import HTTPClient, JSONValue

DISCOVERY_HOSTS = STATION_DISCOVERY_HOSTS | OPEN_METEO_HOSTS
_LOADED = {"catalogue_loaded", "local_catalogue"}
_THESIS = "ascencio_vasquez_2021_thesis"


def _empty_stations() -> pd.DataFrame:
    return pd.DataFrame(columns=["source", "station_id", "latitude", "longitude"])


def _json_object(value: object) -> dict[str, JSONValue]:
    return cast(dict[str, JSONValue], json.loads(json.dumps(value, allow_nan=False)))


def _retrieval(source: str, station_id: str) -> list[dict[str, JSONValue]]:
    commands = {
        "noaa": [("noaa-observations", ["start", "end", "output"])],
        "aemet": [
            ("aemet-daily", ["start", "end", "output"]),
            ("aemet-recent", ["output"]),
        ],
        "dwd": [("dwd-solar", ["start", "end", "output"])],
        "surfrad": [("surfrad-observations", ["start", "end", "output"])],
        "bsrn": [("bsrn-search", ["year", "month", "output"])],
    }
    return [
        _json_object(
            {
                "command": command,
                "parameters": {"station": station_id},
                "required_arguments": required,
            }
        )
        for command, required in commands[source]
    ]


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    """A point-in-time catalogue search, with explicit limits on availability claims."""

    query: dict[str, JSONValue]
    stations: pd.DataFrame
    grids: list[dict[str, JSONValue]]
    source_status: list[dict[str, JSONValue]]
    created_at_utc: str
    status: str

    def as_dict(self) -> dict[str, JSONValue]:
        """Return JSON-safe rows, provenance, references and a content checksum."""
        records = json.loads(
            self.stations.to_json(orient="records", date_format="iso", double_precision=15)
        )
        for record in records:
            source, station_id = str(record["source"]), str(record["station_id"])
            record["observations_verified"] = False
            record["retrieval"] = (
                [] if record.get("retrieval_supported") is False else _retrieval(source, station_id)
            )
        reference_ids = {_THESIS}
        for item in [*self.source_status, *self.grids]:
            references = item.get("reference_ids")
            if isinstance(references, list):
                reference_ids.update(value for value in references if isinstance(value, str))
        body = _json_object(
            {
                "schema_version": 1,
                "created_at_utc": self.created_at_utc,
                "status": self.status,
                "query": self.query,
                "spatial_search": self.stations.attrs["spatial_search"],
                "stations": records,
                "grid_datasets": self.grids,
                "source_status": self.source_status,
                "reference_ids": [_THESIS, *sorted(reference_ids - {_THESIS})],
                "notes": [
                    "Distances use a mean-radius sphere and ignore terrain and elevation.",
                    "Nearby catalogue entries do not establish observation availability, "
                    "quality or suitability as a site reference.",
                    "Catalogue scope and invalid-coordinate counts are reported per source. "
                    "No matches in a filtered catalogue do not prove no nearby stations exist.",
                    "Station feeds can overlap, including SURFRAD and BSRN; identities "
                    "are preserved and observations are not deduplicated.",
                    "Grid coverage from documentation is distinguished from a verified "
                    "one-day sample; CMIP6 point coverage requires inspecting native grids.",
                ],
            }
        )
        body["discovery_sha256"] = hashlib.sha256(
            json.dumps(body, sort_keys=True, allow_nan=False).encode()
        ).hexdigest()
        return body


def find_sources(
    latitude: float,
    longitude: float,
    *,
    radius_km: float = 100.0,
    limit: int = 20,
    station_sources: Sequence[str] = STATION_SOURCES,
    catalogues: Mapping[str, Path] | None = None,
    http: HTTPClient | None = None,
    probe_date: date | None = None,
    cmip6_plan: CMIP6Plan | None = None,
) -> DiscoveryResult:
    """Find station candidates and existing grid products for a geographic point.

    ``limit`` applies across all station providers, ordered by spherical distance.
    Source catalogues are acquired once without bounding-box prefilters, so the
    search also works across the antimeridian and near the poles. A supplied
    ``catalogues`` mapping reuses verified source snapshots with their original
    geographic scope. Missing credentials and provider errors remain explicit
    source statuses; one unavailable provider does not discard successful ones.

    Pass an allowlisted ``HTTPClient`` to enable catalogue requests. With
    ``http=None``, only local catalogues and documented grid metadata are read.
    ``probe_date`` optionally verifies a small Open-Meteo sample for that date;
    the native ERA5 snapshot and CMIP6 coordinates are not implicitly downloaded.
    A verified CMIP6 retrieval plan adds its exact datasets as candidates while
    retaining the requirement to inspect their native coordinate grids.
    """
    validated = nearby_stations(
        _empty_stations(), latitude, longitude, radius_km=radius_km, limit=limit
    )
    latitude, longitude = float(latitude), float(longitude)
    if isinstance(station_sources, str):
        raise ValueError("station_sources must be a sequence of source names")
    selected = tuple(station_sources)
    if len(set(selected)) != len(selected) or any(item not in STATION_SOURCES for item in selected):
        raise ValueError("Station sources must be distinct supported source names")
    paths = dict(catalogues or {})
    if any(source not in selected for source in paths):
        raise ValueError("Every local catalogue must belong to a selected station source")
    if any(not isinstance(path, Path) for path in paths.values()):
        raise ValueError("Local catalogue values must be pathlib.Path objects")
    if probe_date is not None and (type(probe_date) is not date or http is None):
        raise ValueError("A grid probe requires an HTTP client and a calendar date")
    if probe_date == date.max:
        raise ValueError("A grid probe requires the following day's interval endpoint")

    candidates: list[pd.DataFrame] = []
    statuses: list[dict[str, JSONValue]] = []
    totals = {"input_station_count": 0, "invalid_coordinate_count": 0, "within_radius_count": 0}
    for source in selected:
        catalogue = load_station_catalogue(source, http, local_path=paths.get(source))
        details = _json_object(
            {
                "source": source,
                "status": catalogue.status,
                "coverage_scope": catalogue.coverage_scope,
                "reference_ids": list(catalogue.reference_ids),
                "requests": catalogue.requests,
                "notes": catalogue.notes,
                "catalogue_metadata": catalogue.frame.attrs,
                "product_supported_variables": catalogue.frame.attrs.get(
                    "product_supported_variables", []
                ),
                "station_variable_availability_verified": False,
                "catalogue_station_count": len(catalogue.frame),
                "search_status": "unavailable",
                "returned_station_count": 0,
            }
        )
        if catalogue.status in _LOADED:
            ranked = nearby_stations(
                catalogue.frame,
                latitude,
                longitude,
                radius_km=radius_km,
                limit=MAX_NEARBY_STATIONS,
            )
            statistics = ranked.attrs["spatial_search"]
            details["spatial_search"] = _json_object(statistics)
            details["search_status"] = "matches_found" if len(ranked) else "no_matches_in_catalogue"
            for key in totals:
                totals[key] += statistics[key]
            if not ranked.empty:
                subset = ranked.drop(columns=["rank", "distance_km"])
                subset.attrs = {}
                candidates.append(subset)
        statuses.append(details)

    if candidates:
        # Pandas otherwise warns about dtype inference for all-null columns from
        # different providers. Object preserves native values across the union.
        combined = pd.concat([frame.astype(object) for frame in candidates], ignore_index=True)
    else:
        combined = _empty_stations()
    stations = nearby_stations(combined, latitude, longitude, radius_km=radius_km, limit=limit)
    statistics = dict(validated.attrs["spatial_search"])
    statistics.update(totals)
    statistics["returned_station_count"] = len(stations)
    statistics["truncated"] = totals["within_radius_count"] > len(stations)
    stations.attrs["spatial_search"] = statistics
    for details in statuses:
        details["returned_station_count"] = int(stations["source"].eq(str(details["source"])).sum())

    grids = grid_datasets(latitude, longitude)
    if probe_date is not None:
        assert http is not None
        grids = verify_open_meteo(http, grids, day=probe_date)
    if cmip6_plan is not None:
        grids = [item for item in grids if item["source"] != "cmip6"]
        grids.extend(cmip6_plan_candidates(cmip6_plan, latitude, longitude))
    partial = any(item["status"] not in _LOADED for item in statuses) or any(
        item["availability_status"] == "provider_error" for item in grids
    )
    return DiscoveryResult(
        query=_json_object(
            {
                "latitude": float(latitude),
                "longitude": float(longitude),
                "radius_km": float(radius_km),
                "limit": int(limit),
                "station_sources": list(selected),
                "probe_date": probe_date.isoformat() if probe_date is not None else None,
                "network_enabled": http is not None,
            }
        ),
        stations=stations,
        grids=grids,
        source_status=statuses,
        created_at_utc=datetime.now(UTC).isoformat(),
        status="partial" if partial else "complete",
    )


def save_discovery(result: DiscoveryResult, path: Path) -> None:
    """Save a new JSON snapshot without overwriting an earlier discovery result."""
    if path.exists() or path.is_symlink():
        raise ValueError("Discovery snapshot already exists; choose a new output path")
    payload = json.dumps(result.as_dict(), ensure_ascii=False, indent=2, allow_nan=False).encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        # An exclusive hard link publishes the complete file without a rename
        # race overwriting a snapshot created by a concurrent discovery process.
        try:
            os.link(temporary, path)
        except FileExistsError:
            raise ValueError(
                "Discovery snapshot already exists; choose a new output path"
            ) from None
    finally:
        temporary.unlink(missing_ok=True)
