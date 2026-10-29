"""Bounded NOAA GHCNh station-year acquisition with native metadata and QC.

The current GHCNh product replaces the discontinued ISD updates. Its documented
native PSV files preserve timestamps, station identity and per-variable quality,
measurement, report and source codes. Units are already physical values in these
files; applying legacy ISD integer scaling would be incorrect.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
from collections.abc import Iterator
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import cast

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
)

NOAA_HOSTS = frozenset({"www.ncei.noaa.gov"})
_ROOT = "https://www.ncei.noaa.gov/oa/global-historical-climatology-network/hourly"
STATIONS_ENDPOINT = _ROOT + "/doc/ghcnh-station-list.csv"
_FORMAT = "GHCNh 1.1.0 station-year PSV"
# Current U-network identifiers also contain lowercase letters and underscores.
# Preserve the catalogue spelling; changing case changes the source object path.
_STATION_PATTERN = r"[A-Z]{2}[A-Z0-9][A-Za-z0-9_-]{8}"
_STATION_ID = re.compile(_STATION_PATTERN + r"\Z")
_DATE_LABEL = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|\+00:00)?"
_VARIABLES = {
    "temperature": ("temperature_c", "degC"),
    "dew_point_temperature": ("dewpoint_c", "degC"),
    "wind_speed": ("wind_speed_ms", "m/s"),
    "wind_gust": ("gust_ms", "m/s"),
    "sea_level_pressure": ("sea_level_pressure_hpa", "hPa"),
    "station_level_pressure": ("station_pressure_hpa", "hPa"),
    "wet_bulb_temperature": ("wet_bulb_temperature_c", "degC"),
    "altimeter": ("altimeter_hpa", "hPa"),
    "visibility": ("visibility_km", "km"),
}
_ATTRIBUTES = (
    "Measurement_Code",
    "Quality_Code",
    "Report_Type",
    "Source_Code",
    "Source_Station_ID",
)
REFERENCE_IDS = (
    "ascencio_vasquez_2021_thesis",
    "menne_2023_ghcnh",
    "noaa_ghcnh_documentation",
    "noaa_isd_service_transition",
)


def _bounded_integer(value: int, label: str, maximum: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
        raise ValueError(f"{label} must be an integer between 1 and {maximum}")


def _station_id(value: str) -> str:
    if not isinstance(value, str) or _STATION_ID.fullmatch(value) is None:
        raise ValueError("Use one exact 11-character GHCNh station ID from the station catalogue")
    return value


def _dates(start: date, end: date, *, one_year: bool = False) -> None:
    if type(start) is not date or type(end) is not date or start > end:
        raise ValueError("NOAA dates must be ordered inclusive date objects")
    if not 1750 <= start.year <= end.year <= 9998:
        raise ValueError("NOAA observation years must be within 1750..9998")
    if one_year and start.year != end.year:
        raise ValueError("One NOAA observation chunk must fit within a single calendar year")


def _endpoint(station_id: str, year: int) -> str:
    return f"{_ROOT}/access/by-year/{year}/psv/GHCNh_{_station_id(station_id)}_{year}.psv"


def _read_table(text: str, *, delimiter: str, maximum_rows: int) -> pd.DataFrame:
    """Validate record widths before a vectorized, compact Arrow-string parse."""
    if not text or not text.endswith(("\n", "\r")):
        raise RetrievalError("NOAA export is empty or lacks its final complete record delimiter")
    try:
        reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter, strict=True)
        header = next(reader)
        if (
            not 1 <= len(header) <= 512
            or len(set(header)) != len(header)
            or any(not key for key in header)
        ):
            raise RetrievalError("NOAA export has empty, duplicate or excessive columns")
        rows = 0
        for row in reader:
            if not row:
                continue
            rows += 1
            if rows > maximum_rows:
                raise RetrievalError("NOAA export exceeds its configured row limit")
            if len(row) != len(header):
                raise RetrievalError("NOAA export has a truncated or inconsistent record width")
        return pd.read_csv(
            io.StringIO(text),
            sep=delimiter,
            dtype="string[pyarrow]",
            keep_default_na=False,
            na_filter=False,
            on_bad_lines="error",
        )
    except (csv.Error, StopIteration, pd.errors.ParserError, pd.errors.EmptyDataError) as error:
        raise RetrievalError("NOAA export is not a valid complete delimited table") from error


def _number(column: pd.Series, label: str, *, missing: tuple[str, ...] = ("",)) -> pd.Series:
    values = column.str.strip()
    values = values.mask(values.isin(missing))
    try:
        numbers = pd.to_numeric(values, errors="raise").astype("float64")
    except (ValueError, TypeError):
        raise RetrievalError(f"NOAA {label} contains an unexpected nonnumeric value") from None
    if np.isinf(numbers.to_numpy()).any():
        raise RetrievalError(f"NOAA {label} contains an infinite value")
    # Literal NaN/NA strings are not documented native missing codes.
    if (numbers.isna() & values.notna()).any():
        raise RetrievalError(f"NOAA {label} contains an unsupported missing-value code")
    return numbers


def _coordinates(frame: pd.DataFrame, *, catalogue: bool = False) -> None:
    frame["latitude"] = _number(frame["LATITUDE"], "latitude")
    frame["longitude"] = _number(frame["LONGITUDE"], "longitude")
    invalid = (~frame["latitude"].between(-90, 90) & frame["latitude"].notna()) | (
        ~frame["longitude"].between(-180, 180) & frame["longitude"].notna()
    )
    if invalid.any() and not catalogue:
        raise RetrievalError("NOAA station coordinates are outside geographic bounds")
    if catalogue:
        # Preserve malformed provider coordinates without swapping latitude/longitude.
        frame["coordinates_valid"] = frame["latitude"].between(-90, 90) & frame[
            "longitude"
        ].between(-180, 180)
        frame.loc[invalid, ["latitude", "longitude"]] = np.nan
    frame["elevation_m"] = _number(frame["ELEVATION"], "elevation", missing=("", "-999.9"))


def _bbox(value: tuple[float, float, float, float] | None) -> None:
    if value is None:
        return
    if len(value) != 4 or not all(math.isfinite(number) for number in value):
        raise ValueError("bbox requires finite WEST SOUTH EAST NORTH coordinates")
    west, south, east, north = value
    if not -180 <= west <= east <= 180 or not -90 <= south <= north <= 90:
        raise ValueError("bbox must be ordered WEST SOUTH EAST NORTH; split antimeridian boxes")


def normalize_stations(
    text: str,
    *,
    country_code: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    maximum_stations: int = 100_000,
) -> pd.DataFrame:
    """Filter the official catalogue without inferring availability or nearest sites.

    ``country_code`` uses the catalogue's ISO_CODE column. The distinct FIPS
    prefix in GHCN station IDs is retained as ``country_fips`` (CL vs CI for Chile).
    The station list does not establish period or variable coverage.
    """
    _bounded_integer(maximum_stations, "maximum_stations", 1_000_000)
    _bbox(bbox)
    if country_code is not None and not re.fullmatch(r"[A-Z]{2}", country_code):
        raise ValueError("country_code must be one uppercase ISO_CODE from the NOAA catalogue")
    frame = _read_table(text, delimiter=",", maximum_rows=maximum_stations)
    required = {"GHCN_ID", "LATITUDE", "LONGITUDE", "ELEVATION", "NAME", "ISO_CODE"}
    if not required.issubset(frame.columns) or frame.empty:
        raise RetrievalError("NOAA station catalogue omits its documented identity/location fields")
    if not frame["GHCN_ID"].str.fullmatch(_STATION_PATTERN).all():
        raise RetrievalError("NOAA station catalogue contains an invalid GHCN identifier")
    frame = frame.drop_duplicates()
    if frame["GHCN_ID"].duplicated().any():
        raise RetrievalError("NOAA station catalogue has conflicting records for one station ID")
    frame["station_id"] = frame["GHCN_ID"]
    frame["station_name"] = frame["NAME"]
    frame["country_code"] = frame["ISO_CODE"]
    frame["country_fips"] = frame["GHCN_ID"].str[:2]
    _coordinates(frame, catalogue=True)
    source_rows = len(frame)
    invalid_coordinates = int((~frame["coordinates_valid"]).sum())
    if country_code is not None:
        frame = frame.loc[frame["country_code"].eq(country_code)]
    if bbox is not None:
        west, south, east, north = bbox
        frame = frame.loc[
            frame["latitude"].between(south, north) & frame["longitude"].between(west, east)
        ]
    frame = frame.sort_values("station_id").reset_index(drop=True)
    frame.attrs.update(
        source="NOAA NCEI GHCNh station catalogue",
        country_code_system="ISO_CODE as supplied; GHCN FIPS prefix retained separately",
        country_code_filter=country_code,
        bbox_west_south_east_north=bbox,
        source_station_rows=source_rows,
        source_rows_without_valid_coordinates=invalid_coordinates,
        availability_inferred=False,
        nearest_station_selected=False,
        reference_ids=REFERENCE_IDS,
    )
    return frame


def normalize_observations(
    text: str,
    station_id: str,
    start: date,
    end: date,
    *,
    maximum_rows: int = 600_000,
) -> pd.DataFrame:
    """Keep native UTC observations and raw per-variable provenance/QC columns.

    Source values, including flagged observations and reported zeros, are retained.
    Blank values become null only in the added numeric columns. No quality flag
    is treated as a universal pass: meanings depend on the variable and source.
    """
    _station_id(station_id)
    _dates(start, end, one_year=True)
    _bounded_integer(maximum_rows, "maximum_rows", 1_000_000)
    raw = _read_table(text, delimiter="|", maximum_rows=maximum_rows)
    required = {
        "STATION",
        "Station_name",
        "DATE",
        "Year",
        "Month",
        "Day",
        "Hour",
        "Minute",
        "LATITUDE",
        "LONGITUDE",
        "ELEVATION",
        *(_VARIABLES.keys()),
        *(f"{variable}_{attribute}" for variable in _VARIABLES for attribute in _ATTRIBUTES),
    }
    if not required.issubset(raw.columns):
        raise RetrievalError(
            "NOAA file omits the current GHCNh station-year identity/variable/QC schema"
        )
    if not raw["STATION"].eq(station_id).all():
        raise RetrievalError("NOAA file returned a station different from the explicit request")
    if not raw["DATE"].str.fullmatch(_DATE_LABEL).all():
        raise RetrievalError("NOAA DATE must contain native UTC ISO timestamps")
    try:
        timestamps = pd.to_datetime(raw["DATE"], format="ISO8601", utc=True, errors="raise")
    except (ValueError, TypeError):
        raise RetrievalError("NOAA export has an invalid native observation timestamp") from None
    if not timestamps.dt.year.eq(start.year).all():
        raise RetrievalError("NOAA station-year export contains records from a different year")
    for name, values in (
        ("Year", timestamps.dt.year),
        ("Month", timestamps.dt.month),
        ("Day", timestamps.dt.day),
        ("Hour", timestamps.dt.hour),
        ("Minute", timestamps.dt.minute),
    ):
        if not _number(raw[name], name).eq(values).all():
            raise RetrievalError("NOAA DATE disagrees with its separate calendar fields")
    first = pd.Timestamp(start, tz="UTC")
    stop = pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)
    selected = timestamps.ge(first) & timestamps.lt(stop)
    frame = raw.loc[selected].copy()
    frame["station_id"] = frame["STATION"]
    frame["timestamp"] = timestamps.loc[selected]
    identity = [
        "STATION",
        "DATE",
        *(
            column
            for column in raw.columns
            if column.endswith(("_Report_Type", "_Source_Code", "_Source_Station_ID"))
        ),
    ]
    selected_count = len(frame)
    frame = frame.drop_duplicates()
    equal_duplicates = selected_count - len(frame)
    if frame.duplicated(identity).any():
        raise RetrievalError(
            "Conflicting NOAA observations share the same station/time/report/source identity"
        )
    for variable, (column, _) in _VARIABLES.items():
        frame[column] = _number(frame[variable], variable)
    _coordinates(frame)
    frame = frame.sort_values(["timestamp", "station_id"], kind="stable").reset_index(drop=True)
    frame.attrs.update(
        source="NOAA NCEI GHCNh",
        native_format=_FORMAT,
        native_columns=list(raw.columns),
        native_column_count=len(raw.columns),
        native_rows=len(raw),
        source_year=start.year,
        source_first_timestamp_utc=timestamps.min().isoformat() if len(timestamps) else None,
        source_last_timestamp_utc=timestamps.max().isoformat() if len(timestamps) else None,
        requested_start=start.isoformat(),
        requested_end=end.isoformat(),
        source_file_temporal_scope=(
            "whole station-year file fetched; inclusive requested dates selected locally"
        ),
        duplicate_equal_rows_removed=equal_duplicates,
        observation_identity_fields=identity,
        timestamp_convention="native UTC observation time; subhourly and synoptic labels preserved",
        hourly_resampling_applied=False,
        hourly_coverage_claimed=False,
        station_observations=True,
        quality_filter_applied=False,
        sensor_quality_confirmed=False,
        spatial_representativeness_confirmed=False,
        quality_rule="raw variable/source-specific QC codes retained; no universal pass inferred",
        missing_rule=(
            "blank native numeric fields become null; no interpolation or modeled replacement"
        ),
        gust_statistic="reported peak short-duration wind; not relabeled as an hourly maximum",
        units={column: unit for column, unit in _VARIABLES.values()},
        reference_ids=REFERENCE_IDS,
    )
    return frame


@dataclass(frozen=True, slots=True)
class NOAAStations:
    frame: pd.DataFrame
    request: RequestRecord


@dataclass(frozen=True, slots=True)
class NOAAObservations:
    station_id: str
    start: date
    end: date
    frame: pd.DataFrame
    requests: tuple[RequestRecord, ...]
    source_text: str


def _request(station_id: str, start: date, end: date) -> dict[str, JSONValue]:
    _station_id(station_id)
    _dates(start, end, one_year=True)
    return {
        "source": "NOAA NCEI GHCNh",
        "native_format": _FORMAT,
        "station_id": station_id,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "source_year": start.year,
        "endpoint": _endpoint(station_id, start.year),
        "quality_filter_applied": False,
        "hourly_resampling_applied": False,
    }


def _existing(output: Path, request: dict[str, JSONValue]) -> Artifact | None:
    if output.suffix.lower() not in {".parquet", ".pq"}:
        raise ValueError("NOAA observation output must use a .parquet or .pq filename")
    source_path = output.with_suffix(".source.psv")
    if (
        output.is_symlink()
        or source_path.is_symlink()
        or output.with_suffix(output.suffix + ".json").is_symlink()
    ):
        raise ValueError("NOAA output checkpoints must not be symlinks")
    previous = existing_artifact(output, fingerprint(request))
    if previous is None:
        if source_path.exists():
            raise ValueError("Incomplete NOAA source/output checkpoint; inspect before retrying")
        return None
    saved = json.loads(output.with_suffix(output.suffix + ".json").read_text())
    source = saved.get("provenance", {}).get("native_source", {})
    if (
        source.get("filename") != source_path.name
        or not source_path.is_file()
        or source.get("size_bytes") != source_path.stat().st_size
        or source.get("sha256") != sha256_file(source_path)
    ):
        raise ValueError(
            "NOAA preserved source export is missing or differs from its recorded checksum"
        )
    return previous


def save_observations(result: NOAAObservations, output: Path) -> Artifact:
    """Persist selected observations with the complete native source and its hash."""
    request = _request(result.station_id, result.start, result.end)
    previous = _existing(output, request)
    if previous is not None:
        return previous
    data = result.source_text.encode("utf-8")
    source_hash = hashlib.sha256(data).hexdigest()
    if (
        len(result.requests) != 1
        or result.requests[0].endpoint != request["endpoint"]
        or result.requests[0].sha256 != source_hash
        or result.requests[0].size_bytes != len(data)
    ):
        raise ValueError("NOAA source text does not match its recorded native acquisition")
    expected = normalize_observations(
        result.source_text, result.station_id, result.start, result.end, maximum_rows=1_000_000
    )
    if not result.frame.equals(expected) or result.frame.attrs != expected.attrs:
        raise ValueError("NOAA normalized observations differ from the preserved native source")
    source_path = output.with_suffix(".source.psv")
    atomic_bytes(source_path, data)
    provenance = cast(
        dict[str, JSONValue],
        json.loads(
            json.dumps(
                {
                    "requests": [asdict(record) for record in result.requests],
                    "metadata": result.frame.attrs,
                    "native_source": {
                        "filename": source_path.name,
                        "sha256": source_hash,
                        "size_bytes": len(data),
                    },
                },
                allow_nan=False,
            )
        ),
    )
    return write_parquet(result.frame, output, request=request, provenance=provenance)


@dataclass(slots=True)
class NOAAClient:
    """Explicit station retrieval using current NOAA GHCNh public HTTPS exports."""

    http: HTTPClient
    maximum_rows: int = 600_000
    maximum_stations: int = 100_000
    maximum_years: int = 100

    def __post_init__(self) -> None:
        _bounded_integer(self.maximum_rows, "maximum_rows", 1_000_000)
        _bounded_integer(self.maximum_stations, "maximum_stations", 1_000_000)
        _bounded_integer(self.maximum_years, "maximum_years", 1000)

    def stations(
        self,
        *,
        country_code: str | None = None,
        bbox: tuple[float, float, float, float] | None = None,
    ) -> NOAAStations:
        _bbox(bbox)
        if country_code is not None and not re.fullmatch(r"[A-Z]{2}", country_code):
            raise ValueError("country_code must be one uppercase ISO_CODE from the NOAA catalogue")
        response = self.http.get_text(STATIONS_ENDPOINT, use_cache=False)
        frame = normalize_stations(
            response.value,
            country_code=country_code,
            bbox=bbox,
            maximum_stations=self.maximum_stations,
        )
        return NOAAStations(frame, response.record)

    def observations(self, station_id: str, start: date, end: date) -> NOAAObservations:
        _dates(start, end, one_year=True)
        response = self.http.get_text(_endpoint(station_id, start.year), use_cache=False)
        frame = normalize_observations(
            response.value, station_id, start, end, maximum_rows=self.maximum_rows
        )
        return NOAAObservations(station_id, start, end, frame, (response.record,), response.value)

    def iter_observations(
        self, station_id: str, start: date, end: date
    ) -> Iterator[NOAAObservations]:
        """Yield one station-year at a time; no all-years dataset is collected."""
        _station_id(station_id)
        _dates(start, end)
        if end.year - start.year + 1 > self.maximum_years:
            raise ValueError("NOAA date range exceeds maximum_years")
        for year in range(start.year, end.year + 1):
            first = max(start, date(year, 1, 1))
            last = min(end, date(year, 12, 31))
            yield self.observations(station_id, first, last)

    def retrieve(self, station_id: str, start: date, end: date, output: Path) -> Artifact:
        """Reuse only verified Parquet/source pairs before any provider access."""
        request = _request(station_id, start, end)
        previous = _existing(output, request)
        if previous is not None:
            return previous
        return save_observations(self.observations(station_id, start, end), output)
