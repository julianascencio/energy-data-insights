"""The regional example uses attributed finer inputs, not global-map upsampling."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from energy_methods.country_boundaries import load_country_boundaries
from energy_methods.country_mapping import country_grid
from energy_methods.references import get_references
from energy_methods.weather_risk_mapping import map_weather_risks

ROOT = Path(__file__).resolve().parents[1]


def test_country_fixture_boundary_source_and_independent_missingness():
    examples = ROOT / "examples"
    manifest = json.loads((examples / "country_risk_provenance.json").read_text())
    for name, key in (
        ("inputs.csv", "fixture_sha256"),
        ("boundaries.geojson", "boundary_fixture_sha256"),
    ):
        assert (
            hashlib.sha256((examples / f"country_risk_{name}").read_bytes()).hexdigest()
            == manifest[key]
        )
    get_references(manifest["reference_ids"])
    assert manifest["boundary_provenance"]["version"] == "5.1.1"
    assert manifest["countries"] == ["AUT", "SVN"]
    selection = load_country_boundaries(
        examples / "country_risk_boundaries.geojson", ["AUT", "SVN"]
    )
    grid = country_grid(selection, resolution=0.5)
    table = (
        pd.read_csv(examples / "country_risk_inputs.csv")
        .set_index(["year", "lat", "lon"])
        .to_xarray()
    )
    np.testing.assert_array_equal(table.in_country.isel(year=0), grid.country_mask)
    assert int(grid.country_mask.sum()) == manifest["selected_cells"] == 83
    assert len(manifest["requests"]) == 83
    assert len({record["aod_request"]["sha256"] for record in manifest["requests"]}) == 28
    assert (table.valid_aod_days.where(table.in_country == 1, 365) == 365).all()
    table.aod550_mean.attrs = {"units": "1", "wavelength_nm": 550}
    table.snow_depth_sum.attrs = {"units": "cm h", "snow_depth_kind": "physical_ground"}
    result = map_weather_risks(table)
    assert int((result.soiling_risk > 0).sum()) == 83
    assert int((result.snow_risk > 0).sum()) == 82
    assert (result.snow_risk.where(table.in_country.isel(year=0) == 0, 0) == 0).all()


def test_country_plan_and_site_limit_precede_weather_requests(monkeypatch, tmp_path, capsys):
    import importlib.util
    import sys

    import pytest

    spec = importlib.util.spec_from_file_location(
        "prepare_country_risk", ROOT / "scripts/prepare_weather_risk_example.py"
    )
    assert spec is not None and spec.loader is not None
    prepare = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prepare)

    def forbidden(*args, **kwargs):
        raise AssertionError("Plan/limit must be resolved before HTTP weather acquisition")

    monkeypatch.setattr(prepare, "HTTPClient", forbidden)
    argv = [
        "prepare",
        "--countries",
        "AUT",
        "SVN",
        "--boundaries",
        str(ROOT / "examples/country_risk_boundaries.geojson"),
        "--resolution",
        "0.5",
        "--output",
        str(tmp_path),
        "--maximum-sites",
        "1",
    ]
    monkeypatch.setattr(sys, "argv", [*argv, "--plan-only"])
    prepare.main()
    assert "83 snow sites" in capsys.readouterr().out
    assert list(tmp_path.iterdir()) == []
    monkeypatch.setattr(sys, "argv", argv)
    with pytest.raises(ValueError, match="maximum-sites"):
        prepare.main()
