"""Synthetic exact small-battery dimensions and optional rate rows."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.fullriver import parse_small_battery_sheet

TEXT = """TEST-12
DEEP CYCLE AGM
Nominal Voltage 12 Volt
 C100 15 AH
 C20 12 AH
 C10 11 AH
 C5 10 AH
 C1 15 AH
Internal Resistance 14m Ω
Height (w/ terminal) 3.98” 101mm
Height (case only) 3.74” 95mm
Width 3.9” 99mm
Length 5.94” 151mm
Weight 9.26 lbs. 4.2 kg
100% SoC, 25°C, 1.75VPC
"""


def test_native_observations_not_repaired():
    r = parse_small_battery_sheet(TEXT, model="TEST-12")
    capacities = r["capacity_ah_by_discharge_hours"]
    mechanical = r["mechanical"]
    assert isinstance(capacities, dict) and isinstance(mechanical, dict)
    assert capacities["1"] == 15
    assert "3" not in capacities
    assert mechanical["case_height_mm"] == 95
    assert mechanical["terminal_height_mm"] == 101


@pytest.mark.parametrize(
    "old,new",
    [
        ("TEST-12", "TEST-12B"),
        ("101mm", "101cm"),
        ("95mm", "105mm"),
        ("4.2 kg", "4.2 lbs"),
        ("DEEP CYCLE AGM", "DEEP CYCLE"),
        ("C1 15 AH", "C1 15 AH\nC1 16 AH"),
    ],
)
def test_ambiguous_or_changed_dimensions(old, new):
    with pytest.raises(ValueError):
        parse_small_battery_sheet(TEXT.replace(old, new), model="TEST-12")
