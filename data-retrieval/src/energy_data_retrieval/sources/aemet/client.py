"""AEMET station, daily-climate and rolling recent-observation acquisition.

The authenticated API returns short-lived links to data and field metadata.
Both documents are preserved as canonical JSON. Climatological dates retain
their source meaning; only recent ``fint`` labels explicitly described as UTC
in the returned metadata become UTC timestamps.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import unicodedata
from collections.abc import Iterator
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Literal, cast
from urllib.parse import urlsplit

import numpy as np
import pandas as pd

from energy_data_retrieval.storage import (
    Artifact,
    existing_artifact,
    fingerprint,
    sha256_file,
    write_parquet,
)
from energy_data_retrieval.transport import (
    HTTPClient,
    JSONValue,
    RequestRecord,
    RetrievalError,
    atomic_bytes,
    object_value,
)

AEMET_HOSTS = frozenset({"opendata.aemet.es"})
_ROOT = "https://opendata.aemet.es/opendata/api"
STATIONS_ENDPOINT = _ROOT + "/valores/climatologicos/inventarioestaciones/todasestaciones"
REFERENCE_IDS = (
    "ascencio_vasquez_2021_thesis",
    "aemet_opendata_specification",
    "aemet_opendata_access",
    "aemet_observation_guidance",
    "aemet_opendata_key_policy",
)
type Product = Literal["stations", "daily", "recent"]
type BBox = tuple[float, float, float, float]
_STATION = re.compile(r"[A-Z0-9]{3,6}")
_NUMBER = re.compile(r"[+-]?(?:\d+(?:[.,]\d*)?|[.,]\d+)(?:[eE][+-]?\d+)?")
_STAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|\+00:?00)?")
# The live daily product uses camel-case payload keys but lower-case metadata IDs.
# Keep these verified aliases explicit; arbitrary fields are not case-folded.
_METADATA_ALIASES = {"presMax": "presmax", "presMin": "presmin"}
_DAILY_VARIABLES = {
    "tmed": ("temperature_mean_c", "degC"),
    "tmin": ("temperature_min_c", "degC"),
    "tmax": ("temperature_max_c", "degC"),
    "prec": ("precipitation_mm", "mm"),
    "velmedia": ("wind_speed_mean_ms", "m/s"),
    "racha": ("wind_gust_ms", "m/s"),
    "sol": ("sunshine_duration_hours", "hours"),
    "presMax": ("station_pressure_max_hpa", "hPa"),
    "presMin": ("station_pressure_min_hpa", "hPa"),
}
_RECENT_VARIABLES = {
    "ta": ("temperature_c", "degC"),
    "tpr": ("dewpoint_c", "degC"),
    "tamax": ("temperature_max_c", "degC"),
    "tamin": ("temperature_min_c", "degC"),
    "vv": ("wind_speed_ms", "m/s"),
    "vmax": ("wind_gust_ms", "m/s"),
    "pres": ("station_pressure_hpa", "hPa"),
    "pres_nmar": ("sea_level_pressure_hpa", "hPa"),
    "hr": ("relative_humidity_percent", "%"),
    "prec": ("precipitation_mm", "mm"),
}


def _bound(value: int, label: str, maximum: int) -> None:
    if type(value) is not int or not 1 <= value <= maximum:
        raise ValueError(f"{label} must be an integer from 1 through {maximum}")


def _station(value: str) -> str:
    if not isinstance(value, str) or _STATION.fullmatch(value) is None:
        raise ValueError("Use one exact uppercase 3-6 character AEMET station identifier")
    return value


def _dates(start: date, end: date, maximum_days: int) -> None:
    _bound(maximum_days, "maximum_days", 36_600)
    if type(start) is not date or type(end) is not date or start > end or end.year > 9998:
        raise ValueError("AEMET daily dates must be ordered date objects before year 9999")
    if (end - start).days + 1 > maximum_days:
        raise ValueError("AEMET date range exceeds the configured maximum_days")


def daily_chunks(
    start: date,
    end: date,
    *,
    maximum_days: int = 3660,
    chunk_days: int = 31,
) -> Iterator[tuple[date, date]]:
    """Yield bounded inclusive daily requests without collecting a whole history."""
    _bound(chunk_days, "chunk_days", 31)
    _dates(start, end, maximum_days)
    current = start
    while current <= end:
        stop = min(end, current + timedelta(days=chunk_days - 1))
        yield current, stop
        current = stop + timedelta(days=1)


def _bbox(value: BBox | None) -> None:
    if value is None:
        return
    if len(value) != 4 or not all(math.isfinite(number) for number in value):
        raise ValueError("bbox requires finite WEST SOUTH EAST NORTH coordinates")
    west, south, east, north = value
    if not -180 <= west <= east <= 180 or not -90 <= south <= north <= 90:
        raise ValueError("bbox must be ordered WEST SOUTH EAST NORTH; split antimeridian boxes")


def _canonical(value: object) -> bytes:
    # Matches HTTPClient's canonical sanitized JSON acquisition hash exactly.
    return json.dumps(value, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _json(value: object) -> dict[str, JSONValue]:
    return cast(dict[str, JSONValue], json.loads(json.dumps(value, allow_nan=False)))


def _link(value: JSONValue) -> str:
    if not isinstance(value, str) or len(value) > 512:
        raise RetrievalError("AEMET omitted a valid temporary document link")
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in AEMET_HOSTS
        or parsed.netloc != "opendata.aemet.es"
        or parsed.query
        or parsed.fragment
        or re.fullmatch(r"/opendata/sh/[A-Za-z0-9_-]{1,200}", parsed.path) is None
    ):
        raise RetrievalError("AEMET returned an unsupported temporary document link")
    return value


def _fields(metadata: dict[str, JSONValue]) -> dict[str, dict[str, JSONValue]]:
    items = metadata.get("campos")
    if not isinstance(items, list) or not 1 <= len(items) <= 512:
        raise RetrievalError("AEMET field metadata must contain a bounded campos list")
    result = {}
    for item in items:
        record = object_value(item)
        name = record.get("id")
        if not isinstance(name, str) or not 1 <= len(name) <= 100 or name in result:
            raise RetrievalError("AEMET field metadata has a missing or duplicate identifier")
        result[name] = record
    return result


def _rows(payload: JSONValue, maximum_rows: int) -> list[dict[str, JSONValue]]:
    _bound(maximum_rows, "maximum_rows", 1_000_000)
    if not isinstance(payload, list) or not payload:
        raise RetrievalError("AEMET returned no observation or station records")
    if len(payload) > maximum_rows:
        raise RetrievalError("AEMET source exceeds maximum_rows")
    rows = [object_value(item) for item in payload]
    if any(not row or len(row) > 512 for row in rows):
        raise RetrievalError("AEMET source contains an empty or excessively wide record")
    return rows


def _raw(rows: list[dict[str, JSONValue]]) -> pd.DataFrame:
    keys = sorted({key for row in rows for key in row})
    columns = {}
    for key in keys:
        values = [row.get(key) for row in rows]
        columns[f"source:{key}"] = pd.array(
            [
                value if isinstance(value, str) or value is None else _canonical(value).decode()
                for value in values
            ],
            dtype="string[pyarrow]",
        )
    # Retain native JSON types and distinguish omitted fields from explicit null.
    columns["source_record_json"] = pd.array(
        [_canonical(row).decode() for row in rows], dtype="string[pyarrow]"
    )
    return pd.DataFrame(columns)


def _required(rows: list[dict[str, JSONValue]], names: set[str]) -> None:
    if any(not names.issubset(row) for row in rows):
        raise RetrievalError("AEMET source omits required identity or coordinate fields")


def _number(values: pd.Series, label: str, *, precipitation: bool = False) -> pd.Series:
    native = values.astype("string[pyarrow]").str.strip()
    missing = native.isna() | native.eq("")
    special = native.str.casefold().isin(["ip", "acum"]) if precipitation else missing & False
    valid = missing | special | native.str.fullmatch(_NUMBER.pattern)
    if not valid.fillna(False).all():
        raise RetrievalError(f"AEMET {label} contains an unsupported numeric value or code")
    try:
        converted = pd.to_numeric(
            native.mask(missing | special).str.replace(",", ".", regex=False), errors="raise"
        ).astype("float64")
    except (ValueError, TypeError):
        raise RetrievalError(f"AEMET {label} contains an unsupported numeric value") from None
    if np.isinf(converted.to_numpy()).any():
        raise RetrievalError(f"AEMET {label} contains a nonfinite value")
    return converted


def _unit(fields: dict[str, dict[str, JSONValue]], name: str, expected: str) -> None:
    record = fields.get(name)
    if name in _METADATA_ALIASES:
        alias = fields.get(_METADATA_ALIASES[name])
        if record is not None and alias is not None:
            exact_definition = {key: value for key, value in record.items() if key != "id"}
            alias_definition = {key: value for key, value in alias.items() if key != "id"}
            if exact_definition != alias_definition:
                raise RetrievalError(f"AEMET metadata has conflicting case aliases: {name}")
        if record is None:
            record = alias
    if record is None:
        raise RetrievalError(f"AEMET metadata omits the measured field {name}")
    declared = record.get("unidad")
    if declared is not None and not isinstance(declared, str):
        raise RetrievalError(f"AEMET metadata has an invalid unit declaration: {name}")
    text = declared if declared and declared.strip() else str(record.get("descripcion", ""))
    text = "".join(
        character
        for character in unicodedata.normalize("NFKD", text.casefold())
        if not unicodedata.combining(character)
    )
    patterns = {
        "degC": r"(?:°c|\boc\b|celsius)",
        "m/s": r"(?:m\s*/\s*s|metros? por segundo)",
        "hPa": r"(?:hpa|hectopascal)",
        "mm": r"(?:\bmm\b|milimetro)",
        "hours": r"(?:\bhoras?\b|\bh\b)",
        "%": r"(?:%|porcentaje)",
    }
    if re.search(patterns[expected], text) is None:
        raise RetrievalError(
            f"AEMET metadata does not confirm the supported {expected} unit: {name}"
        )


def _measurements(
    frame: pd.DataFrame,
    fields: dict[str, dict[str, JSONValue]],
    variables: dict[str, tuple[str, str]],
) -> dict[str, str]:
    units = {}
    for source, (target, unit) in variables.items():
        key = f"source:{source}"
        if key not in frame:
            continue
        _unit(fields, source, unit)
        frame[target] = _number(frame[key], source, precipitation=source == "prec")
        units[target] = unit
        if source == "prec":
            code = frame[key].str.strip().str.casefold()
            frame["precipitation_qualifier"] = pd.array(
                np.select(
                    [code.eq("ip").fillna(False), code.eq("acum").fillna(False)],
                    ["trace", "accumulated"],
                    default="",
                ),
                dtype="string[pyarrow]",
            )
    return units


def _deduplicate(frame: pd.DataFrame, identity: list[str]) -> tuple[pd.DataFrame, int]:
    original = len(frame)
    frame = frame.drop_duplicates().reset_index(drop=True)
    if frame.duplicated(identity).any():
        raise RetrievalError("AEMET returned conflicting records for one station/time identity")
    return frame, original - len(frame)


def _attrs(product: Product, metadata: dict[str, JSONValue]) -> dict[str, object]:
    return {
        "source": "AEMET OpenData",
        "product": product,
        "source_representation": "canonical JSON; native field values and types retained",
        "json_decoding": "Unicode JSON first; declared ISO-8859-1/15 fallback only when needed",
        "source_metadata": metadata,
        "quality_filter_applied": False,
        "gap_filling_applied": False,
        "station_to_site_mapping_applied": False,
        "reference_ids": REFERENCE_IDS,
    }


def normalize_stations(
    payload: JSONValue,
    metadata: dict[str, JSONValue],
    *,
    bbox: BBox | None = None,
    maximum_rows: int = 100_000,
) -> pd.DataFrame:
    """Keep native catalogue fields and decode explicit DMS coordinate strings."""
    _bbox(bbox)
    _fields(metadata)
    rows = _rows(payload, maximum_rows)
    _required(rows, {"indicativo", "nombre", "latitud", "longitud", "altitud"})
    out = _raw(rows)
    if not out["source:indicativo"].str.fullmatch(_STATION.pattern).fillna(False).all():
        raise RetrievalError("AEMET catalogue contains an unsupported station identifier")
    out["station_id"] = out["source:indicativo"]
    out["station_name"] = out["source:nombre"]
    for source, target, letters, bound in (
        ("latitud", "latitude", "NS", 90),
        ("longitud", "longitude", "EW", 180),
    ):
        pieces = out[f"source:{source}"].str.extract(
            rf"^(\d{{2,3}})(\d{{2}})(\d{{2}})([{letters}])$"
        )
        degrees, minutes, seconds = (
            pd.to_numeric(pieces[index], errors="coerce").astype("float64") for index in range(3)
        )
        values = degrees + minutes / 60 + seconds / 3600
        valid = degrees.between(0, bound) & minutes.between(0, 59) & seconds.between(0, 59)
        valid &= values <= bound
        values = values.where(valid)
        out[target] = values.where(~pieces[3].isin(["S", "W"]), -values)
    out["coordinates_valid"] = out["latitude"].notna() & out["longitude"].notna()
    out.loc[~out["coordinates_valid"], ["latitude", "longitude"]] = np.nan
    out["elevation_m"] = _number(out["source:altitud"], "altitud")
    out, duplicates = _deduplicate(out, ["station_id"])
    source_rows = len(out)
    invalid_coordinates = int((~out["coordinates_valid"]).sum())
    if bbox is not None:
        west, south, east, north = bbox
        out = out.loc[out["longitude"].between(west, east) & out["latitude"].between(south, north)]
    out = out.sort_values("station_id").reset_index(drop=True)
    out.attrs.update(
        _attrs("stations", metadata),
        bbox_west_south_east_north=bbox,
        source_station_rows=source_rows,
        invalid_coordinate_rows=invalid_coordinates,
        exact_duplicate_rows_removed=duplicates,
        availability_inferred=False,
    )
    return out


def normalize_daily(
    payload: JSONValue,
    metadata: dict[str, JSONValue],
    station: str,
    start: date,
    end: date,
    *,
    maximum_rows: int = 100_000,
) -> pd.DataFrame:
    """Retain climatological date labels and per-variable period semantics."""
    _station(station)
    _dates(start, end, 31)
    fields = _fields(metadata)
    rows = _rows(payload, maximum_rows)
    _required(rows, {"indicativo", "fecha"})
    out = _raw(rows)
    if not out["source:indicativo"].eq(station).fillna(False).all():
        raise RetrievalError("AEMET daily data identifies a different station")
    labels = out["source:fecha"]
    if not labels.str.fullmatch(r"\d{4}-\d{2}-\d{2}").fillna(False).all():
        raise RetrievalError("AEMET daily data needs original ISO calendar-date labels")
    try:
        parsed = pd.to_datetime(labels, format="%Y-%m-%d", errors="raise")
    except ValueError:
        raise RetrievalError("AEMET daily data has invalid calendar-date labels") from None
    if not parsed.between(pd.Timestamp(start), pd.Timestamp(end)).all():
        raise RetrievalError("AEMET daily data falls outside the requested date range")
    out["station_id"] = station
    out["date"] = labels
    units = _measurements(out, fields, _DAILY_VARIABLES)
    out, duplicates = _deduplicate(out, ["station_id", "date"])
    out = out.sort_values("date").reset_index(drop=True)
    out.attrs.update(
        _attrs("daily", metadata),
        start=start.isoformat(),
        end=end.isoformat(),
        time_convention=(
            "native climatological date; no UTC instant or common 00-24 period assigned"
        ),
        variable_periods="use each field's native aggregation-period metadata",
        precipitation_codes="Ip=trace; Acum=accumulated; both remain null numerically",
        units=units,
        exact_duplicate_rows_removed=duplicates,
        missing_date_count=(end - start).days + 1 - len(out),
    )
    return out


def normalize_recent(
    payload: JSONValue,
    metadata: dict[str, JSONValue],
    station: str,
    *,
    maximum_rows: int = 100_000,
) -> pd.DataFrame:
    """Keep the API's rolling observations and original variable averaging periods."""
    _station(station)
    fields = _fields(metadata)
    timing = fields.get("fint", {})
    if "UTC" not in (str(timing.get("descripcion", "")) + str(timing.get("unidad", ""))).upper():
        raise RetrievalError("AEMET recent field metadata must explicitly identify fint as UTC")
    rows = _rows(payload, maximum_rows)
    _required(rows, {"idema", "fint"})
    out = _raw(rows)
    if not out["source:idema"].eq(station).fillna(False).all():
        raise RetrievalError("AEMET recent data identifies a different station")
    labels = out["source:fint"]
    if not labels.str.fullmatch(_STAMP.pattern).fillna(False).all():
        raise RetrievalError("AEMET recent observations need original UTC observation labels")
    try:
        out["timestamp"] = pd.to_datetime(labels, format="ISO8601", utc=True, errors="raise")
    except ValueError:
        raise RetrievalError("AEMET recent observations have invalid UTC labels") from None
    out["station_id"] = station
    units = _measurements(out, fields, _RECENT_VARIABLES)
    out, duplicates = _deduplicate(out, ["station_id", "timestamp"])
    out = out.sort_values("timestamp").reset_index(drop=True)
    out.attrs.update(
        _attrs("recent", metadata),
        time_convention="UTC fint reporting label; variables retain their own averaging periods",
        availability="provider's rolling recent window; API v2.0 describes the latest 12 hours",
        historical_hourly_query_supported=False,
        units=units,
        exact_duplicate_rows_removed=duplicates,
        first_observation_utc=out["timestamp"].iloc[0].isoformat(),
        last_observation_utc=out["timestamp"].iloc[-1].isoformat(),
    )
    return out


