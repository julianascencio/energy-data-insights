"""Offline synthetic HTTP fixtures exercise failure paths and secret boundaries."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

import httpx
import pytest

from energy_data_retrieval.transport import HTTPClient, HTTPConfig, RetrievalError

HOST = "fixture.example"
ENDPOINT = f"https://{HOST}/data"


def test_retry_after_and_public_cache(tmp_path: Path) -> None:
    calls = 0
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert request.url.host == HOST
        if calls == 1:
            return httpx.Response(429, headers={"Retry-After": "7"})
        return httpx.Response(200, json={"data": [0, None, 4]})

    with HTTPClient(
        frozenset({HOST}),
        transport=httpx.MockTransport(handler),
        cache_directory=tmp_path,
        config=HTTPConfig(minimum_interval_seconds=0),
        sleep=sleeps.append,
    ) as http:
        first = http.get_json(ENDPOINT, {"day": "2026-10-27"})
        second = http.get_json(ENDPOINT, {"day": "2026-10-27"})
    assert calls == 2
    assert sleeps == [7]
    assert first.value == second.value == {"data": [0, None, 4]}
    assert not first.record.cache_hit and second.record.cache_hit
    assert first.record.sha256 == second.record.sha256


def test_authenticated_responses_never_enter_cache(tmp_path: Path) -> None:
    calls = 0
    secret = "synthetic-private-key"

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert request.url.params["user_key"] == secret
        return httpx.Response(200, json={"echo": secret, "rows": [0]})

    with HTTPClient(
        frozenset({HOST}),
        transport=httpx.MockTransport(handler),
        cache_directory=tmp_path,
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        for _ in range(2):
            result = http.get_json(ENDPOINT, {"day": "2026-10-27"}, secrets={"user_key": secret})
            assert secret not in repr(result)
    assert calls == 2
    assert list(tmp_path.iterdir()) == []


def test_authentication_failure_is_not_retried_or_exposed() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(401, text=str(request.url))

    with (
        HTTPClient(frozenset({HOST}), transport=httpx.MockTransport(handler)) as http,
        pytest.raises(RetrievalError, match="HTTP 401") as caught,
    ):
        http.get_json(ENDPOINT, secrets={"user_key": "synthetic-secret"})
    assert len(requests) == 1
    assert "synthetic-secret" not in str(caught.value)
    assert "user_key" not in str(caught.value)


def test_header_authentication_bypasses_public_cache_and_redacts_echoes(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    secret = "synthetic-aemet-header-secret"
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert str(request.url) == ENDPOINT
        credential = request.headers.get("api_key")
        if credential is None:
            return httpx.Response(200, json={"access": "public"})
        assert credential == secret
        logging.getLogger("httpcore.http11").debug("Private header: %s", credential)
        return httpx.Response(200, json={"echo": credential, "rows": [0, None]})

    with (
        caplog.at_level("DEBUG", logger="httpcore.http11"),
        HTTPClient(
            frozenset({HOST}),
            transport=httpx.MockTransport(handler),
            cache_directory=tmp_path,
            config=HTTPConfig(minimum_interval_seconds=0),
        ) as http,
    ):
        public = http.get_json(ENDPOINT)
        cache = next(tmp_path.glob("*.json"))
        original_cache = cache.read_bytes()
        for _ in range(2):
            result = http.get_json(ENDPOINT, secret_headers={"api_key": secret})
            assert not result.record.cache_hit
            assert result.record.parameters == {}
            assert result.value == {"echo": "[REDACTED]", "rows": [0, None]}
            assert secret not in repr(result)
        assert http.get_json(ENDPOINT).value == public.value
    assert calls == 3
    assert cache.read_bytes() == original_cache
    assert list(tmp_path.glob("*.json")) == [cache]
    assert secret not in caplog.text
    assert "[REDACTED]" in caplog.text


@pytest.mark.parametrize(
    "headers",
    [
        {"Host": "another.example"},
        {"api_key": ""},
        {"api_key": "synthetic\r\ninjected"},
        {"api_key": "synthetic", "API_KEY": "ambiguous"},
    ],
)
def test_unsafe_secret_headers_fail_before_network(headers: dict[str, str]) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        pytest.fail("Invalid credential headers must fail before a request")

    with (
        HTTPClient(frozenset({HOST}), transport=httpx.MockTransport(handler)) as http,
        pytest.raises(ValueError, match=r"[Ss]ecret"),
    ):
        http.get_json(ENDPOINT, secret_headers=headers)


@pytest.mark.parametrize("encoding", ["iso-8859-1", "iso-8859-15"])
def test_declared_legacy_json_requires_opt_in_and_separate_cache(
    tmp_path: Path, encoding: str
) -> None:
    payload = {"station": "Málaga", "unit": "°C"}
    raw = json.dumps(payload, ensure_ascii=False).encode(encoding)
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200, content=raw, headers={"Content-Type": "application/json;charset=" + encoding}
        )

    with HTTPClient(
        frozenset({HOST}),
        transport=httpx.MockTransport(handler),
        cache_directory=tmp_path,
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        with pytest.raises(RetrievalError, match="invalid JSON"):
            http.get_json(ENDPOINT)
        result = http.get_json(ENDPOINT, allow_legacy_charset=True)
        assert result.value == payload
        assert http.get_json(ENDPOINT, allow_legacy_charset=True).record.cache_hit
        with pytest.raises(RetrievalError, match="invalid JSON"):
            http.get_json(ENDPOINT)
    assert calls == 3


def test_valid_utf8_json_precedes_a_misleading_legacy_charset() -> None:
    payload = {"station": "Málaga", "unit": "°C", "symbol": "€"}
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    with HTTPClient(
        frozenset({HOST}),
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200, content=raw, headers={"Content-Type": "application/json;charset=ISO-8859-15"}
            )
        ),
    ) as http:
        assert http.get_json(ENDPOINT, allow_legacy_charset=True).value == payload


@pytest.mark.parametrize("charset", ["", ";charset=windows-1252", ";charset=unknown"])
def test_legacy_json_without_an_approved_declaration_stays_invalid(charset: str) -> None:
    raw = json.dumps({"name": "Málaga"}, ensure_ascii=False).encode("iso-8859-1")
    with (
        HTTPClient(
            frozenset({HOST}),
            transport=httpx.MockTransport(
                lambda _: httpx.Response(
                    200, content=raw, headers={"Content-Type": "application/json" + charset}
                )
            ),
        ) as http,
        pytest.raises(RetrievalError, match="invalid JSON"),
    ):
        http.get_json(ENDPOINT, allow_legacy_charset=True)


@pytest.mark.parametrize(
    "url",
    [
        "http://fixture.example/data",
        "https://evil.example/data",
        "https://fixture.example/data?token=private",
    ],
)
def test_endpoint_allowlist(url: str) -> None:
    with HTTPClient(frozenset({HOST})) as http, pytest.raises(ValueError, match="approved host"):
        http.get_json(url)


def test_credentials_rejected_in_public_parameters() -> None:
    with HTTPClient(frozenset({HOST})) as http, pytest.raises(ValueError, match="secrets"):
        http.get_json(ENDPOINT, {"user_key": "fixture"})


@pytest.mark.parametrize("status", [302, 403, 404])
def test_no_redirect_or_nonretryable_status(status: int) -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(status, headers={"Location": "https://evil.example/"})

    with (
        HTTPClient(frozenset({HOST}), transport=httpx.MockTransport(handler)) as http,
        pytest.raises(RetrievalError),
    ):
        http.get_json(ENDPOINT)
    assert calls == 1


def test_size_bound_and_invalid_json() -> None:
    with (
        HTTPClient(
            frozenset({HOST}),
            config=HTTPConfig(maximum_response_bytes=4),
            transport=httpx.MockTransport(lambda _: httpx.Response(200, content=b"123456")),
        ) as http,
        pytest.raises(RetrievalError, match="byte limit"),
    ):
        http.get_json(ENDPOINT)
    with (
        HTTPClient(
            frozenset({HOST}),
            transport=httpx.MockTransport(lambda _: httpx.Response(200, content=b'{"x": NaN}')),
        ) as http,
        pytest.raises(RetrievalError, match="invalid JSON"),
    ):
        http.get_json(ENDPOINT)


def test_tampered_cache_is_refetched(tmp_path: Path) -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={"count": calls})

    with HTTPClient(
        frozenset({HOST}),
        transport=httpx.MockTransport(handler),
        cache_directory=tmp_path,
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        http.get_json(ENDPOINT)
        path = next(tmp_path.glob("*.json"))
        payload = json.loads(path.read_text())
        payload["value"] = {"count": 999}
        path.write_text(json.dumps(payload))
        result = http.get_json(ENDPOINT)
    assert calls == 2 and result.value == {"count": 2}


def test_encoded_secret_echo_and_http_logs_are_redacted(caplog: pytest.LogCaptureFixture) -> None:
    secret = 'synthetic + / "quoted" credential'

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"echo": secret, "url": str(request.url)})

    with (
        caplog.at_level("DEBUG", logger="httpx"),
        HTTPClient(frozenset({HOST}), transport=httpx.MockTransport(handler)) as http,
    ):
        response = http.get_json(ENDPOINT, secrets={"user_key": secret})
    assert secret not in repr(response)
    assert "synthetic" not in caplog.text
    assert "[REDACTED]" in caplog.text
    assert response.value == {"echo": "[REDACTED]", "url": ENDPOINT + "?user_key=[REDACTED]"}


def test_network_errors_have_finite_attempts_and_safe_messages() -> None:
    attempts = 0
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ConnectError(str(request.url), request=request)

    with (
        HTTPClient(
            frozenset({HOST}),
            transport=httpx.MockTransport(handler),
            config=HTTPConfig(attempts=3, minimum_interval_seconds=0),
            sleep=sleeps.append,
        ) as http,
        pytest.raises(RetrievalError, match="transport failure") as caught,
    ):
        http.get_json(ENDPOINT, secrets={"user_key": "synthetic-secret"})
    assert attempts == 3 and sleeps == [1, 2]
    assert "synthetic-secret" not in str(caught.value)


def test_download_checks_source_size_and_sha256_before_reuse(tmp_path: Path) -> None:
    content = b"synthetic netcdf fixture"
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, content=content)

    destination = tmp_path / "data.nc"
    with HTTPClient(frozenset({HOST}), transport=httpx.MockTransport(handler)) as http:
        digest = hashlib.sha256(content).hexdigest()
        first = http.download_file(
            ENDPOINT, destination, expected_sha256=digest, expected_size_bytes=len(content)
        )
        reused = http.download_file(
            ENDPOINT, destination, expected_sha256=digest, expected_size_bytes=len(content)
        )
        assert first.sha256 == reused.sha256 == digest
        assert not first.cache_hit and reused.cache_hit
        assert calls == 1
        with pytest.raises(ValueError, match="checkpoint"):
            http.download_file(ENDPOINT, destination, expected_size_bytes=len(content) + 1)
        assert calls == 1


@pytest.mark.parametrize("expected", [3, 12])
def test_incorrect_download_size_never_publishes_file(tmp_path: Path, expected: int) -> None:
    destination = tmp_path / "data.nc"
    with (
        HTTPClient(
            frozenset({HOST}),
            transport=httpx.MockTransport(lambda _: httpx.Response(200, content=b"abcdef")),
        ) as http,
        pytest.raises(RetrievalError, match="byte size"),
    ):
        http.download_file(ENDPOINT, destination, expected_size_bytes=expected)
    assert list(tmp_path.iterdir()) == []


def test_oversized_download_is_rejected_before_request(tmp_path: Path) -> None:
    def unexpected_request(_: httpx.Request) -> httpx.Response:
        pytest.fail("The source's declared size must be checked before making a request")

    with (
        HTTPClient(
            frozenset({HOST}),
            config=HTTPConfig(maximum_response_bytes=10),
            transport=httpx.MockTransport(unexpected_request),
        ) as http,
        pytest.raises(ValueError, match="byte limit"),
    ):
        http.download_file(ENDPOINT, tmp_path / "data.nc", expected_size_bytes=11)
    assert list(tmp_path.iterdir()) == []


def test_public_pagination_cursor_preserves_next_link_without_exposing_credentials(
    tmp_path: Path,
) -> None:
    calls = 0
    cursor = "public-dataset-cursor=="

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert request.url.params.get("token", cursor) == cursor
        return httpx.Response(
            200,
            json={"next": f"{ENDPOINT}?token={cursor}&api_key=synthetic-private-key"},
        )

    with HTTPClient(
        frozenset({HOST}),
        transport=httpx.MockTransport(handler),
        cache_directory=tmp_path,
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        ordinary = http.get_json(ENDPOINT)
        first_page = http.get_json(ENDPOINT, public_pagination_token=True)
        next_page = http.get_json(ENDPOINT, {"token": cursor}, public_pagination_token=True)
        cached = http.get_json(ENDPOINT, public_pagination_token=True)
    assert calls == 3  # A redacted cache entry cannot replace a public cursor response.
    assert ordinary.value == {"next": f"{ENDPOINT}?token=[REDACTED]&api_key=[REDACTED]"}
    assert (
        first_page.value
        == next_page.value
        == cached.value
        == {"next": f"{ENDPOINT}?token={cursor}&api_key=[REDACTED]"}
    )
    assert next_page.record.parameters == {"token": cursor}
    assert cached.record.cache_hit


def test_public_cursor_option_does_not_relax_authentication_parameters() -> None:
    def forbidden(_: httpx.Request) -> httpx.Response:
        pytest.fail("Credential mistakes must be rejected before a network request")

    with HTTPClient(frozenset({HOST}), transport=httpx.MockTransport(forbidden)) as http:
        with pytest.raises(ValueError, match="secrets"):
            http.get_json(ENDPOINT, {"token": "secret"})
        with pytest.raises(ValueError, match="secrets"):
            http.get_json(ENDPOINT, {"api_key": "secret"}, public_pagination_token=True)
        with pytest.raises(ValueError, match="authentication token"):
            http.get_json(ENDPOINT, secrets={"token": "secret"}, public_pagination_token=True)
        with pytest.raises(ValueError, match="bounded nonempty"):
            http.get_json(ENDPOINT, {"token": ""}, public_pagination_token=True)
