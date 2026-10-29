"""Bounded station inventories for location discovery, with explicit source status.

Loading an inventory verifies catalogue metadata only. It never certifies the
availability, continuity, quality or spatial representativeness of observations.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast

import pandas as pd
import pyarrow.parquet as pq

from energy_data_retrieval.sources.aemet import (
    AEMET_HOSTS,
    AEMETClient,
)
from energy_data_retrieval.sources.aemet import (
    normalize_stations as normalize_aemet,
)
from energy_data_retrieval.sources.aemet.client import (
    REFERENCE_IDS as AEMET_REFERENCES,
)
from energy_data_retrieval.sources.aemet.client import (
    STATIONS_ENDPOINT as AEMET_ENDPOINT,
)
from energy_data_retrieval.sources.bsrn.stations import (
    REFERENCE_IDS as BSRN_REFERENCES,
)
from energy_data_retrieval.sources.bsrn.stations import (
    STATION_HOSTS as BSRN_STATION_HOSTS,
)
from energy_data_retrieval.sources.bsrn.stations import (
    STATIONS_ENDPOINT as BSRN_ENDPOINT,
)
from energy_data_retrieval.sources.bsrn.stations import (
    fetch_stations as fetch_bsrn,
)
from energy_data_retrieval.sources.bsrn.stations import (
    normalize_stations as normalize_bsrn,
)
from energy_data_retrieval.sources.dwd import (
    DWD_HOSTS,
    DWDClient,
)
from energy_data_retrieval.sources.dwd import (
    normalize_stations as normalize_dwd,
)
from energy_data_retrieval.sources.dwd.client import (
    REFERENCE_IDS as DWD_REFERENCES,
)
from energy_data_retrieval.sources.dwd.client import (
    STATIONS_ENDPOINT as DWD_ENDPOINT,
)
from energy_data_retrieval.sources.noaa import NOAA_HOSTS, NOAAClient
from energy_data_retrieval.sources.noaa.client import (
    REFERENCE_IDS as NOAA_REFERENCES,
)
from energy_data_retrieval.sources.noaa.client import (
    STATIONS_ENDPOINT as NOAA_ENDPOINT,
)
from energy_data_retrieval.sources.surfrad import (
    SURFRAD_HOSTS,
    SURFRADClient,
)
from energy_data_retrieval.sources.surfrad import (
    normalize_stations as normalize_surfrad,
)
from energy_data_retrieval.sources.surfrad.client import (
    REFERENCE_IDS as SURFRAD_REFERENCES,
)
from energy_data_retrieval.sources.surfrad.client import (
    STATIONS_ENDPOINT as SURFRAD_ENDPOINT,
)
from energy_data_retrieval.storage import existing_artifact, fingerprint, sha256_file
from energy_data_retrieval.transport import HTTPClient, JSONValue, RetrievalError, object_value

STATION_SOURCES = ("noaa", "aemet", "dwd", "surfrad", "bsrn")
STATION_DISCOVERY_HOSTS = NOAA_HOSTS | AEMET_HOSTS | DWD_HOSTS | SURFRAD_HOSTS | BSRN_STATION_HOSTS
_COLUMNS = ("source", "station_id", "station_name", "latitude", "longitude", "elevation_m")
_ENDPOINTS = {
    "noaa": NOAA_ENDPOINT,
    "aemet": AEMET_ENDPOINT,
    "dwd": DWD_ENDPOINT,
    "surfrad": SURFRAD_ENDPOINT,
    "bsrn": BSRN_ENDPOINT,
}
_IDENTITIES = {
    "noaa": "NOAA GHCNh station catalogue",
    "aemet": "AEMET OpenData",
    "dwd": "DWD CDC",
    "surfrad": "NOAA GML SURFRAD stations",
    "bsrn": "BSRN PANGAEA station catalogue",
}
_REFERENCES = {
    "noaa": NOAA_REFERENCES,
    "aemet": AEMET_REFERENCES,
    "dwd": DWD_REFERENCES,
    "surfrad": SURFRAD_REFERENCES,
    "bsrn": BSRN_REFERENCES,
}
_PRODUCT_VARIABLES = {
    "noaa": ("temperature", "dew_point", "wind", "pressure", "visibility"),
    "aemet": ("temperature", "precipitation", "wind", "pressure", "sunshine_duration"),
    "dwd": ("global_horizontal_radiation", "diffuse_horizontal_radiation", "sunshine_duration"),
    "surfrad": ("solar_radiation", "longwave_radiation", "temperature", "humidity", "wind"),
    "bsrn": (
        "global_horizontal_radiation",
        "direct_normal_radiation",
        "diffuse_radiation",
        "longwave_radiation",
    ),
}
_NOTES = {
    "noaa": ["GHCNh inventory does not establish observation periods or variable availability."],
    "aemet": [
        "Daily-climate inventory; recent-observation availability must be checked separately.",
        "Fresh AEMET access requires AEMET_API_KEY; verified local catalogue reuse does not.",
    ],
    "dwd": [
        "The hourly solar catalogue reports date extents, not gap-free observation coverage.",
        "Catalogue positions may differ from historical positions recorded in station archives.",
    ],
    "surfrad": [
        "Catalogue installation text is not a verified observation period.",
        "SURFRAD overlaps BSRN; compare identity, time, variables and vintage before combining.",
        "Historical data-file positions can differ from current catalogue coordinates.",
    ],
    "bsrn": [
        "PANGAEA event dates do not verify monthly observation availability or continuity.",
        "The monthly DOI client requires three-letter IDs; E13 remains listed but unsupported.",
        "BSRN can overlap SURFRAD; proximity does not establish site representativeness.",
    ],
}


@dataclass(frozen=True, slots=True)
class StationCatalogue:
    source: str
    status: str
    frame: pd.DataFrame
    coverage_scope: dict[str, JSONValue]
    reference_ids: tuple[str, ...]
    requests: list[dict[str, JSONValue]]
    notes: list[str]


def _json(value: object) -> dict[str, JSONValue]:
    return cast(dict[str, JSONValue], json.loads(json.dumps(value, allow_nan=False)))


def _empty(source: str, status: str, note: str) -> StationCatalogue:
    return StationCatalogue(
        source,
        status,
        pd.DataFrame(columns=list(_COLUMNS)),
        {"provider_catalogue_complete": False, "observations_verified": False},
        tuple(_REFERENCES[source]),
        [],
        [*_NOTES[source], note],
    )


def _read_json(path: Path) -> dict[str, JSONValue]:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 8 * 1024**2:
        raise ValueError("Invalid or excessive catalogue metadata file")
    return object_value(json.loads(path.read_text("utf-8")))


def _checked_source(path: Path, record: JSONValue) -> bytes:
    saved = object_value(record)
    if (
        path.is_symlink()
        or not path.is_file()
        or path.stat().st_size > 64 * 1024**2
        or saved.get("filename", path.name) != path.name
        or saved.get("size_bytes") != path.stat().st_size
        or saved.get("sha256") != sha256_file(path)
    ):
        raise ValueError("Native catalogue sidecar differs from its saved checksum")
    return path.read_bytes()


def _bbox(value: JSONValue) -> tuple[float, float, float, float] | None:
    if value is None:
        return None
    if (
        not isinstance(value, list)
        or len(value) != 4
        or any(
            not isinstance(item, (int, float)) or isinstance(item, bool) or not math.isfinite(item)
            for item in value
        )
    ):
        raise ValueError("Invalid saved catalogue bounding box")
    west, south, east, north = cast(list[float], value)
    if not -180 <= west <= east <= 180 or not -90 <= south <= north <= 90:
        raise ValueError("Invalid saved catalogue bounding box")
    return west, south, east, north


def _validate_local_source(
    source: str, path: Path, request: dict[str, JSONValue], provenance: dict[str, JSONValue]
) -> pd.DataFrame | None:
    bbox = _bbox(request.get("bbox_west_south_east_north"))
    if source == "aemet":
        if request.get("product") != "stations":
            raise ValueError("Local AEMET file is not an inventory")
        records = object_value(provenance.get("source_artifacts"))
        native: list[JSONValue] = []
        for suffix in (".source.json", ".metadata.json", ".envelope.json"):
            sidecar = path.with_suffix(path.suffix + suffix)
            raw = _checked_source(sidecar, records.get(sidecar.name))
            native.append(json.loads(raw))
        maximum = request.get("maximum_rows")
        if type(maximum) is not int:
            raise ValueError("Local AEMET inventory omits its source row bound")
        return normalize_aemet(native[0], object_value(native[1]), bbox=bbox, maximum_rows=maximum)
    if source == "dwd":
        if request.get("product") != "hourly_solar_station_catalogue":
            raise ValueError("Local DWD file is not an inventory")
        raw = _checked_source(
            path.with_suffix(path.suffix + ".source.txt"), provenance.get("source_artifact")
        )
        return normalize_dwd(raw, bbox=bbox, maximum_stations=100_000)
    if source == "surfrad":
        raw = _checked_source(path.with_suffix(".source.html"), provenance.get("native_source"))
        return normalize_surfrad(raw.decode("utf-8"))
    if source == "bsrn":
        raw = _checked_source(
            path.with_suffix(path.suffix + ".source.tsv"), provenance.get("source_artifact")
        )
        return normalize_bsrn(raw.decode("utf-8"))
    return None


def _load_local(source: str, path: Path) -> tuple[pd.DataFrame, list[dict[str, JSONValue]]]:
    if (
        path.suffix.lower() not in {".parquet", ".pq"}
        or path.is_symlink()
        or not path.is_file()
        or path.stat().st_size > 64 * 1024**2
    ):
        raise ValueError("Local catalogue must be a bounded regular Parquet snapshot")
    manifest = _read_json(path.with_suffix(path.suffix + ".json"))
    request = object_value(manifest.get("request"))
    provenance = object_value(manifest.get("provenance"))
    if (
        request.get("source") != _IDENTITIES[source]
        or request.get("endpoint") != _ENDPOINTS[source]
    ):
        raise ValueError("Local snapshot belongs to a different source or product")
    artifact = existing_artifact(path, fingerprint(request))
    parquet = pq.ParquetFile(path)
    if artifact is None or parquet.metadata.num_rows > 100_000 or parquet.metadata.num_columns > 64:
        raise ValueError("Local catalogue exceeds its bounded schema or row count")
    frame = pd.read_parquet(path)
    if len(frame) != artifact.rows or _json(frame.attrs) != provenance.get("metadata"):
        raise ValueError("Local catalogue metadata differs from its saved manifest")
    expected = _validate_local_source(source, path, request, provenance)
    # Parquet may restore equivalent Pandas strings with a different storage backend.
    if expected is not None and (
        not frame.astype(object).equals(expected.astype(object))
        or _json(frame.attrs) != _json(expected.attrs)
    ):
        raise ValueError("Local catalogue differs from its preserved native source")
    bbox = _bbox(request.get("bbox_west_south_east_north"))
    if _json({"bbox": frame.attrs.get("bbox_west_south_east_north")})["bbox"] != (
        list(bbox) if bbox is not None else None
    ):
        raise ValueError("Local catalogue bounding box differs from its request")
    if source == "noaa" and frame.attrs.get("country_code_filter") != request.get(
        "country_code_iso"
    ):
        raise ValueError("Local catalogue country filter differs from its request")
    records = provenance.get("requests")
    if records is None:
        records = [provenance["request"]]
    if not isinstance(records, list):
        raise ValueError("Local catalogue lacks acquisition records")
    return frame, [object_value(record) for record in records]


def _finish(
    source: str, status: str, frame: pd.DataFrame, requests: list[dict[str, JSONValue]]
) -> StationCatalogue:
    if not set(_COLUMNS[1:]).issubset(frame.columns):
        raise ValueError("Catalogue omits required identity and location columns")
    if frame["station_id"].isna().any() or frame["station_id"].duplicated().any():
        raise ValueError("Catalogue has missing or duplicate identities")
    output = frame.copy(deep=True)
    output["source"] = source
    output.attrs = dict(frame.attrs)
    output.attrs.update(
        product_supported_variables=list(_PRODUCT_VARIABLES[source]),
        station_variable_availability_verified=False,
        observation_availability_verified=False,
    )
    bbox = output.attrs.get("bbox_west_south_east_north")
    country = output.attrs.get("country_code_filter")
    notes = [
        *_NOTES[source],
        "Listed variables describe the product; measurements at each station remain unverified.",
    ]
    if status == "local_catalogue":
        notes.append(
            "This is a verified saved catalogue snapshot; freshness was not checked online."
        )
    if bbox is not None or country is not None:
        notes.append(
            "This catalogue is filtered; results outside its saved scope are not assessed."
        )
    scope = _json(
        {
            "provider_catalogue_complete": bbox is None and country is None,
            "bbox_west_south_east_north": bbox,
            "country_code_filter": country,
            "observations_verified": False,
        }
    )
    return StationCatalogue(
        source, status, output, scope, tuple(_REFERENCES[source]), requests, notes
    )


def load_station_catalogue(
    source: str, http: HTTPClient | None, *, local_path: Path | None = None
) -> StationCatalogue:
    """Load one verified inventory and report failures without hiding other sources.

    An explicit local snapshot is never replaced by a fresh request on validation
    failure. Callers may rank a successful frame, but a failure frame is not
    evidence that no stations exist near the requested location.
    """
    if source not in STATION_SOURCES:
        raise ValueError("Unknown station source; choose noaa, aemet, dwd, surfrad or bsrn")
    if local_path is not None:
        try:
            frame, requests = _load_local(source, local_path)
            return _finish(source, "local_catalogue", frame, requests)
        except (OSError, ValueError, TypeError, KeyError, RetrievalError):
            return _empty(
                source,
                "invalid_local_catalogue",
                "Local inventory or provenance failed validation; no live fallback was made.",
            )
    if http is None:
        return _empty(source, "not_requested", "No live client or local inventory was supplied.")
    try:
        if source == "aemet":
            client = AEMETClient.from_environment(http)
            if not client.api_key:
                return _empty(
                    source, "credentials_required", "Fresh access requires AEMET_API_KEY."
                )
            aemet = client.stations()
            return _finish(
                source,
                "catalogue_loaded",
                aemet.frame,
                [_json(asdict(item)) for item in aemet.requests],
            )
        if source == "noaa":
            noaa = NOAAClient(http).stations()
            frame, record = noaa.frame, noaa.request
        elif source == "dwd":
            dwd = DWDClient(http).stations()
            frame, record = dwd.frame, dwd.request
        elif source == "surfrad":
            surfrad = SURFRADClient(http).stations()
            frame, record = surfrad.frame, surfrad.request
        else:
            bsrn = fetch_bsrn(http)
            frame, record = bsrn.frame, bsrn.request
        return _finish(source, "catalogue_loaded", frame, [_json(asdict(record))])
    except (OSError, ValueError, TypeError, KeyError, RetrievalError):
        return _empty(
            source,
            "provider_error",
            "Inventory retrieval or validation failed; observation availability remains unknown.",
        )