def _endpoint(product: Product, station: str | None, start: date | None, end: date | None) -> str:
    if product == "stations":
        return STATIONS_ENDPOINT
    if station is None:
        raise ValueError("AEMET observations require an exact station identifier")
    _station(station)
    if product == "recent":
        return f"{_ROOT}/observacion/convencional/datos/estacion/{station}"
    if product != "daily" or start is None or end is None:
        raise ValueError("AEMET daily acquisition requires inclusive start and end dates")
    _dates(start, end, 31)
    return (
        f"{_ROOT}/valores/climatologicos/diarios/datos/"
        f"fechaini/{start.isoformat()}T00:00:00UTC/"
        f"fechafin/{end.isoformat()}T23:59:59UTC/estacion/{station}"
    )


def _request(
    product: Product,
    station: str | None,
    start: date | None,
    end: date | None,
    bbox: BBox | None,
    maximum_rows: int,
) -> dict[str, JSONValue]:
    _bbox(bbox)
    return _json(
        {
            "source": "AEMET OpenData",
            "schema_version": 1,
            "product": product,
            "endpoint": _endpoint(product, station, start, end),
            "station_id": station,
            "start": start.isoformat() if start is not None else None,
            "end": end.isoformat() if end is not None else None,
            "bbox_west_south_east_north": bbox,
            "maximum_rows": maximum_rows,
            "quality_filter_applied": False,
            "source_representation": "canonical sanitized JSON",
            "json_decoding": "Unicode JSON first; declared ISO-8859-1/15 fallback only when needed",
        }
    )


