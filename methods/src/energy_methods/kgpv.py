"""Köppen-Geiger-Photovoltaic classification: 2019 Fig. A1 and Table 4.

The thesis is the primary citation. Classification uses the paper's precedence
and fixed irradiation thresholds, not a fresh percentile fit to each region.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import xarray as xr
from numpy.typing import ArrayLike, NDArray

REFERENCE_IDS = ("ascencio_vasquez_2021_thesis", "ascencio_vasquez_2019_kgpv", "kottek_2006_kg")
ZONE_CODES = ("", "AH", "AK", "BH", "BK", "CH", "CK", "DL", "DM", "DH", "EL", "EM", "FL")
TP_NAMES = {
    "A": "Tropical",
    "B": "Desert",
    "C": "Steppe",
    "D": "Temperate",
    "E": "Cold",
    "F": "Polar",
}
IRRADIATION_NAMES = {"L": "Low", "M": "Medium", "H": "High", "K": "Very high"}
# Table 4, columns L M H K, rows A..F. Zero is reserved for missing data.
_MERGE = np.array(
    [[1, 1, 1, 2], [3, 3, 3, 4], [5, 5, 5, 6], [7, 8, 9, 9], [10, 11, 11, 11], [12, 12, 12, 12]],
    dtype=np.uint8,
)


@dataclass(frozen=True, slots=True)
class KGPVResult:
    """Cellwise classifications; empty raw labels / class ID zero mean no data."""

    tp_zone: NDArray[np.str_]
    irradiation_zone: NDArray[np.str_]
    raw_zone: NDArray[np.str_]
    zone: NDArray[np.str_]
    class_id: NDArray[np.uint8]
    precipitation_threshold_mm: NDArray[np.float64]


def _inclusive_le(left: NDArray[np.float64], right: NDArray[np.float64]) -> NDArray[np.bool_]:
    # Bound only round-off from twelve-month reductions, not observational uncertainty.
    tolerance = 8 * np.finfo(float).eps * np.maximum(1, np.maximum(np.abs(left), np.abs(right)))
    return left <= right + tolerance


def classify_kgpv(
    temperature_c: ArrayLike,
    precipitation_mm: ArrayLike,
    annual_ghi_kwh_m2: ArrayLike,
    latitude: ArrayLike,
) -> KGPVResult:
    """Classify one cell or any grid with a final January..December axis of length 12.

    Temperature is monthly mean Celsius, precipitation monthly total mm, GHI
    annual irradiation kWh/m². Other inputs must broadcast to the spatial shape.
    NaN in any required month yields no data; infinity/negative rain/GHI fail.
    Summer = Apr-Sep in the north (including equator), Oct-Mar in the south.
    Kottek Eq. 2.1 uses two thirds seasonal rain, not the later 70% variant.

    Precedence: polar (warmest <=10), desert (P<=5*Pth), steppe (P<=10*Pth),
    tropical (coldest >=18), temperate (coldest >-3), cold. Exact 18 is assigned
    tropical to close Fig. A1's strict-inequality gap. I-zone upper edges are
    inclusive: L<=1130, M<=1560, H<=2070; this equality convention is explicit.
    """
    temperature = np.asarray(temperature_c, dtype=float)
    rain = np.asarray(precipitation_mm, dtype=float)
    if temperature.shape != rain.shape or temperature.ndim < 1 or temperature.shape[-1] != 12:
        raise ValueError("Temperature and precipitation must share shape (..., 12), Jan..Dec")
    shape = temperature.shape[:-1]
    ghi = np.broadcast_to(np.asarray(annual_ghi_kwh_m2, dtype=float), shape)
    lat = np.broadcast_to(np.asarray(latitude, dtype=float), shape)
    if (
        np.isinf(temperature).any()
        or np.isinf(rain).any()
        or np.isinf(ghi).any()
        or (rain < 0).any()
        or (ghi < 0).any()
    ):
        raise ValueError("Inputs cannot contain infinity or negative precipitation/irradiation")
    if not np.isfinite(lat).all() or (np.abs(lat) > 90).any():
        raise ValueError("Latitude must be finite and within -90..90")
    valid = (
        np.isfinite(temperature).all(axis=-1) & np.isfinite(rain).all(axis=-1) & np.isfinite(ghi)
    )
    annual_rain = rain.sum(axis=-1)
    north_summer = rain[..., 3:9].sum(axis=-1)
    summer = np.where(lat >= 0, north_summer, annual_rain - north_summer)
    winter = annual_rain - summer
    offset = np.where(
        winter >= annual_rain * (2 / 3), 0, np.where(summer >= annual_rain * (2 / 3), 28, 14)
    )
    threshold = 2 * temperature.mean(axis=-1) + offset
    coldest = temperature.min(axis=-1)
    tp = np.select(
        [
            temperature.max(axis=-1) <= 10,
            _inclusive_le(annual_rain, 5 * threshold),
            _inclusive_le(annual_rain, 10 * threshold),
            coldest >= 18,
            coldest > -3,
        ],
        [5, 1, 2, 0, 3],
        default=4,
    )
    irradiation = np.searchsorted([1130.0, 1560.0, 2070.0], ghi, side="left")
    tp_label = np.where(valid, np.array(list("ABCDEF"))[tp], "")
    i_label = np.where(valid, np.array(list("LMHK"))[irradiation], "")
    ids = np.where(valid, _MERGE[tp, irradiation], 0).astype(np.uint8)
    return KGPVResult(
        tp_label,
        i_label,
        np.char.add(tp_label, i_label),
        np.array(ZONE_CODES)[ids],
        ids,
        np.where(valid, threshold, np.nan),
    )


def map_kgpv(
    temperature: xr.DataArray, precipitation: xr.DataArray, annual_ghi: xr.DataArray
) -> xr.Dataset:
    """Create an auditable map on exactly aligned lat/lon grids and baseline years.

    Use mapping.regrid explicitly on continuous inputs before calling. Missing
    land/ocean cells stay missing. Supply a land mask to inputs when needed;
    CRU TS already excludes Antarctica. The method never invents irradiation.
    """
    for data, unit in ((temperature, "degC"), (precipitation, "mm"), (annual_ghi, "kWh m-2")):
        if data.attrs.get("units") != unit:
            raise ValueError(f"Expected units={unit!r}")
    for data in (temperature, precipitation):
        if set(data.dims) != {"month", "lat", "lon"} or not np.array_equal(
            data.month, np.arange(1, 13)
        ):
            raise ValueError("Climatologies need month=1..12, lat and lon dimensions")
    if set(annual_ghi.dims) != {"lat", "lon"}:
        raise ValueError("Annual GHI needs lat and lon dimensions")
    temperature, precipitation, annual_ghi = xr.align(
        temperature, precipitation, annual_ghi, join="exact"
    )
    for key in ("baseline_start_year", "baseline_end_year"):
        values = [data.attrs.get(key) for data in (temperature, precipitation, annual_ghi)]
        if values[0] is None or len(set(values)) != 1:
            raise ValueError(f"Inputs must declare the same {key}")
    result = classify_kgpv(
        temperature.transpose("lat", "lon", "month").values,
        precipitation.transpose("lat", "lon", "month").values,
        annual_ghi.transpose("lat", "lon").values,
        temperature.lat.values[:, None],
    )
    dims = ("lat", "lon")
    output = xr.Dataset(
        {
            "kgpv_class": (dims, result.class_id),
            "kgpv_zone": (dims, result.zone),
            "raw_zone": (dims, result.raw_zone),
            "tp_zone": (dims, result.tp_zone),
            "irradiation_zone": (dims, result.irradiation_zone),
            "precipitation_threshold_mm": (dims, result.precipitation_threshold_mm),
        },
        coords={"lat": temperature.lat, "lon": temperature.lon},
    )
    output.lat.attrs.update(standard_name="latitude", units="degrees_north", axis="Y")
    output.lon.attrs.update(standard_name="longitude", units="degrees_east", axis="X")
    output.kgpv_class.attrs.update(
        units="1",
        flag_values=np.arange(13, dtype=np.int16),
        flag_meanings="no_data " + " ".join(ZONE_CODES[1:]),
    )
    output.precipitation_threshold_mm.attrs["units"] = "mm"
    output.attrs.update(
        method="KGPV 2019; Fig. A1 and Table 4",
        references="; ".join(REFERENCE_IDS),
        irradiation_thresholds_kwh_m2="1130,1560,2070; upper edges inclusive",
        baseline_start_year=temperature.attrs["baseline_start_year"],
        baseline_end_year=temperature.attrs["baseline_end_year"],
        temperature_source=str(temperature.attrs.get("source", "caller supplied")),
        precipitation_source=str(precipitation.attrs.get("source", "caller supplied")),
        irradiation_source=str(annual_ghi.attrs.get("source", "caller supplied")),
    )
    return output
