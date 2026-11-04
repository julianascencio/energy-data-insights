"""Synthetic reviewed columns; no live download or copied OEM fixture required."""

import hashlib
import json
from copy import deepcopy

import pytest

from energy_data_retrieval.wind_catalogue.portfolio import stage_portfolio

ORIGINAL = b"Synthetic two-column OEM source; not a real product specification"


@pytest.fixture
def review():
    values = {
        "rated_power_kw": 4200,
        "rated_power_conditions": "Synthetic nominal rating; density unknown",
        "rotor_diameter_m": 183.5,
        "swept_area_m2": 26446,
        "hub_height_options_json": '{"heights_m":[95,110,140]}',
        "extensions_json": '{"generator_v":1380,"output_v":1140,"frequency_hz":[50,60]}',
    }
    return {
        "source_id": "synthetic",
        "manufacturer": "Synthetic OEM",
        "revision": "R1",
        "sha256": hashlib.sha256(ORIGINAL).hexdigest(),
        "expected_models": ["S182-4.2", "S165-5.6"],
        "columns": [
            {
                "model": name,
                "locator": f"p1 column {i + 1}",
                "values": deepcopy(values),
                "original_units": {
                    k: "m²" if k == "swept_area_m2" else "source units" for k in values
                },
            }
            for i, name in enumerate(["S182-4.2", "S165-5.6"])
        ],
    }


def stage(review, original=ORIGINAL, existing=None):
    return stage_portfolio(review, original, existing or [], now="2026-11-04T22:01:00Z")


def test_table_geometry_options_and_electrical_boundaries_are_not_decoded(review):
    rows, _ = stage(review)
    assert len(rows) == 2  # Three hub options do not make six configurations.
    for row in rows:
        assert row["rotor_diameter_m"] == 183.5  # Neither 182 nor 165 from model code.
        assert row.get("hub_height_m") is None
        assert row.get("voltage_v") is None
        assert row.get("frequency_hz") is None
        assert row.get("air_density_kg_m3") is None
        assert row.get("compatibility_json") is None
        evidence = json.loads(row["evidence_json"])["swept_area_m2"]
        assert evidence["original_unit"] == "m²"
        assert evidence["unit"] == "m2"


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "extra", "duplicate_expected"])
def test_full_column_partition_required(review, mutation):
    if mutation == "missing":
        review["columns"].pop()
    elif mutation == "duplicate":
        review["columns"][1] = deepcopy(review["columns"][0])
    elif mutation == "extra":
        review["columns"].append({**review["columns"][0], "model": "not a reviewed column"})
    else:
        review["expected_models"].append(review["expected_models"][0])
    with pytest.raises(ValueError, match="columns"):
        stage(review)


def test_checksum_mismatch_rejected(review):
    with pytest.raises(ValueError, match="checksum"):
        stage(review, b"another revision")


def test_power_without_conditions_and_fields_without_units_rejected(review):
    column = review["columns"][0]
    column["values"]["rated_power_conditions"] = ""
    with pytest.raises(ValueError, match="conditions"):
        stage(review)
    column["values"]["rated_power_conditions"] = "nominal"
    column["original_units"].pop("rotor_diameter_m")
    with pytest.raises(ValueError, match="units"):
        stage(review)


def test_revision_and_rating_do_not_change_model_identity(review):
    first, _ = stage(review)
    review["revision"] = "R2"
    review["columns"][0]["values"]["rated_power_kw"] = 4300
    second, _ = stage(review)
    assert {r["record_id"] for r in first} == {r["record_id"] for r in second}
    rows, ledger = stage(review, existing=first)
    assert rows == []
    assert {d["decision"] for d in ledger} == {"existing_identity_review"}


def test_input_order_has_no_effect(review):
    first, _ = stage(review)
    review["columns"].reverse()
    second, _ = stage(review)
    assert first == second
