"""Synthetic report fixture for strict units and exact island partition."""

import pytest

from energy_data_retrieval.bess_catalogue.adb_pacific import parse_cook_outer_islands

PAGE = """Table 3.3 continued Subproject: 3
Mitiaro: 159 kW solar PV, 72 kW/972 kWh BESS
Mauke: 229 kW solar PV, 90 kW/1214 kWh BESS
Atiu: 413 kW solar PV, 162 kW/2186 kWh BESS
Mangaia: 477 kW solar PV, 216 kW/2915 kWh BESS
sealed lead-acid technology Minimum state of charge approximately 50%
All projects were completed in 2019
"""
TEXT = "TCS220320-2 AUGUST 2022" + "\f" * 38 + PAGE


def test_battery_and_solar_are_separate():
    rows = parse_cook_outer_islands(TEXT)
    assert len(rows) == 4
    assert rows[0]["battery_power_kw"] == 72
    assert rows[0]["solar_power_kw"] == 159
    capacities = [r["battery_energy_kwh"] for r in rows]
    assert all(isinstance(v, int) for v in capacities)
    assert capacities == [972, 1214, 2186, 2915]
    assert rows[0]["energy_basis"] == "unspecified"


@pytest.mark.parametrize(
    "old,new",
    [
        ("972 kWh", "972 MWh"),
        ("Mitiaro:", "Mauke:"),
        ("approximately 50%", "approximately 40%"),
        ("AUGUST 2022", "AUGUST 2023"),
    ],
)
def test_changed_scope_or_units(old, new):
    with pytest.raises(ValueError):
        parse_cook_outer_islands(TEXT.replace(old, new))
