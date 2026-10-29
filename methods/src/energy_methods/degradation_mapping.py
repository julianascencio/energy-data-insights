"""Annual stress processing and geographic degradation maps with explicit assumptions."""

from __future__ import annotations

import json
from itertools import pairwise
from typing import Literal

import numpy as np
import pandas as pd
import xarray as xr

from energy_methods.degradation import REFERENCE_IDS, DegradationParameters, degradation_rates
from energy_methods.kgpv import ZONE_CODES
from energy_methods.mapping import cell_areas_km2, normalize_grid

STRESS_UNITS = {
    "module_temperature_mean_c": "degC",
    "module_temperature_upper_c": "degC",
    "module_temperature_lower_c": "degC",
    "relative_humidity_percent": "%",
    "uv_dose_kwh_m2": "kWh m-2 year-1",
    "cycles_per_year": "year-1",
}
RATE_VARIABLES = ("hydrolysis_rate", "photodegradation_rate", "thermomechanical_rate", "total_rate")
RATE_UNITS = "% year-1"
DAILY_EXTREMA_CONVENTION = (
    "UTC hourly interval means; annual mean module temperature and ambient RH; "
    "upper/lower are annual means of daily maxima/minima; integrated 280-400 nm UV; "
    "explicit cycles/year. Repository aggregation, not an exact published raster reproduction."
)


def annual_stresses(weather: xr.Dataset, *, year: int, cycles_per_year: float) -> xr.Dataset:
    """Process ONE complete UTC calendar year of hourly regional weather.

    Inputs: module_temperature_c [degC], relative_humidity_percent [%], and
    uv_irradiance_w_m2 [W m-2], each (time, lat, lon). Time labels are timezone-naive
    datetime64 UTC interval starts; dataset time_zone must be 'UTC'. UV means
    280-400 nm; native ERA5 UV to 440 nm is not interchangeable.

    Arithmetic RH and mean daily extrema are explicit implementation choices;
    use prepared annual stresses when a calibration uses other conventions.
    Any missing hourly input masks the whole cell-year; valid_hour_count remains.
    No annualization of partial coverage, interpolation, or inferred cycle count.
    Call on spatial tiles rather than loading a global hourly year into memory.
    """
    if isinstance(year, bool) or not isinstance(year, int) or not 1678 <= year <= 2261:
        raise ValueError("year must be an integer within datetime64[ns] range")
    if not np.isfinite(cycles_per_year) or cycles_per_year < 0:
        raise ValueError("cycles_per_year must be finite and nonnegative")
    if weather.attrs.get("time_zone") != "UTC":
        raise ValueError("Hourly weather must declare time_zone='UTC'")
    if "time" not in weather.coords or weather.time.dims != ("time",):
        raise ValueError("Hourly weather requires a one-dimensional time coordinate")
    expected = pd.date_range(f"{year}-01-01", f"{year + 1}-01-01", freq="h", inclusive="left")
    if not np.issubdtype(weather.time.dtype, np.datetime64) or not np.array_equal(
        weather.time.values, expected.values
    ):
        raise ValueError("Weather must contain exactly one complete UTC year of hourly starts")
    variables = {
        "module_temperature_c": "degC",
        "relative_humidity_percent": "%",
        "uv_irradiance_w_m2": "W m-2",
    }
    grids = {}
    for name, units in variables.items():
        value = weather[name]
        if set(value.dims) != {"time", "lat", "lon"} or value.attrs.get("units") != units:
            raise ValueError(f"{name} requires (time, lat, lon) and units={units!r}")
        value = normalize_grid(value).transpose("time", "lat", "lon")
        if np.isinf(value).any():
            raise ValueError(f"{name} cannot contain infinity")
        grids[name] = value
    temperature, rh, uv = (grids[name] for name in variables)
    if (temperature <= -273.15).any() or ((rh < 0) | (rh > 100)).any() or (uv < 0).any():
        raise ValueError("Invalid hourly temperature, humidity or UV irradiance")
    valid = np.isfinite(temperature) & np.isfinite(rh) & np.isfinite(uv)
    count = valid.sum("time")
    complete = count == len(expected)
    daily = temperature.resample(time="1D")
    result = xr.Dataset(
        {
            "module_temperature_mean_c": temperature.mean("time", skipna=False),
            "module_temperature_upper_c": daily.max(skipna=False).mean("time", skipna=False),
            "module_temperature_lower_c": daily.min(skipna=False).mean("time", skipna=False),
            "relative_humidity_percent": rh.mean("time", skipna=False),
            "uv_dose_kwh_m2": uv.sum("time", skipna=False) / 1000,
            "cycles_per_year": xr.full_like(count, cycles_per_year, dtype=float),
        }
    ).where(complete)
    for name, units in STRESS_UNITS.items():
        result[name].attrs = {"units": units}
    result["valid_hour_count"] = count.astype("int32")
    result.valid_hour_count.attrs["units"] = "1"
    result.attrs = {
        "stress_convention": DAILY_EXTREMA_CONVENTION,
        "source": str(weather.attrs.get("source", "caller-provided hourly weather")),
        "reference_ids": " ".join(REFERENCE_IDS),
    }
    return result.expand_dims(year=[year])


