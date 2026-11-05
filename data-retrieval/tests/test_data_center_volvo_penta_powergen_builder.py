"""Reviewed Volvo Penta builder boundaries."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "build_data_center_volvo_penta_powergen_batch",
    ROOT / "scripts/build_data_center_volvo_penta_powergen_batch.py",
)
assert SPEC and SPEC.loader
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


def test_stage_iiia_inventory_keeps_frequency_specific_rows_sparse() -> None:
    rows = {source.slug: BUILDER.RATINGS[source.slug] for source in BUILDER.STAGE_IIIA_SOURCES}
    assert sum(len(items) for items in rows.values()) == 22
    assert {row.frequency for row in rows["d8-eu-stage-iiia-epa-tier-3"]} == {50, 60}
    assert {
        row.frequency
        for row in rows["d13-eu-stage-iiia-epa-tier-3"]
        if row.model in {"TAD1350GE", "TAD1353GE"}
    } == {60}
    assert {
        row.frequency
        for row in rows["d16-eu-stage-iiia-epa-tier-3"]
        if row.model in {"TWD1652GE", "TWD1653GE"}
    } == {50}


def test_stage_iiia_builder_preserves_power_boundaries() -> None:
    source = BUILDER.STAGE_IIIA_SOURCES[1]
    candidates = BUILDER.parse_volvo_penta_powergen_matrix(
        BUILDER.extracted_csv(source),
        source_url=BUILDER.url(source),
        expected_count=source.expected,
    )["candidates"]
    candidate = next(
        row for row in candidates if row["model"] == "TAD1353GE" and row["frequency_hz"] == 60
    )
    record = BUILDER.build_record(
        candidate,
        source,
        retrieved_at=BUILDER.STAGE_IIIA_RETRIEVED_AT,
    )
    assert record["output_power_kw"] == 364
    assert record["apparent_power_kva"] == 455
    assert record["frequency_hz"] == 60
    assert "standby electrical kW/kVA" in record["notes"]
