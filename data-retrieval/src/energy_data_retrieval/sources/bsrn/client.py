"""Bounded BSRN discovery and native minute data through PANGAEA's DOI interface.

The supported product is one station/month's LR0100 radiation, optionally with
LR0300 variables in the same published table. This is not a general PANGAEA
client, an FTP credential handler, or an hourly weather preparation step.
"""

from __future__ import annotations

import calendar
import csv
import hashlib
import io
import json
import re
from dataclasses import asdict, dataclass
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
    array_value,
    atomic_bytes,
    object_value,
)

BSRN_HOSTS = frozenset({"doi.pangaea.de", "www.pangaea.de"})
SEARCH_ENDPOINT = "https://www.pangaea.de/advanced/search.php"
REFERENCE_IDS = (
    "ascencio_vasquez_2021_thesis",
    "driemel_2018_bsrn",
    "bsrn_pangaea_access",
    "pangaea_data_access",
    "pangaea_quality_flags",
)
_DOI = re.compile(
    r"(?:https://(?:doi\.org|doi\.pangaea\.de)/|doi:)?10\.1594/PANGAEA\.([1-9]\d{0,8})",
    re.IGNORECASE,
)
_TITLE = re.compile(
    r"Basic(?: and other)? measurements of radiation at station .+ \((\d{4})-(\d{2})\)"
)
_STAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::00)?(?:Z|\+00:00)?")
_NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
_COLUMN_MAP = {
    "Height [m]": "height_m",
    "T2 [°C]": "temperature_2m_c",
    "RH [%]": "relative_humidity_percent",
    "PoPoPoPo [hPa]": "station_pressure_hpa",
}
for _source, _target in (
    ("SWD", "swd"),
    ("DIR", "dir"),
    ("DIF", "dif"),
    ("LWD", "lwd"),
    ("SWU", "swu"),
    ("LWU", "lwu"),
    ("NET", "net"),
):
    for _suffix, _statistic in (
        ("", ""),
        (" std dev", "_stddev"),
        (" min", "_min"),
        (" max", "_max"),
    ):
        _COLUMN_MAP[f"{_source}{_suffix} [W/m**2]"] = f"{_target}{_statistic}_wm2"
_CORE = {"SWD [W/m**2]", "DIR [W/m**2]", "DIF [W/m**2]", "LWD [W/m**2]"}


def _doi(value: object) -> str:
    if not isinstance(value, str) or (match := _DOI.fullmatch(value.strip())) is None:
        raise ValueError("Use one exact PANGAEA DOI, such as 10.1594/PANGAEA.725795")
    return f"10.1594/PANGAEA.{match.group(1)}"


def _selection(station: str, year: int, month: int) -> tuple[str, int, int]:
    if not isinstance(station, str) or re.fullmatch(r"[A-Za-z]{3}", station) is None:
        raise ValueError("BSRN station must be an exact three-letter station code")
    if type(year) is not int or not 1992 <= year <= 9999:
        raise ValueError("BSRN year must be an integer from 1992 through 9999")
    if type(month) is not int or not 1 <= month <= 12:
        raise ValueError("BSRN month must be an integer from 1 through 12")
    return station.lower(), year, month


def _rows_limit(value: int) -> None:
    if type(value) is not int or not 1 <= value <= 50_000:
        raise ValueError("maximum_rows must be an integer from 1 through 50000")


def _json_object(value: object) -> dict[str, JSONValue]:
    return cast(dict[str, JSONValue], json.loads(json.dumps(value, allow_nan=False)))


def _request(
    doi: str, station: str, year: int, month: int, maximum_rows: int
) -> dict[str, JSONValue]:
    return {
        "source": "BSRN via PANGAEA",
        "schema_version": 1,
        "doi": _doi(doi),
        "station": station,
        "year": year,
        "month": month,
        "logical_record": "0100 with 0300 when published in the same table",
        "maximum_rows": maximum_rows,
        "timezone": "UTC; original minute labels retained",
    }


