"""Synthetic layout fragments, not redistributed OEM documents."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.dyness import parse_stack100_manual


def manual() -> str:
    """Make structurally representative tables with deliberately synthetic ratings."""
    pages = ["V2 2025.03.07\nTable 2-1 Parameters of the STACK100 system"]
    for group in [range(3, 8), range(8, 13), range(13, 16)]:
        pages.append(
            "STACK100 User Manual\nModel "
            + " ".join(f"100-{n}s" for n in group)
            + "\nModule Voltage/Capacity 51.2V/100Ah\nSystem Modules Serial Number "
            + " ".join(str(n) for n in group)
            + "\nSystem Energy Range "
            + " ".join(f"{n + 0.1}kWh" for n in group)
            + "\nOperating Voltage "
            + " ".join(f"{n * 10}-{n * 20}V" for n in group)
        )
    return "\f".join(
        p.replace("\nSystem", "\n  System").replace("\nOperating", "\n  Operating") for p in pages
    )


def test_preserves_exact_columns_rounding_units_and_unknown_basis():
    rows = parse_stack100_manual(manual())
    assert len(rows) == 13
    assert rows[0]["model"] == "STACK100-3s"
    assert rows[0]["energy_kwh"] == 3.1  # Not module-count times a family rating.
    assert rows[-1]["model"] == "STACK100-15s"
    assert rows[-1]["dc_voltage_max_v"] == 300
    assert rows[-1]["locator"] == "Printed page 9, Table 2-1, STACK100-15s column"
    assert all(r["review_required"] and r["energy_basis"] == "unspecified" for r in rows)
    assert all("power_kw" not in r and "usable_energy_kwh" not in r for r in rows)


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("V2 2025.03.07", "V3 2026.05.20"),
        ("100-4s", "100-3s"),
        ("100-4s", "100-16s"),
        ("3 4 5 6 7", "3 5 4 6 7"),
        ("4.1kWh ", ""),
        ("3.1kWh", "3.1MWh"),
        ("3.1kWh", "approximately 3.1kWh"),
        ("30-60V", "60-30V"),
        ("System Energy Range", "Nominal Energy"),
    ],
)
def test_rejects_changed_revision_corrupt_identity_or_changed_table(before, after):
    with pytest.raises(ValueError):
        parse_stack100_manual(manual().replace(before, after, 1))


def test_rejects_partial_and_duplicated_pages():
    text = manual()
    with pytest.raises(ValueError, match="exactly three"):
        parse_stack100_manual(text.rsplit("\f", 1)[0])
    with pytest.raises(ValueError, match="exactly three"):
        parse_stack100_manual(text + "\f" + text.rsplit("\f", 1)[1])
