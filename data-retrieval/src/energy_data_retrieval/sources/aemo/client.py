"""Public AEMO NEMWeb dispatch-unit SCADA, preserving instantaneous MW.

``timestamp`` is the published SETTLEMENTDATE dispatch label converted from
fixed AEST (UTC+10) to UTC. SCADAVALUE is a snapshot at the start of that
dispatch interval, not a five-minute average or settlement energy.
"""

from __future__ import annotations

import csv
import io
import math
import re
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from datetime import date, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urljoin, urlsplit
from zipfile import BadZipFile, ZipFile

import pandas as pd

from energy_data_retrieval.transport import HTTPClient, RequestRecord, RetrievalError

AEMO_HOSTS = frozenset({"nemweb.com.au", "www.nemweb.com.au"})
REFERENCE_IDS = ("aemo_dispatch_scada", "aemo_nemweb", "aemo_market_time")
CURRENT_ENDPOINT = "https://nemweb.com.au/Reports/CURRENT/Dispatch_SCADA/"
ARCHIVE_ENDPOINT = "https://nemweb.com.au/Reports/ARCHIVE/Dispatch_SCADA/"
DOCUMENTATION_ENDPOINT = (
    "https://visualisations.aemo.com.au/aemo/nemweb/MMSDataModelReport/"
    "Electricity/MMS%20Data%20Model%20Report_files/MMS_123.htm"
)
NEM_TIMEZONE = timezone(timedelta(hours=10), name="AEST")
_FILE = re.compile(r"PUBLIC_DISPATCHSCADA_\d{8}(?:\d{4}_\d+)?\.zip", re.IGNORECASE)
# Real registered identifiers include TARONG#1 and W/HOE#1.
_DUID = re.compile(r"[A-Za-z0-9_/#-]{1,20}")
_REQUIRED = {"SETTLEMENTDATE", "DUID", "SCADAVALUE"}


def _positive_integer(value: int, name: str) -> None:
    if type(value) is not int or value < 1:
        raise ValueError(f"{name} must be a positive integer")


def _duids(values: Sequence[str] | None) -> tuple[str, ...] | None:
    if values is None:
        return None
    if isinstance(values, str) or not values or len(values) > 10000:
        raise ValueError("duids must be a nonempty sequence of at most 10000 DUID strings")
    if any(not isinstance(value, str) or not _DUID.fullmatch(value) for value in values):
        raise ValueError("Invalid AEMO DUID")
    if len(set(values)) != len(values):
        raise ValueError("duids must be unique")
    return tuple(values)


def _file_url(url: str) -> str:
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in AEMO_HOSTS
        or parsed.port not in (None, 443)
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Use a public query-free HTTPS AEMO NEMWeb archive URL")
    parts = parsed.path.split("/")
    if (
        len(parts) != 5
        or parts[1].lower() != "reports"
        or parts[2].lower() not in {"current", "archive"}
        or parts[3].lower() != "dispatch_scada"
        or not _FILE.fullmatch(parts[4])
    ):
        raise ValueError("URL must identify a PUBLIC_DISPATCHSCADA ZIP in its source directory")
    return url


class _Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            self.links.extend(value for name, value in attrs if name == "href" and value)


@dataclass(frozen=True, slots=True)
class AEMOListing:
    """A current directory snapshot, sorted by source filename, with provenance."""

    urls: tuple[str, ...]
    request: RequestRecord


@dataclass(frozen=True, slots=True)
class AEMOGeneration:
    """Normalized observations and the exact downloaded archive's provenance."""

    frame: pd.DataFrame
    request: RequestRecord


@dataclass(slots=True)
class _ReadBudget:
    maximum_bytes: int
    maximum_members: int
    bytes_read: int = 0
    members_read: int = 0


def _csv_members(
    data: bytes, budget: _ReadBudget, *, name: str = "input.csv", depth: int = 0
) -> Iterator[tuple[str, str]]:
    if not data.startswith(b"PK"):
        try:
            yield name, data.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise RetrievalError("AEMO CSV is not valid UTF-8") from None
        return
    if depth >= 2:
        raise RetrievalError("AEMO ZIP nesting exceeds two archive levels")
    try:
        with ZipFile(io.BytesIO(data)) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                budget.members_read += 1
                if budget.members_read > budget.maximum_members:
                    raise RetrievalError("AEMO ZIP exceeds its member bound")
                if not info.filename.lower().endswith((".csv", ".zip")):
                    raise RetrievalError("AEMO ZIP contains an unsupported member type")
                remaining = budget.maximum_bytes - budget.bytes_read
                if info.file_size > remaining:
                    raise RetrievalError("AEMO ZIP exceeds its uncompressed byte bound")
                with archive.open(info) as stream:
                    body = stream.read(remaining + 1)
                budget.bytes_read += len(body)
                if budget.bytes_read > budget.maximum_bytes:
                    raise RetrievalError("AEMO ZIP exceeds its uncompressed byte bound")
                # Nothing is extracted to disk; member paths are only provenance labels.
                yield from _csv_members(
                    body, budget, name=f"{name}!{info.filename}", depth=depth + 1
                )
    except RetrievalError:
        raise
    except (BadZipFile, RuntimeError, OSError, NotImplementedError):
        raise RetrievalError("AEMO returned an invalid or unsupported ZIP archive") from None