def _timestamp(value: object) -> pd.Timestamp:
    if not isinstance(value, str) or _STAMP.fullmatch(value) is None:
        raise RetrievalError("BSRN timestamps must be original UTC minute labels")
    try:
        return (
            pd.Timestamp(value).tz_localize("UTC")
            if not value.endswith(("Z", "+00:00"))
            else pd.Timestamp(value)
        )
    except ValueError:
        raise RetrievalError("BSRN metadata contains an invalid UTC timestamp") from None


def _validate_metadata(
    metadata: dict[str, JSONValue], doi: str, year: int, month: int
) -> tuple[pd.Timestamp, pd.Timestamp]:
    kind = metadata.get("@type")
    if kind != "Dataset" and (not isinstance(kind, list) or "Dataset" not in kind):
        raise RetrievalError("PANGAEA did not return a Dataset metadata record")
    if _doi(metadata.get("identifier")) != doi:
        raise RetrievalError("PANGAEA metadata identifies a different dataset DOI")
    title = metadata.get("name")
    match = _TITLE.fullmatch(title) if isinstance(title, str) else None
    if match is None or tuple(map(int, match.groups())) != (year, month):
        raise RetrievalError(
            "Expected the requested month of BSRN basic radiation (LR0100), "
            "not another logical record"
        )
    if not metadata.get("creator") or not metadata.get("license"):
        raise RetrievalError("BSRN dataset metadata must retain its creator and license")
    coverage = metadata.get("temporalCoverage")
    if not isinstance(coverage, str) or len(coverage.split("/")) != 2:
        raise RetrievalError("BSRN dataset omits its exact temporal coverage")
    first, last = (_timestamp(value) for value in coverage.split("/"))
    if (
        first > last
        or (first.year, first.month) != (year, month)
        or (last.year, last.month) != (year, month)
    ):
        raise RetrievalError("BSRN dataset temporal coverage disagrees with the requested month")
    return first, last


def _description(text: str) -> tuple[dict[str, str], str]:
    prefix = "/* DATA DESCRIPTION:"
    content = text.removeprefix("\ufeff")
    if not content.startswith(prefix) or "*/" not in content:
        raise RetrievalError("Expected PANGAEA's complete tabular export with DATA DESCRIPTION")
    description, table = content[len(prefix) :].split("*/", 1)
    if len(description) > 1_000_000:
        raise RetrievalError("BSRN source description exceeds the supported metadata bound")
    pieces = re.split(r"(?m)^([A-Za-z][A-Za-z ()/-]*):\t", description)
    if len(pieces) < 3 or len(pieces) % 2 != 1:
        raise RetrievalError("BSRN source description has an unsupported format")
    sections: dict[str, str] = {}
    for name, value in zip(pieces[1::2], pieces[2::2], strict=True):
        if name in sections:
            raise RetrievalError("BSRN source description repeats a metadata section")
        sections[name] = value.strip()
    return sections, table.lstrip("\r\n")


