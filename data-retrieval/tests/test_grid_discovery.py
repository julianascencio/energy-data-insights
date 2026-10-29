"""Synthetic location-discovery evidence; no live data or credentials."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime

import httpx
import pandas as pd
import pytest

from energy_data_retrieval.grid_discovery import (
    cmip6_plan_candidates,
    grid_datasets,
    verify_open_meteo,
)
from energy_data_retrieval.sources.cmip6 import (
    CMIP6_INDEX_HOSTS,
    CMIP6Client,
    CMIP6Plan,
    CMIP6Query,
)
from energy_data_retrieval.sources.earthmover_era5.client import PINNED_SNAPSHOT
from energy_data_retrieval.sources.open_meteo import (
    OpenMeteoClient,
    Site,
    WeatherChunk,
    WeatherProduct,
)
from energy_data_retrieval.sources.open_meteo.client import OPEN_METEO_HOSTS
from energy_data_retrieval.transport import (
    HTTPClient,
    HTTPConfig,
    JSONValue,
    array_value,
    object_value,
)

DAY = date(2025, 1, 1)


def _weather_payload(*, missing: str = "none") -> dict[str, JSONValue]:
    first = int(pd.Timestamp("2025-01-01T00:00:00Z").timestamp())
    values: list[JSONValue] = [None if missing == "all" else 1.0] * 25
    temperature = values.copy()
    if missing == "partial":
        temperature[2] = None
    return {
        "latitude": 28.25,
        "longitude": -16.5,
        "utc_offset_seconds": 0,
        "hourly_units": {
            "shortwave_radiation": "W/m²",
            "temperature_2m": "°C",
            "wind_speed_10m": "m/s",
            "wind_gusts_10m": "m/s",
        },
        "hourly": {
            "time": [first + index * 3600 for index in range(25)],
            "shortwave_radiation": values,
            "temperature_2m": temperature,
            "wind_speed_10m": values,
            "wind_gusts_10m": values,
        },
    }


def _http(handler: httpx.MockTransport | None = None) -> HTTPClient:
    return HTTPClient(
        OPEN_METEO_HOSTS,
        transport=handler or httpx.MockTransport(lambda _: httpx.Response(500)),
        config=HTTPConfig(minimum_interval_seconds=0, attempts=1),
    )


def test_default_candidates_are_json_safe_and_make_no_availability_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected(*args: object, **kwargs: object) -> None:
        raise AssertionError("Candidate discovery must not retrieve data")

    monkeypatch.setattr(OpenMeteoClient, "weather", unexpected)
    rows = grid_datasets(28.37, -16.38)
    assert [row["dataset_id"] for row in rows] == [
        "open_meteo_era5",
        "open_meteo_ifs",
        "earthmover_era5",
        "cmip6",
        "gpcc_monthly_v2025",
        "cru_ts_v4_10",
        "reanalysis-era5-single-levels",
        "reanalysis-era5-single-levels-monthly-means",
    ]
    assert json.loads(json.dumps(rows, allow_nan=False)) == rows
    assert all(row["availability_status"] == "not_checked" for row in rows)
    assert all(row["cell_latitude"] is None and row["cell_longitude"] is None for row in rows)
    assert all(
        array_value(row["reference_ids"])[0] == "ascencio_vasquez_2021_thesis" for row in rows
    )
    assert rows[0]["coverage_start"] == "1940-01-01"
    assert rows[1]["coverage_start"] is None
    assert rows[2]["coverage_start"] is None and rows[2]["coverage_end"] is None
    assert rows[2]["snapshot_id"] == PINNED_SNAPSHOT
    assert rows[3]["geographic_status"] == "point_coverage_unverified"
    assert rows[3]["supported_variables"] == [] and rows[3]["selection_status"] == "required"


@pytest.mark.parametrize(
    ("latitude", "longitude"),
    [(91, 0), (0, 181), (float("nan"), 0), (0, float("inf")), (True, 0)],
)
def test_invalid_coordinates_are_rejected(latitude: float, longitude: float) -> None:
    with pytest.raises(ValueError, match=r"finite|range"):
        grid_datasets(latitude, longitude)


def test_date_annotation_never_infers_snapshot_or_ifs_coverage() -> None:
    rows = grid_datasets(90, 180, start=date(1939, 12, 31), end=date(1940, 1, 1))
    assert rows[0]["temporal_status"] == "partly_outside_documented_coverage"
    assert all(row["temporal_status"] == "not_checked" for row in rows[1:4])
    rows = grid_datasets(-90, -180, start=date(1939, 1, 1), end=date(1939, 12, 31))
    assert rows[0]["temporal_status"] == "outside_documented_coverage"
    assert rows[0]["availability_status"] == "not_checked"
    with pytest.raises(ValueError, match="together"):
        grid_datasets(0, 0, start=DAY)
    with pytest.raises(ValueError, match="before"):
        grid_datasets(0, 0, start=date(2025, 1, 2), end=DAY)
    with pytest.raises(ValueError, match="calendar date"):
        grid_datasets(0, 0, start=datetime(2025, 1, 1, tzinfo=UTC), end=DAY)


@pytest.mark.parametrize("missing", ["none", "partial", "all"])
def test_probe_uses_only_two_bounded_products_and_retains_missingness(missing: str) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.url.params["latitude"] == "28.37"
        assert request.url.params["start_date"] == "2025-01-01"
        assert request.url.params["end_date"] == "2025-01-02"
        assert request.url.params["cell_selection"] == "nearest"
        assert request.url.params["elevation"] == "nan"
        assert "apikey" not in request.url.params
        return httpx.Response(200, json=_weather_payload(missing=missing))

    original = grid_datasets(28.37, -16.38)
    saved = json.dumps(original, sort_keys=True)
    with _http(httpx.MockTransport(handler)) as http:
        rows = verify_open_meteo(http, original, day=DAY)
    assert json.dumps(original, sort_keys=True) == saved
    assert len(requests) == 2
    assert [request.url.params["models"] for request in requests] == ["era5", "ecmwf_ifs"]
    for row in rows[:2]:
        assert row["cell_latitude"] == 28.25 and row["cell_longitude"] == -16.5
        sample = object_value(row["sample"])
        assert sample["date"] == "2025-01-01" and sample["rows"] == 24
        assert sample["complete"] is (missing == "none")
        assert "one UTC day only" in str(sample["scope"])
        assert len(str(object_value(sample["request"])["sha256"])) == 64
        counts = object_value(sample["non_null_counts"])
        if missing == "all":
            assert row["availability_status"] == "empty_sample"
            assert all(value == 0 for value in counts.values())
        else:
            assert row["availability_status"] == "verified_sample"
            assert counts["temperature_c"] == (22 if missing == "partial" else 24)
            assert counts["ghi_wm2"] == 24
    assert rows[2:] == original[2:]
    json.dumps(rows, allow_nan=False)


def test_provider_failure_isolated_and_raw_error_excluded(monkeypatch: pytest.MonkeyPatch) -> None:
    original_weather = OpenMeteoClient.weather

    def fail_one(self: OpenMeteoClient, site: Site, start: date, end: date) -> WeatherChunk:
        if self.product == WeatherProduct.ERA5:
            raise ValueError("synthetic private diagnostic that must never be copied")
        return original_weather(self, site, start, end)

    monkeypatch.setattr(OpenMeteoClient, "weather", fail_one)
    with _http(httpx.MockTransport(lambda _: httpx.Response(200, json=_weather_payload()))) as http:
        rows = verify_open_meteo(http, grid_datasets(28.37, -16.38), day=DAY)
    assert rows[0]["availability_status"] == "provider_error"
    assert rows[0]["cell_latitude"] is None
    assert object_value(rows[0]["sample"])["complete"] is False
    assert "private diagnostic" not in json.dumps(rows)
    assert rows[1]["availability_status"] == "verified_sample"


def test_invalid_sample_location_and_day_do_not_claim_success() -> None:
    payload = _weather_payload()
    payload["latitude"] = 95.0
    with _http(httpx.MockTransport(lambda _: httpx.Response(200, json=payload))) as http:
        rows = verify_open_meteo(http, grid_datasets(0, 0), day=DAY)
        assert rows[0]["availability_status"] == "provider_error"
        assert rows[0]["cell_latitude"] is None
        with pytest.raises(ValueError, match="endpoint"):
            verify_open_meteo(http, [], day=date.max)
        with pytest.raises(ValueError, match="calendar date"):
            verify_open_meteo(http, [], day=datetime(2025, 1, 1))


def test_duplicate_candidates_rejected_before_network() -> None:
    def unexpected(_: httpx.Request) -> httpx.Response:
        raise AssertionError("Duplicate candidates must fail before any requests")

    rows = grid_datasets(0, 0)
    with (
        _http(httpx.MockTransport(unexpected)) as http,
        pytest.raises(ValueError, match="unique"),
    ):
        verify_open_meteo(http, [*rows, rows[0]], day=DAY)


def _cmip6_plan() -> CMIP6Plan:
    query = CMIP6Query(
        "CanESM5", "historical", "r1i1p1f1", "Amon", "rsds", "gn", start_year=2005, end_year=2006
    )
    identifier = "CMIP6.CMIP.CCCma.CanESM5.historical.r1i1p1f1.Amon.rsds.gn.v20190429"
    filename = "rsds_Amon_CanESM5_historical_r1i1p1f1_gn_200001-201412.nc"
    feature = {
        "type": "Feature",
        "id": identifier,
        "collection": "CMIP6",
        "properties": {
            "cmip6:activity_id": ["CMIP"],
            "cmip6:institution_id": "CCCma",
            "cmip6:source_id": "CanESM5",
            "cmip6:experiment_id": "historical",
            "cmip6:member_id": "r1i1p1f1",
            "cmip6:variant_label": "r1i1p1f1",
            "cmip6:sub_experiment_id": "none",
            "cmip6:table_id": "Amon",
            "cmip6:variable_id": "rsds",
            "cmip6:grid_label": "gn",
            "cmip6:mip_era": "CMIP6",
            "version": "20190429",
            "latest": True,
            "retracted": False,
        },
        "links": [{"rel": "cite-as", "href": "https://example.org/fixture-citation"}],
        "assets": {
            filename: {
                "href": "https://esgf-node.ornl.gov/thredds/fileServer/fixture/" + filename,
                "description": "HTTPServer Link",
                "type": "application/netcdf",
                "roles": ["data"],
                "file:size": 1000,
                "file:checksum": "1220" + "a" * 64,
            }
        },
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert not {"latitude", "longitude", "bbox"}.intersection(request.url.params)
        if request.url.path == "/collections":
            return httpx.Response(200, json={"collections": [{"id": "CMIP6"}]})
        return httpx.Response(
            200,
            json={
                "type": "FeatureCollection",
                "features": [feature],
                "numberMatched": 1,
                "links": [],
            },
        )

    with HTTPClient(
        CMIP6_INDEX_HOSTS,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        return CMIP6Client(http).search(query)


def test_cmip6_plan_keeps_native_files_and_never_infers_point_coverage() -> None:
    plan = _cmip6_plan()
    original = plan.sha256
    rows = cmip6_plan_candidates(plan, 28.37, -16.38)
    assert len(rows) == 1
    row = rows[0]
    assert row["dataset_id"] == plan.datasets[0]["id"]
    assert row["availability_status"] == "catalogue_verified"
    assert row["geographic_status"] == "point_coverage_unverified"
    assert row["cell_latitude"] is None and row["cell_longitude"] is None
    assert row["coverage_start"] is None and row["coverage_end"] is None
    assert row["plan_sha256"] == original
    assert row["provider_links"] == plan.datasets[0]["links"]
    assert row["supported_variables"] == ["rsds"]
    file = object_value(array_value(row["selected_files"])[0])
    assert file["start_label"] == "200001" and file["end_label"] == "201412"
    assert file["relative_path"] == plan.files[0].relative_path
    assert object_value(row["selection"])["start_year"] == 2005
    assert plan.sha256 == original
    json.dumps(rows, allow_nan=False)


def test_gpcc_cru_candidates_have_monthly_semantics_and_explicit_time_coverage() -> None:
    rows = {
        str(row["source"]): row
        for row in grid_datasets(28.37, -16.38, start=date(2025, 1, 1), end=date(2026, 1, 1))
    }
    assert rows["gpcc"]["temporal_resolution"] == "monthly"
    assert rows["gpcc"]["temporal_status"] == "within_documented_start_only"
    assert rows["cru_ts"]["temporal_status"] == "partly_outside_documented_coverage"
    for source in ("gpcc", "cru_ts"):
        assert rows[source]["geographic_status"] == "point_coverage_unverified"
        assert rows[source]["availability_status"] == "not_checked"
        assert rows[source]["cell_latitude"] is None
