"""Download pinned 2019 GSA archives, retaining annual GHI and its metadata."""

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
CHILE_ARCHIVE_NAME = "Chile_GISdata_LTAym_YearlyMonthlyTotals_GlobalSolarAtlas-v2_GEOTIFF.zip"
CHILE_ARCHIVE_URL = f"https://api.globalsolaratlas.info/download/Chile/{CHILE_ARCHIVE_NAME}"
CHILE_ARCHIVE_BYTES = 145_387_267
CHILE_ARCHIVE_SHA256 = "3b17db760a4668d2d9752833ae343d63d5993a30e60598effffaeb2558ff7e06"
CHILE_MEMBER_PREFIX = "Chile_GISdata_LTAy_YearlyMonthlyTotals_GlobalSolarAtlas-v2_GEOTIFF"
REFERENCE_IDS = ("global_solar_atlas_2019", "global_solar_atlas_chile_2019")


class SolarAtlasTransport(httpx.BaseTransport):
    """Follow exactly one provider-issued download redirect to its known S3 object.

    The surrounding HTTPClient handles byte limits, retries, hashes and atomic
    files. Its durable record always contains the public API URL. Signed URLs
    are used only in memory, never returned or stored. No arbitrary redirect
    destination is accepted; only the selected, pinned country archive is allowed.
    """

    def __init__(self, inner: httpx.BaseTransport, *, country: str = "Spain") -> None:
        if country not in {"Spain", "Chile"}:
            raise ValueError("Select a pinned Spain or Chile archive")
        self.inner = inner
        self.country = country
        self.name = ARCHIVE_NAME if country == "Spain" else CHILE_ARCHIVE_NAME
        self.url = ARCHIVE_URL if country == "Spain" else CHILE_ARCHIVE_URL

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        """Return the public response or its validated single-object download."""
        if str(request.url) != self.url or request.method != "GET":
            raise ValueError("Solar Atlas transport only accepts the selected pinned archive")
        response = self.inner.handle_request(request)
        if response.status_code != 302:
            return response
        location = response.headers.get("location", "")
        response.close()
        parts = urlsplit(location)
        if (
            parts.scheme != "https"
            or parts.hostname != "worldbank-atlas.s3.us-east-1.amazonaws.com"
            or parts.path != f"/download/{self.country}/{self.name}"
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
    """Use SolarAtlasTransport and a limit of 110 MB (Spain) or 160 MB (Chile)."""

    def __init__(self, http: HTTPClient) -> None:
        self.http = http

    def download_spain_ghi(self, directory: Path) -> tuple[Path, RequestRecord]:
        return self._download_ghi(
            directory,
            ARCHIVE_NAME,
            ARCHIVE_URL,
            ARCHIVE_SHA256,
            ARCHIVE_BYTES,
            MEMBER_PREFIX,
            20_000_000,
        )

    def download_chile_ghi(self, directory: Path) -> tuple[Path, RequestRecord]:
        """Annual 1999-2018 GHI; source coverage ends at 45 degrees south."""
        return self._download_ghi(
            directory,
            CHILE_ARCHIVE_NAME,
            CHILE_ARCHIVE_URL,
            CHILE_ARCHIVE_SHA256,
            CHILE_ARCHIVE_BYTES,
            CHILE_MEMBER_PREFIX,
            64_000_000,
        )

    def _download_ghi(
        self,
        directory: Path,
        name: str,
        url: str,
        checksum: str,
        size: int,
        prefix: str,
        expanded_limit: int,
    ) -> tuple[Path, RequestRecord]:
        directory = Path(directory)
        archive = directory / name
        record = self.http.download_file(
            url,
            archive,
            expected_sha256=checksum,
            expected_size_bytes=size,
        )
        names = [f"{prefix}/GHI.tif{suffix}" for suffix in ("", ".xml", ".pdf")]
        with ZipFile(archive) as source:
            if len(source.namelist()) != len(set(source.namelist())):
                raise RetrievalError("Duplicate members in Solar Atlas archive")
            if not set(names).issubset(source.namelist()):
                raise RetrievalError("Solar Atlas archive is missing GHI or its metadata")
            if sum(source.getinfo(n).file_size for n in names) > expanded_limit:
                raise RetrievalError("Solar Atlas GHI exceeds expanded-size limit")
            contents = {name: source.read(name) for name in names}
        for name, content in contents.items():
            (directory / Path(name).name).write_bytes(content)
        return directory / "GHI.tif", record
