"""Direct Copernicus Climate Data Store access through the optional official SDK."""

from .client import CDS_URL, REFERENCE_IDS, CDSClient, CDSDownload, CDSRequest
from .era5 import era5_requests

__all__ = ["CDS_URL", "REFERENCE_IDS", "CDSClient", "CDSDownload", "CDSRequest", "era5_requests"]
