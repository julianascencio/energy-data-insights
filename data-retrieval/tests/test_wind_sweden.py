"""Synthetic Swedish registry identities, state semantics and completeness checks."""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from energy_data_retrieval.wind_catalogue.sweden import features, stage_partition

NOW = "2026-11-03T10:45:00Z"


def inputs():
    return json.loads((Path(__file__).parent / "fixtures/wind/vbk_synthetic.json").read_text())


def stage(data, existing=None):
    return stage_partition(data["areas"], data["turbines"], existing or [], now=NOW)


def test_linked_inventory_is_not_an_operating_census():
    data = inputs()
    before = deepcopy(data)
    rows, ledger = stage(data)
    project, first, second = rows
    assert data == before
    assert ledger[0]["decision"] == "added"
    assert first["project_record_id"] == second["project_record_id"] == project["record_id"]
    assert project["status"] == first["status"] == "unknown"
    assert second["status"] == "decommissioned"
    assert project["aggregation_role"] == "unresolved"
    assert "installed_capacity_mw" not in project
    assert "turbine_count" not in project  # source current-row count is not installed count
    assert project["fleet_completeness"] == "partial"
    assert "turbine_model" not in second
    assert "rotor_diameter_m" not in first
    assert "rated_power_kw" not in first
    detail = json.loads(first["extensions_json"])
    assert detail["calculated_annual_generation_gwh"] == 0
    assert detail["erection_date"] is None
    assert detail["maximum_power_mw"] == 3
    assert "anchor" in project["location_accuracy"]


def test_repeated_area_names_are_held():
    data = inputs()
    duplicate = deepcopy(data["areas"][0])
    duplicate["properties"]["OMRID"] = "TEST-002"
    data["areas"].append(duplicate)
    rows, ledger = stage(data)
    assert not rows
    assert all(x["decision"] == "deferred" for x in ledger)


def test_repeated_turbine_id_fails_partition():
    data = inputs()
    data["turbines"].append(deepcopy(data["turbines"][0]))
    with pytest.raises(ValueError, match="Duplicate registry"):
        stage(data)


def test_orphan_is_held_without_losing_other_rows():
    data = inputs()
    orphan = deepcopy(data["turbines"][0])
    orphan["properties"].update(OMRID="ABSENT", VERKID="ABSENT-001")
    data["turbines"].append(orphan)
    rows, ledger = stage(data)
    assert len(rows) == 3
    assert ledger[0]["decision"] == "deferred"
    assert ledger[0]["parent_registry_id"] == "ABSENT"


@pytest.mark.parametrize("same_name", [True, False])
def test_existing_name_or_location_never_becomes_duplicate(same_name):
    data = inputs()
    old = {
        "record_id": "prior",
        "entity_type": "projects",
        "country_code": "SWE",
        "name": "Synthetic farm" if same_name else "Different historical name",
        "latitude": 60.01,
        "longitude": 17.01,
    }
    rows, ledger = stage(data, [old])
    assert not rows
    assert ledger[0]["candidate_record_ids"] == ["prior"]


def test_partial_query_rejected():
    with pytest.raises(ValueError, match="complete GeoJSON"):
        features({"type": "FeatureCollection", "features": [], "exceededTransferLimit": True})


def test_replay_stable_ids_and_requires_reconciliation():
    data = inputs()
    rows, _ = stage(data)
    repeated, _ = stage(inputs())
    assert rows == repeated
    staged, ledger = stage(data, rows)
    assert not staged
    assert ledger[0]["decision"] == "deferred"
