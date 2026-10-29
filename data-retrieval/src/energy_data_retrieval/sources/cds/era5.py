"""Explicit ERA5 single-level selections, divided into one request per month."""

from __future__ import annotations

import calendar
import math
import re
from collections.abc import Sequence
from datetime import date

from energy_data_retrieval.transport import JSONValue

from .client import CDSRequest


def era5_requests(
    start: date,
    end: date,
    *,
    variables: Sequence[str],
    area: tuple[float, float, float, float],
    monthly_means: bool = False,
    data_format: str = "grib",
) -> tuple[CDSRequest, ...]:
    """Build inclusive UTC date-label requests for ERA5 reanalysis (not ERA5-Land).

    ``area`` is [north, west, south, east] in degrees. Dateline crossing must be
    split explicitly. Hourly requests include all 24 source labels per selected
    day; no extra endpoint is added or radiation-interval alignment inferred.
    Monthly means require whole calendar months and request 00:00 by CDS convention.
    Plans are limited to 1,200 months and 64 variables, executed sequentially.
    """
    if type(start) is not date or type(end) is not date or not date(1940, 1, 1) <= start <= end:
        raise ValueError("ERA5 dates must be calendar dates ordered from 1940-01-01")
    count = (end.year - start.year) * 12 + end.month - start.month + 1
    if count > 1200:
        raise ValueError("Split ERA5 plans exceeding 1200 months")
    if isinstance(variables, str) or not 1 <= len(variables) <= 64:
        raise ValueError("Supply 1..64 explicit ERA5 variable names")
    if len(set(variables)) != len(variables) or any(
        not isinstance(v, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_]{0,127}", v)
        for v in variables
    ):
        raise ValueError("ERA5 variable names must be unique CDS identifiers")
    if len(area) != 4 or any(
        isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in area
    ):
        raise ValueError("area requires finite north, west, south, east coordinates")
    north, west, south, east = area
    if not (-90 <= south <= north <= 90 and -180 <= west <= east <= 180):
        raise ValueError("area must be ordered north/west/south/east without dateline crossing")
    if data_format not in {"grib", "netcdf"}:
        raise ValueError("data_format must be grib or netcdf")
    if not isinstance(monthly_means, bool):
        raise ValueError("monthly_means must be boolean")
    if monthly_means and (start.day != 1 or end.day != calendar.monthrange(end.year, end.month)[1]):
        raise ValueError("Monthly means require whole calendar months")
    requests = []
    for offset in range(count):
        year, month0 = divmod(start.year * 12 + start.month - 1 + offset, 12)
        month = month0 + 1
        first = start.day if offset == 0 else 1
        last = end.day if offset == count - 1 else calendar.monthrange(year, month)[1]
        selection: dict[str, JSONValue] = {
            "product_type": ["monthly_averaged_reanalysis" if monthly_means else "reanalysis"],
            "variable": [*variables],
            "year": [str(year)],
            "month": [f"{month:02d}"],
            "time": ["00:00"] if monthly_means else [f"{hour:02d}:00" for hour in range(24)],
            "area": [float(v) for v in area],
            "data_format": data_format,
            "download_format": "unarchived",
        }
        if not monthly_means:
            selection["day"] = [f"{day:02d}" for day in range(first, last + 1)]
        dataset = "reanalysis-era5-single-levels" + ("-monthly-means" if monthly_means else "")
        requests.append(CDSRequest(dataset, selection))
    return tuple(requests)
