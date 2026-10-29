"""AEMET API fixtures retain native periods, codes, provenance and secret isolation."""

from __future__ import annotations

import copy
import json
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import cast

import httpx
import pandas as pd
import pytest

from energy_data_retrieval.sources.aemet import (
    AEMET_HOSTS,
    STATIONS_ENDPOINT,
    AEMETClient,
    daily_chunks,
    normalize_daily,
    normalize_recent,
    normalize_stations,
    save_dataset,
)
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, JSONValue, RetrievalError

STATION = "C447A"
KEY = "synthetic-test-key-with-no-access"
DATA_URL = "https://opendata.aemet.es/opendata/sh/fixture-data"
META_URL = "https://opendata.aemet.es/opendata/sh/fixture-metadata"
START = date(2026, 1, 1)
END = date(2026, 1, 4)


def metadata() -> dict[str, JSONValue]:
    units = {
        "tmed": "°C",
        "tmin": "°C",
        "tmax": "°C",
        "prec": "mm (Ip = inferior a 0,1 mm) (Acum = Precipitación acumulada)",
        "velmedia": "m/s",
        "racha": "m/s",
        "sol": "horas",
        "presMax": "hPa",
        "presMin": "hPa",
        "ta": "°C",
        "tpr": "°C",
        "tamax": "°C",
        "tamin": "°C",
        "vv": "m/s",
        "vmax": "m/s",
        "pres": "hPa",
        "pres_nmar": "hPa",
        "hr": "%",
    }
    fields = [{"id": key, "descripcion": key, "unidad": unit} for key, unit in units.items()]
    fields.extend(
        [
            {"id": "fint", "descripcion": "Fecha hora final del período de observación (hora UTC)"},
            {"id": "latitud", "descripcion": "Latitud en grados, minutos y segundos"},
            {"id": "longitud", "descripcion": "Longitud en grados, minutos y segundos"},
        ]
    )
    return cast(
        dict[str, JSONValue],
        {
            "campos": fields,
            "copyright": "Synthetic fixture, following AEMET native field metadata",
            "notaLegal": "https://www.aemet.es/es/nota_legal",
            "formato": "application/json",
        },
    )


def station_rows() -> list[JSONValue]:
    return [
        {
            "indicativo": STATION,
            "nombre": "Estación sintética",
            "provincia": "STA. CRUZ DE TENERIFE",
            "latitud": "282900N",
            "longitud": "161800W",
            "altitud": "632",
            "indsinop": "60020",
        },
        {
            "indicativo": "B893",
            "nombre": "Another synthetic station",
            "latitud": "400000N",
            "longitud": "0030000E",
            "altitud": "10",
        },
    ]


def daily_rows() -> list[JSONValue]:
    return [
        {
            "indicativo": STATION,
            "fecha": f"2026-01-{number:02d}",
            "tmed": "-1,2",
            "tmin": "-3,0",
            "tmax": "1,5",
            "prec": precipitation,
            "velmedia": "0,0",
            "racha": "5,4",
            "sol": "4,3",
            "presMax": "1005,5",
            "horatmin": "07:00",
            "quality": {"synthetic": "retain this code"},
        }
        for number, precipitation in enumerate(["Ip", "0,0", "Acum", None], start=1)
    ]


def recent_rows() -> list[JSONValue]:
    return [
        {
            "idema": STATION,
            "fint": "2026-01-01T01:10:00",
            "ta": -0.5,
            "vv": 3.5,
            "vmax": 7.0,
            "pres": 1000.5,
            "prec": 0,
            "hr": 70.0,
            "qc": "fixture-flag",
        },
        {"idema": STATION, "fint": "2026-01-01T02:00:00", "ta": 0, "prec": None},
    ]


