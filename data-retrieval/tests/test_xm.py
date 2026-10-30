"""SIMEM actual-generation contracts, with synthetic unit tests and a real capture."""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import cast

import httpx
import pandas as pd
import pytest

from energy_data_retrieval.sources.xm import XM_HOSTS, XMClient, parse_generation
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, JSONValue, RetrievalError


def observation(
    day: str = "2024-06-01", *, version: str = "TXF", value: JSONValue = 1250
) -> dict[str, JSONValue]:
    return {
        "CodigoVariable": "GReal",
        "FechaHora": day + " 00:00:00",
        "CodigoDuracion": "PT1H",
        "UnidadMedida": "kWh",
        "CodigoSICAgente": "AGENT",
        "CodigoPlanta": "PLANT",
        "Version": version,
        "Valor": value,
    }


def payload(rows: list[dict[str, JSONValue]] | None = None) -> dict[str, JSONValue]:
    return {
        "success": True,
        "result": {
            "idDataset": "055A4D",
            "metadata": {"granularity": "Horaria", "lastUpdate": "2024-06-07 01:00:00"},
            "records": cast(list[JSONValue], rows if rows is not None else [observation()]),
        },
    }


def test_actual_unit_conversion_source_clock_and_revision_selection() -> None:
    frame = parse_generation(payload([observation(), observation(version="TX1", value=9999)]))
    assert len(frame) == 1 and frame["value"].iloc[0] == 1.25
    assert frame["source_value"].iloc[0] == 1250 and frame["source_unit"].iloc[0] == "kWh"
    assert frame["unit"].iloc[0] == "MWh"
    assert frame["timestamp"].iloc[0] == pd.Timestamp("2024-06-01T05:00Z")
    assert frame.attrs["available_versions"] == ["TX1", "TXF"]
    with pytest.raises(RetrievalError, match="unavailable"):
        parse_generation(payload([observation(version="TX1")]))


def test_null_negative_zero_empty_and_conflicting_duplicates() -> None:
    for value in [None, 0, -10]:
        frame = parse_generation(payload([observation(value=value)]))
        assert (
            pd.isna(frame["value"].iloc[0])
            if value is None
            else frame["value"].iloc[0] == value / 1000
        )
    empty = parse_generation(payload([]))
    assert empty.empty and str(empty["timestamp"].dtype) == "datetime64[ns, UTC]"
    one = observation()
    assert len(parse_generation(payload([one, copy.deepcopy(one)]))) == 1
    with pytest.raises(RetrievalError, match="conflicting"):
        parse_generation(payload([one, observation(value=42)]))


@pytest.mark.parametrize("value", ["1", True, float("inf"), float("nan"), {}])
def test_invalid_measurement_encodings_fail(value: JSONValue) -> None:
    with pytest.raises(RetrievalError):
        parse_generation(payload([observation(value=value)]))


@pytest.mark.parametrize(
    "key,value",
    [
        ("CodigoVariable", "GProg"),
        ("UnidadMedida", "MW"),
        ("CodigoDuracion", "P1D"),
        ("FechaHora", "2024-06-01 00:30:00"),
    ],
)
def test_schedules_wrong_units_and_invalid_hour_rejected(key: str, value: str) -> None:
    row = observation()
    row[key] = value
    with pytest.raises(RetrievalError):
        parse_generation(payload([row]))


def test_wrong_dataset_granularity_errors_and_missing_value() -> None:
    root = payload()
    cast(dict, root["result"])["idDataset"] = "E17D25"
    with pytest.raises(RetrievalError, match="055A4D"):
        parse_generation(root)
    root = payload()
    cast(dict, root["result"])["metadata"]["granularity"] = "Diaria"
    with pytest.raises(RetrievalError, match="hourly"):
        parse_generation(root)
    with pytest.raises(RetrievalError, match="error document"):
        parse_generation({"success": False})
    row = observation()
    del row["Valor"]
    with pytest.raises(RetrievalError, match="omitted Valor"):
        parse_generation(payload([row]))


def test_http_date_chunks_server_revision_filter_and_provenance() -> None:
    calls: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        params = request.url.params
        assert params["datasetId"] == "055A4D" and params["columnDestinyName"] == "Version"
        assert params["values"] == "TXF" and params["startDate"] == params["endDate"]
        return httpx.Response(200, json=payload([observation(params["startDate"])]))

    with HTTPClient(
        XM_HOSTS,
        transport=httpx.MockTransport(handle),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        result = XMClient(http).generation(
            date(2024, 6, 1), date(2024, 6, 2), resource_ids=["PLANT"]
        )
        assert len(result.frame) == len(result.requests) == len(calls) == 2
        assert result.requests[0].parameters["values"] == "TXF"
        with pytest.raises(ValueError, match="maximum_requests"):
            XMClient(http, maximum_requests=1).generation(date(2024, 6, 1), date(2024, 6, 2))
        assert len(calls) == 2
        with pytest.raises(RetrievalError, match="maximum_rows"):
            XMClient(http, maximum_rows=1).generation(date(2024, 6, 1), date(2024, 6, 2))


def test_actual_capture_hash_and_three_complete_resource_profiles() -> None:
    data = Path(__file__).resolve().parents[2] / "examples/connectors/data"
    manifest = json.loads((data / "generation_xm_provenance.json").read_text())
    raw = (data / manifest["fixture"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == manifest["fixture_sha256"]
    frame = parse_generation(json.loads(raw))
    assert len(frame) == 72 and frame["unit_id"].nunique() == 3
    assert frame["version"].eq("TXF").all()
    assert frame.groupby("unit_id")["timestamp"].nunique().eq(24).all()
