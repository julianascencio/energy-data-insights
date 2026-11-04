from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from energy_data_retrieval.data_center_catalogue import stable_id

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "atnorth_reconciliation",
    ROOT / "scripts/build_data_center_atnorth_reconciliation_batch.py",
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

DEN01 = MODULE.DEN01
DEN02 = MODULE.DEN02
FIN03 = MODULE.FIN03
SWE04 = MODULE.SWE04
enrich_den01 = MODULE.enrich_den01
enrich_den02 = MODULE.enrich_den02
enrich_swe04 = MODULE.enrich_swe04
new_fin03 = MODULE.new_fin03


ATNORTH = ROOT / "catalogues/data_centers/records/projects/2026-11-03-atnorth.jsonl"


def records() -> dict[str, dict[str, object]]:
    return {
        record["record_id"]: record
        for record in (json.loads(line) for line in ATNORTH.read_text().splitlines())
    }


def test_fin03_stable_identity_and_unallocated_combined_capacity() -> None:
    record = new_fin03()
    assert record["record_id"] == FIN03 == stable_id("projects", "atNorth", "FIN03")
    assert record["facility_id"] == stable_id("facility", "atNorth", "FIN03")
    assert record["locality"] == "Espoo"
    assert record["status"] == "operational"
    assert "it_capacity_mw" not in record
    assert "grid_capacity_mw" not in record
    assert "facility_capacity_mw" not in record
    observations = json.loads(record["observations_json"])
    combined = [item for item in observations if item["field"] == "combined_portfolio_capacity"]
    assert combined == [
        {
            "as_of": "2023-01-04",
            "boundary": "FIN01 and FIN03 combined; not allocated to FIN03",
            "field": "combined_portfolio_capacity",
            "kind": "reported",
            "locator": "operator-confirmed update",
            "source_id": "dcd-atnorth-finland-acquisition-20230104",
            "unit": "MW",
            "value": 3.2,
        }
    ]


def test_denmark_milestones_preserve_event_boundaries() -> None:
    current = records()
    den01 = enrich_den01(current[DEN01])
    assert "conflicts_json" not in den01
    milestones = {
        (item["field"], item["value"], item["boundary"])
        for item in json.loads(den01["observations_json"])
        if item["field"] in {"first_phase_live", "campus_operational"}
    }
    assert milestones == {
        ("first_phase_live", "Q4 2025", "DEN01 first phase; quarter precision"),
        (
            "campus_operational",
            "Q1 2026",
            "DEN01 campus operational milestone; phase boundary not specified",
        ),
    }

    den02 = enrich_den02(current[DEN02])
    assert den02["status"] == "permitted"
    assert den02["contractor_names"] == ["TSL"]
    assert "facility_capacity_mw" not in den02
    assert "it_capacity_mw" not in den02
    observations = json.loads(den02["observations_json"])
    assert any(
        item["field"] == "first_phase_power" and item["value"] == 60 for item in observations
    )
    assert any(item["field"] == "campus_power" and item["value"] == 500 for item in observations)


def test_swe04_grid_and_site_boundaries_remain_distinct() -> None:
    swe04 = enrich_swe04(records()[SWE04])
    assert swe04["aggregation_role"] == "aggregate"
    assert swe04["grid_capacity_mw"] == 200
    assert swe04["grid_capacity_basis"] == "ultimate_planned"
    assert "300 MW is unclassified planned project power" in swe04["capacity_scope"]
    assert "500 MW belongs to the wider Hamre industrial park" in swe04["capacity_scope"]
    assert "commissioning_date" in json.loads(swe04["conflicts_json"])
    assert swe04.get("commissioning_date") is None
    observations = json.loads(swe04["observations_json"])
    assert any(item["field"] == "project_power" and item["value"] == 300 for item in observations)
    assert any(
        item["field"] == "industrial_park_power_capacity" and item["value"] == 500
        for item in observations
    )
