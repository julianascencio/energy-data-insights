"""Catalogue integrity, update safety and Arrow round trips, without live access."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from energy_data_retrieval.pv_catalogue import (
    SCHEMA,
    build_parquet,
    load_records,
    stable_id,
    upsert_records,
    validate_record,
    write_records,
)
from energy_data_retrieval.pv_catalogue.sam import INVERTER_MAP, parse_sam_csv, verify_sha256

NOW = "2026-10-31T10:00:00Z"
LATER = "2026-10-31T11:00:00Z"
ROOT = Path(__file__).resolve().parents[2] / "catalogues/pv"
SOURCES = {
    "oem": {
        "url": "https://example.org/datasheet",
        "publisher": "OEM",
        "title": "PV",
        "license": "facts only",
        "retrieved_at": NOW,
    }
}


def sample() -> dict:
    return {
        "record_id": stable_id("modules", "OEM", "X-400"),
        "entity_type": "modules",
        "name": "OEM X-400",
        "manufacturer": "OEM",
        "model": "X-400",
        "pmax_stc_w": 400.0,
        "sources": ["oem"],
        "field_sources_json": '{"*":"oem"}',
        "quality_status": "primary_source_extract",
        "created_at": NOW,
        "updated_at": NOW,
        "last_verified_at": NOW,
    }


def test_all_committed_records_validate():
    registry = json.loads((ROOT / "sources.json").read_text())
    rows = load_records(ROOT)
    assert {r["entity_type"] for r in rows} == set(SCHEMA["entity_types"])
    for row in rows:
        validate_record(row, registry)
    # Source records are independent of binary artefacts and APIs.
    assert sum(r["entity_type"] == "modules" for r in rows) > 21000
    assert len({r["country_code"] for r in rows if r["entity_type"] == "projects"}) >= 11


def test_identity_preserves_model_case_and_punctuation():
    assert stable_id("modules", "OEM", "X-B") != stable_id("modules", "OEM", "X-b")
    assert stable_id("modules", "OEM", "X-B") != stable_id("modules", "OEM", "XB")
    assert stable_id("modules", " OEM ", "X-B") == stable_id("modules", "OEM", "X-B")


@pytest.mark.parametrize(
    ("key", "bad"),
    [
        ("pmax_stc_w", -1.0),
        ("pmax_stc_w", float("nan")),
        ("pmax_stc_w", True),
        ("efficiency_stc_pct", 101.0),
        ("latitude", 91.0),
        ("longitude", -181.0),
        ("cell_count", 60.5),
        ("created_at", "2026-10-31T12:00:00"),
        ("sources", []),
        ("sources", ["unknown"]),
        ("field_sources_json", "{}"),
        ("field_sources_json", '{"*":"unknown"}'),
        ("extensions_json", '{"x":NaN}'),
        ("unregistered_voltage", 1500),
    ],
)
def test_invalid_metadata_rejected(key, bad):
    row = sample()
    row[key] = bad
    with pytest.raises(ValueError):
        validate_record(row, SOURCES)


def test_signed_model_coefficient_is_not_negative_watts():
    row = sample()
    row["sandia_c0_per_w"] = -0.00001
    validate_record(row, SOURCES)


def test_ranges_and_dates():
    row = sample()
    row.update(mppt_min_v=600.0, mppt_max_v=400.0)
    with pytest.raises(ValueError, match="range"):
        validate_record(row, SOURCES)
    row = sample()
    row["created_at"] = LATER
    with pytest.raises(ValueError, match="Creation"):
        validate_record(row, SOURCES)


def test_idempotent_upsert_preserves_content_time_and_creation():
    row = sample()
    updated, conflicts = upsert_records([row], [row], now=LATER)
    assert not conflicts
    assert updated[0]["created_at"] == NOW
    assert updated[0]["updated_at"] == NOW
    assert updated[0]["last_verified_at"] == LATER
    again, _ = upsert_records(updated, [row], now=LATER)
    assert again == updated


def test_fill_missing_with_field_evidence_and_do_not_erase():
    old = sample()
    incoming = {
        **old,
        "sources": ["other"],
        "field_sources_json": '{"*":"other"}',
        "weight_kg": 22.0,
        "pmax_stc_w": None,
    }
    updated, conflicts = upsert_records([old], [incoming], now=LATER)
    assert not conflicts
    assert updated[0]["pmax_stc_w"] == 400.0
    assert updated[0]["weight_kg"] == 22.0
    assert json.loads(updated[0]["field_sources_json"])["weight_kg"] == "other"
    assert updated[0]["updated_at"] == LATER


def test_conflict_preserves_entire_existing_record():
    row = sample()
    updated, conflicts = upsert_records([row], [{**row, "pmax_stc_w": 500.0}], now=LATER)
    assert updated == [row]
    assert conflicts[0]["fields"]["pmax_stc_w"] == {"existing": 400.0, "incoming": 500.0}
    with pytest.raises(ValueError, match="older"):
        upsert_records([{**row, "last_verified_at": LATER}], [row], now=NOW)


def test_typed_parquet_roundtrip_and_no_overwrite(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    (root / "sources.json").write_text(json.dumps(SOURCES))
    write_records(root, [sample()])
    assert load_records(root) == [sample()]
    before = next((root / "records").glob("*/*.jsonl")).read_bytes()
    write_records(root, [sample()])
    assert next((root / "records").glob("*/*.jsonl")).read_bytes() == before
    output = tmp_path / "v1"
    report = build_parquet(root, output)
    table = pq.read_table(output / "modules.parquet")
    assert table["pmax_stc_w"][0].as_py() == 400
    assert table["weight_kg"][0].as_py() is None
    assert pa.types.is_timestamp(table.schema.field("created_at").type)
    assert pa.types.is_list(table.schema.field("sources").type)
    assert table["source_urls"][0].as_py() == [SOURCES["oem"]["url"]]
    assert table.schema == pq.read_schema(output / "projects.parquet")
    assert report["tables"]["projects"]["rows"] == 0
    with pytest.raises(FileExistsError):
        build_parquet(root, output)
    second = build_parquet(root, tmp_path / "v2")
    assert report == second
    invalid = {**sample(), "weight_kg": -1}
    with pytest.raises(ValueError):
        write_records(root, [invalid])
    assert load_records(root) == [sample()]


def test_duplicate_ids_fail_before_write(tmp_path):
    (tmp_path / "sources.json").write_text(json.dumps(SOURCES))
    with pytest.raises(ValueError, match="Duplicate"):
        write_records(tmp_path, [sample(), sample()])
    assert not (tmp_path / "records").exists()


def test_projects_do_not_promote_unknown_solar_to_pv():
    row = sample()
    row.update(entity_type="projects", country_code="CHL", technology="solar_unspecified")
    with pytest.raises(ValueError, match="confirmed photovoltaic"):
        validate_record(row, SOURCES)
    row["technology"] = "photovoltaic"
    row["latitude"] = -33.0
    with pytest.raises(ValueError, match="Both coordinates"):
        validate_record(row, SOURCES)


def test_sam_headers_duplicates_and_missing_values():
    columns = ["Name", *INVERTER_MAP, "CEC_hybrid"]
    values = ["OEM: test {240V}"] + ["NaN"] * len(INVERTER_MAP) + ["N"]
    # Minimal real-format CSV: names, units, model-variable names, data.
    content = "\n".join([",".join(columns), "Units", "[0]", ",".join(values)])
    rows, rejected = parse_sam_csv(
        content, entity_type="inverters", source_id="oem", retrieved_at=NOW
    )
    assert not rejected and len(rows) == 1
    assert "pac_rated_w" not in rows[0] and rows[0]["hybrid"] is False
    duplicates = content + "\n" + ",".join(values)
    rows, rejected = parse_sam_csv(
        duplicates, entity_type="inverters", source_id="oem", retrieved_at=NOW
    )
    assert not rows and len(rejected) == 2
    with pytest.raises(ValueError, match="header"):
        parse_sam_csv("Name,watts\na,3", entity_type="inverters", source_id="oem", retrieved_at=NOW)
    with pytest.raises(ValueError, match="checksum"):
        verify_sha256(b"changed", "0" * 64)


def test_no_source_or_input_mutation():
    row = sample()
    before = copy.deepcopy(row)
    upsert_records([row], [{**row, "weight_kg": 20.0}], now=LATER)
    assert row == before


def test_eia_aggregation_filters_units_preserves_missing_and_phase_fields():
    import pandas as pd

    from energy_data_retrieval.pv_catalogue.eia860 import parse_eia860_frames

    plants = pd.DataFrame(
        [
            {
                "Plant Code": 1,
                "Plant Name": "Mixed plant",
                "State": "CA",
                "County": "Example",
                "Latitude": 34.0,
                "Longitude": -119.0,
            }
        ]
    )
    base = {
        "Plant Code": 1,
        "Status": "OP",
        "Prime Mover": "PV",
        "Technology": "Solar Photovoltaic",
        "Nameplate Capacity (MW)": 5.0,
        "DC Net Capacity (MW)": 6.0,
        "Operating Year": 2020,
    }
    solar = pd.DataFrame(
        [
            {**base, "Generator ID": "1"},
            {**base, "Generator ID": "2", "DC Net Capacity (MW)": None},
            {**base, "Generator ID": "3", "Status": "RE"},
            {**base, "Generator ID": "4", "Prime Mover": "ST"},
        ]
    )
    rows = parse_eia860_frames(plants, solar, source_id="oem", retrieved_at=NOW, year=2025)
    assert len(rows) == 1
    assert rows[0]["capacity_ac_mw"] == 10
    assert "capacity_dc_mw" not in rows[0]  # Never sum a partial DC total.
    assert "commissioning_year" not in rows[0]  # Unit date is not whole-project COD.
    assert len(json.loads(rows[0]["phases_json"])) == 2
    validate_record(rows[0], SOURCES)
    with pytest.raises(ValueError, match="Duplicate EIA generator"):
        parse_eia860_frames(
            plants, pd.concat([solar, solar]), source_id="oem", retrieved_at=NOW, year=2025
        )
    with pytest.raises(ValueError, match="columns changed"):
        parse_eia860_frames(
            plants.drop(columns="County"), solar, source_id="oem", retrieved_at=NOW, year=2025
        )


def test_catalogue_rejects_dangling_links_and_semantic_duplicates():
    from energy_data_retrieval.pv_catalogue import validate_catalogue

    row = sample()
    with pytest.raises(ValueError, match="equipment reference"):
        validate_catalogue([{**row, "module_record_ids": ["unknown"]}], SOURCES)
    second = {**row, "record_id": stable_id("modules", "second-id")}
    with pytest.raises(ValueError, match="equipment identity"):
        validate_catalogue([row, second], SOURCES)
    row["field_sources_json"] = '{"*":["oem"]}'
    validate_record(row, SOURCES)
