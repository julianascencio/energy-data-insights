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
