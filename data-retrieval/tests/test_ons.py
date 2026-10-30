"""ONS native/parser contracts; small inline data are synthetic test cases."""

from __future__ import annotations

import hashlib
import io
import json
from datetime import date
from pathlib import Path

import httpx
import pandas as pd
import pytest

from energy_data_retrieval.sources.ons import ONS_HOSTS, ONSClient, parse_generation_csv
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, RetrievalError

HEADER = (
    "din_instante;id_subsistema;nom_usina;id_ons;cod_modalidadeoperacao;nom_tipousina;val_geracao\n"
)
URL = "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/geracao_usina_2_ho/GERACAO_USINA-2_2024_06.parquet"


def native(label: str = "2024-06-01 00:00:00", value: str = "1.5", mode: str = "TIPO I") -> str:
    return HEADER + f"{label};NE;Plant A;A;{mode};Fotovoltaica;{value}\n"


def parquet_bytes(text: str) -> bytes:
    output = io.BytesIO()
    pd.read_csv(io.StringIO(text), sep=";", dtype="string", keep_default_na=False).to_parquet(
        output, index=False
    )
    return output.getvalue()


def catalogue(url: str = URL) -> dict:
    return {
        "success": True,
        "result": {
            "resources": [
                {"name": "Geracao_Usina_2-2024-06", "format": "PARQUET", "url": url},
            ]
        },
    }


def test_mean_power_units_nulls_negatives_and_estimate_exclusion() -> None:
    frame = parse_generation_csv(native(value=""))
    assert pd.isna(frame["value"].iloc[0])
    assert frame["unit"].iloc[0] == "MW" and frame["source_unit"].iloc[0] == "MWmed"
    assert frame["timestamp"].iloc[0] == pd.Timestamp("2024-06-01T03:00Z")
    assert parse_generation_csv(native(value="-2"))["value"].iloc[0] == -2
    assert parse_generation_csv(native(value="0"))["value"].iloc[0] == 0
    for mode in ["TIPO III", "Pequenas Usinas (MMGD)", "Pequenas Usinas (Tipo III)"]:
        excluded = parse_generation_csv(native(mode=mode))
        assert excluded.empty and excluded.attrs["excluded_estimated_rows"] == 1
        included = parse_generation_csv(native(mode=mode), include_estimates=True)
        assert included["quality"].iloc[0] == "estimated_or_forecast"


@pytest.mark.parametrize("label", ["2018-02-17 23:00:00", "2018-11-04 00:00:00"])
def test_historical_dst_folds_and_gaps_fail_without_clock_evidence(label: str) -> None:
    with pytest.raises(RetrievalError, match="timestamp"):
        parse_generation_csv(native(label))
    explicit = parse_generation_csv(native(label), source_timezone="Etc/GMT+3")
    assert len(explicit) == 1


def test_solar_actual_estimate_reference_and_restriction_remain_separate() -> None:
    text = (
        "din_instante;id_subsistema;nom_usina;id_ons;nom_modalidadeoperacao;"
        "val_geracaoverificada;val_geracaoestimada;val_geracaoreferenciafinal;"
        "flg_geracaorestrita;flg_dadoirradianciainvalido\n"
        "2024-06-01 12:30:00;NE;Solar A;A;TIPO II-C;5;8;;1;1\n"
    )
    frame = parse_generation_csv(text, product="solar_curtailment")
    assert frame["value"].iloc[0] == 5 and frame["val_geracaoestimada"].iloc[0] == 8
    assert pd.isna(frame["val_geracaoreferenciafinal"].iloc[0])
    assert frame["flg_dadoirradianciainvalido"].iloc[0] == "1"
    assert frame["aggregation"].iloc[0] == "half_hour_mean"
    assert "curtailment_mwh" not in frame


def test_invalid_schema_numeric_alignment_and_duplicate_conflicts() -> None:
    for text in [
        "oops",
        native(value="inf"),
        native(value="bad"),
        native(mode="FUTURE TYPE"),
        native("2024-06-01 00:15:00"),
    ]:
        with pytest.raises(RetrievalError):
            parse_generation_csv(text)
    repeated = native() + native().splitlines()[1] + "\n"
    assert len(parse_generation_csv(repeated)) == 1
    with pytest.raises(RetrievalError, match="conflicting"):
        parse_generation_csv(native() + native(value="2").splitlines()[1] + "\n")
    with pytest.raises(RetrievalError, match="maximum_rows"):
        parse_generation_csv(repeated, maximum_rows=1)


