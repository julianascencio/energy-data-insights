"""Synthetic region tables test identity, units, dates and complete partitions."""

import pytest

from energy_data_retrieval.bess_catalogue.dcceew_community import (
    COUNTS,
    HEADER,
    parse_community_tables,
)


def fixture():
    lines = ["Last updated: 12 October 2026", "### Business Grants Hub streams 1 & 2"]
    for region, count in COUNTS.items():
        lines.extend([f"#### [Button: {region}]", HEADER])
        for i in range(count):
            status = "In progress" if i == 0 else "From 1/2/25"
            lines.append(f"Applicant | Place {i} | $500,000 | 200 | {status}")
    return "\n".join([*lines, "### ARENA Community Batteries round 1"])


def test_all_rows_and_no_lifecycle_or_owner_inference():
    rows = parse_community_tables(fixture())
    assert len(rows) == 57
    assert rows[0]["operational_from"] is None
    assert rows[1]["operational_from"] == "2025-02-01"
    assert rows[0]["capacity_kwh"] == 200
    assert "owner" not in rows[0] and "status" not in rows[0]
    prefixed = "\n".join(f"L{i}: {line}" for i, line in enumerate(fixture().splitlines()))
    assert parse_community_tables(prefixed) == rows


@pytest.mark.parametrize(
    "old,new",
    [
        ("12 October 2026", "13 October 2026"),
        ("(kWh) capacity", "(MW) capacity"),
        ("Place 1", "Place 0"),
        ("From 1/2/25", "From 31/2/25"),
        ("From 1/2/25", "From 1/2/27"),
        ("In progress", "Under construction"),
        ("$500,000", "EUR500,000"),
        (" | 200 | ", " | 0 | "),
        ("### ARENA Community Batteries round 1", ""),
    ],
)
def test_changed_or_ambiguous_rows_fail(old, new):
    with pytest.raises(ValueError):
        parse_community_tables(fixture().replace(old, new))


def test_missing_row_fails():
    text = fixture().replace("Applicant | Place 2 | $500,000 | 200 | From 1/2/25\n", "", 1)
    with pytest.raises(ValueError, match="row counts"):
        parse_community_tables(text)
