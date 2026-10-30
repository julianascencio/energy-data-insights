"""Provider credential spellings stay out of cache, logs and provenance."""

from __future__ import annotations

import logging
from pathlib import Path

import httpx
import pytest

from energy_data_retrieval.transport import HTTPClient, HTTPConfig


@pytest.mark.parametrize("name", ["serviceKey", "SERVICEKEY", "API-KEY"])
@pytest.mark.parametrize("kind", ["get_json", "get_text"])
def test_provider_credentials_cannot_be_public(name: str, kind: str) -> None:
    with (
        HTTPClient(frozenset({"provider.example"})) as http,
        pytest.raises(ValueError, match="credential"),
    ):
        getattr(http, kind)("https://provider.example/data", {name: "test-only-key"})


@pytest.mark.parametrize("kind", ["get_json", "get_text"])
@pytest.mark.parametrize("in_header", [True, False])
def test_provider_credentials_are_redacted_and_never_cached(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, kind: str, in_header: bool
) -> None:
    token = "test-only-generation-key"
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        supplied = (
            request.headers.get("API-KEY") if in_header else request.url.params.get("serviceKey")
        )
        assert supplied == token
        return httpx.Response(200, json={"echo": token, "url": "?serviceKey=" + token})

    with (
        HTTPClient(
            frozenset({"provider.example"}),
            transport=httpx.MockTransport(handler),
            cache_directory=tmp_path,
            config=HTTPConfig(minimum_interval_seconds=0),
        ) as http,
        caplog.at_level(logging.INFO, logger="httpx"),
    ):
        for _ in range(2):
            result = getattr(http, kind)(
                "https://provider.example/data",
                secrets=None if in_header else {"serviceKey": token},
                secret_headers={"API-KEY": token} if in_header else None,
            )
            assert token not in str(result.value)
            assert result.record.parameters == {}
            assert not result.record.cache_hit
    assert calls == 2
    assert list(tmp_path.iterdir()) == []
    assert token not in caplog.text
