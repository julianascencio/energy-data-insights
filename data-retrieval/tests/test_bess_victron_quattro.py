"""Synthetic merged-column cases; no publisher document is bundled."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.victron import (
    QUATTRO_GROUPS,
    parse_quattro_230v,
)


def layout():
    lines = []
    for j in range(3):
        lines.append("".join((g[j] if j < len(g) else "").center(30) for g in QUATTRO_GROUPS))
    lines += [
        "Nominal Battery Voltage 12 V / 24 V / 48 V",
        "Output (1) Output voltage: 230 VAC",
        "Cont. output power at 25 °C (VA) (3) 3000 5000 8000 10000 15000",
        "Cont. output power at 25 °C (W) 2300 3900 6300 7900 11900",
        "Cont. output power at 40 °C (W) 2100 3600 5400 6400 9900",
        "Cont. output power at 65 °C (W) 1600 2900 3500 4400 6900",
        "Peak power (W) 5900 9900 15900 19900 24900",
        "Charge current house battery (A) (4) 119 / 69  219 / 119 / 69  199 / 109  139  199",
    ]
    return "\n".join(lines)


def test_grouped_models_use_watts_and_individual_charge_current():
    rows = parse_quattro_230v(layout())
    assert len(rows) == 9
    assert rows[0]["power_capacity_mw"] == 0.0023
    assert rows[0]["apparent_power_mva"] == 0.003
    assert rows[1]["maximum_charge_current_a_at_25c"] == 69
    assert rows[4]["model"] == "Quattro 48/5000/70-100/100"
    assert rows[4]["maximum_charge_current_a_at_25c"] == 69
    assert all(r["peak_duration_seconds"] is None for r in rows)
    assert all("energy_capacity_mwh" not in r for r in rows)


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("230 VAC", "120 VAC"),
        ("24/3000/70-50/50", "48/3000/35-50/50"),
        ("119 / 69  219", "119  219"),
        ("2300 3900 6300 7900 11900", "2300 3900 6300 7900"),
        ("2300 3900 6300 7900 11900", "2300 W 3900 6300 7900 11900"),
        ("2100 3600 5400 6400 9900", "2400 3600 5400 6400 9900"),
        ("119 / 69", "119 / 0"),
    ],
)
def test_changed_layout_or_units_fail_closed(before, after):
    with pytest.raises(ValueError):
        parse_quattro_230v(layout().replace(before, after))


def test_reordered_columns_are_not_silently_assigned():
    text = layout().replace("48/10000/140-100/100", "TEMP")
    text = text.replace("48/15000/200-100/100", "48/10000/140-100/100")
    text = text.replace("TEMP", "48/15000/200-100/100")
    with pytest.raises(ValueError, match="Reordered"):
        parse_quattro_230v(text)


def test_duplicate_pages_require_manual_review():
    with pytest.raises(ValueError, match="one Quattro"):
        parse_quattro_230v(layout() + "\f" + layout())
