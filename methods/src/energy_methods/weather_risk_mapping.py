"""Complete-year processing and labelled maps for soiling and snow shading."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import xarray as xr

from energy_methods.mapping import normalize_grid
from energy_methods.weather_risk import (
    REFERENCE_IDS,
    RISK_LABELS,
    SNOW_EDGES,
    SOILING_EDGES,
    snow_loss_from_exposure,
    snow_risk_classes,
    soiling_rate_from_aod,
    soiling_risk_classes,
)


def _time_grid(data: xr.DataArray, *, year: int, frequency: str, units: str) -> xr.DataArray:
    if isinstance(year, bool) or not isinstance(year, int) or not 1678 <= year <= 2261:
        raise ValueError("year must be an integer within the datetime64[ns] range")
    if set(data.dims) != {"time", "lat", "lon"} or data.attrs.get("units") != units:
        raise ValueError(f"Expected (time, lat, lon) with units={units!r}")
    if data.attrs.get("time_zone") != "UTC":
        raise ValueError("Time labels must declare time_zone='UTC'")
    expected = pd.date_range(f"{year}-01-01", f"{year + 1}-01-01", freq=frequency, inclusive="left")
    if not np.issubdtype(data.time.dtype, np.datetime64) or not np.array_equal(
        data.time.values, expected.values
    ):
        raise ValueError("A complete, ordered UTC calendar year is required; no gaps or duplicates")
    if np.isinf(data.values).any() or np.any(data.values < 0):
        raise ValueError("Inputs must be nonnegative and finite, or NaN")
    return normalize_grid(data).transpose("time", "lat", "lon")


def annual_risk_inputs(
    daily_aod550: xr.DataArray, hourly_snow_depth: xr.DataArray, *, year: int
) -> xr.Dataset:
    """Make annual indicators from daily AOD550 [1] and hourly ground snow [cm].

    Both fields require exact matching lat/lon centres and a complete UTC time
    axis, including leap days. Snow must declare snow_depth_kind='physical_ground'.
    NaN values mask only the affected indicator/cell/year; counts remain visible.
    No partial-year annualization, inferred density, gap filling or coastal mask.
    Regrid continuous inputs explicitly before calling, if necessary.
    """
    if daily_aod550.attrs.get("wavelength_nm") != 550:
        raise ValueError("AOD must explicitly declare wavelength_nm=550")
    if hourly_snow_depth.attrs.get("snow_depth_kind") != "physical_ground":
        raise ValueError("Snow must declare physical_ground depth, not water equivalent")
    aod = _time_grid(daily_aod550, year=year, frequency="D", units="1")
    snow = _time_grid(hourly_snow_depth, year=year, frequency="h", units="cm")
    # Different daily/hourly time axes are intentional; only spatial axes align.
    xr.align(aod.isel(time=0, drop=True), snow.isel(time=0, drop=True), join="exact")
    result = xr.Dataset(
        {
            "aod550_mean": aod.mean("time", skipna=False),
            "snow_depth_sum": snow.sum("time", skipna=False),
            "valid_aod_days": aod.count("time").astype("int32"),
            "valid_snow_hours": snow.count("time").astype("int32"),
        }
    )
    result.aod550_mean.attrs = {"units": "1", "wavelength_nm": 550}
    result.snow_depth_sum.attrs = {"units": "cm h", "snow_depth_kind": "physical_ground"}
    for name in ("valid_aod_days", "valid_snow_hours"):
        result[name].attrs["units"] = "1"
    result.attrs = {
        "aod_source": str(aod.attrs.get("source", "caller-provided daily AOD550")),
        "snow_source": str(snow.attrs.get("source", "caller-provided hourly physical ground snow")),
        "coverage": "complete UTC year; any missing value masks its indicator-cell-year",
        "reference_ids": " ".join(REFERENCE_IDS),
    }
    return result.expand_dims(year=[year])


def map_weather_risks(annual_inputs: xr.Dataset) -> xr.Dataset:
    """Map annual-mean soiling rates and annual snow losses over consecutive years.

    Require aod550_mean [1] and snow_depth_sum [cm h] on (year, lat, lon).
    Apply each nonlinear equation to EACH year's indicator, then average the
    resulting rates/losses with skipna=False before assigning labels. This explicit
    repository convention is not specified in full in the thesis's global maps.
    Annual estimates are retained so aggregation is inspectable. The caller masks
    oceans and supplies a validated baseline; this function never fills gaps.
    """
    if "year" not in annual_inputs.coords or annual_inputs.year.dims != ("year",):
        raise ValueError("A one-dimensional year coordinate is required")
    years = np.asarray(annual_inputs.year.values)
    if (
        len(years) == 0
        or not np.issubdtype(years.dtype, np.integer)
        or np.any((years < 1678) | (years > 2261))
        or np.any(np.diff(years) != 1)
    ):
        raise ValueError("Years must be consecutive, unique, increasing integers")
    fields = []
    for name, units in (("aod550_mean", "1"), ("snow_depth_sum", "cm h")):
        data = annual_inputs[name]
        if set(data.dims) != {"year", "lat", "lon"} or data.attrs.get("units") != units:
            raise ValueError(f"{name} requires (year, lat, lon) and units={units!r}")
        fields.append(normalize_grid(data).transpose("year", "lat", "lon"))
    aod, snow = xr.align(*fields, join="exact")
    if aod.attrs.get("wavelength_nm") != 550:
        raise ValueError("AOD must explicitly declare wavelength_nm=550")
    if snow.attrs.get("snow_depth_kind") != "physical_ground":
        raise ValueError("Snow must declare physical_ground depth, not water equivalent")
    annual_soiling = aod.copy(data=soiling_rate_from_aod(aod.values))
    annual_snow = snow.copy(data=snow_loss_from_exposure(snow.values))
    annual_soiling.attrs = {"units": "% day-1", "equation": "thesis 3.2"}
    annual_snow.attrs = {"units": "%", "equation": "thesis 3.3-3.4"}
    soiling = annual_soiling.mean("year", skipna=False, keep_attrs=True)
    snow_loss = annual_snow.mean("year", skipna=False, keep_attrs=True)
    result = xr.Dataset(
        {
            "annual_soiling_rate": annual_soiling,
            "annual_snow_loss": annual_snow,
            "soiling_rate": soiling,
            "snow_loss": snow_loss,
            "soiling_risk": soiling.copy(data=soiling_risk_classes(soiling.values)),
            "snow_risk": snow_loss.copy(data=snow_risk_classes(snow_loss.values)),
        }
    )
    for name, edges, units in (
        ("soiling_risk", SOILING_EDGES, "% day-1"),
        ("snow_risk", SNOW_EDGES, "%"),
    ):
        result[name].attrs = {
            "units": "1",
            "nodata": 0,
            "upper_edges": list(edges),
            "bin_units": units,
            "edge_ownership": "upper-inclusive",
            "class_labels": json.dumps(dict(enumerate(RISK_LABELS))),
        }
    result.attrs = {
        **annual_inputs.attrs,
        "baseline_start_year": int(years[0]),
        "baseline_end_year": int(years[-1]),
        "reference_ids": " ".join(REFERENCE_IDS),
        "aggregation": (
            "equations on each annual input, then mean annual rates/losses; no missing years"
        ),
        "interpretation": (
            "empirical screening indicators; not independently validated global losses "
            "or event probabilities"
        ),
    }
    return result