def normalize_dataset(
    text: str,
    metadata: dict[str, JSONValue],
    *,
    doi: str,
    station: str,
    year: int,
    month: int,
    maximum_rows: int = 50_000,
) -> pd.DataFrame:
    """Keep original minute labels, all raw fields, and unaltered numeric payloads.

    Empty fields become null only in numeric columns. A published qualifier
    (? / * # > <) remains beside its numeric payload and in the original source
    field; qualified numbers are not promoted to unqualified observations.
    Values, including negatives, are never clipped or interpolated.
    """
    doi = _doi(doi)
    station, year, month = _selection(station, year, month)
    _rows_limit(maximum_rows)
    first, last = _validate_metadata(metadata, doi, year, month)
    sections, table = _description(text)
    if "Baseline Surface Radiation Network (BSRN)" not in sections.get("Project(s)", ""):
        raise RetrievalError("PANGAEA dataset is not identified as a BSRN project record")
    events = re.findall(r"(?m)^[\t ]*([A-Z]{3}) \(", sections.get("Event(s)", ""))
    if events != [station.upper()]:
        raise RetrievalError(
            "BSRN source station differs from the requested station or contains multiple stations"
        )
    if doi not in sections.get("Citation", "") or not sections.get("License"):
        raise RetrievalError("BSRN source must preserve its dataset citation and license")
    reader = csv.reader(io.StringIO(table), delimiter="\t", strict=True)
    try:
        headers = next(reader)
        if len(headers) != len(set(headers)) or not headers or headers[0] != "Date/Time":
            raise RetrievalError("BSRN source needs unique headers beginning with Date/Time")
        if not _CORE.intersection(headers):
            raise RetrievalError("BSRN source has no supported LR0100 radiation columns")
        if unknown := set(headers) - {"Date/Time", *_COLUMN_MAP}:
            raise RetrievalError(f"Unsupported BSRN columns or units: {', '.join(sorted(unknown))}")
        rows: list[list[str]] = []
        for row in reader:
            if len(row) != len(headers):
                raise RetrievalError("BSRN row width disagrees with the published parameter table")
            if len(rows) >= maximum_rows:
                raise RetrievalError("BSRN source exceeded maximum_rows")
            rows.append(row)
    except (csv.Error, StopIteration):
        raise RetrievalError("BSRN source has an invalid or empty tabular body") from None
    if not rows:
        raise RetrievalError("BSRN dataset has no observations")
    raw = pd.DataFrame(rows, columns=headers)
    labels = raw["Date/Time"]
    if not labels.str.fullmatch(_STAMP).all():
        raise RetrievalError("BSRN timestamps must be original UTC minute labels")
    try:
        times = pd.to_datetime(labels, utc=True, format="ISO8601", errors="raise")
    except ValueError:
        raise RetrievalError("BSRN source has an invalid UTC minute timestamp") from None
    if times.isna().any() or times.duplicated().any() or not times.is_monotonic_increasing:
        raise RetrievalError("BSRN minute labels must be nonmissing, unique and ordered")
    if times.iloc[0] != first or times.iloc[-1] != last:
        raise RetrievalError("BSRN export endpoints disagree with its advertised dataset coverage")
    if not ((times.dt.year == year) & (times.dt.month == month)).all():
        raise RetrievalError("BSRN source contains observations outside the requested month")
    out = pd.DataFrame({"station_id": station, "timestamp": times, "dataset_doi": doi})
    units: dict[str, str] = {}
    for header in headers[1:]:
        target = _COLUMN_MAP[header]
        values = raw[header]
        if not (values.eq("") | values.str.fullmatch(rf"[?/*#<>]?{_NUMBER}")).all():
            raise RetrievalError(f"BSRN numeric field has an unsupported value/qualifier: {header}")
        qualifiers = values.str.extract(r"^([?/*#<>])", expand=False).fillna("")
        numbers = values.str.replace(r"^[?/*#<>]", "", regex=True).replace("", np.nan)
        converted = pd.to_numeric(numbers, errors="raise").astype("float64")
        if np.isinf(converted).any():
            raise RetrievalError("BSRN numeric field contains an infinite value")
        out[target] = converted
        out[target + "_qualifier"] = qualifiers
        units[target] = header.split("[", 1)[1].rstrip("]")
    for header in headers:
        out[f"source:{header}"] = raw[header]
    expected_minutes = calendar.monthrange(year, month)[1] * 24 * 60
    out.attrs.update(
        source="BSRN via PANGAEA",
        station_id=station,
        dataset_doi=doi,
        year=year,
        month=month,
        logical_records=["0100", "0300"]
        if any(header.startswith(("SWU ", "LWU ", "NET ")) for header in headers)
        else ["0100"],
        source_citation=sections["Citation"],
        source_license=sections["License"],
        source_description=sections,
        units=units,
        source_columns=headers,
        timestamp_convention="original UTC minute labels; no shift or inferred interval anchor",
        temporal_resolution="native minute observations; no resampling",
        missing_minutes_in_calendar_month=expected_minutes - len(out),
        quality_control_applied=False,
        quality_flags_available_in_archive=False,
        numeric_qualifiers=(
            "published PANGAEA prefix retained; numeric payload is not a QC acceptance"
        ),
        hourly_weather_contract=False,
        missing_rule="empty numeric fields become null; no filling, clipping or interpolation",
        reference_ids=list(REFERENCE_IDS),
    )
    return out


