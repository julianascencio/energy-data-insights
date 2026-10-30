"""KPX official schema with synthetic observations; no live credentials used."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import cast

import httpx
import pandas as pd
import pytest

from energy_data_retrieval.sources.kpx import KPX_HOSTS, KPXClient, parse_generation, solar_requests
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, JSONValue, RetrievalError


def item(hour: int, value: JSONValue = 1) -> dict[str, JSONValue]:
    return {
        "tradeYmd": "20240901",
        "tradeNo": str(hour),
        "regionNm": "Jeju",
        "amgo": value,
        "rn": hour,
    }


def payload(
    items: list[dict[str, JSONValue]], *, total: int | None = None, page: int = 1
) -> dict[str, JSONValue]:
    return {
        "response": {
            "header": {"resultCode": "00", "resultMsg": "OK"},
            "body": {
                "items": {"item": cast(JSONValue, items)},
                "pageNo": page,
                "numOfRows": len(items),
                "totalCount": len(items) if total is None else total,
            },
        }
    }


def test_korean_hour_end_convention_and_energy_units() -> None:
    frame = parse_generation(payload([item(1, 0), item(2, None), item(24, -1)]))
    assert frame.timestamp.tolist() == [
        pd.Timestamp("2024-08-31T15:00Z"),
        pd.Timestamp("2024-08-31T16:00Z"),
        pd.Timestamp("2024-09-01T14:00Z"),
    ]
    assert frame.interval_end.iloc[-1] == pd.Timestamp("2024-09-01T15:00Z")
    assert frame.unit.eq("MWh").all()
    assert frame.value.iloc[0] == 0 and pd.isna(frame.value.iloc[1]) and frame.value.iloc[2] == -1


@pytest.mark.parametrize("hour", [0, 25, True, "bad"])
def test_invalid_trade_hours(hour: JSONValue) -> None:
    row = item(1)
    row["tradeNo"] = hour
    with pytest.raises(RetrievalError, match="date/hour"):
        parse_generation(payload([row]))


def test_missing_generation_and_error_response() -> None:
    row = item(1)
    del row["amgo"]
    with pytest.raises(RetrievalError, match="generation field"):
        parse_generation(payload([row]))
    with pytest.raises(RetrievalError, match="API error"):
        parse_generation({"response": {"header": {"resultCode": "30", "resultMsg": "private"}}})
    with pytest.raises(RetrievalError, match="duplicate"):
        parse_generation(payload([item(1), item(1)]))
    empty = parse_generation(payload([]))
    assert empty.empty and str(empty.timestamp.dtype) == "datetime64[ns, UTC]"


def test_pagination_secret_provenance_and_no_public_cache(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    secret = "test-service-key+with/slashes="
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert request.url.params["serviceKey"] == secret
        page = int(request.url.params["pageNo"])
        return httpx.Response(200, json=payload([item(page)], total=2, page=page))

    with HTTPClient(
        KPX_HOSTS,
        cache_directory=tmp_path,
        config=HTTPConfig(minimum_interval_seconds=0),
        transport=httpx.MockTransport(handler),
    ) as http:
        result = KPXClient(http, api_key=secret, page_size=1).solar_generation(
            date(2024, 9, 1), date(2024, 9, 1)
        )
    assert len(calls) == len(result.requests) == len(result.frame) == 2
    assert not list(tmp_path.iterdir())
    assert all("serviceKey" not in record.parameters for record in result.requests)
    assert secret not in repr(result.requests) + caplog.text


@pytest.mark.parametrize("mode", ["missing", "repeated", "changing", "limit"])
def test_rejects_incomplete_or_revised_pagination(mode: str) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params["pageNo"])
        rows = [] if mode == "missing" and page == 2 else [item(1 if mode == "repeated" else page)]
        count = 3 if mode == "changing" and page == 2 else 2
        return httpx.Response(200, json=payload(rows, total=count, page=page))

    with HTTPClient(
        KPX_HOSTS,
        config=HTTPConfig(minimum_interval_seconds=0),
        transport=httpx.MockTransport(handler),
    ) as http:
        client = KPXClient(
            http, api_key="test", page_size=1, maximum_requests=1 if mode == "limit" else 5
        )
        with pytest.raises(RetrievalError):
            client.solar_generation(date(2024, 9, 1), date(2024, 9, 1))


def test_plans_have_no_credentials_and_missing_key_fails_before_http(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = solar_requests(date(2024, 9, 1), date(2024, 9, 2))
    assert len(plan) == 2 and "serviceKey" not in json.dumps(plan)
    with pytest.raises(ValueError, match="maximum_requests"):
        solar_requests(date(2024, 9, 1), date(2024, 9, 2), maximum_requests=1)
    monkeypatch.delenv("KPX_API_KEY", raising=False)
    with (
        HTTPClient(
            KPX_HOSTS, transport=httpx.MockTransport(lambda _: pytest.fail("No network"))
        ) as http,
        pytest.raises(ValueError, match="KPX_API_KEY"),
    ):
        KPXClient.from_environment(http)
