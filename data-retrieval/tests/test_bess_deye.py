"""Synthetic layout tests; no copyrighted source document is bundled."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.deye import parse_bos_g_pro

TABLE = """Synthetic cover\f
Battery Module Number BOS-G25-Pro BOS-G40-Pro BOS-G60-Pro BOS-G80-Pro
System Energy ( kWh ) 20 30 40 50
System Usable Energy (kWh ) 1
18 27 36 45
Rated DC Power ( kW ) 11 12 13 14
System Nominal Voltage ( V ) 200 300 400 500
90% DOD, 0.3C charge & discharge at 25°C
\fSynthetic components
"""


def test_preserves_independent_power_and_energy() -> None:
    rows = parse_bos_g_pro(TABLE)
    assert len(rows) == 4
    assert rows[2]["reported_rated_dc_power_kw"] == 13
    assert rows[2]["system_energy_kwh"] == 40
    assert rows[2]["usable_dc_energy_kwh"] == 36
    assert rows[2]["review_required"] is True


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("BOS-G40-Pro", "BOS-G25-Pro"),
        ("BOS-G40-Pro", "BOS-G40"),
        ("20 30 40 50", "20 30 40"),
        ("20 30 40 50", "20 30 40 50 60"),
        ("Rated DC Power ( kW )", "Rated DC Power ( kVA )"),
        ("18 27 36 45", "18 27 41 45"),
        ("90% DOD", ""),
        ("20 30 40 50", "20 30 0 50"),
    ],
)
def test_rejects_layout_units_and_conditions_drift(old: str, new: str) -> None:
    with pytest.raises(ValueError):
        parse_bos_g_pro(TABLE.replace(old, new))


def test_rejects_duplicate_data_row() -> None:
    with pytest.raises(ValueError, match="duplicate row"):
        parse_bos_g_pro(
            TABLE.replace("\fSynthetic components", "\nRated DC Power ( kW ) 1 2 3 4\f")
        )
