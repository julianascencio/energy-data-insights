"""Acquire the public, CC0 CHELSACanaryClim 1979-2013 climatology."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from energy_data_retrieval.transport import HTTPClient, RequestRecord

CANARY_CLIM_HOSTS = frozenset({"os.zhdk.cloud.switch.ch"})
BASE_URL = "https://os.zhdk.cloud.switch.ch/chelsa01/chelsa_canaryclim/canaries/climatologies"
REFERENCE_IDS = ("canaryclim_2025_data", "patino_2023_canaryclim")


class CanaryClimClient:
    """Download individual COGs with the shared bounded, checksummed transport.

    Configure a response limit of 160 MB for the present monthly files. The
    2025 COGs encode temperature in 0.1 K and precipitation in 0.1 mm/month;
    readers must apply the embedded scale/offset after masking raw nodata.
    File pixel spacing must not be confused with validated climate resolution.
    """

    def __init__(self, http: HTTPClient) -> None:
        self.http = http

    def download_month(
        self,
        directory: Path,
        variable: Literal["tas", "pr"],
        month: int,
        *,
        expected_sha256: str | None = None,
    ) -> tuple[Path, RequestRecord]:
        if variable not in {"tas", "pr"}:
            raise ValueError("CanaryClim variable must be tas or pr")
        if type(month) is not int or not 1 <= month <= 12:
            raise ValueError("month must be an integer in 1..12")
        name = f"CHELSACanaryClim_{variable}_{month:02d}_1979-2013_V.1.0.tif"
        path = Path(directory) / name
        record = self.http.download_file(
            f"{BASE_URL}/{variable}/1979-2013/{name}",
            path,
            expected_sha256=expected_sha256,
        )
        return path, record
