"""GPCC precipitation source."""

from .client import GPCC_HOSTS, GPCCClient, GPCCRequest, iter_monthly

__all__ = ["GPCC_HOSTS", "GPCCClient", "GPCCRequest", "iter_monthly"]