def degradation_classes(rate: xr.DataArray, *, region: Literal["global", "europe"]) -> xr.DataArray:
    """Thesis Section 6.4 bins: 0.2%/year, overflow above 1.4 globally or 0.8 in Europe.

    Upper edges are inclusive, an explicit implementation convention. ID 0 is
    missing, ID 1 includes a true zero; no clipping of high degradation rates.
    """
    if region not in {"global", "europe"}:
        raise ValueError("region must be global or europe")
    if rate.attrs.get("units") != RATE_UNITS:
        raise ValueError(f"Degradation rates require units={RATE_UNITS!r}")
    values = np.asarray(rate.values, dtype=float)
    if np.isinf(values).any() or np.any(values < 0):
        raise ValueError("Rates must be nonnegative or NaN")
    edges = np.array([0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4][: 7 if region == "global" else 4])
    classes = np.where(np.isnan(values), 0, np.searchsorted(edges, values, side="left") + 1)
    labels = {0: "No data", 1: "[0, 0.2]"}
    labels.update({i + 2: f"({low:g}, {high:g}]" for i, (low, high) in enumerate(pairwise(edges))})
    labels[len(edges) + 1] = f">{edges[-1]:g}"
    result = xr.DataArray(
        classes.astype("int8"), coords=rate.coords, dims=rate.dims, name="rate_class"
    )
    result.attrs = {
        "units": "1",
        "bin_units": RATE_UNITS,
        "bin_region": region,
        "upper_edges": edges,
        "class_labels": json.dumps(labels),
        "nodata": 0,
        "edge_ownership": "upper-inclusive",
    }
    return result


def map_degradation(
    stresses: xr.Dataset,
    parameters: DegradationParameters,
    *,
    aggregation: Literal["mean_stress", "mean_rate"],
    region: Literal["global", "europe"] = "global",
) -> xr.Dataset:
    """Map consecutive annual (year, lat, lon) stresses on their exact grid.

    mean_stress evaluates once on equal-year mean stresses (the mapping workflow).
    mean_rate evaluates each year, then averages rates (a different, explicit
    sensitivity scenario). Cells need every stress in every year. Input dataset
    must describe stress_convention; no implicit regridding or ocean filling.
    """
    if aggregation not in {"mean_stress", "mean_rate"}:
        raise ValueError("aggregation must be mean_stress or mean_rate")
    if not str(stresses.attrs.get("stress_convention", "")).strip():
        raise ValueError("Annual stresses must describe stress_convention")
    if "year" not in stresses.coords or stresses.year.dims != ("year",):
        raise ValueError("Annual stresses require a one-dimensional year coordinate")
    years = np.asarray(stresses.year.values)
    if (
        not np.issubdtype(years.dtype, np.integer)
        or not len(years)
        or np.any(np.diff(years) != 1)
        or np.any((years < 1) | (years > 9999))
    ):
        raise ValueError("Years must be increasing, unique, consecutive integers")
    grids = {}
    for name, units in STRESS_UNITS.items():
        value = stresses[name]
        if set(value.dims) != {"year", "lat", "lon"} or value.attrs.get("units") != units:
            raise ValueError(f"{name} requires (year, lat, lon) and units={units!r}")
        if not value.sizes["lat"] or not value.sizes["lon"]:
            raise ValueError("Stress grids must not be empty")
        grids[name] = normalize_grid(value).transpose("year", "lat", "lon")
    annual = xr.Dataset(grids)
    # Validate original annual values even when a mean could conceal bad inputs.
    yearly_rates = degradation_rates(
        **{k: v.values for k, v in grids.items()}, parameters=parameters
    )
    valid_year = np.isfinite(yearly_rates.total)
    count = valid_year.sum(axis=0)
    template = annual.module_temperature_mean_c.isel(year=0, drop=True)
    if aggregation == "mean_stress":
        rates = degradation_rates(
            **{k: v.mean("year", skipna=False).values for k, v in grids.items()},
            parameters=parameters,
        )
        values = (rates.hydrolysis, rates.photodegradation, rates.thermomechanical, rates.total)
    else:
        values = tuple(
            value.mean(axis=0)
            for value in (
                yearly_rates.hydrolysis,
                yearly_rates.photodegradation,
                yearly_rates.thermomechanical,
                yearly_rates.total,
            )
        )
    result = xr.Dataset()
    for name, value in zip(RATE_VARIABLES, values, strict=True):
        result[name] = xr.DataArray(
            np.where(count == len(years), value, np.nan),
            dims=template.dims,
            coords=template.coords,
            attrs={"units": RATE_UNITS, "long_name": name.replace("_", " ")},
        )
    result["valid_year_count"] = xr.DataArray(
        count.astype("int32"), dims=template.dims, coords=template.coords, attrs={"units": "1"}
    )
    result["rate_class"] = degradation_classes(result.total_rate, region=region)
    result.attrs = {
        "method": "Kaaya climate degradation; thesis Eqs. 3.14-3.17 and Section 6.4",
        "reference_ids": " ".join(REFERENCE_IDS),
        "baseline_start_year": int(years[0]),
        "baseline_end_year": int(years[-1]),
        "aggregation": aggregation,
        "coverage_policy": "all stresses in every year",
        "stress_convention": str(stresses.attrs["stress_convention"]),
        "source": str(stresses.attrs.get("source", "caller-provided annual stresses")),
        "calibration": json.dumps(parameters.to_dict(), sort_keys=True),
        "scope": (
            "Module-specific climate indicators; excludes LID, LeTID, PID, soiling and snow losses"
        ),
    }
    return result


