"""Bounded station text exports preserve scientific bytes and public-only caching."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

import httpx
import pytest

from energy_data_retrieval.transport import HTTPClient, HTTPConfig, RetrievalError

HOST = "stations.example"
ENDPOINT = f"https://{HOST}/export"


def test_text_retry_and_cache_preserve_unicode_tabs_and_line_endings(tmp_path: Path) -> None:
    raw = "Date/Time\tSWD [W/m²]\r\n2009-06-01T00:00\t-1\r\n".encode()
    calls = 0
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert request.url.params["format"] == "textfile"
        assert request.headers["Accept"] == "*/*"
        if calls == 1:
            return httpx.Response(429, headers={"Retry-After": "2"})
        return httpx.Response(200, content=raw)

    with HTTPClient(
        frozenset({HOST}),
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(minimum_interval_seconds=0),
        cache_directory=tmp_path,
        sleep=sleeps.append,
    ) as http:
        first = http.get_text(ENDPOINT, {"format": "textfile"})
        second = http.get_text(ENDPOINT, {"format": "textfile"})
    assert first.value.encode() == second.value.encode() == raw
    assert first.record.sha256 == second.record.sha256 == hashlib.sha256(raw).hexdigest()
    assert first.record.size_bytes == len(raw)
    assert not first.record.cache_hit and second.record.cache_hit
    assert calls == 2 and sleeps == [2]


def test_text_export_accepts_provider_selected_attachment_media_type() -> None:
    raw = b"Date/Time\tSWD [W/m**2]\n2009-06-01T00:00\t-1\n"

    def handler(request: httpx.Request) -> httpx.Response:
        # Regression for a live PANGAEA textfile export returning HTTP 400 when
        # the client offered text/tab-separated-values in its Accept header.
        if request.headers.get("Accept") != "*/*":
            return httpx.Response(400)
        return httpx.Response(
            200,
            content=raw,
            headers={"Content-Type": "application/octet-stream"},
        )

    with HTTPClient(frozenset({HOST}), transport=httpx.MockTransport(handler)) as http:
        result = http.get_text(ENDPOINT, {"format": "textfile"}, use_cache=False)
    assert result.value.encode("utf-8") == raw
    assert result.record.sha256 == hashlib.sha256(raw).hexdigest()


def test_modified_text_cache_is_retrieved_again_and_uncached_reads_bypass_it(
    tmp_path: Path,
) -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, content=b"original\t0\n")

    with HTTPClient(
        frozenset({HOST}),
        transport=httpx.MockTransport(handler),
        cache_directory=tmp_path,
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        http.get_text(ENDPOINT)
        path = next(tmp_path.glob("*.text.json"))
        saved = json.loads(path.read_text())
        saved["value"] = "changed\t99\n"
        path.write_text(json.dumps(saved))
        again = http.get_text(ENDPOINT)
        fresh = http.get_text(ENDPOINT, use_cache=False)
    assert calls == 3
    assert again.value == fresh.value == "original\t0\n"
    assert not again.record.cache_hit and not fresh.record.cache_hit


@pytest.mark.parametrize(
    ("raw", "limit", "message"),
    [(b"12345", 4, "byte limit"), (b"\xff\xfe", 10, "invalid UTF-8")],
)
def test_invalid_text_does_not_enter_cache(
    tmp_path: Path, raw: bytes, limit: int, message: str
) -> None:
    with (
        HTTPClient(
            frozenset({HOST}),
            transport=httpx.MockTransport(lambda _: httpx.Response(200, content=raw)),
            config=HTTPConfig(maximum_response_bytes=limit),
            cache_directory=tmp_path,
        ) as http,
        pytest.raises(RetrievalError, match=message),
    ):
        http.get_text(ENDPOINT)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("status", [302, 401, 403])
def test_restricted_or_redirected_text_is_not_retried(status: int) -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            status,
            headers={"Location": "https://elsewhere.example/private"},
            text="private error body",
        )

    with (
        HTTPClient(frozenset({HOST}), transport=httpx.MockTransport(handler)) as http,
        pytest.raises(RetrievalError) as error,
    ):
        http.get_text(ENDPOINT)
    assert calls == 1
    assert f"HTTP {status}" in str(error.value)
    assert "private" not in str(error.value)


def test_text_rejects_authentication_and_unapproved_endpoints_before_network() -> None:
    def forbidden(_: httpx.Request) -> httpx.Response:
        pytest.fail("Invalid requests must fail before network access")

    with HTTPClient(frozenset({HOST}), transport=httpx.MockTransport(forbidden)) as http:
        with pytest.raises(ValueError, match="credentials"):
            http.get_text(ENDPOINT, {"api_key": "private"})
        with pytest.raises(ValueError, match="approved host"):
            http.get_text("https://elsewhere.example/export")
        with pytest.raises(ValueError, match="approved host"):
            http.get_text(ENDPOINT + "?token=private")


def test_text_transport_failure_has_bounded_attempts() -> None:
    calls = 0
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ConnectError("internal transport detail", request=request)

    with (
        HTTPClient(
            frozenset({HOST}),
            transport=httpx.MockTransport(handler),
            config=HTTPConfig(attempts=2, minimum_interval_seconds=0),
            sleep=sleeps.append,
        ) as http,
        pytest.raises(RetrievalError, match="transport failure") as error,
    ):
        http.get_text(ENDPOINT)
    assert calls == 2 and sleeps == [1]
    assert "internal" not in str(error.value)


def test_authenticated_xml_redacts_token_and_never_reuses_public_cache(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    token = "test-only-entsoe-credential"
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        secret = request.url.params.get("securityToken")
        assert calls == 1 or secret == token
        return httpx.Response(200, text=f"<document><echo>{secret or 'public'}</echo></document>")

    with (
        HTTPClient(
            frozenset({HOST}),
            transport=httpx.MockTransport(handler),
            cache_directory=tmp_path,
            config=HTTPConfig(minimum_interval_seconds=0),
        ) as http,
        caplog.at_level(logging.INFO, logger="httpx"),
    ):
        public = http.get_text(ENDPOINT)
        private = http.get_text(ENDPOINT, secrets={"securityToken": token})
        again = http.get_text(ENDPOINT, secrets={"securityToken": token})
    assert calls == 3 and public.value != private.value
    assert private.value == again.value == "<document><echo>[REDACTED]</echo></document>"
    assert private.record.parameters == {} and not private.record.cache_hit
    assert private.record.sha256 == hashlib.sha256(private.value.encode()).hexdigest()
    assert token not in caplog.text
    assert len(list(tmp_path.iterdir())) == 1
    assert token not in next(tmp_path.iterdir()).read_text()


def test_xml_secret_parameters_cannot_be_passed_as_public() -> None:
    with HTTPClient(frozenset({HOST})) as http:
        with pytest.raises(ValueError, match="credentials"):
            http.get_text(ENDPOINT, {"securityToken": "secret"})
        with pytest.raises(ValueError, match="nonempty"):
            http.get_text(ENDPOINT, secrets={"securityToken": ""})


def test_authenticated_text_error_sanitizes_logs(caplog: pytest.LogCaptureFixture) -> None:
    token = "test-only-token-never-expose"
    with (
        HTTPClient(
            frozenset({HOST}),
            transport=httpx.MockTransport(lambda _: httpx.Response(401, text=token)),
        ) as http,
        caplog.at_level(logging.INFO, logger="httpx"),
        pytest.raises(RetrievalError, match="HTTP 401") as failure,
    ):
        http.get_text(ENDPOINT, secrets={"securityToken": token})
    assert token not in str(failure.value) and token not in caplog.text
