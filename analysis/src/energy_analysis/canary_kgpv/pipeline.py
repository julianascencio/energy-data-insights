"""Stream native climate pixels through KGPV without expanding entire COGs.

This is an exploratory mixed-period application: CanaryClim 1979-2013 and
Global Solar Atlas 1994-2018. It deliberately uses the cellwise classifier,
not map_kgpv's interface for climatologies sharing one baseline. Neither the
source periods nor the coarser solar information are relabelled to match.
"""

from __future__ import annotations

import hashlib
import json
import math
from contextlib import ExitStack
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.enums import Resampling
from rasterio.vrt import WarpedVRT
from rasterio.windows import Window, from_bounds

from energy_methods.kgpv import ZONE_CODES, classify_kgpv

REFERENCE_IDS = (
    "ascencio_vasquez_2021_thesis",
    "ascencio_vasquez_2019_kgpv",
    "canaryclim_2025_data",
    "patino_2023_canaryclim",
    "global_solar_atlas_2019",
    "rasterio_documentation",
)

# Disjoint geographic windows cover the seven main island groups, including
# Lobos, La Graciosa and the other Chinijo islets. Coordinates are view bounds,
# not administrative polygons: source masks determine land/coastal coverage.
ISLANDS = {
    "el_hierro": ("El Hierro", (-18.18, 27.62, -17.87, 27.88)),
    "la_palma": ("La Palma", (-17.96, 28.43, -17.70, 28.88)),
    "la_gomera": ("La Gomera", (-17.37, 27.99, -17.07, 28.24)),
    "tenerife": ("Tenerife", (-16.94, 27.99, -16.10, 28.65)),
    "gran_canaria": ("Gran Canaria", (-15.85, 27.72, -15.34, 28.19)),
    "fuerteventura": ("Fuerteventura and Lobos", (-14.54, 28.03, -13.79, 28.80)),
    "lanzarote": ("Lanzarote and Chinijo", (-13.90, 28.82, -13.32, 29.43)),
}
SAMPLE_SITES = {
    "El Hierro": (-17.98, 27.75),
    "La Palma": (-17.85, 28.68),
    "La Gomera": (-17.24, 28.11),
    "Tenerife south": (-16.59, 28.08),
    "Tenerife north": (-16.52, 28.39),
    "Teide": (-16.6438, 28.2724),
    "Anaga": (-16.23, 28.55),
    "Gran Canaria": (-15.60, 28.00),
    "Fuerteventura": (-14.01, 28.43),
    "Lanzarote": (-13.60, 29.04),
    "La Graciosa": (-13.51, 29.25),
}


def file_sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def climate_path(directory: Path, variable: str, month: int) -> Path:
    return directory / f"CHELSACanaryClim_{variable}_{month:02d}_1979-2013_V.1.0.tif"


def _validate_climate(source, reference, variable: str, month: int) -> None:
    tags = source.tags()
    unit = "K" if variable == "tas" else "kg m-2 month-1"
    if (
        source.crs != rasterio.crs.CRS.from_epsg(4326)
        or source.count != 1
        or source.shape != reference.shape
        or source.transform != reference.transform
        or tags.get("variable") != variable
        or tags.get("variable_unit") != unit
        or tags.get("version") != "1.0"
        or tags.get("datetime") != f"15-{month:02d}-1996"
        or source.nodata is None
        or not np.isfinite([source.scales[0], source.offsets[0]]).all()
        or source.scales[0] <= 0
    ):
        raise ValueError("Unexpected CanaryClim metadata, month, units or grid")


def decode_climate(raw: np.ndarray, source, variable: str) -> np.ndarray:
    """Mask the encoded sentinel before applying the file's scale and offset."""
    values = raw.astype(np.float64)
    values[raw == source.nodata] = np.nan
    values = values * source.scales[0] + source.offsets[0]
    if variable == "tas":
        values -= 273.15
    elif variable != "pr":
        raise ValueError("Expected tas or pr")
    return values


