"""Versioned CMIP6 discovery and native NetCDF acquisition through ESGF STAC."""

from energy_data_retrieval.sources.cmip6.client import (
    CMIP6_DATA_HOSTS,
    CMIP6_INDEX_HOSTS,
    CMIP6Client,
    CMIP6File,
    CMIP6Plan,
    CMIP6Query,
    download_plan,
    load_plan,
    save_plan,
)

__all__ = [
    "CMIP6_DATA_HOSTS",
    "CMIP6_INDEX_HOSTS",
    "CMIP6Client",
    "CMIP6File",
    "CMIP6Plan",
    "CMIP6Query",
    "download_plan",
    "load_plan",
    "save_plan",
]