def fixture_http(
    payload: JSONValue,
    calls: list[httpx.Request],
    *,
    cache_directory: Path | None = None,
    mutate_envelope: Callable[[dict[str, JSONValue]], None] | None = None,
    source_metadata: dict[str, JSONValue] | None = None,
) -> HTTPClient:
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path.startswith("/opendata/api/"):
            assert request.headers["api_key"] == KEY
            assert "api_key" not in request.url.params
            envelope: dict[str, JSONValue] = {
                "estado": 200,
                "descripcion": "exito",
                "datos": DATA_URL,
                "metadatos": META_URL,
            }
            if mutate_envelope is not None:
                mutate_envelope(envelope)
            return httpx.Response(200, json=envelope)
        assert "api_key" not in request.headers
        assert not request.url.query
        if str(request.url) == DATA_URL:
            return httpx.Response(200, json=payload)
        assert str(request.url) == META_URL
        return httpx.Response(200, json=source_metadata or metadata())

    return HTTPClient(
        AEMET_HOSTS,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(minimum_interval_seconds=0),
        cache_directory=cache_directory,
        sleep=lambda _: None,
    )


def test_station_dms_and_bbox_preserve_catalogue_metadata() -> None:
    result = normalize_stations(station_rows(), metadata(), bbox=(-18, 27, -13, 30))
    assert result["station_id"].tolist() == [STATION]
    assert result.loc[0, "latitude"] == pytest.approx(28 + 29 / 60)
    assert result.loc[0, "longitude"] == pytest.approx(-16.3)
    assert result.loc[0, "elevation_m"] == 632
    assert result.loc[0, "source:nombre"] == "Estación sintética"
    assert result.attrs["source_station_rows"] == 2
    assert not result.attrs["availability_inferred"]


def test_invalid_catalogue_coordinate_is_not_silently_corrected() -> None:
    rows = station_rows()
    assert isinstance(rows[1], dict)
    rows[1]["latitud"] = "995900N"
    result = normalize_stations(rows, metadata())
    invalid = result.loc[result["station_id"].eq("B893")].iloc[0]
    assert not invalid.coordinates_valid
    assert pd.isna(invalid.latitude) and pd.isna(invalid.longitude)
    assert invalid["source:latitud"] == "995900N"


def test_daily_decimal_trace_accumulated_and_native_date_semantics() -> None:
    frame = normalize_daily(daily_rows(), metadata(), STATION, START, END)
    assert frame["date"].tolist() == [f"2026-01-{n:02d}" for n in range(1, 5)]
    assert "timestamp" not in frame
    assert frame["temperature_mean_c"].tolist() == [-1.2] * 4
    assert frame["wind_speed_mean_ms"].eq(0).all()
    assert frame["precipitation_qualifier"].tolist() == ["trace", "", "accumulated", ""]
    assert frame["precipitation_mm"].isna().tolist() == [True, False, True, True]
    assert frame.loc[1, "precipitation_mm"] == 0
    assert frame.loc[0, "source:prec"] == "Ip"
    assert json.loads(str(frame.loc[0, "source_record_json"]))["quality"] == {
        "synthetic": "retain this code"
    }
    assert "00-24" in frame.attrs["time_convention"]
    assert frame.attrs["missing_date_count"] == 0


def test_recent_preserves_reporting_label_variable_intervals_and_raw_types() -> None:
    frame = normalize_recent(recent_rows(), metadata(), STATION)
    assert frame["timestamp"].tolist() == [
        pd.Timestamp("2026-01-01T01:10:00Z"),
        pd.Timestamp("2026-01-01T02:00:00Z"),
    ]
    assert frame.loc[0, "wind_speed_ms"] == 3.5
    assert frame.loc[0, "wind_gust_ms"] == 7
    assert frame.loc[0, "precipitation_mm"] == 0
    assert pd.isna(frame.loc[1, "precipitation_mm"])
    assert frame.loc[0, "source:qc"] == "fixture-flag"
    assert json.loads(str(frame.loc[0, "source_record_json"]))["ta"] == -0.5
    assert not frame.attrs["historical_hourly_query_supported"]
    assert not frame.attrs["quality_filter_applied"]


def test_metadata_must_confirm_utc_before_assigning_recent_timezone() -> None:
    meta = metadata()
    assert isinstance(meta["campos"], list)
    for item in meta["campos"]:
        if isinstance(item, dict) and item["id"] == "fint":
            item["descripcion"] = "Unspecified clock"
    with pytest.raises(RetrievalError, match="UTC"):
        normalize_recent(recent_rows(), meta, STATION)


