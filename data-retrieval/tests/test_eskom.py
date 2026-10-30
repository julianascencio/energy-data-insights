"""Eskom catalogue discovery, strict scope and native renewable observations."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

import httpx
import pandas as pd
import pytest

from energy_data_retrieval.sources.eskom import ESKOM_HOSTS, EskomClient, parse_generation_csv
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, RetrievalError

CSV = (
    "Date Time Hour Beginning,Wind,PV,CSP,Other RE\n"
    "2024-01-01 00:00:00,30,0,-1,\n2024-01-02 00:00:00,50,0,1,2\n"
)
URL = "https://www.eskom.co.za/dataportal/wp-content/uploads/2024/01/Hourly_Generation.csv"


def test_native_hour_beginning_preserves_missing_and_signed_values() -> None:
    frame = parse_generation_csv(CSV)
    assert len(frame) == 8
    assert frame.timestamp.min() == pd.Timestamp("2023-12-31T22:00Z")
    assert frame.loc[frame.technology.eq("solar_thermal"), "value"].tolist() == [-1, 1]
    assert pd.isna(frame.loc[frame.technology.eq("other_renewable"), "value"].iloc[0])
    assert "embedded generation excluded" in frame.attrs["scope"]


def test_discovery_avoids_total_and_stale_uploads() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path.endswith("/media"):
            return httpx.Response(
                200,
                json=[
                    {"date": "2024-01-03", "source_url": URL.replace("Hourly_", "Total_Hourly_")},
                    {"date": "2024-01-02", "source_url": URL},
                    {"date": "2023-12-01", "source_url": URL.replace("2024/01", "2023/12")},
                ],
            )
        assert str(request.url) == URL
        return httpx.Response(200, text=CSV)

    with HTTPClient(
        ESKOM_HOSTS,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        result = EskomClient(http).generation(date(2024, 1, 2), date(2024, 1, 2))
    assert len(result.requests) == len(calls) == 2
    assert len(result.frame) == 4
    assert result.frame.timestamp.min() == pd.Timestamp("2024-01-01T22:00Z")


@pytest.mark.parametrize(
    "url",
    [
        "http://www.eskom.co.za/data.csv",
        URL.replace("eskom.co.za", "other.example"),
        URL + "?token=x",
        URL.replace("Hourly_", "Total_Hourly_"),
    ],
)
def test_only_official_hourly_renewable_exports_are_accepted(url: str) -> None:
    with HTTPClient(ESKOM_HOSTS) as http, pytest.raises(ValueError, match="official"):
        EskomClient(http).generation(url=url)


def test_invalid_schema_values_and_time() -> None:
    for invalid in (
        CSV.replace("Wind", "Unknown"),
        CSV.replace(",30,", ",inf,"),
        CSV.replace("00:00:00", "00:30:00"),
    ):
        with pytest.raises(RetrievalError):
            parse_generation_csv(invalid)


def test_real_capture_hash_scope_and_values() -> None:
    data = Path(__file__).resolve().parents[2] / "examples/connectors/data"
    content = (data / "generation_eskom.csv").read_bytes()
    manifest = json.loads((data / "generation_eskom_provenance.json").read_text())
    assert hashlib.sha256(content).hexdigest() == manifest["sha256"]
    frame = parse_generation_csv(content)
    assert len(frame) > 1000
    assert frame.technology.nunique() == 4
    assert frame.loc[frame.technology.eq("solar_pv"), "value"].max() > 1000
