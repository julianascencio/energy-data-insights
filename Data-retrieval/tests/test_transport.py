"""Offline synthetic HTTP fixtures exercise failure paths and secret boundaries."""

from __future__ import annotations

import json
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
