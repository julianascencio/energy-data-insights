"""Read, select and export country polygons, with explicit coordinate systems."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

import numpy as np
import shapefile
from pyproj import CRS, Transformer
from shapely import get_coordinates, transform, union_all
from shapely.geometry import MultiPolygon, Polygon, mapping, shape
from shapely.geometry.polygon import orient

REFERENCE_IDS = ("natural_earth_countries", "shapely_documentation", "pyproj_documentation")


@dataclass(frozen=True)
class CountryBoundary:
    code: str
    name: str
    geometry: Polygon | MultiPolygon
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class CountrySelection:
    """Selected countries in EPSG:4326, including all supplied islands and holes."""

    countries: tuple[CountryBoundary, ...]
    source: str = "caller-provided polygons"

    def __post_init__(self) -> None:
        if not self.countries or len({c.code for c in self.countries}) != len(self.countries):
            raise ValueError("Select at least one country with unique codes")
        for country in self.countries:
            _check_geometry(country.geometry)

    @cached_property
    def geometry(self) -> Polygon | MultiPolygon:
        return union_all([country.geometry for country in self.countries])

    @property
    def codes(self) -> tuple[str, ...]:
        return tuple(country.code for country in self.countries)


def _check_geometry(geometry: Polygon | MultiPolygon) -> None:
    if not isinstance(geometry, (Polygon, MultiPolygon)) or geometry.is_empty:
        raise ValueError("Country boundaries must be nonempty Polygon or MultiPolygon geometries")
    coordinates = get_coordinates(geometry)
    if (
        not np.isfinite(coordinates).all()
        or np.any(np.abs(coordinates[:, 0]) > 180 + 1e-8)
        or np.any(np.abs(coordinates[:, 1]) > 90 + 1e-8)
        or not geometry.is_valid
    ):
        raise ValueError("Country geometry must be valid and geographic (EPSG:4326)")
    for polygon in polygons(geometry):
        for ring in (polygon.exterior, *polygon.interiors):
            if np.any(np.abs(np.diff(np.asarray(ring.coords)[:, 0])) > 180):
                raise ValueError("Split country rings at the antimeridian before mapping")


def polygons(geometry: Polygon | MultiPolygon) -> tuple[Polygon, ...]:
    """Polygon parts, preserving holes; useful for outlines and plotting paths."""
    return (geometry,) if isinstance(geometry, Polygon) else tuple(geometry.geoms)


def load_country_boundaries(
    path: Path,
    countries: str | Sequence[str],
    *,
    code_field: str = "ADM0_A3",
    name_field: str = "ADMIN",
    crs: str | None = None,
) -> CountrySelection:
    """Select exact case-insensitive names or codes from .shp or RFC 7946 GeoJSON.

    Natural Earth ADM0_A3/ADMIN are defaults; ISO_A2/ISO_A3 and their _EH variants,
    NAME and NAME_LONG are aliases. No fuzzy matching; unknown/ambiguous names
    fail. Shapefiles require .prj unless crs is supplied. Projected inputs are
    transformed to longitude/latitude with always_xy=True. GeoJSON defaults to
    RFC 7946 WGS84 and rejects legacy embedded CRS unless explicitly overridden.
    Invalid or unsplit antimeridian polygons fail rather than silently changing
    country topology. Only selected records are transformed and validated.
    """
    path = Path(path)
    requested = [countries] if isinstance(countries, str) else list(countries)
    if not requested or any(not isinstance(c, str) or not c.strip() for c in requested):
        raise ValueError("Provide one country name/code or a nonempty sequence")
    if path.suffix.lower() == ".shp":
        projection = path.with_suffix(".prj")
        if crs is None and not projection.exists():
            raise ValueError("Shapefile needs a .prj file or explicit crs")
        source_crs = CRS.from_user_input(crs or projection.read_text())
        encoding_file = path.with_suffix(".cpg")
        encoding = encoding_file.read_text().strip() if encoding_file.exists() else "utf-8"
        with shapefile.Reader(str(path), encoding=encoding) as reader:
            features = [record.__geo_interface__ for record in reader.iterShapeRecords()]
    elif path.suffix.lower() in {".json", ".geojson"}:
        document = json.loads(path.read_text(encoding="utf-8"))
        if document.get("type") != "FeatureCollection":
            raise ValueError("Country GeoJSON must be a FeatureCollection")
        if "crs" in document and crs is None:
            raise ValueError("Legacy GeoJSON CRS requires an explicit crs argument")
        source_crs = CRS.from_user_input(crs or "EPSG:4326")
        features = document["features"]
    else:
        raise ValueError("Country boundary path must be .shp or .geojson")
    aliases = (
        code_field,
        name_field,
        "ISO_A2",
        "ISO_A3",
        "ISO_A2_EH",
        "ISO_A3_EH",
        "NAME",
        "NAME_LONG",
    )
    matches: dict[str, list[int]] = {}
    for index, feature in enumerate(features):
        properties = feature["properties"]
        for key in {str(properties.get(field, "")).strip().casefold() for field in aliases}:
            if key not in {"", "-99", "none"}:
                matches.setdefault(key, []).append(index)
    indices = []
    for query in requested:
        found = matches.get(query.strip().casefold(), [])
        if len(found) != 1:
            raise ValueError(f"Unknown or ambiguous country {query!r}; use a unique source code")
        if found[0] not in indices:
            indices.append(found[0])
    transformer = Transformer.from_crs(source_crs, "EPSG:4326", always_xy=True)
    selected = []
    for index in indices:
        feature = features[index]
        properties = feature["properties"]
        if not properties.get(code_field) or not properties.get(name_field):
            raise ValueError("Selected feature is missing the requested country code/name fields")
        geometry = shape(feature["geometry"])
        if not source_crs.equals(CRS.from_epsg(4326), ignore_axis_order=True):
            geometry = transform(geometry, transformer.transform, interleaved=False)
        _check_geometry(geometry)
        selected.append(
            CountryBoundary(
                str(properties[code_field]),
                str(properties[name_field]),
                geometry,
                tuple(str(properties[field]) for field in aliases if properties.get(field)),
            )
        )
    return CountrySelection(tuple(selected), path.name)


def write_country_boundaries(selection: CountrySelection, path: Path) -> Path:
    """Export selected complete contours as GeoJSON or .shp with CRS companions.

    No simplification or mainland-only filtering. Shapefile outputs include
    .shp/.shx/.dbf/.prj/.cpg; keep all five together when moving the file.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() in {".json", ".geojson"}:
        features = []
        for country in selection.countries:
            features.append(
                {
                    "type": "Feature",
                    "properties": {
                        "ADM0_A3": country.code,
                        "ADMIN": country.name,
                    },
                    "geometry": mapping(country.geometry),
                }
            )
        path.write_text(
            json.dumps(
                {
                    "type": "FeatureCollection",
                    "features": features,
                    "metadata": {"source": selection.source, "crs": "EPSG:4326"},
                },
                allow_nan=False,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
    elif path.suffix.lower() == ".shp":
        with shapefile.Writer(str(path), shapeType=shapefile.POLYGON, encoding="utf-8") as writer:
            writer.field("ADM0_A3", "C", size=32)
            writer.field("ADMIN", "C", size=160)
            for country in selection.countries:
                parts = []
                for polygon in polygons(country.geometry):
                    polygon = orient(polygon, sign=-1.0)  # ESRI: clockwise outer ring.
                    parts.extend(
                        [
                            list(polygon.exterior.coords),
                            *[list(r.coords) for r in polygon.interiors],
                        ]
                    )
                writer.poly(parts)
                writer.record(country.code, country.name)
        path.with_suffix(".prj").write_text(CRS.from_epsg(4326).to_wkt("WKT1_ESRI"))
        path.with_suffix(".cpg").write_text("UTF-8\n")
    else:
        raise ValueError("Choose .shp or .geojson for country contours")
    return path
