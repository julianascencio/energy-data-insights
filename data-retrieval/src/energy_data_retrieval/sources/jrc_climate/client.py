"""JRC PVGIS climate means: bounded download and native CSV import."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from energy_data_retrieval.sources._climate_catalogue import validate_catalogue
from energy_data_retrieval.transport import HTTPClient, RequestRecord

REFERENCE_IDS = ("jrc_2025_climate_dataset", "medina_2026_pv_climates")
URL = "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/PVGIS/climatic-zones-pv/means-global.csv"


def download(http: HTTPClient, path: Path) -> RequestRecord:
    """Download the 212 MB global CSV; configure a sufficient explicit byte limit."""
    return http.download_file(URL, path)


def read_catalogue(path: Path) -> pd.DataFrame:
    """Read source means. G is annual in-plane kWh/m²; Tw is module °C.

    E and eff are PVGIS model outputs, not measured plant performance. Source
    optimal tilt, period and 0.1° resolution must remain attached to an analysis.
    """
    frame = pd.read_csv(path, comment="#")
    result = validate_catalogue(frame, ("G", "Tw", "E", "eff"))
    if (result.G < 0).any() or (result.Tw <= -273.15).any() or (result.E < 0).any():
        raise ValueError("Unphysical JRC climate/performance values")
    return result
