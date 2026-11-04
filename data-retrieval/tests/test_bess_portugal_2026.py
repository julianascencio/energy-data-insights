"""Synthetic final-table regression cases; no publisher content fixtures."""

import pytest

from energy_data_retrieval.bess_catalogue.portugal_grants import parse_2026_grants


def fixture_text():
    header = (
        "após sorteio de desempate 01/C21-i18/2026 Totalizador "
        "Capacidade de (MWh) [GGS] 80 250 000,00 EUR\n"
    )
    yes = "Elegível com proposta favorável de financiamento"
    no = "Elegível sem proposta de financiamento"
    rows = [
        f"{i} Synthetic Entity 123456789 100 000 000,00 EUR "
        f"{'80 250 000,00' if i == 1 else '0,00'} EUR 1,250 0,00 5 20 3 28 1º "
        f"{yes if i == 1 else no}"
        for i in range(1, 46)
    ]
    return header + "\n".join(rows)


def test_preserves_decimal_and_unfunded_without_power_inference():
    rows = parse_2026_grants(fixture_text().encode())
    assert len(rows) == 45
    assert rows[0]["storage_energy_mwh"] == "1.250"
    assert rows[0]["ggs_unit"] is None
    assert rows[1]["favorable_funding_proposal"] is False
    assert rows[1]["proposed_funding_eur"] == "0.00"
    assert "power_capacity_mw" not in rows[0]
    assert "Synthetic Entity" not in str(rows)


@pytest.mark.parametrize(
    "before,after",
    [
        ("01/C21-i18/2026", "01/C21-i08/2025"),
        ("45 Synthetic", "44 Synthetic"),
        ("1,250", "0,000"),
        ("1,250", "1.250"),
        ("80 250 000,00 EUR 1,250", "80 249 999,99 EUR 1,250"),
        ("0,00 EUR 1,250", "1,00 EUR 1,250"),
    ],
)
def test_rejects_unreviewed_or_inconsistent_table(before, after):
    with pytest.raises(ValueError):
        parse_2026_grants(fixture_text().replace(before, after).encode())


def test_missing_row_fails():
    with pytest.raises(ValueError):
        parse_2026_grants("\n".join(fixture_text().splitlines()[:-1]).encode())
