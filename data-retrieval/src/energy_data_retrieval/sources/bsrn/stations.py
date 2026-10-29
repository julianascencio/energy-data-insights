"""Official PANGAEA BSRN station inventory, separate from monthly DOI discovery.

The inventory lists station events and their metadata. Event start/end dates do
not establish that observations exist for every month, variable or location.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import cast

import pandas as pd

from energy_data_retrieval.sources.bsrn.client import REFERENCE_IDS as DATA_REFERENCE_IDS
from energy_data_retrieval.storage import Artifact, write_parquet
from energy_data_retrieval.transport import (
    HTTPClient,
    JSONValue,
    RequestRecord,
    RetrievalError,
    atomic_bytes,
)

STATIONS_ENDPOINT = "https://dataportals.pangaea.de/bsrn/stations"
STATION_HOSTS = frozenset({"dataportals.pangaea.de"})
REFERENCE_IDS = (*DATA_REFERENCE_IDS, "bsrn_station_catalogue")
_COLUMNS = (
    "Event, optional label",
    "Event label",
    "Location",
    "Station info",
    "Latitude",
    "Longitude",
    "Elevation",
    "Date/Time start",
    "Date/Time end",
    "Comment",
    "URI of event",
)


def _number(value: str, *, bound: float | None = None) -> float:
    if not value:
        return float("nan")
    try:
        number = float(value)
    except ValueError:
        raise RetrievalError("BSRN station catalogue has an invalid numeric field") from None
    if not math.isfinite(number) or (bound is not None and abs(number) > bound):
        raise RetrievalError("BSRN station catalogue has an invalid numeric field")
    return number


def _date(value: str) -> str | None:
    if not value:
        return None
    try:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError
        return date.fromisoformat(value).isoformat()
    except ValueError:
        raise RetrievalError("BSRN station catalogue has an invalid event date") from None


def normalize_stations(text: str, *, maximum_stations: int = 1000) -> pd.DataFrame:
    """Parse bounded official TSV, retaining native names, fields and event dates."""
    if type(maximum_stations) is not int or not 1 <= maximum_stations <= 10_000:
        raise ValueError("maximum_stations must be an integer from 1 through 10000")
    if not text.endswith(("\n", "\r")) or len(text.encode("utf-8")) > 4 * 1024**2:
        raise RetrievalError("BSRN station catalogue is incomplete or exceeds its byte bound")
    reader = csv.reader(io.StringIO(text.removeprefix("\ufeff")), delimiter="\t", strict=True)
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    try:
        if tuple(next(reader)) != _COLUMNS:
            raise RetrievalError("BSRN station catalogue has an unsupported header")
        for values in reader:
            if len(rows) >= maximum_stations or len(values) != len(_COLUMNS):
                raise RetrievalError("BSRN station catalogue exceeds its bound or row width")
            native = dict(zip(_COLUMNS, values, strict=True))
            code = native["Event label"]
            if not re.fullmatch(r"[A-Z0-9]{3}", code) or code in seen:
                raise RetrievalError("BSRN station catalogue has invalid or duplicate station IDs")
            if not native["Event, optional label"].strip():
                raise RetrievalError("BSRN station catalogue omits a station name")
            seen.add(code)
            latitude = _number(native["Latitude"], bound=90)
            longitude = _number(native["Longitude"], bound=180)
            start = _date(native["Date/Time start"])
            end = _date(native["Date/Time end"])
            if start is not None and end is not None and start > end:
                raise RetrievalError("BSRN station event dates are reversed")
            rows.append(
                {
                    "source": "bsrn",
                    "station_id": code.lower(),
                    "station_name": native["Event, optional label"],
                    "latitude": latitude,
                    "longitude": longitude,
                    "elevation_m": _number(native["Elevation"]),
                    "coordinates_valid": math.isfinite(latitude) and math.isfinite(longitude),
                    "catalogue_start": start,
                    "catalogue_end": end,
                    "retrieval_supported": re.fullmatch(r"[A-Z]{3}", code) is not None,
                    **{f"source:{key}": value for key, value in native.items()},
                }
            )
    except (csv.Error, StopIteration):
        raise RetrievalError("BSRN station catalogue is not a complete TSV table") from None
    if not rows:
        raise RetrievalError("BSRN station catalogue is empty")
    frame = pd.DataFrame(rows).sort_values("station_id").reset_index(drop=True)
    frame.attrs = {
        "source": "BSRN PANGAEA station catalogue",
        "endpoint": STATIONS_ENDPOINT,
        "source_rows": len(frame),
        "invalid_coordinate_rows": int((~frame["coordinates_valid"]).sum()),
        "availability_inferred": False,
        "event_dates_are_observation_coverage": False,
        "catalogue_coordinates_are_historical_positions": False,
        "reference_ids": list(REFERENCE_IDS),
    }
    return frame


@dataclass(frozen=True, slots=True)
class BSRNStations:
    frame: pd.DataFrame
    request: RequestRecord
    source_text: str


def fetch_stations(http: HTTPClient) -> BSRNStations:
    """Fetch only the official inventory, without downloading monthly observations."""
    response = http.get_text(STATIONS_ENDPOINT, {"format": "textfile"}, use_cache=False)
    return BSRNStations(normalize_stations(response.value), response.record, response.value)


def save_stations(result: BSRNStations, output: Path) -> Artifact:
    """Save a verifiable inventory and its exact native TSV for later offline discovery."""
    if output.suffix.lower() not in {".parquet", ".pq"}:
        raise ValueError("BSRN station catalogue output must use a .parquet or .pq filename")
    native = output.with_suffix(output.suffix + ".source.tsv")
    manifest = output.with_suffix(output.suffix + ".json")
    if any(path.exists() or path.is_symlink() for path in (output, native, manifest)):
        raise ValueError("BSRN catalogue output already exists; select a new snapshot path")
    expected = normalize_stations(result.source_text)
    raw = result.source_text.encode("utf-8")
    if (
        result.request.endpoint != STATIONS_ENDPOINT
        or result.request.parameters != {"format": "textfile"}
        or result.request.sha256 != hashlib.sha256(raw).hexdigest()
        or result.request.size_bytes != len(raw)
        or not result.frame.equals(expected)
        or result.frame.attrs != expected.attrs
    ):
        raise ValueError("BSRN catalogue does not match its native source and request record")
    request: dict[str, JSONValue] = {
        "source": "BSRN PANGAEA station catalogue",
        "schema_version": 1,
        "endpoint": STATIONS_ENDPOINT,
        "format": "textfile",
    }
    provenance = cast(
        dict[str, JSONValue],
        json.loads(
            json.dumps(
                {
                    "request": asdict(result.request),
                    "metadata": result.frame.attrs,
                    "source_artifact": {
                        "filename": native.name,
                        "sha256": result.request.sha256,
                        "size_bytes": result.request.size_bytes,
                    },
                },
                allow_nan=False,
            )
        ),
    )
    atomic_bytes(native, raw)
    return write_parquet(result.frame, output, request=request, provenance=provenance)
