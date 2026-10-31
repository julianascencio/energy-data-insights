"""Published workbook import; native feature conventions and original map labels."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

import pandas as pd

from energy_data_retrieval.sources._climate_catalogue import validate_catalogue
from energy_data_retrieval.transport import HTTPClient, RequestRecord

REFERENCE_IDS = ("triana_2026_ml_climates",)
URL = "https://ars.els-cdn.com/content/image/1-s2.0-S0960148125013473-mmc1.xlsx"
FEATURES = ("Tann", "Tmax", "Tmin", "GHIann", "GHImax", "GHImin", "UVann")
FEATURE_CONVENTION = (
    "Native supplementary-workbook statistics: temperatures in degC, radiation statistics "
    "in source J/m2 convention; GHIann is not silently converted to a physical annual total."
)


def download(http: HTTPClient, path: Path) -> RequestRecord:
    """Download the published workbook and record its content hash."""
    return http.download_file(URL, path)


def read_catalogue(path: Path) -> pd.DataFrame:
    """Read author features and labels from XLSX or the normalized CSV export.

    The workbook contains 55,418 land locations, 21 published ML labels and KGPV
    labels inherited from the earlier study. No source labels are recomputed.
    """
    if path.suffix.lower() == ".xlsx":
        with ZipFile(path) as archive:
            if sum(entry.file_size for entry in archive.infolist()) > 300_000_000:
                raise ValueError("Expanded workbook exceeds 300 MB")
        frame = pd.read_excel(path, sheet_name=0, usecols=range(18), engine="openpyxl")
        frame = frame.rename(
            columns={
                "LAT": "lat",
                "LON": "lon",
                "ML Climate zone": "ml21_zone",
                "KGPV (names)": "kgpv_zone",
            }
        )
    else:
        frame = pd.read_csv(path)
    result = validate_catalogue(frame, (*FEATURES, "Yf"))
    valid = {
        f"{prefix}{i}"
        for prefix, count in (
            ("Tro", 4),
            ("Des", 3),
            ("Mou", 3),
            ("Tem", 5),
            ("Col", 4),
            ("Pol", 2),
        )
        for i in range(1, count + 1)
    }
    kgpv = {"AH", "AK", "BH", "BK", "CH", "CK", "DL", "DM", "DH", "EL", "EM", "FL"}
    if (
        not {"ml21_zone", "kgpv_zone"} <= set(result)
        or not result.ml21_zone.isin(valid).all()
        or not result.kgpv_zone.isin(kgpv).all()
    ):
        raise ValueError("Unknown published ML21/KGPV zone label")
    return result
