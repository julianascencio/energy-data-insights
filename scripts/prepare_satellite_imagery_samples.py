"""Explicit live capture of small native satellite windows; never run by CI.

Requires Python 3.13 and the imagery extra. The output contains public provider
pixels with their own licences, separate from the code licence. Orbital PV
performs all pixel reads and writes without resampling or sharpening.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from energy_data_retrieval.sources.orbitalpv_imagery import (
    IMAGERY_HOSTS,
    ORBITALPV_COMMIT,
    OrbitalPVImageryClient,
    describe_asset,
    select_finest,
)
from energy_data_retrieval.transport import HTTPClient

TENERIFE = (-16.447, 28.192, -16.439, 28.198)
ALTADENA = (-118.1220, 34.2100, -118.1205, 34.2115)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_directory
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    searches = {}
    with HTTPClient(IMAGERY_HOSTS) as http:
        client = OrbitalPVImageryClient(http)
        sentinel = client.search_sentinel(
            TENERIFE,
            time_min="2026-08-01",
            time_max="2026-08-06",
            max_items=10,
            max_cloud_cover=10,
        )
        maxar = client.search_maxar(
            "WildFires-LosAngeles-Jan-2025",
            ALTADENA,
            time_min="2025-01-08",
            time_max="2025-01-09",
        )
        for label, search, asset in (
            ("tenerife", sentinel, "visual"),
            ("altadena", maxar, "pan_analytic"),
        ):
            item = select_finest(search, asset=asset)
            searches[label] = asdict(search)
            assets = ("visual", "red", "scl") if label == "tenerife" else ("pan_analytic", "visual")
            for asset in assets:
                image = client.read_image(item, search.bounds_wgs84, asset=asset)
                if image.data.count() == 0:
                    raise ValueError("Example crop contains only missing pixels")
                path = output / f"imagery_{label}_{asset}.tif"
                image.save_geotiff(path)
                rows.append(
                    {
                        "fixture": path.name,
                        "place": "Icor area, Tenerife, Spain"
                        if label == "tenerife"
                        else "Altadena, California, USA",
                        "resolution": asdict(describe_asset(item, asset)),
                        "shape": list(image.data.shape),
                        "valid_fraction": image.data.count() / image.data.size,
                        "attribution": (
                            "Contains modified Copernicus Sentinel data (2026), processed by ESA; "
                            "distributed by Element 84 Earth Search."
                        )
                        if label == "tenerife"
                        else (
                            "© Maxar/Vantor. Open Data Program, CC BY-NC 4.0. "
                            "Cropped native pixels; no resampling."
                        ),
                        "licence_url": "https://dataspace.copernicus.eu/terms-and-conditions"
                        if label == "tenerife"
                        else "https://creativecommons.org/licenses/by-nc/4.0/",
                    }
                )
                print(
                    f"{path.name}: {image.data.shape}, valid {rows[-1]['valid_fraction']:.1%}",
                    flush=True,
                )
    manifest = {
        "schema_version": 1,
        "captured_at_utc": datetime.now(UTC).isoformat(),
        "orbitalpv_commit": ORBITALPV_COMMIT,
        "processing": (
            "Native enclosing pixel windows. No resampling, sharpening, reflectance "
            "conversion or cloud masking. TIFF sidecars preserve full STAC, masks, "
            "calibration and SHA-256."
        ),
        "samples": rows,
    }
    (output / "imagery_provenance.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (output / "imagery_searches.json").write_text(json.dumps(searches, indent=2) + "\n")


if __name__ == "__main__":
    main()
