"""Synthetic boundary cases; no live network or fabricated real plants."""

import json
from pathlib import Path

import pytest

from energy_data_retrieval.hydro_catalogue import (
    build_parquet,
    capacity_summary,
    stable_id,
    validate_catalogue,
    validate_record,
)
from energy_data_retrieval.hydro_catalogue.gppd import evidence_record, parse_gppd

NOW = "2026-11-05T08:18:58Z"
SOURCE = {
    "synthetic": {
        "url": "https://example.org/synthetic.csv",
        "publisher": "Synthetic fixture",
        "title": "Synthetic fixture",
        "license": "Synthetic test fixture",
        "retrieved_at": NOW,
        "original_availability": "Synthetic in-memory bytes",
    }
}
HEADER = (
    "country,name,gppd_idnr,primary_fuel,capacity_mw,latitude,longitude,"
    "year_of_capacity_data,generation_gwh_2019,estimated_generation_gwh_2019\n"
)


def fixture(**extra):
    values = {
        "record_id": stable_id("projects", "synthetic", "one"),
        "entity_type": "projects",
        "name": "Synthetic hydro",
        "record_scope": "plant",
        "capacity_scope": "Synthetic plant",
        "country_code": "GBR",
        "status": "operational",
        "status_as_of": "2026-11-05",
        "status_date_basis": "Synthetic observation",
        "technology": "pumped_storage",
        "aggregation_role": "independent",
        **extra,
    }
    return evidence_record(values, source_id="synthetic", now=NOW, locator="synthetic fixture")


def test_import_keeps_historical_and_modeled_separate():
    rows, ledger = parse_gppd(
        HEADER + "GBR,Synthetic,H1,Hydro,0,52,-3,,2,3\nGBR,Other,S1,Solar,5,52,-3,,,\n",
        source_id="synthetic",
        now=NOW,
    )
    assert len(rows) == len(ledger) == 1
    row = rows[0]
    assert row["historical_capacity_mw"] == 0
    assert row["status"] == row["technology"] == "unknown"
    assert row["aggregation_role"] == "unresolved"
    assert "installed_capacity_mw" not in row
    assert [x["kind"] for x in json.loads(row["observations_json"])] == ["reported", "modeled"]
    validate_catalogue(rows, SOURCE)
    assert capacity_summary(rows, "historical_capacity_mw")["excluded"] == 1


@pytest.mark.parametrize(
    "capacity,lat,lon",
    [("-1", "52", "-3"), ("nan", "52", "-3"), ("1", "91", "-3"), ("1", "52", "")],
)
def test_invalid_rows_are_deferred(capacity, lat, lon):
    rows, decisions = parse_gppd(
        HEADER + f"GBR,Synthetic,H1,Hydro,{capacity},{lat},{lon},2020,,\n",
        source_id="synthetic",
        now=NOW,
    )
    assert not rows
    assert decisions[0]["decision"] == "deferred"


def test_duplicate_source_id_fails():
    line = "GBR,Synthetic,H1,Hydro,1,52,-3,2020,,\n"
    with pytest.raises(ValueError, match="duplicate"):
        parse_gppd(HEADER + line + line, source_id="synthetic", now=NOW)


def test_scopes_and_pumping_are_not_added_to_generation():
    rows = [
        fixture(installed_capacity_mw=100, pumping_capacity_mw=120),
        fixture(aggregation_role="aggregate", installed_capacity_mw=100),
        fixture(aggregation_role="unresolved", installed_capacity_mw=50),
        fixture(installed_capacity_mw=0, technology="run_of_river"),
        fixture(),
    ]
    report = capacity_summary(rows, "installed_capacity_mw")
    assert report["excluded"] == 2
    assert report["unknown"] == 1
    assert report["by_status"]["operational/pumped_storage"]["reported_mw"] == 100
    assert report["by_status"]["operational/run_of_river"]["reported_mw"] == 0
    assert (
        capacity_summary(rows, "pumping_capacity_mw")["by_status"]["operational/pumped_storage"][
            "reported_mw"
        ]
        == 120
    )
    # Filtering to parents cannot accidentally include their aggregate capacities.
    assert capacity_summary(rows[1:2], "installed_capacity_mw")["by_status"] == {}


@pytest.mark.parametrize(
    "extra",
    [
        {"net_head_m": 10, "gross_head_m": 9},
        {"usable_reservoir_volume_m3": 11, "reservoir_volume_m3": 10},
        {"latitude": 52},
        {"aggregation_role": "child"},
    ],
)
def test_physical_and_identity_boundaries(extra):
    with pytest.raises(ValueError):
        validate_record(fixture(**extra), SOURCE)


def test_deterministic_snapshot_and_duplicate_identity(tmp_path):
    root = tmp_path / "catalogue"
    (root / "records/projects").mkdir(parents=True)
    row = fixture(installed_capacity_mw=100)
    (root / "records/projects/test.jsonl").write_text(json.dumps(row) + "\n")
    (root / "sources.json").write_text(json.dumps(SOURCE))
    a, b = tmp_path / "a", tmp_path / "b"
    assert build_parquet(root, a) == build_parquet(root, b)
    assert (a / "projects.parquet").read_bytes() == (b / "projects.parquet").read_bytes()
    with pytest.raises(ValueError, match="Duplicate"):
        validate_catalogue([row, row], SOURCE)


def test_committed_catalogue():
    from energy_data_retrieval.hydro_catalogue import load_records

    root = Path(__file__).resolve().parents[2] / "catalogues/hydro"
    rows = load_records(root)
    validate_catalogue(rows, json.loads((root / "sources.json").read_text()))
    assert rows
