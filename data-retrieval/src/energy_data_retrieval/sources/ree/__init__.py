"""Spain's public REData generation-by-technology observations."""

from energy_data_retrieval.sources.ree.client import (
    GENERATION_ENDPOINT,
    REE_HOSTS,
    REE_SYSTEMS,
    REEClient,
    REEGeneration,
    normalize_generation,
)

__all__ = [
    "GENERATION_ENDPOINT",
    "REE_HOSTS",
    "REE_SYSTEMS",
    "REEClient",
    "REEGeneration",
    "normalize_generation",
]
