"""REE generation contracts, using synthetic JSON unless explicitly stated."""

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

from energy_data_retrieval.sources.ree import REE_HOSTS, REEClient, normalize_generation
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, JSONValue, RetrievalError


def payload(labels: list[str] | None = None) -> dict[str, JSONValue]:
    stamps = labels or ["2024-10-27T00:00:00+02:00", "2024-10-28T00:00:00+01:00"]
    return {
        "data": {"id": "gen1", "type": "Generación por tecnología"},
        "included": [
            {
                "id": identifier,
                "attributes": {
                    "title": title,
                    "type": kind,
                    "magnitude": None,
                    "composite": False,
                    "last-update": "2026-10-01T10:00:00+02:00",
                    "values": [
                        {"datetime": stamp, "value": value, "percentage": 0.2}
                        for stamp, value in zip(stamps, [0, None], strict=False)
                    ],
                },
            }
            for identifier, title, kind in [
                ("1458", "Solar fotovoltaica", "Renovable"),
                ("10296", "Generación total", "total"),
            ]
        ],
    }


def test_dst_labels_total_exclusion_zero_and_missing() -> None:
    result = normalize_generation(payload())
    assert result["timestamp"].tolist() == [
        pd.Timestamp("2024-10-26T22:00Z"),
        pd.Timestamp("2024-10-27T23:00Z"),
    ]
    assert result["value"].iloc[0] == 0
    assert pd.isna(result["value"].iloc[1])
    assert result["unit"].tolist() == ["MWh", "MWh"]
    assert result["technology_id"].unique().tolist() == ["1458"]
    assert result.attrs["excluded_total_rows"] == 2
    assert len(normalize_generation(payload(), include_total=True)) == 4


def test_duplicate_conflicts_negative_values_and_empty_data() -> None:
    raw = payload()
    entries = cast(list[dict], raw["included"])
    entries[0]["attributes"]["values"][0]["value"] = -2.5
    entries.append(copy.deepcopy(entries[0]))
    result = normalize_generation(raw)
    assert len(result) == 2 and result["value"].iloc[0] == -2.5
    entries[-1]["attributes"]["values"][0]["value"] = 1
    with pytest.raises(RetrievalError, match="conflicting"):
        normalize_generation(raw)
    raw["included"] = []
    empty = normalize_generation(raw)
    assert empty.empty and str(empty["timestamp"].dtype) == "datetime64[ns, UTC]"


@pytest.mark.parametrize("value", [True, "nan", "inf", "bad", {}])
def test_rejects_nonphysical_numeric_encodings(value: JSONValue) -> None:
    raw = payload()
    cast(list[dict], raw["included"])[0]["attributes"]["values"][0]["value"] = value
    with pytest.raises(RetrievalError):
        normalize_generation(raw)


@pytest.mark.parametrize("stamp", ["2024-10-27T00:00:00", "2024-10-27T01:00:00Z", "bad"])
def test_invalid_or_naive_period_labels(stamp: str) -> None:
    with pytest.raises(RetrievalError):
        normalize_generation(payload([stamp]))


def test_wrong_widget_unit_and_error_documents() -> None:
    raw = payload()
    cast(dict, raw["data"])["id"] = "installed-capacity"
    with pytest.raises(RetrievalError, match="gen1"):
        normalize_generation(raw)
    raw = payload()
    cast(list[dict], raw["included"])[0]["attributes"]["magnitude"] = "MW"
    with pytest.raises(RetrievalError, match="magnitude"):
        normalize_generation(raw)
    with pytest.raises(RetrievalError, match="API error"):
        normalize_generation({"errors": [{"code": 400}]})
    with pytest.raises(RetrievalError, match="maximum_rows"):
        normalize_generation(payload(), maximum_rows=1)


def test_request_chunks_geo_parameters_and_provenance() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        query = request.url.params
        assert query["geo_trunc"] == "electric_system"
        assert query["geo_limit"] == "canarias" and query["geo_ids"] == "8742"
        return httpx.Response(200, json=payload([query["start_date"] + ":00+01:00"]))

    with HTTPClient(
        REE_HOSTS,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        result = REEClient(http).generation(date(2023, 12, 31), date(2024, 1, 1), system="canarias")
    assert len(calls) == len(result.requests) == len(result.frame) == 2
    assert calls[0].url.params["end_date"] == "2023-12-31T23:59"
    assert result.frame["area"].unique().tolist() == ["canarias"]
    assert result.requests[1].parameters["start_date"] == "2024-01-01T00:00"


def test_monthly_query_requires_whole_months_and_accepts_leap_year() -> None:
    with HTTPClient(
        REE_HOSTS,
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, json=payload(["2024-02-01T00:00:00+01:00"]))
        ),
    ) as http:
        result = REEClient(http).generation(
            date(2024, 2, 1), date(2024, 2, 29), time_trunc="month", system="ccaa", geo_id="7"
        )
        assert result.frame["aggregation"].tolist() == ["month"]
        assert result.frame["area"].tolist() == ["ccaa:7"]
        with pytest.raises(ValueError, match="complete calendar"):
            REEClient(http).generation(date(2024, 2, 1), date(2024, 2, 28), time_trunc="month")
        with pytest.raises(ValueError, match="complete calendar years"):
            REEClient(http).generation(date(2024, 2, 1), date(2024, 2, 29), time_trunc="year")


def test_no_network_for_invalid_requests() -> None:
    def forbidden(_: httpx.Request) -> httpx.Response:
        pytest.fail("Invalid queries must fail before network access")

    with HTTPClient(REE_HOSTS, transport=httpx.MockTransport(forbidden)) as http:
        client = REEClient(http, maximum_requests=1)
        for time_trunc, system, geo_id in [
            ("hour", "national", None),
            ("day", "unknown", None),
            ("day", "ccaa", None),
            ("day", "national", "8741"),
        ]:
            with pytest.raises(ValueError):
                client.generation(
                    date(2024, 1, 1),
                    date(2024, 1, 2),
                    time_trunc=time_trunc,
                    system=system,
                    geo_id=geo_id,
                )
        with pytest.raises(ValueError, match="maximum_requests"):
            client.generation(date(2023, 1, 1), date(2024, 1, 1))


def test_does_not_accept_provider_ignoring_date_filter() -> None:
    with (
        HTTPClient(
            REE_HOSTS, transport=httpx.MockTransport(lambda _: httpx.Response(200, json=payload()))
        ) as http,
        pytest.raises(RetrievalError, match="outside"),
    ):
        REEClient(http).generation(date(2024, 1, 1), date(2024, 1, 2))


def test_real_gallery_snapshot_hash_and_technology_totals() -> None:
    root = Path(__file__).resolve().parents[2] / "examples/connectors/data"
    path = root / "generation_ree.json"
    manifest = json.loads((root / "generation_ree_provenance.json").read_text())
    assert hashlib.sha256(path.read_bytes()).hexdigest() == manifest["fixture_sha256"]
    frame = normalize_generation(json.loads(path.read_bytes()), include_total=True)
    assert frame["period"].nunique() == 30
    parts = frame.loc[~frame["is_total"]].groupby("period")["value"].sum(min_count=1)
    total = frame.loc[frame["is_total"]].set_index("period")["value"]
    # Provider values are published with limited precision; no correction is applied.
    assert (parts - total).abs().max() < 0.1
    assert set(frame["unit"]) == {"MWh"}
