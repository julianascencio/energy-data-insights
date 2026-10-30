"""ETag-bound range reads and native, scaled CHELSA regional crops."""

import hashlib
import re

import httpx
import numpy as np
import pytest
import rasterio
from rasterio.io import MemoryFile
from rasterio.transform import from_origin

from energy_data_retrieval.sources.chelsa import CHELSAClient
from energy_data_retrieval.sources.chelsa.client import RangeReader
from energy_data_retrieval.transport import RetrievalError


def source_transport(raw, *, fault=None):
    seen = []

    def respond(request):
        seen.append(request)
        if request.method == "HEAD":
            return httpx.Response(
                200, headers={"Content-Length": str(len(raw)), "ETag": '"abcdef"'}
            )
        match = re.fullmatch(r"bytes=(\d+)-(\d+)", request.headers["Range"])
        assert match is not None
        start, stop = map(int, match.groups())
        assert request.headers["If-Match"] == '"abcdef"'
        headers = {"Content-Range": f"bytes {start}-{stop}/{len(raw)}", "ETag": '"abcdef"'}
        if fault == "etag":
            headers["ETag"] = '"changed"'
        elif fault == "range":
            headers["Content-Range"] = "bytes 0-1/2"
        return httpx.Response(
            200 if fault == "full" else 206, headers=headers, content=raw[start : stop + 1]
        )

    return httpx.MockTransport(respond), seen


def test_range_seek_cache_and_budget():
    raw = b"0123456789abcdef"
    transport, seen = source_transport(raw)
    with httpx.Client(transport=transport) as http:
        reader = RangeReader(
            http, "https://example.org/cog", len(raw), '"abcdef"', block_size=4, maximum_bytes=8
        )
        assert reader.read(3) == b"012"
        reader.seek(1)
        assert reader.read(5) == b"12345"
        assert len(seen) == 2
        reader.seek(-2, 2)
        with pytest.raises(RetrievalError, match="budget"):
            reader.read(2)
        reader.seek(0)
        with pytest.raises(RetrievalError, match="unbounded"):
            reader.read(33_000_000)


@pytest.mark.parametrize("fault", ["etag", "range", "full"])
def test_range_fails_closed_on_changed_or_unbounded_response(fault):
    transport, _ = source_transport(b"01234567", fault=fault)
    with httpx.Client(transport=transport) as http:
        reader = RangeReader(http, "https://example.org/cog", 8, '"abcdef"', block_size=4)
        with pytest.raises(RetrievalError, match="changed"):
            reader.read(1)


def test_crop_preserves_integer_cells_scale_and_source_version(tmp_path):
    values = np.arange(48, dtype="uint16").reshape(6, 8) + 2731
    values[1, 2] = 65535
    with MemoryFile() as memory:
        with memory.open(
            driver="GTiff",
            width=8,
            height=6,
            count=1,
            dtype="uint16",
            transform=from_origin(-70, -30, 1 / 120, 1 / 120),
            crs="EPSG:4326",
            nodata=65535,
        ) as target:
            target.write(values, 1)
            target.scales = (0.1,)
            target.update_tags(
                variable="tas", variable_unit="K", version="2.1", datetime="1981-2010"
            )
        raw = memory.read()
    transport, seen = source_transport(raw)
    bounds = (-69.99, -30.031, -69.969, -30.009)
    with httpx.Client(transport=transport) as http:
        client = CHELSAClient(http)
        path, record = client.download_window(tmp_path, "tas", 1, bounds, expected_etag='"abcdef"')
        expected = values[1:4, 1:4]
        with rasterio.open(path) as subset:
            np.testing.assert_array_equal(subset.read(1), expected)
            assert subset.scales == (0.1,) and subset.nodata == 65535
            assert subset.transform.c == pytest.approx(-70 + 1 / 120)
        assert (
            record["pixels_sha256"] == hashlib.sha256(expected.astype("<u2").tobytes()).hexdigest()
        )
        calls = len(seen)
        assert client.download_window(tmp_path, "tas", 1, bounds)[1] == record
        assert len(seen) == calls
        with pytest.raises(ValueError, match="changed"):
            client.download_window(tmp_path, "tas", 1, bounds, expected_etag='"999"')
        with pytest.raises(ValueError, match="reviewed"):
            client.download_window(
                tmp_path / "other", "tas", 1, bounds, expected_pixels_sha256="0" * 64
            )
        assert not list((tmp_path / "other").glob("*.partial"))
        path.write_bytes(b"corrupted")
        with pytest.raises(ValueError, match="changed"):
            client.download_window(tmp_path, "tas", 1, bounds)


@pytest.mark.parametrize(
    "variable,month,bounds",
    [
        ("rsds", 1, (-71, -33, -70, -32)),
        ("tas", True, (-71, -33, -70, -32)),
        ("pr", 13, (-71, -33, -70, -32)),
        ("tas", 1, (-71, -33, -72, -32)),
        ("tas", 1, (-180, -90, 180, 90)),
    ],
)
def test_invalid_request_does_not_issue_http(tmp_path, variable, month, bounds):
    transport, seen = source_transport(b"unused")
    with httpx.Client(transport=transport) as http, pytest.raises(ValueError):
        CHELSAClient(http).download_window(tmp_path, variable, month, bounds)
    assert not seen
