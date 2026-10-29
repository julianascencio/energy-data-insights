"""Native CDS downloads, immutable requests and checksum-verified local reuse.

The official SDK owns authentication, queue polling and transfer retries. Files
retain source units/calendars/intervals; this adapter does not normalize weather.
"""

from __future__ import annotations

import importlib
import json
import math
import re
import shutil
import tempfile
import warnings
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Protocol, cast

from energy_data_retrieval.storage import fingerprint, sha256_file
from energy_data_retrieval.transport import JSONValue, RetrievalError

CDS_URL = "https://cds.climate.copernicus.eu/api"
REFERENCE_IDS = ("ascencio_vasquez_2021_thesis", "copernicus_cds_api")
MAX_REQUEST_BYTES = 1_048_576
_SCHEMA = "energy-cds-download-v1"
_SECRET_FIELDS = {
    "key",
    "token",
    "api_key",
    "apikey",
    "access_token",
    "authorization",
    "password",
    "secret",
    "client_secret",
    "url",
    "headers",
}


def _validate(value: object, depth: int = 0) -> None:
    if depth > 12:
        raise ValueError("CDS request nesting exceeds 12 levels")
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", key):
                raise ValueError("CDS request keys must be parameter names")
            if key.lower().replace("-", "_") in _SECRET_FIELDS:
                raise ValueError("Credentials and transport settings do not belong in CDS requests")
            _validate(item, depth + 1)
    elif isinstance(value, list):
        for item in value:
            _validate(item, depth + 1)
    elif type(value) not in (str, int, float, bool, type(None)):
        raise ValueError("CDS request values must be JSON values")
    elif isinstance(value, float) and not math.isfinite(value):
        raise ValueError("CDS request numbers must be finite")


@dataclass(frozen=True, slots=True, init=False)
class CDSRequest:
    """One dataset slug and the selection copied from its CDS download form.

    Dataset-specific validity and permissions are checked by CDS. The local
    boundary validates JSON and excludes credential/transport fields. The stored
    canonical JSON cannot be changed by later mutation of the caller's dictionary.
    """

    dataset: str
    _selection_json: str

    def __init__(self, dataset: str, selection: Mapping[str, JSONValue]) -> None:
        if not isinstance(dataset, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,127}", dataset):
            raise ValueError("Use the CDS dataset slug, not a URL or path")
        if not isinstance(selection, Mapping) or not selection:
            raise ValueError("CDS selection must be a nonempty JSON object")
        values = dict(selection)
        _validate(values)
        encoded = json.dumps(values, sort_keys=True, allow_nan=False, separators=(",", ":"))
        if len(encoded.encode()) > MAX_REQUEST_BYTES:
            raise ValueError("CDS request exceeds 1 MiB")
        object.__setattr__(self, "dataset", dataset)
        object.__setattr__(self, "_selection_json", encoded)

    @property
    def selection(self) -> dict[str, JSONValue]:
        return json.loads(self._selection_json)

    def as_dict(self) -> dict[str, JSONValue]:
        return {"endpoint": CDS_URL, "dataset": self.dataset, "selection": self.selection}

    @property
    def sha256(self) -> str:
        return fingerprint(self.as_dict())

    @property
    def reference_ids(self) -> tuple[str, ...]:
        references = {
            "reanalysis-era5-single-levels": ("hersbach_2020_era5", "era5_single_levels"),
            "reanalysis-era5-single-levels-monthly-means": (
                "hersbach_2020_era5",
                "era5_single_levels_monthly",
            ),
        }
        return (*REFERENCE_IDS, *references.get(self.dataset, ()))


class _Result(Protocol):
    @property
    def content_length(self) -> int: ...
    def download(self, target: str) -> object: ...


class _SDK(Protocol):
    def retrieve(self, name: str, request: dict[str, JSONValue]) -> _Result: ...


def _quiet(*args: object, **kwargs: object) -> None:
    """SDK messages can include a token or signed result URL; do not forward them."""


def _sdk_version() -> str | None:
    try:
        return version("cdsapi")
    except PackageNotFoundError:
        return None


def _file_format(path: Path) -> str:
    with path.open("rb") as stream:
        prefix = stream.read(8)
    if prefix.startswith(b"GRIB"):
        return "grib"
    if prefix.startswith((b"CDF\x01", b"CDF\x02", b"CDF\x05")):
        return "nc"
    if prefix.startswith(b"\x89HDF\r\n\x1a\n"):
        return "h5"
    if prefix.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
        return "zip"
    if prefix.startswith(b"\x1f\x8b"):
        return "gz"
    return "bin"


@dataclass(frozen=True, slots=True)
class CDSDownload:
    path: Path
    manifest_path: Path
    sha256: str
    bytes: int
    reused: bool


def _existing(directory: Path, request: CDSRequest) -> CDSDownload | None:
    if not directory.exists():
        return None
    try:
        manifest_path = directory / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        artifact = manifest["artifact"]
        filename = artifact["filename"]
        if filename not in {
            f"download.{suffix}" for suffix in ("nc", "h5", "grib", "zip", "gz", "bin")
        }:
            raise ValueError
        path = directory / filename
        if (
            manifest["schema"] != _SCHEMA
            or manifest["complete"] is not True
            or manifest["request"] != request.as_dict()
            or manifest["request_sha256"] != request.sha256
            or artifact["bytes"] != path.stat().st_size
            or artifact["sha256"] != sha256_file(path)
        ):
            raise ValueError
        return CDSDownload(path, manifest_path, artifact["sha256"], artifact["bytes"], True)
    except (OSError, ValueError, TypeError, KeyError):
        raise RetrievalError(
            "Existing CDS output is incomplete or its request/checksum differs"
        ) from None


