"""Bounded HTTP reads with source allowlists, retries and public-only caching."""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import re
import tempfile
import threading
import time
from collections.abc import Callable, Generator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import cast
from urllib.parse import quote, quote_plus, urlsplit

import httpx

type JSONValue = bool | int | float | str | list[JSONValue] | dict[str, JSONValue] | None

_SECRET_NAMES = frozenset(
    {"user_key", "token", "api_key", "apikey", "access_token", "authorization", "password"}
)
_RETRY_STATUSES = frozenset({408, 429, 500, 502, 503, 504})


_ACTIVE_SECRETS: ContextVar[tuple[str, ...]] = ContextVar("retrieval_secrets", default=())
_QUERY_SECRET = re.compile(
    r"([?&](?:user_key|token|api_key|apikey|access_token|authorization|password)=)[^&\s\"']+",
    re.IGNORECASE,
)
_QUERY_SECRET_WITH_PUBLIC_CURSOR = re.compile(
    r"([?&](?:user_key|api_key|apikey|access_token|authorization|password)=)[^&\s\"']+",
    re.IGNORECASE,
)


def _redact_text(
    text: str, secrets: tuple[str, ...], *, public_pagination_token: bool = False
) -> str:
    for secret in secrets:
        for spelling in {secret, quote(secret, safe=""), quote_plus(secret, safe="")}:
            text = text.replace(spelling, "[REDACTED]")
    pattern = _QUERY_SECRET_WITH_PUBLIC_CURSOR if public_pagination_token else _QUERY_SECRET
    return pattern.sub(r"\1[REDACTED]", text)


def _redact_value(
    value: JSONValue, secrets: tuple[str, ...], *, public_pagination_token: bool = False
) -> JSONValue:
    if isinstance(value, str):
        return _redact_text(value, secrets, public_pagination_token=public_pagination_token)
    if isinstance(value, list):
        return [
            _redact_value(item, secrets, public_pagination_token=public_pagination_token)
            for item in value
        ]
    if isinstance(value, dict):
        return {
            _redact_text(
                key, secrets, public_pagination_token=public_pagination_token
            ): _redact_value(item, secrets, public_pagination_token=public_pagination_token)
            for key, item in value.items()
        }
    return value


class _SecretLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = _redact_text(record.getMessage(), _ACTIVE_SECRETS.get())
        record.args = ()
        return True


@contextmanager
def _secret_scope(secrets: tuple[str, ...]) -> Generator[None, None, None]:
    token = _ACTIVE_SECRETS.set(secrets)
    try:
        yield
    finally:
        _ACTIVE_SECRETS.reset(token)


class RetrievalError(RuntimeError):
    """Sanitized retrieval failure; never contains a credential-bearing URL."""


@dataclass(frozen=True, slots=True)
class HTTPConfig:
    """Finite resource and retry limits, shared by all sources."""

    timeout_seconds: float = 45.0
    attempts: int = 4
    retry_base_seconds: float = 1.0
    maximum_retry_seconds: float = 60.0
    minimum_interval_seconds: float = 0.25
    maximum_response_bytes: int = 64 * 1024 * 1024
    cache_ttl_seconds: float = 3600.0

    def __post_init__(self) -> None:
        values = (
            self.timeout_seconds,
            self.retry_base_seconds,
            self.maximum_retry_seconds,
            self.minimum_interval_seconds,
            self.cache_ttl_seconds,
        )
        if not all(math.isfinite(value) and value >= 0 for value in values):
            raise ValueError("HTTP durations must be finite and nonnegative")
        if self.timeout_seconds == 0 or not 1 <= self.attempts <= 10:
            raise ValueError("Positive timeout and 1-10 attempts are required")
        if self.maximum_response_bytes < 1:
            raise ValueError("A positive response byte limit is required")


@dataclass(frozen=True, slots=True)
class RequestRecord:
    """Non-secret provenance for the exact stored, sanitized response bytes."""

    endpoint: str
    parameters: dict[str, str]
    retrieved_at_utc: str
    sha256: str
    size_bytes: int
    cache_hit: bool = False


@dataclass(frozen=True, slots=True)
class JSONResponse:
    value: JSONValue
    record: RequestRecord


