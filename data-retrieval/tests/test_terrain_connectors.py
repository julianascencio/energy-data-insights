"""Synthetic wire fixtures protect real terrain grids, masks and download bounds."""

from __future__ import annotations

import io
import json
from dataclasses import asdict, replace
from zipfile import ZIP_DEFLATED, ZipFile

import httpx
import numpy as np
import pytest
import rasterio
from rasterio.io import MemoryFile
from rasterio.transform import from_origin

from energy_data_retrieval.sources.copernicus_dem import (
    COPERNICUS_DEM_HOSTS,
    CopernicusDEMClient,
)
from energy_data_retrieval.sources.copernicus_dem import tile_name as cop_tile
from energy_data_retrieval.sources.ign_terrain import IGN_TERRAIN_HOSTS, IGNTerrainClient
from energy_data_retrieval.sources.srtm import SRTM_HOSTS, SRTM_SOURCE, SRTMClient, tile_name
from energy_data_retrieval.sources.usgs_3dep import USGS_3DEP_HOSTS, USGS3DEPClient
from energy_data_retrieval.terrain import (
    degree_tiles,
    describe_terrain,
    read_terrain,
    write_terrain_window,
)
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, RetrievalError


def http(hosts, handler, **config):
    return HTTPClient(
        hosts,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(minimum_interval_seconds=0, attempts=1, **config),
    )


def tiff(values, *, crs="EPSG:4326", affine=None, nodata=-9999, scale=1, offset=0):
    with MemoryFile() as mem:
        with mem.open(
            driver="GTiff",
            count=1,
            height=values.shape[0],
            width=values.shape[1],
            dtype=values.dtype,
            crs=crs,
            nodata=nodata,
            compress="deflate",
            transform=affine or from_origin(-17, 29, 0.01, 0.01),
        ) as d:
            d.write(values, 1)
            d.scales = [scale]
            d.offsets = [offset]
        return mem.read()


@pytest.mark.parametrize(
    ("lat", "lon", "expected"),
    [
        (28.4, -16.3, "N28W017"),
        (-34.4, -70.8, "S35W071"),
        (0, 0, "N00E000"),
        (-56, -180, "S56W180"),
        (59.99, 179.99, "N59E179"),
    ],
)
def test_srtm_floor_and_geographic_edges(lat, lon, expected):
    assert tile_name(lat, lon) == expected


@pytest.mark.parametrize(("lat", "lon"), [(60, 0), (-56.01, 0), (0, 180), (np.nan, 0), (0, True)])
def test_srtm_rejects_uncovered_coordinates(lat, lon):
    with pytest.raises(ValueError):
        tile_name(lat, lon)


def test_degree_tiles_no_duplicate_at_integer_edge_and_no_antimeridian_guess():
    assert degree_tiles((-17, 28, -16, 29)) == ((28, -17),)
    assert degree_tiles((-17.01, 28, -16, 29)) == ((28, -18), (28, -17))
    for bounds in [(179, 0, -179, 1), (-180, -90, 180, 90), (0, 0, 0, 1)]:
        with pytest.raises(ValueError):
            degree_tiles(bounds)
    assert "S35_00_W071_00" in cop_tile(-34.4, -70.8)
    assert "COG_10_" in cop_tile(80, 0)


def archive(name, values):
    buf = io.BytesIO()
    with ZipFile(buf, "w", ZIP_DEFLATED) as z:
        z.writestr(name, values)
    return buf.getvalue()


def test_srtm_posts_voids_negative_heights_and_archive_provenance(tmp_path):
    values = np.zeros((3601, 3601), dtype=">i2")
    values[0, :3] = [-32768, -12, 5]
    body = archive("N28W017.hgt", values.tobytes())
    seen = []

    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(200, content=body)

    with http(SRTM_HOSTS, handler) as client:
        path, record = SRTMClient(client).download_tile(tmp_path, latitude=28.2, longitude=-16.2)
        # A second request reuses only the verified archive, regenerating the TIFF.
        again, reused = SRTMClient(client).download_tile(tmp_path, latitude=28.2, longitude=-16.2)
    assert again == path and reused.cache_hit and len(seen) == 1
    assert seen[0].endswith("N28W017.SRTMGL1.hgt.zip")
    with rasterio.open(path) as d:
        assert d.xy(0, 0) == pytest.approx((-17, 29))
        assert d.xy(3600, 3600) == pytest.approx((-16, 28))
        assert d.tags()["source_sha256"] == record.sha256
        assert d.read(1, masked=True)[0, 0] is np.ma.masked
        assert d.read(1)[0, 1] == -12
    info = describe_terrain(path, SRTM_SOURCE)
    assert info.pixel_spacing == pytest.approx((1 / 3600, 1 / 3600))
    assert info.source.vertical_datum == "EGM96" and info.shape == (3601, 3601)
    with pytest.raises(ValueError, match="maximum_pixels"):
        read_terrain(path, SRTM_SOURCE)


