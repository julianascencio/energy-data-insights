"""BESS boundary checks and source-to-Parquet-to-browser conservation."""

import copy
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from energy_data_retrieval.bess_catalogue import (
    SCHEMA,
    build_parquet,
    load_records,
    stable_id,
    validate_catalogue,
)
from energy_data_retrieval.bess_catalogue.catalogue import validate_record

ROOT = Path(__file__).resolve().parents[2] / "catalogues/bess"


@pytest.fixture
def catalogue():
    return load_records(ROOT), json.loads((ROOT / "sources.json").read_text())


def test_committed_records_have_unique_ids_registered_sources_and_separate_scopes(catalogue):
    rows, sources = catalogue
    validate_catalogue(rows, sources)
    assert len({r["country_code"] for r in rows}) >= 20
    assert all(r["entity_type"] == "projects" for r in rows)
    edwards = next(r for r in rows if r["name"] == "Edwards & Sanborn BESS")
    assert edwards.get("power_capacity_mw") is None  # Never substitute site interconnection.
    assert edwards["grid_connection_capacity_mw"] == 1300
    collie = next(r for r in rows if r["name"] == "Neoen Collie Battery")
    phases = json.loads(collie["phases_json"])
    assert sum(p["power_mw"] for p in phases) == collie["power_capacity_mw"]
    assert sum(p["energy_mwh"] for p in phases) == collie["energy_capacity_mwh"]


@pytest.mark.parametrize(
    "field,value,error",
    [
        ("power_capacity_mw", -1, "Out of range"),
        ("energy_capacity_mwh", float("nan"), "Non-finite"),
        ("duration_hours", float("inf"), "Non-finite"),
        ("power_capacity_mw", True, "Wrong type"),
        ("status", "online_probably", "Invalid status"),
        ("status_as_of", "2040-01-01", "after source verification"),
        ("created_at", "2026-01-01T00:00:00", "timezone-aware UTC"),
        ("country_code", "US", "alpha-3"),
        ("latitude", 91, "Out of range"),
        ("unregistered_rating", 1, "unregistered columns"),
    ],
)
def test_invalid_metadata_fails_before_export(catalogue, field, value, error):
    rows, sources = catalogue
    row = copy.deepcopy(rows[0])
    row[field] = value
    with pytest.raises(ValueError, match=error):
        validate_record(row, sources)


def test_missing_evidence_basis_coordinates_and_conflicts_are_rejected(catalogue):
    rows, sources = catalogue
    row = copy.deepcopy(next(r for r in rows if r.get("power_capacity_mw") is not None))
    row["power_basis"] = None
    with pytest.raises(ValueError, match="explicit power_basis"):
        validate_record(row, sources)
    row["power_basis"] = "unspecified"
    row["field_sources_json"] = "{}"
    with pytest.raises(ValueError, match="Missing evidence"):
        validate_record(row, sources)
    row = copy.deepcopy(rows[0])
    row["latitude"] = 10
    with pytest.raises(ValueError, match="Both coordinates"):
        validate_record(row, sources)
    row = copy.deepcopy(next(r for r in rows if r["quality_status"] == "needs_review"))
    row["quality_status"] = "source_backed"
    with pytest.raises(ValueError, match="Conflicting values"):
        validate_record(row, sources)


def test_duplicate_identity_and_external_crosswalks(catalogue):
    rows, sources = catalogue
    with pytest.raises(ValueError, match="Duplicate project"):
        validate_catalogue([rows[0], rows[0]], sources)
    pair = copy.deepcopy(rows[:2])
    for row in pair:
        row["external_ids_json"] = '{"synthetic_registry": "test-123"}'
        evidence = json.loads(row["field_sources_json"])
        evidence["external_ids_json"] = row["sources"]
        row["field_sources_json"] = json.dumps(evidence)
    with pytest.raises(ValueError, match="Duplicate external"):
        validate_catalogue(pair, sources)
    assert stable_id("AUS", "Collie", "Battery") == stable_id("AUS", "Collie", " Battery ")


def test_explicit_null_optional_values_and_reported_zero_are_retained(catalogue):
    rows, sources = catalogue
    row = copy.deepcopy(next(r for r in rows if r.get("power_capacity_mw") is not None))
    row.update(locality=None, conflicts_json=None, external_ids_json=None, power_capacity_mw=0)
    validate_catalogue([row], sources)


def test_snapshot_retains_units_nulls_sources_and_timestamps(tmp_path, catalogue):
    rows, sources = catalogue
    first = build_parquet(ROOT, tmp_path / "first")
    second = build_parquet(ROOT, tmp_path / "second")
    assert first == second
    table = pq.read_table(tmp_path / "first/projects.parquet")
    assert table.num_rows == len(rows)
    assert len(table.schema) == len(SCHEMA["fields"])
    assert table.schema.field("power_capacity_mw").metadata[b"unit"] == b"MW"
    assert table.schema.field("energy_capacity_mwh").metadata[b"unit"] == b"MWh"
    assert table.schema.field("created_at").type == pa.timestamp("us", tz="UTC")
    for original, exported in zip(rows, table.to_pylist(), strict=True):
        assert exported["power_capacity_mw"] == original.get("power_capacity_mw")
        assert exported["source_urls"] == sorted({sources[s]["url"] for s in original["sources"]})
    with pytest.raises(FileExistsError):
        build_parquet(ROOT, tmp_path / "first")
