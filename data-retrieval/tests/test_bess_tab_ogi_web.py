"""Synthetic live-table boundaries, without source-document fixtures."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.tab_ogi_web import (
    EXTRA_MODELS,
    MODELS,
    parse_table_cells,
)


def sample():
    cells = [
        "UF_V/Cell",
        "1,80",
        "1,75",
        "1,75",
        "1,70",
        "1,65",
        "1,65",
        "1,60",
        "EN/IEC 60896-11",
        "Dimensions",
        "Weight",
        "Discharging time  (h)",
        "10",
        "5",
        "3",
        "1",
        "1/2",
        "1/6",
        "1/12",
        "Ri",
        "Isc",
        "L",
        "W",
        "H",
        "with acid",
        "dry",
        "Type",
    ] + ["Ah"] * 7
    cells += ["mΩ", "kA", "mm", "mm", "mm", "kg", "kg"]
    for model in MODELS + EXTRA_MODELS:
        cells += [model, "100", "90", "80", "70", "60", "50"]
        cells += ["" if model in EXTRA_MODELS[2:] else "40"]
        cells += ["0.5", "4.5", "200", "100", "400", "30", "20"]
    return cells


def test_blank_rate_does_not_shift_resistance_or_mass():
    row = parse_table_cells(sample())[-1]
    assert row["values"][6] is None
    assert row["values"][7:9] == [0.5, 4.5]
    assert row["values"][-2:] == [30, 20]
    assert set(row) == {"model", "values"}


@pytest.mark.parametrize(
    "old,new",
    [
        ("kA", "A"),
        ("mΩ", "Ω"),
        ("dry", "wet"),
        ("1/12", "1/10"),
        ("1,80", "1,85"),
        ("L", "W"),
        ("90", "110"),
        ("0.5", ""),
        ("2V 36 OGi 900", "2V 30 OGi 750"),
    ],
)
def test_unreviewed_units_values_or_identity_fail(old, new):
    with pytest.raises(ValueError):
        parse_table_cells([new if c == old else c for c in sample()])


def test_missing_blank_and_reversed_mass_fail():
    cells = sample()
    cells.remove("")
    with pytest.raises(ValueError):
        parse_table_cells(cells)
    cells = sample()
    cells[:2] = ["dry", "with acid"]
    with pytest.raises(ValueError):
        parse_table_cells(cells)
