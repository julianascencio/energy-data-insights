"""Bounded DWD CDC hourly solar archives with native units, times and metadata.

MESS_DATUM is retained at its published UTC minute, and MESS_DATUM_WOZ is
retained separately as local true solar time. Hourly energy totals remain in
J/cm²: the adapter does not infer interval boundaries or round times to an
hourly UTC grid. Station history and instrument metadata remain in the ZIP.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import stat
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path, PurePosixPath
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

DWD_HOSTS = frozenset({"opendata.dwd.de"})
_ROOT = "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/solar"
STATIONS_ENDPOINT = _ROOT + "/ST_Stundenwerte_Beschreibung_Stationen.txt"
REFERENCE_IDS = (
    "ascencio_vasquez_2021_thesis",
    "dwd_2024_hourly_solar",
    "dwd_hourly_solar_documentation",
)
_MAX_ARCHIVE_BYTES = 512 * 1024**2
_STAMP = r"\d{10}:\d{2}"
_HEADERS = (
    "STATIONS_ID",
    "MESS_DATUM",
    "QN_592",
    "ATMO_LBERG",
    "FD_LBERG",
    "FG_LBERG",
    "SD_LBERG",
    "ZENIT",
    "MESS_DATUM_WOZ",
    "eor",
)
_VALUES = {
    "ATMO_LBERG": ("longwave_down_jcm2", "J/cm²"),
    "FD_LBERG": ("diffuse_radiation_jcm2", "J/cm²"),
    "FG_LBERG": ("global_radiation_jcm2", "J/cm²"),
    "SD_LBERG": ("sunshine_duration_minutes", "Minute"),
    "ZENIT": ("solar_zenith_degrees", "degree"),
}


def _integer(value: int, label: str, maximum: int) -> None:
    if type(value) is not int or not 1 <= value <= maximum:
        raise ValueError(f"{label} must be an integer from 1 through {maximum}")


def _station(value: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"\d{5}", value) is None:
        raise ValueError("Use the exact five-digit DWD station identifier, including leading zeros")
    return value


def _dates(start: date, end: date) -> None:
    if type(start) is not date or type(end) is not date or start > end:
        raise ValueError("DWD dates must be ordered inclusive date objects")
    if not 1700 <= start.year <= end.year <= 9998:
        raise ValueError("DWD requested dates must be within 1700..9998")


def _bbox(value: tuple[float, float, float, float] | None) -> None:
    if value is None:
        return
    if len(value) != 4 or not all(math.isfinite(x) for x in value):
        raise ValueError("DWD bbox requires four finite coordinates")
    west, south, east, north = value
    if not (-180 <= west <= east <= 180 and -90 <= south <= north <= 90):
        raise ValueError("DWD bbox must be ordered WEST SOUTH EAST NORTH within geographic bounds")


def _json(value: object) -> dict[str, JSONValue]:
    return cast(dict[str, JSONValue], json.loads(json.dumps(value, allow_nan=False)))


def _endpoint(station_id: str) -> str:
    return f"{_ROOT}/stundenwerte_ST_{_station(station_id)}_row.zip"


def _catalogue_request(bbox: tuple[float, float, float, float] | None) -> dict[str, JSONValue]:
    return _json(
        {
            "source": "DWD CDC",
            "schema_version": 1,
            "product": "hourly_solar_station_catalogue",
            "endpoint": STATIONS_ENDPOINT,
            "bbox_west_south_east_north": bbox,
        }
    )


def _solar_request(station_id: str, start: date, end: date) -> dict[str, JSONValue]:
    return {
        "source": "DWD CDC",
        "schema_version": 1,
        "product": "hourly_solar",
        "station_id": _station(station_id),
        "endpoint": _endpoint(station_id),
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "date_selection": "inclusive UTC dates of native MESS_DATUM labels",
        "units": "original hourly radiation energy in J/cm²; no flux conversion",
    }


def normalize_stations(
    raw: bytes,
    *,
    bbox: tuple[float, float, float, float] | None = None,
    maximum_stations: int = 10_000,
) -> pd.DataFrame:
    """Decode the documented fixed-width station list without losing German names."""
    _bbox(bbox)
    _integer(maximum_stations, "maximum_stations", 100_000)
    if not raw.endswith((b"\n", b"\r")):
        raise RetrievalError("DWD station catalogue lacks its complete final record delimiter")
    lines = raw.decode("iso-8859-1").splitlines()
    if (
        len(lines) < 3
        or lines[0].split()
        != [
            "Stations_id",
            "von_datum",
            "bis_datum",
            "Stationshoehe",
            "geoBreite",
            "geoLaenge",
            "Stationsname",
            "Bundesland",
        ]
        or re.fullmatch(r"[- ]+", lines[1]) is None
    ):
        raise RetrievalError("DWD station catalogue has an unsupported header")
    rows = []
    for line in lines[2:]:
        if not line.strip():
            continue
        if len(rows) >= maximum_stations:
            raise RetrievalError("DWD catalogue exceeds maximum_stations before filtering")
        parts = line.split(maxsplit=6)
        if len(parts) != 7 or len(parts[6]) <= 41:
            raise RetrievalError("DWD station catalogue contains an incomplete record")
        station_id, first, last, elevation, latitude, longitude, names = parts
        try:
            _station(station_id)
            if not re.fullmatch(r"\d{8}", first) or not re.fullmatch(r"\d{8}", last):
                raise ValueError("unsupported dates")
            begin, finish = date.fromisoformat(first), date.fromisoformat(last)
            lat, lon, height = float(latitude), float(longitude), float(elevation)
            if (
                begin > finish
                or not all(math.isfinite(x) for x in (lat, lon, height))
                or not -90 <= lat <= 90
                or not -180 <= lon <= 180
                or not names[:41].strip()
                or not names[41:].strip()
            ):
                raise ValueError("invalid station metadata")
        except ValueError:
            raise RetrievalError("DWD catalogue contains invalid station metadata") from None
        rows.append(
            {
                "station_id": station_id,
                "station_name": names[:41].strip(),
                "state": names[41:].strip(),
                "country_code": "DE",
                "latitude": lat,
                "longitude": lon,
                "elevation_m": height,
                "available_from": begin.isoformat(),
                "available_to": finish.isoformat(),
                "source_line": line,
            }
        )
    if not rows:
        raise RetrievalError("DWD catalogue is empty")
    frame = pd.DataFrame(rows)
    if frame.station_id.duplicated().any():
        raise RetrievalError("DWD catalogue repeats a station identifier")
    count = len(frame)
    if bbox is not None:
        west, south, east, north = bbox
        frame = frame.loc[
            frame.longitude.between(west, east) & frame.latitude.between(south, north)
        ].reset_index(drop=True)
    frame.attrs = {
        "source": "DWD CDC hourly solar station catalogue",
        "encoding": "ISO-8859-1",
        "source_rows": count,
        "catalogue_coordinates": "recent position; historical relocations are in each archive",
        "bbox_west_south_east_north": list(bbox) if bbox is not None else None,
        "reference_ids": list(REFERENCE_IDS),
    }
    return frame


def _archive(
    raw: bytes, station_id: str, maximum_members: int, maximum_bytes: int
) -> tuple[str, str, list[dict[str, object]], str]:
    """Read flat, bounded archive members in memory; never extract filesystem paths."""
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            members = archive.infolist()
            if not 1 <= len(members) <= maximum_members:
                raise RetrievalError("DWD archive exceeds its member-count limit or is empty")
            if len({item.filename for item in members}) != len(members):
                raise RetrievalError("DWD archive repeats member names")
            if sum(item.file_size for item in members) > maximum_bytes:
                raise RetrievalError("DWD archive exceeds its uncompressed byte limit")
            product = []
            parameter_name = f"Metadaten_Parameter_st_stunde_{station_id}.txt"
            records: list[dict[str, object]] = []
            table = parameter = ""
            for member in members:
                name = member.filename
                safe_name = PurePosixPath(name)
                if (
                    len(safe_name.parts) != 1
                    or "\\" in name
                    or safe_name.is_absolute()
                    or member.is_dir()
                    or stat.S_ISLNK(member.external_attr >> 16)
                    or member.flag_bits & 1
                    or member.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                ):
                    raise RetrievalError("DWD archive has an unsafe or unsupported member")
                is_product = re.fullmatch(
                    rf"produkt_st_stunde_\d{{8}}_\d{{8}}_{station_id}\.txt", name
                )
                is_metadata = re.fullmatch(
                    rf"Metadaten_[A-Za-z0-9_]+_{station_id}\.(?:txt|html)", name
                )
                if not is_product and not is_metadata:
                    raise RetrievalError("DWD archive has an unexpected member or station")
                with archive.open(member) as stream:
                    content = stream.read(maximum_bytes + 1)
                if len(content) != member.file_size or len(content) > maximum_bytes:
                    raise RetrievalError("DWD archive member disagrees with its bounded size")
                records.append(
                    {
                        "filename": name,
                        "size_bytes": len(content),
                        "sha256": hashlib.sha256(content).hexdigest(),
                    }
                )
                if is_product:
                    product.append(name)
                    table = content.decode("ascii")
                elif name == parameter_name:
                    parameter = content.decode("iso-8859-1")
            if len(product) != 1 or not parameter:
                raise RetrievalError(
                    "DWD archive needs one product table and its parameter metadata"
                )
            return table, parameter, records, product[0]
    except RetrievalError:
        raise
    except (zipfile.BadZipFile, UnicodeError, RuntimeError, NotImplementedError):
        raise RetrievalError(
            "DWD source is not a readable complete supported ZIP archive"
        ) from None


def _parameter_records(text: str, station_id: str) -> list[dict[str, str]]:
    rows = []
    try:
        reader = csv.DictReader(io.StringIO(text), delimiter=";", strict=True)
        required = {"Stations_ID", "Parameter", "Einheit", "Zusatz-Info", "eor"}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise RetrievalError("DWD parameter metadata has unsupported columns")
        for row in reader:
            first = row.get("Stations_ID", "")
            if first.startswith(("Legende:", "generiert:")):
                break
            if not first.strip().isdigit() or first.strip().zfill(5) != station_id:
                raise RetrievalError("DWD parameter metadata identifies a different station")
            if row.get("eor") != "eor" or None in row or any(v is None for v in row.values()):
                raise RetrievalError("DWD parameter metadata contains an incomplete row")
            rows.append({key: value.strip() for key, value in row.items() if key})
    except (csv.Error, AttributeError):
        raise RetrievalError("DWD parameter metadata is malformed") from None
    if not rows:
        raise RetrievalError("DWD parameter metadata is empty")
    return rows


def _number(values: pd.Series, name: str) -> pd.Series:
    clean = values.str.strip().mask(values.str.strip().eq("-999"))
    try:
        numbers = pd.to_numeric(clean, errors="raise").astype("float64")
    except (ValueError, TypeError):
        raise RetrievalError(f"DWD {name} contains an unsupported numeric value") from None
    if np.isinf(numbers.to_numpy()).any() or (numbers.isna() & clean.notna()).any():
        raise RetrievalError(f"DWD {name} contains an unsupported nonfinite/missing value")
    return numbers.mask(numbers.eq(-999))


def normalize_solar(
    raw: bytes,
    station_id: str,
    start: date,
    end: date,
    *,
    maximum_rows: int = 1_000_000,
    maximum_archive_members: int = 128,
    maximum_uncompressed_bytes: int = _MAX_ARCHIVE_BYTES,
) -> pd.DataFrame:
    """Preserve hourly J/cm² sums and exact UTC/true-solar-time labels and QN codes."""
    station_id = _station(station_id)
    _dates(start, end)
    _integer(maximum_rows, "maximum_rows", 2_000_000)
    _integer(maximum_archive_members, "maximum_archive_members", 1024)
    _integer(maximum_uncompressed_bytes, "maximum_uncompressed_bytes", _MAX_ARCHIVE_BYTES)
    table, parameters, members, product = _archive(
        raw, station_id, maximum_archive_members, maximum_uncompressed_bytes
    )
    if not table.endswith(("\n", "\r")):
        raise RetrievalError("DWD product lacks its complete final record delimiter")
    try:
        reader = csv.reader(io.StringIO(table), delimiter=";", strict=True)
        if tuple(next(reader)) != _HEADERS:
            raise RetrievalError("DWD solar table has unsupported columns or units")
        for count, row in enumerate(reader, start=1):
            if count > maximum_rows:
                raise RetrievalError("DWD solar archive exceeds maximum_rows before filtering")
            if len(row) != len(_HEADERS) or row[-1] != "eor":
                raise RetrievalError("DWD solar table contains an incomplete record")
        frame = pd.read_csv(
            io.StringIO(table),
            sep=";",
            dtype="string[pyarrow]",
            keep_default_na=False,
            na_filter=False,
        )
    except (csv.Error, StopIteration, pd.errors.ParserError, pd.errors.EmptyDataError):
        raise RetrievalError("DWD solar table is not a complete delimited table") from None
    if frame.empty:
        raise RetrievalError("DWD solar table has no observations")
    source_ids = frame.STATIONS_ID.str.strip()
    if (
        not source_ids.str.fullmatch(r"\d{1,5}").all()
        or not source_ids.str.zfill(5).eq(station_id).all()
    ):
        raise RetrievalError("DWD solar table identifies a different station")
    labels, woz_labels = frame.MESS_DATUM.str.strip(), frame.MESS_DATUM_WOZ.str.strip()
    if not labels.str.fullmatch(_STAMP).all() or not woz_labels.str.fullmatch(_STAMP).all():
        raise RetrievalError("DWD solar timestamps must retain the native minute-resolution labels")
    try:
        timestamps = pd.to_datetime(labels, format="%Y%m%d%H:%M", utc=True, errors="raise")
        woz = pd.to_datetime(woz_labels, format="%Y%m%d%H:%M", errors="raise")
    except ValueError:
        raise RetrievalError("DWD solar table contains an invalid timestamp") from None
    if timestamps.duplicated().any() or not timestamps.is_monotonic_increasing:
        raise RetrievalError("DWD solar UTC labels must be unique and ordered")
    parameter_records = _parameter_records(parameters, station_id)
    frame["station_id"] = station_id
    frame["timestamp"] = timestamps
    frame["timestamp_woz"] = woz
    for original, (target, unit) in _VALUES.items():
        frame[target] = _number(frame[original], original)
        if original == "ZENIT" or frame[target].isna().all():
            continue
        matching = [row for row in parameter_records if row["Parameter"] == original]
        if not matching or any(
            row["Einheit"] != unit or row["Zusatz-Info"] != "in UTC und WOZ" for row in matching
        ):
            raise RetrievalError("DWD parameter metadata does not confirm native units and UTC/WOZ")
    quality = _number(frame.QN_592, "QN_592")
    if not (quality.isna() | (quality.eq(quality.round()) & quality.between(0, 99))).all():
        raise RetrievalError("DWD QN_592 must contain integer quality levels")
    frame["quality_level"] = quality.astype("Int64")
    chosen = frame.timestamp.ge(pd.Timestamp(start, tz="UTC")) & frame.timestamp.lt(
        pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)
    )
    out = frame.loc[chosen].reset_index(drop=True)
    if out.empty:
        raise RetrievalError("DWD archive contains no observations in the requested UTC dates")
    out.attrs = {
        "source": "DWD CDC hourly solar",
        "dataset_version": "v24.03 format contract; acquired archive vintage is separately hashed",
        "product_member": product,
        "source_rows": len(frame),
        "selected_rows": len(out),
        "timezone": "UTC for MESS_DATUM; source minute offsets retained",
        "timestamp_woz": "local true solar time; not a civil timezone or a second UTC timestamp",
        "time_basis_evidence": f"Metadaten_Parameter_st_stunde_{station_id}.txt",
        "interval_boundary": "source reference label; start/end alignment is not inferred",
        "native_statistic": "hourly radiation energy and sunshine-duration sums",
        "units": {target: unit for target, unit in _VALUES.values()},
        "missing_value": "-999 in numeric source fields; original strings retained",
        "quality": "QN_592 retained as source procedure code; no universal pass or masking applied",
        "parameter_metadata": parameter_records,
        "archive_members": members,
        "license": "CC BY 4.0",
        "reference_ids": list(REFERENCE_IDS),
    }
    return out


@dataclass(frozen=True, slots=True)
class DWDStations:
    frame: pd.DataFrame
    request: RequestRecord
    raw_bytes: bytes
    bbox: tuple[float, float, float, float] | None = None
    maximum_stations: int = 10_000


@dataclass(frozen=True, slots=True)
class DWDSolar:
    station_id: str
    start: date
    end: date
    frame: pd.DataFrame
    request: RequestRecord
    raw_bytes: bytes
    maximum_rows: int = 1_000_000
    maximum_archive_members: int = 128
    maximum_uncompressed_bytes: int = _MAX_ARCHIVE_BYTES


def _sidecar(output: Path, *, catalogue: bool) -> Path:
    return output.with_suffix(output.suffix + (".source.txt" if catalogue else ".source.zip"))


def _existing(output: Path, request: dict[str, JSONValue], *, catalogue: bool) -> Artifact | None:
    manifest_path = output.with_suffix(output.suffix + ".json")
    if output.is_symlink() or manifest_path.is_symlink():
        raise ValueError("DWD output and manifest must not be symlinks")
    previous = existing_artifact(output, fingerprint(request))
    source = _sidecar(output, catalogue=catalogue)
    if previous is None:
        if source.exists() or source.is_symlink():
            raise ValueError("Incomplete DWD source sidecar; inspect it or use a new output")
        return None
    manifest = json.loads(manifest_path.read_text("utf-8"))
    try:
        saved = manifest["provenance"]["source_artifact"]
        if (
            source.is_symlink()
            or not source.is_file()
            or saved["filename"] != source.name
            or source.stat().st_size != saved["size_bytes"]
            or sha256_file(source) != saved["sha256"]
        ):
            raise ValueError("DWD source sidecar differs from its saved checksum")
    except (KeyError, TypeError):
        raise ValueError("DWD output lacks required source provenance") from None
    return previous


def _save(
    frame: pd.DataFrame,
    raw: bytes,
    record: RequestRecord,
    output: Path,
    request: dict[str, JSONValue],
    *,
    catalogue: bool,
) -> Artifact:
    if (
        record.endpoint != request["endpoint"]
        or record.parameters
        or record.size_bytes != len(raw)
        or record.sha256 != hashlib.sha256(raw).hexdigest()
    ):
        raise ValueError("DWD source bytes differ from their acquisition provenance")
    source = _sidecar(output, catalogue=catalogue)
    atomic_bytes(source, raw)
    return write_parquet(
        frame,
        output,
        request=request,
        provenance=_json(
            {
                "request": asdict(record),
                "metadata": frame.attrs,
                "source_artifact": {
                    "filename": source.name,
                    "size_bytes": len(raw),
                    "sha256": record.sha256,
                },
                "reference_ids": list(REFERENCE_IDS),
            }
        ),
    )


def save_stations(result: DWDStations, output: Path) -> Artifact:
    request = _catalogue_request(result.bbox)
    if previous := _existing(output, request, catalogue=True):
        return previous
    verified = normalize_stations(
        result.raw_bytes, bbox=result.bbox, maximum_stations=result.maximum_stations
    )
    if not verified.equals(result.frame) or verified.attrs != result.frame.attrs:
        raise ValueError("DWD station frame differs from its source metadata")
    return _save(verified, result.raw_bytes, result.request, output, request, catalogue=True)


def save_solar(result: DWDSolar, output: Path) -> Artifact:
    request = _solar_request(result.station_id, result.start, result.end)
    if previous := _existing(output, request, catalogue=False):
        return previous
    verified = normalize_solar(
        result.raw_bytes,
        result.station_id,
        result.start,
        result.end,
        maximum_rows=result.maximum_rows,
        maximum_archive_members=result.maximum_archive_members,
        maximum_uncompressed_bytes=result.maximum_uncompressed_bytes,
    )
    if not verified.equals(result.frame) or verified.attrs != result.frame.attrs:
        raise ValueError("DWD solar frame differs from its native source observations or metadata")
    return _save(verified, result.raw_bytes, result.request, output, request, catalogue=False)


@dataclass(slots=True)
class DWDClient:
    http: HTTPClient
    maximum_rows: int = 1_000_000
    maximum_stations: int = 10_000
    maximum_archive_members: int = 128
    maximum_uncompressed_bytes: int = _MAX_ARCHIVE_BYTES

    def __post_init__(self) -> None:
        _integer(self.maximum_rows, "maximum_rows", 2_000_000)
        _integer(self.maximum_stations, "maximum_stations", 100_000)
        _integer(self.maximum_archive_members, "maximum_archive_members", 1024)
        _integer(self.maximum_uncompressed_bytes, "maximum_uncompressed_bytes", _MAX_ARCHIVE_BYTES)

    def _download(self, endpoint: str) -> tuple[bytes, RequestRecord]:
        with tempfile.TemporaryDirectory(prefix="energy-dwd-") as directory:
            target = Path(directory) / "source"
            record = self.http.download_file(endpoint, target)
            return target.read_bytes(), record

    def stations(self, *, bbox: tuple[float, float, float, float] | None = None) -> DWDStations:
        _bbox(bbox)
        raw, request = self._download(STATIONS_ENDPOINT)
        frame = normalize_stations(raw, bbox=bbox, maximum_stations=self.maximum_stations)
        return DWDStations(frame, request, raw, bbox, self.maximum_stations)

    def retrieve_stations(
        self, output: Path, *, bbox: tuple[float, float, float, float] | None = None
    ) -> Artifact:
        _bbox(bbox)
        if previous := _existing(output, _catalogue_request(bbox), catalogue=True):
            return previous
        return save_stations(self.stations(bbox=bbox), output)

    def solar(self, station_id: str, start: date, end: date) -> DWDSolar:
        station_id = _station(station_id)
        _dates(start, end)
        raw, request = self._download(_endpoint(station_id))
        frame = normalize_solar(
            raw,
            station_id,
            start,
            end,
            maximum_rows=self.maximum_rows,
            maximum_archive_members=self.maximum_archive_members,
            maximum_uncompressed_bytes=self.maximum_uncompressed_bytes,
        )
        return DWDSolar(
            station_id,
            start,
            end,
            frame,
            request,
            raw,
            self.maximum_rows,
            self.maximum_archive_members,
            self.maximum_uncompressed_bytes,
        )

    def retrieve(self, station_id: str, start: date, end: date, output: Path) -> Artifact:
        station_id = _station(station_id)
        _dates(start, end)
        if previous := _existing(output, _solar_request(station_id, start, end), catalogue=False):
            return previous
        return save_solar(self.solar(station_id, start, end), output)