def _window(reference, bounds: tuple[float, float, float, float]) -> Window:
    window = from_bounds(*bounds, transform=reference.transform)
    left = max(0, math.floor(window.col_off))
    top = max(0, math.floor(window.row_off))
    right = min(reference.width, math.ceil(window.col_off + window.width))
    bottom = min(reference.height, math.ceil(window.row_off + window.height))
    if left >= right or top >= bottom:
        raise ValueError("Island window does not intersect the source grid")
    return Window.from_slices((top, bottom), (left, right))


def _classify_window(sources, solar, window: Window, first: np.ndarray):
    reference = sources["tas"][0]
    land = first != reference.nodata
    count = int(land.sum())
    classes = np.zeros(first.shape, dtype=np.uint8)
    if not count:
        return classes, land
    fields = {}
    for variable in ("tas", "pr"):
        monthly = []
        for month, source in enumerate(sources[variable]):
            raw = first if variable == "tas" and month == 0 else source.read(1, window=window)
            monthly.append(decode_climate(raw[land], source, variable))
        fields[variable] = np.stack(monthly, axis=-1)
    ghi = solar.read(1, window=window, masked=True).filled(np.nan)[land]
    rows = np.nonzero(land)[0] + window.row_off
    latitude = reference.transform.f + (rows + 0.5) * reference.transform.e
    result = classify_kgpv(fields["tas"], fields["pr"], ghi, latitude)
    classes[land] = result.class_id
    return classes, land


