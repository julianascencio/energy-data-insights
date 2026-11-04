"""Download pinned CanaryClim temperature and prepare 100 m offline input tiles."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path

import httpx
import numpy as np
import rasterio
from rasterio.io import MemoryFile
from rasterio.transform import from_origin
from rasterio.warp import Resampling, reproject, transform_bounds

from energy_analysis.canary_kgpv.pipeline import ISLANDS
from energy_data_retrieval.sources.canary_clim import CANARY_CLIM_HOSTS
from energy_data_retrieval.transport import HTTPClient, HTTPConfig


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("artifacts/pvdeg-canary"))
    args = parser.parse_args()
    pinned = json.loads(Path("examples/analysis/kgpv_canary_provenance.json").read_text())
    records = [r for r in pinned["sources"] if "_tas_" in r["endpoint"]]
    args.output.mkdir(parents=True, exist_ok=True)
    tiles = {}
    for island, (label, bounds) in ISLANDS.items():
        west, south, east, north = transform_bounds("EPSG:4326", "EPSG:32628", *bounds)
        west, north = math.floor(west / 100) * 100, math.ceil(north / 100) * 100
        width, height = math.ceil((east - west) / 100), math.ceil((north - south) / 100)
        path = args.output / f"pvdeg_canary_{island}.tif"
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            width=width,
            height=height,
            count=12,
            dtype="int16",
            nodata=-32768,
            crs="EPSG:32628",
            transform=from_origin(west, north, 100, 100),
            compress="deflate",
            predictor=2,
        ) as target:
            target.scales = (0.01,) * 12
            target.update_tags(units="degC", period="1979-2013", evidence="modeled climatology")
        tiles[island] = {"file": path.name, "label": label}
    with HTTPClient(
        allowed_hosts=CANARY_CLIM_HOSTS,
        config=HTTPConfig(maximum_response_bytes=160_000_000, timeout_seconds=180),
        transport=httpx.HTTPTransport(proxy=os.environ.get("HTTPS_PROXY")),
    ) as http:
        for month in range(1, 13):
            record = next(r for r in records if f"_tas_{month:02d}_" in r["endpoint"])
            response = http.request_bytes(record["endpoint"])
            if hashlib.sha256(response.value).hexdigest() != record["sha256"]:
                raise ValueError("Source checksum mismatch")
            with MemoryFile(response.value) as memory, memory.open() as source:
                if (
                    source.tags().get("variable_unit") != "K"
                    or source.tags().get("datetime") != f"15-{month:02d}-1996"
                    or source.tags().get("variable") != "tas"
                    or source.crs != rasterio.crs.CRS.from_epsg(4326)
                    or source.nodata is None
                    or not np.isfinite([source.scales[0], source.offsets[0]]).all()
                    or source.scales[0] <= 0
                ):
                    raise ValueError("Expected encoded Kelvin with explicit nodata")
                for tile in tiles.values():
                    with rasterio.open(args.output / tile["file"], "r+") as target:
                        raw = np.full(target.shape, source.nodata, dtype=source.dtypes[0])
                        reproject(
                            rasterio.band(source, 1),
                            raw,
                            dst_transform=target.transform,
                            dst_crs=target.crs,
                            dst_nodata=source.nodata,
                            resampling=Resampling.nearest,
                        )
                        valid = raw != source.nodata
                        encoded = np.full(raw.shape, -32768, dtype=np.int16)
                        celsius = raw[valid] * source.scales[0] + source.offsets[0] - 273.15
                        encoded[valid] = np.rint(celsius * 100).astype(np.int16)
                        target.write(encoded, month)
                        target.set_band_description(month, f"month_{month:02d}_temperature")
            print(f"Processed month {month}", flush=True)
    # Rewrite once to compact TIFF blocks accumulated by monthly updates.
    for tile in tiles.values():
        path = args.output / tile["file"]
        compact = path.with_suffix(".compact.tif")
        with (
            rasterio.open(path) as source,
            rasterio.open(
                compact,
                "w",
                **{
                    **source.profile,
                    "tiled": True,
                    "blockxsize": 256,
                    "blockysize": 256,
                    "zlevel": 9,
                },
            ) as target,
        ):
            target.write(source.read())
            target.scales = source.scales
            target.descriptions = source.descriptions
            target.update_tags(**source.tags())
        compact.replace(path)
        tile["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = {
        "source": "CHELSACanaryClim v1.0",
        "doi": "10.16904/envidat.692",
        "license": "CC0-1.0",
        "period": [1979, 2013],
        "source_records": records,
        "grid": "EPSG:32628, 100 m; nearest native source pixel at each cell centre",
        "limits": "Modeled climatology, not observations or 100 m validated PV degradation",
        "tiles": tiles,
        "pvdeg_version": "0.7.4",
        "scenario": {
            "activation_energy_kj_mol": 60,
            "module_offset_c": 20,
            "reference_temperature_c": 25,
            "humidity_exponent": 0,
            "irradiance_exponent": 0,
        },
    }
    (args.output / "pvdeg_canary_provenance.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
