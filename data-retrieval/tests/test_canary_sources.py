"""Public source URL bounds, source-byte integrity and safe GSA redirection."""

import json
import logging
from pathlib import Path
from zipfile import ZipFile

import httpx
import pytest

from energy_data_retrieval.sources.canary_clim import CANARY_CLIM_HOSTS, CanaryClimClient
from energy_data_retrieval.sources.global_solar_atlas.client import (
    ARCHIVE_NAME,
    ARCHIVE_URL,
    GSA_HOSTS,
    MEMBER_PREFIX,
    GlobalSolarAtlasClient,
    SolarAtlasTransport,
)
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, RetrievalError


def test_canary_month_url_cache_and_bad_selectors(tmp_path):
    seen = []

    def respond(request):
        seen.append(str(request.url))
        return httpx.Response(200, content=b"fixture COG")

    with HTTPClient(
        allowed_hosts=CANARY_CLIM_HOSTS, transport=httpx.MockTransport(respond)
    ) as http:
        client = CanaryClimClient(http)
        path, record = client.download_month(tmp_path, "tas", 2)
        assert path.read_bytes() == b"fixture COG"
        assert record.endpoint.endswith("tas/1979-2013/CHELSACanaryClim_tas_02_1979-2013_V.1.0.tif")
        assert client.download_month(tmp_path, "tas", 2)[1].cache_hit
        for month in (0, 13, True):
            with pytest.raises(ValueError, match="month"):
                client.download_month(tmp_path, "tas", month)
        with pytest.raises(ValueError, match="variable"):
            client.download_month(tmp_path, "bad", 1)  # ty: ignore[invalid-argument-type]
        path.write_bytes(b"changed")
        with pytest.raises(ValueError, match="checksum"):
            client.download_month(tmp_path, "tas", 2)
    assert len(seen) == 1


def test_gsa_follows_only_exact_object_and_never_persists_signed_query(tmp_path, caplog):
    signature = "temporary-private-signature"
    location = (
        f"https://worldbank-atlas.s3.us-east-1.amazonaws.com/download/Spain/{ARCHIVE_NAME}"
        f"?X-Amz-Signature={signature}"
    )
    seen = []

    def respond(request):
        seen.append(str(request.url))
        if str(request.url) == ARCHIVE_URL:
            return httpx.Response(302, headers={"Location": location})
        return httpx.Response(200, content=b"archive")

    caplog.set_level(logging.DEBUG)
    with HTTPClient(
        allowed_hosts=GSA_HOSTS, transport=SolarAtlasTransport(httpx.MockTransport(respond))
    ) as http:
        record = http.download_file(ARCHIVE_URL, tmp_path / "sample.zip")
    assert len(seen) == 2
    assert record.endpoint == ARCHIVE_URL and not record.parameters
    manifest = json.loads((tmp_path / "sample.zip.download.json").read_text())
    assert "X-Amz" not in json.dumps(manifest)
    assert signature not in caplog.text


@pytest.mark.parametrize(
    "location",
    [
        "https://example.com/file.zip",
        "http://worldbank-atlas.s3.us-east-1.amazonaws.com/download/Spain/other.zip",
        "https://worldbank-atlas.s3.us-east-1.amazonaws.com/download/Spain/other.zip",
        f"https://user@worldbank-atlas.s3.us-east-1.amazonaws.com/download/Spain/{ARCHIVE_NAME}",
    ],
)
def test_gsa_rejects_unexpected_redirects(location, tmp_path):
    def respond(request):
        return httpx.Response(302, headers={"Location": location})

    with (
        HTTPClient(
            allowed_hosts=GSA_HOSTS, transport=SolarAtlasTransport(httpx.MockTransport(respond))
        ) as http,
        pytest.raises(RetrievalError, match="redirect"),
    ):
        http.download_file(ARCHIVE_URL, tmp_path / "sample.zip")
    assert not (tmp_path / "sample.zip").exists()


