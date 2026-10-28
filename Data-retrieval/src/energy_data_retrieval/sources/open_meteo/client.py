"""Model-explicit hourly weather with audited end-label to interval-start alignment."""

from __future__ import annotations

import math
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from enum import StrEnum

import numpy as np
import pandas as pd

from energy_data_retrieval.storage import bounded_map
from energy_data_retrieval.transport import (
    HTTPClient,
    JSONValue,
    RequestRecord,
    RetrievalError,
    array_value,
    object_value,
)

OPEN_METEO_HOSTS = frozenset(
    {
        "archive-api.open-meteo.com",
        "historical-forecast-api.open-meteo.com",
        "customer-archive-api.open-meteo.com",
        "customer-historical-forecast-api.open-meteo.com",
    }
)
_VARIABLES = ("shortwave_radiation", "temperature_2m", "wind_speed_10m", "wind_gusts_10m")


class WeatherProduct(StrEnum):
    ERA5 = "era5"
    IFS = "ifs"


@dataclass(frozen=True, slots=True)
class Site:
    site_id: str
    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if (
            not self.site_id
            or not math.isfinite(self.latitude)
            or not math.isfinite(self.longitude)
        ):
            raise ValueError("A nonempty site ID and finite coordinates are required")
        if not -90 <= self.latitude <= 90 or not -180 <= self.longitude <= 180:
            raise ValueError("WGS84 latitude/longitude out of range")


@dataclass(frozen=True, slots=True)
class WeatherChunk:
    site: Site
    start: date
    end: date
    product: WeatherProduct
    frame: pd.DataFrame
    request: RequestRecord
    cell_latitude: float
    cell_longitude: float


@dataclass(slots=True)
class OpenMeteoClient:
    http: HTTPClient
    product: WeatherProduct = WeatherProduct.ERA5
    api_key: str | None = field(default=None, repr=False)
    chunk_days: int = 31

    def __post_init__(self) -> None:
        if not 1 <= self.chunk_days <= 366:
            raise ValueError("chunk_days must be between 1 and 366")

    def weather(self, site: Site, start: date, end: date) -> WeatherChunk:
        """Read a finite UTC date chunk with one extra day for end samples.

        No implicit Best Match product is used. Both products are modelled data,
        not station measurements. Native nearest-cell selection disables elevation
        downscaling. Public and customer endpoints never share credential caches.
        """
        if start > end or (end - start).days + 1 > self.chunk_days:
            raise ValueError("Request must be a nonempty chunk within chunk_days")
        host = (
            "archive-api.open-meteo.com"
            if self.product == WeatherProduct.ERA5
            else "historical-forecast-api.open-meteo.com"
        )
        if self.api_key:
            host = "customer-" + host
        endpoint = f"https://{host}/v1/" + (
            "archive" if self.product == WeatherProduct.ERA5 else "forecast"
        )
        parameters = {
            "latitude": str(site.latitude),
            "longitude": str(site.longitude),
            "start_date": start.isoformat(),
            "end_date": (end + timedelta(days=1)).isoformat(),
            "hourly": ",".join(_VARIABLES),
            "models": "era5" if self.product == WeatherProduct.ERA5 else "ecmwf_ifs",
            "timezone": "UTC",
            "timeformat": "unixtime",
            "wind_speed_unit": "ms",
            "temperature_unit": "celsius",
            "cell_selection": "nearest",
            "elevation": "nan",
        }
        response = self.http.get_json(
            endpoint,
            parameters,
            secrets={"apikey": self.api_key} if self.api_key else None,
        )
        payload = object_value(response.value)
        frame = normalize_hourly(payload, site.site_id, start, end, product=self.product)
        latitude, longitude = payload.get("latitude"), payload.get("longitude")
        if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
            raise RetrievalError("Weather response omits selected grid coordinates")
        return WeatherChunk(
            site,
            start,
            end,
            self.product,
            frame,
            response.record,
            float(latitude),
            float(longitude),
        )

    def iter_weather(
        self,
        sites: Iterable[Site],
        start: date,
        end: date,
        *,
        workers: int = 2,
    ) -> Iterator[WeatherChunk]:
        """Yield bounded location/date partitions without collecting a fleet history."""
        if start > end:
            raise ValueError("start must be on or before end")

        def jobs() -> Iterator[tuple[Site, date, date]]:
            seen: set[str] = set()
            for site in sites:
                if site.site_id in seen:
                    raise ValueError("Site IDs must be unique")
                seen.add(site.site_id)
                current = start
                while current <= end:
                    stop = min(end, current + timedelta(days=self.chunk_days - 1))
                    yield site, current, stop
                    current = stop + timedelta(days=1)

        def fetch(job: tuple[Site, date, date]) -> WeatherChunk:
            return self.weather(*job)

        yield from bounded_map(fetch, jobs(), workers=workers)


