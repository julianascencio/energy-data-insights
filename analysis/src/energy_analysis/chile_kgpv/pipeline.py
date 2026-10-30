"""Mainland Chile KGPV on the native 9-arcsecond Global Solar Atlas lattice.

Climate remains 30 arcseconds. Extending the output lattice southward does not
extend solar coverage: missing climate or GHI yields class zero, including all
land south of the Chile GSA archive's 45 S edge. No solar source is spliced in.
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
from pyproj import Geod
from rasterio.enums import Resampling
from rasterio.features import geometry_mask
from rasterio.vrt import WarpedVRT
from rasterio.windows import Window, from_bounds

from energy_methods.country_boundaries import (
    CountryBoundary,
    CountrySelection,
    load_country_boundaries,
    polygons,
    write_country_boundaries,
)
from energy_methods.kgpv import ZONE_CODES, classify_kgpv

REFERENCE_IDS = (
    "ascencio_vasquez_2021_thesis",
    "ascencio_vasquez_2019_kgpv",
    "chelsa_2021_climatologies",
    "karger_2017_chelsa",
    "global_solar_atlas_chile_2019",
    "natural_earth_countries",
    "rasterio_documentation",
)
CLIMATE_BOUNDS = (-76.0, -54.0, -66.5, -17.4)
SAMPLE_SITES = {
    "Arica": (-70.29, -18.48),
    "Altiplano": (-69.30, -18.20),
    "Atacama": (-69.50, -24.50),
    "Copiapo": (-70.33, -27.37),
    "La Serena": (-71.24, -29.91),
    "Santiago": (-70.65, -33.45),
    "Rengo": (-70.86, -34.41),
    "Temuco": (-72.60, -38.74),
    "Puerto Montt": (-72.94, -41.46),
    "Coyhaique": (-72.07, -45.57),
    "Cochrane": (-72.57, -47.25),
    "Punta Arenas inland": (-70.95, -53.15),
}


def file_sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def mainland_boundary(path: Path) -> CountrySelection:
    """Largest connected Chile polygon by WGS84 geodesic area, with its holes.

    This explicit contiguous-land policy excludes Tierra del Fuego, Chiloe,
    offshore archipelagos and Antarctic claims. No simplification is applied.
    """
    selected = load_country_boundaries(path, "CHL")
    geod = Geod(ellps="WGS84")
    mainland = max(
        polygons(selected.geometry), key=lambda p: abs(geod.geometry_area_perimeter(p)[0])
    )
    return CountrySelection((CountryBoundary("CHL", "Chile mainland", mainland),), selected.source)


def climate_path(raw: Path, variable: str, month: int) -> Path:
    return raw / "climate" / f"CHELSA_{variable}_{month:02d}_1981-2010_V.2.1.tif"


def decode_climate(values: np.ndarray, source, variable: str) -> np.ndarray:
    """Decode masked native integer values; K to Celsius, kg/m²/month to mm."""
    result = values.astype(float)
    result[values == source.nodata] = np.nan
    result = result * source.scales[0] + source.offsets[0]
    if variable == "tas":
        return result - 273.15
    if variable != "pr":
        raise ValueError("Expected tas or pr")
    return result


def _validate_climate(source, reference, variable: str) -> None:
    tags = source.tags()
    if (
        source.crs != rasterio.crs.CRS.from_epsg(4326)
        or source.count != 1
        or source.shape != reference.shape
        or not np.allclose(source.transform, reference.transform, rtol=0, atol=1e-10)
        or source.dtypes != ("uint16",)
        or source.nodata != 65535
        or source.transform.b != 0
        or source.transform.d != 0
        or not np.isclose(source.transform.a, 1 / 120)
        or not np.isclose(source.transform.e, -1 / 120)
        or tags.get("variable") != variable
        or tags.get("version") != "2.1"
        or tags.get("datetime") != "1981-2010"
        or tags.get("variable_unit") != ("K" if variable == "tas" else "kg m-2 month-1")
        or not np.isfinite([source.scales[0], source.offsets[0]]).all()
        or source.scales[0] <= 0
    ):
        raise ValueError("Unexpected CHELSA climate metadata or grid")


def _grid(solar, boundary):
    floating = from_bounds(*boundary.geometry.bounds, transform=solar.transform)
    row, col = math.floor(floating.row_off), math.floor(floating.col_off)
    bottom = math.ceil(floating.row_off + floating.height)
    right = math.ceil(floating.col_off + floating.width)
    window = Window.from_slices((row, bottom), (col, right))
    return solar.window_transform(window), int(window.width), int(window.height)


def prepare_map(raw: Path, output: Path, *, tile_size: int = 512) -> dict:
    """Classify bounded tiles, retaining the solar lattice and mainland mask.

    Band 1 is class 1..12, zero unclassified. Band 2 is the polygon-centre mask
    (1 mainland, 0 outside). Band 3 is complete-input availability (0/1).
    Nearest source cells are used; there is no interpolation or coastal fill.
    """
    if type(tile_size) is not int or not 128 <= tile_size <= 1024:
        raise ValueError("tile_size must be an integer in 128..1024")
    output.mkdir(parents=True, exist_ok=True)
    selection = mainland_boundary(raw / "boundaries/ne_10m_admin_0_countries.shp")
    boundary_path = write_country_boundaries(selection, output / "kgpv_chile_mainland.geojson")
    # Companions are generated for local GIS use; the gallery distributes GeoJSON.
    write_country_boundaries(selection, output / "kgpv_chile_mainland.shp")
    path = output / "kgpv_chile_mainland.tif"
    temporary = path.with_suffix(".tif.partial")
    counts = np.zeros(13, dtype=np.int64)
    area_km2 = np.zeros(13)
    geod = Geod(ellps="WGS84")
    with ExitStack() as stack, rasterio.Env(GDAL_CACHEMAX=128_000_000):
        sources = {
            v: [stack.enter_context(rasterio.open(climate_path(raw, v, m))) for m in range(1, 13)]
            for v in ("tas", "pr")
        }
        reference = sources["tas"][0]
        for variable, months in sources.items():
            for source in months:
                _validate_climate(source, reference, variable)
        solar = stack.enter_context(rasterio.open(raw / "GHI.tif"))
        if (
            solar.crs != reference.crs
            or solar.count != 1
            or solar.nodata is None
            or solar.transform.b != 0
            or solar.transform.d != 0
            or not np.isclose(solar.transform.a, 0.0025)
            or not np.isclose(solar.transform.e, -0.0025)
            or solar.scales != (1.0,)
            or solar.offsets != (0.0,)
        ):
            raise ValueError("Expected annual GSA GHI on its 9-arcsecond grid")
        transform, width, height = _grid(solar, selection)
        options = dict(
            crs=solar.crs,
            transform=transform,
            width=width,
            height=height,
            resampling=Resampling.nearest,
            warp_mem_limit=32,
        )
        climate = {
            v: [stack.enter_context(WarpedVRT(s, **options)) for s in months]
            for v, months in sources.items()
        }
        ghi = stack.enter_context(WarpedVRT(solar, **options, nodata=np.nan, dtype="float32"))
        pixel_areas = []
        for row in range(height):
            north = transform.f + row * transform.e
            south = north + transform.e
            area, _ = geod.polygon_area_perimeter(
                [transform.c, transform.c + transform.a, transform.c + transform.a, transform.c],
                [north, north, south, south],
            )
            pixel_areas.append(abs(area) / 1e6)
        profile = dict(
            driver="GTiff",
            width=width,
            height=height,
            count=3,
            dtype="uint8",
            crs=solar.crs,
            transform=transform,
            nodata=0,
            tiled=True,
            compress="deflate",
            zlevel=9,
            blockxsize=512,
            blockysize=512,
        )
        try:
            with rasterio.open(temporary, "w", **profile) as target:
                target.set_band_description(1, "KGPV class 1..12; 0 unclassified")
                target.set_band_description(2, "Mainland polygon pixel-centre mask 0/1")
                target.set_band_description(3, "Complete climate and GHI inputs 0/1")
                target.update_tags(
                    title="Contiguous mainland Chile: exploratory KGPV",
                    zone_codes=json.dumps(dict(enumerate(ZONE_CODES))),
                    climate_period="1981-2010",
                    solar_period="1999-2018",
                    baseline_policy="Mixed historical periods; not a common-baseline map",
                    climate_resolution="30 arcseconds (about 1 km), nearest source cell",
                    solar_resolution="9 arcseconds (nominal 250 m); archive ends at 45 S",
                    missing_policy="No extrapolation or gap filling; all inputs required",
                    boundary_policy="Largest connected Chile polygon; centre-of-pixel mask",
                    license=(
                        "CHELSA CC0; GSA CC BY 4.0 with additional terms; "
                        "Natural Earth public domain"
                    ),
                    source="CHELSA v2.1; World Bank/ESMAP/Solargis GSA 2.0; Natural Earth",
                    references=";".join(REFERENCE_IDS),
                )
                for row in range(0, height, tile_size):
                    for col in range(0, width, tile_size):
                        window = Window.from_slices(
                            (row, min(row + tile_size, height)),
                            (col, min(col + tile_size, width)),
                        )
                        shape = (int(window.height), int(window.width))
                        land = geometry_mask(
                            [selection.geometry],
                            out_shape=shape,
                            transform=target.window_transform(window),
                            invert=True,
                            all_touched=False,
                        )
                        if not land.any():
                            continue
                        fields = {
                            v: np.stack(
                                [
                                    decode_climate(view.read(1, window=window)[land], source, v)
                                    for view, source in zip(climate[v], sources[v], strict=True)
                                ],
                                axis=-1,
                            )
                            for v in ("tas", "pr")
                        }
                        annual = ghi.read(1, window=window, masked=True).filled(np.nan)[land]
                        rows = np.nonzero(land)[0] + row
                        latitude = transform.f + (rows + 0.5) * transform.e
                        result = classify_kgpv(fields["tas"], fields["pr"], annual, latitude)
                        classes = np.zeros(shape, dtype=np.uint8)
                        classes[land] = result.class_id
                        target.write(classes, 1, window=window)
                        target.write(land.astype(np.uint8), 2, window=window)
                        target.write((classes > 0).astype(np.uint8), 3, window=window)
                        counts += np.bincount(result.class_id, minlength=13)
                        area_km2 += np.bincount(
                            result.class_id, weights=np.asarray(pixel_areas)[rows], minlength=13
                        )
                target.build_overviews([4, 16, 64], Resampling.nearest)
                target.update_tags(ns="rio_overview", resampling="nearest")
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
        samples = []
        with rasterio.open(path) as output_map:
            for name, (lon, lat) in SAMPLE_SITES.items():
                row, col = output_map.index(lon, lat)
                if not 0 <= row < height or not 0 <= col < width:
                    continue
                window = Window.from_slices((row, row + 1), (col, col + 1))
                if not output_map.read(2, window=window).item():
                    continue
                x, y = output_map.xy(row, col)
                record = dict(
                    site=name,
                    longitude=x,
                    latitude=y,
                    annual_ghi_kwh_m2=float(ghi.read(1, window=window).item()),
                    class_id=int(output_map.read(1, window=window).item()),
                )
                record["zone"] = ZONE_CODES[int(output_map.read(1, window=window).item())]
                for variable in ("tas", "pr"):
                    for m, (view, source) in enumerate(
                        zip(climate[variable], sources[variable], strict=True), 1
                    ):
                        record[f"{variable}_{m:02d}"] = float(
                            decode_climate(view.read(1, window=window), source, variable).item()
                        )
                samples.append(record)
        sample_path = output / "kgpv_chile_samples.csv"
        pd.DataFrame(samples).to_csv(sample_path, index=False, float_format="%.17g")
    return dict(
        file=path.name,
        sha256=file_sha256(path),
        shape=[height, width],
        transform=list(transform),
        mainland_pixels=int(counts.sum()),
        classified_pixels=int(counts[1:].sum()),
        missing_mainland_pixels=int(counts[0]),
        class_counts={ZONE_CODES[i] or "unclassified": int(n) for i, n in enumerate(counts)},
        area_km2={ZONE_CODES[i] or "unclassified": float(n) for i, n in enumerate(area_km2)},
        area_policy="Sum of full WGS84 ellipsoidal pixel areas selected by polygon centres",
        contour_files_sha256={
            p.name: file_sha256(p)
            for p in sorted(output.glob("kgpv_chile_mainland.*"))
            if p.suffix in {".shp", ".shx", ".dbf", ".prj", ".cpg"}
        },
        boundary_file=boundary_path.name,
        boundary_sha256=file_sha256(boundary_path),
        sample_file=sample_path.name,
        sample_sha256=file_sha256(sample_path),
    )
