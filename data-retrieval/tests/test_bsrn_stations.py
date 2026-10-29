"""The official BSRN inventory supplies locations, not verified monthly data."""

from __future__ import annotations

import csv
import io
from pathlib import Path

import httpx
import pandas as pd
import pytest

from energy_data_retrieval.sources.bsrn.stations import (
    STATION_HOSTS,
    STATIONS_ENDPOINT,
    fetch_stations,
    normalize_stations,
    save_stations,
)
from energy_data_retrieval.station_discovery import load_station_catalogue
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, RetrievalError


def catalogue(*, changes: dict[str, str] | None = None) -> str:
    first = {
        "Event, optional label": "Synthetic Izaña",
        "Event label": "IZA",
        "Location": "Tenerife, Spain",
        "Station info": "",
        "Latitude": "28.3093",
        "Longitude": "-16.4993",
        "Elevation": "2372.9",
        "Date/Time start": "2009-03-01",
        "Date/Time end": "",
        "Comment": "Synthetic mountain-top metadata; station relocation remains native.",
        "URI of event": "https://bsrn.aemet.es/",
    }
    first.update(changes or {})
    second = dict(
        first,
        **{
            "Event, optional label": "Synthetic closed event",
            "Event label": "E13",
            "Latitude": "36.605",
            "Longitude": "-97.485",
            "Elevation": "",
            "Date/Time start": "1997-08-01",
            "Date/Time end": "2016-06-30",
        },
    )
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=list(first), delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows([first, second])
    return out.getvalue()


def test_native_station_identity_missing_elevation_and_event_dates_are_preserved() -> None:
    result = normalize_stations(catalogue()).set_index("station_id")
    assert set(result.index) == {"iza", "e13"}
    assert result.loc["iza", "station_name"] == "Synthetic Izaña"
    assert result.loc["iza", "source:Event label"] == "IZA"
    assert result.loc["iza", "latitude"] == 28.3093
    assert result.loc["iza", "longitude"] == -16.4993
    assert result.loc["iza", "elevation_m"] == 2372.9
    assert pd.isna(result.loc["e13", "elevation_m"])
    assert result.loc["e13", "catalogue_end"] == "2016-06-30"
    assert result.loc["iza", "catalogue_end"] is None
    assert bool(result.loc["iza", "retrieval_supported"])
    assert not bool(result.loc["e13", "retrieval_supported"])
    assert "available_to" not in result
    assert not result.attrs["event_dates_are_observation_coverage"]
    assert not result.attrs["availability_inferred"]


@pytest.mark.parametrize(
    "changes",
    [
        {"Latitude": "91"},
        {"Longitude": "181"},
        {"Latitude": "nan"},
        {"Elevation": "infinity"},
        {"Event label": "long-code"},
        {"Event label": "E13"},
        {"Event, optional label": " "},
        {"Date/Time start": "2026-02-30"},
        {"Date/Time end": "1999-01-01"},
    ],
)
def test_malformed_inventory_fails_instead_of_becoming_empty(changes: dict[str, str]) -> None:
    with pytest.raises(RetrievalError):
        normalize_stations(catalogue(changes=changes))


def test_inventory_bounds_header_and_truncation_are_checked() -> None:
    with pytest.raises(RetrievalError, match="bound"):
        normalize_stations(catalogue(), maximum_stations=1)
    with pytest.raises(ValueError, match="maximum_stations"):
        normalize_stations(catalogue(), maximum_stations=True)
    with pytest.raises(RetrievalError, match="incomplete"):
        normalize_stations(catalogue().rstrip())
    with pytest.raises(RetrievalError, match="header"):
        normalize_stations(catalogue().replace("Latitude", "Unknown", 1))


def test_inventory_acquisition_native_snapshot_and_offline_reuse(tmp_path: Path) -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert str(request.url).split("?")[0] == STATIONS_ENDPOINT
        assert dict(request.url.params) == {"format": "textfile"}
        return httpx.Response(200, text=catalogue())

    with HTTPClient(
        STATION_HOSTS,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        result = fetch_stations(http)
    path = tmp_path / "stations.parquet"
    saved = save_stations(result, path)
    assert saved.rows == 2
    assert path.with_suffix(".parquet.source.tsv").read_text() == catalogue()
    reused = load_station_catalogue("bsrn", None, local_path=path)
    assert reused.status == "local_catalogue"
    assert reused.coverage_scope["provider_catalogue_complete"]
    assert len(reused.frame) == 2
    assert len(calls) == 1
    with pytest.raises(ValueError, match="already exists"):
        save_stations(result, path)
    path.with_suffix(".parquet.source.tsv").write_text(catalogue() + "tampered\n")
    assert load_station_catalogue("bsrn", None, local_path=path).status == "invalid_local_catalogue"


def test_missing_station_coordinates_are_kept_as_unavailable() -> None:
    frame = normalize_stations(catalogue(changes={"Latitude": ""}))
    assert not bool(frame.set_index("station_id").loc["iza", "coordinates_valid"])
    assert frame.attrs["invalid_coordinate_rows"] == 1
