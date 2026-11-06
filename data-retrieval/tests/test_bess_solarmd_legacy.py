"""Synthetic legacy identity and unit guards; not copied OEM data."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.solarmd import LEGACY_MODELS, parse_legacy_ss7000


def sample():
    return [
        [
            "Battery Name",
            "Module Quantity",
            "Voltage Range (V)",
            "Nominal Voltage (V)",
            "Nominal Capacity (kWh)",
            "Current Rating (A)",
        ]
    ] + [[m, str(i), "100V - 300", "200", "50", "100"] for i, m in enumerate(LEGACY_MODELS, 8)]


def test_no_power_or_warranty_inference():
    rows = parse_legacy_ss7000(sample(), revision="1.0 / 2024-04-26")
    assert len(rows) == 10 and rows[0]["module_model"] == "SS6143"
    assert "power_kw" not in rows[0] and "warranty_years" not in rows[0]


@pytest.mark.parametrize(
    "column,value",
    [(0, "SS7011-05"), (1, "9"), (2, "300V - 100"), (3, "NaN"), (4, "50 kVA"), (5, "-200")],
)
def test_rejects_changes(column, value):
    data = sample()
    data[1][column] = value
    with pytest.raises(ValueError):
        parse_legacy_ss7000(data, revision="1.0 / 2024-04-26")


def test_revision():
    with pytest.raises(ValueError):
        parse_legacy_ss7000(sample(), revision="2.0")
