"""Prepare the attributed, offline world basemap for connector coverage examples.

Run explicitly from a repository checkout; ordinary gallery builds never call
this script or download map data. The source archive is pinned to Natural Earth
5.1.1, 1:110 million, with all retained polygon vertices unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import httpx
import shapefile
from shapely.geometry import mapping

from energy_data_retrieval.sources.natural_earth import NATURAL_EARTH_HOSTS, NaturalEarthClient
from energy_data_retrieval.transport import HTTPClient, HTTPConfig
from energy_methods.country_boundaries import load_country_boundaries

REFERENCE_IDS = ("natural_earth_countries",)
SOURCE_VERSION = "5.1.1"
SOURCE_SHA256 = "0f243aeac8ac6cf26f0417285b0bd33ac47f1b5bdb719fd3e0df37d03ea37110"
PROPERTY_FIELDS = (
    "ADM0_A3",
    "ADMIN",
    "ISO_A2",
    "ISO_A3",
    "ISO_A2_EH",
    "ISO_A3_EH",
    "NAME",
    "NAME_LONG",
)
FIXTURE_NAME = "generation_coverage_world.geojson"
MANIFEST_NAME = "generation_coverage_provenance.json"


def prepare_basemap(output: Path, cache: Path, *, use_environment_proxy: bool = False) -> Path:
    """Retrieve the pinned archive, validate 176 country polygons, and save GeoJSON.

    Antarctica is excluded explicitly because its unsplit world-spanning ring
    does not satisfy the existing country-map antimeridian contract. The other
    176 source features require no geometric repair or simplification. The map
    is a geographic backdrop; political contours do not define grid territories.
    """
    proxy = os.environ.get("HTTPS_PROXY") if use_environment_proxy else None
    with HTTPClient(
        NATURAL_EARTH_HOSTS,
        config=HTTPConfig(maximum_response_bytes=5_000_000),
        transport=httpx.HTTPTransport(proxy=proxy),
    ) as http:
        download = NaturalEarthClient(http).download_countries(
            cache, scale="110m", expected_sha256=SOURCE_SHA256
        )
    source_manifest = json.loads(download.manifest.read_text(encoding="utf-8"))
    if source_manifest["version"] != SOURCE_VERSION:
        raise ValueError("The world basemap must use the reviewed Natural Earth 5.1.1 source")

    source_properties = {}
    with shapefile.Reader(str(download.shapefile), encoding="utf-8") as reader:
        for record in reader.iterShapeRecords():
            properties = record.__geo_interface__["properties"]
            code = str(properties["ADM0_A3"])
            if code in source_properties:
                raise ValueError("Natural Earth country identifiers must be unique")
            source_properties[code] = {
                key: properties[key] for key in PROPERTY_FIELDS if key in properties
            }
    if len(source_properties) != 177 or "ATA" not in source_properties:
        raise ValueError("Unexpected feature inventory in the pinned Natural Earth archive")

    codes = [code for code in source_properties if code != "ATA"]
    countries = load_country_boundaries(download.shapefile, codes)
    document = {
        "type": "FeatureCollection",
        "metadata": {
            "source": "Natural Earth Admin 0 - Countries",
            "version": SOURCE_VERSION,
            "scale": "1:110 million",
            "coordinate_reference_system": "EPSG:4326",
            "boundary_policy": "Natural Earth default de facto boundaries",
            "excluded_codes": ["ATA"],
        },
        "features": [
            {
                "type": "Feature",
                "properties": source_properties[country.code],
                "geometry": mapping(country.geometry),
            }
            for country in countries.countries
        ],
    }
    content = (
        json.dumps(document, ensure_ascii=False, allow_nan=False, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    if len(content) > 2_000_000:
        raise ValueError("Offline basemap exceeds the repository's 2 MB source-file limit")
    output.mkdir(parents=True, exist_ok=True)
    fixture = output / FIXTURE_NAME
    fixture.write_bytes(content)
    manifest = {
        "schema_version": 1,
        "source": source_manifest["source"],
        "version": SOURCE_VERSION,
        "scale": "110m",
        "scale_meaning": "1:110 million map scale, not metre accuracy",
        "license": source_manifest["license"],
        "terms_url": source_manifest["terms_url"],
        "boundary_policy": source_manifest["boundary_policy"],
        "request": source_manifest["request"],
        "source_files_sha256": source_manifest["files_sha256"],
        "fixture": FIXTURE_NAME,
        "fixture_sha256": hashlib.sha256(content).hexdigest(),
        "fixture_bytes": len(content),
        "source_feature_count": len(source_properties),
        "retained_feature_count": len(countries.countries),
        "retained_properties": list(PROPERTY_FIELDS),
        "coordinate_reference_system": "EPSG:4326",
        "excluded_features": [
            {
                "ADM0_A3": "ATA",
                "ADMIN": "Antarctica",
                "reason": (
                    "Its unsplit world-spanning ring fails the existing country-map "
                    "antimeridian contract; the generation coverage view omits Antarctica"
                ),
            }
        ],
        "transformations": [
            "Read source WGS84 shapefile through the existing country-boundary loader",
            "Exclude Antarctica; retain all other source polygon parts, holes and vertices",
            "Retain only country identifiers, names and source ISO aliases",
            "Serialize compact UTF-8 RFC 7946 GeoJSON without geometric simplification or repair",
        ],
        "interpretation": (
            "Country polygons are a geographic backdrop, not electrical-system boundaries "
            "or evidence that a connector supplies every location in a shaded country"
        ),
        "reference_ids": list(REFERENCE_IDS),
    }
    (output / MANIFEST_NAME).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return fixture


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=root / "examples/connectors/data")
    parser.add_argument(
        "--cache", type=Path, default=root / "artifacts/connector-coverage/boundaries"
    )
    parser.add_argument("--use-environment-proxy", action="store_true")
    args = parser.parse_args()
    fixture = prepare_basemap(
        args.output, args.cache, use_environment_proxy=args.use_environment_proxy
    )
    print(f"Saved {fixture} with 176 unchanged source country geometries")


if __name__ == "__main__":
    main()
