"""Uruguay's public ADME SCADA generation archive."""

from .client import ADME_HOSTS, ADMEClient, parse_scada_sas

__all__ = ["ADME_HOSTS", "ADMEClient", "parse_scada_sas"]
