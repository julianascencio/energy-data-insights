"""Check the real Icor site association, source fidelity and offline imagery workflow."""

import hashlib
import importlib.util
import json
import runpy
import socket
import sys
from pathlib import Path

import numpy as np
import pytest
from pyproj import Geod
from shapely.geometry import Polygon, shape

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "examples/connectors/data"


def test_official_site_matches_one_mapped_plant_and_retains_provider_capacity():
    site = json.loads((DATA / "candelaria_site.json").read_text())
    raw = (DATA / site["catalogue_fixture"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == site["catalogue_request"]["sha256"]
    assert len(raw) == site["catalogue_request"]["size_bytes"]
    official = site["official_site"]
    assert official in json.loads(raw)["features"]
    assert official["properties"]["instalacion_nombre"] == "Planta Icor"
    assert official["properties"]["instalacion_potencia"] == 2000
    assert official["properties"]["instalacion_unidad_potencia"] == "kW"
    point = shape(official["geometry"])
    assert point.x == official["properties"]["instalacion_longitud"]
    assert point.y == official["properties"]["instalacion_latitud"]
    osm = json.loads((DATA / "candelaria_osm.json").read_text())
    matches = []
    for feature in osm["elements"]:
        tags = feature.get("tags", {})
        if tags.get("power") == "plant" and tags.get("plant:method") == "photovoltaic":
            boundary = Polygon([(p["lon"], p["lat"]) for p in feature["geometry"]])
            if boundary.covers(point):
                matches.append(feature["id"])
                assert boundary.equals_exact(shape(site["footprint"]["geometry"]), 0)
    assert matches == [430266023]
    assert site["footprint"]["properties"]["osm_id"] == matches[0]
    distance = Geod(ellps="WGS84").inv(*site["candelaria_reference_lonlat"], point.x, point.y)[2]
    assert distance / 1000 == pytest.approx(site["distance_km"])
    assert 19.1 < distance / 1000 < 19.3
    island = (DATA / "candelaria_tenerife.geojson").read_bytes()
    assert hashlib.sha256(island).hexdigest() == site["locator_fixture_sha256"]
    assert shape(json.loads(island)["geometry"]).covers(point)


def test_captures_keep_hashes_queries_dates_and_aerial_unknowns():
    site = json.loads((DATA / "candelaria_site.json").read_text())
    for path in DATA.glob("candelaria_*.meta.json"):
        metadata = json.loads(path.read_text())
        captured = path.with_name(path.name.removesuffix(".meta.json"))
        assert hashlib.sha256(captured.read_bytes()).hexdigest() == metadata["sha256"]
    aerial = json.loads((DATA / "candelaria_pnoa.png.meta.json").read_text())
    assert aerial["bbox_wgs84"] == site["farm_bounds_wgs84"]
    assert aerial["product_kind"] == "rendered_display"
    assert aerial["native_resolution_m"] is None
    assert aerial["acquisition_date"].startswith("mixed_or_unknown")
    assert aerial["not_calibrated_reflectance"]
    assert aerial["request"]["SRS"] == "EPSG:4326"
    assert aerial["request"]["VERSION"] == "1.1.1"  # This version uses lon,lat.
    assert aerial["request"]["LAYERS"] == "OI.OrthoimageCoverage"


@pytest.mark.skipif(
    sys.version_info < (3, 13) or importlib.util.find_spec("orbitalpv") is None,
    reason="Native image loading requires Python 3.13 and the optional imagery group",
)
def test_farm_gallery_runs_offline_with_native_grids_and_local_quality(monkeypatch):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    def forbidden(*args, **kwargs):
        raise AssertionError("The farm gallery must run entirely offline")

    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(plt, "show", lambda: None)
    try:
        result = runpy.run_path(str(ROOT / "examples/connectors/plot_candelaria_solar_farm.py"))
        for name, spacing in (("visual", 10), ("red", 10), ("scl", 20)):
            image = result[name]
            assert image.crs == "EPSG:32628"
            assert image.transform[0] == spacing and image.transform[4] == -spacing
            assert image.data.count() > 0
            assert image.item_metadata["id"] == "S2A_T28RCS_20260804T115232_L2A"
        # The independent area check catches swapped CRS coordinates or a full-scene mask.
        assert 0.8 < result["outline"].area / 10_000 < 1.2
        assert 20 <= int(result["valid"].sum()) <= 30
        assert result["class_counts"] == {5: 25}
        red = result["red"]
        np.testing.assert_allclose(red.reflectance(), red.data * 0.0001 - 0.1)
        assert len(result["fig_location"].axes) == 3
        assert len(result["fig_quality"].axes) == 4  # Two maps and their colour bars.
    finally:
        plt.close("all")
