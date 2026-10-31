"""Synthetic STAC boundaries plus actual Orbital PV native-pixel integration."""

import json
import sys
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Any

import httpx
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from energy_data_retrieval.sources.orbitalpv_imagery import (
    IMAGERY_HOSTS,
    ImagerySearch,
    OrbitalPVImageryClient,
    describe_asset,
    load_satellite_image,
    select_finest,
)
from energy_data_retrieval.sources.orbitalpv_imagery import client as module
from energy_data_retrieval.transport import HTTPClient, HTTPConfig

ROOT = "https://maxar-opendata.s3.amazonaws.com/events/Test/"
ACQUISITION = "104001009C64B300"
BOUNDS = (-118.122, 34.210, -118.1205, 34.2115)


def item(gsd=0.33, platform="WV03"):
    return {
        "type": "Feature",
        "id": platform,
        "bbox": [-119, 34, -118, 35],
        "properties": {
            "datetime": "2025-01-08T12:00:00Z",
            "platform": platform,
            "gsd": gsd,
            "proj:epsg": 32611,
        },
        "assets": {
            key: {
                "href": f"{ROOT}ard/{key}.tif",
                "type": "image/tiff",
                "proj:transform": [spacing, 0, 390000, 0, -spacing, 3800000, 0, 0, 1],
                "roles": ["data"],
            }
            for key, spacing in (
                ("pan_analytic", 0.3233),
                ("visual", 0.30517578125),
                ("ms_analytic", 1.2932),
            )
        },
    }


def search(*items):
    return ImagerySearch("maxar-open-data", items, BOUNDS, "2025-01-08", "2025-01-09", True, (), {})


def test_finest_uses_native_detail_not_pansharpened_display_grid():
    fine, coarse = item(), item(0.48, "GE01")
    coarse["assets"]["pan_analytic"]["proj:transform"] = [0.4667, 0, 390000, 0, -0.4667, 3800000]
    assert describe_asset(fine, "visual").grid_spacing_m == (0.30517578125,) * 2
    assert describe_asset(fine, "visual").detail_limit_m == 0.33
    assert describe_asset(coarse, "visual").detail_limit_m == 0.48
    assert select_finest(search(coarse, fine), asset="visual")["id"] == "WV03"
    assert describe_asset(fine, "ms_analytic").native_gsd_m is None
    fine["assets"]["pan_analytic"]["proj:transform"] = [0.5, 0, 390000, 0, -0.5, 3800000]
    assert describe_asset(fine, "pan_analytic").detail_limit_m == 0.5
    assert select_finest(search(fine, coarse))["id"] == "GE01"


def test_selection_requires_complete_known_resolution_and_requested_detail():
    with pytest.raises(ValueError, match="incomplete"):
        select_finest(replace(search(item()), complete=False))
    assert select_finest(replace(search(item()), complete=False), allow_incomplete=True)
    for candidates in (search(), search(item(None))):
        with pytest.raises(ValueError, match="verified native GSD"):
            select_finest(candidates)
    with pytest.raises(ValueError, match="verified native GSD"):
        select_finest(search(item()), maximum_detail_m=0.3)
    with pytest.raises(ValueError, match="positive"):
        select_finest(search(item()), maximum_detail_m=float("nan"))
    original = item()
    selected = select_finest(search(original))
    selected["properties"]["gsd"] = 99
    assert original["properties"]["gsd"] == 0.33
    original["assets"]["visual"]["gsd"] = 0.6
    assert describe_asset(original, "visual").detail_limit_m == 0.6


def test_resolution_units_missing_native_gsd_and_preview_rejection():
    scene = item()
    scene["properties"]["proj:epsg"] = 4326
    assert describe_asset(scene).grid_spacing_m is None
    scene["assets"]["visual"]["type"] = "image/jpeg"
    with pytest.raises(ValueError, match="GeoTIFF"):
        describe_asset(scene)
    scene = item()
    scene["assets"]["visual"]["proj:transform"][1] = 0.1
    with pytest.raises(ValueError, match="north-up"):
        describe_asset(scene)


