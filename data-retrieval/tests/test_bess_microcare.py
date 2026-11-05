"""Synthetic fixtures exercise column identity, units and electrical boundaries."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.microcare import parse_manual


def fixture():
    return """Manual Version: INV-10&15kW- LION- 2021-1-V21R1
Model 10kW48V 15kW48V
Capacity Watt 10000 15000
Nominal Voltage 48 VDC 48 VDC
Acceptable Voltage Range 40-60 VDC 40-60 VDC
Maxi Input Amps 250A 375A
Standby Power 100W 150W
Maximum Current 100A 100A
"""


def test_exact_columns_and_power_boundary():
    rows = parse_manual(fixture(), "10-15")["candidates"]
    assert [(r["model"], r["power_w"], r["maximum_dc_input_a"]) for r in rows] == [
        ("10kW48V", 10000, 250),
        ("15kW48V", 15000, 375),
    ]
    assert all("energy" not in k for row in rows for k in row)


@pytest.mark.parametrize(
    "old,new",
    [
        ("10kW48V 15kW48V", "15kW48V 10kW48V"),
        ("100A 100A", "100A"),
        ("250A 375A", "250kA 375kA"),
        ("40-60 VDC 40-60 VDC", "50-60 VDC 40-60 VDC"),
        ("2021-1-V21R1", "2026-1-V22R1"),
    ],
)
def test_changed_source_fails_closed(old, new):
    with pytest.raises(ValueError):
        parse_manual(fixture().replace(old, new), "10-15")


def test_duplicate_table_and_ambiguous_row_rejected():
    with pytest.raises(ValueError):
        parse_manual(fixture() + fixture(), "10-15")
    with pytest.raises(ValueError):
        parse_manual(fixture() + "Standby Power 80W 90W\n", "10-15")
