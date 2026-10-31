"""Distances, ambiguous coordinates, missing data and preserved source evidence."""

import json
from copy import deepcopy
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from energy_analysis.climate_comparison.site import load_site_example, site_climate_profile
from energy_methods.climate_zones import ClimateProvenance
from energy_methods.jrc_climate import fit_jrc_climate

DATA = Path(__file__).resolve().parents[2] / "examples/analysis"
META = {"source": "Synthetic test", "period": "test only", "resolution": "test points"}


def profile(frame, source="ml21", *, latitude=0, longitude=0, radius=50, model=None, metadata=None):
    return site_climate_profile(
        latitude,
        longitude,
        catalogues={source: frame},
        source_metadata={source: META if metadata is None else metadata},
        radius_km=radius,
        jrc_model=model,
    )["classifications"]


def test_real_site_retains_every_native_field_and_all_source_metadata():
    frames, manifest, model = load_site_example(DATA)
    before = deepcopy(manifest)
    result = site_climate_profile(
        -34.406, -70.858, catalogues=frames, source_metadata=manifest["sources"], jrc_model=model
    )
    expected = {"JRC": "JRC09", "KGPV": "DH", "ML21": "Mou1", "PVCZ": "T6:H3"}
    for scheme, source in (("JRC", "jrc"), ("KGPV", "ml21"), ("ML21", "ml21"), ("PVCZ", "pvcz")):
        item = result["classifications"][scheme]
        assert item["status"] == "matched"
        assert item["code"] == expected[scheme]
        assert item["source"] == manifest["sources"][source]
        assert set(item["candidates"][0]) == set(frames[source].columns)
        assert set(item["field_metadata"]) == set(frames[source].columns)
        assert item["label"] and item["use"] and item["limitation"]
    assert len(result["classifications"]["PVCZ"]["candidates"][0]) == 49
    assert manifest == before
    json.dumps(result, allow_nan=False)


def test_antimeridian_distance_and_no_more_distant_match():
    frame = pd.DataFrame(
        {
            "lat": [0, 0],
            "lon": [-179.9, 170],
            "kgpv_zone": ["AH", "BK"],
            "ml21_zone": ["Tro1", "Des1"],
            "extra_native": [123, 456],
        }
    )
    result = profile(frame, longitude=179.9, radius=30)
    assert result["KGPV"]["code"] == "AH"
    assert result["KGPV"]["distance_km"] == pytest.approx(22.239016, abs=1e-5)
    assert result["ML21"]["candidates"][0]["extra_native"] == 123
    rejected = profile(frame, longitude=179.9, radius=20)
    assert rejected["KGPV"]["status"] == "outside_radius"
    assert rejected["KGPV"]["code"] is None
    assert rejected["KGPV"]["candidates"] == []
    assert result["PVCZ"]["status"] == "source_not_supplied"


def test_rounded_pvcz_coordinate_conflict_is_not_silently_resolved():
    frame = pd.DataFrame({"lat": [0, 0], "lon": [0, 0], "pvcz_labeled": ["T1:H1", "T2:H2"]})
    item = profile(frame, source="pvcz")["PVCZ"]
    assert item["status"] == "ambiguous" and item["code"] is None
    assert len(item["candidates"]) == 2
    frame["pvcz_labeled"] = "T1:H1"
    item = profile(frame, source="pvcz")["PVCZ"]
    assert item["status"] == "matched" and len(item["candidates"]) == 2


def test_missing_nearest_jrc_features_do_not_select_farther_complete_point():
    model = fit_jrc_climate(
        [[100, 10], [120, 12], [1000, 30], [1100, 32]],
        provenance=ClimateProvenance("Synthetic", "test", "points"),
        n_clusters=2,
        n_init=2,
    )
    frame = pd.DataFrame({"lat": [0, 0], "lon": [0, 0.1], "G": [np.nan, 100], "Tw": [20, 10]})
    item = profile(frame, "jrc", model=model)["JRC"]
    assert item["status"] == "missing_inputs" and item["distance_km"] == 0
    assert item["code"] is None and item["candidates"][0]["G"] is None
    assert profile(frame, "jrc")["JRC"]["status"] == "model_not_supplied"
    json.dumps(item, allow_nan=False)


def test_bounded_sample_cannot_be_used_as_a_global_catalogue():
    frames, manifest, model = load_site_example(DATA)
    result = site_climate_profile(
        28.3, -16.4, catalogues=frames, source_metadata=manifest["sources"], jrc_model=model
    )
    assert all(
        item["status"] == "outside_sample_coverage" for item in result["classifications"].values()
    )
    with pytest.raises(ValueError, match="source, period"):
        site_climate_profile(0, 0, catalogues=frames, source_metadata={}, jrc_model=model)


@pytest.mark.parametrize(
    "latitude,longitude,radius",
    [(91, 0, 50), (0, 181, 50), (0, 0, -1), (0, 0, True), (0, 0, np.nan)],
)
def test_invalid_query_rejected_even_without_source_rows(latitude, longitude, radius):
    with pytest.raises(ValueError):
        site_climate_profile(
            latitude, longitude, catalogues={}, source_metadata={}, radius_km=radius
        )


def test_empty_table_does_not_invent_a_class():
    item = profile(pd.DataFrame(columns=["lat", "lon", "kgpv_zone", "ml21_zone"]))["KGPV"]
    assert item["status"] == "no_source_rows" and item["code"] is None
