"""Synthetic portfolio controls: no original report fixture reproduced."""

import pytest

from energy_data_retrieval.bess_catalogue.flower import parse_flower_portfolio

TABLE = b"""Second quarter interim report 2026\fOperational BESS assets  Size (MW)  Size (MWh)
Alpha  2  3  Right column narrative
Assets under construction
Beta  4  8
Total  6  11
"""


def test_stages_units_and_page_without_duration_or_cod():
    rows = parse_flower_portfolio(TABLE)
    assert [r["status"] for r in rows] == ["operational", "under_construction"]
    assert rows[0]["source_page"] == 2
    assert rows[1]["energy_mwh"] == 8
    assert "duration" not in rows[0]
    assert "commercial_operation_date" not in rows[0]


@pytest.mark.parametrize(
    "content",
    [
        TABLE.replace(b"Beta", b"Alpha"),
        TABLE.replace(b"2026", b"2027"),
        TABLE.replace(b"Assets under construction", b"Unknown section"),
        TABLE.replace(b"Total  6", b"Total  7"),
        TABLE.replace(b"Total  6  11", b""),
        TABLE.replace(b"Size (MWh)", b"Size (GWh)"),
        TABLE.replace(b"Alpha  2  3", b"Alpha  0  3"),
    ],
)
def test_ambiguous_or_invalid_inventory_fails(content):
    with pytest.raises(ValueError):
        parse_flower_portfolio(content)
