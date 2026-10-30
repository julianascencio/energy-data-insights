"""CAISO clock labels, five-minute power and distinct storage/import flows."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

import httpx
import pandas as pd
import pytest

from energy_data_retrieval.sources.caiso import CAISO_HOSTS, CAISOClient, parse_fuel_mix
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, RetrievalError

CSV = "Time,Solar,Wind,Batteries,Imports\r\n00:00,0,7,-3,9\r\n00:05,-1,,4,-2\r\n"


def test_other_supply_is_separate_because_it_can_include_demand_response() -> None:
    frame = parse_fuel_mix("Time,Solar,Other\n00:00,0,10\n", day=date(2024, 6, 1))
    assert frame.loc[frame.flow.eq("other_supply"), "value"].tolist() == [10]
    assert frame.loc[frame.flow.eq("generation"), "technology"].tolist() == ["solar"]


def test_power_values_flows_nulls_and_summer_pacific_labels() -> None:
    frame = parse_fuel_mix(CSV, day=date(2024, 6, 1))
    assert frame.timestamp.iloc[0] == pd.Timestamp("2024-06-01T07:00Z")
    assert frame.unit.unique().tolist() == ["MW"]
    assert frame.loc[frame.flow.eq("net_storage"), "value"].tolist() == [-3, 4]
    assert frame.loc[frame.flow.eq("net_import"), "value"].tolist() == [9, -2]
    wind = frame.loc[frame.technology.eq("wind"), "value"]
    assert wind.iloc[0] == 7 and pd.isna(wind.iloc[1])
    assert frame.loc[frame.technology.eq("solar"), "value"].tolist() == [0, -1]
    assert frame.attrs["interval_minutes"] == 5
    assert parse_fuel_mix(CSV, day=date(2024, 1, 1)).timestamp.iloc[0] == pd.Timestamp(
        "2024-01-01T08:00Z"
    )


@pytest.mark.parametrize("day,label", [(date(2024, 11, 3), "01:00"), (date(2024, 3, 10), "02:00")])
def test_does_not_invent_offsets_on_dst_transition_days(day: date, label: str) -> None:
    with pytest.raises(RetrievalError, match="DST"):
        parse_fuel_mix(f"Time,Solar\n{label},10\n", day=day)


@pytest.mark.parametrize(
    "text",
    [
        "Time,Unknown\n00:00,1\n",
        "Time,Solar,Solar\n00:00,1,2\n",
        "Time,Solar\n00:00,1\n00:00,2\n",
        "Time,Solar\n00:03,1\n",
        "Time,Solar\n25:00,1\n",
        "Time,Solar\n00:00,nan\n",
        "Time,Solar\n00:00,1,2\n",
        "<html>Not a CSV</html>",
    ],
)
def test_invalid_schema_time_values_and_duplicates(text: str) -> None:
    with pytest.raises(RetrievalError):
        parse_fuel_mix(text, day=date(2024, 6, 1))


def test_fetch_bounds_provenance_and_no_authentication() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert not request.url.query
        assert "authorization" not in request.headers
        return httpx.Response(200, text=CSV, headers={"Content-Type": "text/csv"})

    with HTTPClient(
        CAISO_HOSTS,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        result = CAISOClient(http).generation(date(2024, 6, 1), date(2024, 6, 2))
        with pytest.raises(ValueError, match="maximum_requests"):
            CAISOClient(http, maximum_requests=1).generation(date(2024, 6, 1), date(2024, 6, 2))
        with pytest.raises(RetrievalError, match="maximum_rows"):
            CAISOClient(http, maximum_rows=4).generation(date(2024, 6, 1), date(2024, 6, 1))
    assert len(result.frame) == 16
    assert len(result.requests) == 2
    assert calls[0].url.path == "/outlook/history/20240601/fuelsource.csv"
    assert result.requests[0].sha256 == hashlib.sha256(CSV.encode()).hexdigest()


def test_empty_data_is_not_filled_and_missing_files_raise() -> None:
    assert parse_fuel_mix("Time,Solar\n", day=date(2024, 6, 1)).empty
    with (
        HTTPClient(
            CAISO_HOSTS, transport=httpx.MockTransport(lambda _: httpx.Response(404))
        ) as http,
        pytest.raises(RetrievalError, match="404"),
    ):
        CAISOClient(http).generation(date(2024, 6, 1), date(2024, 6, 1))


def test_real_snapshot_hash_and_count() -> None:
    data = Path(__file__).resolve().parents[2] / "examples/connectors/data"
    raw = (data / "generation_caiso.csv").read_bytes()
    manifest = json.loads((data / "generation_caiso_provenance.json").read_text())
    assert hashlib.sha256(raw).hexdigest() == manifest["files"][0]["sha256"]
    frame = parse_fuel_mix(raw.decode(), day=date(2024, 6, 1))
    assert len(frame) == 288 * 13
    assert frame.timestamp.nunique() == 288
    assert frame.loc[frame.technology.eq("solar"), "value"].iloc[0] == 175
