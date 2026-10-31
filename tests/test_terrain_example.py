"""Real captured terrain samples retain attribution, exact grids and offline execution."""

import hashlib
import json
import runpy
import socket
from pathlib import Path

import numpy as np
import pytest

from energy_data_retrieval.terrain import TerrainSource, describe_terrain, read_terrain
from energy_methods.references import get_references

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "examples/connectors/data"


def test_real_terrain_crops_hashes_datums_resolution_and_validity():
    manifest = json.loads((DATA / "terrain_provenance.json").read_text())
    assert len(manifest["samples"]) == 4
    expected = {
        "srtm": ("EGM96", "degree", 1 / 3600),
        "copernicus_dem": ("EGM2008", "degree", 1 / 3600),
        "ign_terrain": (
            "Spanish official orthometric heights; mainland/island height reference varies",
            "metre",
            5,
        ),
        "usgs_3dep": ("NAVD88 in CONUS; verify project metadata elsewhere", "metre", 1),
    }
    for row in manifest["samples"]:
        path = DATA / row["fixture"]
        content = path.read_bytes()
        assert hashlib.sha256(content).hexdigest() == row["fixture_sha256"]
        assert len(content) == row["fixture_bytes"] < 2_000_000
        source = TerrainSource(**row["source"])
        info = describe_terrain(path, source)
        datum, unit, spacing = expected[source.id]
        assert source.vertical_datum == datum and info.horizontal_unit == unit
        assert info.pixel_spacing == pytest.approx((spacing, spacing))
        assert list(info.shape) == row["fixture_shape"]
        assert info.pixel_spacing == pytest.approx(row["original_raster"]["pixel_spacing"])
        assert info.crs == row["original_raster"]["crs"]
        w = read_terrain(path, source)
        assert np.isfinite(w.elevation_m).mean() == row["valid_fraction"] > 0
        assert row["request"]["endpoint"].startswith("https://")
        assert len(row["request"]["sha256"]) == 64
        get_references(source.reference_ids)
        if source.id == "copernicus_dem":
            assert "all rights reserved" in row["extra"]["attribution"]
        if source.id == "usgs_3dep":
            assert row["extra"]["product"]["source_id"] == "69c20ed7b66b01d6ebf33c9a"


def test_terrain_map_and_site_lookup_run_without_network(monkeypatch):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    def forbidden(*args, **kwargs):
        raise AssertionError("Terrain gallery must be offline")

    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(plt, "show", lambda: None)
    try:
        result = runpy.run_path(str(ROOT / "examples/connectors/plot_terrain_sources.py"))
        assert len(result["windows"]) == 4
        assert len(result["site_record"]["terrain"]) == 3
        assert all(row["elevation_m"] > 0 for row in result["site_record"]["terrain"])
        for ax, w in zip(result["axes"].flat, result["windows"], strict=True):
            np.testing.assert_array_equal(ax.images[0].get_array().filled(np.nan), w.elevation_m)
            assert ax.images[0].get_interpolation() == "none"
    finally:
        plt.close("all")
