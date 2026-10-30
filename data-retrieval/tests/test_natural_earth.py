"""Bounded Natural Earth archives and companion/checksum provenance."""

import hashlib
import io
import json
from zipfile import ZipFile

import httpx
import pytest

from energy_data_retrieval.sources.natural_earth import NATURAL_EARTH_HOSTS, NaturalEarthClient
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, RetrievalError


def archive(missing=None):
    contents = io.BytesIO()
    with ZipFile(contents, "w") as output:
        for suffix in (".shp", ".dbf", ".shx", ".prj", ".cpg", ".VERSION.txt"):
            if suffix != missing:
                output.writestr(f"ne_10m_admin_0_countries{suffix}", "fixture")
        output.writestr("../escape.txt", "must never be extracted")
    return contents.getvalue()


def client(payload, calls):
    def handler(request):
        calls.append(request)
        return httpx.Response(200, content=payload)

    return HTTPClient(
        allowed_hosts=NATURAL_EARTH_HOSTS,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(attempts=1, minimum_interval_seconds=0),
    )


def test_download_companions_provenance_checksum_and_reuse(tmp_path):
    payload, calls = archive(), []
    expected = hashlib.sha256(payload).hexdigest()
    with client(payload, calls) as http:
        first = NaturalEarthClient(http).download_countries(
            tmp_path / "boundaries", expected_sha256=expected
        )
        second = NaturalEarthClient(http).download_countries(
            tmp_path / "boundaries", expected_sha256=expected
        )
    assert len(calls) == 1 and second.request.cache_hit
    assert calls[0].url.path == "/10m_cultural/ne_10m_admin_0_countries.zip"
    assert first.shapefile.exists()
    assert not (tmp_path / "escape.txt").exists()
    metadata = json.loads(first.manifest.read_text())
    assert metadata["request"]["sha256"] == expected
    assert len(metadata["files_sha256"]) == 6


def test_missing_companions_and_unsupported_scale_fail(tmp_path):
    calls = []
    with client(archive(".prj"), calls) as http:
        with pytest.raises(ValueError, match="scale"):
            NaturalEarthClient(http).download_countries(tmp_path, scale="1m")  # ty: ignore[invalid-argument-type]
        assert calls == []
        with pytest.raises(RetrievalError, match="missing"):
            NaturalEarthClient(http).download_countries(tmp_path)
    assert not (tmp_path / "ne_10m_admin_0_countries.shp").exists()
