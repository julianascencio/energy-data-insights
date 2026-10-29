"""Streaming, equal-year monthly climatologies with explicit coverage gates."""

from __future__ import annotations

import json
from collections.abc import Iterable

import numpy as np
import pandas as pd
import xarray as xr

REFERENCE_IDS = ("ascencio_vasquez_2021_thesis", "ascencio_vasquez_2019_kgpv")


def monthly_climatology(
    batches: Iterable[xr.DataArray],
    *,
    start_year: int,
    end_year: int,
    minimum_valid_years: int | None = None,
) -> xr.Dataset:
    """Consume one monthly archive at a time, retaining twelve sums/counts per cell.

    Every calendar month in the requested period must be present exactly once.
    By default each cell also needs every year for every month. Relaxing the cell
    gate is explicit; the returned counts expose unequal sampling. Temperature
    monthly means and precipitation monthly totals are averaged across years,
    never summed across the baseline. No interpolation or missing-to-zero fill.
    """
    if (
        type(start_year) is not int
        or type(end_year) is not int
        or not 1 <= start_year <= end_year <= 9998
    ):
        raise ValueError("Use ordered integer baseline years")
    years = end_year - start_year + 1
    required = years if minimum_valid_years is None else minimum_valid_years
    if type(required) is not int or not 1 <= required <= years:
        raise ValueError("minimum_valid_years must be within the baseline length")
    expected = set(pd.period_range(f"{start_year}-01", f"{end_year}-12", freq="M"))
    seen: set[pd.Period] = set()
    total: xr.DataArray | None = None
    count: xr.DataArray | None = None
    attrs: dict[str, object] = {}
    files: list[str] = []
    name = ""
    for batch in batches:
        if "time" not in batch.dims or not batch.name:
            raise ValueError("Each batch needs a named variable and a time dimension")
        if batch.sizes["time"] == 0:
            continue
        periods = pd.DatetimeIndex(batch.time.values).to_period("M")
        if periods.has_duplicates or periods.hasnans or not periods.is_monotonic_increasing:
            raise ValueError("Duplicate or unordered calendar months")
        keep = np.array([period in expected for period in periods])
        batch = batch.isel(time=np.flatnonzero(keep))
        selected = set(periods[keep])
        if not selected:
            continue
        if seen & selected:
            raise ValueError("Overlapping calendar months between input archives")
        seen.update(selected)
        if total is None:
            name = str(batch.name)
            attrs = dict(batch.attrs)
            template = batch.isel(time=0, drop=True).astype(float)
            total = xr.zeros_like(template).expand_dims(month=np.arange(1, 13)).copy()
            count = xr.zeros_like(total, dtype=np.int32)
        else:
            if batch.name != name or batch.attrs.get("units") != attrs.get("units"):
                raise ValueError("Batches must have the same variable and units")
            for key in ("source", "product_version", "infilled"):
                if batch.attrs.get(key) != attrs.get(key):
                    raise ValueError(f"Batches disagree on {key}")
            if set(batch.dims) - {"time"} != set(total.dims) - {"month"}:
                raise ValueError("Batches must have identical spatial dimensions")
            xr.align(total.isel(month=0, drop=True), batch.isel(time=0, drop=True), join="exact")
        assert count is not None
        finite = batch.where(np.isfinite(batch))
        sums = (
            finite.groupby("time.month")
            .sum("time", skipna=True)
            .reindex(month=np.arange(1, 13), fill_value=0)
        )
        counts = (
            finite.groupby("time.month").count("time").reindex(month=np.arange(1, 13), fill_value=0)
        )
        total = total + sums
        count = count + counts
        if "source_file" in batch.attrs:
            files.append(str(batch.attrs["source_file"]))
    if total is None or count is None or seen != expected:
        raise ValueError(f"Incomplete baseline: {len(expected - seen)} calendar months missing")
    mean = (total / count.where(count > 0)).where(count >= required).rename(name)
    attrs.pop("source_file", None)
    mean.attrs.update(
        attrs,
        baseline_start_year=start_year,
        baseline_end_year=end_year,
        minimum_valid_years=required,
        aggregation="equal-year monthly climatology",
    )
    result = xr.Dataset({name: mean, "valid_years": count.astype(np.int32)})
    result.attrs.update(
        baseline_start_year=start_year,
        baseline_end_year=end_year,
        source_files=json.dumps(files),
        minimum_valid_years=required,
    )
    result.valid_years.attrs.update(units="1", long_name="valid years per calendar month and cell")
    return result