@pytest.mark.parametrize(
    ("name", "size"), [("../N28W017.hgt", 3601), ("N28W017.hgt", 1201), ("N28W018.hgt", 3601)]
)
def test_srtm_rejects_wrong_tile_traversal_or_coarse_grid(tmp_path, name, size):
    body = archive(name, bytes(size * size * 2))
    with (
        http(SRTM_HOSTS, lambda _: httpx.Response(200, content=body)) as client,
        pytest.raises(ValueError, match="SRTMGL1"),
    ):
        SRTMClient(client).download_tile(tmp_path, latitude=28, longitude=-17)
    assert not list(tmp_path.glob("*.tif"))


def test_copernicus_native_high_latitude_spacing_and_no_zero_mask(tmp_path):
    body = tiff(
        np.zeros((3600, 360), dtype="float32"),
        affine=from_origin(-5 / 3600, 86 + 0.5 / 3600, 10 / 3600, 1 / 3600),
        nodata=None,
    )
    with http(COPERNICUS_DEM_HOSTS, lambda _: httpx.Response(200, content=body)) as client:
        path, _ = CopernicusDEMClient(client).download_tile(tmp_path, latitude=85, longitude=0)
    with rasterio.open(path) as d:
        assert d.res == pytest.approx((10 / 3600, 1 / 3600))
        assert not np.ma.getmaskarray(d.read(1, masked=True)).any()


def test_missing_copernicus_tile_never_falls_back(tmp_path):
    calls = []

    def handler(r):
        calls.append(r)
        return httpx.Response(404)

    with http(COPERNICUS_DEM_HOSTS, handler) as client, pytest.raises(RetrievalError, match="404"):
        CopernicusDEMClient(client).download_tile(tmp_path, latitude=28, longitude=-17)
    assert len(calls) == 1 and not list(tmp_path.glob("*.tif"))


def test_read_decode_native_crop_and_round_trip(tmp_path):
    path = tmp_path / "input.tif"
    values = np.array([[0, -9999, -20], [10, 20, 30], [40, 50, 60]], dtype="int16")
    path.write_bytes(tiff(values, scale=0.5, offset=2))
    w = read_terrain(path, SRTM_SOURCE)
    assert w.elevation_m[0, 0] == 2 and w.elevation_m[0, 2] == -8
    assert np.isnan(w.elevation_m[0, 1])
    assert w.sample(28.995, -16.995) == 2 and w.sample(28.995, -16.985) is None
    with pytest.raises(ValueError, match="outside"):
        w.sample(28, -16)
    crop = read_terrain(path, SRTM_SOURCE, bounds_wgs84=(-16.999, 28.981, -16.981, 28.999))
    assert crop.elevation_m.shape == (2, 2) and crop.transform == w.transform
    with pytest.raises(ValueError, match="outside"):
        read_terrain(path, SRTM_SOURCE, bounds_wgs84=(-18, 28, -16, 30))
    out = write_terrain_window(crop, tmp_path / "crop.tif")
    reread = read_terrain(out, SRTM_SOURCE)
    np.testing.assert_array_equal(reread.elevation_m, crop.elevation_m)
    assert reread.metadata.pixel_spacing == (0.01, 0.01)
    assert describe_terrain(path, SRTM_SOURCE).nodata == -9999
    assert describe_terrain(out, SRTM_SOURCE).nodata == "NaN"
    json.dumps(asdict(reread.metadata), allow_nan=False)


def description():
    return """<wcs:CoverageDescriptions xmlns:wcs="http://www.opengis.net/wcs/2.0"
    xmlns:gml="http://www.opengis.net/gml/3.2"><wcs:CoverageDescription>
    <wcs:CoverageId>Elevacion4083_5</wcs:CoverageId>
    <gml:Envelope srsName="http://www.opengis.net/def/crs/EPSG/0/4083" axisLabels="x y">
    <gml:lowerCorner>188197.5 3060497.5</gml:lowerCorner>
    <gml:upperCorner>662002.5 3255102.5</gml:upperCorner></gml:Envelope>
    <gml:origin><gml:Point><gml:pos>188200 3255100</gml:pos></gml:Point></gml:origin>
    <gml:offsetVector>5 0</gml:offsetVector><gml:offsetVector>0 -5</gml:offsetVector>
    </wcs:CoverageDescription></wcs:CoverageDescriptions>"""


