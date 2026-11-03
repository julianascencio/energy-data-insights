"""Synthetic controls for CEB section identity, units and missing rows."""

import pytest

from energy_data_retrieval.bess_catalogue.ceb import parse_ceb_battery_table

SYNTHETIC = b"""Date : 26 May 2022
\fBattery Energy Storage System Project
18 MW / 9 MWh
Location  Capacity
Amaury Substation  2MW, 1MWh
Henrietta Substation  2MW, 1MWh
Wooton Substation  4MW, 2MWh
Anahita Substation  4MW, 2MWh
La Tour Koenig Substation  2MW, 1MWh
Jin Fei Substation  4 MW, 2 MWh
20 MW / 10 MWh
Location  Capacity
Amaury  20 MW, 10 MWh
"""


def test_separate_expansion_and_unknown_lifecycle():
    rows = parse_ceb_battery_table(SYNTHETIC)
    assert len(rows) == 7
    assert sum(r["power_mw"] for r in rows[:6]) == 18
    assert rows[0]["source_name"] == "Amaury Substation"
    assert rows[-1]["source_name"] == "Amaury"
    assert rows[-1]["section"] == "separate_expansion"
    assert {r["status"] for r in rows} == {"unknown"}
    assert {r["source_page"] for r in rows} == {2}


@pytest.mark.parametrize(
    "old,new",
    [
        (b"26 May 2022", b"26 May 2023"),
        (b"18 MW / 9 MWh", b"18 MW / 9 MW"),
        (b"18 MW / 9 MWh", b"20 MW / 9 MWh"),
        (b"2MW, 1MWh", b"0MW, 1MWh"),
        (b"Henrietta Substation", b"Amaury Substation"),
        (b"Jin Fei Substation  4 MW, 2 MWh\n", b""),
        (b"Amaury  20 MW", b"Other  20 MW"),
    ],
)
def test_changed_table_fails_closed(old, new):
    with pytest.raises(ValueError):
        parse_ceb_battery_table(SYNTHETIC.replace(old, new))
