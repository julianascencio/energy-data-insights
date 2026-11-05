"""Synthetic fixtures: exact identities, discharge rates and explicit units."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.fullriver import parse_datasheet

TEXT = """SYNTHETIC-1
 C100 150AH
 C20 125AH
 C10 112AH
 C5 100AH
 Internal Resistance 2.4m Ω
All listed ratings @ 100% SoC, 25°C, 1.75VPC
"""


def test_rate_and_boundary():
    row = parse_datasheet(TEXT, model="SYNTHETIC-1")
    assert row["capacity_ah_by_discharge_hours"] == {"100": 150, "20": 125, "10": 112, "5": 100}
    assert row["internal_resistance_milliohm"] == 2.4
    assert row["end_voltage_v_per_cell"] == 1.75


@pytest.mark.parametrize(
    "old,new",
    [
        ("25°C", "20°C"),
        ("C20 125AH", "C20 125A"),
        ("2.4m Ω", "2.4 Ω"),
        ("SYNTHETIC-1", "SYNTHETIC-1B"),
        ("C5 100AH", "C5 100AH\nC5 101AH"),
    ],
)
def test_changed_identity_units_or_conditions(old, new):
    with pytest.raises(ValueError):
        parse_datasheet(TEXT.replace(old, new), model="SYNTHETIC-1")