@dataclass(frozen=True, slots=True)
class AEMETDataset:
    product: Product
    station: str | None
    start: date | None
    end: date | None
    bbox: BBox | None
    maximum_rows: int
    frame: pd.DataFrame
    payload: JSONValue
    metadata: dict[str, JSONValue]
    envelope: dict[str, JSONValue]
    requests: tuple[RequestRecord, ...]


def _normalize(result: AEMETDataset) -> pd.DataFrame:
    if result.product == "stations":
        return normalize_stations(
            result.payload, result.metadata, bbox=result.bbox, maximum_rows=result.maximum_rows
        )
    if result.station is None:
        raise ValueError("AEMET observation result omits its station")
    if result.product == "recent":
        return normalize_recent(
            result.payload, result.metadata, result.station, maximum_rows=result.maximum_rows
        )
    if result.product != "daily" or result.start is None or result.end is None:
        raise ValueError("AEMET result omits its daily selection")
    return normalize_daily(
        result.payload,
        result.metadata,
        result.station,
        result.start,
        result.end,
        maximum_rows=result.maximum_rows,
    )


def _sidecars(output: Path) -> tuple[Path, Path, Path]:
    return (
        output.with_suffix(output.suffix + ".source.json"),
        output.with_suffix(output.suffix + ".metadata.json"),
        output.with_suffix(output.suffix + ".envelope.json"),
    )


