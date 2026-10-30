"""Download Spain's 2019 GSA archive, retaining annual GHI and its metadata."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from zipfile import ZipFile

import httpx

from energy_data_retrieval.transport import HTTPClient, RequestRecord, RetrievalError, _secret_scope

GSA_HOSTS = frozenset({"api.globalsolaratlas.info"})
ARCHIVE_NAME = "Spain_GISdata_LTAym_YearlyMonthlyTotals_GlobalSolarAtlas-v2_GEOTIFF.zip"
ARCHIVE_URL = f"https://api.globalsolaratlas.info/download/Spain/{ARCHIVE_NAME}"
ARCHIVE_BYTES = 95_749_512
ARCHIVE_SHA256 = "32449665d93ce101ad22220a050ef23c6e03da47488e49f2b4db0e0b4b66f56c"
MEMBER_PREFIX = "Spain_GISdata_LTAy_YearlyMonthlyTotals_GlobalSolarAtlas-v2_GEOTIFF"
REFERENCE_IDS = ("global_solar_atlas_2019",)


class SolarAtlasTransport(httpx.BaseTransport):
    """Follow exactly one provider-issued download redirect to its known S3 object.

    The surrounding HTTPClient handles byte limits, retries, hashes and atomic
    files. Its durable record always contains the public API URL. Signed URLs
    are used only in memory, never returned or stored. No arbitrary redirect
    destination is accepted; this transport is specific to the Spain archive.
    """

    def __init__(self, inner: httpx.BaseTransport) -> None:
        self.inner = inner

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        """Return the public response or its validated single-object download."""
        if str(request.url) != ARCHIVE_URL or request.method != "GET":
            raise ValueError("Solar Atlas transport only accepts the pinned Spain archive")
        response = self.inner.handle_request(request)
        if response.status_code != 302:
            return response
        location = response.headers.get("location", "")
        response.close()
        parts = urlsplit(location)
        if (
            parts.scheme != "https"
            or parts.hostname != "worldbank-atlas.s3.us-east-1.amazonaws.com"
            or parts.path != f"/download/Spain/{ARCHIVE_NAME}"
            or parts.username is not None
            or parts.password is not None
            or parts.fragment
            or parts.port not in (None, 443)
        ):
            raise RetrievalError("Unexpected Solar Atlas download redirect")
        secrets = (location, *(v for values in parse_qs(parts.query).values() for v in values))
        with _secret_scope(secrets):
            return self.inner.handle_request(httpx.Request("GET", location))

    def close(self) -> None:
        self.inner.close()


class GlobalSolarAtlasClient:
    """Use an HTTPClient configured with SolarAtlasTransport and a 110 MB limit."""

    def __init__(self, http: HTTPClient) -> None:
        self.http = http

    def download_spain_ghi(self, directory: Path) -> tuple[Path, RequestRecord]:
        directory = Path(directory)
        archive = directory / ARCHIVE_NAME
        record = self.http.download_file(
            ARCHIVE_URL,
            archive,
            expected_sha256=ARCHIVE_SHA256,
            expected_size_bytes=ARCHIVE_BYTES,
        )
        names = [f"{MEMBER_PREFIX}/GHI.tif{suffix}" for suffix in ("", ".xml", ".pdf")]
        with ZipFile(archive) as source:
            if len(source.namelist()) != len(set(source.namelist())):
                raise RetrievalError("Duplicate members in Solar Atlas archive")
            if not set(names).issubset(source.namelist()):
                raise RetrievalError("Solar Atlas archive is missing GHI or its metadata")
            if sum(source.getinfo(n).file_size for n in names) > 20_000_000:
                raise RetrievalError("Solar Atlas GHI exceeds expanded-size limit")
            contents = {name: source.read(name) for name in names}
        for name, content in contents.items():
            (directory / Path(name).name).write_bytes(content)
        return directory / "GHI.tif", record
