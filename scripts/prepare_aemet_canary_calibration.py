"""Capture AEMET 2022-2023 station observations and explicit ERA5 hourly inputs.

Run from the repository root with AEMET_API_KEY. Never logs credentials.
Acquisition is resumable; source payloads are archived separately from the gallery.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_origin, xy
from rasterio.warp import Resampling, reproject, transform

from energy_data_retrieval.sources.aemet.client import AEMETClient, _link
from energy_data_retrieval.sources.open_meteo import OpenMeteoClient, Site, WeatherProduct
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, object_value

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "examples/analysis/aemet_era5_canary"
RAW = ROOT / "outputs/aemet_era5_canary"


def save_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def acquire_aemet() -> None:
    """Use the all-station daily API in conservative 15-day partitions."""
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    complete = OUT / "aemet_provenance.json"
    if complete.exists():
        manifest = json.loads(complete.read_text())
        if "daily_files" in manifest:
            for item in manifest["daily_files"]:
                if hashlib.sha256((OUT / item["file"]).read_bytes()).hexdigest() != item["sha256"]:
                    raise ValueError("Captured AEMET partition checksum mismatch")
            print("Reusing checksum-verified AEMET 2022-2023 snapshot", flush=True)
            return
        # Migrate the first capture into bounded, plain-text station partitions.
        if hashlib.sha256((OUT / "daily.csv").read_bytes()).hexdigest() != manifest["daily_sha256"]:
            raise ValueError("AEMET source checksum mismatch")
        split_daily(pd.read_csv(OUT / "daily.csv", dtype=str), manifest)
        (OUT / "daily.csv").unlink()
        return
    records = []
    with HTTPClient(
        frozenset({"opendata.aemet.es"}), config=HTTPConfig(minimum_interval_seconds=2.0)
    ) as http:
        client = AEMETClient.from_environment(http)
        assert client.api_key
        inventory = client.stations(bbox=(-18.5, 27, -13, 30))
        stations = inventory.frame[
            ["station_id", "station_name", "latitude", "longitude", "elevation_m"]
        ]
        stations.to_csv(OUT / "stations.csv", index=False)
        save_json(OUT / "station_metadata.json", inventory.metadata)
        ids = set(stations.station_id)
        day = date(2022, 1, 1)
        while day <= date(2023, 12, 31):
            end = min(day + timedelta(days=14), date(2023, 12, 31))
            path = RAW / f"daily_{day}.json"
            if not path.exists():
                endpoint = (
                    "https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos/"
                    f"fechaini/{day}T00:00:00UTC/fechafin/{end}T23:59:59UTC/todasestaciones"
                )
                envelope = http.get_json(
                    endpoint,
                    secret_headers={"api_key": client.api_key},
                    use_cache=False,
                    allow_legacy_charset=True,
                )
                value = object_value(envelope.value)
                if value.get("estado") != 200:
                    raise ValueError(f"AEMET daily partition {day} failed")
                data = http.get_json(
                    _link(value.get("datos")), use_cache=False, allow_legacy_charset=True
                )
                meta = http.get_json(
                    _link(value.get("metadatos")), use_cache=False, allow_legacy_charset=True
                )
                save_json(path, data.value)
                save_json(OUT / "daily_metadata.json", meta.value)
                save_json(
                    path.with_suffix(".provenance.json"),
                    {
                        "requests": [asdict(x.record) for x in (envelope, data, meta)],
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    },
                )
            rows = json.loads(path.read_text())
            if not isinstance(rows, list):
                raise ValueError("Daily response must be a list")
            records.extend(row for row in rows if row["indicativo"] in ids)
            print(f"AEMET {day} through {end}: captured", flush=True)
            day = end + timedelta(days=1)
    frame = pd.DataFrame(records)
    if frame.duplicated(["indicativo", "fecha"]).any():
        raise ValueError("Duplicate station-date observations")
    frame.sort_values(["indicativo", "fecha"]).to_csv(OUT / "daily.csv", index=False)
    save_json(
        OUT / "aemet_provenance.json",
        {
            "source": "AEMET OpenData",
            "period": ["2022-01-01", "2023-12-31"],
            "attribution": "Fuente: AEMET. Retrieved for ERA5 bias-correction research.",
            "stations": len(stations),
            "rows": len(frame),
            "requests": [
                json.loads(p.read_text()) for p in sorted(RAW.glob("daily_*.provenance.json"))
            ],
            "daily_sha256": hashlib.sha256((OUT / "daily.csv").read_bytes()).hexdigest(),
            "station_sha256": hashlib.sha256((OUT / "stations.csv").read_bytes()).hexdigest(),
        },
    )
    split_daily(frame, json.loads((OUT / "aemet_provenance.json").read_text()))
    (OUT / "daily.csv").unlink()
    print(f"AEMET complete: {len(frame)} observations", flush=True)


def split_daily(frame: pd.DataFrame, manifest: dict) -> None:
    """Preserve source strings in one small CSV per station, with per-file hashes."""
    (OUT / "daily").mkdir(exist_ok=True)
    records = []
    for station, rows in frame.groupby("indicativo"):
        path = OUT / "daily" / f"{station}.csv"
        rows.to_csv(path, index=False)
        records.append(
            {
                "file": str(path.relative_to(OUT)),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "rows": len(rows),
            }
        )
    manifest["daily_files"] = records
    manifest["daily_sha256_before_partitioning"] = manifest.pop("daily_sha256", None)
    save_json(OUT / "aemet_provenance.json", manifest)


def save_weather_partitions(frame: pd.DataFrame, slug: str) -> list[dict]:
    """One plain-text CSV per native node and year; no large binary Git inputs."""
    records = []
    for year in (2022, 2023):
        path = OUT / "weather" / f"{slug}_{year}.csv"
        rows = frame.loc[pd.to_datetime(frame.timestamp, utc=True).dt.year == year]
        rows.to_csv(path, index=False)
        records.append({"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return records


def prepare_grid() -> pd.DataFrame:
    """5 km display cells intersecting the existing 100 m Canary land masks."""
    affine = from_origin(160000, 3290000, 5000, 5000)
    land = np.zeros((50, 106), dtype=np.uint8)
    for path in sorted((ROOT / "examples/analysis").glob("pvdeg_canary_*.tif")):
        with rasterio.open(path) as src:
            source = (src.read_masks(1) > 0).astype("uint8")
            destination = np.zeros_like(land)
            reproject(
                source,
                destination,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=affine,
                dst_crs="EPSG:32628",
                resampling=Resampling.max,
            )
            land |= destination
    rows, cols = np.where(land > 0)
    east, north = xy(affine, rows, cols)
    lon, lat = transform("EPSG:32628", "EPSG:4326", east, north)
    grid = pd.DataFrame(
        {
            "row": rows,
            "col": cols,
            "easting": east,
            "northing": north,
            "latitude": lat,
            "longitude": lon,
        }
    )
    grid.to_csv(OUT / "grid.csv", index=False)
    return grid


def acquire_era5() -> None:
    """Request each 0.25-degree node once; retain provider-selected cell IDs."""
    grid = prepare_grid()
    stations = pd.read_csv(OUT / "stations.csv")
    targets = pd.concat([grid[["latitude", "longitude"]], stations[["latitude", "longitude"]]])
    nodes = (targets * 4).round() / 4
    nodes = nodes.drop_duplicates().sort_values(["latitude", "longitude"])
    (OUT / "weather").mkdir(exist_ok=True)
    manifest = []
    with HTTPClient(
        frozenset({"archive-api.open-meteo.com"}),
        config=HTTPConfig(minimum_interval_seconds=8.0, timeout_seconds=30, attempts=6),
    ) as http:
        client = OpenMeteoClient(
            http, product=WeatherProduct.ERA5, include_degradation=True, chunk_days=366
        )
        for latitude, longitude in nodes.to_numpy(dtype=float):
            slug = f"{latitude:.2f}_{longitude:.2f}"
            meta_path = OUT / "weather" / f"{slug}.json"
            if meta_path.exists():
                record = json.loads(meta_path.read_text())
                if "files" not in record:
                    old = OUT / "weather" / record["file"]
                    if hashlib.sha256(old.read_bytes()).hexdigest() != record["sha256"]:
                        raise ValueError("Legacy ERA5 input checksum mismatch")
                    record["files"] = save_weather_partitions(pd.read_csv(old), slug)
                    record["legacy_sha256"] = record.pop("sha256")
                    record.pop("file")
                    save_json(meta_path, record)
                    old.unlink()
                manifest.append(record)
                continue
            frames = []
            requests = []
            selected = []
            for year in (2022, 2023):
                result = client.weather(
                    Site(slug, latitude, longitude), date(year, 1, 1), date(year, 12, 31)
                )
                frames.append(result.frame)
                requests.append(asdict(result.request))
                selected.append((result.cell_latitude, result.cell_longitude))
            if selected[0] != selected[1]:
                raise ValueError("Provider changed cell across years")
            frame = pd.concat(frames, ignore_index=True)
            files = save_weather_partitions(frame, slug)
            record = {
                "files": files,
                "requested_latitude": latitude,
                "requested_longitude": longitude,
                "cell_latitude": selected[0][0],
                "cell_longitude": selected[0][1],
                "requests": requests,
            }
            save_json(meta_path, record)
            manifest.append(record)
            print(f"ERA5 {slug}: {len(frame)} hours", flush=True)
    save_json(
        OUT / "era5_provenance.json",
        {
            "source": "ERA5 via Open-Meteo, models=era5, elevation=nan, cell_selection=nearest",
            "attribution": (
                "Contains modified Copernicus Climate Change Service information. "
                "Open-Meteo CC BY 4.0."
            ),
            "period": ["2022-01-01", "2023-12-31"],
            "nodes": manifest,
            "display_grid_m": 5000,
            "native_resolution_degrees": 0.25,
            "meaning": "Display spacing is not weather or degradation accuracy.",
        },
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1 or sys.argv[1] == "aemet":
        acquire_aemet()
    if len(sys.argv) == 1 or sys.argv[1] == "era5":
        acquire_era5()
