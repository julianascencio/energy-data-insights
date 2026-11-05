"""Synthetic table boundary tests; no copyrighted document fixture."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.tab_ups import MODELS, parse_models


def sample():
    return "\n".join(
        [
            "Uf (V/cell) 1,80 1,75 1,70 1,65 1,63 1,60",
            "Discharging time (min) 60 30 15 10 5",
            "Dry Wet",
            "Type C10 (Ah) W/cell W/cell W/cell W/cell W/cell mΩ (kA) mm mm mm kg kg",
            *(m + " 40 42 64 92 120 181 16,8 0,73 272 205 375 23,4 35,4" for m in MODELS),
        ]
    )


def test_separate_capacity_and_per_cell_power():
    r = parse_models(sample())[0]
    assert r["values"][:3] == [40, 42, 64]
    assert r["values"][7] == 0.73
    assert set(r) == {"model", "values"}


@pytest.mark.parametrize(
    "old,new",
    [
        ("W/cell", "W"),
        ("C10 (Ah)", "C20 (Ah)"),
        ("1,63", "1,65"),
        ("60 30", "60 20"),
        ("Dry Wet", "Wet Dry"),
        ("0,73", ""),
        ("23,4 35,4", "35,4 23,4"),
        ("2V 36 UPS 3600", "2V 30 UPS 3000"),
    ],
)
def test_fail_closed(old, new):
    with pytest.raises(ValueError):
        parse_models(sample().replace(old, new))
