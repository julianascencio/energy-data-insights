"""Acquire pinned regional sources and reproduce the mainland Chile KGPV map."""

from __future__ import annotations

import argparse
import json
import os
import ssl
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from xml.etree import ElementTree

import httpx
import numpy as np
import rasterio

from energy_analysis.chile_kgpv.pipeline import (
    CLIMATE_BOUNDS,
    REFERENCE_IDS,
    file_sha256,
    prepare_map,
)
from energy_data_retrieval.sources.chelsa import CHELSAClient
from energy_data_retrieval.sources.global_solar_atlas import (
    GSA_HOSTS,
    GlobalSolarAtlasClient,
    SolarAtlasTransport,
)
from energy_data_retrieval.sources.natural_earth import NATURAL_EARTH_HOSTS, NaturalEarthClient
from energy_data_retrieval.transport import HTTPClient, HTTPConfig

BOUNDARY_SHA256 = "ce1ac7036499a0edd641fbc093cd209a98f96a49d2eca8480aaacad35138a7f6"
GSA_ATTRIBUTION = (
    "Data obtained from the Global Solar Atlas 2.0, a free, web-based application "
    "developed and operated by Solargis s.r.o. on behalf of the World Bank Group, "
    "utilizing Solargis data, with funding provided by the Energy Sector Management "
    "Assistance Program (ESMAP). https://globalsolaratlas.info"
)


def acquire(raw: Path, pinned: dict, *, proxy: str | None = None, workers: int = 2) -> None:
    """Download exact GSA/boundary archives and ETag/pixel-pinned CHELSA windows."""
    records = {Path(r["url"]).name: r for r in pinned["climate_subsets"]}
    context = ssl.create_default_context()

    def download(pair):
        variable, month = pair
        name = f"CHELSA_{variable}_{month:02d}_1981-2010_V.2.1.tif"
        source = records[name]
        with httpx.Client(timeout=120, trust_env=False, proxy=proxy, verify=context) as http:
            CHELSAClient(http).download_window(
                raw / "climate",
                variable,
                month,
                CLIMATE_BOUNDS,
                expected_etag=source["etag"],
                expected_pixels_sha256=source["pixels_sha256"],
            )

    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(download, [(v, m) for v in ("tas", "pr") for m in range(1, 13)]))
    with HTTPClient(
        allowed_hosts=GSA_HOSTS,
        config=HTTPConfig(maximum_response_bytes=160_000_000, timeout_seconds=120),
        transport=SolarAtlasTransport(
            httpx.HTTPTransport(proxy=proxy, verify=context), country="Chile"
        ),
    ) as http:
        GlobalSolarAtlasClient(http).download_chile_ghi(raw)
    with HTTPClient(
        allowed_hosts=NATURAL_EARTH_HOSTS,
        transport=httpx.HTTPTransport(proxy=proxy, verify=context),
    ) as http:
        NaturalEarthClient(http).download_countries(
            raw / "boundaries",
            scale="10m",
            expected_sha256=BOUNDARY_SHA256,
        )


