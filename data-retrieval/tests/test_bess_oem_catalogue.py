"""Evidence, configuration boundaries and deterministic OEM export contracts."""

import copy
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from energy_data_retrieval.bess_oem_catalogue import (
    SCHEMA,
    build_parquet,
    load_records,
    stable_id,
    validate_catalogue,
)
from energy_data_retrieval.bess_oem_catalogue.catalogue import validate_record

ROOT = Path(__file__).resolve().parents[2] / "catalogues/bess_oem"


@pytest.fixture
def catalogue():
    return load_records(ROOT), json.loads((ROOT / "sources.json").read_text())


def test_committed_products_keep_variants_claims_and_boundaries(catalogue):
    rows, sources = catalogue
    validate_catalogue(rows, sources)
    assert len({r["manufacturer"] for r in rows}) >= 25
    nidec = [r for r in rows if r["manufacturer"] == "Nidec Conversion"]
    assert all(r.get("power_capacity_mw") is None for r in nidec)
    assert all(r["apparent_power_mva"] > 0 for r in nidec)
    hithium = next(r for r in rows if r.get("cell_capacity_ah") == 1175)
    assert json.loads(hithium["compliance_claims_json"])["status"] == "in_progress"
    assert hithium["efficiency_qualifier"] == "minimum"
    ngk = next(r for r in rows if r["manufacturer"] == "NGK Insulators")
    assert json.loads(ngk["extensions_json"])["lifecycle"]["new_production_discontinued"]
    assert ngk["product_status"] == "historical_document"
    assert ngk.get("operating_temperature_min_c") is None  # Internal ≠ ambient.
    assert stable_id("OEM", "Model B", "EU") != stable_id("OEM", "Model b", "EU")


@pytest.mark.parametrize(
    "field,value,error",
    [
        ("energy_capacity_mwh", -1, "Out of range"),
        ("energy_capacity_mwh", float("nan"), "Non-finite"),
        ("power_capacity_mw", True, "Wrong type"),
        ("entity_type", "projects", "Invalid entity_type"),
        ("created_at", "2026-01-01T00:00:00", "timezone-aware UTC"),
        ("energy_basis", None, "requires explicit"),
        ("round_trip_efficiency_pct", 101, "Out of range"),
        ("warranty_years", 20, "requires explicit"),
        ("cycle_life", 10000, "requires explicit"),
        ("unknown_rating", 1, "unregistered columns"),
    ],
)
def test_invalid_metadata_rejected(catalogue, field, value, error):
    rows, sources = catalogue
    row = copy.deepcopy(next(r for r in rows if r.get("energy_capacity_mwh") is not None))
    row[field] = value
    with pytest.raises(ValueError, match=error):
        validate_record(row, sources)


def test_evidence_and_family_ranges_cannot_be_published_as_fixed_skus(catalogue):
    rows, sources = catalogue
    row = copy.deepcopy(next(r for r in rows if r["record_scope"] == "family"))
    row.update(energy_capacity_mwh=5, energy_basis="nominal", energy_boundary="dc")
    with pytest.raises(ValueError, match="Family rating ranges"):
        validate_record(row, sources)
    row = copy.deepcopy(rows[0])
    row["field_sources_json"] = "{}"
    with pytest.raises(ValueError, match="Missing evidence"):
        validate_record(row, sources)
    row["field_sources_json"] = json.dumps({"*": row["sources"]})
    with pytest.raises(ValueError, match="unregistered column"):
        validate_record(row, sources)
    with pytest.raises(ValueError, match="Duplicate equipment identity"):
        validate_catalogue([rows[0], rows[0]], sources)


def test_snapshot_preserves_nulls_units_evidence_and_timestamps(tmp_path, catalogue):
    rows, sources = catalogue
    first = build_parquet(ROOT, tmp_path / "first")
    assert first == build_parquet(ROOT, tmp_path / "second")
    table = pq.read_table(tmp_path / "first/systems.parquet")
    assert table.num_rows == len(rows)
    assert len(table.schema) == len(SCHEMA["fields"])
    assert table.schema.field("power_capacity_mw").metadata[b"unit"] == b"MW"
    assert table.schema.field("apparent_power_mva").metadata[b"unit"] == b"MVA"
    assert table.schema.field("created_at").type == pa.timestamp("us", tz="UTC")
    for original, exported in zip(rows, table.to_pylist(), strict=True):
        assert exported["energy_capacity_mwh"] == original.get("energy_capacity_mwh")
        assert exported["source_urls"] == sorted({sources[s]["url"] for s in original["sources"]})
        assert exported["field_sources_json"] == original["field_sources_json"]
    with pytest.raises(FileExistsError):
        build_parquet(ROOT, tmp_path / "first")