def kgpv_degradation_summary(rates: xr.Dataset, kgpv: xr.DataArray) -> xr.Dataset:
    """Area-weighted mechanism means per KGPV zone on exactly matching regular grids.

    Only cells with all four rates and a known KGPV class contribute. KGPV may
    use a different climate baseline; its supplied metadata is recorded. Regrid
    class maps explicitly with nearest-neighbour before calling this function.
    """
    zones = normalize_grid(kgpv).transpose("lat", "lon")
    if (
        np.isinf(zones).any()
        or ((zones < 0) | (zones >= len(ZONE_CODES)) | (zones != np.floor(zones)))
        .where(zones.notnull(), False)
        .any()
    ):
        raise ValueError("KGPV class IDs must be 0..12 or NaN")
    layers = []
    for name in RATE_VARIABLES:
        layer = normalize_grid(rates[name]).transpose("lat", "lon")
        if layer.attrs.get("units") != RATE_UNITS or np.isinf(layer).any() or (layer < 0).any():
            raise ValueError(f"{name} must be nonnegative rates in {RATE_UNITS}")
        layer, _ = xr.align(layer, zones, join="exact")
        layers.append(layer)
    valid = xr.concat([layer.notnull() for layer in layers], dim="mechanism").all("mechanism")
    areas = cell_areas_km2(zones)
    rows = []
    for identifier in range(1, len(ZONE_CODES)):
        selected = valid & (zones == identifier)
        weights = areas.where(selected, 0)
        area = float(weights.sum())
        row = {"valid_area_km2": area, "valid_cell_count": int(selected.sum())}
        for name, layer in zip(RATE_VARIABLES, layers, strict=True):
            row[name] = float((layer.where(selected, 0) * weights).sum()) / area if area else np.nan
        rows.append(row)
    result = xr.Dataset(
        {name: ("kgpv_zone", [row[name] for row in rows]) for name in rows[0]},
        coords={"kgpv_zone": list(ZONE_CODES[1:])},
    )
    for name in RATE_VARIABLES:
        result[name].attrs["units"] = RATE_UNITS
    result.valid_area_km2.attrs["units"] = "km2"
    result.valid_cell_count.attrs["units"] = "1"
    result.attrs = {
        "weighting": "spherical grid-cell area; valid intersection only",
        "kgpv_metadata": json.dumps(dict(kgpv.attrs), default=str, sort_keys=True),
        "degradation_metadata": json.dumps(dict(rates.attrs), default=str, sort_keys=True),
        "reference_ids": " ".join((*REFERENCE_IDS, "ascencio_vasquez_2019_kgpv")),
    }
    return result
