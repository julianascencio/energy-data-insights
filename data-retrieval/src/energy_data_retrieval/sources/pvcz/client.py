"""Read pinned PVCZ CSV data without loading upstream pickle files."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from energy_data_retrieval.sources._climate_catalogue import validate_catalogue
from energy_data_retrieval.transport import HTTPClient, RequestRecord

REFERENCE_IDS = ("karin_2019_pvcz", "karin_pvcz_software")
COMMIT = "aa89fab8d1d66f46f4ea8575e2452aa75a927535"
URL = (
    f"https://raw.githubusercontent.com/toddkarin/pvcz/{COMMIT}/pvcz/"
    "PVCZ-2019_ver0p2_world_PV_climate_stressors_and_zones.csv"
)


def download(http: HTTPClient, path: Path) -> RequestRecord:
    """Download the pinned public CSV with the shared transport's provenance."""
    return http.download_file(URL, path)


def read_catalogue(path: Path) -> pd.DataFrame:
    """Keep original stress values and authoritative labels, including rounding.

    The author CSV rounds stresses. Reclassifying a rounded value exactly on a
    threshold can disagree with its original label; do not overwrite that label.
    Three-significant-digit coordinates can coincide for distinct native cells.
    Preserve these rows; coordinates are not unique IDs or exact grid centers.
    """
    result = validate_catalogue(
        pd.read_csv(path),
        ("T_equiv_rack_1p1eV", "specific_humidity_mean", "pvcz"),
        rounded_locations=True,
    )
    if "pvcz_labeled" not in result:
        raise ValueError("Missing published PVCZ labels")
    valid = {f"T{t}:H{h}": (h - 1) * 10 + t - 1 for h in range(1, 6) for t in range(1, 11)}
    mapped = result.pvcz_labeled.map(valid)
    if mapped.isna().any() or not mapped.eq(result.pvcz).all():
        raise ValueError("Published PVCZ IDs and labels disagree")
    if ((result.specific_humidity_mean < 0) | (result.specific_humidity_mean > 1000)).any():
        raise ValueError("Expected specific humidity in g/kg")
    return result