def test_metadata_prevents_treating_kmh_as_metres_per_second() -> None:
    meta = metadata()
    assert isinstance(meta["campos"], list)
    for item in meta["campos"]:
        if isinstance(item, dict) and item["id"] == "vv":
            item["unidad"] = "km/h"
            item["descripcion"] = "Conflicting old description says m/s"
    with pytest.raises(RetrievalError, match="m/s"):
        normalize_recent(recent_rows(), meta, STATION)


def test_live_daily_pressure_metadata_aliases_preserve_native_names_and_definitions() -> None:
    meta = metadata()
    assert isinstance(meta["campos"], list)
    for item in meta["campos"]:
        if isinstance(item, dict) and item["id"] in {"presMax", "presMin"}:
            item["id"] = str(item["id"]).lower()
    rows = daily_rows()
    assert isinstance(rows[0], dict)
    rows[0]["presMin"] = "995,2"
    frame = normalize_daily(rows, meta, STATION, START, END)
    assert frame.loc[0, "station_pressure_max_hpa"] == 1005.5
    assert frame.loc[0, "station_pressure_min_hpa"] == 995.2
    assert frame.loc[0, "source:presMax"] == "1005,5"
    assert frame.loc[0, "source:presMin"] == "995,2"
    assert "source:presmax" not in frame
    assert frame.attrs["source_metadata"] == meta
    assert json.loads(str(frame.loc[0, "source_record_json"]))["presMax"] == "1005,5"


@pytest.mark.parametrize("conflicting_exact", [False, True])
def test_pressure_metadata_aliases_do_not_hide_wrong_units_or_conflicts(
    conflicting_exact: bool,
) -> None:
    meta = metadata()
    assert isinstance(meta["campos"], list)
    for item in meta["campos"]:
        if isinstance(item, dict) and item["id"] == "presMax":
            alias = dict(item, id="presmax", unidad="kPa")
            if conflicting_exact:
                meta["campos"].append(alias)
            else:
                item.update(alias)
            break
    message = "conflicting case aliases" if conflicting_exact else "hPa"
    with pytest.raises(RetrievalError, match=message):
        normalize_daily(daily_rows(), meta, STATION, START, END)


def test_live_recent_compact_utc_offset_preserves_exact_labels_and_times() -> None:
    rows = recent_rows()
    for row in rows:
        assert isinstance(row, dict)
        row["fint"] = str(row["fint"]) + "+0000"
    frame = normalize_recent(rows, metadata(), STATION)
    assert frame["timestamp"].tolist() == [
        pd.Timestamp("2026-01-01T01:10:00Z"),
        pd.Timestamp("2026-01-01T02:00:00Z"),
    ]
    assert frame.loc[0, "source:fint"] == "2026-01-01T01:10:00+0000"
    assert json.loads(str(frame.loc[0, "source_record_json"]))["fint"].endswith("+0000")


@pytest.mark.parametrize("offset", ["+0100", "+01:00", "-0100"])
def test_recent_non_utc_offsets_are_not_silently_reinterpreted(offset: str) -> None:
    rows = recent_rows()
    assert isinstance(rows[0], dict)
    rows[0]["fint"] = str(rows[0]["fint"]) + offset
    with pytest.raises(RetrievalError, match="UTC observation labels"):
        normalize_recent(rows, metadata(), STATION)


@pytest.mark.parametrize("problem", ["station", "date", "conflict", "nonnumeric", "nonfinite"])
def test_daily_rejects_wrong_identity_dates_conflicts_and_unknown_numeric_codes(
    problem: str,
) -> None:
    rows = daily_rows()
    assert isinstance(rows[0], dict)
    if problem == "station":
        rows[0]["indicativo"] = "B893"
    elif problem == "date":
        rows[0]["fecha"] = "2025-12-31"
    elif problem == "conflict":
        rows.append(dict(rows[0], tmed="88,8"))
    elif problem == "nonnumeric":
        rows[0]["tmed"] = "unknown"
    else:
        rows[0]["tmed"] = "1e999"
    with pytest.raises(RetrievalError):
        normalize_daily(rows, metadata(), STATION, START, END)