@dataclass(frozen=True, slots=True)
class BSRNSearch:
    station: str
    year: int
    month: int
    query: str
    candidates: tuple[dict[str, JSONValue], ...]
    requests: tuple[RequestRecord, ...]

    def as_dict(self) -> dict[str, object]:
        return asdict(self) | {
            "source": "BSRN via PANGAEA",
            "candidate_validation_required": True,
            "search_complete": True,
            "search_api": "current internal endpoint used by official pangaeapy",
            "reference_ids": list(REFERENCE_IDS),
        }


@dataclass(frozen=True, slots=True)
class BSRNDataset:
    doi: str
    station: str
    year: int
    month: int
    maximum_rows: int
    frame: pd.DataFrame
    metadata: dict[str, JSONValue]
    raw_text: str
    requests: tuple[RequestRecord, ...]


def _sidecars(output: Path) -> tuple[Path, Path]:
    return output.with_suffix(output.suffix + ".source.tsv"), output.with_suffix(
        output.suffix + ".metadata.json"
    )


def _existing(output: Path, request: dict[str, JSONValue]) -> Artifact | None:
    if output.is_symlink() or output.with_suffix(output.suffix + ".json").is_symlink():
        raise ValueError("BSRN output and manifest must not be symlinks")
    artifact = existing_artifact(output, fingerprint(request))
    paths = _sidecars(output)
    if artifact is None:
        if any(path.exists() or path.is_symlink() for path in paths):
            raise ValueError("Incomplete BSRN source sidecars; inspect them or choose a new output")
        return None
    manifest = json.loads(output.with_suffix(output.suffix + ".json").read_text("utf-8"))
    try:
        saved = manifest["provenance"]["source_artifacts"]
        for path in paths:
            record = saved[path.name]
            if (
                path.is_symlink()
                or not path.is_file()
                or path.stat().st_size != record["size_bytes"]
                or sha256_file(path) != record["sha256"]
            ):
                raise ValueError("BSRN source sidecar differs from its saved checksum")
    except (KeyError, TypeError):
        raise ValueError("BSRN output omits required source sidecar provenance") from None
    return artifact


def save_dataset(result: BSRNDataset, output: Path) -> Artifact:
    """Publish normalized minutes plus exact source text, JSON-LD and source hashes."""
    request = _request(result.doi, result.station, result.year, result.month, result.maximum_rows)
    previous = _existing(output, request)
    if previous is not None:
        return previous
    # Validate a caller-created result against its immutable source inputs before saving.
    verified = normalize_dataset(
        result.raw_text,
        result.metadata,
        doi=result.doi,
        station=result.station,
        year=result.year,
        month=result.month,
        maximum_rows=result.maximum_rows,
    )
    if not verified.equals(result.frame) or verified.attrs != result.frame.attrs:
        raise ValueError("BSRN result frame differs from its source observations or metadata")
    text_path, metadata_path = _sidecars(output)
    source_text = result.raw_text.encode("utf-8")
    metadata_bytes = json.dumps(
        result.metadata, ensure_ascii=False, sort_keys=True, allow_nan=False
    ).encode("utf-8")
    atomic_bytes(text_path, source_text)
    atomic_bytes(metadata_path, metadata_bytes)
    provenance = _json_object(
        {
            "requests": [asdict(record) for record in result.requests],
            "metadata": verified.attrs,
            "dataset_metadata": result.metadata,
            "source_artifacts": {
                path.name: {
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "size_bytes": len(content),
                }
                for path, content in ((text_path, source_text), (metadata_path, metadata_bytes))
            },
            "reference_ids": REFERENCE_IDS,
        }
    )
    return write_parquet(verified, output, request=request, provenance=provenance)