def prepare_maps(
    raw_directory: Path,
    output_directory: Path,
    *,
    islands: tuple[str, ...] = tuple(ISLANDS),
    tile_size: int = 512,
) -> dict:
    """Write two-band native GeoTIFFs, with bounded tile working memory.

    Band 1: KGPV class 1..12 (0 unclassified). Band 2: January temperature's
    native valid footprint (1 land/input coverage, 0 outside). Missing climate
    or solar inputs stay unclassified; no coastal extrapolation is performed.
    Radiation is nearest-cell sampled before classification, retaining its
    9-arcsecond source support. All output climate pixels keep native centres.
    """
    if not islands or len(set(islands)) != len(islands) or set(islands) - ISLANDS.keys():
        raise ValueError("Select unique known island groups")
    if type(tile_size) is not int or not 128 <= tile_size <= 1024:
        raise ValueError("tile_size must be an integer in 128..1024")
    output_directory.mkdir(parents=True, exist_ok=True)
    records = {}
    with ExitStack() as stack, rasterio.Env(GDAL_CACHEMAX=128_000_000):
        sources = {
            variable: [
                stack.enter_context(rasterio.open(climate_path(raw_directory, variable, month)))
                for month in range(1, 13)
            ]
            for variable in ("tas", "pr")
        }
        reference = sources["tas"][0]
        for variable, monthly in sources.items():
            for month, source in enumerate(monthly, start=1):
                _validate_climate(source, reference, variable, month)
        if (
            reference.transform.a <= 0
            or reference.transform.e >= 0
            or reference.transform.b != 0
            or reference.transform.d != 0
        ):
            raise ValueError("Expected a north-up CanaryClim grid")
        ghi_source = stack.enter_context(rasterio.open(raw_directory / "GHI.tif"))
        if (
            ghi_source.crs != reference.crs
            or ghi_source.count != 1
            or not np.isclose(ghi_source.transform.a, 0.0025)
            or not np.isclose(ghi_source.transform.e, -0.0025)
            or ghi_source.nodata is None
        ):
            raise ValueError("Expected the pinned 9-arcsecond GSA GHI raster")
        solar = stack.enter_context(
            WarpedVRT(
                ghi_source,
                crs=reference.crs,
                transform=reference.transform,
                width=reference.width,
                height=reference.height,
                resampling=Resampling.nearest,
                nodata=np.nan,
                dtype="float32",
                warp_mem_limit=64,
            )
        )
        for key in islands:
            label, bounds = ISLANDS[key]
            view = _window(reference, bounds)
            path = output_directory / f"kgpv_canary_{key}.tif"
            counts = np.zeros(13, dtype=np.int64)
            land_count = 0
            profile = dict(
                driver="GTiff",
                width=int(view.width),
                height=int(view.height),
                count=2,
                dtype="uint8",
                crs=reference.crs,
                transform=reference.window_transform(view),
                nodata=0,
                tiled=True,
                blockxsize=512,
                blockysize=512,
                compress="deflate",
                zlevel=9,
                BIGTIFF="IF_SAFER",
                SPARSE_OK=True,
            )
            with rasterio.open(path, "w", **profile) as target:
                target.set_band_description(1, "KGPV class: 0 unclassified, 1..12 see zone_codes")
                target.set_band_description(2, "CanaryClim valid temperature footprint: 0/1")
                target.update_tags(
                    title=f"{label}: exploratory native-grid KGPV",
                    zone_codes=json.dumps(dict(enumerate(ZONE_CODES))),
                    climate_period="1979-2013",
                    solar_period="1994-2018",
                    baseline_policy="Mixed historical periods; not a common-baseline map",
                    solar_resolution_degrees="0.0025",
                    solar_sampling="nearest source cell; no new subpixel radiation detail",
                    climate_resolution_note=(
                        "Native COG spacing about 5 m; published model benchmark 100 m. "
                        "Pixel spacing is not validated climate or KGPV accuracy."
                    ),
                    source=(
                        "CHELSACanaryClim v1.0; Global Solar Atlas 2.0, World Bank/ESMAP/Solargis"
                    ),
                    references=";".join(REFERENCE_IDS),
                    license="Derived climate: CC0; solar: CC BY 4.0 with GSA additional terms",
                )
                for row in range(0, int(view.height), tile_size):
                    for col in range(0, int(view.width), tile_size):
                        local = Window.from_slices(
                            (row, min(row + tile_size, int(view.height))),
                            (col, min(col + tile_size, int(view.width))),
                        )
                        window = Window.from_slices(
                            (int(view.row_off) + row, int(view.row_off) + row + int(local.height)),
                            (int(view.col_off) + col, int(view.col_off) + col + int(local.width)),
                        )
                        first = reference.read(1, window=window)
                        classes, land = _classify_window(sources, solar, window, first)
                        if not land.any():
                            continue
                        target.write(classes, 1, window=local)
                        target.write(land.astype(np.uint8), 2, window=local)
                        land_count += int(land.sum())
                        counts += np.bincount(classes[land], minlength=13)
                target.build_overviews([4, 16, 64], Resampling.nearest)
                target.update_tags(ns="rio_overview", resampling="nearest")
            records[key] = {
                "name": label,
                "file": path.name,
                "shape": [int(view.height), int(view.width)],
                "transform": list(reference.window_transform(view)),
                "bounds": list(bounds),
                "source_land_pixels": land_count,
                "classified_pixels": int(counts[1:].sum()),
                "missing_land_pixels": int(counts[0]),
                "class_counts": dict(zip(ZONE_CODES[1:], counts[1:].tolist(), strict=True)),
                "sha256": file_sha256(path),
                "size_bytes": path.stat().st_size,
            }
            print(
                f"{label}: {counts[1:].sum():,} classified / {land_count:,} land pixels; "
                f"{path.stat().st_size:,} bytes",
                flush=True,
            )
        samples = []
        for name, (lon, lat) in SAMPLE_SITES.items():
            row, col = reference.index(lon, lat)
            window = Window.from_slices((row, row + 1), (col, col + 1))
            record = {
                "name": name,
                "requested_lon": lon,
                "requested_lat": lat,
                "lon": reference.xy(row, col)[0],
                "lat": reference.xy(row, col)[1],
            }
            for variable, prefix in (("tas", "t"), ("pr", "p")):
                for month, source in enumerate(sources[variable], start=1):
                    value = decode_climate(source.read(1, window=window), source, variable)[0, 0]
                    record[f"{prefix}{month:02d}"] = value
            record["annual_ghi"] = float(
                solar.read(1, window=window, masked=True).filled(np.nan)[0, 0]
            )
            result = classify_kgpv(
                [record[f"t{m:02d}"] for m in range(1, 13)],
                [record[f"p{m:02d}"] for m in range(1, 13)],
                record["annual_ghi"],
                record["lat"],
            )
            record["kgpv_class"] = int(result.class_id)
            record["kgpv_zone"] = str(result.zone)
            samples.append(record)
        pd.DataFrame(samples).to_csv(
            output_directory / "kgpv_canary_samples.csv",
            index=False,
            float_format="%.10g",
            na_rep="",
            lineterminator="\n",
        )
    return records