def parse_dispatch_scada(
    content: str | bytes,
    *,
    duids: Sequence[str] | None = None,
    maximum_rows: int = 500000,
    maximum_uncompressed_bytes: int = 128 * 1024**2,
    maximum_members: int = 1000,
) -> pd.DataFrame:
    """Parse MMS CSV, an interval ZIP, or a daily ZIP of interval ZIPs.

    Native fields are retained under ``source:`` column names. Missing SCADA
    readings stay missing, and negative readings stay negative. Duplicate
    (dispatch label, DUID) keys fail instead of silently choosing a revision.
    The row bound applies before the optional DUID filter. No technology or
    generator/load classification is inferred from a DUID's spelling.
    """
    selected = _duids(duids)
    for value, name in (
        (maximum_rows, "maximum_rows"),
        (maximum_uncompressed_bytes, "maximum_uncompressed_bytes"),
        (maximum_members, "maximum_members"),
    ):
        _positive_integer(value, name)
    data = content.encode("utf-8") if isinstance(content, str) else content
    if len(data) > maximum_uncompressed_bytes:
        raise RetrievalError("AEMO input exceeds its byte bound")
    budget = _ReadBudget(maximum_uncompressed_bytes, maximum_members)
    rows: list[dict[str, object]] = []
    total_rows = 0
    seen: set[tuple[str, str]] = set()
    try:
        for member, text in _csv_members(data, budget):
            headers: dict[str, list[str]] = {}
            for fields in csv.reader(io.StringIO(text), strict=True):
                if fields[1:3] != ["DISPATCH", "UNIT_SCADA"]:
                    continue
                if len(fields) < 4:
                    raise RetrievalError("AEMO SCADA row has no version or columns")
                if fields[0] == "I":
                    names = fields[4:]
                    if not _REQUIRED.issubset(names) or len(names) != len(set(names)):
                        raise RetrievalError("AEMO SCADA header omits required or unique columns")
                    if fields[3] in headers and headers[fields[3]] != names:
                        raise RetrievalError("AEMO SCADA schema changes within one member")
                    headers[fields[3]] = names
                elif fields[0] == "D":
                    names = headers.get(fields[3])
                    if names is None or len(fields) != len(names) + 4:
                        raise RetrievalError(
                            "AEMO SCADA row has no matching header or column count"
                        )
                    total_rows += 1
                    if total_rows > maximum_rows:
                        raise RetrievalError("AEMO SCADA exceeds its row bound")
                    native = dict(zip(names, fields[4:], strict=True))
                    duid = native["DUID"]
                    if not _DUID.fullmatch(duid):
                        raise RetrievalError("AEMO SCADA contains an invalid DUID")
                    key = (native["SETTLEMENTDATE"], duid)
                    if key in seen:
                        raise RetrievalError(
                            "AEMO SCADA contains duplicate dispatch label/DUID keys"
                        )
                    seen.add(key)
                    if selected is not None and duid not in selected:
                        continue
                    raw_value = native["SCADAVALUE"].strip()
                    try:
                        value = float(raw_value) if raw_value else float("nan")
                    except ValueError:
                        raise RetrievalError("AEMO SCADA has a nonnumeric power value") from None
                    if raw_value and not math.isfinite(value):
                        raise RetrievalError("AEMO SCADA has a nonfinite power value")
                    rows.append(
                        {
                            "timestamp": native["SETTLEMENTDATE"],
                            "source": "aemo",
                            "area": "NEM",
                            "unit_id": duid,
                            "technology": None,
                            "value": value,
                            "unit": "MW",
                            "quantity_kind": "instantaneous_power",
                            "source_member": member,
                            **{f"source:{name}": raw for name, raw in native.items()},
                        }
                    )
    except csv.Error:
        raise RetrievalError("AEMO returned malformed MMS CSV") from None
    if not rows:
        raise RetrievalError("AEMO file contains no matching dispatch-unit SCADA observations")
    frame = pd.DataFrame(rows)
    if selected is not None and set(frame["unit_id"]) != set(selected):
        raise RetrievalError("One or more requested DUIDs are absent from the AEMO file")
    try:
        timestamps = pd.to_datetime(frame["timestamp"], format="%Y/%m/%d %H:%M:%S", errors="raise")
        if (
            timestamps.isna().any()
            or (timestamps.dt.minute % 5 != 0).any()
            or (timestamps.dt.second != 0).any()
        ):
            raise ValueError("Invalid dispatch labels")
        frame["timestamp"] = timestamps.dt.tz_localize(NEM_TIMEZONE).dt.tz_convert("UTC")
    except (ValueError, TypeError):
        raise RetrievalError(
            "AEMO dispatch labels must be valid five-minute NEM timestamps"
        ) from None
    frame = frame.sort_values(["timestamp", "unit_id"], ignore_index=True)
    if frame.duplicated(["timestamp", "unit_id"]).any():
        raise RetrievalError("AEMO SCADA contains duplicate dispatch label/DUID keys")
    frame.attrs.update(
        source="AEMO NEMWeb DISPATCH_UNIT_SCADA",
        reference_ids=list(REFERENCE_IDS),
        native_timezone="AEST (UTC+10), without daylight saving",
        timestamp_convention="Published SETTLEMENTDATE dispatch label, converted to UTC",
        measurement_convention="Instantaneous MW at the start of the dispatch interval",
        interval_average=False,
        settlement_energy=False,
        source_rows_before_filter=total_rows,
        selected_duids=list(selected) if selected else None,
        gap_filling_applied=False,
        negative_values_clipped=False,
        documentation_url=DOCUMENTATION_ENDPOINT,
        coverage_note=(
            "Scheduled and semi-scheduled units, plus non-scheduled units with SCADA; "
            "not complete distributed generation and not restricted to generator DUIDs"
        ),
    )
    return frame


