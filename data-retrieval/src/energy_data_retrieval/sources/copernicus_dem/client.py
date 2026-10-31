"""Anonymous GLO-30 Public cloud-optimized GeoTIFFs; no GLO-90 fallback."""

from __future__ import annotations

import math
from pathlib import Path

import rasterio

from energy_data_retrieval.terrain import TerrainSource, validate_point
from energy_data_retrieval.transport import HTTPClient, RequestRecord, TextResponse

COPERNICUS_DEM_HOSTS = frozenset({"copernicus-dem-30m.s3.amazonaws.com"})
BASE_URL = "https://copernicus-dem-30m.s3.amazonaws.com"
REFERENCE_IDS = ("copernicus_dem", "copernicus_dem_aws")
COPERNICUS_DEM_SOURCE = TerrainSource(
    "copernicus_dem",
    "Copernicus DEM GLO-30 Public (AWS)",
    "DSM including buildings and vegetation",
    "EGM2008",
    REFERENCE_IDS,
)


def tile_name(latitude: float, longitude: float) -> str:
    """Return the documented COG tile ID; 10 means 1 arcsecond, not 10 metres."""
    validate_point(latitude, longitude)
    lat, lon = math.floor(latitude), math.floor(longitude)
    return (
        f"Copernicus_DSM_COG_10_{'N' if lat >= 0 else 'S'}{abs(lat):02d}_00_"
        f"{'E' if lon >= 0 else 'W'}{abs(lon):03d}_00_DEM"
    )


class CopernicusDEMClient:
    """Download original GLO-30 COGs, preserving grid, masks and datum.

    GLO-30 Public is the AWS distribution, not a claim about the newest CDSE
    release. Ocean tiles and some restricted tiles are absent. Longitude
    spacing increases poleward; read the actual transform. Default downloads
    retain the complete native tile and can be reused through HTTP manifests.
    """

    def __init__(self, http: HTTPClient) -> None:
        self.http = http

    def available_tiles(self) -> TextResponse:
        """Retrieve the provider's tileList.txt, with exact response provenance."""
        return self.http.get_text(f"{BASE_URL}/tileList.txt", {})

    def download_tile(
        self,
        directory: Path,
        *,
        latitude: float,
        longitude: float,
        expected_sha256: str | None = None,
    ) -> tuple[Path, RequestRecord]:
        name = tile_name(latitude, longitude)
        path = Path(directory) / f"{name}.tif"
        record = self.http.download_file(
            f"{BASE_URL}/{name}/{name}.tif",
            path,
            expected_sha256=expected_sha256,
        )
        with rasterio.open(path) as dataset:
            if (
                dataset.count != 1
                or dataset.crs != rasterio.crs.CRS.from_epsg(4326)
                or dataset.height != 3600
                or dataset.width not in {3600, 2400, 1800, 1200, 720, 360}
                or dataset.transform.b != 0
                or dataset.transform.d != 0
                or dataset.transform.a <= 0
                or dataset.transform.e >= 0
                or not math.isclose(dataset.res[1], 1 / 3600)
                or not math.isclose(dataset.res[0] * dataset.width, 1.0)
                or not math.isclose(
                    dataset.bounds.left + dataset.res[0] / 2,
                    math.floor(longitude),
                    abs_tol=1e-9,
                    rel_tol=0,
                )
                or not math.isclose(
                    dataset.bounds.top - dataset.res[1] / 2,
                    math.floor(latitude) + 1,
                    abs_tol=1e-9,
                    rel_tol=0,
                )
            ):
                raise ValueError("Response is not a native GLO-30 geographic tile")
        return path, record
