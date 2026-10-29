"""NOAA SURFRAD daily radiation and meteorology with native interval-end labels.

The seven primary SURFRAD stations report three-minute averages before 2009 and
one-minute averages thereafter. Acquisition retains the original daily text,
header, measurement fields and quality codes; it performs no quality masking,
hourly aggregation, or automatic deduplication against the BSRN archive.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Iterator
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from html.parser import HTMLParser
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

SURFRAD_HOSTS = frozenset({"gml.noaa.gov"})
ARCHIVE_ENDPOINT = "https://gml.noaa.gov/aftp/data/radiation/surfrad"
STATIONS_ENDPOINT = "https://gml.noaa.gov/grad/surfrad/sitepage.html"
DOCUMENTATION_ENDPOINT = ARCHIVE_ENDPOINT + "/bon/README_SURFRAD.txt"
STATION_IDS = ("bon", "tbl", "dra", "fpk", "gwn", "psu", "sxf")
REFERENCE_IDS = (
    "ascencio_vasquez_2021_thesis",
    "augustine_2000_surfrad",
    "augustine_2005_surfrad",
    "noaa_surfrad_documentation",
    "noaa_surfrad_stations",
    "noaa_surfrad_overview",
    "noaa_surfrad_archive",
)
_STATIONS = {
    "bon": ("BND", "Bondville"),
    "tbl": ("TBL", "Table Mountain"),
    "dra": ("DRA", "Desert Rock"),
    "fpk": ("FPK", "Fort Peck"),
    "gwn": ("GWN", "Goodwin Creek"),
    "psu": ("PSU", "Penn State"),
    "sxf": ("SXF", "Sioux Falls"),
}
_SITE_CODES = {site: station for station, (site, _) in _STATIONS.items()}
_NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
_HEADER = re.compile(rf"\s*({_NUMBER})\s+({_NUMBER})\s+({_NUMBER})\s+m\s+version\s+(\d+)\s*")
# Order and units are defined by NOAA's README_SURFRAD; UVB alone is mW/m2.
_MEASUREMENTS = (
    ("dw_solar", "qc_dwsolar", "ghi_wm2", "W/m2"),
    ("uw_solar", "qc_uwsolar", "upwelling_shortwave_wm2", "W/m2"),
    ("direct_n", "qc_direct_n", "dni_wm2", "W/m2"),
    ("diffuse", "qc_diffuse", "dhi_wm2", "W/m2"),
    ("dw_ir", "qc_dwir", "downwelling_longwave_wm2", "W/m2"),
    ("dw_casetemp", "qc_dwcasetemp", "downwelling_case_temperature_k", "K"),
    ("dw_dometemp", "qc_dwdometemp", "downwelling_dome_temperature_k", "K"),
    ("uw_ir", "qc_uwir", "upwelling_longwave_wm2", "W/m2"),
    ("uw_casetemp", "qc_uwcasetemp", "upwelling_case_temperature_k", "K"),
    ("uw_dometemp", "qc_uwdometemp", "upwelling_dome_temperature_k", "K"),
    ("uvb", "qc_uvb", "uvb_mwm2", "mW/m2"),
    ("par", "qc_par", "par_wm2", "W/m2"),
    ("netsolar", "qc_netsolar", "net_shortwave_wm2", "W/m2"),
    ("netir", "qc_netir", "net_longwave_wm2", "W/m2"),
    ("totalnet", "qc_totalnet", "net_radiation_wm2", "W/m2"),
    ("temp", "qc_temp", "temperature_10m_c", "degC"),
    ("rh", "qc_rh", "relative_humidity_percent", "%"),
    ("windspd", "qc_windspd", "wind_speed_ms", "m/s"),
    ("winddir", "qc_winddir", "wind_direction_deg", "degree"),
    ("pressure", "qc_pressure", "station_pressure_hpa", "hPa"),
)
NATIVE_COLUMNS = (
    "year",
    "jday",
    "month",
    "day",
    "hour",
    "min",
    "dt",
    "zen",
    *(name for value, quality, _, _ in _MEASUREMENTS for name in (value, quality)),
)
_CATALOGUE_COLUMNS = (
    "Code",
    "Name",
    "Latitude",
    "Longitude",
    "Elevation",
    "Time Zone",
    "Installed",
)


def _bounded_integer(value: int, label: str, maximum: int) -> None:
    if type(value) is not int or not 1 <= value <= maximum:
        raise ValueError(f"{label} must be an integer from 1 through {maximum}")


def _station_id(value: str) -> str:
    if not isinstance(value, str) or value not in STATION_IDS:
        raise ValueError("Use a SURFRAD archive station ID: " + ", ".join(STATION_IDS))
    return value


def _day(value: date) -> date:
    if type(value) is not date or not 1994 <= value.year <= 9998:
        raise ValueError("SURFRAD day must be a date with a year from 1994 through 9998")
    return value


def _endpoint(station_id: str, day: date) -> str:
    station_id, day = _station_id(station_id), _day(day)
    return (
        f"{ARCHIVE_ENDPOINT}/{station_id}/{day.year}/"
        f"{station_id}{day.year % 100:02d}{day.timetuple().tm_yday:03d}.dat"
    )


def _json_object(value: object) -> dict[str, JSONValue]:
    return cast(dict[str, JSONValue], json.loads(json.dumps(value, allow_nan=False)))


class _Tables(HTMLParser):
    """Read table text only; no external resources or active HTML are evaluated."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self._depth = 0
        self._table: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self._depth += 1
            if self._depth == 1:
                self._table = []
        elif self._depth == 1 and tag == "tr":
            self._row = []
        elif self._depth == 1 and tag in {"td", "th"} and self._row is not None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._cell is not None and self._row is not None:
            value = " ".join("".join(self._cell).split())
            if len(value) > 8192:
                raise RetrievalError("SURFRAD station catalogue contains an excessive table cell")
            self._row.append(value)
            self._cell = None
        elif tag == "tr" and self._row is not None:
            self._table.append(self._row)
            self._row = None
            if len(self._table) > 128:
                raise RetrievalError("SURFRAD station catalogue exceeds its table row bound")
        elif tag == "table" and self._depth:
            self._depth -= 1
            if self._depth == 0:
                self.tables.append(self._table)
                self._row = None
                self._cell = None
                if len(self.tables) > 32:
                    raise RetrievalError("SURFRAD station catalogue contains too many tables")