@dataclass(slots=True)
class AEMOClient:
    """Read public NEMWeb files using the shared bounded HTTP transport.

    No API key is required. Directory listings and current files are transient;
    retain the returned source URL, retrieval date and SHA-256 with your output.
    """

    http: HTTPClient
    maximum_rows: int = 500000
    maximum_uncompressed_bytes: int = 128 * 1024**2
    maximum_members: int = 1000
    maximum_files: int = 5000

    def __post_init__(self) -> None:
        for name in (
            "maximum_rows",
            "maximum_uncompressed_bytes",
            "maximum_members",
            "maximum_files",
        ):
            _positive_integer(getattr(self, name), name)

    def list_files(self, *, archive: bool = False) -> AEMOListing:
        """Discover current interval ZIPs or available daily archive ZIPs.

        Only links to matching files in the requested official directory are
        returned. The provider's archive retention is finite; older files may
        require a different historical source.
        """
        endpoint = ARCHIVE_ENDPOINT if archive else CURRENT_ENDPOINT
        response = self.http.get_text(endpoint, use_cache=False)
        parser = _Links()
        parser.feed(response.value)
        parser.close()
        urls: set[str] = set()
        for link in parser.links:
            candidate = urljoin(endpoint, link)
            try:
                _file_url(candidate)
            except ValueError:
                continue
            if urlsplit(candidate).path.rsplit("/", 1)[0].lower() != (
                urlsplit(endpoint).path.rstrip("/").lower()
            ):
                continue
            urls.add(candidate)
        if len(urls) > self.maximum_files:
            raise RetrievalError("AEMO directory exceeds its file bound")
        if not urls:
            raise RetrievalError("AEMO directory lists no supported dispatch SCADA files")
        return AEMOListing(tuple(sorted(urls)), response.record)

    def fetch_file(self, url: str, *, duids: Sequence[str] | None = None) -> AEMOGeneration:
        """Download and parse one validated interval or daily archive URL."""
        _file_url(url)
        _duids(duids)
        with TemporaryDirectory(prefix="energy-aemo-") as directory:
            path = Path(directory) / "dispatch.zip"
            record = self.http.download_file(url, path)
            frame = parse_dispatch_scada(
                path.read_bytes(),
                duids=duids,
                maximum_rows=self.maximum_rows,
                maximum_uncompressed_bytes=self.maximum_uncompressed_bytes,
                maximum_members=self.maximum_members,
            )
        return AEMOGeneration(frame, record)

    def generation_day(self, day: date, *, duids: Sequence[str] | None = None) -> AEMOGeneration:
        """Read a daily archive (NEM labels 00:05 through the next day's 00:00).

        Missing/expired archives raise an explicit retrieval error. A day is a
        native NEM market date, not a UTC calendar date. No completeness is
        implied when individual unit observations are absent.
        """
        if type(day) is not date or not 1998 <= day.year <= 9998:
            raise ValueError("day must be a date in the AEMO NEM period")
        result = self.fetch_file(
            f"{ARCHIVE_ENDPOINT}PUBLIC_DISPATCHSCADA_{day:%Y%m%d}.zip", duids=duids
        )
        start = pd.Timestamp(day).tz_localize(NEM_TIMEZONE).tz_convert("UTC")
        end = start + pd.Timedelta(days=1)
        if not ((result.frame["timestamp"] > start) & (result.frame["timestamp"] <= end)).all():
            raise RetrievalError("AEMO archive contains dispatch labels outside the requested day")
        result.frame.attrs["nem_day"] = day.isoformat()
        return result
