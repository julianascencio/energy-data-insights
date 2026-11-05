from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "atnorth_current_permits",
    ROOT / "scripts/build_data_center_atnorth_current_permit_batch.py",
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

ATNORTH = ROOT / "catalogues/data_centers/records/projects/2026-11-03-atnorth.jsonl"


def records() -> dict[str, dict[str, object]]:
    return {
        record["record_id"]: record
        for record in (json.loads(line) for line in ATNORTH.read_text().splitlines())
    }


def test_fin04_permit_identities_do_not_infer_capacity_or_contract_binding() -> None:
    fin04 = MODULE.enrich_fin04(records()[MODULE.FIN04])
    observations = json.loads(fin04["observations_json"])
    permits = {
        item["value"]
        for item in observations
        if item["field"] in {"building_permit", "building_permit_modification"}
        and item["source_id"] in MODULE.SOURCES
    }
    assert permits == {
        "286-2025-384",
        "286-2026-281",
        "286-2026-282 modifies 286-2025-165",
        "286-2026-277",
    }
    assert "it_capacity_mw" not in fin04
    assert "grid_capacity_mw" not in fin04
    assert (
        "relationship to the two generic YIT contract records remains unresolved" in fin04["notes"]
    )


def test_swe04_grid_and_heat_reuse_boundaries_remain_non_operational() -> None:
    swe04 = MODULE.enrich_swe04(records()[MODULE.SWE04])
    observations = json.loads(swe04["observations_json"])
    assert any(
        item["field"] == "backup_combustion_input"
        and item["value"] == 1200
        and "not electrical output" in item["boundary"]
        for item in observations
    )
    assert any(
        item["field"] == "grid_line_construction_period"
        and item["value"] == "November 2026 to March 2029"
        and "not SWE04 commissioning" in item["boundary"]
        for item in observations
    )
    assert swe04["status"] == "permitted"
    assert swe04.get("commissioning_date") is None
    assert swe04["heat_rejection"].endswith("no delivered heat evidenced")
