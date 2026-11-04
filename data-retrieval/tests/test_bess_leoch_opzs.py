"""Synthetic OPzS tests; no OEM fixture redistribution."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.leoch_opzs import parse_opzs

TEXT = """OPzS SERIES-FLOODED BATTERY
2OPzS100
Publication No.:LB-2OPzS100-PD-EN-V0-20000101
Rated Voltage P-RV 2V
Nominal Capacity (20℃) C10,1.80V/cell P-1080 123Ah
Short-circuit current P-SC 789A
Max.Charging Current (20℃) 0.15C
Approx Weight P-GWEIGHT 12.3kg
Dry Weight P-DWEIGHT 8.1kg
-15~55℃ 0~45℃ -15~45℃ 2.23-2.25V/cell 2.40-2.45V/cell
20 years design life (20℃) ≤4% per month at 20°C
"""


def test_mass_and_units():
    row = parse_opzs(TEXT, "2OPzS100")
    assert row["approximate_mass_kg"] == 12.3
    assert row["dry_mass_kg"] == 8.1
    assert row["capacity_ah"] == 123
    assert row["short_circuit_a"] == 789
    assert row["maximum_charging_c_rate"] == 0.15
    assert "power_capacity_mw" not in row


@pytest.mark.parametrize(
    "old,new",
    [
        ("2V", "12V"),
        ("0.15C", "0.15A"),
        ("C10,1.80V/cell", "C20,1.80V/cell"),
        ("123Ah", "P-1080"),
        ("12.3kg", "0kg"),
        ("8.1kg", "8.1lb"),
        ("2OPzS100-PD", "3OPzS150-PD"),
        ("-15~55℃", "-20~55℃"),
        ("\n2OPzS100\n", "\n3OPzS150\n"),
        ("(20℃)", "(25℃)"),
    ],
)
def test_changed_basis(old, new):
    with pytest.raises(ValueError):
        parse_opzs(TEXT.replace(old, new), "2OPzS100")


def test_duplicate_rating():
    with pytest.raises(ValueError):
        parse_opzs(TEXT + "\nShort-circuit current 1A", "2OPzS100")
