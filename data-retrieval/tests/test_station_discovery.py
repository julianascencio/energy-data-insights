"""Discovery preserves inventory scope and reports failures independently of distance."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import cast

import httpx
import pandas as pd
import pytest

from energy_data_retrieval.sources.aemet import AEMETClient
from energy_data_retrieval.sources.noaa import NOAAClient
from energy_data_retrieval.sources.noaa.client import STATIONS_ENDPOINT as NOAA_ENDPOINT
from energy_data_retrieval.station_discovery import (
    STATION_DISCOVERY_HOSTS,
    STATION_SOURCES,
    load_station_catalogue,
)
from energy_data_retrieval.storage import write_parquet
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, JSONValue, RetrievalError

_NOAA = (
    "GHCN_ID,LATITUDE,LONGITUDE,ELEVATION,NAME,ISO_CODE\n"
    "SPM00060020,28.48,-16.34,632,Synthetic Tenerife,ES\n"
    "USW00094728,40.78,-73.97,39,Synthetic New York,US\n"
)
_BBOX = (-18.0, 27.0, -13.0, 30.0)
_KEY = "synthetic-discovery-fixture-key"


def _http(handler) -> HTTPClient:
    return HTTPClient(
        STATION_DISCOVERY_HOSTS,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(attempts=1, minimum_interval_seconds=0),
    )


def _json(value: object) -> dict[str, JSONValue]:
    return cast(dict[str, JSONValue], json.loads(json.dumps(value)))


def test_fresh_catalogue_is_fetched_once_without_a_spatial_filter() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert str(request.url) == NOAA_ENDPOINT
        return httpx.Response(200, text=_NOAA)

    with _http(handler) as http:
        result = load_station_catalogue("noaa", http)
    assert result.status == "catalogue_loaded"
    assert len(calls) == 1 and len(result.requests) == 1
    assert result.frame.source.tolist() == ["noaa", "noaa"]
    assert result.frame.station_id.tolist() == ["SPM00060020", "USW00094728"]
    assert result.coverage_scope["provider_catalogue_complete"]
    assert not result.coverage_scope["observations_verified"]
    assert not result.frame.attrs["station_variable_availability_verified"]
    assert "temperature" in result.frame.attrs["product_supported_variables"]
    assert "GHCN_ID" in result.frame


def test_filtered_saved_noaa_inventory_retains_spatial_country_scope(tmp_path: Path) -> None:
    with _http(lambda _: httpx.Response(200, text=_NOAA)) as http:
        catalogue = NOAAClient(http).stations(country_code="ES", bbox=_BBOX)
    path = tmp_path / "stations.parquet"
    write_parquet(
        catalogue.frame,
        path,
        request={
            "source": "NOAA GHCNh station catalogue",
            "endpoint": NOAA_ENDPOINT,
            "country_code_iso": "ES",
            "bbox_west_south_east_north": list(_BBOX),
        },
        provenance=_json({"request": asdict(catalogue.request), "metadata": catalogue.frame.attrs}),
    )
    result = load_station_catalogue("noaa", None, local_path=path)
    assert result.status == "local_catalogue" and len(result.frame) == 1
    assert not result.coverage_scope["provider_catalogue_complete"]
    assert result.coverage_scope["bbox_west_south_east_north"] == list(_BBOX)
    assert result.coverage_scope["country_code_filter"] == "ES"
    assert result.frame.attrs["source_station_rows"] == 2
    assert any("filtered" in note for note in result.notes)
    with path.open("ab") as out:
        out.write(b"tamper")
    assert load_station_catalogue("noaa", None, local_path=path).status == "invalid_local_catalogue"


def _aemet_handler(request: httpx.Request) -> httpx.Response:
    if request.url.path.startswith("/opendata/api/"):
        assert request.headers["api_key"] == _KEY
        return httpx.Response(
            200,
            json={
                "estado": 200,
                "datos": "https://opendata.aemet.es/opendata/sh/data",
                "metadatos": "https://opendata.aemet.es/opendata/sh/meta",
            },
        )
    if request.url.path.endswith("/meta"):
        return httpx.Response(200, json={"campos": [{"id": "latitud"}, {"id": "longitud"}]})
    return httpx.Response(
        200,
        json=[
            {
                "indicativo": "C447A",
                "nombre": "Synthetic Tenerife",
                "latitud": "282900N",
                "longitud": "161800W",
                "altitud": "632",
                "provincia": "Tenerife",
            },
            {
                "indicativo": "B893",
                "nombre": "Synthetic other",
                "latitud": "400000N",
                "longitud": "0030000E",
                "altitud": "10",
            },
        ],
    )


def test_fresh_aemet_status_and_verified_restart_without_credentials(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("AEMET_API_KEY", _KEY)
    path = tmp_path / "stations.parquet"
    with _http(_aemet_handler) as http:
        fresh = load_station_catalogue("aemet", http)
        assert fresh.status == "catalogue_loaded" and len(fresh.frame) == 2
        AEMETClient.from_environment(http).retrieve_stations(path, bbox=_BBOX)
    monkeypatch.delenv("AEMET_API_KEY")
    reused = load_station_catalogue("aemet", None, local_path=path)
    assert reused.status == "local_catalogue" and len(reused.frame) == 1
    assert reused.frame["source:indicativo"].tolist() == ["C447A"]
    assert reused.frame.attrs["source_station_rows"] == 2
    assert not reused.coverage_scope["provider_catalogue_complete"]
    assert _KEY not in json.dumps(reused.requests)


@pytest.mark.parametrize("suffix", [".source.json", ".metadata.json", ".envelope.json"])
def test_aemet_rejects_tampered_native_sidecars_without_live_fallback(
    suffix: str, tmp_path: Path
) -> None:
    path = tmp_path / "stations.parquet"
    with _http(_aemet_handler) as http:
        AEMETClient(http, _KEY).retrieve_stations(path)
    path.with_suffix(path.suffix + suffix).write_text("{}")

    def no_network(_: httpx.Request) -> httpx.Response:
        raise AssertionError("Invalid local snapshot must not trigger network access")

    with _http(no_network) as http:
        result = load_station_catalogue("aemet", http, local_path=path)
    assert result.status == "invalid_local_catalogue"


def test_missing_aemet_key_is_an_explicit_nonempty_status(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AEMET_API_KEY", raising=False)

    def no_network(_: httpx.Request) -> httpx.Response:
        raise AssertionError("Missing credentials must not trigger network access")

    with _http(no_network) as http:
        result = load_station_catalogue("aemet", http)
    assert result.status == "credentials_required"
    assert result.frame.empty
    assert set(result.frame.columns) >= {"source", "station_id", "latitude", "longitude"}
    assert not result.coverage_scope["provider_catalogue_complete"]


def test_provider_failure_omits_exception_contents_and_does_not_claim_absence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(*_args, **_kwargs):
        raise RetrievalError("arbitrary credential-bearing provider exception")

    monkeypatch.setattr(NOAAClient, "stations", fail)
    with _http(lambda _: httpx.Response(500)) as http:
        result = load_station_catalogue("noaa", http)
    assert result.status == "provider_error"
    assert "credential-bearing" not in str(result)
    assert "no_nearby" not in result.status
    assert not result.coverage_scope["provider_catalogue_complete"]


@pytest.mark.parametrize("source", STATION_SOURCES)
def test_unrequested_sources_and_missing_files_are_not_success(source: str, tmp_path: Path) -> None:
    assert load_station_catalogue(source, None).status == "not_requested"
    assert load_station_catalogue(source, None, local_path=tmp_path / "missing.parquet").status == (
        "invalid_local_catalogue"
    )


def test_other_source_snapshot_is_not_reused(tmp_path: Path) -> None:
    path = tmp_path / "wrong.parquet"
    frame = pd.DataFrame({"station_id": ["x"], "latitude": [0], "longitude": [0]})
    write_parquet(frame, path, request={"source": "other"}, provenance={})
    assert load_station_catalogue("noaa", None, local_path=path).status == "invalid_local_catalogue"
    with pytest.raises(ValueError, match="Unknown station source"):
        load_station_catalogue("unknown", None)
