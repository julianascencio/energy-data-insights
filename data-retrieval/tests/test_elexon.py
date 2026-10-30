"""Elexon contracts: synthetic responses plus an explicitly attributed real capture."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import pandas as pd
import pytest

from energy_data_retrieval.sources.elexon import ELEXON_HOSTS, ElexonClient, normalize_generation
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, JSONValue, RetrievalError


def point(day: date, period: int, value: JSONValue = 1.25) -> dict[str, JSONValue]:
    first = datetime.combine(day, time(), ZoneInfo("Europe/London")).astimezone(UTC)
    end = first + timedelta(minutes=30 * period)
    return {
        "dataset": "B1610",
        "bmUnit": "T_TEST-1",
        "nationalGridBmUnitId": "TEST-1",
        "settlementDate": day.isoformat(),
        "settlementPeriod": period,
        "halfHourEndTime": end.replace(tzinfo=None).isoformat(),
        "settlementRunType": "SF",
        "psrType": "Generation",
        "quantity": value,
    }


def test_mwh_signs_nulls_and_uk_dst_settlement_periods() -> None:
    day = date(2024, 10, 27)
    result = normalize_generation([point(day, 3, -4), point(day, 5, 0), point(day, 50, None)])
    assert result["timestamp"].tolist() == [
        pd.Timestamp("2024-10-27T00:00Z"),
        pd.Timestamp("2024-10-27T01:00Z"),
        pd.Timestamp("2024-10-27T23:30Z"),
    ]
    assert result["value"].iloc[:2].tolist() == [-4, 0]
    assert pd.isna(result["value"].iloc[2])
    assert result["unit"].unique().tolist() == ["MWh"]
    assert result["settlement_run"].unique().tolist() == ["SF"]
    spring = normalize_generation([point(date(2024, 3, 31), 46)])
    assert spring.interval_end.iloc[0] == pd.Timestamp("2024-03-31T23:00Z")
    with pytest.raises(RetrievalError, match="period"):
        normalize_generation([point(date(2024, 3, 31), 47)])


@pytest.mark.parametrize("value", [True, "1.2", float("nan"), float("inf"), {}])
def test_invalid_quantities(value: JSONValue) -> None:
    with pytest.raises(RetrievalError, match="quantity"):
        normalize_generation([point(date(2024, 1, 1), 1, value)])


def test_timestamp_validation_duplicates_and_revisions() -> None:
    record = point(date(2024, 1, 1), 1)
    assert len(normalize_generation([record, record])) == 1
    with pytest.raises(RetrievalError, match="revisions"):
        normalize_generation([record, record | {"settlementRunType": "R1"}])
    with pytest.raises(RetrievalError, match="end label"):
        normalize_generation([record | {"halfHourEndTime": "2024-01-01T01:00:00"}])
    with pytest.raises(RetrievalError, match="B1610"):
        normalize_generation([record | {"dataset": "INDGEN"}])
    with pytest.raises(RetrievalError, match="maximum_rows"):
        normalize_generation([record, record], maximum_rows=1)
    assert normalize_generation([]).empty


def test_chunking_25_hour_day_and_public_request_provenance() -> None:
    calls: list[httpx.Request] = []
    day = date(2024, 10, 27)
    midnight = datetime(2024, 10, 26, 23, tzinfo=UTC)

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert request.url.host == "data.elexon.co.uk"
        assert request.url.params["bmUnit"] == "T_TEST-1"
        assert "authorization" not in request.headers
        begin = datetime.fromisoformat(request.url.params["from"])
        period = int((begin - midnight).total_seconds() / 1800) + 1
        return httpx.Response(200, json=[point(day, period)])

    with HTTPClient(
        ELEXON_HOSTS,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        result = ElexonClient(http).generation(day, day, bm_unit="T_TEST-1")
    assert len(calls) == len(result.requests) == 5
    assert result.frame.settlement_period.tolist() == [1, 13, 25, 37, 49]
    assert calls[-1].url.params["to"] == "2024-10-27T23:30:00+00:00"
    assert all(len(record.sha256) == 64 for record in result.requests)


def test_rejects_ignored_filters_and_invalid_selection() -> None:
    def forbidden(_: httpx.Request) -> httpx.Response:
        pytest.fail("Invalid query reached the network")

    with HTTPClient(ELEXON_HOSTS, transport=httpx.MockTransport(forbidden)) as http:
        with pytest.raises(ValueError, match="maximum_requests"):
            ElexonClient(http, maximum_requests=1).generation(date(2024, 1, 1), date(2024, 1, 1))
        with pytest.raises(ValueError, match="bm_unit"):
            ElexonClient(http).generation(date(2024, 1, 1), date(2024, 1, 1), bm_unit="../secret")
    with (
        HTTPClient(
            ELEXON_HOSTS,
            transport=httpx.MockTransport(
                lambda _: httpx.Response(200, json=[point(date(2023, 1, 1), 1)])
            ),
        ) as http,
        pytest.raises(RetrievalError, match="outside"),
    ):
        ElexonClient(http).generation(date(2024, 1, 1), date(2024, 1, 1))


def test_attributed_real_day_preserves_native_quantity() -> None:
    data = Path(__file__).resolve().parents[2] / "examples/connectors/data"
    manifest = json.loads((data / "generation_elexon_provenance.json").read_text())
    raw = (data / "generation_elexon.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == manifest["files"][0]["sha256"]
    frame = normalize_generation(json.loads(raw))
    assert len(frame) == 48
    assert frame.unit_id.unique().tolist() == ["T_SUTBS-1"]
    assert frame.value.iloc[0] == -0.023
    assert frame.value.max() == 14.095
