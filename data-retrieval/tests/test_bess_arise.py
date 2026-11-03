"""Synthetic layout-shaped input, not a redistributed government document."""

import pytest

from energy_data_retrieval.bess_catalogue.arise import SITE_LABELS, parse_arise_screening


def document():
    rows = []
    for i, label in enumerate(SITE_LABELS):
        row = f"{label} 0.5 20\u2019x8\u2019 2 123"
        if i == 3:
            row = "Addu (Mainland 2.5 40\u2019x8\u2019 1 456\n in Hithadhoo)"
        if i == 4:
            row = "Addu 1 40\u2019 x 8\u2019 1 456\n (Hulhudhoo\n Meedhoo)"
        rows.append(row)
    return (
        "37 MWh\fIsland Capacity Container Number Estimate\n(MWh) Size Area (sqft)\n"
        + "\n".join(rows)
        + "\npg. 15\f09th December 2021\nPRIVATE CONTACT NOT EXPORTED"
    )


def test_shared_grids_and_independent_planning_values():
    rows = parse_arise_screening(document())
    assert len(rows) == 18
    assert rows[3]["source_site_label"] == "Addu (Mainland in Hithadhoo)"
    assert rows[4]["source_site_label"] == "Addu (Hulhudhoo Meedhoo)"
    assert rows[3]["planned_energy_mwh"] == 2.5
    assert rows[9]["source_site_label"] == "Kallaidhoo"
    assert sum(r["planned_energy_mwh"] for r in rows) == 11.5
    assert rows[0]["estimated_container_count"] == 2
    assert rows[0]["estimated_area_sqft"] == 123
    assert "PRIVATE CONTACT" not in str(rows)
    assert all("status" not in r and "power_mw" not in r for r in rows)


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("(MWh)", "(MW)"),
        ("09th December 2021", "09th December 2022"),
        ("Eydhafushi", "Thinadhoo"),
        ("Villingili 0.5 20\u2019x8\u2019 2 123", ""),
        ("Eydhafushi 0.5", "Eydhafushi 0"),
        ("0.5 20\u2019x8\u2019 2", "0.5 20\u2019x8\u2019 0"),
        ("pg. 15", "pg. 16"),
    ],
)
def test_unreviewed_layout_or_identity_requires_review(old, new):
    with pytest.raises(ValueError):
        parse_arise_screening(document().replace(old, new, 1))


def test_duplicate_table_is_not_silently_selected():
    with pytest.raises(ValueError, match="one reviewed"):
        parse_arise_screening(document() + "\f" + document())
