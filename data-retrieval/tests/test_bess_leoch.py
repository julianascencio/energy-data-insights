"""Synthetic boundary tests, not redistributed OEM text fixtures."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.leoch import parse_opzv

TEXT = """OPzV SERIES-TUBULAR GEL
4OPzV200
Publication No.:LB-4OPzV200-PD-EN-V0-20000101
Rated Voltage P-RV 2V
Nominal Capacity (25℃) C10,1.80V/cell P-1080 123Ah
Short-circuit current P-SC 789A
Max.Charging Current (25℃) 0.25C
12.3kg (example)
-20~55℃ 0~40℃ -20~50℃ 2.23-2.27V/cell 2.40-2.45V/cell
20 year design life (20℃) ≤3% per month at 25°C
"""


def test_units():
    row = parse_opzv(TEXT, "4OPzV200")
    assert row["capacity_ah"] == 123
    assert row["short_circuit_a"] == 789
    assert row["maximum_charging_c_rate"] == 0.25
    assert "power_capacity_mw" not in row


@pytest.mark.parametrize(
    "old,new",
    [
        ("2V", "12V"),
        ("0.25C", "0.25A"),
        ("C10,1.80V/cell", "C20,1.80V/cell"),
        ("123Ah", "0Ah"),
        ("4OPzV200-PD", "5OPzV250-PD"),
        ("-20~55℃", "-20~50℃"),
    ],
)
def test_changed_scope(old, new):
    with pytest.raises(ValueError):
        parse_opzv(TEXT.replace(old, new), "4OPzV200")


def test_duplicate():
    with pytest.raises(ValueError):
        parse_opzv(TEXT + "\nShort-circuit current 10A", "4OPzV200")


def test_heading_required():
    with pytest.raises(ValueError):
        parse_opzv(TEXT.replace("\n4OPzV200\n", "\n5OPzV250\n"), "4OPzV200")
