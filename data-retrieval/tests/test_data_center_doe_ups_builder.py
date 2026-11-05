"""Reviewed DOE CCMS UPS builder and exact-deduplication boundaries."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "build_data_center_doe_ups_batch",
    ROOT / "scripts/build_data_center_doe_ups_batch.py",
)
assert SPEC and SPEC.loader
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def test_doe_ups_builder_exhausts_displayed_rows_without_synthesis() -> None:
    rows = BUILDER.rows()
    assert len(rows) == 50
    assert sum(row["brand"] == "ABB" for row in rows) == 4
    assert sum(row["brand"] == "APC" for row in rows) == 46
    assert sum(row["lowest_mode"] == "VFI" for row in rows) == 4
    assert sum(row["lowest_mode"] == "VI" for row in rows) == 24
    assert sum(row["lowest_mode"] == "VFD" for row in rows) == 22
    assert len({(row["brand"], row["individual_model"]) for row in rows}) == 50


def test_doe_ups_builder_keeps_watts_va_and_efficiency_boundaries() -> None:
    row = next(row for row in BUILDER.rows() if row["individual_model"] == "BR1500GQ")
    record = BUILDER.build_record(row)
    assert record["output_power_kw"] == 0.865
    assert record["apparent_power_kva"] == 1.5
    assert record["efficiency_pct"] == 98.9
    assert "VI lowest supported mode" in str(record["power_conditions"])
    assert "not evidence of deployment" in str(record["notes"])


def test_doe_ups_builder_adds_39_and_enriches_11_exact_models(
    tmp_path: Path,
) -> None:
    equipment_dir = ROOT / "catalogues/data_centers/records/equipment"
    new_records, enriched_ids = BUILDER.build(equipment_dir, tmp_path)
    assert len(new_records) == 39
    assert len(enriched_ids) == 11
    assert len({record["record_id"] for record in new_records}) == 39
    assert sum(record["manufacturer"] == "ABB" for record in new_records) == 4
    assert sum(record["manufacturer"] == "Schneider Electric" for record in new_records) == 35

    new_file = read_jsonl(tmp_path / BUILDER.NEW_FILENAME)
    assert len(new_file) == 39
    assert all(BUILDER.SOURCE_ID in record["sources"] for record in new_file)

    enriched_model, (enriched_id, filename) = next(iter(BUILDER.EXISTING.items()))
    enriched = next(
        record for record in read_jsonl(tmp_path / filename) if record["record_id"] == enriched_id
    )
    assert enriched["record_id"] == enriched_id
    assert BUILDER.SOURCE_ID in enriched["sources"]
    assert "doe_ccms_public_listing" in json.loads(str(enriched["certifications_json"]))
    assert any(
        observation["field"] == "individual_model"
        and observation["value"] == enriched_model
        and observation["source_id"] == BUILDER.SOURCE_ID
        for observation in json.loads(str(enriched["observations_json"]))
    )
