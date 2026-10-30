"""IESO contract tests; inline reports are synthetic, gallery capture is real."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

import httpx
import pandas as pd
import pytest

from energy_data_retrieval.sources.ieso import IESO_HOSTS, IESOClient, parse_generation_xml
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, RetrievalError


def report(day: str = "2024-07-01", entries: list[tuple[int, str | None]] | None = None) -> str:
    outputs = "".join(
        f"<Output><Hour>{hour}</Hour>"
        + ("" if value is None else f"<EnergyMW>{value}</EnergyMW>")
        + "</Output>"
        for hour, value in (entries if entries is not None else [(1, "0"), (24, "N/A")])
    )
    return (
        '<IMODocument docID="GenOutputCapability" xmlns="http://www.theIMO.com/schema">'
        "<IMODocHeader><CreatedAt>2024-07-02T01:00:00</CreatedAt></IMODocHeader>"
        f"<IMODocBody><Date>{day}</Date><Generators><Generator>"
        "<GeneratorName>SOLAR-A</GeneratorName><FuelType>SOLAR</FuelType>"
        f"<Outputs>{outputs}</Outputs>"
        "<Capabilities><Capability><Hour>1</Hour><EnergyMW>900</EnergyMW></Capability></Capabilities>"
        "<Forecasts><Forecast><Hour>1</Hour><EnergyMW>800</EnergyMW></Forecast></Forecasts>"
        "</Generator></Generators></IMODocBody></IMODocument>"
    )


def test_actual_only_fixed_est_even_in_summer_and_hour_24() -> None:
    frame = parse_generation_xml(report())
    assert frame["timestamp"].tolist() == [
        pd.Timestamp("2024-07-01T05:00Z"),
        pd.Timestamp("2024-07-02T04:00Z"),
    ]
    assert frame["interval_end"].iloc[-1] == pd.Timestamp("2024-07-02T05:00Z")
    assert len(frame) == 2 and frame["value"].iloc[0] == 0
    assert pd.isna(frame["value"].iloc[1])
    assert frame["unit"].unique().tolist() == ["MW"]
    assert parse_generation_xml(report("2024-12-01"))["timestamp"].iloc[0].hour == 5


def test_native_omitted_energy_empty_and_na_remain_missing() -> None:
    frame = parse_generation_xml(report(entries=[(1, None), (2, ""), (3, "N/A"), (4, "-2.5")]))
    assert frame["value"].isna().tolist() == [True, True, True, False]
    assert frame["quality"].tolist() == ["missing"] * 3 + ["operational_telemetry"]
    assert frame["value"].iloc[-1] == -2.5


@pytest.mark.parametrize("raw", ["nan", "inf", "-inf", "broken"])
def test_rejects_invalid_numeric_output(raw: str) -> None:
    with pytest.raises(RetrievalError):
        parse_generation_xml(report(entries=[(1, raw)]))


@pytest.mark.parametrize("hour", [0, 25])
def test_rejects_invalid_hour(hour: int) -> None:
    with pytest.raises(RetrievalError, match="hour"):
        parse_generation_xml(report(entries=[(hour, "1")]))


def test_xml_validation_and_duplicate_conflicts() -> None:
    for raw in [
        "<broken",
        report().replace("GenOutputCapability", "Forecast"),
        "<!DOCTYPE x>" + report(),
    ]:
        with pytest.raises(RetrievalError):
            parse_generation_xml(raw)
    assert len(parse_generation_xml(report(entries=[(1, "1"), (1, "1")]))) == 1
    with pytest.raises(RetrievalError, match="conflicting"):
        parse_generation_xml(report(entries=[(1, "1"), (1, "2")]))
    with pytest.raises(RetrievalError, match="maximum_rows"):
        parse_generation_xml(report(), maximum_rows=1)
    with pytest.raises(RetrievalError, match="actual Outputs"):
        parse_generation_xml(
            report().replace("<Outputs>", "<Other>").replace("</Outputs>", "</Other>")
        )


def test_http_daily_bounds_report_dates_and_provenance() -> None:
    calls: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        day = "2024-07-01" if "20240701" in request.url.path else "2024-07-02"
        return httpx.Response(200, text=report(day))

    with HTTPClient(
        IESO_HOSTS,
        transport=httpx.MockTransport(handle),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        result = IESOClient(http).generation(
            date(2024, 7, 1), date(2024, 7, 2), unit_ids=["SOLAR-A"]
        )
        assert len(result.frame) == 4 and len(result.requests) == len(calls) == 2
        assert result.requests[0].sha256 == hashlib.sha256(report().encode()).hexdigest()
        with pytest.raises(ValueError, match="maximum_requests"):
            IESOClient(http, maximum_requests=1).generation(date(2024, 7, 1), date(2024, 7, 2))
        assert len(calls) == 2
        with pytest.raises(RetrievalError, match="maximum_rows"):
            IESOClient(http, maximum_rows=3).generation(date(2024, 7, 1), date(2024, 7, 2))
        with pytest.raises(RetrievalError, match="absent"):
            IESOClient(http).generation(date(2024, 7, 1), date(2024, 7, 1), unit_ids=["UNKNOWN"])
    with (
        HTTPClient(
            IESO_HOSTS, transport=httpx.MockTransport(lambda _: httpx.Response(200, text=report()))
        ) as http,
        pytest.raises(RetrievalError, match="outside"),
    ):
        IESOClient(http).generation(date(2024, 7, 2), date(2024, 7, 2))


def test_real_capture_hash_and_complete_three_solar_profiles() -> None:
    data = Path(__file__).resolve().parents[2] / "examples/connectors/data"
    manifest = json.loads((data / "generation_ieso_provenance.json").read_text())
    raw = (data / manifest["fixture"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == manifest["fixture_sha256"]
    frame = parse_generation_xml(raw.decode())
    assert len(frame) == 72 and frame["unit_id"].nunique() == 3
    assert frame.groupby("unit_id")["hour_ending"].nunique().eq(24).all()
    assert frame["technology"].eq("SOLAR").all()
