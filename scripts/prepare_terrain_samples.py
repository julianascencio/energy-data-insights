"""Explicit live capture of small, attributed native terrain windows for the gallery.

Run manually with --download-directory outside the repository. CI and gallery
execution use the committed crops and never invoke this script. No mosaicking,
interpolation, datum conversion, synthetic elevations or resampling is applied.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from energy_data_retrieval.sources.copernicus_dem import (
    COPERNICUS_DEM_HOSTS,
    COPERNICUS_DEM_SOURCE,
    CopernicusDEMClient,
)
from energy_data_retrieval.sources.ign_terrain import (
    IGN_TERRAIN_HOSTS,
    IGN_TERRAIN_SOURCE,
    IGNTerrainClient,
)
from energy_data_retrieval.sources.srtm import SRTM_HOSTS, SRTM_SOURCE, SRTMClient
from energy_data_retrieval.sources.usgs_3dep import (
    USGS_3DEP_HOSTS,
    USGS_3DEP_SOURCE,
    USGS3DEPClient,
)
from energy_data_retrieval.terrain import (
    TerrainSource,
    describe_terrain,
    read_terrain,
    write_terrain_window,
)
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, RequestRecord

TENERIFE = (-16.655, 28.245, -16.645, 28.255)
COLORADO = (-105.350, 39.996, -105.347, 39.999)
COPERNICUS_NOTICE = (
    "produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space "
    "GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved"
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download-directory", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, default=Path("examples/connectors/data"))
    parser.add_argument("--usgs-source-id", default="69c20ed7b66b01d6ebf33c9a")
    args = parser.parse_args()
    rows: list[dict[str, object]] = []
    output = args.output_directory
    output.mkdir(parents=True, exist_ok=True)

    def capture(
        path: Path,
        request: RequestRecord,
        source: TerrainSource,
        bounds: tuple[float, float, float, float] | None,
        place: str,
        extra: dict[str, object] | None = None,
    ) -> None:
        metadata = describe_terrain(path, source)
        window = read_terrain(path, source, bounds_wgs84=bounds)
        filename = f"terrain_{source.id}.tif"
        fixture = write_terrain_window(window, output / filename)
        content = fixture.read_bytes()
        if not np.isfinite(window.elevation_m).any():
            raise ValueError(f"{source.id} sample has no valid elevations")
        rows.append(
            {
                "source": asdict(source),
                "place": place,
                "request": asdict(request),
                "original_raster": asdict(metadata),
                "requested_bounds_wgs84": bounds,
                "fixture": filename,
                "fixture_sha256": hashlib.sha256(content).hexdigest(),
                "fixture_bytes": len(content),
                "fixture_shape": list(window.elevation_m.shape),
                "fixture_bounds_native": list(window.metadata.bounds),
                "valid_fraction": float(np.isfinite(window.elevation_m).mean()),
                "extra": extra or {},
            }
        )
        print(f"{source.id}: {window.elevation_m.shape}, {len(content):,} bytes", flush=True)

    with HTTPClient(SRTM_HOSTS) as http:
        path, record = SRTMClient(http).download_tile(
            args.download_directory, latitude=28.25, longitude=-16.65
        )
        capture(path, record, SRTM_SOURCE, TENERIFE, "Tenerife, Spain")
    with HTTPClient(COPERNICUS_DEM_HOSTS) as http:
        path, record = CopernicusDEMClient(http).download_tile(
            args.download_directory, latitude=28.25, longitude=-16.65
        )
        capture(
            path,
            record,
            COPERNICUS_DEM_SOURCE,
            TENERIFE,
            "Tenerife, Spain",
            {"attribution": COPERNICUS_NOTICE},
        )
    with HTTPClient(IGN_TERRAIN_HOSTS) as http:
        path, record = IGNTerrainClient(http).download_window(args.download_directory, TENERIFE)
        capture(
            path,
            record,
            IGN_TERRAIN_SOURCE,
            None,
            "Tenerife, Spain",
            {
                "wcs_provenance": json.loads(path.with_suffix(".provenance.json").read_text()),
                "requested_bounds_wgs84": TENERIFE,
                "attribution": (
                    "Contains geographic information from IGN Spain, MDT WCS, CC BY 4.0."
                ),
            },
        )
    with HTTPClient(
        USGS_3DEP_HOSTS, config=HTTPConfig(maximum_response_bytes=512 * 1024 * 1024)
    ) as http:
        client = USGS3DEPClient(http)
        result = client.search(COLORADO)
        matches = [p for p in result.products if p.source_id == args.usgs_source_id]
        if len(matches) != 1:
            raise ValueError(
                "Pinned USGS example project is unavailable; review metadata explicitly"
            )
        product = matches[0]
        path, record = client.download_product(args.download_directory, product)
        capture(
            path,
            record,
            USGS_3DEP_SOURCE,
            COLORADO,
            "Colorado, USA",
            {
                "product": asdict(product),
                "search_requests": [asdict(r) for r in result.requests],
                "search_total": result.total,
                "attribution": (
                    "USGS 3DEP, public domain. Project metadata retained; not a global 1 m grid."
                ),
            },
        )
    manifest = {
        "schema_version": 1,
        "captured_at_utc": datetime.now(UTC).isoformat(),
        "processing": (
            "Native enclosing windows; metres decoded; missing values become NaN; "
            "no resampling or vertical conversion."
        ),
        "samples": rows,
    }
    (output / "terrain_provenance.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    )


if __name__ == "__main__":
    main()