def _existing(output: Path, request: dict[str, JSONValue]) -> Artifact | None:
    if output.suffix.lower() not in {".parquet", ".pq"}:
        raise ValueError("AEMET output must use a .parquet or .pq filename")
    paths = _sidecars(output)
    if any(
        path.is_symlink() for path in (output, output.with_suffix(output.suffix + ".json"), *paths)
    ):
        raise ValueError("AEMET checkpoint files must not be symlinks")
    previous = existing_artifact(output, fingerprint(request))
    if previous is None:
        if any(path.exists() for path in paths):
            raise ValueError("Incomplete AEMET source/output checkpoint; choose a new output")
        return None
    saved = json.loads(output.with_suffix(output.suffix + ".json").read_text("utf-8"))
    try:
        records = saved["provenance"]["source_artifacts"]
        for path in paths:
            record = records[path.name]
            if (
                not path.is_file()
                or path.stat().st_size != record["size_bytes"]
                or sha256_file(path) != record["sha256"]
            ):
                raise ValueError("AEMET canonical source differs from its saved checksum")
    except (KeyError, TypeError):
        raise ValueError("AEMET checkpoint omits required native source provenance") from None
    return previous


def save_dataset(result: AEMETDataset, output: Path) -> Artifact:
    """Publish a verified normalized frame and all three canonical source documents."""
    request = _request(
        result.product, result.station, result.start, result.end, result.bbox, result.maximum_rows
    )
    previous = _existing(output, request)
    if previous is not None:
        return previous
    bodies = tuple(
        _canonical(value) for value in (result.payload, result.metadata, result.envelope)
    )
    endpoints = (
        request["endpoint"],
        _link(result.envelope.get("datos")),
        _link(result.envelope.get("metadatos")),
    )
    acquisition_bodies = (bodies[2], bodies[0], bodies[1])
    if len(result.requests) != 3:
        raise ValueError("AEMET result omits an acquisition record")
    for record, endpoint, body in zip(result.requests, endpoints, acquisition_bodies, strict=True):
        if (
            record.endpoint != endpoint
            or record.parameters
            or record.sha256 != hashlib.sha256(body).hexdigest()
            or record.size_bytes != len(body)
        ):
            raise ValueError("AEMET canonical source differs from its acquisition hash")
    expected = _normalize(result)
    if not expected.equals(result.frame) or expected.attrs != result.frame.attrs:
        raise ValueError("AEMET normalized frame differs from its preserved source")
    source_artifacts = {}
    for path, body in zip(_sidecars(output), bodies, strict=True):
        atomic_bytes(path, body)
        source_artifacts[path.name] = {
            "sha256": hashlib.sha256(body).hexdigest(),
            "size_bytes": len(body),
        }
    provenance = _json(
        {
            "requests": [asdict(record) for record in result.requests],
            "metadata": expected.attrs,
            "source_artifacts": source_artifacts,
            "reference_ids": REFERENCE_IDS,
        }
    )
    return write_parquet(expected, output, request=request, provenance=provenance)