def test_exact_duplicates_and_missing_days_are_recorded() -> None:
    rows = daily_rows()[:2]
    rows.append(copy.deepcopy(rows[0]))
    frame = normalize_daily(rows, metadata(), STATION, START, END)
    assert len(frame) == 2
    assert frame.attrs["exact_duplicate_rows_removed"] == 1
    assert frame.attrs["missing_date_count"] == 2


@pytest.mark.parametrize("field", ["indicativo", "fecha"])
def test_null_identity_does_not_become_a_valid_daily_record(field: str) -> None:
    rows = daily_rows()
    assert isinstance(rows[0], dict)
    rows[0][field] = None
    with pytest.raises(RetrievalError):
        normalize_daily(rows, metadata(), STATION, START, END)


def test_daily_chunks_boundaries_and_aggregate_bounds() -> None:
    chunks = list(daily_chunks(date(2024, 2, 28), date(2024, 3, 31)))
    assert chunks == [
        (date(2024, 2, 28), date(2024, 3, 29)),
        (date(2024, 3, 30), date(2024, 3, 31)),
    ]
    with pytest.raises(ValueError, match="maximum_days"):
        list(daily_chunks(START, END, maximum_days=3))
    with pytest.raises(ValueError, match="chunk_days"):
        list(daily_chunks(START, END, chunk_days=32))


def test_two_stage_header_auth_canonical_sidecars_and_restart_without_key(tmp_path: Path) -> None:
    calls: list[httpx.Request] = []
    cache = tmp_path / "cache"
    output = tmp_path / "daily.parquet"
    with fixture_http(daily_rows(), calls, cache_directory=cache) as http:
        client = AEMETClient(http, KEY)
        first = client.retrieve_daily(STATION, START, END, output)
        assert KEY not in repr(client)
        assert len(calls) == 3
        assert "fechaini/2026-01-01T00:00:00UTC" in calls[0].url.path
        assert "fechafin/2026-01-04T23:59:59UTC" in calls[0].url.path
        resumed = AEMETClient(http).retrieve_daily(STATION, START, END, output)
        assert first == resumed and len(calls) == 3
    assert not cache.exists()
    source = output.with_suffix(".parquet.source.json")
    assert json.loads(source.read_bytes()) == daily_rows()
    for path in tmp_path.iterdir():
        if path.suffix == ".json":
            assert KEY not in path.read_text()
    manifest = json.loads(output.with_suffix(".parquet.json").read_text())
    assert len(manifest["provenance"]["source_artifacts"]) == 3
    assert manifest["request"]["product"] == "daily"


def test_station_and_recent_client_requests_use_distinct_products(tmp_path: Path) -> None:
    for product, payload in (("stations", station_rows()), ("recent", recent_rows())):
        calls: list[httpx.Request] = []
        with fixture_http(payload, calls) as http:
            client = AEMETClient(http, KEY)
            if product == "stations":
                artifact = client.retrieve_stations(tmp_path / "stations.parquet")
                assert str(calls[0].url) == STATIONS_ENDPOINT
            else:
                artifact = client.retrieve_recent(STATION, tmp_path / "recent.parquet")
                assert calls[0].url.path.endswith(
                    "/observacion/convencional/datos/estacion/" + STATION
                )
        assert artifact.rows == 2 and len(calls) == 3


@pytest.mark.parametrize("status", [401, 404, 429])
def test_http_200_api_errors_are_not_observation_snapshots(status: int) -> None:
    calls: list[httpx.Request] = []
    with (
        fixture_http(
            daily_rows(), calls, mutate_envelope=lambda value: value.update(estado=status)
        ) as http,
        pytest.raises(RetrievalError, match="estado 200"),
    ):
        AEMETClient(http, KEY).daily(STATION, START, END)
    assert len(calls) == 1