def _coordinate(value: str, latitude: bool) -> float:
    match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*°\s*([NSEW])", value)
    if match is None or match[2] not in ("NS" if latitude else "EW"):
        raise RetrievalError("SURFRAD station catalogue has an unsupported coordinate")
    number = float(match[1]) * (-1 if match[2] in "SW" else 1)
    if abs(number) > (90 if latitude else 180):
        raise RetrievalError("SURFRAD station catalogue coordinate is outside geographic bounds")
    return number


def normalize_stations(text: str) -> pd.DataFrame:
    """Read the official seven-station table, preserving BND versus bon identity.

    The linked ARM Southern Great Plains station is explicitly outside this
    provider. Catalogue positions are current metadata and do not replace the
    coordinates/elevation in a historical observation file's own header.
    """
    parser = _Tables()
    parser.feed(text)
    parser.close()
    tables = [table for table in parser.tables if table and tuple(table[0]) == _CATALOGUE_COLUMNS]
    if len(tables) != 1:
        raise RetrievalError("SURFRAD catalogue omits its unique documented station table")
    rows: list[dict[str, object]] = []
    for row in tables[0][1:]:
        if len(row) == 1:  # The official table ends with a station-coordinate footnote.
            continue
        if len(row) != len(_CATALOGUE_COLUMNS):
            raise RetrievalError("SURFRAD station catalogue has an unexpected row width")
        site_code = row[0].replace("*", "").strip()
        if site_code == "SGP":
            continue
        if site_code not in _SITE_CODES:
            raise RetrievalError("SURFRAD catalogue has an unsupported new station code")
        elevation = re.fullmatch(r"(-?\d+(?:\.\d+)?)\s+m", row[4])
        if elevation is None or not row[1] or not row[6]:
            raise RetrievalError("SURFRAD catalogue lacks station name, elevation or installation")
        station_id = _SITE_CODES[site_code]
        rows.append(
            {
                "station_id": station_id,
                "site_code": site_code,
                "station_name": row[1],
                "latitude": _coordinate(row[2], True),
                "longitude": _coordinate(row[3], False),
                "elevation_m": float(elevation[1]),
                "country_code": "US",
                "installed": row[6],
                "archive_directory": f"{ARCHIVE_ENDPOINT}/{station_id}/",
                "possible_bsrn_overlap": True,
                **{
                    f"source:{key}": value
                    for key, value in zip(_CATALOGUE_COLUMNS, row, strict=True)
                },
            }
        )
    frame = pd.DataFrame(rows)
    if (
        len(frame) != len(STATION_IDS)
        or frame["station_id"].duplicated().any()
        or set(frame["station_id"]) != set(STATION_IDS)
    ):
        raise RetrievalError("SURFRAD catalogue must contain each of the seven supported stations")
    frame = frame.sort_values("station_id").reset_index(drop=True)
    frame.attrs.update(
        source="NOAA GML SURFRAD station catalogue",
        endpoint=STATIONS_ENDPOINT,
        archive_station_codes=list(STATION_IDS),
        catalogue_positions_are_observation_positions=False,
        availability_inferred=False,
        possible_network_overlap=(
            "BSRN; compare station, time, variables and vintage before combining"
        ),
        cross_provider_deduplication_applied=False,
        reference_ids=list(REFERENCE_IDS),
    )
    return frame