def normalize_hourly(
    payload: dict[str, JSONValue],
    site_id: str,
    start: date,
    end: date,
    *,
    product: WeatherProduct,
) -> pd.DataFrame:
    """Align GHI, temperature and wind to identical one-hour UTC intervals.

    Radiation is the preceding-hour mean at interval end. Temperature and wind
    are means of the two instantaneous endpoints and remain null if either is
    missing. Forecast gust is the preceding-hour maximum; the archive defines
    ERA5 gust at the indicated hour, so its end sample is explicitly retained as
    instantaneous and must not be called a measured or hourly maximum.
    """
    if payload.get("utc_offset_seconds") != 0:
        raise RetrievalError("Weather source did not return the requested UTC clock")
    hourly = object_value(payload.get("hourly"))
    units = object_value(payload.get("hourly_units"))
    expected_units = {
        "shortwave_radiation": {"W/m²", "W/m2"},
        "temperature_2m": {"°C", "celsius"},
        "wind_speed_10m": {"m/s"},
        "wind_gusts_10m": {"m/s"},
    }
    for variable, allowed in expected_units.items():
        unit = units.get(variable)
        if not isinstance(unit, str) or unit not in allowed:
            raise RetrievalError(f"Unexpected source unit for {variable}")
    raw_time = array_value(hourly.get("time"))
    if len(raw_time) < 2 or not all(
        isinstance(t, int) and not isinstance(t, bool) for t in raw_time
    ):
        raise RetrievalError("Weather time must contain at least two Unix-second integer labels")
    time_axis = np.asarray(raw_time, dtype=np.int64)
    if not np.all(np.diff(time_axis) == 3600):
        raise RetrievalError("Weather source has a duplicate, gap or nonhourly timestamp")
    values: dict[str, np.ndarray] = {}
    for variable in _VARIABLES:
        raw = array_value(hourly.get(variable))
        if len(raw) != len(time_axis):
            raise RetrievalError("Weather value/time lengths differ")
        if not all(
            value is None or (isinstance(value, (int, float)) and not isinstance(value, bool))
            for value in raw
        ):
            raise RetrievalError("Weather source contains a nonnumeric observation")
        vector = np.asarray(raw, dtype=np.float64)
        if np.isinf(vector).any():
            raise RetrievalError("Weather source contains infinite values")
        values[variable] = vector
    timestamps = pd.to_datetime(time_axis[:-1], unit="s", utc=True)
    frame = pd.DataFrame(
        {
            "site_id": site_id,
            "timestamp": timestamps,
            "duration_hours": 1.0,
            "ghi_wm2": values["shortwave_radiation"][1:],
            "temperature_c": (values["temperature_2m"][:-1] + values["temperature_2m"][1:]) / 2,
            "wind_speed_ms": (values["wind_speed_10m"][:-1] + values["wind_speed_10m"][1:]) / 2,
            "gust_ms": values["wind_gusts_10m"][1:],
        }
    )
    begin = pd.Timestamp(datetime.combine(start, datetime.min.time(), UTC))
    stop = pd.Timestamp(datetime.combine(end + timedelta(days=1), datetime.min.time(), UTC))
    frame = frame.loc[(frame["timestamp"] >= begin) & (frame["timestamp"] < stop)].reset_index(
        drop=True
    )
    expected_hours = (end - start).days * 24 + 24
    if len(frame) != expected_hours:
        raise RetrievalError(
            "Weather response lacks requested interval endpoints; no values were filled"
        )
    frame.attrs.update(
        source="Open-Meteo",
        product=product.value,
        timestamp_convention="UTC interval start",
        ghi_alignment="preceding-hour mean at interval end",
        temperature_wind_alignment="mean of instantaneous start/end samples",
        gust_alignment=(
            "preceding-hour maximum at end"
            if product == WeatherProduct.IFS
            else "instantaneous end sample"
        ),
        station_observations=False,
        spatial_selection="nearest native grid cell; no elevation downscaling",
    )
    return frame
