"""Synthetic layout tests; no copyrighted datasheet fixture is bundled."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.victron import parse_multiplus_new_230v

SYNTHETIC = """MultiPlus-II Inverter/Charger, new models
MultiPlus-II 230V 12/4k/160-32 48/4k5/55-32 48/6k5/100-50 48/10k/150-100
Cont. output power at 25 °C 3,5 kW 4 kW 6 kW 10kW
Cont. output power at 40 °C 3 kW 3,5 kW 5kW 9kW
Cont. output power at 65 °C 2 kW 3 kW 4kW 6kW
Max apparent feed-in power 3,5 kW 4 kW 6 kW 10kW
Peak power 6 kW/2s 7 kW/1min 11 kW/1min 15kW/2min
Max. battery charge current at 25 °C 160 A 55 A 100 A 150 A
Max. battery charge current at 40 °C 150 A 50 A 95 A 140 A
"""


def test_active_power_units_and_overload_times_remain_distinct():
    rows = parse_multiplus_new_230v(SYNTHETIC)
    assert len(rows) == 4
    assert rows[0]["power_capacity_mw"] == 0.0035
    assert [r["peak_duration_seconds"] for r in rows] == [2, 60, 60, 120]
    assert all(r["apparent_power_mva"] is None for r in rows)
    assert "dc_voltage_nominal_v" not in rows[0]
    assert rows[-1]["model"] == "MultiPlus-II 48/10k/150-100"


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("12/4k/160-32 48/4k5/55-32", "48/4k5/55-32 12/4k/160-32"),
        ("48/6k5/100-50", "48/4k5/55-32"),
        ("3,5 kW 4 kW 6 kW 10kW", "3,5 kVA 4 kVA 6 kVA 10kVA"),
        ("6 kW/2s", "6 kW"),
        ("6 kW/2s", "6 kW/0s"),
        ("160 A 55 A 100 A 150 A", "160 A 55 A 150 A"),
        ("3 kW 3,5 kW 5kW 9kW", "4 kW 3,5 kW 5kW 9kW"),
    ],
)
def test_changed_identity_units_incomplete_columns_and_invalid_ratings_fail(before, after):
    with pytest.raises(ValueError):
        parse_multiplus_new_230v(SYNTHETIC.replace(before, after))


def test_duplicated_rows_require_review():
    with pytest.raises(ValueError, match="duplicated"):
        parse_multiplus_new_230v(SYNTHETIC + "Peak power 6kW/2s 7kW/1min 11kW/1min 15kW/2min\n")


def test_poppler_page_break_and_sidebar_do_not_corrupt_table_columns():
    lines = SYNTHETIC.splitlines()
    # Synthetic side captions occupy a separate left column on the table page.
    table = "\n".join("side caption".ljust(24) + line for line in lines[1:])
    extracted = lines[0] + "\n\f" + table
    assert parse_multiplus_new_230v(extracted) == parse_multiplus_new_230v(SYNTHETIC)
