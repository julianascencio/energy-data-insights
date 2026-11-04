"""Synthetic final-grant table tests; no original report data."""

from decimal import Decimal

import pytest

from energy_data_retrieval.bess_catalogue.portugal_grants import parse_final_grants


def fixture():
    pages = ["Versão: 1.1\n08 de abril de 2025"] + [""] * 25
    rows = [f"{i}  {100 + i}  Synthetic entity  1,00 €  {i},00 €" for i in range(1, 42)]
    pages += [
        "Tabela 1 deste Relatório Final Lista definitiva\n" + "\n".join(rows[:33]),
        "\n".join(rows[33:]) + "\nTabela 2 deste Relatório Final\n42  999  Excluded  9,00 €",
    ]
    return "\f".join(pages).encode()


def test_final_partition_and_scope():
    rows = parse_final_grants(fixture())
    assert len(rows) == 41
    assert rows[-1]["application_id"] == "141"
    assert all(Decimal(r["cumulative_arithmetic_difference_eur"]) == 0 for r in rows)
    assert all("status" not in r and "power_capacity_mw" not in r for r in rows)


def test_conflicting_cumulative_not_repaired():
    rows = parse_final_grants(fixture().replace(b"18,00", b"18,50"))
    assert rows[17]["reported_cumulative_eur"] == "18.50"
    assert rows[17]["cumulative_arithmetic_difference_eur"] == "0.50"
    assert rows[18]["cumulative_arithmetic_difference_eur"] == "-0.50"


@pytest.mark.parametrize(
    "old,new",
    [
        (b"Vers\xc3\xa3o: 1.1", b"Versao: 2"),
        (b"41  141", b"40  141"),
        (b"41  141", b"41  140"),
        (b"Tabela 1 deste Relat", b"Tabela preliminar Relat"),
        (b"1,00", b"1.00"),
    ],
)
def test_changed_version_or_identity_fails(old, new):
    with pytest.raises(ValueError):
        parse_final_grants(fixture().replace(old, new))
