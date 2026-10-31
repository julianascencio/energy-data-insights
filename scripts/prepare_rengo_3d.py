"""Explicit live acquisition of the Rengo terrain fixture; never run by tests/docs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import httpx
import numpy as np

from energy_data_retrieval.sources.copernicus_dem import (
    COPERNICUS_DEM_HOSTS,
    COPERNICUS_DEM_SOURCE,
    CopernicusDEMClient,
)
from energy_data_retrieval.terrain import describe_terrain, read_terrain, write_terrain_window
from energy_data_retrieval.transport import HTTPClient, HTTPConfig

ROOT = Path(__file__).resolve().parents[1]
BOUNDS = (-70.869, -34.457, -70.856, -34.444)
NOTICE = (
    "produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and "
    "© Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS "
    "by the European Union and ESA; all rights reserved"
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New fixture directory")
    parser.add_argument(
        "--download-directory",
        type=Path,
        required=True,
        help="Full tile cache, outside tracked examples",
    )
    parser.add_argument(
        "--proxy-from-env",
        action="store_true",
        help="Explicitly use HTTPS_PROXY if this environment requires it",
    )
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    args.download_directory.mkdir(parents=True, exist_ok=True)
    transport = (
        httpx.HTTPTransport(proxy=os.environ.get("HTTPS_PROXY")) if args.proxy_from_env else None
    )
    with HTTPClient(
        COPERNICUS_DEM_HOSTS,
        transport=transport,
        config=HTTPConfig(maximum_response_bytes=128 * 1024 * 1024),
    ) as http:
        tile, receipt = CopernicusDEMClient(http).download_tile(
            args.download_directory, latitude=-34.4515, longitude=-70.8615
        )
    window = read_terrain(tile, COPERNICUS_DEM_SOURCE, bounds_wgs84=BOUNDS)
    path = write_terrain_window(window, args.output / "el_mirlo_copernicus.tif")
    manifest = {
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "source": asdict(COPERNICUS_DEM_SOURCE),
        "request": asdict(receipt),
        "original_raster": asdict(describe_terrain(tile, COPERNICUS_DEM_SOURCE)),
        "requested_bounds_wgs84": BOUNDS,
        "fixture": path.name,
        "fixture_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "fixture_shape": list(window.elevation_m.shape),
        "fixture_bounds_native": window.metadata.bounds,
        "finite_fraction": float(np.isfinite(window.elevation_m).mean()),
        "elevation_range_m": [
            float(np.nanmin(window.elevation_m)),
            float(np.nanmax(window.elevation_m)),
        ],
        "notice": NOTICE,
        "limitations": "GLO-30 is a DSM including vegetation/buildings, not surveyed bare-earth "
        "ground. Native sampling is about 30 m; display interpolation adds no terrain detail. "
        "Vertical reference remains EGM2008.",
    }
    provenance = args.output / "terrain_provenance.json"
    provenance.write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n")
    original = ROOT / "examples/analysis/data"
    config = json.loads((original / "rengo_3d/scene_config.json").read_text())
    config["sha256"] = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (path, provenance)
    }
    config["counting_manifest_sha256"] = hashlib.sha256(
        (original / "rengo_modules/rengo_study.json").read_bytes()
    ).hexdigest()
    (args.output / "scene_config.json").write_text(json.dumps(config, indent=2) + "\n")
    print(f"Captured {path}; compare source hashes before replacing the pinned fixture.")


if __name__ == "__main__":
    main()
