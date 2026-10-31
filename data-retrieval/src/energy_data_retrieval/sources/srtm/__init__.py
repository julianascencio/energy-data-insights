"""NASA SRTM one-arcsecond elevation tiles."""

from .client import (
    SRTM_HOSTS,
    SRTM_SOURCE,
    SRTMClient,
    tile_name,
)

__all__ = ["SRTM_HOSTS", "SRTM_SOURCE", "SRTMClient", "tile_name"]
