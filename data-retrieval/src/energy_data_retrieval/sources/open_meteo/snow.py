"""ERA5-Land physical ground snow depth via Open-Meteo's historical API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd

from energy_data_retrieval.sources.open_meteo.client import Site
from energy_data_retrieval.transport import (
    HTTPClient,
    RequestRecord,
    RetrievalError,
    array_value,
    object_value,
)


@dataclass(frozen=True, slots=True)
class SnowDepthChunk:
    site: Site
    frame: pd.DataFrame
    request: RequestRecord
    cell_latitude: float
    cell_longitude: float


@dataclass(slots=True)
class OpenMeteoSnowClient:
    http: HTTPClient

    def hourly_depth(self, site: Site, start: date, end: date) -> SnowDepthChunk:
        """Fetch 1-366 days of ERA5-Land instantaneous physical depth, m -> cm.

        Explicit era5_land model, nearest cell, no elevation downscaling and UTC.
        No endpoint averaging or extra day: the thesis sums hourly depth samples.
        ERA5-Land is an alternative to the ERA5 product used by the thesis; never
        describe this as unconverted native ERA5 snow water equivalent. Open-Meteo
        documents snow-depth overestimation. Public service terms apply.
        """
        if start < date(1950, 1, 1) or not 1 <= (end - start).days + 1 <= 366:
            raise ValueError("Request 1-366 days from 1950 onward")
        response = self.http.get_json(
            "https://archive-api.open-meteo.com/v1/archive",
            {
                "latitude": str(site.latitude),
                "longitude": str(site.longitude),
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "hourly": "snow_depth",
                "models": "era5_land",
                "timezone": "UTC",
                "timeformat": "unixtime",
                "cell_selection": "nearest",
                "elevation": "nan",
            },
        )
        payload = object_value(response.value)
        hourly = object_value(payload.get("hourly"))
        units = object_value(payload.get("hourly_units"))
        if payload.get("utc_offset_seconds") != 0 or units != {
            "time": "unixtime",
            "snow_depth": "m",
        }:
            raise RetrievalError("Unexpected snow source units or clock")
        raw_time = array_value(hourly.get("time"))
        expected = pd.date_range(
            start, end + timedelta(days=1), freq="h", inclusive="left", tz="UTC"
        )
        if not all(type(t) is int for t in raw_time) or not np.array_equal(
            np.asarray(raw_time), expected.as_unit("s").to_numpy(dtype="int64")
        ):
            raise RetrievalError("Snow response has missing, duplicate or unexpected hourly labels")
        raw = array_value(hourly.get("snow_depth"))
        if len(raw) != len(expected) or not all(v is None or type(v) in (int, float) for v in raw):
            raise RetrievalError("Snow value/time lengths differ or values are nonnumeric")
        depth = np.asarray(raw, dtype=float)
        if np.isinf(depth).any() or np.any(depth < 0):
            raise RetrievalError("Snow depth must be nonnegative, finite or missing")
        lat, lon = payload.get("latitude"), payload.get("longitude")
        if (
            isinstance(lat, bool)
            or isinstance(lon, bool)
            or not isinstance(lat, (float, int))
            or not isinstance(lon, (float, int))
            or not np.isfinite(float(lat))
            or not np.isfinite(float(lon))
            or not -90 <= float(lat) <= 90
            or not -180 <= float(lon) <= 180
        ):
            raise RetrievalError("Missing or invalid selected snow grid coordinates")
        return SnowDepthChunk(
            site,
            pd.DataFrame({"timestamp": expected, "snow_depth_cm": depth * 100}),
            response.record,
            float(lat),
            float(lon),
        )
