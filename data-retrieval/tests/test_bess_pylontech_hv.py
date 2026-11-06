"""Synthetic layouts test scope/identity without redistributing source tables."""

from copy import deepcopy

import pytest

from energy_data_retrieval.bess_oem_catalogue.pylontech_hv import parse_h1_v2

REVISION = "22P1FH1018 / 5PMPA08-00135"


def tables():
    def row(label, values):
        return [label, None, *[str(v) for v in values]]

    first = [
        row("Product Type", ["Force-H1-V2"]),
        row("Cell Technology", ["Li-iron (LFP)"]),
        row("Battery Module Name", ["FH48074"]),
        row("Battery Controller Name", ["FC0500-40S-V2"]),
        row("Battery System Capacity (AH)", ["74Ah"]),
        row("Battery Module Quantity(pcs)", range(2, 8)),
        row("Battery System Capacity(kWh)", range(10, 16)),
        row("Battery System Voltage (Vdc)", range(100, 106)),
        row("Battery System Charge Upper Voltage (Vdc)", range(110, 116)),
        row("Battery System Discharge Lower Voltage (Vdc)", range(90, 96)),
    ]
    second = [
        row("Product Type", ["Force-H1-V2"]),
        row("Weight (kg)", range(80, 86)),
        row("Dimension(W*D*H, mm)", ["600*380\n*500"] * 6),
    ]
    for direction in ["Charge", "Discharge"]:
        for kind, value in [("Standard", 10), ("Normal", 20), ("Max.@15s", 30)]:
            first.append(row(f"Battery System {direction} Current (Amps, {kind})", [value]))
    return [first, second]


def test_configurations_preserve_native_energy_and_current_scope():
    rows = parse_h1_v2(tables(), revision=REVISION)
    assert len(rows) == 6
    assert [r["module_count"] for r in rows] == list(range(2, 8))
    assert rows[0]["energy_kwh_reported"] == 10
    assert rows[-1]["charge_normal_a"] == 20
    assert rows[0]["dimensions_wdh_mm"] == [600, 380, 500]
    assert rows[0]["discharge_peak_seconds"] == 15
    assert all("power_kw" not in r for r in rows)


@pytest.mark.parametrize(
    "case",
    [
        "revision",
        "model",
        "duplicate_row",
        "units",
        "columns",
        "order",
        "bounds",
        "component",
        "dimension",
        "page_count",
    ],
)
def test_reject_unreviewed_layout_or_identity(case):
    data = deepcopy(tables())
    revision = REVISION
    if case == "revision":
        revision = "older Force-H1 2.3"
    elif case == "model":
        data[0][0][-1] = "Force-H1"
    elif case == "duplicate_row":
        data[0].append(data[0][6])
    elif case == "units":
        data[0][6][0] = "Battery System Capacity(MWh)"
    elif case == "columns":
        data[0][6].pop()
    elif case == "order":
        data[0][5][-1] = "6"
    elif case == "bounds":
        data[0][9][2] = "120"
    elif case == "component":
        data[0][2][-1] = "FH9637M"
    elif case == "dimension":
        data[1][-1][2] = "600*380"
    elif case == "page_count":
        data.append(data[1])
    with pytest.raises(ValueError):
        parse_h1_v2(data, revision=revision)
