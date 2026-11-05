"""Synthetic EPD fixtures: no downloaded document is required by CI."""

import copy
import hashlib
import json

import pytest

from energy_data_retrieval.wind_catalogue.epd import enrich_from_epd
from energy_data_retrieval.wind_catalogue.gppd import evidence_record

NOW = "2026-11-04T23:00:00Z"
RAW = b"synthetic EPD fixture"


def fixture():
    row = evidence_record(
        {
            "record_id": "fixture",
            "entity_type": "equipment",
            "manufacturer": "Example",
            "model": "T1",
            "swept_area_m2": 100.0,
        },
        source_id="prior",
        now="2026-11-01T00:00:00Z",
        locator="synthetic table",
    )
    review = {
        "sha256": hashlib.sha256(RAW).hexdigest(),
        "source_id": "epd",
        "manufacturer": "Example",
        "expected_models": ["T1"],
        "declaration": "synthetic 1",
        "published_at": "2025-01-01",
        "models": [
            {
                "model": "T1",
                "locator": "p3",
                "technical": {"generator_voltage_v": 690},
                "scalar_observations": {
                    "swept_area_m2": {"value": 90.0, "unit": "m2", "locator": "p3"}
                },
                "scenarios": [
                    {
                        "kind": "modeled",
                        "boundary": "one turbine; net electricity delivered to grid",
                        "unit": "MWh",
                        "value": 1000,
                        "reference_service_life_years": 20,
                        "mean_wind_speed_m_s": 8,
                        "location": "Hypothetical site",
                        "locator": "p4",
                        "reference_period": "20-year modeled lifetime",
                    }
                ],
            }
        ],
    }
    return row, review


def test_conflict_preserves_history_and_creation_and_is_idempotent():
    row, review = fixture()
    before = copy.deepcopy(row)
    result = enrich_from_epd(review, RAW, [row], now=NOW)[0]
    assert row == before
    assert result["record_id"] == row["record_id"]
    assert result["created_at"] == row["created_at"]
    assert result["swept_area_m2"] is None
    assert [x["value"] for x in json.loads(result["conflicts_json"])["swept_area_m2"]] == [100, 90]
    assert "observations_json" not in result
    assert "design_life_years" not in result  # LCA lifetime is not turbine design life
    assert enrich_from_epd(review, RAW, [result], now="2026-11-05T00:00:00Z") == [result]
    review["models"][0]["technical"]["generator_voltage_v"] = 900
    with pytest.raises(ValueError, match="Immutable"):
        enrich_from_epd(review, RAW, [result], now=NOW)


@pytest.mark.parametrize(
    "change",
    [
        "checksum",
        "missing",
        "duplicate",
        "identity",
        "measured",
        "boundary",
        "period",
        "nan",
        "unit",
        "promotion",
    ],
)
def test_rejects_unsafe_mappings(change):
    row, review = fixture()
    item = review["models"][0]
    if change == "checksum":
        review["sha256"] = "0" * 64
    if change == "missing":
        review["expected_models"].append("T2")
    if change == "duplicate":
        review["models"].append(copy.deepcopy(item))
    if change == "identity":
        row["manufacturer"] = "Unrelated"
    if change == "measured":
        item["scenarios"][0]["kind"] = "measured"
    if change == "boundary":
        item["scenarios"][0]["boundary"] = "whole farm; gross"
    if change == "period":
        del item["scenarios"][0]["reference_period"]
    if change == "nan":
        item["scenarios"][0]["value"] = float("nan")
    if change == "unit":
        item["scalar_observations"]["swept_area_m2"]["unit"] = "km2"
    if change == "promotion":
        item["scalar_observations"]["installed_capacity_mw"] = {"value": 50}
    with pytest.raises(ValueError):
        enrich_from_epd(review, RAW, [row], now=NOW)


def test_equal_geometry_adds_provenance_without_conflict():
    row, review = fixture()
    review["models"][0]["scalar_observations"]["swept_area_m2"]["value"] = 100.0
    result = enrich_from_epd(review, RAW, [row], now=NOW)[0]
    assert result["swept_area_m2"] == 100
    assert "conflicts_json" not in result
    assert json.loads(result["field_sources_json"])["swept_area_m2"] == ["epd", "prior"]
