"""RTE actual generation, forecast-only gaps and Explore API pagination."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from datetime import date
from pathlib import Path

import httpx
import pandas as pd
import pytest

from energy_data_retrieval.sources.rte import RTE_HOSTS, RTEClient, normalize_generation
from energy_data_retrieval.sources.rte.client import TECHNOLOGIES
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, JSONValue, RetrievalError


def row(label: str, value: JSONValue = 0) -> dict[str, JSONValue]:
    return {
        "perimetre": "France",
        "nature": "Données définitives",
        "date_heure": label,
        **dict.fromkeys(TECHNOLOGIES, value),
    }


def page(rows: Sequence[JSONValue], total: int | None = None) -> dict[str, JSONValue]:
    return {"total_count": len(rows) if total is None else total, "results": list(rows)}


def test_actual_half_hours_missing_values_and_non_overlapping_technology_levels() -> None:
    values = [
        row("2024-06-01T00:00:00Z"),
        row("2024-06-01T00:15:00Z", None),
        row("2024-06-01T00:30:00Z", None),
    ]
    values[0].update({"solaire": -2, "gaz_ccg": 999, "pompage": -500, "consommation": 100000})
    result = normalize_generation(page(values))
    assert len(result) == 16
    assert result.attrs["excluded_forecast_only_rows"] == 1
    assert set(result.technology) == set(TECHNOLOGIES)
    assert result.loc[result.technology.eq("solaire"), "value"].iloc[0] == -2
    assert result.loc[result.timestamp.eq(pd.Timestamp("2024-06-01T00:30Z")), "value"].isna().all()
    assert result.unit.unique().tolist() == ["MW"]


def test_dst_offsets_preserved_without_collapsing_local_hour() -> None:
    result = normalize_generation(
        page([row("2024-10-27T02:00:00+02:00"), row("2024-10-27T02:00:00+01:00")])
    )
    assert sorted(result.timestamp.unique()) == [
        pd.Timestamp("2024-10-27T00:00Z"),
        pd.Timestamp("2024-10-27T01:00Z"),
    ]


@pytest.mark.parametrize("value", [True, "nan", "infinity", "bad", {}])
def test_invalid_numbers_and_unexpected_live_data(value: JSONValue) -> None:
    with pytest.raises(RetrievalError):
        normalize_generation(page([row("2024-06-01T00:00:00Z", value)]))


def test_schema_and_conflicting_records() -> None:
    with pytest.raises(RetrievalError, match="quarter-hour forecast"):
        normalize_generation(page([row("2024-06-01T00:15:00Z", 1)]))
    with pytest.raises(RetrievalError, match="offset"):
        normalize_generation(page([row("2024-06-01T00:00:00")]))
    with pytest.raises(RetrievalError, match="Conflicting"):
        normalize_generation(page([row("2024-06-01T00:00:00Z", 1), row("2024-06-01T00:00:00Z", 2)]))
    with pytest.raises(RetrievalError, match="consolidated"):
        normalize_generation(page([row("2024-06-01T00:00:00Z") | {"nature": "Données temps réel"}]))
    assert normalize_generation(page([])).empty


def test_paginated_fetch_and_provenance_use_french_civil_date() -> None:
    records = [
        row("2024-05-31T22:00:00Z"),
        row("2024-05-31T22:15:00Z", None),
        row("2024-05-31T22:30:00Z", 3),
    ]
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert "2024-05-31T22:00:00+00:00" in request.url.params["where"]
        assert "2024-06-01T22:00:00+00:00" in request.url.params["where"]
        offset = int(request.url.params["offset"])
        return httpx.Response(200, json=page(records[offset : offset + 2], total=3))

    with HTTPClient(
        RTE_HOSTS,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        result = RTEClient(http, page_size=2).generation(date(2024, 6, 1), date(2024, 6, 1))
    assert len(calls) == len(result.requests) == 2
    assert len(result.frame) == 16
    assert result.frame.attrs["excluded_forecast_only_rows"] == 1


@pytest.mark.parametrize("failure", ["repeat", "empty", "changed_total"])
def test_broken_pagination_fails_instead_of_truncating(failure: str) -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        record = row("2024-06-01T00:00:00Z")
        if calls == 1:
            return httpx.Response(200, json=page([record], total=2))
        return httpx.Response(
            200,
            json=page(
                [] if failure == "empty" else [record], total=3 if failure == "changed_total" else 2
            ),
        )

    with (
        HTTPClient(
            RTE_HOSTS,
            transport=httpx.MockTransport(handler),
            config=HTTPConfig(minimum_interval_seconds=0),
        ) as http,
        pytest.raises(RetrievalError, match="pagination"),
    ):
        RTEClient(http, page_size=1).generation(date(2024, 6, 1), date(2024, 6, 1))
    assert calls == 2


def test_real_snapshot_hash_and_quarter_hour_forecast_exclusion() -> None:
    data = Path(__file__).resolve().parents[2] / "examples/connectors/data"
    raw = (data / "generation_rte.json").read_bytes()
    manifest = json.loads((data / "generation_rte_provenance.json").read_text())
    assert hashlib.sha256(raw).hexdigest() == manifest["files"][0]["sha256"]
    frame = normalize_generation(json.loads(raw))
    assert len(frame) == 384
    assert frame.timestamp.nunique() == 48
    assert frame.attrs["excluded_forecast_only_rows"] == 48
