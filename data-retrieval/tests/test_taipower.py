"""Taipower snapshot scope, timestamps, missing values and live request contracts."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import cast

import httpx
import pandas as pd
import pytest

from energy_data_retrieval.sources.taipower import TAIPOWER_HOSTS, TaipowerClient, parse_generation
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, JSONValue, RetrievalError

DATA = Path(__file__).resolve().parents[2] / "examples/connectors/data"


def payload() -> dict[str, JSONValue]:
    return {
        "DateTime": "2026-10-30T12:00:00",
        "aaData": [
            {
                "機組類型": "太陽能",
                "機組名稱": "Example PV",
                "裝置容量(MW)": "100",
                "淨發電量(MW)": "0",
                "備註": "",
            },
            {
                "機組類型": "太陽能",
                "機組名稱": "其它購電太陽能",
                "裝置容量(MW)": "-",
                "淨發電量(MW)": None,
                "備註": "",
            },
            {
                "機組類型": "太陽能",
                "機組名稱": "小計",
                "裝置容量(MW)": "100(20.0%)",
                "淨發電量(MW)": "0(0.0%)",
                "備註": "",
            },
            {
                "機組類型": "儲能負載(Energy Storage System Load)</b>",
                "機組名稱": "Pump#1",
                "裝置容量(MW)": "100",
                "淨發電量(MW)": "-20",
                "備註": "",
            },
        ],
    }


def test_totals_groups_and_storage_load_are_distinct() -> None:
    frame = parse_generation(payload())
    assert len(frame) == 1 and frame.value.iloc[0] == 0
    assert frame.timestamp.iloc[0] == pd.Timestamp("2026-10-30T04:00Z")
    assert frame.measurement_kind.eq("power_snapshot").all()
    all_rows = parse_generation(payload(), include_aggregates=True, include_storage_load=True)
    assert len(all_rows) == 4 and all_rows.is_total.sum() == 1
    assert pd.isna(all_rows.loc[all_rows.asset_id.eq("其它購電太陽能"), "value"]).all()
    assert all_rows.loc[all_rows.flow.eq("consumption"), "value"].item() == -20


@pytest.mark.parametrize("number", [True, "inf", "nan", {}, "oops"])
def test_invalid_generation_values(number: JSONValue) -> None:
    raw = payload()
    cast(list[dict], raw["aaData"])[0]["淨發電量(MW)"] = number
    with pytest.raises(RetrievalError):
        parse_generation(raw)


def test_duplicate_and_limit_fail() -> None:
    raw = payload()
    rows = cast(list[dict], raw["aaData"])
    rows.append(copy.deepcopy(rows[0]))
    with pytest.raises(RetrievalError, match="duplicate"):
        parse_generation(raw)
    with pytest.raises(RetrievalError, match="maximum_rows"):
        parse_generation(payload(), maximum_rows=1)


def test_latest_does_not_reuse_stale_public_cache(tmp_path: Path) -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json=payload())

    with HTTPClient(
        TAIPOWER_HOSTS,
        cache_directory=tmp_path,
        config=HTTPConfig(minimum_interval_seconds=0),
        transport=httpx.MockTransport(handler),
    ) as http:
        client = TaipowerClient(http)
        first, second = client.latest(), client.latest()
    assert len(calls) == 2 and not list(tmp_path.iterdir())
    assert first.requests[0].sha256 == second.requests[0].sha256


def test_real_snapshot_hash_and_scope() -> None:
    raw = (DATA / "generation_taipower.json").read_bytes()
    manifest = json.loads((DATA / "generation_taipower_provenance.json").read_text())
    assert hashlib.sha256(raw).hexdigest() == manifest["fixture_sha256"]
    frame = parse_generation(json.loads(raw))
    assert len(frame) > 100 and frame.timestamp.nunique() == 1
    assert not frame.is_aggregate.any() and frame.flow.eq("generation").all()
    assert {"solar", "wind", "hydro", "gas"} <= set(frame.technology)
    complete = parse_generation(json.loads(raw), include_aggregates=True, include_storage_load=True)
    assert len(complete) == len(json.loads(raw)["aaData"])
    assert complete.value.isna().any()