def test_catalogue_parquet_discovery_and_http_provenance() -> None:
    body = parquet_bytes(native())
    calls: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.host == "dados.ons.org.br":
            assert request.url.params["id"] == "geracao-usina-2"
            return httpx.Response(200, json=catalogue())
        assert str(request.url) == URL
        return httpx.Response(200, content=body)

    with HTTPClient(
        ONS_HOSTS,
        transport=httpx.MockTransport(handle),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        result = ONSClient(http).generation(date(2024, 6, 1), date(2024, 6, 1), plant_ids=["A"])
    assert len(calls) == len(result.requests) == 2 and len(result.frame) == 1
    assert result.requests[1].sha256 == hashlib.sha256(body).hexdigest()
    assert result.frame["value"].iloc[0] == 1.5


@pytest.mark.parametrize(
    "url", ["https://evil.example/file.parquet", URL + "?token=x", URL + "#other"]
)
def test_unapproved_catalogue_resources_never_fetched(url: str) -> None:
    calls: list[str] = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.host)
        return httpx.Response(200, json=catalogue(url))

    with (
        HTTPClient(ONS_HOSTS, transport=httpx.MockTransport(handle)) as http,
        pytest.raises(RetrievalError, match="unapproved"),
    ):
        ONSClient(http).generation(date(2024, 6, 1), date(2024, 6, 1))
    assert calls == ["dados.ons.org.br"]


def test_request_budget_and_parquet_metadata_row_bound() -> None:
    calls: list[str] = []
    body = parquet_bytes(native() + native("2024-06-01 01:00:00").splitlines()[1] + "\n")

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.host)
        return (
            httpx.Response(200, json=catalogue())
            if request.url.host == "dados.ons.org.br"
            else httpx.Response(200, content=body)
        )

    with HTTPClient(
        ONS_HOSTS,
        transport=httpx.MockTransport(handle),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        with pytest.raises(ValueError, match="maximum_requests"):
            ONSClient(http, maximum_requests=1).generation(date(2024, 6, 1), date(2024, 6, 1))
        assert not calls
        with pytest.raises(RetrievalError, match="before decompression"):
            ONSClient(http, maximum_rows=1).generation(date(2024, 6, 1), date(2024, 6, 1))


def test_multiple_exports_aggregate_estimate_exclusion_metadata() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.host == "dados.ons.org.br":
            root = catalogue()
            root["result"]["resources"].append(
                {
                    "name": "Geracao_Usina_2-2024-07",
                    "format": "PARQUET",
                    "url": URL.replace("2024_06", "2024_07"),
                }
            )
            return httpx.Response(200, json=root)
        july = "2024_07" in request.url.path
        month = "07" if july else "06"
        text = native(f"2024-{month}-01 00:00:00")
        for hour in range(2 if july else 1):
            estimate = native(f"2024-{month}-01 {hour:02}:00:00", mode="TIPO III")
            text += estimate.splitlines()[1] + "\n"
        return httpx.Response(200, content=parquet_bytes(text))

    with HTTPClient(
        ONS_HOSTS,
        transport=httpx.MockTransport(handle),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        result = ONSClient(http).generation(date(2024, 6, 1), date(2024, 7, 1))
    assert len(result.frame) == 2 and len(result.requests) == 3
    assert result.frame.attrs["excluded_estimated_rows"] == 3


def test_actual_gallery_captures_and_flags() -> None:
    data = Path(__file__).resolve().parents[2] / "examples/connectors/data"
    for name, product, expected in [
        ("generation_ons", "generation", 336),
        ("generation_ons_solar", "solar_curtailment", 672),
    ]:
        manifest = json.loads((data / f"{name}_provenance.json").read_text())
        raw = (data / manifest["fixture"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == manifest["fixture_sha256"]
        frame = parse_generation_csv(raw.decode(), product=product)
        assert len(frame) == expected and frame["unit_id"].nunique() == 2
        assert frame["quality"].eq("verified").all()
        if product == "solar_curtailment":
            assert frame["val_geracaoreferenciafinal"].isna().any()
            assert frame["flg_geracaorestrita"].eq("1").any()