def catalogue():
    collection = {
        "type": "Collection",
        "id": "Test",
        "license": "CC-BY-NC-4.0",
        "extent": {
            "spatial": {"bbox": [[-119, 34, -118, 35]]},
            "temporal": {"interval": [["2025-01-08", "2025-01-09"]]},
        },
        "links": [{"rel": "child", "href": f"./ard/{ACQUISITION}_collection.json"}],
    }
    acquisition = deepcopy(collection)
    acquisition.update(
        id=ACQUISITION, license="proprietary", links=[{"rel": "item", "href": "./scene.json"}]
    )
    scene = item()
    scene["assets"]["visual"]["href"] = "./visual.tif"
    return {
        f"{ROOT}collection.json": collection,
        f"{ROOT}ard/{ACQUISITION}_collection.json": acquisition,
        f"{ROOT}ard/scene.json": scene,
    }


def query(documents, **kwargs):
    with HTTPClient(
        IMAGERY_HOSTS,
        config=HTTPConfig(minimum_interval_seconds=0),
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json=documents[str(request.url)])
        ),
    ) as http:
        return OrbitalPVImageryClient(http).search_maxar(
            "Test",
            kwargs.pop("bounds", BOUNDS),
            time_min="2025-01-08",
            time_max="2025-01-09",
            **kwargs,
        )


def test_static_stac_traversal_preserves_scope_licences_receipts_and_relative_assets():
    result = query(catalogue(), acquisition_ids=(ACQUISITION,))
    assert result.complete and len(result.requests) == 3 and len(result.items) == 1
    assert result.items[0]["assets"]["visual"]["href"] == ROOT + "ard/visual.tif"
    rights = result.items[0]["properties"]["edi:open_data"]
    assert rights["event_license"] == "CC-BY-NC-4.0"
    assert rights["acquisition_license"] == "proprietary"
    assert all(record.sha256 for record in result.requests)
    outside = query(catalogue(), bounds=(10, 10, 11, 11), acquisition_ids=(ACQUISITION,))
    assert outside.complete and not outside.items and len(outside.requests) == 1
    with pytest.raises(ValueError, match="absent"):
        query(catalogue(), acquisition_ids=("0000000000000000",))


def test_catalogue_budgets_cycles_and_host_scope_fail_without_partial_success():
    with pytest.raises(ValueError, match="maximum_documents"):
        query(catalogue(), maximum_documents=2)
    documents = catalogue()
    documents[ROOT + "collection.json"]["links"] *= 2
    with pytest.raises(ValueError, match="Repeated"):
        query(documents)
    for target in ("https://untrusted.example/data.json", "../Other/collection.json"):
        documents = catalogue()
        documents[ROOT + "collection.json"]["links"][0]["href"] = target
        with pytest.raises(ValueError, match=r"approved provider|selected public event"):
            query(documents)


def test_catalogue_prunes_collection_dates_and_nonmatching_item_bbox():
    documents = catalogue()
    documents[ROOT + f"ard/{ACQUISITION}_collection.json"]["extent"]["temporal"]["interval"] = [
        ["2020-01-01", "2020-02-01"]
    ]
    result = query(documents)
    assert len(result.requests) == 2 and not result.items
    documents = catalogue()
    documents[ROOT + "ard/scene.json"]["bbox"] = [10, 10, 11, 11]
    assert not query(documents).items


def require_orbital():
    if sys.version_info < (3, 13):
        pytest.skip("Optional Orbital PV integration requires Python 3.13")
    return pytest.importorskip("orbitalpv")


def test_missing_or_incompatible_optional_dependency_has_actionable_error(monkeypatch):
    monkeypatch.setattr(module.sys, "version_info", (3, 12))
    with pytest.raises(ImportError, match=r"Python 3\.13"):
        module._orbital()
    monkeypatch.setattr(module.sys, "version_info", (3, 13))
    monkeypatch.setattr(module.importlib, "import_module", lambda name: object())
    with pytest.raises(ImportError, match="pinned imagery extra"):
        module._orbital()


def test_sentinel_search_delegates_to_installed_orbital_and_keeps_cap(monkeypatch):
    require_orbital()

    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(
            200,
            request=request,
            json={
                "type": "FeatureCollection",
                "features": [item()],
                "links": [
                    {"rel": "next", "href": "https://earth-search.aws.element84.com/v1/search"}
                ],
            },
        )

    monkeypatch.setattr(
        httpx.Client,
        "request",
        lambda self, method, url, **kwargs: respond(
            httpx.Request(method, url, json=kwargs.get("json"), params=kwargs.get("params"))
        ),
    )
    with HTTPClient(IMAGERY_HOSTS) as http:
        result = OrbitalPVImageryClient(http).search_sentinel(
            BOUNDS, time_min="2025-01-08", time_max="2025-01-09", max_items=1
        )
    assert len(requests) == 1 and not result.complete
    payload = json.loads(requests[0].content)
    assert payload["collections"] == ["sentinel-2-c1-l2a"]
    assert result.metadata["features"][0]["id"] == "WV03"


