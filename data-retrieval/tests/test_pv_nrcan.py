"""Synthetic identity, rights and inference boundaries for the MPI reader."""

import hashlib
import io

import openpyxl
import pytest

from energy_data_retrieval.pv_catalogue.nrcan import HEADERS, read_nrcan_mpi


def sample(*, notice="", updates=None, headers=HEADERS, duplicate=False):
    book = openpyxl.Workbook()
    about = book.active
    about.title = "About + Caveats"
    about.append(["Potential cost estimates are approximate.", notice])
    book.create_sheet("Definitions")
    private = book.create_sheet("__vendor")
    private.sheet_state = "hidden"
    private.append(["PRIVATE_TOKEN"])
    sheet = book.create_sheet("MPI 2025 Data")
    sheet.append(headers)
    row = dict.fromkeys(HEADERS)
    row.update(
        {
            "Project ID": "0007",
            "Project Name": "Synthetic Solar",
            "Company/ Proponent": "Example Ltd",
            "P/T": "AB",
            "Status 2025": "Approved",
            "Cost 2025 (CAD) {$M}": 12.5,
            "Sector": "Energy",
            "ENERGY - Type": "Electricity",
            "Cleantech - Type": "Solar",
            "Latitude 1": 50,
            "Longitude 1": -110,
        }
    )
    row.update(updates or {})
    sheet.append([row.get(h) for h in headers])
    if duplicate:
        sheet.append([row.get(h) for h in headers])
    output = io.BytesIO()
    book.save(output)
    return output.getvalue()


def read(data):
    return read_nrcan_mpi(data, sha256=hashlib.sha256(data).hexdigest())


def test_no_identity_power_or_owner_inference():
    result = read(sample())
    assert result["source_rows_reviewed"] == 1
    row = result["candidates"][0]
    assert row["source_project_id"] == "0007"
    assert row["cost_2025_million_cad_as_reported"] == 12.5
    assert row["accepted"] is False
    assert len(row["held_reasons"]) == 6
    assert not {"owners", "capacity_ac_mw", "status", "latitude", "longitude"} & row.keys()
    assert "PRIVATE_TOKEN" not in str(result)


@pytest.mark.parametrize(
    "notice",
    [
        "This spreadsheet or parts thereof are not authorized or approved "
        "for publication at this time.",
        "NOT  AUTHORIZED\nOR APPROVED FOR PUBLICATION",
        "Not authorised for publication",
        "Not approved for publication",
    ],
)
def test_embedded_restriction_cannot_be_overridden(notice):
    with pytest.raises(ValueError, match="publication restriction"):
        read(sample(notice=notice))


def test_checksum_before_workbook_parsing():
    with pytest.raises(ValueError, match="checksum"):
        read_nrcan_mpi(b"not a workbook", sha256="0" * 64)


def test_header_change_is_not_silently_mapped():
    with pytest.raises(ValueError, match="schema"):
        read(sample(headers=(*HEADERS[:-1], "Technology")))


def test_duplicate_identity_is_not_merged():
    with pytest.raises(ValueError, match="duplicate"):
        read(sample(duplicate=True))


def test_numeric_id_does_not_lose_leading_zeroes():
    with pytest.raises(ValueError, match="four-digit"):
        read(sample(updates={"Project ID": 7}))


@pytest.mark.parametrize("cost", [-1, True, "12\u201320"])
def test_cost_types_and_bounds_require_review(cost):
    with pytest.raises(ValueError, match="cost malformed"):
        read(sample(updates={"Cost 2025 (CAD) {$M}": cost}))


def test_non_solar_is_not_a_candidate():
    assert read(sample(updates={"Cleantech - Type": "Wind"}))["candidates"] == []


def test_sector_mismatch_is_not_positive_pv():
    with pytest.raises(ValueError, match="classification"):
        read(sample(updates={"Sector": "Mining"}))


def test_valid_checksum_does_not_make_invalid_workbook_readable():
    with pytest.raises(ValueError, match="unreadable"):
        read(b"not a workbook")


def test_missing_public_identity_is_not_staged():
    with pytest.raises(ValueError, match="identity"):
        read(sample(updates={"Project Name": ""}))
