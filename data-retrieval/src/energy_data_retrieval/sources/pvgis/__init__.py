"""PVGIS solar resource, PV performance, weather, terrain and coverage APIs."""

from .client import (
    PVGIS_HOSTS,
    PVGIS6Client,
    PVGISClient,
    PVGISResponse,
    describe_endpoint,
    endpoints,
    load_response,
)

__all__ = [
    "PVGIS_HOSTS",
    "PVGIS6Client",
    "PVGISClient",
    "PVGISResponse",
    "describe_endpoint",
    "endpoints",
    "load_response",
]