def _numeric(raw: pd.Series, label: str) -> pd.Series:
    if not raw.str.fullmatch(_NUMBER).all():
        raise RetrievalError(f"SURFRAD {label} contains an unsupported numeric value")
    try:
        values = pd.to_numeric(raw, errors="raise").astype("float64")
    except (ValueError, OverflowError):
        raise RetrievalError(
            f"SURFRAD {label} contains a nonfinite or out-of-range value"
        ) from None
    if not np.isfinite(values.to_numpy()).all():
        raise RetrievalError(f"SURFRAD {label} contains a nonfinite value")
    return values


def normalize_day(
    text: str, station_id: str, day: date, *, maximum_rows: int = 1440
) -> pd.DataFrame:
    """Keep the native UTC averaging-period end and all 48 original text fields."""
    station_id, day = _station_id(station_id), _day(day)
    _bounded_integer(maximum_rows, "maximum_rows", 1440)
    if not text or not text.endswith(("\n", "\r")):
        raise RetrievalError("SURFRAD daily export is empty or has an incomplete last record")
    lines = text.removeprefix("\ufeff").splitlines()
    if len(lines) < 3 or lines[0].strip() != _STATIONS[station_id][1]:
        raise RetrievalError("SURFRAD daily header does not identify the requested station")
    header = _HEADER.fullmatch(lines[1])
    if header is None or header[4] != "1":
        raise RetrievalError("SURFRAD station header has an unsupported format or file version")
    latitude, longitude, elevation = (float(header[i]) for i in (1, 2, 3))
    if (
        not all(math.isfinite(value) for value in (latitude, longitude, elevation))
        or not -90 <= latitude <= 90
        or not -180 <= longitude <= 180
    ):
        raise RetrievalError("SURFRAD source header has invalid station coordinates")
    duration = 180 if day < date(2009, 1, 1) else 60
    nominal_rows = 86400 // duration
    rows: list[list[str]] = []
    for line in lines[2:]:
        if not line.strip():
            continue
        fields = line.split()
        if len(fields) != len(NATIVE_COLUMNS):
            raise RetrievalError("SURFRAD daily export has a truncated or unsupported record width")
        if len(rows) >= min(maximum_rows, nominal_rows):
            raise RetrievalError("SURFRAD daily export exceeds the configured or native row bound")
        rows.append(fields)
    if not rows:
        raise RetrievalError("SURFRAD daily export contains no observations")
    raw = pd.DataFrame(rows, columns=NATIVE_COLUMNS, dtype="string[pyarrow]")
    calendar: dict[str, pd.Series] = {}
    for key in ("year", "jday", "month", "day", "hour", "min"):
        if not raw[key].str.fullmatch(r"\d{1,4}").all():
            raise RetrievalError("SURFRAD date/time fields must be unsigned integers")
        calendar[key] = raw[key].astype("int64")
    if (
        not calendar["year"].eq(day.year).all()
        or not calendar["month"].eq(day.month).all()
        or not calendar["day"].eq(day.day).all()
        or not calendar["jday"].eq(day.timetuple().tm_yday).all()
        or not calendar["hour"].between(0, 23).all()
        or not calendar["min"].between(0, 59).all()
    ):
        raise RetrievalError("SURFRAD calendar fields disagree with the requested UTC day")
    try:
        times = pd.to_datetime(
            pd.DataFrame(
                {key: calendar[key] for key in ("year", "month", "day", "hour")}
                | {"minute": calendar["min"]}
            ),
            utc=True,
            errors="raise",
        )
    except ValueError:
        raise RetrievalError("SURFRAD source has an unsupported UTC timestamp") from None
    if times.duplicated().any() or not times.is_monotonic_increasing:
        raise RetrievalError("SURFRAD interval-end timestamps must be unique and ordered")
    decimal_time = _numeric(raw["dt"], "decimal UTC time")
    if not np.allclose(
        decimal_time.to_numpy(),
        (calendar["hour"] + calendar["min"] / 60).to_numpy(),
        atol=0.00051,
        rtol=0,
    ):
        raise RetrievalError("SURFRAD decimal time disagrees with hour/minute labels")
    zenith = _numeric(raw["zen"], "solar zenith").mask(lambda values: values.eq(-9999.9))
    if not (zenith.between(0, 180) | zenith.isna()).all():
        raise RetrievalError("SURFRAD solar zenith is outside its documented angular range")
    data: dict[str, object] = {
        "station_id": station_id,
        "site_code": _STATIONS[station_id][0],
        "timestamp": times,
        "interval_end": times,
        "interval_start": times - pd.Timedelta(seconds=duration),
        "duration_seconds": duration,
        "latitude": latitude,
        "longitude": longitude,
        "elevation_m": elevation,
        "solar_zenith_deg": zenith,
    }
    units = {"solar_zenith_deg": "degree", "duration_seconds": "s"}
    quality_columns: dict[str, str] = {}
    missing_flag_mismatches = 0
    for source, quality, target, unit in _MEASUREMENTS:
        values = _numeric(raw[source], source)
        if not raw[quality].str.fullmatch(r"\d").all():
            raise RetrievalError(f"SURFRAD {quality} must be a native nonnegative one-digit flag")
        flags = raw[quality].astype("int8")
        missing = values.eq(-9999.9)
        missing_flag_mismatches += int((missing & flags.ne(1)).sum())
        data[target] = values.mask(missing)
        data[target + "_qc"] = flags
        units[target] = unit
        quality_columns[target] = target + "_qc"
    data.update({f"source:{column}": raw[column] for column in NATIVE_COLUMNS})
    frame = pd.DataFrame(data)
    frame.attrs.update(
        source="NOAA GML SURFRAD daily observations",
        schema_version=1,
        station_id=station_id,
        site_code=_STATIONS[station_id][0],
        utc_day=day.isoformat(),
        source_header={
            "station_name": lines[0].strip(),
            "latitude": latitude,
            "longitude": longitude,
            "elevation_m": elevation,
            "version": 1,
        },
        timestamp_convention=(
            "Original UTC averaging-period end; midnight belongs to the ending day"
        ),
        averaging_period_seconds=duration,
        nominal_records_per_utc_day=nominal_rows,
        native_rows=len(frame),
        unreported_nominal_records=nominal_rows - len(frame),
        source_decimal_time_tolerance_hours=0.00051,
        quality_columns=quality_columns,
        quality_filter_applied=False,
        missing_value_sentinel=-9999.9,
        missing_values_without_flag_one=missing_flag_mismatches,
        hourly_resampling_applied=False,
        gap_filling_applied=False,
        units=units,
        possible_network_overlap=(
            "BSRN; compare station, time, variables and vintage before combining"
        ),
        cross_provider_deduplication_applied=False,
        source_product="GML daily processed text; not realtime, QCRAD or NCEI NetCDF",
        license="CC0-1.0; retain NOAA attribution and dataset subset/access date",
        documentation_url=DOCUMENTATION_ENDPOINT,
        reference_ids=list(REFERENCE_IDS),
    )
    return frame