@dataclass(slots=True)
class BSRNClient:
    http: HTTPClient
    maximum_rows: int = 50_000

    def __post_init__(self) -> None:
        _rows_limit(self.maximum_rows)

    def search(
        self,
        station: str,
        year: int,
        month: int,
        *,
        maximum_results: int = 100,
        page_size: int = 20,
    ) -> BSRNSearch:
        """Discover DOI candidates; a broad search hit is not verified station data.

        PANGAEA documents this search endpoint as internal and not a stable public
        REST contract. It is used by its official client; DOI retrieval below is
        independent of search and uses the documented DOI export interface.
        """
        station, year, month = _selection(station, year, month)
        for value, label, bound in (
            (maximum_results, "maximum_results", 1000),
            (page_size, "page_size", 100),
        ):
            if type(value) is not int or not 1 <= value <= bound:
                raise ValueError(f"{label} must be an integer from 1 through {bound}")
        query = f'project:BSRN event:{station.upper()} "{year:04d}-{month:02d}"'
        candidates: list[dict[str, JSONValue]] = []
        requests = []
        seen: set[str] = set()
        expected_total: int | None = None
        for offset in range(0, maximum_results, page_size):
            response = self.http.get_json(
                SEARCH_ENDPOINT,
                {"q": query, "count": str(page_size), "offset": str(offset)},
                use_cache=False,
            )
            requests.append(response.record)
            payload = object_value(response.value)
            total = payload.get("totalCount")
            if type(total) is not int or not 0 <= total <= maximum_results:
                raise RetrievalError("BSRN search count is invalid or exceeds maximum_results")
            if expected_total is not None and total != expected_total:
                raise RetrievalError("BSRN search changed during pagination; repeat discovery")
            expected_total = total
            if payload.get("offset") != offset:
                raise RetrievalError("BSRN search returned an unexpected result offset")
            results = array_value(payload.get("results"))
            if len(results) > page_size or len(candidates) + len(results) > total:
                raise RetrievalError("BSRN search result count disagrees with its metadata")
            for result in results:
                record = object_value(result)
                doi = _doi(record.get("URI"))
                if doi in seen:
                    raise RetrievalError("BSRN search repeated a DOI across its result pages")
                seen.add(doi)
                candidates.append(
                    {"doi": doi, "url": f"https://doi.pangaea.de/{doi}", "search_metadata": record}
                )
            if len(candidates) == total:
                return BSRNSearch(station, year, month, query, tuple(candidates), tuple(requests))
            if len(results) != page_size:
                raise RetrievalError("BSRN search ended before all matching candidates arrived")
        raise RetrievalError("BSRN search exceeded its bounded pagination limit")

    def dataset(self, doi: str, *, station: str, year: int, month: int) -> BSRNDataset:
        """Fetch and validate one explicitly identified station/month radiation dataset."""
        doi = _doi(doi)
        station, year, month = _selection(station, year, month)
        endpoint = f"https://doi.pangaea.de/{doi}"
        metadata = self.http.get_json(endpoint, {"format": "metadata_jsonld"}, use_cache=False)
        payload = object_value(metadata.value)
        _validate_metadata(payload, doi, year, month)
        exported = self.http.get_text(endpoint, {"format": "textfile"}, use_cache=False)
        frame = normalize_dataset(
            exported.value,
            payload,
            doi=doi,
            station=station,
            year=year,
            month=month,
            maximum_rows=self.maximum_rows,
        )
        return BSRNDataset(
            doi,
            station,
            year,
            month,
            self.maximum_rows,
            frame,
            payload,
            exported.value,
            (metadata.record, exported.record),
        )

    def retrieve(self, doi: str, *, station: str, year: int, month: int, output: Path) -> Artifact:
        """Reuse an exact verified local snapshot before making any network request."""
        doi = _doi(doi)
        station, year, month = _selection(station, year, month)
        previous = _existing(output, _request(doi, station, year, month, self.maximum_rows))
        if previous is not None:
            return previous
        return save_dataset(self.dataset(doi, station=station, year=year, month=month), output)
