"""Synthetic table tests; no OEM documents redistributed."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.crown import SOURCE_URL, parse_crown_table

HEADER = """SB-CRP-G0720
Specifications effective as of July 1, 2020.
Depth-of-Discharge (DoD) of 50%, or 1.94 VPC.
100-Hr
2, 6 & 12 VOLT CRP MONOBLOC SERIES — LOW MAINTENANCE FLA
"""
ROW = "GC2 6CRP235 6 235 260 1.37 1.51 10.25 260 7.06 179 10.94 278 63 28.6 STD\n"


def parse(text: str):
    return parse_crown_table(text.encode(), source_url=SOURCE_URL)


def test_keeps_energy_and_rate_conditions_separate():
    row = parse(HEADER + ROW)[0]
    assert row["capacity_ah"] == {"C20": 235, "C100": 260}
    assert row["reported_energy_kwh"] == {"C20": 1.37, "C100": 1.51}
    assert "energy_capacity_mwh" not in row
    assert "cell_capacity_ah" not in row
    assert row["dimensions_mm"]["height"] == 278


@pytest.mark.parametrize(
    "changed",
    [
        HEADER.replace("G0720", "G0721") + ROW,
        HEADER + ROW + ROW,
        HEADER + ROW.replace("260 1.37", "1.37"),
        HEADER + ROW.replace("235 260", "0 260"),
        HEADER,
    ],
)
def test_changed_or_ambiguous_input_fails(changed):
    with pytest.raises(ValueError):
        parse(changed)


def test_multiword_terminal_and_no_bci():
    text = (
        HEADER + "2 & 6 VOLT CRP POWER MODULE SERIES — LOW MAINTENANCE FLA\n"
        "— 2CRP2500 2 2500 3275 4.85 6.35 12.81 325 6.56 167 33.37 848 313 141.9 HD SS\n"
    )
    row = parse(text)[0]
    assert row["terminal"] == "HD SS"
    assert row["bci_group"] is None
    assert row["product_level"] == "flooded_module"


def test_unreviewed_url_rejected():
    with pytest.raises(ValueError):
        parse_crown_table((HEADER + ROW).encode(), source_url="https://example.com/table.pdf")
