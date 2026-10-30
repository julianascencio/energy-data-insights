"""Mainland topology, real source-grid alignment and missing-input preservation."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import rasterio
from rasterio.transform import from_origin
from rasterio.windows import from_bounds
from shapely.geometry import MultiPolygon, Polygon, box

from energy_analysis.chile_kgpv import pipeline
from energy_methods.country_boundaries import (
    CountryBoundary,
    CountrySelection,
    write_country_boundaries,
)
from energy_methods.kgpv import classify_kgpv

FIXTURES = Path(__file__).resolve().parents[2] / "examples/analysis"


@pytest.fixture
def tiny_sources(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    (raw / "climate").mkdir(parents=True)
    mainland = Polygon(
        [(-70, -30), (-69.6, -30), (-69.6, -30.1), (-70, -30.1)],
        [[(-69.9, -30.01), (-69.88, -30.01), (-69.88, -30.03), (-69.9, -30.03)]],
    )
    country = MultiPolygon([mainland, box(-70.1, -30.1, -70.08, -30.08)])
    boundary = raw / "boundaries/ne_10m_admin_0_countries.shp"
    write_country_boundaries(
        CountrySelection((CountryBoundary("CHL", "Chile", country),)), boundary
    )
    for variable in ("tas", "pr"):
        for month in range(1, 13):
            data = np.full((12, 48), 2932 if variable == "tas" else 0, dtype="uint16")
            if variable == "pr" and month == 7:
                data[4, 4] = 65535
            with rasterio.open(
                pipeline.climate_path(raw, variable, month),
                "w",
                driver="GTiff",
                width=48,
                height=12,
                count=1,
                dtype="uint16",
                nodata=65535,
                crs="EPSG:4326",
                transform=from_origin(-70, -30, 1 / 120, 1 / 120),
            ) as target:
                target.write(data, 1)
                target.scales = (0.1,)
                target.update_tags(
                    variable=variable,
                    variable_unit="K" if variable == "tas" else "kg m-2 month-1",
                    version="2.1",
                    datetime="1981-2010",
                )
    # Solar stops halfway south. No GHI may be extrapolated into the other half.
    data = np.full((20, 160), 1800, dtype="float32")
    data[:, 80:] = 2300
    with rasterio.open(
        raw / "GHI.tif",
        "w",
        driver="GTiff",
        count=1,
        width=160,
        height=20,
        dtype="float32",
        nodata=-9999,
        crs="EPSG:4326",
        transform=from_origin(-70, -30, 0.0025, 0.0025),
    ) as target:
        target.write(data, 1)
    monkeypatch.setattr(
        pipeline, "SAMPLE_SITES", {"Covered": (-69.95, -30.01), "Missing": (-69.95, -30.08)}
    )
    return raw, mainland


def test_mainland_holes_native_solar_edges_missing_month_and_south(tiny_sources, tmp_path):
    raw, expected_geometry = tiny_sources
    selection = pipeline.mainland_boundary(raw / "boundaries/ne_10m_admin_0_countries.shp")
    assert selection.geometry.equals(expected_geometry)
    maps = []
    for tile_size in (128, 256):
        out = tmp_path / str(tile_size)
        record = pipeline.prepare_map(raw, out, tile_size=tile_size)
        with rasterio.open(out / record["file"]) as source:
            assert source.transform == from_origin(-70, -30, 0.0025, 0.0025)
            maps.append(source.read())
            assert next(source.sample([(-69.89, -30.02)])).tolist() == [0, 0, 0]  # hole
            assert next(source.sample([(-69.963, -30.037)])).tolist() == [0, 1, 0]  # July missing
            assert next(source.sample([(-69.95, -30.08)])).tolist() == [0, 1, 0]  # south of GHI
            assert next(source.sample([(-69.80125, -30.01125)])).tolist() == [3, 1, 1]
            assert next(source.sample([(-69.79875, -30.01125)])).tolist() == [4, 1, 1]
        assert record["missing_mainland_pixels"] > 0
    np.testing.assert_array_equal(*maps)
    assert np.all(maps[0][2] == (maps[0][0] > 0))


def test_bad_climate_grid_or_units_rejected(tiny_sources, tmp_path):
    raw, _ = tiny_sources
    with rasterio.open(pipeline.climate_path(raw, "tas", 3), "r+") as source:
        source.update_tags(variable_unit="degC")
    with pytest.raises(ValueError, match="metadata"):
        pipeline.prepare_map(raw, tmp_path / "out")


def test_reviewed_chile_map_sources_and_samples():
    manifest = json.loads((FIXTURES / "kgpv_chile_provenance.json").read_text())
    record = manifest["map"]
    assert len(manifest["climate_subsets"]) == 24
    assert manifest["solar_grid"]["valid_pixel_center_latitude_range"][0] == pytest.approx(
        -44.99875
    )
    for name, checksum in record["contour_files_sha256"].items():
        assert pipeline.file_sha256(FIXTURES / name) == checksum
    assert manifest["climate_period"] != manifest["solar_period"]
    for key, checksum in [
        ("file", "sha256"),
        ("boundary_file", "boundary_sha256"),
        ("sample_file", "sample_sha256"),
    ]:
        assert pipeline.file_sha256(FIXTURES / record[key]) == record[checksum]
    samples = pd.read_csv(FIXTURES / record["sample_file"])
    expected = classify_kgpv(
        samples[[f"tas_{m:02d}" for m in range(1, 13)]],
        samples[[f"pr_{m:02d}" for m in range(1, 13)]],
        samples.annual_ghi_kwh_m2,
        samples.latitude,
    )
    np.testing.assert_array_equal(expected.class_id, samples.class_id)
    with rasterio.open(FIXTURES / record["file"]) as source:
        assert source.count == 3
        assert source.transform.a == pytest.approx(0.0025)
        for row in samples.itertuples():
            assert next(source.sample([(row.longitude, row.latitude)])).tolist() == [
                row.class_id,
                1,
                int(bool(row.class_id)),
            ]
        # Every mainland pixel south of the source edge is retained but unclassified.
        window = from_bounds(-75.7, -53.88, -67.02, -45.01, source.transform)
        data = source.read(window=window)
        assert data[1].any() and not data[0].any() and not data[2].any()
