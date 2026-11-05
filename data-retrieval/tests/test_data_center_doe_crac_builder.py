"""Reviewed DOE CCMS computer-room air-conditioner builder boundaries."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "build_data_center_doe_crac_batch",
    ROOT / "scripts/build_data_center_doe_crac_batch.py",
)
assert SPEC and SPEC.loader
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


def test_doe_crac_builder_exhausts_displayed_page_without_synthesis() -> None:
    rows = BUILDER.rows()
    assert len(rows) == 50
    assert sum(row["brand"] == "AboveAir" for row in rows) == 36
    assert sum(row["brand"] == "AIRSYS" for row in rows) == 14
    assert len({(row["brand"], row["basic_model"]) for row in rows}) == 50


def test_doe_crac_builder_quarantines_aboveair_capacity_conflict() -> None:
    row = next(row for row in BUILDER.rows() if row["basic_model"] == "HKA-053(kW)*")
    record = BUILDER.build_record(row)
    assert record["cooling_capacity_kw"] is None
    assert record["quality_status"] == "needs_review"
    conflicts = json.loads(record["conflicts_json"])
    assert len(conflicts["cooling_capacity_kw"]) == 2
    assert record["airflow_m3_h"] == 9344.56


def test_doe_crac_builder_converts_only_nonconflicting_air_sys_capacity() -> None:
    row = next(row for row in BUILDER.rows() if row["basic_model"] == "UNI-EDG.20V1*1MR410CAC")
    record = BUILDER.build_record(row)
    assert record["cooling_capacity_kw"] == 19.9
    assert record["airflow_m3_h"] == 4281.507
    assert "conflicts_json" not in record
    observations = json.loads(record["observations_json"])
    assert any(
        item["field"] == "net_total_cooling_capacity"
        and item["value"] == 67900
        and item["unit"] == "Btu/h"
        for item in observations
    )
