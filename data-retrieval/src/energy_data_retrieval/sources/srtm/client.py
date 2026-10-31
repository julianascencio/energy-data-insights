"""NASA SRTMGL1 one-arcsecond HGT tiles from ESA's public SNAP auxiliary mirror."""

from __future__ import annotations

import math
from pathlib import Path
from zipfile import BadZipFile, ZipFile

import numpy as np
from rasterio.io import MemoryFile
from rasterio.transform import from_origin

from energy_data_retrieval.terrain import TerrainSource, validate_point
from energy_data_retrieval.transport import HTTPClient, RequestRecord, RetrievalError, atomic_bytes

SRTM_HOSTS = frozenset({"step.esa.int"})
BASE_URL = "https://step.esa.int/auxdata/dem/SRTMGL1"
REFERENCE_IDS = ("nasa_srtmgl1", "esa_srtm_mirror")
SRTM_SOURCE = TerrainSource(
    "srtm",
    "SRTMGL1 (ESA SNAP mirror)",
    "radar surface, with void filling",
    "EGM96",
    REFERENCE_IDS,
)


def tile_name(latitude: float, longitude: float) -> str:
    """Southwest tile name; negative coordinates use floor, never truncation."""
    validate_point(latitude, longitude)
    if not -56 <= latitude < 60:
        raise ValueError("SRTM covers land between 56 S and 60 N; no polar fallback")
    lat, lon = math.floor(latitude), math.floor(longitude)
    return f"{'N' if lat >= 0 else 'S'}{abs(lat):02d}{'E' if lon >= 0 else 'W'}{abs(lon):03d}"


class SRTMClient:
    """Download the finest public SRTM grid: 1 arcsecond, approximately 30 m.

    This is not 1 m terrain. HGT samples are 3601 x 3601 signed big-endian
    int16 posts, including shared boundary posts. Heights remain EGM96 metres;
    no SNAP ellipsoid correction is applied. Missing tiles raise retrieval
    errors; absent land or mirror coverage is never replaced by zero.
    """

    def __init__(self, http: HTTPClient) -> None:
        self.http = http

    def download_tile(
        self,
        directory: Path,
        *,
        latitude: float,
        longitude: float,
        expected_sha256: str | None = None,
    ) -> tuple[Path, RequestRecord]:
        name = tile_name(latitude, longitude)
        archive = Path(directory) / f"{name}.SRTMGL1.hgt.zip"
        record = self.http.download_file(
            f"{BASE_URL}/{archive.name}",
            archive,
            expected_sha256=expected_sha256,
        )
        try:
            with ZipFile(archive) as bundle:
                members = bundle.infolist()
                if (
                    len(members) != 1
                    or members[0].filename != f"{name}.hgt"
                    or members[0].file_size != 3601 * 3601 * 2
                    or members[0].flag_bits & 1
                ):
                    raise ValueError("Expected exactly one 3601 x 3601 SRTMGL1 HGT member")
                values = np.frombuffer(bundle.read(members[0]), dtype=">i2").reshape(3601, 3601)
        except BadZipFile as error:
            raise RetrievalError("Invalid SRTM ZIP response") from error
        # Pixel centres coincide with the published HGT posts, including edges.
        spacing = 1 / 3600
        affine = from_origin(
            math.floor(longitude) - spacing / 2,
            math.floor(latitude) + 1 + spacing / 2,
            spacing,
            spacing,
        )
        path = Path(directory) / f"{name}.SRTMGL1.tif"
        with MemoryFile() as memory:
            with memory.open(
                driver="GTiff",
                height=3601,
                width=3601,
                count=1,
                dtype="int16",
                crs="EPSG:4326",
                transform=affine,
                nodata=-32768,
                compress="deflate",
            ) as dataset:
                dataset.write(values.astype("int16"), 1)
                dataset.set_band_unit(1, "m")
                dataset.update_tags(
                    AREA_OR_POINT="Point",
                    source=SRTM_SOURCE.name,
                    vertical_datum="EGM96",
                    source_sha256=record.sha256,
                )
            atomic_bytes(path, memory.read())
        return path, record
