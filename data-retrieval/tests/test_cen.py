"""CEN source-schema fixtures are synthetic and contain no live credentials."""

from __future__ import annotations

from datetime import date

import httpx
import pandas as pd
import pytest

from energy_data_retrieval.sources.cen import (
    CENClient,
    aggregate_units,
    normalize_generation,
    normalize_registry,
)
from energy_data_retrieval.sources.cen.client import CEN_HOSTS
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, JSONValue, RetrievalError


def row(
    power: float | None = 0.0, *, unit: int = 1, time: str = "2026-10-27 09:00:00"
) -> dict[str, JSONValue]:
    return {
        "id_central": 10,
        "id_opreal": unit,
        "fecha_hora": time,
        "gen_real_mw": power,
        "tipo_tecnologia": "Solar",
    }


def envelope(page: int, rows: list[JSONValue], pages: int = 2) -> dict[str, JSONValue]:
    return {
        "page": page,
        "pageSize": 2,
        "totalPages": pages,
        "startDate": "2026-10-27",
        "endDate": "2026-10-27",
        "data": rows,
    }


def test_pagination_and_zero_missing_normalization() -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params["page"])
        calls.append(page)
        return httpx.Response(
            200, json=envelope(page, [row(0.0 if page == 1 else None, unit=page)])
        )

    with HTTPClient(
        CEN_HOSTS,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        result = CENClient(http, "synthetic-key", page_size=2).generation_day(date(2026, 10, 27))
    assert calls == [1, 2]
    assert result.units["actual_mwh"].iloc[0] == 0
    assert pd.isna(result.units["actual_mwh"].iloc[1])
    assert result.units["timestamp"].iloc[0] == pd.Timestamp("2026-10-27T12:00:00Z")
    assert len(result.requests) == 2
    assert result.exclusions.empty


def test_changed_pagination_fails() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params["page"])
        return httpx.Response(200, json=envelope(page, [row()], pages=2 if page == 1 else 3))

    with (
        HTTPClient(
            CEN_HOSTS,
            transport=httpx.MockTransport(handler),
            config=HTTPConfig(minimum_interval_seconds=0),
        ) as http,
        pytest.raises(RetrievalError, match="pagination changed"),
    ):
        CENClient(http, "synthetic-key", page_size=2).generation_day(date(2026, 10, 27))


def test_dst_nonexistent_is_audited_and_ambiguous_rejected() -> None:
    frame, excluded = normalize_generation(
        [row(time="2026-09-06 00:00:00"), row(time="2026-09-06 01:00:00")]
    )
    assert len(frame) == 1 and len(excluded) == 1
    assert excluded["reason"].iloc[0] == "nonexistent_civil_clock_label"
    with pytest.raises(RetrievalError, match="Ambiguous"):
        normalize_generation([row(time="2026-04-04 23:00:00")])


def test_duplicates_and_missing_identity() -> None:
    duplicate = row(3)
    missing = dict(row(4), id_central=None)
    frame, excluded = normalize_generation([duplicate, duplicate, missing])
    assert len(frame) == 1 and len(excluded) == 1
    with pytest.raises(RetrievalError, match="Conflicting"):
        normalize_generation([row(0), row(None)])


def test_roster_blocks_partial_site_totals() -> None:
    units, _ = normalize_generation([row(4, unit=1), row(None, unit=2)])
    result = aggregate_units(units, {"10": frozenset({"1", "2"})})
    assert result["reported_mwh"].iloc[0] == 4
    assert pd.isna(result["actual_mwh"].iloc[0])
    assert not result["generation_complete"].iloc[0]
    units, _ = normalize_generation([row(0, unit=1), row(0, unit=2)])
    result = aggregate_units(units, {"10": frozenset({"1", "2"})})
    assert result["actual_mwh"].iloc[0] == 0 and result["generation_complete"].iloc[0]
    with pytest.raises(ValueError, match="verified site roster"):
        aggregate_units(units, {"10": frozenset({"1"})})


def test_registry_does_not_invent_dc_capacity() -> None:
    frame = normalize_registry(
        [
            {
                "id": 10,
                "nombre": "Synthetic PV",
                "latitud": -34,
                "longitud": -71,
                "potencia_maxima": 10,
            }
        ]
    )
    assert frame["site_id"].iloc[0] == "10"
    assert frame["reported_maximum_power_mw"].iloc[0] == 10
    assert frame["dc_capacity_mw"].isna().all()
    assert frame["ac_capacity_mw"].isna().all()
    assert not frame["dc_capacity_qualified"].any()