@pytest.mark.parametrize(
    "url",
    [
        "http://opendata.aemet.es/opendata/sh/example",
        "https://elsewhere.example/opendata/sh/example",
        "https://opendata.aemet.es@elsewhere.example/opendata/sh/example",
        "https://opendata.aemet.es/opendata/sh/example?api_key=private",
        "https://opendata.aemet.es/opendata/sh/../api/private",
    ],
)
def test_unapproved_temporary_links_stop_before_followup(url: str) -> None:
    calls: list[httpx.Request] = []
    with (
        fixture_http(
            daily_rows(), calls, mutate_envelope=lambda value: value.update(datos=url)
        ) as http,
        pytest.raises(RetrievalError, match="document link"),
    ):
        AEMETClient(http, KEY).daily(STATION, START, END)
    assert len(calls) == 1


def test_expired_temporary_response_and_credential_echo_are_rejected(tmp_path: Path) -> None:
    for payload in ({"estado": 404, "descripcion": "datos expirados"}, [{"secret": KEY}]):
        calls: list[httpx.Request] = []
        with (
            fixture_http(cast(JSONValue, payload), calls) as http,
            pytest.raises(RetrievalError),
        ):
            AEMETClient(http, KEY).retrieve_recent(STATION, tmp_path / "unsaved.parquet")
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("suffix", [".source.json", ".metadata.json", ".envelope.json"])
def test_changed_source_sidecars_prevent_restart_without_network(
    tmp_path: Path, suffix: str
) -> None:
    calls: list[httpx.Request] = []
    output = tmp_path / "daily.parquet"
    with fixture_http(daily_rows(), calls) as http:
        client = AEMETClient(http, KEY)
        client.retrieve_daily(STATION, START, END, output)
        output.with_suffix(".parquet" + suffix).write_text("[]")
        with pytest.raises(ValueError, match="checksum"):
            AEMETClient(http).retrieve_daily(STATION, START, END, output)
    assert len(calls) == 3


def test_modified_normalization_or_native_source_cannot_claim_original_provenance(
    tmp_path: Path,
) -> None:
    calls: list[httpx.Request] = []
    with fixture_http(daily_rows(), calls) as http:
        result = AEMETClient(http, KEY).daily(STATION, START, END)
    result.frame.loc[0, "temperature_mean_c"] = 99
    with pytest.raises(ValueError, match="normalized frame"):
        save_dataset(result, tmp_path / "modified.parquet")
    assert not list(tmp_path.iterdir())
    assert isinstance(result.payload, list) and isinstance(result.payload[0], dict)
    result.payload[0]["tmed"] = "99"
    with pytest.raises(ValueError, match="acquisition hash"):
        save_dataset(result, tmp_path / "modified.parquet")


def test_missing_key_invalid_selection_and_row_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("AEMET_API_KEY", raising=False)
    calls: list[httpx.Request] = []
    with fixture_http(daily_rows(), calls) as http:
        client = AEMETClient.from_environment(http)
        with pytest.raises(ValueError, match="AEMET_API_KEY"):
            client.retrieve_stations(tmp_path / "stations.parquet")
        with pytest.raises(ValueError, match="identifier"):
            client.recent("../private")
        with pytest.raises(ValueError, match="maximum_days"):
            client.daily(STATION, START, date(2026, 2, 3))
        assert not calls
        with pytest.raises(RetrievalError, match="maximum_rows"):
            AEMETClient(http, KEY, maximum_rows=2).daily(STATION, START, END)


def test_incomplete_checkpoint_and_changed_request_are_not_overwritten(tmp_path: Path) -> None:
    calls: list[httpx.Request] = []
    output = tmp_path / "daily.parquet"
    output.with_suffix(".parquet.source.json").write_text("[]")
    with (
        fixture_http(daily_rows(), calls) as http,
        pytest.raises(ValueError, match="Incomplete"),
    ):
        AEMETClient(http, KEY).retrieve_daily(STATION, START, END, output)
    assert not calls


