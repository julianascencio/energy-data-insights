"""Synthetic independent identity and inventory boundary tests."""

import pytest

from energy_data_retrieval.wind_catalogue.canada import reconcile_group


def inputs():
    old = {
        "record_id": "test",
        "name": "Test Wind Farm",
        "country_code": "CAN",
        "latitude": 50,
        "longitude": -110,
        "historical_capacity_mw": 6,
    }
    rows = [
        {
            "Project Name": "Test",
            "Province_Territory": "Synthetic",
            "Turbine Identifier": str(i),
            "Total Project Capacity (MW)": 6,
            "Latitude": 50,
            "Longitude": -110,
            "Model": model,
            "Number of Turbines in Project": 2,
        }
        for i, model in enumerate(["Model A", "Model B"])
    ]
    return rows, [old]


def test_mixed_models_and_unknowns_preserved():
    rows, old = inputs()
    summary, decision = reconcile_group(rows, old)
    assert decision["decision"] == "enriched"
    assert summary is not None
    assert summary["inventory_turbine_rows"] == 2
    assert len(summary["fleet_groups"]) == 2
    assert summary["fleet_groups"][0]["Turbine Rated Capacity (kW)"] is None
    assert "unknown" in summary["fleet_completeness"]
    assert "status" not in summary


@pytest.mark.parametrize("change", ["duplicate", "far", "capacity", "missing", "ambiguous"])
def test_identity_and_inventory_holds(change):
    rows, old = inputs()
    if change == "duplicate":
        rows[1]["Turbine Identifier"] = rows[0]["Turbine Identifier"]
    if change == "far":
        rows[1]["Latitude"] = 51
    if change == "capacity":
        rows[0]["Total Project Capacity (MW)"] = 12
    if change == "missing":
        rows[0]["Latitude"] = None
    if change == "ambiguous":
        old.append(dict(old[0]))
    summary, decision = reconcile_group(rows, old)
    assert summary is None
    assert decision["decision"] == "deferred"


def test_mixed_project_groups_rejected():
    rows, old = inputs()
    rows[1]["Project Name"] = "Other"
    with pytest.raises(ValueError):
        reconcile_group(rows, old)