def test_actual_orbital_reader_keeps_pixels_masks_calibration_and_checksum(tmp_path, monkeypatch):
    require_orbital()
    source = tmp_path / "synthetic.tif"
    pixels = np.arange(1, 101, dtype=np.uint16).reshape(1, 10, 10)
    pixels[0, 3, 2] = 0
    with rasterio.open(
        source,
        "w",
        driver="GTiff",
        count=1,
        width=10,
        height=10,
        dtype="uint16",
        crs="EPSG:4326",
        transform=from_origin(-1, 1, 0.01, 0.01),
        nodata=0,
    ) as dst:
        dst.write(pixels)
    scene: dict[str, Any] = {
        "id": "synthetic",
        "collection": "sentinel-2-c1-l2a",
        "properties": {},
        "assets": {
            "red": {
                "href": ROOT + "red.tif",
                "type": "image/tiff",
                "gsd": 10,
                "roles": ["data", "reflectance"],
                "raster:bands": [{"scale": 0.0001, "offset": -0.1, "nodata": 0}],
            }
        },
    }
    original = rasterio.open
    monkeypatch.setattr(
        rasterio,
        "open",
        lambda name, *a, **kw: original(
            source if str(name) == ROOT + "red.tif" else name, *a, **kw
        ),
    )
    with HTTPClient(IMAGERY_HOSTS) as http:
        client = OrbitalPVImageryClient(http)
        image = client.read_image(scene, (-1, 0.9, -0.9, 1), asset="red")
        assert image.data.shape == (1, 10, 10)
        np.testing.assert_array_equal(image.data.data, pixels)
        assert image.data.mask[0, 3, 2] and image.data.count() == 99
        assert image.reflectance()[0, 3, 3] == pytest.approx(34 * 0.0001 - 0.1)
        with pytest.raises(ValueError, match="max_pixels"):
            client.read_image(scene, (-1, 0.9, -0.9, 1), asset="red", maximum_samples=10)
        bad = deepcopy(scene)
        bad["assets"]["red"]["href"] = "https://untrusted.example/red.tif"
        with pytest.raises(ValueError, match="approved provider"):
            client.read_image(bad, (-1, 0.9, -0.9, 1), asset="red")
        bad = deepcopy(scene)
        bad["assets"]["red"]["proj:epsg"] = 32611
        with pytest.raises(ValueError, match="Actual TIFF CRS"):
            client.read_image(bad, (-1, 0.9, -0.9, 1), asset="red")
        bad["assets"]["red"]["proj:epsg"] = 4326
        # Synthetic projected-metadata mismatch is checked above; geographic
        # degree spacing is never labelled as metres by the resolution summary.
        assert describe_asset(bad, "red").grid_spacing_m is None
    saved = tmp_path / "saved.tif"
    image.save_geotiff(saved)
    loaded = load_satellite_image(str(saved))
    np.testing.assert_array_equal(loaded.data.mask, image.data.mask)
    assert loaded.transform == image.transform
    saved.write_bytes(saved.read_bytes() + b"corrupt")
    with pytest.raises(ValueError, match=r"checksum|SHA|hash"):
        load_satellite_image(str(saved))


def test_real_offline_captures_have_native_detail_and_full_metadata():
    require_orbital()
    data = Path(__file__).resolve().parents[2] / "examples/connectors/data"
    manifest = json.loads((data / "imagery_provenance.json").read_text())
    for row in manifest["samples"]:
        image = load_satellite_image(str(data / row["fixture"]))
        assert list(image.data.shape) == row["shape"]
        assert image.data.count() / image.data.size == pytest.approx(row["valid_fraction"])
        assert (
            image.item_metadata and image.asset_metadata and image.source_url.startswith("https://")
        )
    pan = load_satellite_image(str(data / "imagery_altadena_pan_analytic.tif"))
    detail = describe_asset(pan.item_metadata, pan.asset_key).detail_limit_m
    assert detail is not None and detail <= 0.35