def test_cli_daily_partitions_preserve_canonical_sources_and_resume_without_credentials(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from energy_data_retrieval import cli, station_cli

    calls: list[httpx.Request] = []
    payload: list[JSONValue] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal payload
        calls.append(request)
        if request.url.path.startswith("/opendata/api/"):
            assert request.headers["api_key"] == KEY
            assert not request.url.query
            pieces = request.url.path.split("/")
            start = pieces[pieces.index("fechaini") + 1][:10]
            end = pieces[pieces.index("fechafin") + 1][:10]
            payload = daily_rows()[:2]
            assert isinstance(payload[0], dict) and isinstance(payload[1], dict)
            payload[0]["fecha"] = start
            payload[1]["fecha"] = end
            return httpx.Response(
                200,
                json={"estado": 200, "datos": DATA_URL, "metadatos": META_URL},
            )
        assert "api_key" not in request.headers
        if str(request.url) == DATA_URL:
            return httpx.Response(200, json=payload)
        assert str(request.url) == META_URL
        return httpx.Response(200, json=metadata())

    def factory(allowed_hosts: frozenset[str], *, config: HTTPConfig | None = None) -> HTTPClient:
        return HTTPClient(
            allowed_hosts,
            config=config,
            transport=httpx.MockTransport(handler),
            sleep=lambda _: None,
        )

    monkeypatch.setattr(station_cli, "HTTPClient", factory)
    monkeypatch.setenv("AEMET_API_KEY", KEY)
    arguments = [
        "aemet-daily",
        "--station",
        STATION,
        "--start",
        "2026-01-01",
        "--end",
        "2026-02-03",
        "--output",
        str(tmp_path / "aemet"),
    ]
    assert cli.main(arguments) == 0
    assert len(calls) == 6
    outputs = sorted((tmp_path / "aemet").glob("*/*.parquet"))
    assert [path.name for path in outputs] == [
        "daily_2026-01-01_2026-01-31.parquet",
        "daily_2026-02-01_2026-02-03.parquet",
    ]
    for path in outputs:
        assert path.parent.name == path.parent.name.lower()
        assert len(pd.read_parquet(path)) == 2
        source = path.with_suffix(".parquet.source.json")
        source_rows = json.loads(source.read_bytes())
        assert source_rows[0]["indicativo"] == STATION
        assert source_rows[0]["prec"] == "Ip"
    for path in (tmp_path / "aemet").rglob("*.json"):
        assert KEY not in path.read_text()
    monkeypatch.delenv("AEMET_API_KEY")
    assert cli.main(arguments) == 0
    assert len(calls) == 6
    assert KEY not in capsys.readouterr().out


@pytest.mark.parametrize("encoding", ["iso-8859-15", "utf-8"])
def test_declared_latin15_json_and_mislabeled_utf8_retain_native_unicode(
    tmp_path: Path, encoding: str
) -> None:
    rows = station_rows()
    assert isinstance(rows[0], dict)
    rows[0]["nombre"] = "Estación española €"

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.startswith("/opendata/api/"):
            assert request.headers["api_key"] == KEY
            value: JSONValue = {
                "estado": 200,
                "descripcion": "Éxito",
                "datos": DATA_URL,
                "metadatos": META_URL,
            }
        elif str(request.url) == DATA_URL:
            value = rows
        else:
            assert str(request.url) == META_URL
            value = metadata()
        return httpx.Response(
            200,
            content=json.dumps(value, ensure_ascii=False).encode(encoding),
            headers={"Content-Type": "application/json;charset=ISO-8859-15"},
        )

    output = tmp_path / "stations.parquet"
    with HTTPClient(
        AEMET_HOSTS,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        AEMETClient(http, KEY).retrieve_stations(output)
    frame = pd.read_parquet(output)
    assert (
        frame.loc[frame["station_id"].eq(STATION), "station_name"].iloc[0] == "Estación española €"
    )
    assert json.loads(output.with_suffix(".parquet.source.json").read_bytes()) == rows
    assert json.loads(output.with_suffix(".parquet.metadata.json").read_bytes()) == metadata()
