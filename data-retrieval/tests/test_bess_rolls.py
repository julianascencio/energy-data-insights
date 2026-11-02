"""Synthetic model, units and rate-condition tests; no OEM document fixtures."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.rolls import parse_rolls_flooded_html

URL = "https://rollsbattery.com/battery/synthetic/"


def sample():
    values = {
        "Series": "FLA SERIES 4000",
        "Volts": "6",
        "Cells": "3",
        "Charge Voltage Range": "2.45-2.5 V/cell @ 25°C",
        "Weight": "40 kg",
        "Length": "300 mm",
        "Width": "180 mm",
        "Height Incl. Term.": "400 mm",
        "Maximum Charge Current": "60 A",
    }
    rows = "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in values.items())
    return (
        "<table><tr><td>FLOODED DEEP CYCLE BATTERY</td>"
        '<td class="battery-title-model">SYNTHETIC</td></tr>'
        + rows
        + "<tr><th>@ 100 Hour Rate</th><td>400 AH</td><td>4 A</td></tr>"
        "<tr><th>@ 20 Hour Rate</th><td>300 AH</td><td>15 A</td></tr>"
        "</table>Rev.#1 | January 2026"
    ).encode()


def parse(content):
    return parse_rolls_flooded_html(content, source_url=URL, expected_model="SYNTHETIC")


def test_optional_charge_fields_and_rates_remain_separate():
    r = parse(sample())
    assert r["maximum_charge_current_a"] == 60
    assert r["recommended_charge_current_a"] is None
    assert [(d["hours"], d["capacity_ah"]) for d in r["discharge_rates"]] == [(100, 400), (20, 300)]
    assert "energy_capacity_mwh" not in r
    assert r["length_mm"] == 300


@pytest.mark.parametrize(
    "old,new",
    [
        (b"SYNTHETIC", b"OTHER"),
        (b"300 mm", b"300 cm"),
        (b"400 AH", b"400 A"),
        (b"@ 20 Hour Rate", b"@ 100 Hour Rate"),
        (b"Rev.#1", b"edition unknown"),
        (b"FLOODED DEEP CYCLE BATTERY", b"LITHIUM BATTERY"),
    ],
)
def test_changed_identity_units_or_layout_fail(old, new):
    with pytest.raises(ValueError):
        parse(sample().replace(old, new))


def test_duplicate_voltage_fails():
    with pytest.raises(ValueError, match="Duplicate label"):
        parse(sample().replace(b"</table>", b"<tr><th>Volts</th><td>12</td></tr></table>"))
