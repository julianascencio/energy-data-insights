"""Geographic station discovery with explicit spherical-distance assumptions."""

from __future__ import annotations

from copy import deepcopy
from math import pi
from numbers import Integral, Real

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike, NDArray
from pandas.api.types import (
    is_bool_dtype,
    is_complex_dtype,
    is_datetime64_any_dtype,
    is_object_dtype,
    is_timedelta64_dtype,
)

type FloatArray = NDArray[np.float64]

EARTH_MEAN_RADIUS_KM = 6371.0088
MAX_DISTANCE_KM = pi * EARTH_MEAN_RADIUS_KM
MAX_NEARBY_STATIONS = 100_000


def _real(value: float, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite real number")
    result = float(value)
    if not np.isfinite(result):
        raise ValueError(f"{name} must be a finite real number")
    return result


def _location(latitude: float, longitude: float) -> tuple[float, float]:
    latitude = _real(latitude, "latitude")
    longitude = _real(longitude, "longitude")
    if not -90 <= latitude <= 90:
        raise ValueError("latitude must lie between -90 and 90 degrees")
    if not -180 <= longitude <= 180:
        raise ValueError("longitude must lie between -180 and 180 degrees")
    return latitude, longitude


def haversine_distance_km(
    latitude: float,
    longitude: float,
    station_latitudes: ArrayLike,
    station_longitudes: ArrayLike,
) -> FloatArray:
    """Return vectorized great-circle distances from one location, in kilometres.

    Coordinates are decimal degrees. Both station arrays must be finite, equally
    sized one-dimensional vectors, with latitude in [-90, 90] and longitude in
    [-180, 180]. The fixed mean-radius sphere has radius 6371.0088 km; distances
    are spherical approximations and do not account for elevation or terrain.
    Longitude wraps across the antimeridian. Longitude at either pole does not
    change that pole's physical location.
    """
    latitude, longitude = _location(latitude, longitude)
    latitudes = np.asarray(station_latitudes, dtype=np.float64)
    longitudes = np.asarray(station_longitudes, dtype=np.float64)
    if latitudes.ndim != 1 or longitudes.ndim != 1:
        raise ValueError("Station coordinates must be one-dimensional arrays")
    if latitudes.shape != longitudes.shape:
        raise ValueError("Station coordinate arrays must have equal lengths")
    if not np.all(np.isfinite(latitudes) & (np.abs(latitudes) <= 90)):
        raise ValueError("Station latitudes must be finite and between -90 and 90 degrees")
    if not np.all(np.isfinite(longitudes) & (np.abs(longitudes) <= 180)):
        raise ValueError("Station longitudes must be finite and between -180 and 180 degrees")

    delta_latitude = np.radians(latitudes - latitude)
    delta_longitude = np.radians((longitudes - longitude + 180) % 360 - 180)
    query_cosine = 0.0 if abs(latitude) == 90 else np.cos(np.radians(latitude))
    station_cosines = np.where(np.abs(latitudes) == 90, 0.0, np.cos(np.radians(latitudes)))
    haversine = (
        np.sin(delta_latitude / 2) ** 2
        + query_cosine * station_cosines * np.sin(delta_longitude / 2) ** 2
    )
    haversine = np.clip(haversine, 0.0, 1.0)
    return 2 * EARTH_MEAN_RADIUS_KM * np.arctan2(np.sqrt(haversine), np.sqrt(1 - haversine))


def _catalogue_coordinates(values: pd.Series) -> FloatArray:
    """Coerce numeric catalogue strings while excluding unusable coordinate types."""
    if (
        is_bool_dtype(values.dtype)
        or is_complex_dtype(values.dtype)
        or is_datetime64_any_dtype(values.dtype)
        or is_timedelta64_dtype(values.dtype)
    ):
        return np.full(len(values), np.nan)
    if is_object_dtype(values.dtype):
        values = values.mask(
            values.map(
                lambda value: isinstance(value, (bool, complex, np.bool_, np.complexfloating))
            )
        )
    return pd.to_numeric(values, errors="coerce").to_numpy(dtype=np.float64, na_value=np.nan)


def nearby_stations(
    stations: pd.DataFrame,
    latitude: float,
    longitude: float,
    *,
    radius_km: float = 100.0,
    limit: int = 20,
) -> pd.DataFrame:
    """Rank station candidates inside an inclusive geographic search radius.

    Required columns are ``station_id``, ``latitude`` and ``longitude``. Original
    columns and attributes are retained in a new frame; ``distance_km`` and the
    one-based ``rank`` are added. Existing columns with either name are rejected
    to prevent overwriting source fields. Query coordinates must be finite.

    Unavailable, nonnumeric, nonfinite or out-of-range catalogue coordinates are
    excluded. Their count, the query and the sphere assumption are recorded in
    ``result.attrs["spatial_search"]``. The radius must be positive and no larger
    than half the sphere's circumference; ``limit`` must be an integer in
    [1, 100000]. Results sort by distance, then source, station ID and original
    row order for deterministic ties. No station records are deduplicated.

    Proximity alone establishes neither data availability nor suitability as a
    site's weather reference. Provider coverage, quality and local terrain need
    separate assessment.
    """
    latitude, longitude = _location(latitude, longitude)
    radius_km = _real(radius_km, "radius_km")
    if not 0 < radius_km <= MAX_DISTANCE_KM:
        raise ValueError(f"radius_km must be positive and at most {MAX_DISTANCE_KM} km")
    if (
        isinstance(limit, (bool, np.bool_))
        or not isinstance(limit, Integral)
        or not 1 <= limit <= MAX_NEARBY_STATIONS
    ):
        raise ValueError(f"limit must be an integer between 1 and {MAX_NEARBY_STATIONS}")
    limit = int(limit)
    if stations.columns.has_duplicates:
        raise ValueError("Station catalogue column names must be unique")
    required = {"station_id", "latitude", "longitude"}
    if missing := required.difference(stations.columns):
        raise ValueError(f"Station catalogue lacks required columns: {', '.join(sorted(missing))}")
    if reserved := {"rank", "distance_km"}.intersection(stations.columns):
        raise ValueError(f"Station catalogue uses reserved columns: {', '.join(sorted(reserved))}")

    latitudes = _catalogue_coordinates(stations["latitude"])
    longitudes = _catalogue_coordinates(stations["longitude"])
    valid = (
        np.isfinite(latitudes)
        & np.isfinite(longitudes)
        & (np.abs(latitudes) <= 90)
        & (np.abs(longitudes) <= 180)
    )
    positions = np.flatnonzero(valid)
    distances = haversine_distance_km(latitude, longitude, latitudes[valid], longitudes[valid])
    inside = distances <= radius_km
    positions, distances = positions[inside], distances[inside]
    station_keys = stations["station_id"].astype("string").fillna("").to_numpy(dtype=str)
    source_keys = (
        stations["source"].astype("string").fillna("").to_numpy(dtype=str)
        if "source" in stations
        else np.full(len(stations), "")
    )
    order = np.lexsort((positions, station_keys[positions], source_keys[positions], distances))[
        :limit
    ]
    result = stations.iloc[positions[order]].copy().reset_index(drop=True)
    result["distance_km"] = distances[order]
    result["rank"] = np.arange(1, len(result) + 1, dtype=np.int64)
    result.attrs = deepcopy(stations.attrs)
    result.attrs["spatial_search"] = {
        "distance_method": "haversine_mean_radius_sphere",
        "earth_radius_km": EARTH_MEAN_RADIUS_KM,
        "latitude": latitude,
        "longitude": longitude,
        "radius_km": radius_km,
        "limit": limit,
        "input_station_count": len(stations),
        "invalid_coordinate_count": int(np.count_nonzero(~valid)),
        "within_radius_count": len(positions),
        "returned_station_count": len(result),
        "truncated": len(positions) > len(result),
    }
    return result
