"""Bounded, checksummed acquisition of Natural Earth Admin 0 country contours."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal
from zipfile import ZipFile

from energy_data_retrieval.transport import HTTPClient, RequestRecord, RetrievalError

NATURAL_EARTH_HOSTS = frozenset({"naturalearth.s3.amazonaws.com"})
REFERENCE_IDS = ("natural_earth_countries",)


@dataclass(frozen=True, slots=True)
class BoundaryDownload:
    """Local .shp path, companion files and exact public-source provenance."""

    shapefile: Path
    manifest: Path
    request: RequestRecord


class NaturalEarthClient:
    def __init__(self, http: HTTPClient) -> None:
        self.http = http

    def download_countries(
        self,
        directory: Path,
        *,
        scale: Literal["10m", "50m", "110m"] = "10m",
        expected_sha256: str | None = None,
    ) -> BoundaryDownload:
        """Keep .shp/.shx/.dbf/.prj/.cpg companions and a source/hash manifest.

        Scale means 1:10/50/110 million, not metre accuracy. The official URL
        tracks releases; pass a previously recorded SHA-256 to require identical
        bytes. Only exact, flat member names are read; archives are never blindly
        extracted. Compressed size is bounded by the shared HTTP configuration.
        """
        if scale not in {"10m", "50m", "110m"}:
            raise ValueError("Natural Earth scale must be 10m, 50m or 110m")
        stem = f"ne_{scale}_admin_0_countries"
        directory = Path(directory)
        archive = directory / f"{stem}.zip"
        url = f"https://naturalearth.s3.amazonaws.com/{scale}_cultural/{stem}.zip"
        request = self.http.download_file(url, archive, expected_sha256=expected_sha256)
        required = {f"{stem}{suffix}" for suffix in (".shp", ".shx", ".dbf", ".prj")}
        optional = {f"{stem}.cpg", f"{stem}.VERSION.txt"}
        with ZipFile(archive) as source:
            names = source.namelist()
            if len(names) != len(set(names)) or not required.issubset(names):
                raise RetrievalError("Country archive has duplicate or missing shapefile members")
            selected = sorted(required | (optional & set(names)))
            if sum(source.getinfo(name).file_size for name in selected) > 50_000_000:
                raise RetrievalError("Country shapefile exceeds the 50 MB expanded limit")
            # Read and verify CRCs before writing any companion files.
            contents = {name: source.read(name) for name in selected}
        hashes = {}
        for name, content in contents.items():
            (directory / name).write_bytes(content)
            hashes[name] = hashlib.sha256(content).hexdigest()
        manifest = directory / f"{stem}.provenance.json"
        manifest.write_text(
            json.dumps(
                {
                    "source": "Natural Earth Admin 0 - Countries",
                    "scale": scale,
                    "version": contents.get(f"{stem}.VERSION.txt", b"unspecified").decode().strip(),
                    "license": "Public domain",
                    "terms_url": "https://www.naturalearthdata.com/about/terms-of-use/",
                    "boundary_policy": "Natural Earth default de facto boundaries",
                    "request": asdict(request),
                    "files_sha256": hashes,
                    "reference_ids": list(REFERENCE_IDS),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return BoundaryDownload(directory / f"{stem}.shp", manifest, request)
