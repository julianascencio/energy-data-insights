"""Synthetic register fixtures test boundaries independently of live downloads."""

from datetime import datetime

import pytest

from energy_data_retrieval.wind_catalogue.dnv import HEADER, gearbox_partition


def test_dated_register_preserves_statement_scope_and_unknown_expiry():
    rows = [
        HEADER,
        (
            "CC DNV-SE-0074",
            "Component",
            "Applicant",
            "DE-1",
            "Gearbox synthetic",
            datetime(2020, 1, 2),
            None,
        ),
        ("Other", "Other", "Applicant", "CC-2", "Gearbox other", None, None),
    ]
    got = gearbox_partition(rows)
    assert got == [
        dict(
            row=2,
            scheme="CC DNV-SE-0074",
            applicant="Applicant",
            certificate="DE-1",
            object="Gearbox synthetic",
            issued="2020-01-02",
            valid_until=None,
        )
    ]
    assert "manufacturer" not in got[0] and "current_validity" not in got[0]


def test_bad_header_duplicate_identifier_and_string_date_fail_closed():
    row = ("CC DNV-SE-0074", "Component", "Applicant", "CC-1", "Gearbox synthetic", None, None)
    for rows in [[("bad",)], [HEADER, row, row], [HEADER, (*row[:5], "2020-01-01", None)]]:
        with pytest.raises(ValueError):
            gearbox_partition(rows)


def test_complementary_partition_does_not_infer_component_category():
    from energy_data_retrieval.wind_catalogue.dnv import component_partition

    rows = [
        HEADER,
        (
            "CC DNV-SE-0074",
            "Component",
            "Applicant",
            "DB-1",
            "Plain Bearing Drive Train",
            None,
            None,
        ),
        ("CC DNV-SE-0074", "Component", "Applicant", "CC-2", "CMG465BFI72-0323", None, None),
        ("CC DNV-SE-0074", "Component", "Applicant", "CC-3", "Gearbox synthetic", None, None),
    ]
    selected = component_partition(rows, gearbox_mentions=False)
    assert [r["row"] for r in selected] == [2, 3]
    assert selected[0]["certificate"] == "DB-1"
    assert all("equipment_category" not in r for r in selected)
    assert len(selected) + len(gearbox_partition(rows)) == 3
