"""Offline command workflows for explicit BSRN and current NOAA station sources."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Callable
from pathlib import Path

import httpx
import pandas as pd
import pytest

from energy_data_retrieval import cli
from energy_data_retrieval.sources.bsrn import REFERENCE_IDS as BSRN_REFERENCES
from energy_data_retrieval.sources.noaa.client import REFERENCE_IDS as NOAA_REFERENCES
from energy_data_retrieval.transport import HTTPClient, HTTPConfig

DOI = "10.1594/PANGAEA.725795"
NOAA_STATION = "USW00014732"


def offline_client(
    monkeypatch: pytest.MonkeyPatch, handler: Callable[[httpx.Request], httpx.Response]
) -> None:
    def factory(allowed_hosts: frozenset[str], *, config: HTTPConfig | None = None) -> HTTPClient:
        return HTTPClient(
            allowed_hosts,
            config=config,
            transport=httpx.MockTransport(handler),
            sleep=lambda _: None,
        )

    monkeypatch.setattr(cli, "HTTPClient", factory)


def bsrn_export() -> str:
    return (
        "/* DATA DESCRIPTION:\n"
        f"Citation:\tSynthetic fixture. https://doi.org/{DOI}\n"
        "Project(s):\tBaseline Surface Radiation Network (BSRN)\n"
        "Event(s):\tCAB (Synthetic station)\n"
        "License:\tSynthetic fixture license\n"
        "*/\n"
        "Date/Time\tSWD [W/m**2]\tDIR [W/m**2]\n"
        "2009-06-01T00:00\t-1\t0\n"
        "2009-06-01T00:01\t\t?5\n"
    )


def noaa_export(year: int, station_id: str = NOAA_STATION) -> str:
    label = f"{year}-12-31T23:51:00" if year == 2025 else f"{year}-01-01T00:15:00"
    stamp = pd.Timestamp(label)
    row = {
        "STATION": station_id,
        "Station_name": "Synthetic station",
        "DATE": label,
        "Year": str(year),
        "Month": str(stamp.month),
        "Day": str(stamp.day),
        "Hour": str(stamp.hour),
        "Minute": str(stamp.minute),
        "LATITUDE": "40.779",
        "LONGITUDE": "-73.880",
        "ELEVATION": "3.4",
    }
    values = {
        "temperature": "-0.6",
        "dew_point_temperature": "",
        "wind_speed": "0.0",
        "wind_gust": "3.6",
        "sea_level_pressure": "1013.2",
        "station_level_pressure": "",
        "wet_bulb_temperature": "",
        "altimeter": "1014.0",
        "visibility": "16.09",
    }
    for name, value in values.items():
        row[name] = value
        row[name + "_Measurement_Code"] = ""
        row[name + "_Quality_Code"] = "3"
        row[name + "_Report_Type"] = "FM-15"
        row[name + "_Source_Code"] = "fixture"
        row[name + "_Source_Station_ID"] = "fixture-id"
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=list(row), delimiter="|", lineterminator="\n")
    writer.writeheader()
    writer.writerow(row)
    return stream.getvalue()


def test_bsrn_cli_search_retrieve_and_verified_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.host == "www.pangaea.de":
            assert "event:CAB" in request.url.params["q"]
            return httpx.Response(
                200, json={"totalCount": 1, "offset": 0, "results": [{"URI": "doi:" + DOI}]}
            )
        assert request.url.path == "/" + DOI
        if request.url.params["format"] == "metadata_jsonld":
            return httpx.Response(
                200,
                json={
                    "@type": "Dataset",
                    "identifier": DOI,
                    "name": "Basic measurements of radiation at station Cabauw (2009-06)",
                    "creator": {"name": "Synthetic investigator"},
                    "license": "Synthetic fixture license",
                    "temporalCoverage": "2009-06-01T00:00:00/2009-06-01T00:01:00",
                },
            )
        assert request.url.params["format"] == "textfile"
        return httpx.Response(200, content=bsrn_export().encode())

    offline_client(monkeypatch, handler)
    selection = ["--station", "cab", "--year", "2009", "--month", "6", "--request-interval", "0"]
    search_path = tmp_path / "search.json"
    assert cli.main(["bsrn-search", *selection, "--output", str(search_path)]) == 0
    search = json.loads(search_path.read_text())
    assert search["candidate_validation_required"] is True
    assert search["candidates"][0]["doi"] == DOI
    destination = tmp_path / "cab.parquet"
    command = ["bsrn-dataset", *selection, "--doi", DOI, "--output", str(destination)]
    assert cli.main(command) == cli.main(command) == 0
    assert len(calls) == 3
    saved = pd.read_parquet(destination)
    assert saved["timestamp"].dt.minute.tolist() == [0, 1]
    assert saved["swd_wm2"].iloc[0] == -1 and pd.isna(saved["swd_wm2"].iloc[1])
    assert saved["dir_wm2_qualifier"].iloc[1] == "?"
    assert destination.with_suffix(".parquet.source.tsv").read_text() == bsrn_export()


def test_noaa_catalogue_cli_filters_iso_country_and_geographic_box(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    catalogue = (
        "GHCN_ID,LATITUDE,LONGITUDE,ELEVATION,NAME,ISO_CODE\n"
        "SP000060015,28.477,-16.320,632.0,Synthetic Tenerife,ES\n"
        "USW00014732,40.779,-73.880,3.4,Synthetic New York,US\n"
    )
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, content=catalogue.encode())

    offline_client(monkeypatch, handler)
    destination = tmp_path / "stations.parquet"
    command = [
        "noaa-stations",
        "--country-code",
        "es",
        "--bbox",
        "-18",
        "27",
        "-13",
        "30",
        "--output",
        str(destination),
    ]
    assert cli.main(command) == cli.main(command) == 0
    assert calls == 1
    saved = pd.read_parquet(destination)
    assert saved["country_code"].tolist() == ["ES"]
    assert saved["country_fips"].tolist() == ["SP"]


@pytest.mark.parametrize("station_id", [NOAA_STATION, "CAU0mt_st-1"])
def test_noaa_cli_partitions_years_preserves_native_observations_and_reuses_snapshots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, station_id: str
) -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        year = int(request.url.path.split("/by-year/", 1)[1].split("/", 1)[0])
        calls.append(year)
        assert request.url.path.endswith(f"GHCNh_{station_id}_{year}.psv")
        return httpx.Response(200, content=noaa_export(year, station_id).encode())

    offline_client(monkeypatch, handler)
    destination = tmp_path / "noaa"
    command = [
        "noaa-observations",
        "--station",
        station_id,
        "--start",
        "2025-12-31",
        "--end",
        "2026-01-01",
        "--request-interval",
        "0",
        "--output",
        str(destination),
    ]
    assert cli.main(command) == cli.main(command) == 0
    assert calls == [2025, 2026]
    paths = sorted(destination.rglob("*.parquet"))
    assert len(paths) == 2
    for path in paths:
        assert all(part == part.lower() for part in path.relative_to(destination).parts[:-1])
        saved = pd.read_parquet(path)
        assert saved["station_id"].tolist() == [station_id]
        assert saved["temperature_c"].iloc[0] == -0.6
        assert saved["wind_speed_ms"].iloc[0] == 0
        assert saved["temperature_Quality_Code"].iloc[0] == "3"
        assert saved["timestamp"].dt.minute.iloc[0] in {15, 51}
        assert "ghi_wm2" not in saved


def test_invalid_station_paths_and_excessive_years_fail_before_requests(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden(_: httpx.Request) -> httpx.Response:
        pytest.fail("Invalid requests must fail before provider access")

    offline_client(monkeypatch, forbidden)
    common = ["--start", "2025-12-31", "--end", "2026-01-01", "--output", str(tmp_path / "noaa")]
    with pytest.raises(SystemExit) as traversal:
        cli.main(["noaa-observations", "--station", "../../bad", *common])
    with pytest.raises(SystemExit) as limit:
        cli.main(["noaa-observations", "--station", NOAA_STATION, *common, "--maximum-years", "1"])
    assert traversal.value.code == limit.value.code == 2
    assert list(tmp_path.iterdir()) == []


def test_station_reference_ids_resolve_to_the_thesis_first_catalogue() -> None:
    root = Path(__file__).resolve().parents[2]
    catalogue = json.loads((root / "methods/src/energy_methods/references.json").read_text())
    known = {entry["id"] for entry in catalogue}
    for ids in (BSRN_REFERENCES, NOAA_REFERENCES):
        assert ids[0] == catalogue[0]["id"] == "ascencio_vasquez_2021_thesis"
        assert set(ids) <= known