@dataclass(frozen=True, slots=True)
class TextResponse:
    """Public UTF-8 response with a hash of its exact decoded HTTP entity bytes."""

    value: str
    record: RequestRecord


def atomic_bytes(path: Path, data: bytes) -> None:
    """Replace one file atomically; failed writes never publish a partial file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def object_value(value: JSONValue) -> dict[str, JSONValue]:
    if not isinstance(value, dict):
        raise RetrievalError("Expected a JSON object")
    return value


def array_value(value: JSONValue) -> list[JSONValue]:
    if not isinstance(value, list):
        raise RetrievalError("Expected a JSON array")
    return value


def _reject_nonfinite(value: str) -> None:
    raise ValueError(f"Non-finite JSON number: {value}")


def _decode(body: bytes) -> JSONValue:
    try:
        return cast(JSONValue, json.loads(body, parse_constant=_reject_nonfinite))
    except (ValueError, UnicodeDecodeError):
        raise RetrievalError("Source returned invalid JSON") from None


class HTTPClient:
    """An HTTPS GET transport with a fixed host allowlist and no redirects.

    Authentication must be passed separately through ``secrets``. Authenticated
    responses are never read from or written to the public response cache.
    Supply an httpx transport for offline tests, rather than a preauthenticated
    client. This ensures authorization cannot silently bypass cache isolation.
    """

    def __init__(
        self,
        allowed_hosts: frozenset[str],
        *,
        config: HTTPConfig | None = None,
        cache_directory: Path | None = None,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if not allowed_hosts:
            raise ValueError("At least one approved host is required")
        self.config = config or HTTPConfig()
        self.allowed_hosts = allowed_hosts
        self.cache_directory = cache_directory
        self._sleep = sleep
        self._rate_lock = threading.Lock()
        self._next_request = 0.0
        for name in (
            "httpx",
            "httpcore.connection",
            "httpcore.http11",
            "httpcore.http2",
            "httpcore.proxy",
        ):
            logger = logging.getLogger(name)
            if not any(isinstance(item, _SecretLogFilter) for item in logger.filters):
                logger.addFilter(_SecretLogFilter())
        self._client = httpx.Client(
            transport=transport,
            timeout=self.config.timeout_seconds,
            follow_redirects=False,
            trust_env=False,
            limits=httpx.Limits(max_connections=8, max_keepalive_connections=4),
            headers={"User-Agent": "energy-data-insights/0.1", "Accept": "application/json"},
        )

    def __enter__(self) -> HTTPClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def _wait_for_slot(self) -> None:
        with self._rate_lock:
            now = time.monotonic()
            wait = max(0.0, self._next_request - now)
            self._next_request = max(now, self._next_request) + self.config.minimum_interval_seconds
        if wait:
            self._sleep(wait)

    def _retry_delay(self, response: httpx.Response | None, attempt: int) -> float:
        delay = self.config.retry_base_seconds * (2**attempt)
        if response is not None:
            value = response.headers.get("retry-after", "")
            try:
                requested = float(value)
            except ValueError:
                try:
                    requested = (parsedate_to_datetime(value) - datetime.now(UTC)).total_seconds()
                except (TypeError, ValueError, OverflowError):
                    requested = 0.0
            if math.isfinite(requested):
                delay = max(delay, requested)
        return min(self.config.maximum_retry_seconds, max(0.0, delay))

    def download_file(
        self,
        endpoint: str,
        path: Path,
        *,
        expected_sha256: str | None = None,
        expected_size_bytes: int | None = None,
    ) -> RequestRecord:
        """Stream one public export to disk with verified whole-file restart semantics.

        An interrupted transfer is retried from byte zero. HTTP ranges are not
        assumed safe for changing archives. Reuse requires both an intact file
        and its matching manifest. Credential-bearing and redirected URLs fail.
        A supplied source byte count is checked before publishing or reusing a file.
        """
        parsed = urlsplit(endpoint)
        if (
            parsed.scheme != "https"
            or parsed.hostname not in self.allowed_hosts
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or parsed.port not in (None, 443)
        ):
            raise ValueError("Endpoint must be a query-free HTTPS URL on an approved host")
        if expected_sha256 is not None and not re.fullmatch("[a-fA-F0-9]{64}", expected_sha256):
            raise ValueError("Expected SHA-256 must be a 64-character hexadecimal digest")
        if expected_size_bytes is not None:
            if type(expected_size_bytes) is not int or expected_size_bytes < 0:
                raise ValueError("Expected byte size must be a nonnegative integer")
            if expected_size_bytes > self.config.maximum_response_bytes:
                raise ValueError("Expected byte size exceeds the configured byte limit")
        expected = expected_sha256.lower() if expected_sha256 else None
        manifest = path.with_suffix(path.suffix + ".download.json")
        if path.exists() or manifest.exists():
            if not path.exists() or not manifest.exists():
                raise ValueError("Incomplete download checkpoint; inspect it before retrying")
            saved = json.loads(manifest.read_text())
            with path.open("rb") as stream:
                actual = hashlib.file_digest(stream, "sha256").hexdigest()
            if (
                saved["endpoint"] != endpoint
                or saved["sha256"] != actual
                or saved["size_bytes"] != path.stat().st_size
                or path.stat().st_size > self.config.maximum_response_bytes
                or (expected is not None and actual != expected)
                or (expected_size_bytes is not None and path.stat().st_size != expected_size_bytes)
            ):
                raise ValueError("Download checkpoint differs from its source or checksum")
            return RequestRecord(
                endpoint, {}, saved["retrieved_at_utc"], actual, path.stat().st_size, True
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        last_status: int | None = None
        for attempt in range(self.config.attempts):
            self._wait_for_slot()
            response: httpx.Response | None = None
            descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
            temporary = Path(name)
            try:
                with (
                    os.fdopen(descriptor, "wb") as target,
                    self._client.stream(
                        "GET", endpoint, headers={"Accept": "application/octet-stream"}
                    ) as response,
                ):
                    last_status = response.status_code
                    if last_status == 200:
                        digest = hashlib.sha256()
                        size = 0
                        for chunk in response.iter_bytes(chunk_size=64 * 1024):
                            size += len(chunk)
                            if size > self.config.maximum_response_bytes:
                                raise RetrievalError("Export exceeded the configured byte limit")
                            if expected_size_bytes is not None and size > expected_size_bytes:
                                raise RetrievalError(
                                    "Downloaded export exceeds its expected byte size"
                                )
                            digest.update(chunk)
                            target.write(chunk)
                        if expected_size_bytes is not None and size != expected_size_bytes:
                            raise RetrievalError("Downloaded export has an unexpected byte size")
                        if expected is not None and digest.hexdigest() != expected:
                            raise RetrievalError("Downloaded export has an unexpected SHA-256")
                        target.flush()
                        os.fsync(target.fileno())
                        record = RequestRecord(
                            endpoint, {}, datetime.now(UTC).isoformat(), digest.hexdigest(), size
                        )
                    elif last_status not in _RETRY_STATUSES:
                        break
                if last_status == 200:
                    temporary.replace(path)
                    atomic_bytes(manifest, json.dumps(asdict(record), indent=2).encode())
                    return record
            except httpx.TransportError:
                last_status = None
            finally:
                temporary.unlink(missing_ok=True)
            if attempt + 1 < self.config.attempts:
                self._sleep(self._retry_delay(response, attempt))
        status = f"HTTP {last_status}" if last_status is not None else "transport failure"
        raise RetrievalError(f"Export retrieval failed from {parsed.hostname}: {status}") from None

    def get_text(
        self,
        endpoint: str,
        parameters: Mapping[str, str] | None = None,
        *,
        use_cache: bool = True,
    ) -> TextResponse:
        """Read a bounded public UTF-8 export, retaining tabs, line endings and units.

        This method does not accept credentials. Public CSV, PSV and TSV endpoints
        may use non-secret query parameters. Cache entries are separate from JSON
        responses and are accepted only after source, size and hash verification.
        """
        parsed = urlsplit(endpoint)
        if (
            parsed.scheme != "https"
            or parsed.hostname not in self.allowed_hosts
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or parsed.port not in (None, 443)
        ):
            raise ValueError("Endpoint must be a query-free HTTPS URL on an approved host")
        public = dict(parameters or {})
        if any(name.lower() in _SECRET_NAMES for name in public):
            raise ValueError("Text retrieval accepts public parameters only, never credentials")
        cache_key = hashlib.sha256(
            json.dumps(["text-utf8", endpoint, public], sort_keys=True).encode()
        ).hexdigest()
        cache = (
            self.cache_directory / f"{cache_key}.text.json"
            if use_cache and self.cache_directory is not None
            else None
        )
        if cache is not None and cache.exists():
            try:
                # JSON escaping can expand one control byte to six bytes.
                if cache.stat().st_size <= 6 * self.config.maximum_response_bytes + 65536:
                    saved = object_value(_decode(cache.read_bytes()))
                    value = saved["value"]
                    metadata = object_value(saved["record"])
                    captured = datetime.fromisoformat(str(metadata["retrieved_at_utc"]))
                    if isinstance(value, str):
                        raw = value.encode("utf-8")
                        if (
                            0
                            <= (datetime.now(UTC) - captured).total_seconds()
                            <= self.config.cache_ttl_seconds
                            and metadata["endpoint"] == endpoint
                            and metadata["parameters"] == public
                            and len(raw) <= self.config.maximum_response_bytes
                            and metadata["size_bytes"] == len(raw)
                            and metadata["sha256"] == hashlib.sha256(raw).hexdigest()
                        ):
                            return TextResponse(
                                value,
                                RequestRecord(
                                    endpoint,
                                    public,
                                    str(metadata["retrieved_at_utc"]),
                                    str(metadata["sha256"]),
                                    len(raw),
                                    True,
                                ),
                            )
            except (OSError, KeyError, TypeError, ValueError, RetrievalError):
                pass
        last_status: int | None = None
        for attempt in range(self.config.attempts):
            self._wait_for_slot()
            response: httpx.Response | None = None
            try:
                with self._client.stream(
                    "GET",
                    endpoint,
                    params=public,
                    # Export endpoints choose their own attachment/media type.
                    # PANGAEA rejects some specific text Accept combinations;
                    # UTF-8 decoding and source schema validation remain strict.
                    headers={"Accept": "*/*"},
                ) as response:
                    last_status = response.status_code
                    if last_status == 200:
                        chunks = bytearray()
                        for chunk in response.iter_bytes(chunk_size=64 * 1024):
                            if len(chunks) + len(chunk) > self.config.maximum_response_bytes:
                                raise RetrievalError(
                                    "Source response exceeded the configured byte limit"
                                )
                            chunks.extend(chunk)
                        raw = bytes(chunks)
                        try:
                            value = raw.decode("utf-8")
                        except UnicodeDecodeError:
                            raise RetrievalError("Source returned invalid UTF-8 text") from None
                        record = RequestRecord(
                            endpoint,
                            public,
                            datetime.now(UTC).isoformat(),
                            hashlib.sha256(raw).hexdigest(),
                            len(raw),
                        )
                        if cache is not None:
                            atomic_bytes(
                                cache,
                                json.dumps(
                                    {"record": asdict(record), "value": value},
                                    ensure_ascii=False,
                                    allow_nan=False,
                                ).encode("utf-8"),
                            )
                        return TextResponse(value, record)
                    if last_status not in _RETRY_STATUSES:
                        break
            except httpx.TransportError:
                last_status = None
            if attempt + 1 < self.config.attempts:
                self._sleep(self._retry_delay(response, attempt))
        status = f"HTTP {last_status}" if last_status is not None else "transport failure"
        raise RetrievalError(f"Retrieval failed from {parsed.hostname}: {status}") from None

    def get_json(
        self,
        endpoint: str,
        parameters: Mapping[str, str] | None = None,
        *,
        secrets: Mapping[str, str] | None = None,
        use_cache: bool = True,
        public_pagination_token: bool = False,
    ) -> JSONResponse:
        """Fetch JSON, preserving zero/null values and non-secret request provenance.

        ``public_pagination_token`` opts into a provider's non-authentication
        ``token`` cursor, including next links on its first page. Other credential
        names and explicit secrets remain redacted; authentication tokens cannot
        use this option. The default treats all token parameters as secrets.
        """
        parsed = urlsplit(endpoint)
        if (
            parsed.scheme != "https"
            or parsed.hostname not in self.allowed_hosts
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or parsed.port not in (None, 443)
        ):
            raise ValueError("Endpoint must be a query-free HTTPS URL on an approved host")
        public = dict(parameters or {})
        if any(
            name.lower() in _SECRET_NAMES and not (public_pagination_token and name == "token")
            for name in public
        ):
            raise ValueError("Pass credential parameters through secrets, never parameters")
        private = dict(secrets or {})
        if public_pagination_token:
            if any(name.lower() == "token" for name in private):
                raise ValueError(
                    "An authentication token cannot also be a public pagination cursor"
                )
            cursor = public.get("token")
            if cursor is not None and (
                not isinstance(cursor, str)
                or not 1 <= len(cursor) <= 8192
                or any(ord(character) < 32 for character in cursor)
            ):
                raise ValueError("Public pagination token must be a bounded nonempty string")
        if any(not value for value in private.values()) or set(public) & set(private):
            raise ValueError("Secret parameters must be nonempty and separate")
        cache_key = hashlib.sha256(
            json.dumps(
                [endpoint, public, public_pagination_token], sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest()
        cache = (
            self.cache_directory / f"{cache_key}.json"
            if use_cache and not private and self.cache_directory is not None
            else None
        )
        if cache is not None and cache.exists():
            try:
                saved = object_value(_decode(cache.read_bytes()))
                record = cast(dict[str, object], object_value(saved["record"]))
                captured = datetime.fromisoformat(str(record["retrieved_at_utc"]))
                body = json.dumps(saved["value"], separators=(",", ":"), allow_nan=False).encode()
                if (
                    0
                    <= (datetime.now(UTC) - captured).total_seconds()
                    <= self.config.cache_ttl_seconds
                    and hashlib.sha256(body).hexdigest() == record["sha256"]
                    and len(body) == record["size_bytes"]
                ):
                    return JSONResponse(
                        saved["value"],
                        RequestRecord(
                            endpoint,
                            public,
                            str(record["retrieved_at_utc"]),
                            str(record["sha256"]),
                            len(body),
                            True,
                        ),
                    )
            except (OSError, KeyError, TypeError, ValueError, RetrievalError):
                pass  # A malformed cache entry is ignored, never accepted as source truth.
        last_status: int | None = None
        for attempt in range(self.config.attempts):
            self._wait_for_slot()
            response: httpx.Response | None = None
            try:
                with (
                    _secret_scope(tuple(private.values())),
                    self._client.stream("GET", endpoint, params=public | private) as response,
                ):
                    last_status = response.status_code
                    if response.status_code == 200:
                        chunks = bytearray()
                        for chunk in response.iter_bytes():
                            if len(chunks) + len(chunk) > self.config.maximum_response_bytes:
                                raise RetrievalError(
                                    "Source response exceeded the configured byte limit"
                                )
                            chunks.extend(chunk)
                        raw = bytes(chunks)
                        value = _redact_value(
                            _decode(raw),
                            tuple(private.values()),
                            public_pagination_token=public_pagination_token,
                        )
                        # Canonical bytes identify the sanitized stored response.
                        body = json.dumps(value, separators=(",", ":"), allow_nan=False).encode()
                        record = RequestRecord(
                            endpoint,
                            public,
                            datetime.now(UTC).isoformat(),
                            hashlib.sha256(body).hexdigest(),
                            len(body),
                        )
                        if cache is not None:
                            atomic_bytes(
                                cache,
                                json.dumps(
                                    {"record": asdict(record), "value": value},
                                    allow_nan=False,
                                ).encode(),
                            )
                        return JSONResponse(value, record)
                    if response.status_code not in _RETRY_STATUSES:
                        break
            except httpx.TransportError:
                last_status = None
            if attempt + 1 < self.config.attempts:
                self._sleep(self._retry_delay(response, attempt))
        status = f"HTTP {last_status}" if last_status is not None else "transport failure"
        raise RetrievalError(f"Retrieval failed from {parsed.hostname}: {status}") from None
