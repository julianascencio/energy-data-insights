"""Reproduce native-resolution Canary KGPV maps from pinned public source bytes."""

from __future__ import annotations

import argparse
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from xml.etree import ElementTree

import httpx
import rasterio

from energy_analysis.canary_kgpv.pipeline import ISLANDS, REFERENCE_IDS, file_sha256, prepare_maps
from energy_data_retrieval.sources.canary_clim import CANARY_CLIM_HOSTS, CanaryClimClient
from energy_data_retrieval.sources.global_solar_atlas import (
    GSA_HOSTS,
    GlobalSolarAtlasClient,
    SolarAtlasTransport,
)
from energy_data_retrieval.transport import HTTPClient, HTTPConfig

GSA_ATTRIBUTION = (
    "Data obtained from the Global Solar Atlas 2.0, a free, web-based application "
    "developed and operated by Solargis s.r.o. on behalf of the World Bank Group, "
    "utilizing Solargis data, with funding provided by the Energy Sector Management "
    "Assistance Program (ESMAP). https://globalsolaratlas.info"
)


def write_manifest(raw: Path, output: Path, records: dict) -> dict:
    """Keep source periods, licenses, source grids and hashes with derived maps."""
    source_records = [json.loads(p.read_text()) for p in sorted(raw.glob("*.tif.download.json"))]
    source_records += [
        json.loads(p.read_text()) for p in sorted(raw.glob("Spain_*.zip.download.json"))
    ]
    if len(source_records) != 25:
        raise ValueError("Expected exactly 24 climate files and one solar archive")
    # Read complete mixed-content license text, preserving the provider's addition.
    metadata = ElementTree.parse(raw / "GHI.tif.xml")
    rights = next(
        "".join(e.itertext())
        for e in metadata.iter()
        if e.tag.endswith("CharacterString") and (e.text or "").startswith("Copyright:")
    )
    with rasterio.open(raw / "CHELSACanaryClim_tas_01_1979-2013_V.1.0.tif") as climate:
        climate_grid = {
            "shape": list(climate.shape),
            "transform": list(climate.transform),
            "crs": str(climate.crs),
            "scale": climate.scales[0],
            "offset": climate.offsets[0],
            "encoded_nodata": climate.nodata,
        }
    with rasterio.open(raw / "GHI.tif") as solar:
        solar_grid = {
            "shape": list(solar.shape),
            "transform": list(solar.transform),
            "crs": str(solar.crs),
            "encoded_nodata": solar.nodata,
            "sha256": file_sha256(raw / "GHI.tif"),
            "metadata_sha256": file_sha256(raw / "GHI.tif.xml"),
        }
    sample_path = output / "kgpv_canary_samples.csv"
    manifest = {
        "description": "Exploratory Canary Islands KGPV on native CanaryClim climate pixels",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "climate_source": "CHELSACanaryClim-climatologies v1.0 (2025 COG release)",
        "climate_baseline": [1979, 2013],
        "solar_source": "Global Solar Atlas 2.0 (2019 Spain archive)",
        "solar_baseline": [1994, 2018],
        "baseline_policy": "Mixed periods; no claim of a common climatological baseline",
        "native_climate_grid": climate_grid,
        "native_solar_grid": solar_grid,
        "resolution_note": (
            "Native climate COG spacing is 0.00004684877106756975 degrees (about 5.2 m "
            "north-south and 4.6 m east-west here). This is pixel spacing, not validated "
            "5 m climate accuracy. The published model comparison used 100 m. Solar "
            "information remains 0.0025 degrees (9 arcseconds, nominally 250 m)."
        ),
        "preprocessing": [
            "Validate all 24 monthly COGs: CRS, grid, month, variable, unit, version and scale.",
            "Mask encoded nodata, apply each band's scale/offset; convert K to Celsius.",
            "Precipitation kg m-2 month-1 equals mm per climatological month.",
            "GSA GHI is already annual irradiation in kWh m-2; do not multiply by 365 again.",
            "Nearest GHI source cell at each native climate pixel; no coastal extrapolation.",
            "Apply existing classify_kgpv with the fixed 2019 thresholds, in bounded tiles.",
            "Retain January temperature's valid footprint in band 2; missing inputs give class 0.",
            "The seven disjoint windows include La Graciosa/Chinijo and Lobos.",
            "Nearest-class overviews are for display only; band 1 retains native results.",
        ],
        "units": {"temperature": "degC", "precipitation": "mm month-1", "annual_ghi": "kWh m-2"},
        "islands": records,
        "sample_file": sample_path.name,
        "sample_sha256": file_sha256(sample_path),
        "sources": source_records,
        "licenses": {
            "climate": "CC0 1.0; https://doi.org/10.16904/envidat.692",
            "solar": rights,
            "solar_attribution": GSA_ATTRIBUTION,
            "source_terms": "https://globalsolaratlas.info/support/terms-of-use",
            "changes": (
                "Regional extraction, nearest-cell sampling and derived KGPV classification."
            ),
        },
        "reference_ids": list(REFERENCE_IDS),
        "software": {p: version(p) for p in ("numpy", "pandas", "rasterio", "pyproj")},
    }
    (output / "kgpv_canary_provenance.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=Path("artifacts/canary-kgpv/raw"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/canary-kgpv/native"))
    parser.add_argument(
        "--source-manifest",
        type=Path,
        default=Path("examples/analysis/kgpv_canary_provenance.json"),
    )
    parser.add_argument("--islands", nargs="+", choices=tuple(ISLANDS), default=list(ISLANDS))
    parser.add_argument("--tile-size", type=int, default=512)
    parser.add_argument("--workers", type=int, choices=(1, 2), default=2)
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--use-environment-proxy", action="store_true")
    args = parser.parse_args()
    pinned = json.loads(args.source_manifest.read_text())
    sources = {Path(r["endpoint"]).name: r for r in pinned["sources"]}
    total = sum(r["size_bytes"] for r in sources.values())
    print(
        f"24 climate COGs + 1 solar archive: {total / 1e9:.2f} GB if uncached; "
        f"{len(args.islands)} native-grid island groups.",
        flush=True,
    )
    if args.plan_only:
        return
    proxy = os.environ.get("HTTPS_PROXY") if args.use_environment_proxy else None
    with HTTPClient(
        allowed_hosts=CANARY_CLIM_HOSTS,
        config=HTTPConfig(maximum_response_bytes=160_000_000, timeout_seconds=120),
        transport=httpx.HTTPTransport(proxy=proxy),
    ) as http:
        client = CanaryClimClient(http)

        def download(pair):
            variable, month = pair
            name = f"CHELSACanaryClim_{variable}_{month:02d}_1979-2013_V.1.0.tif"
            return client.download_month(
                args.cache, variable, month, expected_sha256=sources[name]["sha256"]
            )

        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            list(pool.map(download, [(v, m) for m in range(1, 13) for v in ("tas", "pr")]))
    with HTTPClient(
        allowed_hosts=GSA_HOSTS,
        config=HTTPConfig(maximum_response_bytes=110_000_000, timeout_seconds=120),
        transport=SolarAtlasTransport(httpx.HTTPTransport(proxy=proxy)),
    ) as http:
        GlobalSolarAtlasClient(http).download_spain_ghi(args.cache)
    records = prepare_maps(
        args.cache, args.output, islands=tuple(args.islands), tile_size=args.tile_size
    )
    write_manifest(args.cache, args.output, records)


if __name__ == "__main__":
    main()