@dataclass(slots=True)
class AEMETClient:
    """Bounded authenticated queries followed by public temporary JSON downloads."""

    http: HTTPClient
    api_key: str | None = field(default=None, repr=False)
    maximum_rows: int = 100_000
    maximum_days: int = 3660

    def __post_init__(self) -> None:
        _bound(self.maximum_rows, "maximum_rows", 1_000_000)
        _bound(self.maximum_days, "maximum_days", 36_600)

    @classmethod
    def from_environment(
        cls, http: HTTPClient, *, maximum_rows: int = 100_000, maximum_days: int = 3660
    ) -> AEMETClient:
        return cls(http, os.environ.get("AEMET_API_KEY"), maximum_rows, maximum_days)

    def _acquire(
        self,
        product: Product,
        station: str | None = None,
        start: date | None = None,
        end: date | None = None,
        bbox: BBox | None = None,
    ) -> AEMETDataset:
        endpoint = _endpoint(product, station, start, end)
        _bbox(bbox)
        if not self.api_key:
            raise ValueError("Set AEMET_API_KEY to an authorized, current AEMET OpenData API key")
        envelope = self.http.get_json(
            endpoint,
            secret_headers={"api_key": self.api_key},
            use_cache=False,
            allow_legacy_charset=True,
        )
        record = object_value(envelope.value)
        if type(record.get("estado")) is not int or record["estado"] != 200:
            raise RetrievalError("AEMET API did not return estado 200; no snapshot was saved")
        data_endpoint = _link(record.get("datos"))
        metadata_endpoint = _link(record.get("metadatos"))
        responses = []
        for source_endpoint in (data_endpoint, metadata_endpoint):
            response = self.http.get_json(
                source_endpoint, use_cache=False, allow_legacy_charset=True
            )
            value = response.value
            if isinstance(value, dict) and "estado" in value:
                raise RetrievalError(
                    "AEMET temporary data or metadata expired or returned an API error"
                )
            if self.api_key.encode() in _canonical(value):
                raise RetrievalError("AEMET returned credential-bearing source content; not saved")
            responses.append(response)
        data, metadata = responses
        result = AEMETDataset(
            product,
            station,
            start,
            end,
            bbox,
            self.maximum_rows,
            pd.DataFrame(),
            data.value,
            object_value(metadata.value),
            record,
            (envelope.record, data.record, metadata.record),
        )
        return AEMETDataset(
            product,
            station,
            start,
            end,
            bbox,
            self.maximum_rows,
            _normalize(result),
            data.value,
            result.metadata,
            record,
            result.requests,
        )

    def stations(self, *, bbox: BBox | None = None) -> AEMETDataset:
        return self._acquire("stations", bbox=bbox)

    def daily(self, station: str, start: date, end: date) -> AEMETDataset:
        _dates(start, end, min(31, self.maximum_days))
        return self._acquire("daily", station, start, end)

    def recent(self, station: str) -> AEMETDataset:
        return self._acquire("recent", station)

    def retrieve_stations(self, output: Path, *, bbox: BBox | None = None) -> Artifact:
        request = _request("stations", None, None, None, bbox, self.maximum_rows)
        previous = _existing(output, request)
        return previous if previous is not None else save_dataset(self.stations(bbox=bbox), output)

    def retrieve_daily(self, station: str, start: date, end: date, output: Path) -> Artifact:
        _dates(start, end, min(31, self.maximum_days))
        request = _request("daily", station, start, end, None, self.maximum_rows)
        previous = _existing(output, request)
        return (
            previous
            if previous is not None
            else save_dataset(self.daily(station, start, end), output)
        )

    def retrieve_recent(self, station: str, output: Path) -> Artifact:
        request = _request("recent", station, None, None, None, self.maximum_rows)
        previous = _existing(output, request)
        return previous if previous is not None else save_dataset(self.recent(station), output)
