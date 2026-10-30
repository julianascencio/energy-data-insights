"""RTE/ODRÉ's attributed French generation mix."""

from energy_data_retrieval.sources.rte.client import RTE_HOSTS, RTEClient, normalize_generation

__all__ = ["RTE_HOSTS", "RTEClient", "normalize_generation"]
