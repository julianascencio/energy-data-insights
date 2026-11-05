"""Synthetic rate, identity and unit tests; no source document fixture."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.tab_topzs import MODELS, parse_models


def sample():
    return "\n".join(
        [
            "Uf (V/cell) 1,80 1,80 1,85 Capacity C10 C20 C100",
            "Ri Isc L W H Dry Wet Type Ah Ah Ah* mΩ A mm mm mm kg kg",
            "20 °C at C10 (1,80 V/cell) and 25 °C at C100 (1,85 V/cell)",
            *(m + " 265 289 345 0,56 3721 198 83 472 12,4 18,4" for m in MODELS),
        ]
    )


def test_preserve_rates_and_amperes():
    row = parse_models(sample())[0]
    assert row["values"][:5] == [265, 289, 345, 0.56, 3721]
    assert parse_models(sample())[5]["model"] == "6 TOPzS750"
    assert set(row) == {"model", "values"}


@pytest.mark.parametrize(
    "old,new",
    [
        ("mΩ A", "mΩ kA"),
        ("C20", "C5"),
        ("1,85", "1,80"),
        ("25 °C", "20 °C"),
        ("Dry Wet", "Wet Dry"),
        ("12,4 18,4", "18,4 12,4"),
        ("3721", ""),
        ("8 TOPzS 1000", "7 TOPzS 875"),
    ],
)
def test_reject_changed_table(old, new):
    with pytest.raises(ValueError):
        parse_models(sample().replace(old, new))