def test_gsa_archive_extracts_only_exact_members(tmp_path, monkeypatch):
    import hashlib

    from energy_data_retrieval.sources.global_solar_atlas import client as module

    archive = tmp_path / "source.zip"
    with ZipFile(archive, "w") as z:
        for suffix in ("", ".xml", ".pdf"):
            z.writestr(f"{MEMBER_PREFIX}/GHI.tif{suffix}", b"source metadata or data")
        z.writestr("../../unexpected", b"never extract")
    raw = archive.read_bytes()
    monkeypatch.setattr(module, "ARCHIVE_BYTES", len(raw))
    monkeypatch.setattr(module, "ARCHIVE_SHA256", hashlib.sha256(raw).hexdigest())
    with HTTPClient(
        allowed_hosts=GSA_HOSTS,
        config=HTTPConfig(attempts=1),
        transport=httpx.MockTransport(lambda request: httpx.Response(200, content=raw)),
    ) as http:
        path, record = GlobalSolarAtlasClient(http).download_spain_ghi(tmp_path / "out")
    assert path.name == "GHI.tif" and path.read_bytes() == b"source metadata or data"
    assert Path(str(path) + ".xml").is_file()
    assert record.sha256 == hashlib.sha256(raw).hexdigest()
    assert not (tmp_path / "unexpected").exists()


def test_chile_redirect_cannot_fetch_spain_archive(tmp_path):
    from energy_data_retrieval.sources.global_solar_atlas.client import CHILE_ARCHIVE_URL

    seen = []

    def respond(request):
        seen.append(request)
        return httpx.Response(
            302,
            headers={
                "Location": f"https://worldbank-atlas.s3.us-east-1.amazonaws.com/download/Spain/{ARCHIVE_NAME}"
            },
        )

    with (
        HTTPClient(
            allowed_hosts=GSA_HOSTS,
            transport=SolarAtlasTransport(httpx.MockTransport(respond), country="Chile"),
        ) as http,
        pytest.raises(RetrievalError, match="redirect"),
    ):
        http.download_file(CHILE_ARCHIVE_URL, tmp_path / "chile.zip")
    assert len(seen) == 1
    with pytest.raises(ValueError, match="pinned"):
        SolarAtlasTransport(httpx.MockTransport(respond), country="Other")


def test_chile_archive_pin_and_canonical_redirect(tmp_path, monkeypatch):
    import hashlib

    from energy_data_retrieval.sources.global_solar_atlas import client as module

    archive = tmp_path / "source.zip"
    with ZipFile(archive, "w") as z:
        for suffix in ("", ".xml", ".pdf"):
            z.writestr(f"{module.CHILE_MEMBER_PREFIX}/GHI.tif{suffix}", b"Chile fixture")
    raw = archive.read_bytes()
    monkeypatch.setattr(module, "CHILE_ARCHIVE_BYTES", len(raw))
    monkeypatch.setattr(module, "CHILE_ARCHIVE_SHA256", hashlib.sha256(raw).hexdigest())

    def respond(request):
        if str(request.url) == module.CHILE_ARCHIVE_URL:
            return httpx.Response(
                302,
                headers={
                    "Location": f"https://worldbank-atlas.s3.us-east-1.amazonaws.com/download/Chile/{module.CHILE_ARCHIVE_NAME}?X-Amz-Signature=temporary"
                },
            )
        return httpx.Response(200, content=raw)

    with HTTPClient(
        allowed_hosts=GSA_HOSTS,
        transport=SolarAtlasTransport(httpx.MockTransport(respond), country="Chile"),
    ) as http:
        path, record = GlobalSolarAtlasClient(http).download_chile_ghi(tmp_path / "out")
    assert path.read_bytes() == b"Chile fixture"
    assert record.endpoint == module.CHILE_ARCHIVE_URL
    assert "X-Amz" not in path.with_name(module.CHILE_ARCHIVE_NAME + ".download.json").read_text()
