"""Bounded ESGF STAC discovery with explicit CMIP6 identity and native-file plans.

The STAC index contains datasets; their HTTP assets are native NetCDF files.
Year selection chooses intersecting whole files, never crops, regrids, corrects
calendars or manufactures an hourly weather product. Saved metadata retains the
provider's citation links, identifiers, licenses, units and ensemble identity.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import cast
from urllib.parse import parse_qsl, unquote, urlsplit

from energy_data_retrieval.transport import (
    HTTPClient,
    JSONValue,
    RequestRecord,
    RetrievalError,
    array_value,
    atomic_bytes,
    object_value,
)

_INDEXES = {
    "east": "https://discovery.east.esgf.io",
    "west": "https://discovery.west.esgf.io",
}
CMIP6_INDEX_HOSTS = frozenset({"discovery.east.esgf.io", "discovery.west.esgf.io"})
REFERENCE_IDS = (
    "ascencio_vasquez_2021_thesis",
    "eyring_2016_cmip6",
    "oneill_2016_scenariomip",
    "esgf_stac_access",
    "intake_esgf_cmip6_catalogue_guidance",
    "stac_file_info",
    "cmip6_data_user_guide",
    "cmip6_terms_of_use",
)
CMIP6_DATA_HOSTS = frozenset(
    {
        "dap.ceda.ac.uk",
        "esgf-node.ornl.gov",
        "esgf-data1.llnl.gov",
        "esgf-data2.llnl.gov",
        "esgf-data3.llnl.gov",
        "esgf-data.dkrz.de",
        "esgf3.dkrz.de",
        "esgf.ceda.ac.uk",
        "esgf.ipsl.fr",
        "esgf.nci.org.au",
    }
)
_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}\Z")
_TIME_RANGE = re.compile(r"(\d{4}(?:\d{2}){0,5})-(\d{4}(?:\d{2}){0,5})\Z")
_MAX_PLAN_BYTES = 32 * 1024 * 1024
_FACETS = ("source_id", "experiment_id", "member_id", "table_id", "variable_id", "grid_label")
_DRS_FIELDS = (
    "activity_id",
    "institution_id",
    "source_id",
    "experiment_id",
    "member_id",
    "table_id",
    "variable_id",
    "grid_label",
)


def _json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode("utf-8")


def _integer(value: object, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{label} must be an integer of at least {minimum}")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise RetrievalError(f"CMIP6 metadata omits {label}")
    return value


def _version(value: object) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"v?\d{8}", value):
        raise ValueError("CMIP6 version must be YYYYMMDD or vYYYYMMDD")
    return value.removeprefix("v")


@dataclass(frozen=True, slots=True)
class CMIP6Query:
    """One explicit model/experiment/member/table/variable/grid combination.

    An omitted version resolves the index's latest non-retracted version at
    discovery time. The plan pins that concrete version. Optional inclusive
    years select overlapping native files, whose actual coverage may be wider.
    """

    source_id: str
    experiment_id: str
    member_id: str
    table_id: str
    variable_id: str
    grid_label: str
    institution_id: str | None = None
    activity_id: str | None = None
    version: str | None = None
    start_year: int | None = None
    end_year: int | None = None

    def __post_init__(self) -> None:
        for name in (*_FACETS, "institution_id", "activity_id"):
            value = getattr(self, name)
            if value is None and name not in _FACETS:
                continue
            if not isinstance(value, str) or not _TOKEN.fullmatch(value):
                raise ValueError(f"{name} must be one explicit CMIP6 token, without wildcards")
        if self.version is not None:
            object.__setattr__(self, "version", _version(self.version))
        if (self.start_year is None) != (self.end_year is None):
            raise ValueError("start_year and end_year must be supplied together")
        if self.start_year is not None and self.end_year is not None:
            _integer(self.start_year, "start_year", minimum=1)
            _integer(self.end_year, "end_year", minimum=1)
            if not self.start_year <= self.end_year <= 9999:
                raise ValueError("CMIP6 years must be ordered and within 1..9999")

    def filter(self) -> dict[str, JSONValue]:
        """Return the exact CQL2 JSON filter used by both official STAC indices."""
        clauses: list[JSONValue] = []
        for name in (*_FACETS, "institution_id", "activity_id"):
            value = getattr(self, name)
            if value is not None:
                clauses.append({"op": "=", "args": [{"property": f"cmip6:{name}"}, value]})
        clauses.append({"op": "=", "args": [{"property": "retracted"}, False]})
        clauses.append(
            {"op": "=", "args": [{"property": "version"}, self.version]}
            if self.version is not None
            else {"op": "=", "args": [{"property": "latest"}, True]}
        )
        return {"op": "and", "args": clauses}


@dataclass(frozen=True, slots=True)
class CMIP6File:
    """A pinned native file and the provider checksum required for transfer."""

    dataset_id: str
    filename: str
    url: str
    size_bytes: int
    sha256: str
    start_label: str | None
    end_label: str | None

    @property
    def relative_path(self) -> str:
        folder = hashlib.sha256(self.dataset_id.encode()).hexdigest()
        return f"files/{folder}/{self.filename}"


@dataclass(frozen=True, slots=True)
class CMIP6Plan:
    """Portable discovery snapshot, including the complete selected STAC items."""

    query: CMIP6Query
    index: str
    collection: str
    created_at_utc: str
    datasets: tuple[dict[str, JSONValue], ...]
    requests: tuple[RequestRecord, ...]
    files: tuple[CMIP6File, ...]

    @property
    def total_size_bytes(self) -> int:
        return sum(file.size_bytes for file in self.files)

    def _payload(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "source": "ESGF CMIP6 STAC",
            "index": self.index,
            "collection": self.collection,
            "created_at_utc": self.created_at_utc,
            "query": asdict(self.query),
            "datasets": self.datasets,
            "requests": [asdict(record) for record in self.requests],
            "files": [asdict(file) | {"relative_path": file.relative_path} for file in self.files],
            "total_size_bytes": self.total_size_bytes,
            "search_complete_for_index": True,
            "global_coverage_claimed": False,
            "temporal_selection": "whole_file_overlap_by_year",
            "native_calendars_and_units_preserved": True,
            "reference_ids": REFERENCE_IDS,
        }

    @property
    def sha256(self) -> str:
        return hashlib.sha256(_json_bytes(self._payload())).hexdigest()

    def as_dict(self) -> dict[str, object]:
        """Return an independent JSON-safe payload with its SHA-256 fingerprint."""
        return cast(dict[str, object], json.loads(_json_bytes(self._payload()))) | {
            "plan_sha256": self.sha256
        }


def _safe_file_url(value: object, filename: str) -> str:
    url = _text(value, "asset href")
    parsed = urlsplit(url)
    path = unquote(parsed.path)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in (None, 443)
        or parsed.query
        or parsed.fragment
        or "\\" in path
        or any(part in {".", ".."} for part in path.split("/"))
        or path.rsplit("/", 1)[-1] != filename
        or any(ord(character) < 32 for character in url)
    ):
        raise RetrievalError("CMIP6 file needs a query-free HTTPS URL matching its native filename")
    return url


def _checksum(value: object) -> str:
    # STAC file extension: 0x12 = SHA-256, 0x20 = 32-byte digest, then digest.
    if not isinstance(value, str) or not re.fullmatch(r"1220[a-fA-F0-9]{64}", value):
        raise RetrievalError(
            "CMIP6 file:checksum must be a SHA-256 hexadecimal multihash (1220...)"
        )
    return value[4:].lower()


def _time_label(value: str) -> tuple[int, ...]:
    parts = (int(value[:4]), *(int(value[index : index + 2]) for index in range(4, len(value), 2)))
    ranges = ((1, 9999), (1, 12), (1, 31), (0, 23), (0, 59), (0, 59))
    if not all(low <= number <= high for number, (low, high) in zip(parts, ranges, strict=False)):
        raise RetrievalError("CMIP6 filename contains an invalid calendar label")
    return parts


def _native_filename(filename: str, query: CMIP6Query) -> tuple[str | None, str | None]:
    prefix = "_".join(
        getattr(query, field)
        for field in (
            "variable_id",
            "table_id",
            "source_id",
            "experiment_id",
            "member_id",
            "grid_label",
        )
    )
    if filename == prefix + ".nc":
        if not query.table_id.lower().endswith("fx"):
            raise RetrievalError("A non-fixed CMIP6 table requires a native filename time range")
        if query.start_year is not None:
            raise RetrievalError(
                "A year selection cannot be applied to a fixed/time-unlabelled file"
            )
        return None, None
    if not filename.startswith(prefix + "_") or not filename.endswith(".nc"):
        raise RetrievalError("CMIP6 filename disagrees with the requested dataset facets")
    timerange = filename[len(prefix) + 1 : -3]
    match = _TIME_RANGE.fullmatch(timerange)
    if match is None:
        raise RetrievalError("Unsupported CMIP6 native filename time range")
    start, end = match.groups()
    if len(start) != len(end) or _time_label(start) > _time_label(end):
        raise RetrievalError("CMIP6 filename has an unordered or inconsistent time range")
    return start, end


def _dataset_files(item: dict[str, JSONValue], query: CMIP6Query) -> tuple[CMIP6File, ...]:
    identifier = _text(item.get("id"), "dataset id")
    fields = identifier.split(".")
    if (
        item.get("type") != "Feature"
        or len(fields) != 10
        or fields[0] != "CMIP6"
        or not all(_TOKEN.fullmatch(value) for value in fields[1:])
        or not fields[-1].startswith("v")
    ):
        raise RetrievalError("CMIP6 item needs a versioned CMIP6 dataset identifier")
    if _text(item.get("collection"), "collection").casefold() != "cmip6":
        raise RetrievalError("STAC response belongs to a different project")
    properties = object_value(item.get("properties"))
    version = _version(properties.get("version"))
    if fields[-1] != "v" + version or properties.get("retracted") is not False:
        raise RetrievalError("CMIP6 dataset version is inconsistent or retracted")
    if query.version is not None:
        if version != query.version:
            raise RetrievalError("CMIP6 returned a different version from the pinned request")
    elif properties.get("latest") is not True:
        raise RetrievalError("CMIP6 returned a non-latest dataset for a latest-version request")
    for name, from_id in zip(_DRS_FIELDS, fields[1:-1], strict=True):
        value = properties.get(f"cmip6:{name}")
        agrees = (
            from_id in value
            if name == "activity_id" and isinstance(value, list)
            else value == from_id
        )
        if not agrees or (getattr(query, name) is not None and getattr(query, name) != from_id):
            raise RetrievalError(
                f"CMIP6 returned inconsistent or unexpected {name}; inspect the catalogue"
            )
    if properties.get("cmip6:mip_era") != "CMIP6":
        raise RetrievalError("STAC item does not identify the CMIP6 project")
    member = _text(properties.get("cmip6:member_id"), "member_id")
    variant = properties.get("cmip6:variant_label")
    sub_experiment = properties.get("cmip6:sub_experiment_id")
    if isinstance(variant, str) and isinstance(sub_experiment, str):
        expected_member = variant if sub_experiment == "none" else f"{sub_experiment}-{variant}"
        if member != expected_member:
            raise RetrievalError("CMIP6 member_id disagrees with variant/sub-experiment metadata")
    assets = object_value(item.get("assets"))
    if len(assets) > 10_000:
        raise RetrievalError("CMIP6 dataset exceeds the 10,000-asset inspection limit")
    files = []
    native_count = 0
    for filename, raw in sorted(assets.items()):
        asset = object_value(raw)
        if asset.get("description") != "HTTPServer Link":
            continue
        native_count += 1
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,250}\.nc", filename):
            raise RetrievalError("CMIP6 asset key must be a safe native NetCDF filename")
        start, end = _native_filename(filename, query)
        if (
            start is not None
            and end is not None
            and query.start_year is not None
            and query.end_year is not None
            and (int(end[:4]) < query.start_year or int(start[:4]) > query.end_year)
        ):
            continue
        files.append(
            CMIP6File(
                identifier,
                filename,
                _safe_file_url(asset.get("href"), filename),
                _integer(asset.get("file:size"), "CMIP6 file:size", minimum=1),
                _checksum(asset.get("file:checksum")),
                start,
                end,
            )
        )
    if native_count == 0:
        raise RetrievalError("CMIP6 dataset has no native HTTPServer file assets")
    return tuple(files)


def _build_plan(
    query: CMIP6Query,
    index: str,
    collection: str,
    created_at_utc: str,
    datasets: tuple[dict[str, JSONValue], ...],
    requests: tuple[RequestRecord, ...],
) -> CMIP6Plan:
    if index not in _INDEXES or collection.casefold() != "cmip6":
        raise ValueError("CMIP6 plan needs an official east/west index and CMIP6 collection")
    timestamp = datetime.fromisoformat(created_at_utc)
    if timestamp.tzinfo is None or timestamp.utcoffset() != UTC.utcoffset(timestamp):
        raise ValueError("CMIP6 plan creation time must carry UTC offset")
    if not 1 <= len(datasets) <= 1000:
        raise RetrievalError(
            "No matching CMIP6 datasets, or the 1000-dataset plan limit was exceeded"
        )
    identities: set[str] = set()
    files: list[CMIP6File] = []
    for item in datasets:
        identifier = _text(item.get("id"), "dataset id")
        base = identifier.rsplit(".", 1)[0]
        if base in identities:
            raise RetrievalError("CMIP6 search repeated a dataset or returned ambiguous versions")
        identities.add(base)
        files.extend(_dataset_files(item, query))
    if not 1 <= len(files) <= 10_000:
        raise RetrievalError(
            "No CMIP6 files overlap the requested years, or the file limit was exceeded"
        )
    if len({file.relative_path for file in files}) != len(files):
        raise RetrievalError("CMIP6 file destinations collide")
    return CMIP6Plan(query, index, collection, created_at_utc, datasets, requests, tuple(files))


def _next_token(
    payload: dict[str, JSONValue], endpoint: str, parameters: dict[str, str]
) -> str | None:
    next_links = [
        object_value(link)
        for link in array_value(payload.get("links"))
        if object_value(link).get("rel") == "next"
    ]
    if not next_links:
        return None
    if len(next_links) != 1:
        raise RetrievalError("CMIP6 search supplied ambiguous pagination links")
    link = next_links[0]
    target = urlsplit(_text(link.get("href"), "next-page URL"))
    expected = urlsplit(endpoint)
    if (
        link.get("method", "GET") != "GET"
        or "body" in link
        or target.scheme != "https"
        or target.netloc != expected.netloc
        or target.path != expected.path
        or target.fragment
    ):
        raise RetrievalError("CMIP6 pagination must remain on the chosen HTTPS search endpoint")
    pairs = parse_qsl(target.query, keep_blank_values=True, strict_parsing=True)
    values = dict(pairs)
    if len(values) != len(pairs) or any(
        key != "token" and parameters.get(key) != value for key, value in pairs
    ):
        raise RetrievalError("CMIP6 pagination changed the original request filters")
    token = values.get("token", "")
    if not token or len(token) > 8192:
        raise RetrievalError("CMIP6 pagination requires a bounded nonempty continuation token")
    return token


@dataclass(slots=True)
class CMIP6Client:
    """Search one explicitly chosen ESGF index without collecting an unbounded archive."""

    http: HTTPClient
    index: str = "east"
    page_size: int = 20
    maximum_datasets: int = 100
    maximum_files: int = 1000

    def __post_init__(self) -> None:
        if self.index not in _INDEXES:
            raise ValueError("CMIP6 index must be east or west")
        for value, label, maximum in (
            (self.page_size, "page_size", 100),
            (self.maximum_datasets, "maximum_datasets", 1000),
            (self.maximum_files, "maximum_files", 10_000),
        ):
            if _integer(value, label, minimum=1) > maximum:
                raise ValueError(f"{label} must be no greater than {maximum}")

    def search(self, query: CMIP6Query) -> CMIP6Plan:
        """Complete a bounded search, rejecting truncation and mismatching facets.

        East and west currently spell the collection ID differently. Resolve it
        from the catalogue, and explicitly retain CMIP6 even if CMIP7 becomes the
        service default. A completed search covers only this chosen index.
        """
        root = _INDEXES[self.index]
        response = self.http.get_json(root + "/collections", use_cache=False)
        catalog = object_value(response.value)
        collections = [object_value(item) for item in array_value(catalog.get("collections"))]
        matching = [
            item["id"]
            for item in collections
            if isinstance(item.get("id"), str) and str(item["id"]).casefold() == "cmip6"
        ]
        if len(matching) != 1:
            raise RetrievalError("The chosen ESGF index does not advertise one CMIP6 collection")
        collection = _text(matching[0], "CMIP6 collection id")
        parameters = {
            "collections": collection,
            "limit": str(self.page_size),
            "filter-lang": "cql2-json",
            "filter": _json_bytes(query.filter()).decode(),
        }
        endpoint = root + "/search"
        requests = [response.record]
        datasets: list[dict[str, JSONValue]] = []
        seen_tokens: set[str] = set()
        seen_ids: set[str] = set()
        expected_total: int | None = None
        file_count = 0
        metadata_bytes = 0
        token: str | None = None
        for _ in range(self.maximum_datasets + 1):
            response = self.http.get_json(
                endpoint,
                parameters | ({"token": token} if token else {}),
                use_cache=False,
                public_pagination_token=True,
            )
            requests.append(response.record)
            payload = object_value(response.value)
            if payload.get("type") != "FeatureCollection":
                raise RetrievalError("CMIP6 search did not return a STAC FeatureCollection")
            page = [object_value(item) for item in array_value(payload.get("features"))]
            if len(page) > self.page_size:
                raise RetrievalError("CMIP6 index exceeded the requested page-size bound")
            if "numberReturned" in payload:
                returned = _integer(payload["numberReturned"], "CMIP6 numberReturned")
                if returned != len(page):
                    raise RetrievalError("CMIP6 page count disagrees with its records")
            if "numberMatched" in payload:
                count = _integer(payload["numberMatched"], "CMIP6 numberMatched")
                if count > self.maximum_datasets:
                    raise RetrievalError(
                        "CMIP6 search exceeds maximum_datasets; narrow the request"
                    )
                if expected_total is not None and count != expected_total:
                    raise RetrievalError(
                        "CMIP6 catalogue changed during pagination; repeat discovery"
                    )
                expected_total = count
            for item in page:
                identifier = _text(item.get("id"), "dataset id")
                if identifier in seen_ids:
                    raise RetrievalError("CMIP6 pagination repeated a dataset")
                seen_ids.add(identifier)
                file_count += len(_dataset_files(item, query))
                metadata_bytes += len(_json_bytes(item))
                if len(seen_ids) > self.maximum_datasets or file_count > self.maximum_files:
                    raise RetrievalError("CMIP6 search exceeds the configured dataset/file limit")
                if metadata_bytes > _MAX_PLAN_BYTES:
                    raise RetrievalError("CMIP6 dataset metadata exceeds the 32 MiB plan limit")
                datasets.append(item)
            token = _next_token(payload, endpoint, parameters)
            if token is None:
                if expected_total is not None and len(datasets) != expected_total:
                    raise RetrievalError(
                        "CMIP6 pagination ended before all matching datasets arrived"
                    )
                return _build_plan(
                    query,
                    self.index,
                    collection,
                    datetime.now(UTC).isoformat(),
                    tuple(datasets),
                    tuple(requests),
                )
            if not page or token in seen_tokens:
                raise RetrievalError("CMIP6 search supplied an empty or cyclic continuation page")
            seen_tokens.add(token)
        raise RetrievalError("CMIP6 search exceeded its bounded page count")


def _validated_plan(plan: CMIP6Plan) -> CMIP6Plan:
    checked = _build_plan(
        plan.query,
        plan.index,
        plan.collection,
        plan.created_at_utc,
        plan.datasets,
        plan.requests,
    )
    if checked.files != plan.files:
        raise ValueError("CMIP6 plan file records disagree with their saved STAC metadata")
    return checked


def save_plan(plan: CMIP6Plan, path: Path) -> None:
    """Write a new portable JSON plan; never replace an earlier discovery snapshot."""
    _validated_plan(plan)
    if path.exists() or path.is_symlink():
        raise ValueError("CMIP6 plan already exists; choose a new path for a new discovery")
    data = _json_bytes(plan.as_dict())
    if len(data) > _MAX_PLAN_BYTES:
        raise ValueError("CMIP6 plan exceeds the 32 MiB manifest limit; narrow the request")
    atomic_bytes(path, data)


def load_plan(path: Path) -> CMIP6Plan:
    """Validate a bounded JSON snapshot, its fingerprint, metadata and file paths."""
    if path.stat().st_size > _MAX_PLAN_BYTES:
        raise ValueError("CMIP6 plan exceeds the 32 MiB manifest limit")
    saved = json.loads(path.read_bytes())
    if not isinstance(saved, dict):
        raise ValueError("CMIP6 plan must be a JSON object")
    payload = {key: value for key, value in saved.items() if key != "plan_sha256"}
    if saved.get("plan_sha256") != hashlib.sha256(_json_bytes(payload)).hexdigest():
        raise ValueError("CMIP6 plan fingerprint does not match its contents")
    try:
        query = CMIP6Query(**saved["query"])
        requests = tuple(RequestRecord(**record) for record in saved["requests"])
        datasets = tuple(object_value(item) for item in saved["datasets"])
        plan = _build_plan(
            query, saved["index"], saved["collection"], saved["created_at_utc"], datasets, requests
        )
    except (KeyError, TypeError) as error:
        raise ValueError("CMIP6 plan has an unsupported or malformed schema") from error
    if plan.as_dict() != saved:
        raise ValueError("CMIP6 plan schema or derived file metadata is inconsistent")
    return plan


def download_plan(
    plan: CMIP6Plan,
    output: Path,
    http: HTTPClient,
    *,
    maximum_total_bytes: int = 2 * 1024**3,
) -> dict[str, object]:
    """Download pinned files sequentially with preflight bounds and verified restart.

    The supplied HTTP client's host allowlist and per-file byte limit apply.
    Every source size and SHA-256 must agree before a native file is published.
    Existing individual downloads are reused only after full hash verification.
    """
    _validated_plan(plan)
    _integer(maximum_total_bytes, "maximum_total_bytes", minimum=1)
    if plan.total_size_bytes > maximum_total_bytes:
        raise ValueError(
            "CMIP6 plan exceeds maximum_total_bytes; narrow or explicitly raise the limit"
        )
    for file in plan.files:
        if urlsplit(file.url).hostname not in http.allowed_hosts:
            raise ValueError(
                "CMIP6 asset host is not approved; inspect the plan before allowing it"
            )
        if file.size_bytes > http.config.maximum_response_bytes:
            raise ValueError("CMIP6 file exceeds the HTTP per-file byte limit")
    if output.is_symlink():
        raise ValueError("CMIP6 output directory must not be a symlink")
    output.mkdir(parents=True, exist_ok=True)
    plan_path = output / "plan.json"
    if plan_path.exists():
        if plan_path.is_symlink() or load_plan(plan_path).sha256 != plan.sha256:
            raise ValueError("CMIP6 output belongs to a different or changed discovery plan")
    else:
        if any(output.iterdir()):
            raise ValueError("CMIP6 output is nonempty without its discovery plan")
        save_plan(plan, plan_path)
    downloaded: list[dict[str, object]] = []
    reused = 0
    for file in plan.files:
        path = output / file.relative_path
        if any(parent.is_symlink() for parent in (path.parent, path.parent.parent)):
            raise ValueError("CMIP6 output contains a symlinked data directory")
        if path.is_symlink() or path.with_suffix(path.suffix + ".download.json").is_symlink():
            raise ValueError("CMIP6 output contains a symlinked file or checkpoint")
        record = http.download_file(
            file.url,
            path,
            expected_sha256=file.sha256,
            expected_size_bytes=file.size_bytes,
        )
        reused += int(record.cache_hit)
        downloaded.append(
            {
                "dataset_id": file.dataset_id,
                "relative_path": file.relative_path,
                "url": file.url,
                "size_bytes": record.size_bytes,
                "sha256": record.sha256,
                "retrieved_at_utc": record.retrieved_at_utc,
            }
        )
    manifest = {
        "schema_version": 1,
        "source": "ESGF CMIP6 STAC",
        "plan_sha256": plan.sha256,
        "file_count": len(downloaded),
        "size_bytes": plan.total_size_bytes,
        "files": downloaded,
        "native_calendars_and_units_preserved": True,
        "spatial_or_temporal_subsetting_applied": False,
    }
    manifest_path = output / "manifest.json"
    if manifest_path.is_symlink():
        raise ValueError("CMIP6 output manifest must not be a symlink")
    if manifest_path.exists():
        if json.loads(manifest_path.read_bytes()) != manifest:
            raise ValueError("CMIP6 output manifest differs from the verified download records")
    else:
        atomic_bytes(manifest_path, _json_bytes(manifest))
    return {
        "output_path": str(output),
        "manifest_path": str(manifest_path),
        "plan_sha256": plan.sha256,
        "file_count": len(downloaded),
        "size_bytes": plan.total_size_bytes,
        "reused_files": reused,
    }
