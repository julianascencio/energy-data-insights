"""Synthetic current GHCNh fixtures validate native timing, units, QC and replay."""

from __future__ import annotations

import csv
import io
import json
from datetime import date
from pathlib import Path

import httpx
import pandas as pd
import pytest

from energy_data_retrieval.sources.noaa import (
    NOAA_HOSTS,
    STATIONS_ENDPOINT,
    NOAAClient,
    normalize_observations,
    normalize_stations,
    save_observations,
)
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, RetrievalError

STATION = "CIM00085574"
DAY = date(2026, 1, 1)
VARIABLES = (
    "temperature",
    "dew_point_temperature",
    "wind_speed",
    "wind_gust",
    "sea_level_pressure",
    "station_level_pressure",
    "wet_bulb_temperature",
    "altimeter",
    "visibility",
)
ATTRIBUTES = (
    "Measurement_Code",
    "Quality_Code",
    "Report_Type",
    "Source_Code",
    "Source_Station_ID",
)


def row(stamp: str = "2026-01-01T00:51:00", **updates: str) -> dict[str, str]:
    stamp_date, stamp_time = stamp[:19].split("T")
    year, month, day = stamp_date.split("-")
    hour, minute, _ = stamp_time.split(":")
    result = {
        "STATION": STATION,
        "Station_name": "Synthetic station",
        "DATE": stamp,
        "Year": year,
        "Month": month,
        "Day": day,
        "Hour": hour,
        "Minute": minute,
        "LATITUDE": "-33.4",
        "LONGITUDE": "-70.8",
        "ELEVATION": "476.0",
    }
    for variable in VARIABLES:
        result[variable] = ""
        result.update({f"{variable}_{attribute}": "" for attribute in ATTRIBUTES})
    result.update(
        {
            "temperature": "-1.2",
            "temperature_Quality_Code": "2",
            "temperature_Report_Type": "FM15",
            "temperature_Source_Code": "223",
            "temperature_Source_Station_ID": "ICAO-FICT",
            "dew_point_temperature": "-5.3",
            "wind_speed": "0.0",
            "wind_gust": "3.6",
            "sea_level_pressure": "1013.2",
            "station_level_pressure": "950.0",
            "wet_bulb_temperature": "-1.8",
            "altimeter": "1013.0",
            "visibility": "16.09",
            "wind_direction": "VRB",
            "precipitation": "0.0",
            "precipitation_Measurement_Code": "T",
            "REM": "Synthetic observation; quoted | pipe retained",
        }
    )
    result.update(updates)
    return result


