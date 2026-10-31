"""USGS National Map discovery and downloads of project-based 1 m terrain."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

import rasterio

from energy_data_retrieval.terrain import Bounds, TerrainSource, validate_bounds
from energy_data_retrieval.transport import HTTPClient, JSONValue, RequestRecord, object_value

USGS_3DEP_HOSTS = frozenset({"tnmaccess.nationalmap.gov", "prd-tnm.s3.amazonaws.com"})
BASE_URL = "https://tnmaccess.nationalmap.gov/api/v1/products"
DATASET = "Digital Elevation Model (DEM) 1 meter"
REFERENCE_IDS = ("usgs_3dep", "usgs_tnm_api")
USGS_3DEP_SOURCE = TerrainSource(
    "usgs_3dep",
    "USGS 3DEP project-based 1 m DEM",
    "lidar-derived bare-earth DTM",
    "NAVD88 in CONUS; verify project metadata elsewhere",
    REFERENCE_IDS,
)


@dataclass(frozen=True, slots=True)
class TerrainProduct:
    """Provider product metadata retained verbatim; publication is not acquisition."""

    source_id: str
    title: str
    download_url: str
    size_bytes: int
    metadata: dict[str, JSONValue]


@dataclass(frozen=True, slots=True)
class TerrainSearch:
    """Complete bounded catalogue result and every page's provenance."""

    products: tuple[TerrainProduct, ...]
    requests: tuple[RequestRecord, ...]
    total: int


def _download_url(url: str) -> None:
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "prd-tnm.s3.amazonaws.com"
        or parsed.port not in (None, 443)
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or not parsed.path.startswith("/StagedProducts/Elevation/1m/")
        or not parsed.path.lower().endswith(".tif")
        or "/../" in parsed.path
    ):
        raise ValueError("Expected an official USGS 3DEP 1 m GeoTIFF URL")


class USGS3DEPClient:
    """Discover all matching project tiles before choosing one explicitly.

    There is no global or complete US 1 m coverage claim. Overlapping projects
    can differ in survey date, extent, datum and nodata. This connector selects
    the project-based 1 m dataset, not the newer seamless 1 m product. Configure
    a sufficient bounded download budget for the selected file's advertised size.
    """

    def __init__(self, http: HTTPClient) -> None:
        self.http = http

    def search(
        self,
        bounds_wgs84: Bounds,
        *,
        maximum_items: int = 1000,
        page_size: int = 100,
    ) -> TerrainSearch:
        validate_bounds(bounds_wgs84)
        if type(maximum_items) is not int or maximum_items < 1:
            raise ValueError("maximum_items must be a positive integer")
        if type(page_size) is not int or not 1 <= page_size <= 1000:
            raise ValueError("page_size must be an integer in 1..1000")
        products: list[TerrainProduct] = []
        records: list[RequestRecord] = []
        seen: set[str] = set()
        total: int | None = None
        while total is None or len(products) < total:
            response = self.http.get_json(
                BASE_URL,
                {
                    "datasets": DATASET,
                    "bbox": ",".join(map(str, bounds_wgs84)),
                    "max": str(min(page_size, maximum_items)),
                    "offset": str(len(products)),
                    "prodFormats": "GeoTIFF",
                },
                use_cache=False,
            )
            document = object_value(response.value)
            current = document.get("total")
            if type(current) is not int or current < 0 or document.get("errors"):
                raise ValueError("Invalid USGS catalogue response")
            if current > maximum_items:
                raise ValueError("USGS result exceeds maximum_items; narrow the area")
            if total is not None and total != current:
                raise ValueError("USGS catalogue changed during pagination; retry the search")
            total = current
            rows = document.get("items")
            if not isinstance(rows, list) or (not rows and len(products) < total):
                raise ValueError("Incomplete USGS catalogue page")
            records.append(response.record)
            for row in rows:
                item = object_value(row)
                source_id, title = item.get("sourceId"), item.get("title")
                url, size = item.get("downloadURL"), item.get("sizeInBytes")
                if (
                    not isinstance(source_id, str)
                    or not source_id
                    or source_id in seen
                    or not isinstance(title, str)
                    or not isinstance(url, str)
                    or type(size) is not int
                    or size < 1
                ):
                    raise ValueError("Invalid or repeated USGS product metadata")
                _download_url(url)
                seen.add(source_id)
                products.append(TerrainProduct(source_id, title, url, size, dict(item)))
            if len(products) > total:
                raise ValueError("USGS page exceeds advertised total")
        return TerrainSearch(tuple(products), tuple(records), total)

    def download_product(
        self,
        directory: Path,
        product: TerrainProduct,
        *,
        expected_sha256: str | None = None,
    ) -> tuple[Path, RequestRecord]:
        _download_url(product.download_url)
        if type(product.size_bytes) is not int or product.size_bytes < 1:
            raise ValueError("USGS product requires a positive advertised byte count")
        if product.size_bytes > self.http.config.maximum_response_bytes:
            raise ValueError(
                "Product exceeds HTTP byte budget; explicitly increase it or choose another"
            )
        path = Path(directory) / Path(urlsplit(product.download_url).path).name
        record = self.http.download_file(
            product.download_url,
            path,
            expected_sha256=expected_sha256,
            expected_size_bytes=product.size_bytes,
        )
        with rasterio.open(path) as dataset:
            if (
                dataset.count != 1
                or dataset.crs is None
                or not dataset.crs.is_projected
                or dataset.crs.linear_units not in {"metre", "meter"}
                or not all(math.isclose(x, 1.0) for x in dataset.res)
            ):
                raise ValueError("USGS response is not projected 1 m numeric terrain")
        return path, record
