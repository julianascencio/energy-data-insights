"""Synthetic ERA workbook boundaries, missing data and identity safeguards."""

import copy
import io
import json

import openpyxl
import pytest

from energy_data_retrieval.hydro_catalogue import era


def workbook():
    book = openpyxl.Workbook()
    sheet = book.active
    sheet.title = era.SHEET
    for col, year in enumerate(range(2000, 2027), 4):
        sheet.cell(9, col, year)
    for row, label in {
        10: "Hydro electricity - Large Hydros",
        18: "Hydro-Electricity - Mini-hydros",
        80: "Hydro Electricity- Minihydros",
        47: "Solar PV",
        85: "Solar PV",
    }.items():
        sheet.cell(row, 3, label)
    for row in [*range(11, 18), *range(19, 47), *range(81, 85)]:
        sheet.cell(row, 3, f"Synthetic station {row}")
        sheet.cell(row, 30, 0.064 if row == 83 else 2)
    sheet.cell(11, 5, 0)
    sheet.cell(48, 3, "Non-hydro synthetic plant")
    sheet.cell(48, 30, 9000)
    sheet.cell(103, 3, "Total")
    sheet.cell(103, 30, 9999)
    return book


def parse(book):
    buffer = io.BytesIO()
    book.save(buffer)
    book.close()
    return era.parse_inventory(buffer.getvalue())


def entry():
    return {
        "inventory": {
            "row": 11,
            "source_name": "Synthetic station",
            "observations": [],
        },
        "review": {
            "decision": "reviewed_new_identity",
            "source_name": "Synthetic station",
            "name": "Synthetic station",
            "aliases": ["Synthetic alias"],
            "accession": "synthetic-001",
            "identity_basis": "Synthetic regulator review",
            "report_locator": "Synthetic report row",
        },
    }


def test_complete_hydro_partition_preserves_missing_zero_and_micro_scale():
    rows = parse(workbook())
    assert len(rows) == 39
    assert sum(len(r["observations"]) for r in rows) == 1053
    assert rows[0]["observations"][0]["value"] is None
    assert rows[0]["observations"][1]["value"] == 0
    assert rows[-2]["observations"][-1]["value"] == 0.064
    assert rows[-2]["section"] == "Off-grid mini hydro"
    assert rows[0]["observations"][-1]["period"] == "2026 (as of September)"
    assert rows[0]["observations"][-1]["locator"].startswith(era.SHEET + "!AD11;")
    assert not any(o["value"] in (9000, 9999) for r in rows for o in r["observations"])


@pytest.mark.parametrize("cell,value", [("D9", 1999), ("C18", "Solar"), ("C85", "Hydro")])
def test_shape_drift_fails(cell, value):
    book = workbook()
    book.active[cell] = value
    with pytest.raises(ValueError, match="Unexpected"):
        parse(book)


@pytest.mark.parametrize("value", [-1, True, "2 MW"])
def test_invalid_capacity_fails(value):
    book = workbook()
    book.active["AD11"] = value
    with pytest.raises(ValueError, match="Invalid generating capacity"):
        parse(book)


def test_empty_and_duplicate_rows_fail():
    book = workbook()
    book.active["C12"] = "Synthetic station 11"
    with pytest.raises(ValueError, match="duplicate"):
        parse(book)
    book = workbook()
    book.active["AD12"] = None
    with pytest.raises(ValueError, match="Empty"):
        parse(book)


def test_accession_stable_no_operational_or_additive_promotion():
    e = entry()
    row = era.new_record(e, now="2026-11-06T00:00:00Z")
    changed = copy.deepcopy(e)
    changed["review"]["source_name"] = changed["inventory"]["source_name"] = "Renamed"
    changed["review"]["name"] = "Renamed"
    assert era.new_record(changed, now="2026-11-06T00:00:00Z")["record_id"] == row["record_id"]
    assert row["external_ids_json"] == "{}"
    assert row["aggregation_role"] == "unresolved"
    assert row["status"] == "unknown"
    for field in (
        "latitude",
        "installed_capacity_mw",
        "storage_capacity_mwh",
        "pumping_capacity_mw",
    ):
        assert row.get(field) is None
    assert era.REPORT_ID in json.loads(row["field_sources_json"])["name"]


@pytest.mark.parametrize(
    "field", ["decision", "source_name", "accession", "identity_basis", "report_locator"]
)
def test_review_required(field):
    e = entry()
    e["review"][field] = ""
    with pytest.raises(ValueError, match="identity review"):
        era.new_record(e, now="2026-11-06T00:00:00Z")


def test_duplicate_accessions_and_alias_collision_fail_before_write(tmp_path, monkeypatch):
    monkeypatch.setattr(era, "load_records", lambda root: [])
    batch = {"reviewed_at": "2026-11-06T00:00:00Z", "accepted": [entry(), entry()]}
    output = tmp_path / "new.jsonl"
    with pytest.raises(ValueError, match="Duplicate"):
        era.accept_new(tmp_path, batch, output)
    assert not output.exists()
    prior = era.new_record(entry(), now=batch["reviewed_at"])
    prior.update(record_id="different", name="Unrelated name", aliases=["Synthetic alias"])
    monkeypatch.setattr(era, "load_records", lambda root: [prior])
    batch["accepted"] = [entry()]
    with pytest.raises(ValueError, match="Name collision"):
        era.accept_new(tmp_path, batch, output)
    assert not output.exists()
