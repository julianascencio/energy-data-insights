"""Protect the offline connector inventory, geographic scope and source fixtures."""

import csv
import hashlib
import json
import math
import runpy
import socket
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit

import numpy as np
from shapely.geometry import Point

from energy_methods.country_boundaries import load_country_boundaries
from energy_methods.references import get_references

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "examples/connectors/data"
COUNTRY_HOSTS = {
    "adme": "URY",
    "cen": "CHL",
    "eia": "USA",
    "elexon": "GBR",
    "emi": "NZL",
    "eskom": "ZAF",
    "kpx": "KOR",
    "ons": "BRA",
    "ree": "ESP",
    "rte": "FRA",
    "smard": "DEU",
    "taipower": "TWN",
    "xm": "COL",
}
REGIONAL_HOSTS = {
    "aemo": "AUS",
    "aeso": "CAN",
    "caiso": "USA",
    "ieso": "CAN",
    "tepco": "JPN",
}
NETWORK_HOSTS = {
    "bsrn": "dataportals.pangaea.de",
    "dwd": "opendata.dwd.de",
    "noaa": "www.ncei.noaa.gov",
    "surfrad": "gml.noaa.gov",
}


def _json(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def _catalogue():
    return _json("generation_coverage_catalogue.json")


def _station_rows():
    with (DATA / "generation_coverage_stations.csv").open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def _assert_sha256(value):
    assert isinstance(value, str) and len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def _assert_request_provenance(request):
    assert urlsplit(request["endpoint"]).scheme == "https"
    assert isinstance(request["parameters"], dict)
    _assert_sha256(request["sha256"])
    assert request["size_bytes"] > 0
    acquired = datetime.fromisoformat(request["retrieved_at_utc"])
    assert acquired.utcoffset() == timedelta(0)


def test_catalogue_covers_every_source_once_with_existing_references():
    catalogue = _catalogue()
    assert catalogue["schema_version"] == 1
    date.fromisoformat(catalogue["as_of"])
    rows = catalogue["connectors"]
    ids = [row["id"] for row in rows]
    source_root = ROOT / "data-retrieval/src/energy_data_retrieval/sources"
    implemented = {path.name for path in source_root.iterdir() if (path / "__init__.py").is_file()}
    assert len(ids) == len(set(ids)) == 43
    assert set(ids) == implemented
    assert Counter(row["category"] for row in rows) == {
        "generation": 22,
        "grid": 14,
        "station_network": 5,
        "local_import": 1,
        "basemap": 1,
    }
    for row in rows:
        assert row["label"].strip() and row["scope"].strip()
        assert row["access"] in {"public", "credential", "export", "mixed", "local"}
        assert urlsplit(row["source_url"]).scheme == "https"
        assert len(row["references"]) == len(set(row["references"]))
        if row["id"] == "station":
            # User files have no external data provider to cite.
            assert row["references"] == []
            assert row["access"] == "local"
        else:
            assert row["references"]
            get_references(row["references"])


def test_generation_hosts_do_not_turn_regional_or_site_products_into_country_coverage():
    rows = {row["id"]: row for row in _catalogue()["connectors"]}
    generation = {id: row for id, row in rows.items() if row["category"] == "generation"}
    kinds = {
        kind: {id for id, row in generation.items() if row["coverage_kind"] == kind}
        for kind in ("country_system", "regional", "selected_areas", "research_site")
    }
    assert kinds == {
        "country_system": set(COUNTRY_HOSTS),
        "regional": set(REGIONAL_HOSTS),
        "selected_areas": {"entsoe"},
        "research_site": {"pvdaq", "nist", "dkasc"},
    }
    for id, country in (COUNTRY_HOSTS | REGIONAL_HOSTS).items():
        assert rows[id]["country_codes"] == [country]
    # A schematic European point and one contributed PV archive example cannot
    # justify a list of national polygons to fill.
    assert rows["entsoe"]["country_codes"] == []
    assert rows["pvdaq"]["country_codes"] == []
    assert rows["entsoe"]["access"] == "credential"
    assert rows["nist"]["access"] == rows["dkasc"]["access"] == "export"


def test_weather_scope_keeps_land_masks_model_selection_and_point_networks_distinct():
    rows = {row["id"]: row for row in _catalogue()["connectors"]}
    expected = {
        "global_grid": {"open_meteo", "earthmover_era5", "cds", "nasa_power"},
        "regional_grid": {"canary_clim", "global_solar_atlas"},
        "land_grid": {"gpcc", "cru_ts", "chelsa", "jrc_climate", "ml21", "pvcz", "pvgis"},
        "catalogue_grid": {"cmip6"},
        "global_network": {"noaa", "bsrn"},
        "country_network": {"aemet", "dwd", "surfrad"},
        "user_defined": {"station"},
        "global_basemap": {"natural_earth"},
    }
    observed = {
        kind: {id for id, row in rows.items() if row["coverage_kind"] == kind} for kind in expected
    }
    assert observed == expected
    assert rows["aemet"]["country_codes"] == ["ESP"]
    assert rows["dwd"]["country_codes"] == ["DEU"]
    assert rows["surfrad"]["country_codes"] == ["USA"]
    assert rows["aemet"]["access"] == rows["cds"]["access"] == "credential"
    for row in rows.values():
        if row["coverage_kind"] == "regional_grid":
            # Host geography must not turn the Canary Islands product or the
            # pinned Spain/Chile GHI archives into a global weather service.
            assert row["category"] == "grid"
            assert row["country_codes"] == (
                ["ESP", "CHL"] if row["id"] == "global_solar_atlas" else ["ESP"]
            )
            assert row["access"] == "public"
        elif row["category"] in {"grid", "local_import", "basemap"}:
            assert row["country_codes"] == []
        if row["category"] != "generation":
            # Global products and station networks are not represented by invented
            # generation-site coordinates.
            assert "locator" not in row


def test_generation_locators_are_geographic_and_have_explicit_meanings():
    rows = _catalogue()["connectors"]
    document = _json("generation_coverage_world.geojson")
    codes = {feature["properties"]["ADM0_A3"] for feature in document["features"]}
    countries = load_country_boundaries(DATA / "generation_coverage_world.geojson", sorted(codes))
    geometries = {country.code: country.geometry for country in countries.countries}
    site_meanings = {
        "pvdaq": "archive_example",
        "nist": "verified_site",
        "dkasc": "precinct_locator",
    }
    for row in rows:
        assert len(row["country_codes"]) == len(set(row["country_codes"]))
        assert set(row["country_codes"]) <= codes
        if row["category"] != "generation":
            continue
        locator = row["locator"]
        longitude, latitude = locator["longitude"], locator["latitude"]
        assert math.isfinite(longitude) and -180 <= longitude <= 180
        assert math.isfinite(latitude) and -90 <= latitude <= 90
        if row["id"] in site_meanings:
            assert locator["meaning"] == site_meanings[row["id"]]
            assert urlsplit(row["locator_source"]).scheme == "https"
        else:
            assert locator["meaning"] == "schematic_region"
        if row["coverage_kind"] == "country_system":
            # The approximate country label must remain inside its actual host
            # polygon; this does not turn that polygon into a grid-service area.
            assert geometries[row["country_codes"][0]].covers(Point(longitude, latitude))


def test_basemap_hash_and_provenance_account_for_every_retained_or_excluded_feature():
    manifest = _json("generation_coverage_provenance.json")
    content = (DATA / manifest["fixture"]).read_bytes()
    assert hashlib.sha256(content).hexdigest() == manifest["fixture_sha256"]
    assert len(content) == manifest["fixture_bytes"]
    document = json.loads(content)
    assert document["type"] == "FeatureCollection"
    metadata = document["metadata"]
    assert metadata["version"] == manifest["version"]
    assert metadata["coordinate_reference_system"] == manifest["coordinate_reference_system"]
    assert manifest["coordinate_reference_system"] == "EPSG:4326"
    assert metadata["boundary_policy"] == manifest["boundary_policy"]
    codes = [feature["properties"]["ADM0_A3"] for feature in document["features"]]
    assert len(codes) == len(set(codes)) == manifest["retained_feature_count"]
    excluded = manifest["excluded_features"]
    excluded_codes = {feature["ADM0_A3"] for feature in excluded}
    # Antarctica is the disclosed antimeridian exception. No other country's
    # disappearance can be concealed by updating only a fixture row count.
    assert excluded_codes == set(metadata["excluded_codes"]) == {"ATA"}
    assert excluded_codes.isdisjoint(codes)
    assert all(feature["reason"].strip() for feature in excluded)
    assert manifest["source_feature_count"] == len(codes) + len(excluded)
    assert manifest["retained_properties"]
    for feature in document["features"]:
        assert set(feature["properties"]) == set(manifest["retained_properties"])
    _assert_request_provenance(manifest["request"])
    assert urlsplit(manifest["request"]["endpoint"]).hostname == "naturalearth.s3.amazonaws.com"
    assert {Path(name).suffix for name in manifest["source_files_sha256"]} >= {
        ".shp",
        ".shx",
        ".dbf",
        ".prj",
    }
    for digest in manifest["source_files_sha256"].values():
        _assert_sha256(digest)
    get_references(manifest["reference_ids"])


def test_station_fixture_preserves_all_valid_provider_locations_without_sampling():
    manifest = _json("generation_coverage_stations_provenance.json")
    content = (DATA / manifest["fixture"]).read_bytes()
    assert hashlib.sha256(content).hexdigest() == manifest["fixture_sha256"]
    assert len(content) == manifest["fixture_bytes"]
    assert manifest["columns"] == ["provider", "station_id", "latitude", "longitude"]
    rows = _station_rows()
    assert len(rows) == manifest["fixture_rows"]
    keys = [(row["provider"], row["station_id"]) for row in rows]
    assert len(keys) == len(set(keys))
    assert all(row["station_id"].strip() for row in rows)
    assert manifest["sampling_applied"] is False
    assert manifest["date_country_or_bbox_filter_applied"] is False
    assert manifest["cross_provider_deduplication_applied"] is False
    for row in rows:
        longitude, latitude = float(row["longitude"]), float(row["latitude"])
        assert math.isfinite(longitude) and -180 <= longitude <= 180
        assert math.isfinite(latitude) and -90 <= latitude <= 90
    counts = Counter(row["provider"] for row in rows)
    catalogues = {item["provider"]: item for item in manifest["catalogues"]}
    assert len(catalogues) == len(manifest["catalogues"])
    assert set(catalogues) == set(counts) == set(NETWORK_HOSTS)
    for provider, item in catalogues.items():
        assert counts[provider] == item["valid_coordinate_count"]
        assert item["normalized_station_count"] == (
            item["valid_coordinate_count"] + item["invalid_coordinate_count"]
        )
        assert item["native_station_count"] == (
            item["normalized_station_count"] + item["identical_native_rows_coalesced"]
        )
        dropped = item["dropped_station_ids"]
        assert len(dropped) == len(set(dropped)) == item["invalid_coordinate_count"]
        provider_ids = {row["station_id"] for row in rows if row["provider"] == provider}
        assert provider_ids.isdisjoint(dropped)
        assert set(item["catalogue_only_station_ids"]) <= provider_ids
        _assert_request_provenance(item["request"])
        assert urlsplit(item["request"]["endpoint"]).hostname == NETWORK_HOSTS[provider]
        attributes = item["catalogue_attributes"]
        assert attributes.get("bbox_west_south_east_north") is None
        assert attributes.get("country_code_filter") is None
        assert attributes.get("availability_inferred", False) is False
        get_references(item["reference_ids"])
    assert set(manifest["reference_ids"]) == {
        reference for item in catalogues.values() for reference in item["reference_ids"]
    }
    get_references(manifest["reference_ids"])
    connector_rows = {row["id"]: row for row in _catalogue()["connectors"]}
    excluded = manifest["excluded_connector"]
    assert excluded["provider"] == "aemet" and excluded["reason"].strip()
    assert connector_rows[excluded["provider"]]["access"] == "credential"
    assert set(catalogues) | {excluded["provider"]} == {
        id for id, row in connector_rows.items() if row["category"] == "station_network"
    }


def test_gallery_runs_offline_and_plots_the_reviewed_hosts_and_every_station(monkeypatch):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PathCollection

    attempts = []

    def forbidden(*args, **kwargs):
        attempts.append((args, kwargs))
        raise AssertionError("The connector coverage gallery must run entirely offline")

    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(plt, "show", lambda: None)
    existing_figures = set(plt.get_fignums())
    try:
        result = runpy.run_path(str(ROOT / "examples/connectors/plot_generation_coverage.py"))
        assert not attempts
        assert len(result["catalogue"]["connectors"]) == 43
        assert result["generation_country_codes"] == set(COUNTRY_HOSTS.values())
        assert len(result["generation"]) == 22
        assert {row[0] for row in result["grid_labels"]} == {
            row["id"] for row in result["catalogue"]["connectors"] if row["category"] == "grid"
        }
        rows = _station_rows()
        assert len(result["stations"]) == len(rows)
        assert set(
            zip(result["stations"]["provider"], result["stations"]["station_id"], strict=True)
        ) == {(row["provider"], row["station_id"]) for row in rows}
        # Inspect the plotted points, not just the dataframe: this catches
        # plotting-time sampling, omitted networks and swapped coordinates.
        observed = {provider: [] for provider in NETWORK_HOSTS}
        for axis in result["fig_weather"].axes:
            for collection in axis.collections:
                if isinstance(collection, PathCollection) and collection.get_label() in observed:
                    offsets = np.asarray(collection.get_offsets())
                    assert np.isfinite(offsets).all()
                    observed[collection.get_label()].extend(map(tuple, offsets))
        for provider, points in observed.items():
            expected = [
                (float(row["longitude"]), float(row["latitude"]))
                for row in rows
                if row["provider"] == provider
            ]
            assert len(points) == len(expected) > 0
            np.testing.assert_allclose(sorted(points), sorted(expected), rtol=0, atol=1e-9)
        assert result["fig_generation"] is not result["fig_weather"]
    finally:
        for number in set(plt.get_fignums()) - existing_figures:
            plt.close(number)
