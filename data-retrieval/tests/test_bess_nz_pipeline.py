"""Synthetic planning inventories, not copies of publisher rows."""

import csv
import io

import pytest
from openpyxl import Workbook

from energy_data_retrieval.bess_catalogue.nz_pipeline import (
    HEADERS,
    parse_nz_pipeline,
    parse_transpower_pipeline,
)


def csv_data(**overrides):
    row = dict(
        zip(
            HEADERS,
            [
                "Synthetic Developer",
                "Test battery",
                "Electrical energy",
                "Chemical battery energy storage system",
                "12",
                "-",
                "999",
                "2020",
                "Committed",
                "Y",
                "North Island",
            ],
            strict=True,
        )
    )
    row.update(overrides)
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=HEADERS)
    writer.writeheader()
    writer.writerow(row)
    return stream.getvalue().encode("utf-8-sig")


def test_planning_year_not_cod_and_annual_energy_not_storage():
    row = parse_nz_pipeline(csv_data())[0]
    assert row["source_row"] == 2
    assert row["power_mw"] == 12
    assert row["earliest_commissioning_year"] == 2020
    assert row["planning_status"] == "Committed"
    assert "status" not in row and "energy_mwh" not in row


def test_nonbattery_excluded():
    assert parse_nz_pipeline(csv_data(Technology="Pumped hydro")) == []


@pytest.mark.parametrize(
    "changes",
    [{"Fuel": "Water"}, {"Megawatts": "nan"}, {"Status": "Operating"}, {"Grid connected?": "?"}],
)
def test_unreviewed_classification_or_units_fail(changes):
    with pytest.raises(ValueError):
        parse_nz_pipeline(csv_data(**changes))


def test_duplicate_candidate_rejected():
    content = csv_data().decode("utf-8-sig")
    with pytest.raises(ValueError, match="duplicate"):
        parse_nz_pipeline((content + content.splitlines()[-1] + "\n").encode())


def workbook(duplicate=False):
    book = Workbook()
    sheet = book.active
    sheet.title = "Forward Pipeline"
    sheet.append(
        [
            "Project ID",
            "Parent Project ID",
            "Customer",
            "Project name",
            "Region",
            "Connection location (substation or circuit)",
            "Max MW",
            "Connection voltage",
            "Technology",
            "Transpower stage",
            "Status Flag",
            "Stage % complete",
            "Status",
            "Consented",
            "Estimated connection livening date",
        ]
    )
    sheet.append([1, 0, "Test", "Solar", "Region", "Node", 50, 33, "Solar"])
    sheet.append(
        [
            2,
            1,
            "Test",
            "Battery",
            "Region",
            "Node",
            50,
            33,
            "BESS",
            "Delivery",
            None,
            0.5,
            "Detailed Design",
            "Consent Granted",
            "TBA",
        ]
    )
    sheet.append(
        [
            2 if duplicate else "0003",
            None,
            None,
            None,
            "Region",
            "Node",
            "20(!10)",
            "33",
            "BESS",
            "Application",
        ]
    )
    stream = io.BytesIO()
    book.save(stream)
    return stream.getvalue()


def test_hybrid_child_and_unnamed_connection_preserved_without_inferred_status():
    rows = parse_transpower_pipeline(workbook())
    assert len(rows) == 2
    assert rows[0]["reported_fields"]["Parent Project ID"] == "1"
    assert rows[0]["reported_fields"]["Status"] == "Detailed Design"
    assert rows[1]["identity_review_required"]
    assert rows[1]["reported_fields"]["Parent Project ID"] is None
    assert rows[1]["reported_fields"]["Project ID"] == "0003"
    assert rows[1]["reported_fields"]["Max MW"] == "20(!10)"
    assert "power_mw" not in rows[1]


def test_duplicate_registry_id_fails():
    with pytest.raises(ValueError, match="duplicate"):
        parse_transpower_pipeline(workbook(duplicate=True))