class CDSClient:
    """Lazy official SDK, sequential transfers and verified completed-download reuse.

    ``timeout_seconds`` is a network timeout, not a deadline for CDS's queue.
    ``maximum_download_bytes`` checks advertised size before transfer and actual
    size afterwards; the SDK owns streaming. No token is accepted in request JSON.
    ``sdk`` permits offline tests or an explicitly configured compatible client.
    """

    def __init__(
        self,
        *,
        timeout_seconds: int = 60,
        attempts: int = 3,
        maximum_download_bytes: int = 1_073_741_824,
        sdk: _SDK | None = None,
    ) -> None:
        for value, low, high, name in (
            (timeout_seconds, 1, 600, "timeout_seconds"),
            (attempts, 1, 10, "attempts"),
            (maximum_download_bytes, 1, 10 * 1024**3, "maximum_download_bytes"),
        ):
            if type(value) is not int or not low <= value <= high:
                raise ValueError(f"{name} must be an integer in [{low}, {high}]")
        self.timeout_seconds = timeout_seconds
        self.attempts = attempts
        self.maximum_download_bytes = maximum_download_bytes
        self._sdk = sdk

    def _client(self) -> _SDK:
        if self._sdk is None:
            try:
                module = importlib.import_module("cdsapi")
            except ModuleNotFoundError:
                raise ImportError(
                    "Install energy-data-retrieval[cds] to download CDS data"
                ) from None
            try:
                # The SDK's optional portal-announcement fetch emits raw exception
                # text through warnings instead of its callbacks. Keep that
                # advisory warning private too; actual retrieval failures raise.
                with warnings.catch_warnings():
                    warnings.filterwarnings(
                        "ignore", category=UserWarning, module=r"ecmwf\.datastores\.client"
                    )
                    self._sdk = cast(
                        _SDK,
                        module.Client(
                            url=CDS_URL,
                            verify=True,
                            quiet=True,
                            debug=False,
                            progress=False,
                            timeout=self.timeout_seconds,
                            retry_max=self.attempts,
                            sleep_max=30,
                            info_callback=_quiet,
                            warning_callback=_quiet,
                            error_callback=_quiet,
                            debug_callback=_quiet,
                        ),
                    )
            except Exception:
                raise RetrievalError(
                    "CDS client setup failed. Configure CDSAPI_KEY or ~/.cdsapirc with a "
                    "personal access token; see https://cds.climate.copernicus.eu/how-to-api"
                ) from None
        return self._sdk

    def download(self, request: CDSRequest, output: Path) -> CDSDownload:
        """Store one native result and its provenance in a request-hash directory.

        Matching complete artifacts are reused after hashing, without SDK imports
        or credential reads. Failed transfers remove their temporary directory.
        Interrupted remote jobs are not persisted/reconnected: retrying may submit
        a new job. Completed earlier monthly requests remain independently reusable.
        """
        directory = Path(output) / request.dataset / request.sha256
        cached = _existing(directory, request)
        if cached is not None:
            return cached
        client = self._client()
        directory.parent.mkdir(parents=True, exist_ok=True)
        temporary = Path(tempfile.mkdtemp(prefix=".cds-", dir=directory.parent))
        try:
            raw = temporary / "download.partial"
            try:
                result = client.retrieve(request.dataset, request.selection)
                size = result.content_length
                if type(size) is not int or not 0 < size <= self.maximum_download_bytes:
                    raise RetrievalError(
                        "CDS advertised result size is empty, unknown or exceeds limit"
                    )
                result.download(str(raw))
            except RetrievalError:
                raise
            except Exception:
                raise RetrievalError(
                    "CDS retrieval failed. Check the dataset selection, token, accepted licence "
                    "and CDS job status. Provider messages and signed URLs are not exposed."
                ) from None
            if not raw.is_file() or raw.stat().st_size != size:
                raise RetrievalError(
                    "CDS downloaded size does not match the advertised result size"
                )
            suffix = _file_format(raw)
            filename = f"download.{suffix}"
            path = temporary / filename
            raw.rename(path)
            digest = sha256_file(path)
            manifest = {
                "schema": _SCHEMA,
                "complete": True,
                "retrieved_at": datetime.now(UTC).isoformat(),
                "request": request.as_dict(),
                "request_sha256": request.sha256,
                "artifact": {
                    "filename": filename,
                    "bytes": size,
                    "sha256": digest,
                    "format_detected_from_signature": suffix,
                },
                "cdsapi_version": _sdk_version(),
                "dataset_url": f"https://cds.climate.copernicus.eu/datasets/{request.dataset}",
                "reference_ids": list(request.reference_ids),
                "processing": "Native bytes; no extraction, unit conversion or timestamp changes",
                "version_note": "A request hash does not pin the upstream dataset vintage; "
                "retrieval time and artifact hash identify this local download.",
            }
            (temporary / "manifest.json").write_text(
                json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8"
            )
            # A competing completed run has a nonempty directory, so rename fails
            # without overwriting it. There is no shared mutable cache index.
            temporary.rename(directory)
            return CDSDownload(
                directory / filename, directory / "manifest.json", digest, size, False
            )
        finally:
            shutil.rmtree(temporary, ignore_errors=True)