def psv(rows: list[dict[str, str]]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(row()), delimiter="|", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


CATALOGUE = (
    "GHCN_ID,LATITUDE,LONGITUDE,ELEVATION,STATE,NAME,GSN,(US)HCN_(US)CRN,WMO_ID,ICAO,ISO_CODE\n"
    "CIM00085574,-33.4,-70.8,476.0,,Synthetic Chile,,,,FICT,CL\n"
    "CIM00085442,-23.4,-70.5,-999.9,,Synthetic north,,,,TEST,CL\n"
    "USW00014732,40.8,-73.9,3.0,NY,Synthetic USA,,,,FAKE,US\n"
)


def test_native_units_timestamp_raw_qc_and_trace_are_preserved() -> None:
    text = psv(
        [
            row(),
            row(
                "2026-01-01T01:23:00",
                temperature="",
                wind_speed="",
                wind_gust="0.0",
                temperature_Quality_Code="",
            ),
            row("2026-01-02T00:00:00", temperature="12.3"),
        ]
    )
    frame = normalize_observations(text, STATION, DAY, DAY)
    assert len(frame) == 2
    assert frame["timestamp"].tolist() == [
        pd.Timestamp("2026-01-01T00:51Z"),
        pd.Timestamp("2026-01-01T01:23Z"),
    ]
    assert frame.loc[0, "temperature_c"] == -1.2  # Native decimals, no legacy ISD /10.
    assert frame.loc[0, "dewpoint_c"] == -5.3
    assert frame.loc[0, "wind_speed_ms"] == 0
    assert frame.loc[0, "gust_ms"] == 3.6 and frame.loc[1, "gust_ms"] == 0
    assert pd.isna(frame.loc[1, "temperature_c"]) and pd.isna(frame.loc[1, "wind_speed_ms"])
    assert frame.loc[0, "temperature_Quality_Code"] == "2"
    assert frame.loc[1, "temperature_Quality_Code"] == ""
    assert frame.loc[0, "precipitation_Measurement_Code"] == "T"
    assert frame.loc[0, "wind_direction"] == "VRB"
    assert frame.loc[0, "REM"] == row()["REM"]
    assert frame.loc[0, "sea_level_pressure_hpa"] == 1013.2
    assert "ghi_wm2" not in frame and "site_id" not in frame and "duration_hours" not in frame
    assert frame.attrs["native_rows"] == 3 and not frame.attrs["hourly_resampling_applied"]
    assert not frame.attrs["quality_filter_applied"]
    assert isinstance(frame["STATION"].dtype, pd.StringDtype)
    assert frame["STATION"].dtype.storage == "pyarrow"


def test_simultaneous_distinct_reports_survive_equal_duplicates_are_removed() -> None:
    first = row()
    other_report = row(temperature="-1.0", temperature_Report_Type="FM16")
    frame = normalize_observations(psv([first, first, other_report]), STATION, DAY, DAY)
    assert len(frame) == 2 and frame["timestamp"].nunique() == 1
    assert frame.attrs["duplicate_equal_rows_removed"] == 1
    with pytest.raises(RetrievalError, match="same station/time/report/source"):
        normalize_observations(psv([first, row(temperature="-2.0")]), STATION, DAY, DAY)
    with pytest.raises(RetrievalError, match="same station/time/report/source"):
        normalize_observations(psv([first, row(temperature_Quality_Code="1")]), STATION, DAY, DAY)


@pytest.mark.parametrize(
    "changes",
    [
        {"STATION": "USW00014732"},
        {"DATE": "2026-01-01T00:51:00+03:00"},
        {"DATE": "2026-02-30T00:51:00"},
        {"DATE": "2025-01-01T00:51:00"},
        {"Minute": "50"},
        {"temperature": "NaN"},
        {"temperature": "inf"},
        {"LATITUDE": "91"},
    ],
)
def test_wrong_identity_calendar_schema_and_numeric_drift_fail(changes: dict[str, str]) -> None:
    with pytest.raises(RetrievalError):
        normalize_observations(psv([row(**changes)]), STATION, DAY, DAY)


def test_native_export_completeness_and_resource_bounds() -> None:
    text = psv([row(), row("2026-01-01T01:51:00")])
    with pytest.raises(RetrievalError, match="row limit"):
        normalize_observations(text, STATION, DAY, DAY, maximum_rows=1)
    with pytest.raises(RetrievalError, match="complete record"):
        normalize_observations(text.rstrip("\n"), STATION, DAY, DAY)
    with pytest.raises(RetrievalError, match="record width"):
        normalize_observations(text + STATION + "|2026-01-01T02:00:00\n", STATION, DAY, DAY)
    with pytest.raises(RetrievalError, match="QC schema"):
        normalize_observations(
            "STATION|DATE\n" + STATION + "|2026-01-01T00:00:00\n", STATION, DAY, DAY
        )


def test_empty_date_selection_is_not_filled_to_hourly() -> None:
    frame = normalize_observations(psv([row("2026-01-02T00:51:00")]), STATION, DAY, DAY)
    assert frame.empty
    assert list(frame["timestamp"]) == []
    assert frame.attrs["native_rows"] == 1 and not frame.attrs["hourly_coverage_claimed"]


def test_station_catalogue_iso_country_filter_and_bbox_without_guessed_coverage() -> None:
    frame = normalize_stations(CATALOGUE, country_code="CL", bbox=(-72, -35, -69, -30))
    assert frame["station_id"].tolist() == [STATION]
    assert frame.loc[0, "country_code"] == "CL" and frame.loc[0, "country_fips"] == "CI"
    assert not frame.attrs["availability_inferred"] and not frame.attrs["nearest_station_selected"]
    all_chile = normalize_stations(CATALOGUE, country_code="CL")
    assert len(all_chile) == 2 and all_chile["elevation_m"].isna().sum() == 1
    assert normalize_stations(CATALOGUE, country_code="CI").empty
    with pytest.raises(ValueError, match="ISO_CODE"):
        normalize_stations(CATALOGUE, country_code="cl")
    with pytest.raises(ValueError, match="WEST SOUTH EAST NORTH"):
        normalize_stations(CATALOGUE, bbox=(170, -10, -170, 10))
    with pytest.raises(RetrievalError, match="row limit"):
        normalize_stations(CATALOGUE, maximum_stations=1)


def test_station_metadata_conflicts_are_not_silently_merged() -> None:
    extra = CATALOGUE.splitlines()[1].replace("476.0", "600.0")
    with pytest.raises(RetrievalError, match="conflicting records"):
        normalize_stations(CATALOGUE + extra + "\n")


def test_catalogue_keeps_case_sensitive_ids_and_flags_invalid_coordinates() -> None:
    text = CATALOGUE + (
        "CAU0mt_st-1,40,-70,0,,Synthetic case-sensitive ID,,,,,CA\n"
        "RUU71-00102,135.117,48.8,0,,Synthetic bad coordinate,,,,,XX\n"
    )
    frame = normalize_stations(text)
    assert "CAU0mt_st-1" in frame["station_id"].tolist()
    bad = frame.loc[frame["station_id"].eq("RUU71-00102")].iloc[0]
    assert bad["LATITUDE"] == "135.117" and bad["LONGITUDE"] == "48.8"
    assert not bad["coordinates_valid"]
    assert pd.isna(bad["latitude"]) and pd.isna(bad["longitude"])
    assert frame.attrs["source_rows_without_valid_coordinates"] == 1
    assert len(normalize_stations(text, country_code="CL")) == 2


def test_public_client_exact_native_paths_and_annual_iteration() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.url.host == "www.ncei.noaa.gov" and not request.url.query
        if str(request.url) == STATIONS_ENDPOINT:
            return httpx.Response(200, text=CATALOGUE)
        year = int(request.url.path.split("/")[-3])
        assert request.url.path.endswith(f"/psv/GHCNh_{STATION}_{year}.psv")
        return httpx.Response(200, text=psv([row(f"{year}-01-01T00:51:00")]))

    with HTTPClient(
        NOAA_HOSTS,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        client = NOAAClient(http)
        stations = client.stations(country_code="CL")
        result = list(client.iter_observations(STATION, date(2025, 12, 31), date(2026, 1, 1)))
    assert len(requests) == 3 and len(stations.frame) == 2
    assert len(result) == 2 and result[0].frame.empty and len(result[1].frame) == 1
    assert result[0].start == date(2025, 12, 31) and result[1].end == date(2026, 1, 1)


def test_client_rejects_unbounded_or_unsafe_input_before_network() -> None:
    def forbidden(_: httpx.Request) -> httpx.Response:
        pytest.fail("Invalid input must not access NOAA")

    with HTTPClient(NOAA_HOSTS, transport=httpx.MockTransport(forbidden)) as http:
        client = NOAAClient(http, maximum_years=1)
        with pytest.raises(ValueError, match="maximum_years"):
            list(client.iter_observations(STATION, date(2025, 1, 1), DAY))
        with pytest.raises(ValueError, match="calendar year"):
            client.observations(STATION, date(2025, 1, 1), DAY)
        with pytest.raises(ValueError, match="station ID"):
            client.observations("../../station", DAY, DAY)
        with pytest.raises(ValueError, match="ISO_CODE"):
            client.stations(country_code="*")


def test_verified_parquet_and_native_source_are_reused_before_network(tmp_path: Path) -> None:
    text = psv([row()])
    requests = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        return httpx.Response(200, text=text)

    output = tmp_path / "station_2026.parquet"
    with HTTPClient(
        NOAA_HOSTS,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        client = NOAAClient(http)
        first = client.retrieve(STATION, DAY, DAY, output)
        second = client.retrieve(STATION, DAY, DAY, output)
        assert first == second and requests == 1
        assert output.with_suffix(".source.psv").read_text() == text
        restored = pd.read_parquet(output)
        assert restored.loc[0, "temperature_Quality_Code"] == "2"
        manifest = json.loads(output.with_suffix(".parquet.json").read_text())
        assert manifest["provenance"]["native_source"]["filename"] == "station_2026.source.psv"
        assert manifest["provenance"]["metadata"]["hourly_resampling_applied"] is False
        output.with_suffix(".source.psv").write_text(text + "tampered\n")
        with pytest.raises(ValueError, match="preserved source"):
            client.retrieve(STATION, DAY, DAY, output)
        assert requests == 1


def test_incomplete_source_checkpoint_is_not_overwritten(tmp_path: Path) -> None:
    def forbidden(_: httpx.Request) -> httpx.Response:
        pytest.fail("An incomplete checkpoint needs inspection before network")

    output = tmp_path / "station_2026.parquet"
    output.with_suffix(".source.psv").write_text(psv([row()]))
    with (
        HTTPClient(NOAA_HOSTS, transport=httpx.MockTransport(forbidden)) as http,
        pytest.raises(ValueError, match="Incomplete NOAA"),
    ):
        NOAAClient(http).retrieve(STATION, DAY, DAY, output)


def test_mutated_normalized_values_cannot_claim_unmodified_source_provenance(
    tmp_path: Path,
) -> None:
    with HTTPClient(
        NOAA_HOSTS,
        transport=httpx.MockTransport(lambda _: httpx.Response(200, text=psv([row()]))),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        result = NOAAClient(http).observations(STATION, DAY, DAY)
    result.frame.loc[0, "temperature_c"] = 99.0
    with pytest.raises(ValueError, match="differ from the preserved"):
        save_observations(result, tmp_path / "changed.parquet")
    assert list(tmp_path.iterdir()) == []


def test_missing_station_year_is_an_explicit_provider_failure() -> None:
    with (
        HTTPClient(
            NOAA_HOSTS, transport=httpx.MockTransport(lambda _: httpx.Response(404))
        ) as http,
        pytest.raises(RetrievalError, match="HTTP 404"),
    ):
        NOAAClient(http).observations(STATION, DAY, DAY)
