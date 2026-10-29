"""DWD native timing, energy units, archive integrity and bounded acquisition."""

from __future__ import annotations

import io
import json
import zipfile
from datetime import date
from pathlib import Path

import httpx
import pandas as pd
import pytest

from energy_data_retrieval.sources.dwd import (
    DWD_HOSTS,
    STATIONS_ENDPOINT,
    DWDClient,
    normalize_solar,
    normalize_stations,
    save_solar,
    save_stations,
)
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, RetrievalError

STATION = "01048"
DAY = date(2024, 1, 1)
TABLE = (
    "STATIONS_ID;MESS_DATUM;QN_592;ATMO_LBERG;FD_LBERG;FG_LBERG;SD_LBERG;ZENIT;MESS_DATUM_WOZ;eor\r\n"
    "       1048;2024010100:05;10;100;0;0;0;120.25;2024010101:00;eor\r\n"
    "       1048;2024010101:05;1;-999;-999.0;-1;0;117.52;2024010102:00;eor\r\n"
    "       1048;2024010200:05;-999;110;2;3;5;80.01;2024010201:00;eor\r\n"
)


def parameters(*, unit: str = "J/cm²", timezone: str = "in UTC und WOZ") -> str:
    header = (
        "Stations_ID;Von_Datum;Bis_Datum;Stationsname;Parameter;Parameterbeschreibung;"
        "Einheit;Datenquelle (Strukturversion=SV);Zusatz-Info;"
        "Besonderheiten;Literaturhinweis;eor;\r\n"
    )
    rows = ""
    for parameter in ("ATMO_LBERG", "FD_LBERG", "FG_LBERG", "SD_LBERG"):
        units = "Minute" if parameter == "SD_LBERG" else unit
        rows += (
            f"1048;20240101;20240102;Synthetic station;{parameter};Synthetic hourly total;"
            f"{units};Synthetic fixture;{timezone};;;eor;\r\n"
        )
    return header + rows + "Legende: synthetic fixture\r\n"


def archive_bytes(
    table: str = TABLE,
    metadata: str | None = None,
    *,
    extras: dict[str, bytes] | None = None,
    omit_metadata: bool = False,
) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("produkt_st_stunde_20240101_20240102_01048.txt", table)
        if not omit_metadata:
            archive.writestr(
                "Metadaten_Parameter_st_stunde_01048.txt",
                (parameters() if metadata is None else metadata).encode("iso-8859-1"),
            )
        for name, value in (extras or {}).items():
            archive.writestr(name, value)
    return out.getvalue()


def catalogue_bytes() -> bytes:
    header = (
        "Stations_id von_datum bis_datum Stationshoehe geoBreite geoLaenge "
        "Stationsname Bundesland\r\n"
        "----------- --------- --------- ------------- --------- --------- "
        "----------------------------------------- ----------\r\n"
    )
    return (
        header
        + "01048 19960901 20260930 227 51.1278 13.7543 "
        + f"{'Dresden-Klotzsche':41}Sachsen\r\n"
        + "02932 19900101 20260930 447 48.2433 12.2450 "
        + f"{'München Flughafen':41}Bayern\r\n"
    ).encode("iso-8859-1")


def test_native_energy_utc_minute_offsets_and_woz_are_preserved() -> None:
    frame = normalize_solar(archive_bytes(), STATION, DAY, DAY)
    assert len(frame) == 2 and frame.attrs["source_rows"] == 3
    assert frame.timestamp.tolist() == [
        pd.Timestamp("2024-01-01T00:05Z"),
        pd.Timestamp("2024-01-01T01:05Z"),
    ]
    assert frame.timestamp_woz.dt.tz is None
    assert frame.timestamp_woz.iloc[0] == pd.Timestamp("2024-01-01T01:00")
    assert frame.global_radiation_jcm2.tolist() == [0.0, -1.0]
    assert frame.longwave_down_jcm2.iloc[0] == 100.0
    assert pd.isna(frame.longwave_down_jcm2.iloc[1])
    assert pd.isna(frame.diffuse_radiation_jcm2.iloc[1])
    assert frame.quality_level.tolist() == [10, 1]
    assert frame.STATIONS_ID.iloc[0] == "       1048"
    assert frame.FD_LBERG.iloc[1] == "-999.0"
    assert "ghi_wm2" not in frame and "interval_start" not in frame
    assert frame.attrs["units"]["global_radiation_jcm2"] == "J/cm²"


def test_catalogue_decodes_original_names_and_filters() -> None:
    frame = normalize_stations(catalogue_bytes())
    assert frame.station_id.tolist() == ["01048", "02932"]
    assert frame.station_name.tolist() == ["Dresden-Klotzsche", "München Flughafen"]
    assert frame.country_code.tolist() == ["DE", "DE"]
    assert "München" in frame.source_line.iloc[1]
    filtered = normalize_stations(catalogue_bytes(), bbox=(13, 50, 14, 52))
    assert filtered.station_id.tolist() == ["01048"]
    assert filtered.attrs["source_rows"] == 2


@pytest.mark.parametrize(
    ("original", "replacement", "message"),
    [
        ("       1048", "       9999", "different station"),
        ("2024010100:05", "2024023000:05", "invalid timestamp"),
        ("2024010100:05", "202401010005", "minute-resolution"),
        ("2024010101:05", "2024010100:05", "unique and ordered"),
        (";100;0;0;", ";NaN;0;0;", "numeric value"),
        (";10;100;", ";10.5;100;", "integer quality"),
        (";ZENIT;", ";UNKNOWN;", "unsupported columns"),
        (";2024010101:00;eor", ";2024010101:00;", "incomplete record"),
    ],
)
def test_invalid_solar_source_fails(original: str, replacement: str, message: str) -> None:
    with pytest.raises(RetrievalError, match=message):
        normalize_solar(archive_bytes(TABLE.replace(original, replacement)), STATION, DAY, DAY)


