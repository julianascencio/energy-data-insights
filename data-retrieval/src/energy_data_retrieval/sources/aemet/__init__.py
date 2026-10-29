"""AEMET OpenData station inventory, daily climate and recent observations."""

from energy_data_retrieval.sources.aemet.client import (
    AEMET_HOSTS,
    REFERENCE_IDS,
    STATIONS_ENDPOINT,
    AEMETClient,
    AEMETDataset,
    daily_chunks,
    normalize_daily,
    normalize_recent,
    normalize_stations,
    save_dataset,
)

__all__ = [
    "AEMET_HOSTS",
    "REFERENCE_IDS",
    "STATIONS_ENDPOINT",
    "AEMETClient",
    "AEMETDataset",
    "daily_chunks",
    "normalize_daily",
    "normalize_recent",
    "normalize_stations",
    "save_dataset",
]
