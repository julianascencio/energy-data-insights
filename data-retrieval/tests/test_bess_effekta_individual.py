"""Synthetic layouts, not redistributed manufacturer sheets."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.effekta_individual import (
    SOURCE_URLS,
    parse_individual_sheet,
)

SHEET = """BT12-EXAMPLE (12V / 20Ah)
AGM Specifications
Nominal Voltage    12V
Nominal Capacity   20Ah
Dimensions Length   180 ± 2mm
Width    77 ± 1.5mm
Height max.    167 ± 2mm
Height of the terminals    165 ± 2mm
Approx. Weight    5,4kg
Max. charging current    6 A
Max. Discharge Current    200 A (5 s)
"""


def parse(text=SHEET, model="BT12-EXAMPLE"):
    return parse_individual_sheet(
        text.encode(), source_url=sorted(SOURCE_URLS)[0], expected_model=model
    )


def test_separate_capacity_current_mass_and_heights():
    row = parse()
    assert row["nominal_monobloc_ah"] == 20
    assert row["approximate_mass_kg"] == 5.4
    assert row["dimensions"]["width"]["tolerance_mm"] == 1.5
    assert row["dimensions"]["Height of the terminals"]["value_mm"] == 165
    assert row["peak_discharge"] == {"ampere": 200, "seconds": 5}
    assert "energy_capacity_mwh" not in row
    assert "power_capacity_mw" not in row
    assert "cell_capacity_ah" not in row


def test_short_circuit_is_not_peak_and_c_rate_is_not_amperes():
    row = parse(
        SHEET.replace("6 A", "0,3C").replace(
            "Max. Discharge Current    200 A (5 s)", "Short-circuit current    1300 A"
        )
    )
    assert row["maximum_charge"] == {"value": 0.3, "unit": "C"}
    assert row["peak_discharge"] is None
    assert row["short_circuit_ampere"] == 1300


def test_ignores_later_page_heading_but_preserves_source_checksum():
    row = parse(SHEET + "\fBT12-OTHER (12V / 20Ah)")
    assert row["model"] == "BT12-EXAMPLE"
    assert row["extracted_text_sha256"] != parse()["extracted_text_sha256"]


@pytest.mark.parametrize(
    "text",
    [
        SHEET.replace("BT12-EXAMPLE", "BT12-EXAMPLER"),
        SHEET + "Nominal Voltage    12V\n",
        SHEET.replace("20Ah", "20Wh"),
        SHEET.replace("6 A", "6 kA"),
        SHEET.replace("5 s", "5 min"),
        SHEET.replace("12V", "0V"),
        SHEET.replace("AGM", "unspecified"),
        SHEET + "Short-circuit current    1300 A\n",
    ],
)
def test_changed_or_ambiguous_input_fails_closed(text):
    with pytest.raises(ValueError):
        parse(text)


def test_rejects_unreviewed_source():
    with pytest.raises(ValueError):
        parse_individual_sheet(
            SHEET.encode(), source_url="https://example.org", expected_model="BT12-EXAMPLE"
        )
