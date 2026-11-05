"""Acquire native CHELSA temperature for continental Chile and its coastal islands."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import ssl
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import rasterio
from rasterio.features import geometry_mask
from shapely.geometry import box, mapping

from energy_analysis.chile_kgpv.prepare import BOUNDARY_SHA256
from energy_data_retrieval.sources.chelsa import CHELSAClient
from energy_data_retrieval.sources.natural_earth import NATURAL_EARTH_HOSTS, NaturalEarthClient
from energy_data_retrieval.transport import HTTPClient
from energy_methods.country_boundaries import load_country_boundaries

BOUNDS = (-76.0, -56.0, -66.0, -17.4)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=Path("artifacts/pvdeg-chile/raw"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/pvdeg-chile/inputs"))
    parser.add_argument("--source-manifest", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    # Reuse already verified whole-object ETags; this larger crop has new pixel hashes.
    pins = json.loads(Path("examples/analysis/kgpv_chile_provenance.json").read_text())
    records = {Path(r["url"]).name: r for r in pins["climate_subsets"]}
    expected = {}
    if args.source_manifest:
        expected = {r["month"]: r for r in json.loads(args.source_manifest.read_text())["months"]}
    proxy = os.environ.get("HTTPS_PROXY")
    with HTTPClient(
        allowed_hosts=NATURAL_EARTH_HOSTS,
        transport=httpx.HTTPTransport(proxy=proxy, verify=ssl.create_default_context()),
    ) as http:
        boundary = NaturalEarthClient(http).download_countries(
            args.cache / "boundaries", scale="10m", expected_sha256=BOUNDARY_SHA256
        )
    geometry = load_country_boundaries(boundary.shapefile, "CHL").geometry.intersection(
        box(*BOUNDS)
    )
    boundary_path = args.output / "pvdeg_chile_boundary.geojson"
    boundary_path.write_text(json.dumps(mapping(geometry)) + "\n")

    def acquire(month):
        name = f"CHELSA_tas_{month:02d}_1981-2010_V.2.1.tif"
        with httpx.Client(
            timeout=120, trust_env=False, proxy=proxy, verify=ssl.create_default_context()
        ) as http:
            source_path, record = CHELSAClient(http).download_window(
                args.cache / "climate",
                "tas",
                month,
                BOUNDS,
                expected_etag=records[name]["etag"],
                expected_pixels_sha256=expected.get(month, {})
                .get("source", {})
                .get("pixels_sha256"),
            )
        path = args.output / f"pvdeg_chile_tas_{month:02d}.tif"
        with rasterio.open(source_path) as source:
            values = source.read(1)
            land = geometry_mask(
                [mapping(geometry)], out_shape=source.shape, transform=source.transform, invert=True
            )
            values[~land] = 65535
            profile = {
                **source.profile,
                "compress": "deflate",
                "predictor": 2,
                "zlevel": 9,
                "tiled": True,
                "blockxsize": 256,
                "blockysize": 256,
            }
            with rasterio.open(path, "w", **profile) as target:
                target.write(values, 1)
                target.scales, target.offsets = source.scales, source.offsets
                target.update_tags(**source.tags(), month=str(month))
        print(f"Month {month}: {path.stat().st_size:,} bytes", flush=True)
        return {
            "month": month,
            "file": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "source": record,
        }

    with ThreadPoolExecutor(max_workers=2) as pool:
        months = list(pool.map(acquire, range(1, 13)))
    manifest = {
        "description": "Continental Chile and coastal islands: native CHELSA inputs for PVDeg",
        "period": [1981, 2010],
        "grid_arcseconds": 30,
        "bounds": list(BOUNDS),
        "months": months,
        "climate_source": "CHELSA v2.1",
        "climate_doi": "10.16904/envidat.228",
        "climate_license": "CC0-1.0",
        "boundary_file": boundary_path.name,
        "boundary_sha256": hashlib.sha256(boundary_path.read_bytes()).hexdigest(),
        "boundary_archive_sha256": BOUNDARY_SHA256,
        "boundary_source": "Natural Earth Admin 0, 1:10 million, public domain",
        "coverage": (
            "Continental Chile, Chiloe, Tierra del Fuego and coastal archipelagos; "
            "excludes Pacific oceanic islands and Antarctica"
        ),
        "scenario": {
            "activation_energy_kj_mol": 60,
            "module_offset_c": 20,
            "reference_temperature_c": 25,
            "humidity_exponent": 0,
            "irradiance_exponent": 0,
        },
        "evidence": "Modeled historical climatology and assumed module temperature offset",
        "resolution_limit": (
            "Native 30-arcsecond spacing; not validated site-level degradation accuracy"
        ),
    }
    (args.output / "pvdeg_chile_provenance.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