@pytest.mark.parametrize("metadata", [parameters(unit="W/m²"), parameters(timezone="in MEZ")])
def test_parameter_metadata_must_confirm_units_and_time_basis(metadata: str) -> None:
    with pytest.raises(RetrievalError, match="confirm native units"):
        normalize_solar(archive_bytes(metadata=metadata), STATION, DAY, DAY)


@pytest.mark.parametrize(
    "name", ["../escape.txt", "/escape.txt", "folder/file.txt", "unexpected.txt"]
)
def test_unexpected_or_unsafe_archive_members_fail(name: str) -> None:
    with pytest.raises(RetrievalError, match="member"):
        normalize_solar(archive_bytes(extras={name: b"x"}), STATION, DAY, DAY)


@pytest.mark.parametrize(
    ("limits", "message"),
    [
        ({"maximum_rows": 2}, "maximum_rows"),
        ({"maximum_archive_members": 1}, "member-count"),
        ({"maximum_uncompressed_bytes": 100}, "uncompressed byte"),
    ],
)
def test_archive_resource_limits_apply_before_date_selection(
    limits: dict[str, int], message: str
) -> None:
    with pytest.raises(RetrievalError, match=message):
        normalize_solar(archive_bytes(), STATION, DAY, DAY, **limits)


def test_missing_metadata_truncated_table_and_empty_date_selection_fail() -> None:
    with pytest.raises(RetrievalError, match="parameter metadata"):
        normalize_solar(archive_bytes(omit_metadata=True), STATION, DAY, DAY)
    with pytest.raises(RetrievalError, match="final record"):
        normalize_solar(archive_bytes(TABLE.rstrip()), STATION, DAY, DAY)
    with pytest.raises(RetrievalError, match="no observations"):
        normalize_solar(archive_bytes(), STATION, date(2025, 1, 1), date(2025, 1, 2))


def test_catalogue_rejects_invalid_records_and_bounds() -> None:
    with pytest.raises(RetrievalError, match="maximum_stations"):
        normalize_stations(catalogue_bytes(), maximum_stations=1)
    with pytest.raises(RetrievalError, match="invalid station metadata"):
        normalize_stations(catalogue_bytes().replace(b"51.1278", b"151.1278"))
    with pytest.raises(ValueError, match="bbox"):
        normalize_stations(catalogue_bytes(), bbox=(14, 50, 13, 52))


def test_native_artifacts_and_restart_verify_every_source_before_network(tmp_path: Path) -> None:
    archive = archive_bytes()
    catalogue = catalogue_bytes()
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if str(request.url) == STATIONS_ENDPOINT:
            return httpx.Response(200, content=catalogue)
        assert request.url.path.endswith("stundenwerte_ST_01048_row.zip")
        return httpx.Response(200, content=archive)

    with HTTPClient(
        DWD_HOSTS,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        client = DWDClient(http)
        solar_path = tmp_path / "solar.parquet"
        station_path = tmp_path / "stations.parquet"
        solar = client.retrieve(STATION, DAY, DAY, solar_path)
        stations = client.retrieve_stations(station_path)
        assert solar.rows == stations.rows == 2
        assert solar == client.retrieve(STATION, DAY, DAY, solar_path)
        assert stations == client.retrieve_stations(station_path)
        assert len(requests) == 2
        assert solar_path.with_suffix(".parquet.source.zip").read_bytes() == archive
        assert station_path.with_suffix(".parquet.source.txt").read_bytes() == catalogue
        manifest = json.loads(solar_path.with_suffix(".parquet.json").read_text())
        assert manifest["provenance"]["metadata"]["source_rows"] == 3
        solar_path.with_suffix(".parquet.source.zip").write_bytes(b"tampered")
        with pytest.raises(ValueError, match="source sidecar"):
            client.retrieve(STATION, DAY, DAY, solar_path)
        assert len(requests) == 2


def test_mutated_normalized_values_cannot_claim_original_provenance(tmp_path: Path) -> None:
    with HTTPClient(
        DWD_HOSTS,
        transport=httpx.MockTransport(
            lambda r: httpx.Response(
                200,
                content=catalogue_bytes() if str(r.url) == STATIONS_ENDPOINT else archive_bytes(),
            )
        ),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        client = DWDClient(http)
        solar = client.solar(STATION, DAY, DAY)
        solar.frame.loc[0, "global_radiation_jcm2"] = 9999.0
        with pytest.raises(ValueError, match="differs from its native"):
            save_solar(solar, tmp_path / "solar.parquet")
        stations = client.stations()
        stations.frame.loc[0, "latitude"] = 1.0
        with pytest.raises(ValueError, match="differs from its source"):
            save_stations(stations, tmp_path / "stations.parquet")
    assert not list(tmp_path.iterdir())


def test_invalid_identifiers_and_incomplete_snapshots_fail_before_network(tmp_path: Path) -> None:
    def forbidden(_: httpx.Request) -> httpx.Response:
        pytest.fail("Invalid requests and incomplete snapshots must fail before networking")

    with HTTPClient(DWD_HOSTS, transport=httpx.MockTransport(forbidden)) as http:
        client = DWDClient(http)
        with pytest.raises(ValueError, match="five-digit"):
            client.solar("../bad", DAY, DAY)
        with pytest.raises(ValueError, match="ordered"):
            client.solar(STATION, date(2024, 1, 2), DAY)
        output = tmp_path / "solar.parquet"
        output.with_suffix(".parquet.source.zip").write_bytes(archive_bytes())
        with pytest.raises(ValueError, match="Incomplete"):
            client.retrieve(STATION, DAY, DAY, output)
