"""Location discovery combines evidence without claiming unverified observations."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from energy_data_retrieval import discovery
from energy_data_retrieval.sources.cmip6 import CMIP6File, CMIP6Plan, CMIP6Query
from energy_data_retrieval.station_discovery import StationCatalogue
from energy_data_retrieval.transport import HTTPClient, JSONValue

THESIS = "ascencio_vasquez_2021_thesis"


def station_catalogue(
    source: str,
    rows: list[tuple[str, float, float]],
    *,
    status: str = "local_catalogue",
    scope: dict[str, JSONValue] | None = None,
) -> StationCatalogue:
    frame = pd.DataFrame(rows, columns=["station_id", "latitude", "longitude"])
    frame["source"] = source
    frame["station_name"] = ["Synthetic station " + value for value in frame["station_id"]]
    frame.attrs["product_supported_variables"] = ["temperature", "wind"]
    return StationCatalogue(
        source=source,
        status=status,
        frame=frame,
        coverage_scope=scope
        if scope is not None
        else {"provider_catalogue_complete": True, "observations_verified": False},
        reference_ids=(THESIS,),
        requests=[],
        notes=["Synthetic catalogue; observation availability is unverified."],
    )


def install_catalogues(
    monkeypatch: pytest.MonkeyPatch, values: dict[str, StationCatalogue]
) -> list[tuple[str, HTTPClient | None, Path | None]]:
    calls: list[tuple[str, HTTPClient | None, Path | None]] = []

    def load(
        source: str, http: HTTPClient | None, *, local_path: Path | None = None
    ) -> StationCatalogue:
        calls.append((source, http, local_path))
        return values[source]

    monkeypatch.setattr(discovery, "load_station_catalogue", load)
    return calls


def example_plan() -> CMIP6Plan:
    identifier = "CMIP6.CMIP.CCCma.CanESM5.historical.r1i1p1f1.Amon.rsds.gn.v20190429"
    filename = "rsds_Amon_CanESM5_historical_r1i1p1f1_gn_200001-201412.nc"
    return CMIP6Plan(
        query=CMIP6Query("CanESM5", "historical", "r1i1p1f1", "Amon", "rsds", "gn"),
        index="west",
        collection="CMIP6",
        created_at_utc="2026-01-01T00:00:00Z",
        datasets=(
            {
                "id": identifier,
                "properties": {"cmip6:variable_units": "W m-2", "native_calendar": "360_day"},
                "links": [{"rel": "cite-as", "href": "https://example.test/dataset-citation"}],
            },
        ),
        requests=(),
        files=(
            CMIP6File(
                identifier,
                filename,
                "https://esgf-node.ornl.gov/thredds/fileServer/cmip6/" + filename,
                100,
                "a" * 64,
                "200001",
                "201412",
            ),
        ),
    )


def test_global_rank_and_limit_preserve_provider_identity_and_source_counts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tables = {
        "noaa": station_catalogue(
            "noaa", [("n-tie", 0, 0.2), ("n-far", 0, 1), ("n-invalid", np.nan, 0)]
        ),
        "aemet": station_catalogue("aemet", [("A1", 0, 0.1), ("A2", 0, 0.2)]),
    }
    original = tables["noaa"].frame.copy(deep=True)
    calls = install_catalogues(monkeypatch, tables)
    result = discovery.find_sources(0, 0, radius_km=100, limit=2, station_sources=("noaa", "aemet"))
    assert result.status == "complete"
    assert list(zip(result.stations["source"], result.stations["station_id"], strict=True)) == [
        ("aemet", "A1"),
        ("aemet", "A2"),
    ]
    assert result.stations["rank"].tolist() == [1, 2]
    assert result.stations["distance_km"].is_monotonic_increasing
    statistics = result.stations.attrs["spatial_search"]
    assert statistics["input_station_count"] == 5
    assert statistics["invalid_coordinate_count"] == 1
    assert statistics["within_radius_count"] == 3
    assert statistics["returned_station_count"] == 2
    assert statistics["truncated"] is True
    statuses = {row["source"]: row for row in result.source_status}
    assert statuses["noaa"]["search_status"] == "matches_found"
    assert statuses["noaa"]["returned_station_count"] == 0
    assert statuses["aemet"]["returned_station_count"] == 2
    assert statuses["aemet"]["product_supported_variables"] == ["temperature", "wind"]
    assert statuses["aemet"]["station_variable_availability_verified"] is False
    assert statuses["aemet"]["catalogue_metadata"] == tables["aemet"].frame.attrs
    assert [source for source, _, _ in calls] == ["noaa", "aemet"]
    pd.testing.assert_frame_equal(tables["noaa"].frame, original)
    records = result.as_dict()["stations"]
    assert isinstance(records, list)
    assert all(isinstance(row, dict) and row["observations_verified"] is False for row in records)


def test_partial_results_distinguish_missing_credentials_and_provider_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_catalogues(
        monkeypatch,
        {
            "noaa": station_catalogue("noaa", [("N1", 0, 0)]),
            "aemet": station_catalogue("aemet", [], status="credentials_required"),
            "dwd": station_catalogue("dwd", [], status="provider_error"),
        },
    )
    result = discovery.find_sources(0, 0, station_sources=("noaa", "aemet", "dwd"))
    assert result.status == "partial"
    assert result.stations["station_id"].tolist() == ["N1"]
    statuses = {row["source"]: row for row in result.source_status}
    assert statuses["aemet"]["status"] == "credentials_required"
    assert statuses["dwd"]["status"] == "provider_error"
    assert statuses["aemet"]["search_status"] == statuses["dwd"]["search_status"] == "unavailable"
    assert len(result.grids) == 8


def test_filtered_local_scope_remains_explicit_when_no_nearby_candidate_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scope: dict[str, JSONValue] = {
        "provider_catalogue_complete": False,
        "bbox_west_south_east_north": [10, 10, 12, 12],
        "country_code_filter": "DE",
        "observations_verified": False,
    }
    calls = install_catalogues(
        monkeypatch, {"noaa": station_catalogue("noaa", [("N1", 11, 11)], scope=scope)}
    )
    path = tmp_path / "filtered.parquet"
    result = discovery.find_sources(0, 0, station_sources=("noaa",), catalogues={"noaa": path})
    assert calls == [("noaa", None, path)]
    assert result.status == "complete"
    assert result.stations.empty
    assert result.source_status[0]["coverage_scope"] == scope
    assert result.source_status[0]["search_status"] == "no_matches_in_catalogue"
    assert result.as_dict()["source_status"] == result.source_status


@pytest.mark.parametrize(
    "options",
    [
        {"radius_km": 0},
        {"limit": 0},
        {"station_sources": "noaa"},
        {"station_sources": ("noaa", "noaa")},
        {"station_sources": ("unknown",)},
        {"station_sources": (), "catalogues": {"noaa": Path("local.parquet")}},
        {"catalogues": {"noaa": "local.parquet"}},
        {"probe_date": date(2025, 1, 1)},
        {"probe_date": datetime(2025, 1, 1)},
    ],
)
def test_invalid_options_are_rejected_before_any_provider_is_loaded(
    monkeypatch: pytest.MonkeyPatch, options: dict
) -> None:
    def unexpected(*args: object, **kwargs: object) -> None:
        pytest.fail("Invalid query reached provider loading")

    monkeypatch.setattr(discovery, "load_station_catalogue", unexpected)
    monkeypatch.setattr(discovery, "verify_open_meteo", unexpected)
    with pytest.raises(ValueError):
        discovery.find_sources(0, 0, **options)


def test_invalid_coordinates_are_rejected_before_any_provider_is_loaded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected(*args: object, **kwargs: object) -> None:
        pytest.fail("Invalid coordinates reached provider loading")

    monkeypatch.setattr(discovery, "load_station_catalogue", unexpected)
    with pytest.raises(ValueError, match="latitude"):
        discovery.find_sources(91, 0)


def test_numpy_query_scalars_are_normalized_before_station_and_grid_discovery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_catalogues(monkeypatch, {"noaa": station_catalogue("noaa", [("N1", 28.5, -16)])})
    coordinates: dict = {"latitude": np.float32(28.5), "longitude": np.int64(-16)}
    result = discovery.find_sources(**coordinates, station_sources=("noaa",))
    assert result.stations["station_id"].tolist() == ["N1"]
    assert result.stations.loc[0, "distance_km"] == 0
    assert type(result.query["latitude"]) is type(result.query["longitude"]) is float
    assert all(row["requested_latitude"] == 28.5 for row in result.grids)
    assert all(row["requested_longitude"] == -16.0 for row in result.grids)


def test_json_nulls_checksum_and_unsupported_retrieval_preserve_source_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    table = station_catalogue("bsrn", [("E13", 0, 0)])
    table.frame["elevation_m"] = np.nan
    table.frame["source:unknown_measurement"] = np.inf
    table.frame["source:native_label"] = "Estación ñ"
    table.frame["retrieval_supported"] = False
    install_catalogues(monkeypatch, {"bsrn": table})
    result = discovery.find_sources(0, 0, station_sources=("bsrn",))
    body = result.as_dict()
    serialized = json.dumps(body, allow_nan=False)
    assert "Infinity" not in serialized and "NaN" not in serialized
    rows = body["stations"]
    assert isinstance(rows, list) and isinstance(rows[0], dict)
    assert rows[0]["elevation_m"] is None
    assert rows[0]["source:unknown_measurement"] is None
    assert rows[0]["source:native_label"] == "Estación ñ"
    assert rows[0]["retrieval"] == []
    assert rows[0]["observations_verified"] is False
    fingerprint = body.pop("discovery_sha256")
    assert (
        fingerprint
        == hashlib.sha256(json.dumps(body, sort_keys=True, allow_nan=False).encode()).hexdigest()
    )
    assert result.as_dict()["discovery_sha256"] == fingerprint
    references = body["reference_ids"]
    assert isinstance(references, list) and references[0] == THESIS
    assert len(references) == len(set(references))


def test_new_snapshots_are_written_without_overwriting_files_or_dangling_symlinks(
    tmp_path: Path,
) -> None:
    result = discovery.find_sources(0, 0, station_sources=())
    path = tmp_path / "results" / "discovery.json"
    discovery.save_discovery(result, path)
    initial = path.read_bytes()
    assert json.loads(initial) == result.as_dict()
    with pytest.raises(ValueError, match="already exists"):
        discovery.save_discovery(result, path)
    assert path.read_bytes() == initial
    missing = tmp_path / "not-created.json"
    link = tmp_path / "linked.json"
    link.symlink_to(missing)
    with pytest.raises(ValueError, match="already exists"):
        discovery.save_discovery(result, link)
    assert not missing.exists()


def test_saved_cmip6_plan_replaces_generic_selection_without_asserting_point_coverage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected(*args: object, **kwargs: object) -> None:
        pytest.fail("Local grid discovery attempted provider access")

    monkeypatch.setattr(discovery, "load_station_catalogue", unexpected)
    monkeypatch.setattr(discovery, "verify_open_meteo", unexpected)
    plan = example_plan()
    result = discovery.find_sources(28.5, -16.5, station_sources=(), cmip6_plan=plan)
    candidates = [row for row in result.grids if row["source"] == "cmip6"]
    assert len(candidates) == 1
    row = candidates[0]
    assert row["dataset_id"] == plan.datasets[0]["id"]
    assert row["plan_sha256"] == plan.sha256
    assert row["availability_status"] == "catalogue_verified"
    assert row["geographic_status"] == "point_coverage_unverified"
    assert row["cell_latitude"] is row["cell_longitude"] is None
    assert row["provider_properties"] == plan.datasets[0]["properties"]
    assert row["provider_links"] == plan.datasets[0]["links"]
    assert result.query["network_enabled"] is False


def test_concurrent_snapshot_publication_cannot_overwrite_another_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "discovery.json"
    result = discovery.find_sources(0, 0, station_sources=())
    original_link = discovery.os.link

    def publish_competing_result(source: Path, destination: Path) -> None:
        destination.write_bytes(b"already published by another process")
        original_link(source, destination)

    monkeypatch.setattr(discovery.os, "link", publish_competing_result)
    with pytest.raises(ValueError, match="already exists"):
        discovery.save_discovery(result, path)
    assert path.read_bytes() == b"already published by another process"
    assert list(tmp_path.iterdir()) == [path]


def test_explicit_grid_probe_is_routed_once_and_failure_keeps_other_candidates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[HTTPClient, date]] = []

    def probe(
        http: HTTPClient, candidates: list[dict[str, JSONValue]], *, day: date
    ) -> list[dict[str, JSONValue]]:
        calls.append((http, day))
        assert len(candidates) == 8
        return [
            row | {"availability_status": "provider_error"}
            if row["dataset_id"] == "open_meteo_era5"
            else row
            for row in candidates
        ]

    monkeypatch.setattr(discovery, "verify_open_meteo", probe)
    with HTTPClient(discovery.DISCOVERY_HOSTS) as http:
        result = discovery.find_sources(
            0, 0, station_sources=(), probe_date=date(2025, 1, 1), http=http
        )
    assert calls == [(http, date(2025, 1, 1))]
    assert result.status == "partial"
    assert len(result.grids) == 8
    assert result.query["probe_date"] == "2025-01-01"
    assert result.query["network_enabled"] is True
