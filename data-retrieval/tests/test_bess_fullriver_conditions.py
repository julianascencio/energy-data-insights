"""Synthetic layout fixture; category boundaries matter more than shared values."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.fullriver import parse_charging_conditions

TEXT = """TEST-6
TEMPERATURE RANGE SPECIFICATIONS CHARGE VOLTAGES
Condition Recommended Maximum Recommended Maximum Battery Voltages
Storage 5°F to 122°F -40°F to 160°F -15°C to 50°C -40°C to 71°C Charge Stage 6V 12V 24V 48V
Operation 5°F to 104°F -40°F to 160°F -15°C to 40°C -40°C to 71°C Bulk 7.35V 14.7V 29.4V 58.8V
Charge with TC 5°F to 122°F -40°F to 160°F -15°C to 50°C -40°C to 71°C
Absorption 7.35V 14.7V 29.4V 58.8V
Charge w/o TC 32°F to 104°F 5°F to 122°F 0°C to 40°C -15°C to 50°C Float 6.8V 13.6V 27.2V 54.6V
*TC= Temperature Compensation TC Factor: (-2mV/°F/cell) or (-4mV/°C/cell)
TERMINAL TORQUE
"""


def test_categories_and_bank_boundaries():
    r = parse_charging_conditions(TEXT, model="TEST-6")
    ranges = r["temperature_ranges"]
    charges = r["charge_voltages_v_by_bank_voltage_v"]
    assert isinstance(ranges, dict) and isinstance(charges, dict)
    assert ranges["Charge w/o TC"]["recommended_c"]["min"] == 0
    assert ranges["Charge w/o TC"]["maximum_c"]["min"] == -15
    assert charges["float"]["6"] == 6.8
    assert charges["bulk"]["48"] == 58.8


@pytest.mark.parametrize(
    "old,new",
    [
        ("TEST-6", "TEST-6A"),
        ("6V 12V", "12V 12V"),
        ("7.35V 14.7V", "7.35A 14.7V"),
        ("Recommended Maximum Recommended Maximum", "Maximum Recommended Recommended Maximum"),
        ("0°C to 40°C", "40°C to 0°C"),
        ("-4mV/°C/cell", "-4V/°C/cell"),
        ("Charge w/o TC", "Charge without compensation"),
    ],
)
def test_fail_closed(old, new):
    with pytest.raises(ValueError):
        parse_charging_conditions(TEXT.replace(old, new), model="TEST-6")
