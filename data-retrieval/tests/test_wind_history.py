"""Synthetic history-table fixtures test completeness and non-inference."""

import copy
import hashlib

import pytest

from energy_data_retrieval.wind_catalogue.history import stage_history


def fixture():
    original = b"synthetic OEM table, not real product data"
    slot = dict(
        row=1,
        locator="synthetic p1 row1",
        manufacturer="Synthetic OEM",
        model="TYPE",
        identity_suffix="published type",
        rotor_diameter_m=10,
        rating_text="20-30 kW",
        rated_power_kw=None,
    )
    return dict(
        source_id="synthetic",
        sha256=hashlib.sha256(original).hexdigest(),
        expected_rows=[1],
        rows=[slot],
    ), original


def stage(doc, original, existing=None):
    return stage_history(doc, original, existing or [], now="2026-11-05T00:00:00Z")


def test_range_not_expanded_or_converted_to_nominal():
    doc, original = fixture()
    rows, _ = stage(doc, original)
    assert len(rows) == 1
    assert rows[0].get("rated_power_kw") is None
    assert "20-30 kW" in rows[0]["extensions_json"]
    assert stage(doc, original)[0] == rows


def test_duplicate_option_observations_do_not_create_new_type():
    doc, original = fixture()
    second = copy.deepcopy(doc["rows"][0])
    second.update(row=2, locator="synthetic p1 row2", tower_option_m=80)
    doc["rows"].append(second)
    doc["expected_rows"].append(2)
    assert len(stage(doc, original)[0]) == 1


def test_existing_model_never_overwritten():
    doc, original = fixture()
    rows, ledger = stage(
        doc, original, [dict(entity_type="equipment", manufacturer="Synthetic OEM", model="TYPE")]
    )
    assert rows == []
    assert ledger[0]["decision"] == "existing_model_revision_review"


def test_conflict_held_before_normalization():
    doc, original = fixture()
    doc["rows"][0]["hold_reason"] = "Printed unit conflicts with header"
    assert stage(doc, original)[0] == []


def test_missing_rows_and_changed_original_rejected():
    doc, original = fixture()
    with pytest.raises(ValueError, match="checksum"):
        stage(doc, original + b"changed")
    doc["expected_rows"].append(2)
    with pytest.raises(ValueError, match="rows"):
        stage(doc, original)


def test_same_identity_conflicting_rating_rejected():
    doc, original = fixture()
    second = copy.deepcopy(doc["rows"][0])
    second.update(row=2, rated_power_kw=30)
    doc["rows"].append(second)
    doc["expected_rows"].append(2)
    with pytest.raises(ValueError, match="Conflicting"):
        stage(doc, original)
