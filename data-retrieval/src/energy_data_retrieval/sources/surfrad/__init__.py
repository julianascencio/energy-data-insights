"""NOAA SURFRAD native daily radiation and weather-station observations."""

from energy_data_retrieval.sources.surfrad.client import (
    ARCHIVE_ENDPOINT,
    DOCUMENTATION_ENDPOINT,
    NATIVE_COLUMNS,
    REFERENCE_IDS,
    STATION_IDS,
    STATIONS_ENDPOINT,
    SURFRAD_HOSTS,
    SURFRADClient,
    SURFRADDay,
    SURFRADStations,
    normalize_day,
    normalize_stations,
    save_day,
    save_stations,
)

__all__ = [
    "ARCHIVE_ENDPOINT",
    "DOCUMENTATION_ENDPOINT",
    "NATIVE_COLUMNS",
    "REFERENCE_IDS",
    "STATIONS_ENDPOINT",
    "STATION_IDS",
    "SURFRAD_HOSTS",
    "SURFRADClient",
    "SURFRADDay",
    "SURFRADStations",
    "normalize_day",
    "normalize_stations",
    "save_day",
    "save_stations",
]