def test_ign_repeated_subsets_native_alignment_and_saved_metadata(tmp_path):
    seen = []

    def handler(r):
        seen.append(r)
        if r.url.params["REQUEST"] == "DescribeCoverage":
            return httpx.Response(200, text=description())
        assert "SCALESIZE" not in r.url.params and "OUTPUTCRS" not in r.url.params
        subset = r.url.params.get_list("SUBSET")
        (west, east), (south, north) = [tuple(map(float, v[2:-1].split(","))) for v in subset]
        assert (west - 188197.5) % 5 == 0 and (north - 3255102.5) % 5 == 0
        data = tiff(
            np.ones((round((north - south) / 5), round((east - west) / 5)), dtype="int16"),
            crs="EPSG:4083",
            affine=from_origin(west, north, 5, 5),
        )
        return httpx.Response(200, content=data)

    with http(IGN_TERRAIN_HOSTS, handler) as client:
        path, record = IGNTerrainClient(client).download_window(
            tmp_path, (-16.651, 28.249, -16.649, 28.251)
        )
    assert len(seen) == 2
    manifest = json.loads(path.with_suffix(".provenance.json").read_text())
    assert manifest["request"]["sha256"] == record.sha256
    assert "query:SUBSET" in record.parameters
    with rasterio.open(path) as d:
        assert d.res == (5, 5)


@pytest.mark.parametrize("mode", ["oversized", "changed", "exception"])
def test_ign_rejects_invalid_request_or_response(tmp_path, mode):
    calls = []

    def handler(r):
        calls.append(r)
        if r.url.params["REQUEST"] == "DescribeCoverage":
            text = description().replace("5 0", "25 0") if mode == "changed" else description()
            return httpx.Response(200, text=text)
        return httpx.Response(200, text="<ExceptionReport/>")

    with http(IGN_TERRAIN_HOSTS, handler) as client, pytest.raises((ValueError, RetrievalError)):
        IGNTerrainClient(client).download_window(
            tmp_path,
            (-16.66, 28.24, -16.64, 28.26),
            maximum_pixels=1 if mode == "oversized" else 4_000_000,
        )
    assert len(calls) == (2 if mode == "exception" else 1)
    assert not list(tmp_path.glob("*.tif"))


def product(i):
    return {
        "sourceId": str(i),
        "title": f"Tile {i}",
        "sizeInBytes": 100,
        "downloadURL": f"https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/a{i}.tif",
        "publicationDate": "2020-01-01",
        "body": "Synthetic metadata",
    }


def test_usgs_pagination_retains_projects_without_guessing_newest():
    def handler(r):
        offset = int(r.url.params["offset"])
        assert r.url.params["datasets"].endswith("1 meter")
        return httpx.Response(200, json={"total": 2, "items": [product(offset)], "errors": []})

    with http(USGS_3DEP_HOSTS, handler) as client:
        result = USGS3DEPClient(client).search((-105.35, 39.99, -105.34, 40), page_size=1)
    assert result.total == 2 and len(result.requests) == 2
    assert result.products[1].metadata["publicationDate"] == "2020-01-01"


@pytest.mark.parametrize("mode", ["duplicate", "changed", "missing", "limit", "unsafe"])
def test_usgs_search_cannot_silently_truncate_or_follow_other_hosts(mode):
    def handler(r):
        offset = int(r.url.params["offset"])
        row = product(0 if mode == "duplicate" else offset)
        if mode == "unsafe":
            row["downloadURL"] = "https://evil.example/terrain.tif"
        return httpx.Response(
            200,
            json={
                "total": 3 if (mode == "changed" and offset) else 2,
                "items": [] if mode == "missing" else [row],
                "errors": [],
            },
        )

    with http(USGS_3DEP_HOSTS, handler) as client, pytest.raises(ValueError):
        USGS3DEPClient(client).search(
            (-105.35, 39.99, -105.34, 40),
            page_size=1,
            maximum_items=1 if mode == "limit" else 10,
        )


def test_usgs_download_validates_size_host_and_native_grid(tmp_path):
    body = tiff(
        np.zeros((4, 5), dtype="float32"),
        crs="EPSG:26913",
        affine=from_origin(470000, 4430000, 1, 1),
    )

    def handler(r):
        if r.url.host == "tnmaccess.nationalmap.gov":
            return httpx.Response(
                200, json={"total": 1, "items": [product(0) | {"sizeInBytes": len(body)}]}
            )
        return httpx.Response(200, content=body)

    with http(USGS_3DEP_HOSTS, handler) as client:
        adapter = USGS3DEPClient(client)
        p = adapter.search((-105.35, 39.99, -105.34, 40)).products[0]
        path, _ = adapter.download_product(tmp_path, p)
        assert path.is_file()
        with pytest.raises(ValueError, match="budget"):
            adapter.download_product(tmp_path, replace(p, size_bytes=2**40))
        with pytest.raises(ValueError, match="official"):
            adapter.download_product(tmp_path, replace(p, download_url="https://example.org/a.tif"))
