"""Capture the Icor solar-farm example near Candelaria (Python 3.13).

Live acquisition is explicit; the gallery and tests use the saved inputs.
Caches retain their original acquisition/retrieval dates and checksums.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import shutil
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from pyproj import Geod
from shapely.geometry import Point, Polygon, mapping

from energy_data_retrieval.sources.natural_earth import NaturalEarthClient
from energy_data_retrieval.sources.orbitalpv_imagery import (
    IMAGERY_HOSTS,
    ORBITALPV_COMMIT,
    OrbitalPVImageryClient,
    describe_asset,
    select_finest,
)
from energy_data_retrieval.transport import HTTPClient
from energy_methods.country_boundaries import load_country_boundaries, polygons

CATALOGUE = (
    "https://datos.tenerife.es/ckan/dataset/fa991fa9-a113-452c-9f1b-331b1ffefbe1/"
    "resource/2782375b-f2c7-4a05-a685-4eee554a6b1b/download/"
    "plantas-fotovoltaicas-y-parques-eolicos.geojson"
)
OSM_BOUNDS = (-16.447, 28.192, -16.439, 28.198)
FARM_BOUNDS = (-16.4431, 28.1935, -16.4410, 28.1953)
CANDELARIA = (-16.370, 28.355)  # Rounded town-centre reference, not the user's home.


def copy_verified(source: Path, target: Path) -> None:
    """Copy captured bytes and their unchanged provenance only after validation."""
    sidecar = source.with_suffix(source.suffix + ".meta.json")
    metadata = json.loads(sidecar.read_text())
    if hashlib.sha256(source.read_bytes()).hexdigest() != metadata["sha256"]:
        raise ValueError("Cached input checksum mismatch")
    shutil.copyfile(source, target)
    shutil.copyfile(sidecar, target.with_suffix(target.suffix + ".meta.json"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--download-directory", type=Path, required=True)
    parser.add_argument("--osm-cache", type=Path)
    parser.add_argument("--pnoa-cache", type=Path)
    args = parser.parse_args()
    output = args.output_directory
    output.mkdir(parents=True, exist_ok=True)
    if any(output.glob("candelaria_*")):
        raise FileExistsError("Use a fresh directory; existing example inputs are not overwritten")
    opv = importlib.import_module("orbitalpv")
    research = importlib.import_module("orbitalpv.ground_research")
    hosts = IMAGERY_HOSTS | {"datos.tenerife.es", "naturalearth.s3.amazonaws.com"}
    with HTTPClient(frozenset(hosts)) as http:
        result = http.get_json(CATALOGUE, {})
        catalogue = cast(dict[str, Any], result.value)
        assert isinstance(catalogue, dict) and isinstance(catalogue["features"], list)
        catalogue_name = "candelaria_catalogue.geojson"
        (output / catalogue_name).write_bytes(
            json.dumps(catalogue, separators=(",", ":"), allow_nan=False).encode()
        )
        matches = [
            feature
            for feature in catalogue["features"]
            if feature["properties"]["instalacion_id"] == 6
        ]
        if len(matches) != 1 or matches[0]["properties"]["instalacion_nombre"] != "Planta Icor":
            raise ValueError("Review the source catalogue: pinned Icor identity changed")
        official = matches[0]
        point = Point(official["geometry"]["coordinates"])
        osm_path = output / "candelaria_osm.json"
        if args.osm_cache:
            copy_verified(args.osm_cache, osm_path)
        with opv.OpenStreetMapEnergyConnector() as connector:
            osm = connector.fetch_energy_features(
                bbox=OSM_BOUNDS, sources=("solar",), cache_path=osm_path
            )
        candidates = []
        for feature in osm["elements"]:
            tags = feature.get("tags", {})
            if tags.get("power") != "plant" or tags.get("plant:method") != "photovoltaic":
                continue
            boundary = Polygon([(p["lon"], p["lat"]) for p in feature["geometry"]])
            if boundary.is_valid and boundary.covers(point):
                candidates.append((feature, boundary))
        if len(candidates) != 1:
            raise ValueError("Official Icor point must match exactly one mapped PV plant")
        feature, boundary = candidates[0]
        connector = OrbitalPVImageryClient(http)
        found = connector.search_sentinel(
            FARM_BOUNDS,
            time_min="2026-08-01",
            time_max="2026-08-06",
            max_cloud_cover=10,
            max_items=10,
            cache_path=str(output / "candelaria_scenes.json"),
        )
        scene = select_finest(found, asset="visual")
        samples = []
        for asset in ("visual", "red", "scl"):
            image = connector.read_image(scene, FARM_BOUNDS, asset=asset)
            filename = f"candelaria_{asset}.tif"
            image.save_geotiff(output / filename)
            samples.append(
                {"fixture": filename, "resolution": asdict(describe_asset(scene, asset))}
            )
        aerial = output / "candelaria_pnoa.png"
        if args.pnoa_cache:
            copy_verified(args.pnoa_cache, aerial)
        else:
            with research.PNOAConnector() as connector:
                connector.download_map(
                    aerial, bbox=FARM_BOUNDS, layer="OI.OrthoimageCoverage", width=768, height=768
                )
        aerial_meta = json.loads(aerial.with_suffix(".png.meta.json").read_text())
        if tuple(aerial_meta["bbox_wgs84"]) != FARM_BOUNDS:
            raise ValueError("Aerial cache must match the exact farm viewport")
        countries = NaturalEarthClient(http).download_countries(
            args.download_directory, scale="10m"
        )
        spain = load_country_boundaries(countries.shapefile, "ESP")
        tenerife = [polygon for polygon in polygons(spain.geometry) if polygon.covers(point)]
        if len(tenerife) != 1:
            raise ValueError("The farm point must identify one Tenerife locator contour")
        locator = {
            "type": "Feature",
            "properties": {"name": "Tenerife"},
            "geometry": mapping(tenerife[0]),
        }
        (output / "candelaria_tenerife.geojson").write_text(json.dumps(locator, indent=2) + "\n")
        site = {
            "schema_version": 1,
            "prepared_at_utc": datetime.now(UTC).isoformat(),
            "orbitalpv_commit": ORBITALPV_COMMIT,
            "official_site": official,
            "catalogue_request": asdict(result.record),
            "catalogue_fixture": catalogue_name,
            "catalogue_license": "CC BY; Cabildo Insular de Tenerife / ITER",
            "candelaria_reference_lonlat": CANDELARIA,
            "distance_basis": (
                "WGS84 ellipsoidal straight-line distance from rounded town centre; "
                "not a road distance or nearest-farm claim"
            ),
            "distance_km": Geod(ellps="WGS84").inv(*CANDELARIA, point.x, point.y)[2] / 1000,
            "footprint": {
                "type": "Feature",
                "properties": {
                    "osm_type": feature["type"],
                    "osm_id": feature["id"],
                    "original_tags": feature["tags"],
                    "join": (
                        "Unique OSM photovoltaic plant polygon containing the official catalogue "
                        "point; spatial association, not a surveyed or operator-validated boundary"
                    ),
                },
                "geometry": mapping(boundary),
            },
            "footprint_license": "ODbL-1.0; © OpenStreetMap contributors",
            "satellite_samples": samples,
            "aerial_fixture": aerial.name,
            "aerial_attribution": (
                "PNOA/IGN; aerial orthophotography, rendered WMS display; "
                "native resolution and capture date not established by this request"
            ),
            "locator_source": json.loads(countries.manifest.read_text()),
            "locator_fixture_sha256": hashlib.sha256(
                (output / "candelaria_tenerife.geojson").read_bytes()
            ).hexdigest(),
            "farm_bounds_wgs84": FARM_BOUNDS,
        }
        (output / "candelaria_site.json").write_text(
            json.dumps(site, indent=2, ensure_ascii=False) + "\n"
        )
        print(f"Planta Icor: {site['distance_km']:.2f} km from Candelaria; OSM {feature['id']}")


if __name__ == "__main__":
    main()