@dataclass(frozen=True, slots=True)
class SURFRADStations:
    frame: pd.DataFrame
    request: RequestRecord
    raw_text: str


@dataclass(frozen=True, slots=True)
class SURFRADDay:
    station_id: str
    day: date
    maximum_rows: int
    frame: pd.DataFrame
    request: RequestRecord
    raw_text: str


def _stations_request() -> dict[str, JSONValue]:
    return {
        "source": "NOAA GML SURFRAD stations",
        "schema_version": 1,
        "endpoint": STATIONS_ENDPOINT,
    }


def _day_request(station_id: str, day: date, maximum_rows: int) -> dict[str, JSONValue]:
    _bounded_integer(maximum_rows, "maximum_rows", 1440)
    return {
        "source": "NOAA GML SURFRAD daily observations",
        "schema_version": 1,
        "station_id": _station_id(station_id),
        "utc_day": _day(day).isoformat(),
        "endpoint": _endpoint(station_id, day),
        "maximum_rows": maximum_rows,
        "timestamp_convention": "native UTC interval end",
    }


def _source_path(output: Path, catalogue: bool) -> Path:
    return output.with_suffix(".source.html" if catalogue else ".source.dat")


def _existing(output: Path, request: dict[str, JSONValue], *, catalogue: bool) -> Artifact | None:
    source = _source_path(output, catalogue)
    manifest = output.with_suffix(output.suffix + ".json")
    if any(path.is_symlink() for path in (output, source, manifest)):
        raise ValueError("SURFRAD output, native source and manifest must not be symlinks")
    previous = existing_artifact(output, fingerprint(request))
    if previous is None:
        if source.exists():
            raise ValueError("Incomplete SURFRAD native source; inspect it or choose a new output")
        return None
    try:
        native = json.loads(manifest.read_text("utf-8"))["provenance"]["native_source"]
        if (
            native["filename"] != source.name
            or not source.is_file()
            or native["size_bytes"] != source.stat().st_size
            or native["sha256"] != sha256_file(source)
        ):
            raise ValueError("SURFRAD native source differs from its saved size or checksum")
    except (KeyError, TypeError):
        raise ValueError("SURFRAD manifest omits required native source provenance") from None
    return previous


