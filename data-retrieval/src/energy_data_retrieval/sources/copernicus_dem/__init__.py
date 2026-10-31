"""Copernicus DEM GLO-30 Public COGs."""

from .client import (
    COPERNICUS_DEM_HOSTS,
    COPERNICUS_DEM_SOURCE,
    CopernicusDEMClient,
    tile_name,
)

__all__ = ["COPERNICUS_DEM_HOSTS", "COPERNICUS_DEM_SOURCE", "CopernicusDEMClient", "tile_name"]
