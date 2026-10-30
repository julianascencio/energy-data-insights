"""Native-pixel, nodata and solar-support contracts, using tiny offline rasters."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
import rasterio
from rasterio.transform import from_origin
from rasterio.windows import Window

from energy_analysis.canary_kgpv import pipeline
from energy_analysis.canary_kgpv.plotting import plot_tile
from energy_methods.kgpv import classify_kgpv

FIXTURES = Path(__file__).resolve().parents[2] / "examples" / "analysis"


@pytest.fixture
def tiny_sources(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    raw.mkdir()
    # 300 native columns span two 250 m solar cells; processing crosses tile edges.
    transform = from_origin(-16, 28, 0.005 / 300, 0.005 / 300)
    for variable in ("tas", "pr"):
        for month in range(1, 13):
            data = np.full((150, 300), 2932 if variable == "tas" else 0, dtype="uint16")
            data[:, 0] = 65535  # ocean in every input
            if variable == "pr" and month == 7:
                data[20, 50] = 65535  # missing month, with a retained land footprint
            with rasterio.open(
                pipeline.climate_path(raw, variable, month),
                "w",
                driver="GTiff",
                width=300,
                height=150,
                count=1,
                dtype="uint16",
                nodata=65535,
                crs="EPSG:4326",
                transform=transform,
            ) as target:
                target.write(data, 1)
                target.scales = (0.1,)
                target.update_tags(
                    variable=variable,
                    variable_unit="K" if variable == "tas" else "kg m-2 month-1",
                    version="1.0",
                    datetime=f"15-{month:02d}-1996",
                )
    with rasterio.open(
        raw / "GHI.tif",
        "w",
        driver="GTiff",
        width=2,
        height=1,
        count=1,
        dtype="float32",
        nodata=-9999,
        crs="EPSG:4326",
        transform=from_origin(-16, 28, 0.0025, 0.0025),
    ) as target:
        target.write(np.array([[1800, 2300]], dtype="float32"), 1)
    monkeypatch.setattr(pipeline, "ISLANDS", {"test": ("Test", (-16, 27.9975, -15.995, 28))})
    monkeypatch.setattr(pipeline, "SAMPLE_SITES", {"Test": (-15.999, 27.999)})
    return raw, transform


def test_native_pixels_nearest_solar_nodata_and_tile_invariance(tiny_sources, tmp_path):
    raw, transform = tiny_sources
    outputs = []
    for size in (128, 256):
        output = tmp_path / str(size)
        records = pipeline.prepare_maps(raw, output, islands=("test",), tile_size=size)
        with rasterio.open(output / records["test"]["file"]) as result:
            assert result.transform == transform
            outputs.append(result.read())
        assert records["test"]["missing_land_pixels"] == 1
    np.testing.assert_array_equal(*outputs)
    classes, land = outputs[0]
    assert not land[:, 0].any() and not classes[:, 0].any()
    assert land[20, 50] == 1 and classes[20, 50] == 0
    # A desert cell switches BH -> BK exactly at the solar source-cell edge.
    assert classes[40, 149] == 3 and classes[40, 150] == 4
    assert np.all(classes[:, 151:300] == 4)
    with rasterio.open(pipeline.climate_path(raw, "tas", 1)) as source:
        decoded = pipeline.decode_climate(np.array([2932, 65535]), source, "tas")
    assert decoded[0] == pytest.approx(20.05) and np.isnan(decoded[1])


@pytest.mark.parametrize("change", ["units", "month", "grid"])
def test_rejects_inconsistent_climate_metadata(tiny_sources, tmp_path, change):
    raw, _ = tiny_sources
    with rasterio.open(pipeline.climate_path(raw, "tas", 12), "r+") as source:
        if change == "units":
            source.update_tags(variable_unit="degC")
        elif change == "month":
            source.update_tags(datetime="15-11-1996")
        else:
            source.transform = from_origin(-16, 28, 0.01, 0.01)
    with pytest.raises(ValueError, match="metadata"):
        pipeline.prepare_maps(raw, tmp_path / "out", islands=("test",))


def test_missing_solar_is_not_extrapolated(tiny_sources, tmp_path):
    raw, _ = tiny_sources
    with rasterio.open(raw / "GHI.tif", "r+") as source:
        source.write(np.array([[1800, -9999]], dtype="float32"), 1)
    pipeline.prepare_maps(raw, tmp_path / "out", islands=("test",))
    with rasterio.open(tmp_path / "out/kgpv_canary_test.tif") as result:
        data = result.read()
    assert np.all(data[0, :, 151:300] == 0) and np.all(data[1, :, 151:300] == 1)


def test_reviewed_fixture_integrity_native_grid_and_sample_classes():
    manifest = json.loads((FIXTURES / "kgpv_canary_provenance.json").read_text())
    assert len(manifest["sources"]) == 25
    assert manifest["climate_baseline"] != manifest["solar_baseline"]
    samples = pd.read_csv(FIXTURES / manifest["sample_file"])
    assert pipeline.file_sha256(FIXTURES / manifest["sample_file"]) == manifest["sample_sha256"]
    expected = classify_kgpv(
        samples[[f"t{m:02d}" for m in range(1, 13)]].to_numpy(),
        samples[[f"p{m:02d}" for m in range(1, 13)]].to_numpy(),
        samples.annual_ghi.to_numpy(),
        samples.lat.to_numpy(),
    )
    np.testing.assert_array_equal(expected.class_id, samples.kgpv_class)
    matched = 0
    for record in manifest["islands"].values():
        path = FIXTURES / record["file"]
        assert pipeline.file_sha256(path) == record["sha256"]
        with rasterio.open(path) as source:
            assert source.count == 2 and source.crs == rasterio.crs.CRS.from_epsg(4326)
            assert list(source.shape) == record["shape"]
            assert list(source.transform) == record["transform"]
            assert source.transform.a == pytest.approx(0.00004684877106756975)
            assert source.tags()["solar_period"] == "1994-2018"
            for site in samples.itertuples():
                if (
                    source.bounds.left < site.lon < source.bounds.right
                    and source.bounds.bottom < site.lat < source.bounds.top
                ):
                    actual = next(source.sample([(site.lon, site.lat)]))
                    assert actual.tolist() == [site.kgpv_class, 1]
                    matched += 1
    assert matched == len(samples)


def test_display_read_is_bounded_and_zoom_keeps_native_cells():
    path = FIXTURES / "kgpv_canary_tenerife.tif"
    fig, ax = plt.subplots()
    try:
        image = plot_tile(path, ax, maximum_display_pixels=20_000)
        array = image.get_array()
        assert array is not None and array.size <= 20_000
        with rasterio.open(path) as source:
            west, north = source.xy(5000, 5000, offset="ul")
            east, south = source.xy(5010, 5010, offset="ul")
            expected = source.read(1, window=Window.from_slices((5000, 5010), (5000, 5010)))
        image = plot_tile(path, ax, bounds=(west, south, east, north))
        array = image.get_array()
        assert array is not None and array.shape == expected.shape
        with pytest.raises(ValueError, match="bounds"):
            plot_tile(path, ax, bounds=(1, 0, -1, 2))
    finally:
        plt.close(fig)
