"""SMARD epoch intervals, native MWh and bounded weekly downloads."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

import httpx
import pandas as pd
import pytest

from energy_data_retrieval.sources.smard import SMARD_HOSTS, SMARDClient, normalize_generation
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, JSONValue, RetrievalError


def payload(points: list[JSONValue]) -> dict[str, JSONValue]:
    return {"meta_data": {"version": 1, "created": 1742248754814}, "series": points}


def test_mwh_are_not_converted_again_and_dst_epochs_stay_distinct() -> None:
    stamps = [
        int(pd.Timestamp(label).timestamp() * 1000)
        for label in ("2024-10-27T00:00Z", "2024-10-27T01:00Z", "2024-10-27T01:15Z")
    ]
    result = normalize_generation(
        payload([[stamps[0], 1.25], [stamps[1], 0], [stamps[2], None]]), technology="solar"
    )
    assert result.value.iloc[:2].tolist() == [1.25, 0]
    assert pd.isna(result.value.iloc[2])
    assert result.unit.unique().tolist() == ["MWh"]
    assert result.timestamp.dt.tz_convert("Europe/Berlin").dt.hour.iloc[:2].tolist() == [2, 2]
    assert result.timestamp.nunique() == 3
    assert (result.interval_end - result.interval_start).eq(pd.Timedelta(minutes=15)).all()


@pytest.mark.parametrize(
    "point",
    [
        [True, 1],
        [1716760800001, 1],
        [1716760800000, True],
        [1716760800000, "1"],
        [1716760800000, float("inf")],
        [1716760800000],
    ],
)
def test_bad_native_points(point: JSONValue) -> None:
    with pytest.raises(RetrievalError):
        normalize_generation(payload([point]), technology="solar")


def test_duplicates_schema_empty_and_invalid_selection() -> None:
    point: JSONValue = [1716760800000, -2]
    assert normalize_generation(payload([point, point]), technology="solar").value.tolist() == [-2]
    with pytest.raises(RetrievalError, match="Conflicting"):
        normalize_generation(payload([point, [1716760800000, 2]]), technology="solar")
    with pytest.raises(RetrievalError, match="version"):
        normalize_generation({"meta_data": {"version": 2}, "series": []}, technology="solar")
    with pytest.raises(ValueError, match="documented"):
        normalize_generation(payload([]), technology="capacity")
    assert normalize_generation(payload([]), technology="solar").empty


def test_week_index_selection_and_25_hour_civil_day() -> None:
    first = int(pd.Timestamp("2024-10-26T22:00Z").timestamp() * 1000)
    week = int(pd.Timestamp("2024-10-20T22:00Z").timestamp() * 1000)
    next_week = int(pd.Timestamp("2024-10-27T23:00Z").timestamp() * 1000)
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path.endswith("index_quarterhour.json"):
            return httpx.Response(200, json={"timestamps": [week, next_week]})
        assert request.url.path.endswith(f"4068_DE_quarterhour_{week}.json")
        points: list[JSONValue] = [[first - 900000, 77]]
        for index in range(100):
            points.append([first + index * 900000, 1.25])
        points.append([next_week, 88])
        return httpx.Response(200, json=payload(points))

    with HTTPClient(
        SMARD_HOSTS,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        result = SMARDClient(http).generation(
            date(2024, 10, 27), date(2024, 10, 27), technologies=["solar"]
        )
    assert len(calls) == len(result.requests) == 2
    assert len(result.frame) == 100
    assert result.frame.value.sum() == 125


def test_request_budget_and_invalid_index_fail_before_week_download() -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={"timestamps": [1716760800000]})

    with (
        HTTPClient(SMARD_HOSTS, transport=httpx.MockTransport(handler)) as http,
        pytest.raises(ValueError, match="maximum_requests"),
    ):
        SMARDClient(http, maximum_requests=1).generation(
            date(2024, 6, 1), date(2024, 6, 1), technologies=["solar"]
        )
    assert calls == 1
    with (
        HTTPClient(
            SMARD_HOSTS,
            transport=httpx.MockTransport(
                lambda _: httpx.Response(200, json={"timestamps": [True]})
            ),
        ) as http,
        pytest.raises(RetrievalError, match="invalid epoch"),
    ):
        SMARDClient(http).generation(date(2024, 6, 1), date(2024, 6, 1), technologies=["solar"])


def test_attributed_real_week_captures_keep_all_quarters() -> None:
    data = Path(__file__).resolve().parents[2] / "examples/connectors/data"
    manifest = json.loads((data / "generation_smard_provenance.json").read_text())
    for entry in manifest["files"]:
        raw = (data / entry["file"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == entry["sha256"]
        technology = entry["file"].removeprefix("generation_smard_").removesuffix(".json")
        result = normalize_generation(json.loads(raw), technology=technology)
        assert len(result) == 672
        assert result.timestamp.nunique() == 672
