"""AESO contracts; synthetic API cases and a genuine native historical capture."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import cast

import httpx
import pandas as pd
import pytest

from energy_data_retrieval.sources.aeso import (
    AESO_HOSTS,
    AESOClient,
    parse_current_generation,
    parse_generation_csv,
)
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, JSONValue, RetrievalError

HEADER = (
    "Date (MST),Date (MPT),Asset Short Name,Asset Name,Volume,"
    "Maximum Capability,System Capability,Fuel Type\r\n"
)


def native(value: str = "0") -> str:
    return (
        HEADER
        + f"2024-11-03 00:00:00,2024-11-03 01:00:00,AB1,Solar A,{value},100,95,SOLAR\r\n"
        + "2024-11-03 01:00:00,2024-11-03 01:00:00,AB1,Solar A,-2,100,95,SOLAR\r\n"
    )


def current(value: JSONValue = 12) -> dict[str, JSONValue]:
    return {
        "last_updated_datetime_utc": "2024-11-03 07:01",
        "last_updated_datetime_mpt": "2024-11-03 01:01",
        "asset_list": [
            {
                "asset": "AB1",
                "fuel_type": "SOLAR",
                "sub_fuel_type": "",
                "maximum_capability": 100,
                "net_generation": value,
                "dispatched_contingency_reserve": 4,
            }
        ],
    }


def test_native_fixed_mst_keeps_both_dst_fold_labels_and_mean_mw() -> None:
    frame = parse_generation_csv(native())
    assert frame["timestamp"].tolist() == [
        pd.Timestamp("2024-11-03T07:00Z"),
        pd.Timestamp("2024-11-03T08:00Z"),
    ]
    assert frame["Date (MPT)"].nunique() == 1
    assert frame["value"].tolist() == [0, -2]
    assert frame["Maximum Capability"].tolist() == [100, 100]
    assert frame["unit"].eq("MW").all() and frame["aggregation"].eq("60_minute_mean").all()
    assert parse_generation_csv(native(""))["value"].isna().iloc[0]


def test_native_five_minute_alignment_requires_explicit_product() -> None:
    text = native().replace("2024-11-03 00:00:00", "2024-11-03 00:05:00")
    assert len(parse_generation_csv(text, interval_minutes=5)) == 2
    with pytest.raises(RetrievalError, match="labels"):
        parse_generation_csv(text)
    with pytest.raises(ValueError, match="interval_minutes"):
        parse_generation_csv(native(), interval_minutes=15)


@pytest.mark.parametrize("value", ["bad", "inf", "-inf"])
def test_native_invalid_values_rejected(value: str) -> None:
    with pytest.raises(RetrievalError):
        parse_generation_csv(native(value))


def test_native_conflicts_schema_and_row_bound() -> None:
    text = native()
    assert len(parse_generation_csv(text + text.splitlines()[1] + "\n")) == 2
    with pytest.raises(RetrievalError, match="conflicting"):
        parse_generation_csv(text + native("9").splitlines()[1] + "\n")
    with pytest.raises(RetrievalError, match="native CSD"):
        parse_generation_csv(text.replace("Volume", "Installed Capacity"))
    with pytest.raises(RetrievalError, match="maximum_rows"):
        parse_generation_csv(text, maximum_rows=1)


def test_current_explicit_utc_net_generation_and_auxiliary_fields() -> None:
    frame = parse_current_generation(current(-3))
    assert frame["timestamp"].iloc[0] == pd.Timestamp("2024-11-03T07:01Z")
    assert frame["value"].iloc[0] == -3
    assert frame["maximum_capability_mw"].iloc[0] == 100
    assert frame["dispatched_contingency_reserve_mw"].iloc[0] == 4
    assert frame["aggregation"].iloc[0] == "snapshot"
    assert pd.isna(parse_current_generation(current(None))["value"].iloc[0])


@pytest.mark.parametrize("value", ["12", True, float("nan"), float("inf")])
def test_current_rejects_invalid_values(value: JSONValue) -> None:
    with pytest.raises(RetrievalError):
        parse_current_generation(current(value))


def test_current_missing_fields_and_conflicting_duplicates() -> None:
    root = current()
    assets = cast(list[dict], root["asset_list"])
    assets.append({**assets[0], "net_generation": 20})
    with pytest.raises(RetrievalError, match="conflicting"):
        parse_current_generation(root)
    root = current()
    del cast(list[dict], root["asset_list"])[0]["net_generation"]
    with pytest.raises(RetrievalError, match="omitted net_generation"):
        parse_current_generation(root)
    root = current()
    root["last_updated_datetime_utc"] = "2024-11-03T07:01Z"
    with pytest.raises(RetrievalError, match="timestamp"):
        parse_current_generation(root)


def test_api_secret_header_scope_and_provenance() -> None:
    calls: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert request.headers["API-KEY"] == "synthetic-test-key"
        assert request.url.params["assetIds"] == "AB1"
        assert request.url.path.endswith("/v1/csd/generation/assets/current")
        root = current()
        assets = cast(list[dict], root["asset_list"])
        assets.append({**assets[0], "asset": "EXTRA"})
        return httpx.Response(200, json=root)

    with HTTPClient(
        AESO_HOSTS,
        transport=httpx.MockTransport(handle),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        result = AESOClient(http).current_generation(
            api_key="synthetic-test-key", asset_ids=["AB1"]
        )
        assert len(calls) == len(result.requests) == len(result.frame) == 1
        assert "synthetic-test-key" not in repr(result.requests)
        assert result.requests[0].parameters == {"assetIds": "AB1"}
        with pytest.raises(ValueError):
            AESOClient(http).current_generation(api_key="")
        with pytest.raises(ValueError, match=r"1\.\.20"):
            AESOClient(http).current_generation(
                api_key="synthetic-test-key", asset_ids=["AB1"] * 21
            )
        assert len(calls) == 1


def test_bounded_native_file_import_records_actual_bytes_without_http(tmp_path: Path) -> None:
    path = tmp_path / "source.csv"
    raw = native().encode()
    path.write_bytes(raw)

    def forbidden(_: httpx.Request) -> httpx.Response:
        pytest.fail("Local imports must not perform HTTP requests")

    with HTTPClient(AESO_HOSTS, transport=httpx.MockTransport(forbidden)) as http:
        result = AESOClient(http).from_native_file(path)
        assert result.requests == () and len(result.frame) == 2
        assert result.frame.attrs["local_file_sha256"] == hashlib.sha256(raw).hexdigest()
        assert result.frame.attrs["local_file_size_bytes"] == len(raw)
        with pytest.raises(RetrievalError, match="maximum_bytes"):
            AESOClient(http).from_native_file(path, maximum_bytes=10)


def test_real_capture_native_bytes_full_week_and_solar_units() -> None:
    data = Path(__file__).resolve().parents[2] / "examples/connectors/data"
    manifest = json.loads((data / "generation_aeso_provenance.json").read_text())
    raw = (data / manifest["fixture"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == manifest["fixture_sha256"]
    assert b"\r\n" in raw
    frame = parse_generation_csv(raw.decode())
    assert len(frame) == 336 and frame["unit_id"].nunique() == 2
    assert frame["technology"].eq("SOLAR").all()
    assert frame.groupby("unit_id")["timestamp"].nunique().eq(168).all()