def write_manifest(raw: Path, output: Path, result: dict) -> dict:
    climate = [json.loads(p.read_text()) for p in sorted((raw / "climate").glob("*.subset.json"))]
    if len(climate) != 24:
        raise ValueError("Expected exactly 24 regional monthly source records")
    metadata = ElementTree.parse(raw / "GHI.tif.xml")
    rights = next(
        "".join(e.itertext())
        for e in metadata.iter()
        if e.tag.endswith("CharacterString") and (e.text or "").startswith("Copyright:")
    )
    with rasterio.open(raw / "GHI.tif") as solar:
        first_row, last_row = solar.height, -1
        for _, window in solar.block_windows():
            values = solar.read(1, window=window, masked=True)
            valid = ~np.ma.getmaskarray(values) & np.isfinite(values) & (values >= 0)
            rows = np.where(valid)[0]
            if len(rows):
                first_row = min(first_row, int(rows.min() + window.row_off))
                last_row = max(last_row, int(rows.max() + window.row_off))
        if last_row < first_row:
            raise ValueError("Solar source contains no valid values")
        solar_grid = dict(
            shape=list(solar.shape),
            transform=list(solar.transform),
            bounds=list(solar.bounds),
            valid_pixel_center_latitude_range=[solar.xy(last_row, 0)[1], solar.xy(first_row, 0)[1]],
            crs=str(solar.crs),
            nodata=solar.nodata,
            sha256=file_sha256(raw / "GHI.tif"),
            metadata_sha256=file_sha256(raw / "GHI.tif.xml"),
        )
    manifest = dict(
        description="Contiguous mainland Chile KGPV; native GSA lattice with explicit source gaps",
        generated_at_utc=datetime.now(UTC).isoformat(),
        boundary_policy=(
            "Largest connected Chile polygon by geodesic area; excludes all islands and Antarctica"
        ),
        climate_period=[1981, 2010],
        solar_period=[1999, 2018],
        baseline_policy="Exploratory mixed historical periods, not a common-period climatology",
        resolution_note=(
            "9-arcsecond output/GHI grid, nominal 250 m. Temperature and precipitation "
            "retain 30-arcsecond (about 1 km) source support, sampled by nearest cell. "
            "Pixel spacing does not establish KGPV accuracy. Natural Earth 10m "
            "denotes 1:10 million cartographic scale, not ten-metre contours."
        ),
        missing_policy=(
            "Class 0 if any required input is missing. GSA Chile ends at 45 S; all "
            "southern mainland beyond that latitude remains explicitly unclassified. "
            "Other coastal/mountain source gaps also remain unclassified."
        ),
        units=dict(temperature="degC", precipitation="mm month-1", annual_ghi="kWh m-2 year-1"),
        preprocessing=[
            "Crop native CHELSA cells using integral windows and HTTP ranges with If-Match.",
            "Check strong source ETags and SHA-256 of decoded uint16 crop bytes (little endian).",
            "Mask 65535 before scale/offset; K minus 273.15; rain kg/m2 equals mm.",
            "GSA already supplies annual GHI kWh/m2. No multiplication by 365.",
            "Snap the mainland bounding box to the GSA lattice, retaining its pixel centres.",
            "Rasterize mainland at pixel centres; preserve polygon holes; nearest climate cells.",
            "Apply classify_kgpv: fixed 2019 thresholds and Southern Hemisphere seasons.",
            "Three bands: class ID, mainland mask, complete-input flag. No extrapolation.",
            "Nearest-class overviews affect display only. Raw sources remain outside Git.",
        ],
        map=result,
        climate_subsets=climate,
        solar_grid=solar_grid,
        solar_archive=json.loads(next(raw.glob("Chile_*.zip.download.json")).read_text()),
        boundary_source=json.loads(
            (raw / "boundaries/ne_10m_admin_0_countries.provenance.json").read_text()
        ),
        licenses=dict(
            climate="CC0 1.0; https://doi.org/10.16904/envidat.228",
            solar=rights,
            solar_attribution=GSA_ATTRIBUTION,
            source_terms="https://globalsolaratlas.info/support/terms-of-use",
            boundary="Natural Earth public domain",
            changes="Regional cropping, nearest climate-cell sampling and KGPV classification",
        ),
        reference_ids=list(REFERENCE_IDS),
        software={p: version(p) for p in ("numpy", "pandas", "rasterio", "pyproj")},
    )
    (output / "kgpv_chile_provenance.json").write_text(
        json.dumps(manifest, indent=2, allow_nan=False) + "\n"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=Path("artifacts/chile-kgpv/raw"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/chile-kgpv/native"))
    parser.add_argument(
        "--source-manifest", type=Path, default=Path("examples/analysis/kgpv_chile_provenance.json")
    )
    parser.add_argument("--tile-size", type=int, default=512)
    parser.add_argument("--workers", type=int, choices=(1, 2), default=2)
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--use-environment-proxy", action="store_true")
    args = parser.parse_args()
    pinned = json.loads(args.source_manifest.read_text())
    print("24 native CHELSA regional crops + 145 MB GSA archive + 5 MB boundaries.", flush=True)
    print("250 m nominal output; climate about 1 km. GSA missing south of 45 S.", flush=True)
    if args.plan_only:
        return
    proxy = os.environ.get("HTTPS_PROXY") if args.use_environment_proxy else None
    acquire(args.cache, pinned, proxy=proxy, workers=args.workers)
    result = prepare_map(args.cache, args.output, tile_size=args.tile_size)
    write_manifest(args.cache, args.output, result)


if __name__ == "__main__":
    main()
