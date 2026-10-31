"""IGN Spain WCS 2.0.1 numeric terrain subsets on the advertised 5 m grids."""

from __future__ import annotations

import hashlib
import json
import math
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from rasterio.io import MemoryFile
from rasterio.warp import transform_bounds

from energy_data_retrieval.terrain import Bounds, TerrainSource, validate_bounds
from energy_data_retrieval.transport import (
    HTTPClient,
    RequestRecord,
    RetrievalError,
    TextResponse,
    atomic_bytes,
)

IGN_TERRAIN_HOSTS = frozenset({"servicios.idee.es"})
BASE_URL = "https://servicios.idee.es/wcs-inspire/mdt"
REFERENCE_IDS = ("ign_mdt", "ign_terrain_wcs")
IGN_TERRAIN_SOURCE = TerrainSource(
    "ign_terrain",
    "IGN Spain MDT WCS (5 m)",
    "bare-earth DTM",
    "Spanish official orthometric heights; mainland/island height reference varies",
    REFERENCE_IDS,
)
_COVERAGES = {"canaries": ("Elevacion4083_5", 4083), "peninsula": ("Elevacion25830_5", 25830)}
_NS = {"gml": "http://www.opengis.net/gml/3.2", "wcs": "http://www.opengis.net/wcs/2.0"}


@dataclass(frozen=True, slots=True)
class CoverageDescription:
    """Advertised native grid and original XML, including provider metadata quirks."""

    coverage_id: str
    crs: str
    bounds: Bounds
    origin: tuple[float, float]
    spacing: tuple[float, float]
    xml: str
    request: RequestRecord


def _xml(text: str) -> ET.Element:
    if "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
        raise ValueError("Unexpected XML document type or entity")
    root = ET.fromstring(text)
    if root.tag.endswith("ExceptionReport"):
        raise RetrievalError("IGN returned a WCS exception; check coverage and bounds")
    return root


class IGNTerrainClient:
    """Bounded native-spacing WCS windows; never a colorized WMS map.

    The service exposes a 5 m grid. Finer CNIG 2 m and 0.5 m regional downloads
    are separate products, not returned by this endpoint. Output precision and
    nodata follow the actual TIFF, even if DescribeCoverage has generic units.
    """

    def __init__(self, http: HTTPClient) -> None:
        self.http = http

    def capabilities(self) -> TextResponse:
        return self.http.get_text(
            BASE_URL,
            {
                "SERVICE": "WCS",
                "VERSION": "2.0.1",
                "REQUEST": "GetCapabilities",
            },
        )

    def describe(
        self, region: Literal["canaries", "peninsula"] = "canaries"
    ) -> CoverageDescription:
        if region not in _COVERAGES:
            raise ValueError("region must be canaries or peninsula (mainland/Balearic grid)")
        coverage, epsg = _COVERAGES[region]
        response = self.http.get_text(
            BASE_URL,
            {
                "SERVICE": "WCS",
                "VERSION": "2.0.1",
                "REQUEST": "DescribeCoverage",
                "COVERAGEID": coverage,
            },
        )
        root = _xml(response.value)
        envelope = root.find(".//gml:Envelope", _NS)
        if envelope is None or not envelope.attrib.get("srsName", "").endswith(f"/{epsg}"):
            raise ValueError("Unexpected IGN coverage CRS")
        if root.findtext(".//wcs:CoverageId", namespaces=_NS) != coverage:
            raise ValueError("Unexpected IGN coverage identity")

        def pair(query: str) -> tuple[float, float]:
            parts = (root.findtext(query, namespaces=_NS) or "").split()
            if len(parts) != 2 or not all(math.isfinite(float(v)) for v in parts):
                raise ValueError("Invalid IGN grid metadata")
            return float(parts[0]), float(parts[1])

        lower, upper = pair(".//gml:lowerCorner"), pair(".//gml:upperCorner")
        vectors = [
            tuple(map(float, (e.text or "").split()))
            for e in root.findall(".//gml:offsetVector", _NS)
        ]
        if vectors != [(5.0, 0.0), (0.0, -5.0)] or envelope.attrib.get("axisLabels") != "x y":
            raise ValueError("Expected an advertised north-up 5 m IGN grid")
        return CoverageDescription(
            coverage,
            f"EPSG:{epsg}",
            (*lower, *upper),
            pair(".//gml:origin/gml:Point/gml:pos"),
            (5.0, 5.0),
            response.value,
            response.record,
        )

    def download_window(
        self,
        directory: Path,
        bounds_wgs84: Bounds,
        *,
        region: Literal["canaries", "peninsula"] = "canaries",
        maximum_pixels: int = 4_000_000,
    ) -> tuple[Path, RequestRecord]:
        validate_bounds(bounds_wgs84)
        if type(maximum_pixels) is not int or maximum_pixels < 1:
            raise ValueError("maximum_pixels must be a positive integer")
        description = self.describe(region)
        west, south, east, north = transform_bounds(
            "EPSG:4326",
            description.crs,
            *bounds_wgs84,
            densify_pts=21,
        )
        # Snap enclosing edges to the grid declared by DescribeCoverage.
        x0, y0 = description.origin[0] - 2.5, description.origin[1] + 2.5
        west, east = x0 + math.floor((west - x0) / 5) * 5, x0 + math.ceil((east - x0) / 5) * 5
        south, north = y0 + math.floor((south - y0) / 5) * 5, y0 + math.ceil((north - y0) / 5) * 5
        if not (
            description.bounds[0] <= west < east <= description.bounds[2]
            and description.bounds[1] <= south < north <= description.bounds[3]
        ):
            raise ValueError("Requested area lies outside the advertised IGN grid")
        width, height = round((east - west) / 5), round((north - south) / 5)
        if width * height > maximum_pixels:
            raise ValueError("IGN window exceeds maximum_pixels")
        parameters = {
            "SERVICE": "WCS",
            "VERSION": "2.0.1",
            "REQUEST": "GetCoverage",
            "COVERAGEID": description.coverage_id,
            "FORMAT": "image/tiff",
            "SUBSET": [f"x({west},{east})", f"y({south},{north})"],
        }
        response = self.http.request_bytes(BASE_URL, parameters)
        if response.value.lstrip().startswith(b"<"):
            _xml(response.value.decode("utf-8"))
            raise RetrievalError("IGN returned XML instead of numeric terrain")
        with MemoryFile(response.value) as memory, memory.open() as dataset:
            if (
                dataset.count != 1
                or str(dataset.crs) != description.crs
                or dataset.res != (5.0, 5.0)
                or dataset.width != width
                or dataset.height != height
                or any(
                    not math.isclose(a, b, abs_tol=1e-6, rel_tol=0)
                    for a, b in zip(dataset.bounds, (west, south, east, north), strict=True)
                )
            ):
                raise ValueError("IGN returned a different grid, resolution or extent")
        key = hashlib.sha256(json.dumps(parameters, sort_keys=True).encode()).hexdigest()[:16]
        path = Path(directory) / f"{description.coverage_id}_{key}.tif"
        atomic_bytes(path, response.value)
        atomic_bytes(
            path.with_suffix(".provenance.json"),
            json.dumps(
                {
                    "request": asdict(response.record),
                    "description_request": asdict(description.request),
                    "source": asdict(IGN_TERRAIN_SOURCE),
                    "description_xml": description.xml,
                },
                indent=2,
            ).encode(),
        )
        return path, response.record
