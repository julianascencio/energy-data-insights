"""IGN Spain five-metre numeric WCS terrain."""

from .client import (
    IGN_TERRAIN_HOSTS,
    IGN_TERRAIN_SOURCE,
    CoverageDescription,
    IGNTerrainClient,
)

__all__ = ["IGN_TERRAIN_HOSTS", "IGN_TERRAIN_SOURCE", "CoverageDescription", "IGNTerrainClient"]
