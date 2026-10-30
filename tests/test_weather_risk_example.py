"""Integrity of the attributed offline worldwide risk example."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from energy_methods.references import get_references
from energy_methods.weather_risk_mapping import map_weather_risks

ROOT = Path(__file__).resolve().parents[1]


def test_real_fixture_coverage_provenance_and_ocean_mask():
    path = ROOT / "examples/weather_risk_inputs.csv"
    manifest = json.loads((ROOT / "examples/weather_risk_provenance.json").read_text())
    assert hashlib.sha256(path.read_bytes()).hexdigest() == manifest["fixture_sha256"]
    assert manifest["region"] == "world" and manifest["year"] == 2023
    assert len(manifest["requests"]) == manifest["land_cells"] == 102
    get_references(manifest["reference_ids"])  # Unknown citations must fail.
    for record in manifest["requests"]:
        assert record["aod_request"]["parameters"]["parameters"] == "AOD_55"
        assert record["snow_request"]["parameters"]["models"] == "era5_land"
        for source in ("aod_request", "snow_request"):
            assert len(record[source]["sha256"]) == 64
            assert record[source]["retrieved_at_utc"]

    table = pd.read_csv(path).set_index(["year", "lat", "lon"]).to_xarray()
    np.testing.assert_array_equal(table.lat, np.arange(-82.5, 90, 15))
    np.testing.assert_array_equal(table.lon, np.arange(-172.5, 180, 15))
    land = table.is_land == 1
    for count, expected in (("valid_aod_days", 365), ("valid_snow_hours", 8760)):
        assert (table[count].where(land, expected) == expected).all()
    for name in ("aod550_mean", "snow_depth_sum"):
        assert table[name].where(~land).isnull().all()
    table.aod550_mean.attrs = {"units": "1", "wavelength_nm": 550}
    table.snow_depth_sum.attrs = {"units": "cm h", "snow_depth_kind": "physical_ground"}
    result = map_weather_risks(table)
    for name in ("soiling_risk", "snow_risk"):
        assert int((result[name] > 0).sum()) == 102
        assert (result[name].where(~land.isel(year=0), 0) == 0).all()
        assert set(np.unique(result[name])) == set(range(6))
