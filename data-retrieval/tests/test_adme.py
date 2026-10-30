"""ADME SAS contracts; inline cases are synthetic, the gallery file is genuine."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta
from pathlib import Path

import httpx
import pandas as pd
import pytest

from energy_data_retrieval.sources.adme import ADME_HOSTS, ADMEClient, parse_scada_sas
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, RetrievalError

DATA = Path(__file__).resolve().parents[2] / "examples/connectors/data"
FILENAME = "scada_central_7_2026102121.sas"


def native(first: datetime = datetime(2024, 6, 1), values: list[float] | None = None) -> str:
    values = values if values is not None else [0, -111111, -2]
    header = (
        f"3\tNSeries\n{first.year}\t{first.month}\t{first.day}\t"
        f"{first.hour}\t{first.minute}\t{first.second}\t// first\n"
        f"1.0000000298023224\t// hours\n{len(values)}\tNPuntos\n1\tCycle\n"
        "\tPLANT.030GETOTMEDP.AV\tPLANT.000CONSIGNAP.AV\t\n"
    )
    rows = []
    for index, value in enumerate(values):
        serial = (first + timedelta(hours=index) - datetime(1899, 12, 30)).total_seconds() / 86400
        rows.append(f"{serial:.8f}\t{value}\t50\t-121111\n")
    return header + "".join(rows)


def test_actual_channel_dispatch_limit_missing_sentinels_and_native_clock() -> None:
    frame = parse_scada_sas(native(), central_id=7)
    assert frame["timestamp"].iloc[0] == pd.Timestamp("2024-06-01T03:00Z")
    assert frame["value"].iloc[0] == 0 and pd.isna(frame["value"].iloc[1])
    assert frame["value"].iloc[2] == -2
    assert frame["dispatch_limit_mw"].eq(50).all()
    assert frame["unnamed_series_3"].isna().all()
    assert frame["sampling_seconds"].eq(3600).all() and frame["unit"].eq("MW").all()
    assert "interval_end" not in frame and "curtailment_mwh" not in frame
    boundary = parse_scada_sas(native(values=[-10000, -10000.01]), central_id=7)
    assert boundary["value"].iloc[0] == -10000 and pd.isna(boundary["value"].iloc[1])


def test_ambiguous_dst_clock_rejected_and_explicit_fixed_clock_supported() -> None:
    text = native(datetime(2024, 11, 3, 1), [1, 2])
    with pytest.raises(RetrievalError, match="clock labels"):
        parse_scada_sas(text, central_id=7, source_timezone="America/New_York")
    assert len(parse_scada_sas(text, central_id=7, source_timezone="Etc/GMT+5")) == 2


def test_limits_forecasts_and_unidentified_power_are_not_actual_generation() -> None:
    with pytest.raises(RetrievalError, match="not a limit"):
        parse_scada_sas(native(), central_id=7, power_series="PLANT.000CONSIGNAP.AV")
    altered = native().replace("PLANT.030GETOTMEDP.AV", "OTHER.POWER")
    with pytest.raises(RetrievalError, match="ambiguous"):
        parse_scada_sas(altered, central_id=7)
    with pytest.raises(RetrievalError, match="GETOTMEDP"):
        parse_scada_sas(altered, central_id=7, power_series="OTHER.POWER")
    with pytest.raises(RetrievalError):
        parse_scada_sas(
            altered.replace("OTHER.POWER", "PRONOSTICO.POWER"),
            central_id=7,
            power_series="PRONOSTICO.POWER",
        )
    actual = (DATA / "generation_adme.sas").read_text()
    for channel in ["PCGRANDE.000CANTMOLINOSDISP.AV", "PCGRANDE.000VELVIENTO.AV"]:
        with pytest.raises(RetrievalError, match="GETOTMEDP"):
            parse_scada_sas(actual, central_id=7, power_series=channel)


@pytest.mark.parametrize(
    "transform",
    [
        lambda text: text.replace("3\tNSeries", "4\tNSeries"),
        lambda text: text.replace("3\tNPuntos", "4\tNPuntos"),
        lambda text: text.replace("\t0\t50\t", "\tbad\t50\t"),
        lambda text: text.replace("\t0\t50\t", "\tinf\t50\t"),
        lambda text: "<html>Warning: failed export</html>",
    ],
)
def test_rejects_malformed_header_values_and_php_error_documents(transform) -> None:
    with pytest.raises(RetrievalError):
        parse_scada_sas(transform(native()), central_id=7)


def test_irregular_labels_duplicate_samples_and_row_limits() -> None:
    text = native()
    lines = text.splitlines()
    lines[7] = lines[6]
    with pytest.raises(RetrievalError, match="clock labels"):
        parse_scada_sas("\n".join(lines), central_id=7)
    with pytest.raises(RetrievalError, match="maximum_rows"):
        parse_scada_sas(text, central_id=7, maximum_rows=2)


def test_discovered_native_file_date_selection_and_provenance() -> None:
    raw = (DATA / "generation_adme.sas").read_bytes()
    calls: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path.endswith("/"):
            return httpx.Response(
                200,
                text=(
                    f'<a href="{FILENAME}">SCADA</a>'
                    '<a href="https://evil.example/scada_central_7_2026102221.sas">skip</a>'
                    '<a href="prono_central_7_2026102121.sas">forecast</a>'
                ),
            )
        assert request.url.path.endswith(FILENAME)
        return httpx.Response(200, content=raw)

    with HTTPClient(
        ADME_HOSTS,
        transport=httpx.MockTransport(handle),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        result = ADMEClient(http).generation(date(2026, 10, 22), date(2026, 10, 27), central_id=7)
        assert len(result.frame) == 144 and len(result.requests) == len(calls) == 2
        assert result.requests[1].sha256 == hashlib.sha256(raw).hexdigest()
        assert result.frame["source_datetime"].dt.date.min() == date(2026, 10, 22)
        with pytest.raises(ValueError, match="maximum_requests"):
            ADMEClient(http, maximum_requests=1).generation(
                date(2026, 10, 22), date(2026, 10, 22), central_id=7
            )
        assert len(calls) == 2
        with pytest.raises(RetrievalError, match="no SCADA archive"):
            ADMEClient(http).generation(date(2026, 10, 22), date(2026, 10, 22), central_id=999)


def test_discovered_file_must_match_filename_and_cover_whole_dates() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/"):
            return httpx.Response(200, text=f'<a href="{FILENAME}">SCADA</a>')
        return httpx.Response(200, text=native(datetime(2026, 10, 21, 21)))

    with (
        HTTPClient(
            ADME_HOSTS,
            transport=httpx.MockTransport(handle),
            config=HTTPConfig(minimum_interval_seconds=0),
        ) as http,
        pytest.raises(RetrievalError, match="does not cover"),
    ):
        ADMEClient(http).generation(date(2026, 10, 22), date(2026, 10, 22), central_id=7)


def test_real_complete_capture_hash_and_missing_observations() -> None:
    manifest = json.loads((DATA / "generation_adme_provenance.json").read_text())
    raw = (DATA / manifest["fixture"]).read_bytes()
    assert (
        hashlib.sha256(raw).hexdigest() == manifest["fixture_sha256"] == manifest["source_sha256"]
    )
    frame = parse_scada_sas(raw.decode(), central_id=7)
    assert len(frame) == 169 and frame["value"].isna().sum() == 8
    assert frame["power_series"].iloc[0] == "PCGRANDE.030GETOTMEDP.AV"
    assert frame["dispatch_limit_mw"].nunique() > 1
