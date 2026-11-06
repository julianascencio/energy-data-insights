"""Synthetic table tests for configuration/measurement boundaries."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.pylontech_force import parse_force


def table(family="Force-L2"):
    count = 3 if family == "Force-L2" else 6
    module, controller, version, code = (
        ("FL4874M", "FC0048M-100S", "2.2", "20P2FL0301")
        if count == 3
        else ("FL48074", "FC0048-100S", "2.3", "20P1FL0302")
    )
    numbers = " ".join(str(x) for x in range(2, count + 2))
    normal = "75 100 100" if count == 3 else "75 100"
    peak = "Max.@15S" if count == 3 else "Max."
    rows = [
        f"{family} Operation Manual\nInformation Version: {version}\n{code}\f",
        "Battery System Capacity(kWh) " + " ".join(str(4 * x) for x in range(2, count + 2)),
        "Battery Module Quantity(pcs) " + numbers,
        "Battery System Capacity(" + ("Ah" if count == 3 else "AH") + ") " + numbers,
        "Battery Module Name " + module,
        "Battery Controller Name " + controller,
        "Battery System Voltage(Vdc) 48",
        "Battery System Charge Upper-Voltage(Vdc) 53.5",
        "Battery System Discharge lower-Voltage(Vdc) 44.5",
        "Weight (kg) " + numbers,
    ]
    for action in ["Charge", "Discharge"]:
        peak_class = "Max.@15S" if action == "Charge" else peak
        rows += [
            f"Battery System {action} Current(Amps, Standard) " + numbers,
            f"Battery System {action} Current(Amps, Normal) " + normal,
            f"Battery System {action} Current(Amps, {peak_class}) 110",
        ]
    return "\n".join(rows)


@pytest.mark.parametrize("family,count", [("Force-L1", 6), ("Force-L2", 3)])
def test_explicit_configurations_and_merged_current(family, count):
    rows = parse_force(table(family), family=family)
    assert len(rows) == count
    assert [r["module_count"] for r in rows] == list(range(2, count + 2))
    assert rows[0]["charge_normal_a"] == 75
    assert all(r["charge_normal_a"] == 100 for r in rows[1:])
    assert rows[-1]["discharge_peak_seconds"] == (None if count == 6 else 15)
    assert not any("power" in key for row in rows for key in row)


@pytest.mark.parametrize(
    "before,after",
    [
        ("Information Version: 2.2", "Information Version: 2.3"),
        ("Battery Module Quantity(pcs) 2 3 4", "Battery Module Quantity(pcs) 2 2 4"),
        ("Battery System Capacity(kWh) 8 12 16", "Battery System Capacity(MWh) 8 12 16"),
        (
            "Battery System Charge Current(Amps, Normal) 75 100 100",
            "Battery System Charge Current(Amps, Normal) 75 100",
        ),
        ("FL4874M", "FL48074"),
        ("Battery System Voltage(Vdc) 48", "Battery System Voltage(Vdc) 60"),
    ],
)
def test_reject_changed_identity_units_columns_and_bounds(before, after):
    with pytest.raises(ValueError):
        parse_force(table().replace(before, after), family="Force-L2")


def test_reject_duplicate_table_and_unknown_family():
    with pytest.raises(ValueError):
        parse_force(table() + "\f" + table(), family="Force-L2")
    with pytest.raises(ValueError):
        parse_force(table(), family="Force-L3")
