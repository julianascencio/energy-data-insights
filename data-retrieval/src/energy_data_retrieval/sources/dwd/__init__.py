"""DWD CDC station discovery and native hourly solar-radiation archives."""

from energy_data_retrieval.sources.dwd.client import (
    DWD_HOSTS,
    REFERENCE_IDS,
    STATIONS_ENDPOINT,
    DWDClient,
    DWDSolar,
    DWDStations,
    normalize_solar,
    normalize_stations,
    save_solar,
    save_stations,
)

__all__ = [
    "DWD_HOSTS",
    "REFERENCE_IDS",
    "STATIONS_ENDPOINT",
    "DWDClient",
    "DWDSolar",
    "DWDStations",
    "normalize_solar",
    "normalize_stations",
    "save_solar",
    "save_stations",
]
