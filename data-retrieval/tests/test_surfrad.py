"""SURFRAD native averages, flags, catalogue identities and verified persistence."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path

import httpx
import pandas as pd
import pytest

from energy_data_retrieval.sources.surfrad import (
    STATION_IDS,
    STATIONS_ENDPOINT,
    SURFRAD_HOSTS,
    SURFRADClient,
    normalize_day,
    normalize_stations,
    save_day,
)
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, RetrievalError

DAY = date(2026, 1, 1)
URL = "https://gml.noaa.gov/aftp/data/radiation/surfrad/bon/2026/bon26001.dat"
_SITES = (
    ("BND<sup>*</sup>", "Bondville, Illinois", "40.05192", "88.37309", "230", "April 1994"),
    ("TBL", "Table Mountain, Boulder, Colorado", "40.12498", "105.23680", "1689", "July 1995"),
    ("DRA", "Desert Rock, Nevada", "36.62373", "116.01947", "1007", "March 1998"),
    ("FPK", "Fort Peck, Montana", "48.30783", "105.10170", "634", "November 1994"),
    ("GWN", "Goodwin Creek, Mississippi", "34.2547", "89.8729", "98", "December 1994"),
    ("PSU", "Penn. State Univ., Pennsylvania", "40.72012", "77.93085", "376", "June 1998"),
    ("SXF", "Sioux Falls, South Dakota", "43.73403", "96.62328", "473", "June 2003"),
)


def catalogue() -> str:
    header = (
        "<tr>"
        + "".join(
            f"<th>{name}</th>"
            for name in (
                "Code",
                "Name",
                "Latitude",
                "Longitude",
                "Elevation",
                "Time Zone",
                "Installed",
            )
        )
        + "</tr>"
    )
    rows = []
    for code, name, lat, lon, elevation, installed in _SITES:
        fields = (
            code,
            f'<a href="station.html">{name}</a>',
            lat + "&deg; N",
            lon + "&deg; W",
            elevation + " m",
            "6 hours from UTC",
            installed,
        )
        rows.append("<tr>" + "".join(f"<td>{field}</td>" for field in fields) + "</tr>")
    external = "<tr><td>SGP</td><td>External ARM site</td>" + "<td></td>" * 5 + "</tr>"
    return "<html><table>" + header + "".join(rows) + external + "</table></html>\n"


def row(day: date = DAY, minute: int = 0, *, changes: dict[str, str] | None = None) -> list[str]:
    # The 20 measurement/flag pairs follow NOAA's documented on-disk order.
    values = [
        "-1.2",
        "0.0",
        "900.0",
        "20.0",
        "300.0",
        "274.15",
        "274.16",
        "400.0",
        "290.1",
        "290.2",
        "1.7",
        "54.0",
        "50.0",
        "-100.0",
        "-50.0",
        "25.4",
        "60.0",
        "3.0",
        "180.0",
        "1010.0",
    ]
    fields = [
        str(day.year),
        str(day.timetuple().tm_yday),
        str(day.month),
        str(day.day),
        str(minute // 60),
        str(minute % 60),
        f"{minute / 60:.3f}",
        "100.0",
    ]
    for value in values:
        fields.extend((value, "0"))
    for index, value in (changes or {}).items():
        fields[int(index)] = value
    return fields


def daily(rows: list[list[str]] | None = None, *, day: date = DAY) -> str:
    return " Bondville\r\n   40.05  -88.37  213 m version 1\r\n" + "".join(
        " " + " ".join(fields) + "\r\n" for fields in (rows if rows is not None else [row(day)])
    )


def client(
    handler: Callable[[httpx.Request], httpx.Response],
    *,
    maximum_response_bytes: int = 8 * 1024**2,
) -> HTTPClient:
    return HTTPClient(
        SURFRAD_HOSTS,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(
            minimum_interval_seconds=0, maximum_response_bytes=maximum_response_bytes
        ),
        sleep=lambda _: None,
    )


def test_native_end_times_values_units_missing_flags_and_raw_fields() -> None:
    first = row(changes={"9": "2", "38": "-9999.9", "39": "1"})
    second = row(minute=2, changes={"8": "0.0", "7": "-9999.9"})
    frame = normalize_day(daily([first, second]), "bon", DAY)
    assert frame.timestamp.tolist() == [
        pd.Timestamp("2026-01-01T00:00Z"),
        pd.Timestamp("2026-01-01T00:02Z"),
    ]
    assert frame.interval_start.iloc[0] == pd.Timestamp("2025-12-31T23:59Z")
    assert frame.interval_end.equals(frame.timestamp)
    assert frame.duration_seconds.tolist() == [60, 60]
    assert frame.ghi_wm2.tolist() == [-1.2, 0.0]
    assert frame.ghi_wm2_qc.tolist() == [2, 0]  # Flagged observations remain present.
    assert pd.isna(frame.temperature_10m_c.iloc[0])
    assert frame.temperature_10m_c.iloc[1] == 25.4
    assert frame.uvb_mwm2.iloc[0] == 1.7 and frame.par_wm2.iloc[0] == 54
    assert frame.downwelling_case_temperature_k.iloc[0] == 274.15
    assert frame.station_pressure_hpa.iloc[0] == 1010
    assert frame["source:temp"].iloc[0] == "-9999.9"
    assert frame["source:qc_dwsolar"].iloc[0] == "2"
    assert len([name for name in frame if str(name).startswith("source:")]) == 48
    assert pd.isna(frame.solar_zenith_deg.iloc[1])
    assert frame.attrs["unreported_nominal_records"] == 1438
    assert not frame.attrs["quality_filter_applied"]
    assert not frame.attrs["hourly_resampling_applied"]
    assert not frame.attrs["gap_filling_applied"]
    assert not frame.attrs["cross_provider_deduplication_applied"]
    assert "BSRN" in frame.attrs["possible_network_overlap"]


def test_legacy_three_minute_averages_and_leap_year_are_not_shifted() -> None:
    day = date(2008, 12, 31)
    frame = normalize_day(daily([row(day), row(day, minute=3)], day=day), "bon", day)
    assert frame.timestamp.iloc[0] == pd.Timestamp("2008-12-31T00:00Z")
    assert frame.interval_start.iloc[0] == pd.Timestamp("2008-12-30T23:57Z")
    assert frame.duration_seconds.tolist() == [180, 180]
    assert frame.attrs["nominal_records_per_utc_day"] == 480
    assert frame["source:jday"].iloc[0] == "366"


@pytest.mark.parametrize(
    "changes", [{"0": "2025"}, {"1": "2"}, {"2": "2"}, {"3": "2"}, {"4": "24"}, {"5": "60"}]
)
def test_calendar_fields_must_agree_with_selected_day(changes: dict[str, str]) -> None:
    with pytest.raises(RetrievalError, match="calendar"):
        normalize_day(daily([row(changes=changes)]), "bon", DAY)


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"6": "0.2"}, "decimal time"),
        ({"8": "NaN"}, "numeric"),
        ({"8": "1e999"}, "nonfinite"),
        ({"9": "-1"}, "flag"),
        ({"7": "181.0"}, "solar zenith"),
    ],
)
def test_invalid_measurement_or_time_fields_fail(changes: dict[str, str], message: str) -> None:
    with pytest.raises(RetrievalError, match=message):
        normalize_day(daily([row(changes=changes)]), "bon", DAY)


def test_duplicate_disordered_truncated_and_empty_data_fail() -> None:
    for rows in ([row(), row()], [row(minute=2), row()]):
        with pytest.raises(RetrievalError, match="unique and ordered"):
            normalize_day(daily(rows), "bon", DAY)
    with pytest.raises(RetrievalError, match="record width"):
        normalize_day(daily([row()[:-1]]), "bon", DAY)
    with pytest.raises(RetrievalError, match="incomplete"):
        normalize_day(daily().rstrip(), "bon", DAY)
    with pytest.raises(RetrievalError, match=r"no observations|header"):
        normalize_day(daily([]) + "\n", "bon", DAY)


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ("Bondville", "Fort Peck", "station"),
        ("version 1", "version 2", "version"),
        ("40.05", "91.00", "coordinates"),
    ],
)
def test_source_header_identity_and_geography_are_checked(old: str, new: str, message: str) -> None:
    with pytest.raises(RetrievalError, match=message):
        normalize_day(daily().replace(old, new), "bon", DAY)


def test_row_bounds_and_missing_flag_inconsistency_are_explicit() -> None:
    with pytest.raises(RetrievalError, match="row bound"):
        normalize_day(daily([row(), row(minute=1)]), "bon", DAY, maximum_rows=1)
    old = date(2008, 1, 1)
    with pytest.raises(RetrievalError, match="row bound"):
        normalize_day(daily([row(old, minute=i) for i in range(481)]), "bon", old)
    frame = normalize_day(daily([row(changes={"8": "-9999.9", "9": "0"})]), "bon", DAY)
    assert pd.isna(frame.ghi_wm2.iloc[0]) and frame.ghi_wm2_qc.iloc[0] == 0
    assert frame.attrs["missing_values_without_flag_one"] == 1


def test_official_catalogue_retains_archive_identity_and_current_positions() -> None:
    frame = normalize_stations(catalogue())
    assert set(frame.station_id) == set(STATION_IDS) and len(frame) == 7
    bon = frame.set_index("station_id").loc["bon"]
    assert bon.site_code == "BND" and bon.elevation_m == 230
    assert bon.latitude == 40.05192 and bon.longitude == -88.37309
    assert bon["source:Time Zone"] == "6 hours from UTC"
    assert bon.archive_directory.endswith("/bon/")
    assert frame.possible_bsrn_overlap.all()
    assert not frame.attrs["catalogue_positions_are_observation_positions"]
    assert normalize_day(daily(), "bon", DAY).elevation_m.iloc[0] == 213


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ("<td>TBL</td>", "<td>BND</td>", "seven"),
        ("<td>TBL</td>", "<td>XYZ</td>", "new station"),
        ("40.05192", "91.0", "coordinate"),
        ("<th>Latitude</th>", "<th>Changed</th>", "table"),
    ],
)
def test_changed_or_malformed_catalogue_fails(old: str, new: str, message: str) -> None:
    with pytest.raises(RetrievalError, match=message):
        normalize_stations(catalogue().replace(old, new))


def test_daily_and_station_snapshots_restart_without_network(tmp_path: Path) -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        assert request.headers["Accept"] == "*/*"
        return httpx.Response(
            200, content=(catalogue() if request.url.path.endswith(".html") else daily()).encode()
        )

    with client(handler) as http:
        provider = SURFRADClient(http)
        out = tmp_path / "bon" / "2026-01-01.parquet"
        first = provider.retrieve("bon", DAY, out)
        assert provider.retrieve("bon", DAY, out) == first
        station_path = tmp_path / "stations.parquet"
        first_stations = provider.retrieve_stations(station_path)
        assert provider.retrieve_stations(station_path) == first_stations
    assert calls == [URL, STATIONS_ENDPOINT]
    assert out.with_suffix(".source.dat").read_bytes() == daily().encode()
    assert station_path.with_suffix(".source.html").read_bytes() == catalogue().encode()
    manifest = json.loads(out.with_suffix(".parquet.json").read_text())
    assert manifest["provenance"]["native_source"]["filename"] == "2026-01-01.source.dat"
    assert manifest["request"]["timestamp_convention"] == "native UTC interval end"
    assert pd.read_parquet(out).shape[0] == 1


@pytest.mark.parametrize(
    "damage", ["changed_source", "missing_source", "changed_parquet", "symlink_source"]
)
def test_modified_or_incomplete_snapshots_fail_before_network(tmp_path: Path, damage: str) -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, content=daily().encode())

    with client(handler) as http:
        provider = SURFRADClient(http)
        output = tmp_path / "day.parquet"
        provider.retrieve("bon", DAY, output)
        source = output.with_suffix(".source.dat")
        if damage == "changed_source":
            source.write_text("altered")
        elif damage == "missing_source":
            source.unlink()
        elif damage == "changed_parquet":
            output.write_bytes(b"altered")
        else:
            target = tmp_path / "original.dat"
            source.rename(target)
            source.symlink_to(target)
        with pytest.raises(ValueError):
            provider.retrieve("bon", DAY, output)
    assert calls == 1


def test_mutated_frame_or_source_cannot_claim_original_provenance(tmp_path: Path) -> None:
    with client(lambda _: httpx.Response(200, content=daily().encode())) as http:
        result = SURFRADClient(http).day("bon", DAY)
    original = result.frame.copy(deep=True)
    result.frame.loc[0, "ghi_wm2"] = 999.0
    with pytest.raises(ValueError, match="normalized frame"):
        save_day(result, tmp_path / "mutated.parquet")
    changed_source = replace(result, frame=original, raw_text=daily().replace("-1.2", "-2.0"))
    with pytest.raises(ValueError, match="native text"):
        save_day(changed_source, tmp_path / "changed-source.parquet")
    assert not list(tmp_path.iterdir())


def test_bounded_daily_iteration_crosses_leap_year_without_aggregation() -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.path)
        day = date(2008, 12, 31) if request.url.path.endswith("bon08366.dat") else date(2009, 1, 1)
        return httpx.Response(200, content=daily(day=day).encode())

    with client(handler) as http:
        results = list(SURFRADClient(http).iter_days("bon", date(2008, 12, 31), date(2009, 1, 1)))
    assert [r.frame.duration_seconds.iloc[0] for r in results] == [180, 60]
    assert seen[0].endswith("/bon/2008/bon08366.dat")
    assert seen[1].endswith("/bon/2009/bon09001.dat")


def test_invalid_identifiers_dates_limits_and_incomplete_output_fail_before_network(
    tmp_path: Path,
) -> None:
    def forbidden(_: httpx.Request) -> httpx.Response:
        pytest.fail("Invalid request must not access the network")

    with client(forbidden) as http:
        provider = SURFRADClient(http, maximum_days=1)
        for station in ("../bon", "BON", "sgp", "inl"):
            with pytest.raises(ValueError, match="station ID"):
                provider.day(station, DAY)
        with pytest.raises(ValueError, match="date"):
            provider.day("bon", datetime(2026, 1, 1))
        with pytest.raises(ValueError, match="maximum_days"):
            list(provider.iter_days("bon", DAY, date(2026, 1, 2)))
        with pytest.raises(ValueError, match="maximum_rows"):
            SURFRADClient(http, maximum_rows=1441)
        output = tmp_path / "day.parquet"
        output.with_suffix(".source.dat").write_text("incomplete")
        with pytest.raises(ValueError, match="Incomplete"):
            provider.retrieve("bon", DAY, output)


def test_unavailable_days_fail_explicitly_and_large_exports_are_bounded() -> None:
    with (
        client(lambda _: httpx.Response(404)) as http,
        pytest.raises(RetrievalError, match="HTTP 404"),
    ):
        list(SURFRADClient(http).iter_days("bon", DAY, DAY))
    with (
        client(
            lambda _: httpx.Response(200, content=daily().encode()), maximum_response_bytes=50
        ) as http,
        pytest.raises(RetrievalError, match="byte limit"),
    ):
        SURFRADClient(http).day("bon", DAY)