def _save(
    frame: pd.DataFrame,
    expected: pd.DataFrame,
    raw_text: str,
    record: RequestRecord,
    output: Path,
    request: dict[str, JSONValue],
    *,
    catalogue: bool,
) -> Artifact:
    source = raw_text.encode("utf-8")
    digest = hashlib.sha256(source).hexdigest()
    if (
        record.endpoint != request["endpoint"]
        or record.parameters
        or record.size_bytes != len(source)
        or record.sha256 != digest
    ):
        raise ValueError("SURFRAD native text differs from its recorded source acquisition")
    if not frame.equals(expected) or frame.attrs != expected.attrs:
        raise ValueError("SURFRAD normalized frame differs from its native source or metadata")
    path = _source_path(output, catalogue)
    atomic_bytes(path, source)
    return write_parquet(
        expected,
        output,
        request=request,
        provenance=_json_object(
            {
                "request": asdict(record),
                "metadata": expected.attrs,
                "native_source": {
                    "filename": path.name,
                    "size_bytes": len(source),
                    "sha256": digest,
                },
                "reference_ids": list(REFERENCE_IDS),
            }
        ),
    )


def save_stations(result: SURFRADStations, output: Path) -> Artifact:
    """Save the seven-station catalogue and exact public HTML snapshot."""
    request = _stations_request()
    if previous := _existing(output, request, catalogue=True):
        return previous
    return _save(
        result.frame,
        normalize_stations(result.raw_text),
        result.raw_text,
        result.request,
        output,
        request,
        catalogue=True,
    )


def save_day(result: SURFRADDay, output: Path) -> Artifact:
    """Save native interval observations and their exact daily text export."""
    request = _day_request(result.station_id, result.day, result.maximum_rows)
    if previous := _existing(output, request, catalogue=False):
        return previous
    return _save(
        result.frame,
        normalize_day(
            result.raw_text, result.station_id, result.day, maximum_rows=result.maximum_rows
        ),
        result.raw_text,
        result.request,
        output,
        request,
        catalogue=False,
    )


@dataclass(slots=True)
class SURFRADClient:
    """Bounded acquisition of the primary seven-station SURFRAD daily archive."""

    http: HTTPClient
    maximum_rows: int = 1440
    maximum_days: int = 366

    def __post_init__(self) -> None:
        _bounded_integer(self.maximum_rows, "maximum_rows", 1440)
        _bounded_integer(self.maximum_days, "maximum_days", 36600)

    def stations(self) -> SURFRADStations:
        response = self.http.get_text(STATIONS_ENDPOINT, use_cache=False)
        return SURFRADStations(normalize_stations(response.value), response.record, response.value)

    def retrieve_stations(self, output: Path) -> Artifact:
        if previous := _existing(output, _stations_request(), catalogue=True):
            return previous
        return save_stations(self.stations(), output)

    def day(self, station_id: str, day: date) -> SURFRADDay:
        response = self.http.get_text(_endpoint(station_id, day), use_cache=False)
        frame = normalize_day(response.value, station_id, day, maximum_rows=self.maximum_rows)
        return SURFRADDay(
            station_id, day, self.maximum_rows, frame, response.record, response.value
        )

    def iter_days(self, station_id: str, start: date, end: date) -> Iterator[SURFRADDay]:
        """Yield daily partitions; unavailable days fail explicitly instead of being skipped."""
        _station_id(station_id)
        _day(start)
        _day(end)
        if start > end or (end - start).days + 1 > self.maximum_days:
            raise ValueError("SURFRAD dates must be ordered and fit within maximum_days")
        for offset in range((end - start).days + 1):
            yield self.day(station_id, start + timedelta(days=offset))

    def retrieve(self, station_id: str, day: date, output: Path) -> Artifact:
        """Verify completed output and native sidecar before any network access."""
        request = _day_request(station_id, day, self.maximum_rows)
        if previous := _existing(output, request, catalogue=False):
            return previous
        return save_day(self.day(station_id, day), output)
