"""Public-domain Natural Earth country shapefiles."""

from energy_data_retrieval.sources.natural_earth.client import (
    NATURAL_EARTH_HOSTS,
    BoundaryDownload,
    NaturalEarthClient,
)

__all__ = ["NATURAL_EARTH_HOSTS", "BoundaryDownload", "NaturalEarthClient"]
