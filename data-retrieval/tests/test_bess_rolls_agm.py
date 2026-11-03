"""Synthetic exact-model tests; no copyrighted table fixture."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.rolls_agm import parse_rolls_agm_text

MODEL = "S12-TESTAGM-RE"
URL = "https://www.rollsbattery.com/battery/s12-testagm-re/"
TEXT = """# AGM VRLA DEEP CYCLE BATTERY
# S12-TESTAGM-RE
Series | VRLA AGM-S | Warranty | See terms
Volts | 12 | Design | test
Cells | 6
Terminal Type | M8
Charge Voltage Range | 2.45 V/cell @ 25°C
Float Voltage Range | 2.3 V/cell @ 25°C
Recommended Charge Current | 20 A
Maximum Charge Current | 30 A
Internal Resistance | 4 mΩ
@ 100 Hour Rate | 120 AH | 1.2 A
@ 20 Hour Rate | 100 AH | 5 A
@ 10 Hour Rate | 90 AH | 9 A
@ 5 Hour Rate | 80 AH |
Weight | 30 kg | 66 lbs
Length | 300 mm | 11.81"
Width | 170 mm | 6.69"
Height Incl. Term. | 220 mm | 8.66"
Rev.#1 | January 2025
"""


def parse(text=TEXT, url=URL):
    return parse_rolls_agm_text(text.encode(), source_url=url, expected_model=MODEL)


def test_boundaries_and_missing_current():
    row = parse()
    assert row["discharge_rates"][-1]["current_a"] is None
    assert row["reported_fields"]["Charge Voltage Range"] == ["2.45 V/cell @ 25°C"]
    assert row["numeric"]["Weight"] == 30
    assert "source_sha256" not in row
    assert len(row["extracted_text_sha256"]) == 64
    assert "energy_capacity_mwh" not in row


def test_inconsistent_rate_is_preserved_for_review():
    row = parse(TEXT.replace("120 AH | 1.2 A", "120 AH | 1.5 A"))
    assert row["rate_conflicts"] == [{"hours": 100, "capacity_ah": 120, "current_a": 1.5}]


@pytest.mark.parametrize(
    "old,new",
    [
        ("# S12-TESTAGM-RE", "# OTHER"),
        ("Series | VRLA AGM-S", "Series | VRLA GEL"),
        ("Weight | 30 kg", "Weight | 30 lb"),
        ("@ 20 Hour Rate | 100 AH | 5 A", "@ 20 Hour Rate | 100 WH | 5 A"),
        ("Rev.#1 | January 2025", ""),
        ("@ 5 Hour Rate | 80 AH |", "@ 10 Hour Rate | 80 AH |"),
        ("Cells | 6", "Cells | 6\nCells | 6"),
    ],
)
def test_rejects_drift(old, new):
    with pytest.raises(ValueError):
        parse(TEXT.replace(old, new))


def test_url_identity_and_host():
    for url in [URL.replace("rollsbattery.com", "example.org"), URL.replace("testagm", "other")]:
        with pytest.raises(ValueError):
            parse(url=url)
