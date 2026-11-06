"""Synthetic boundary cases; fixture numbers are not OEM specifications."""

from copy import deepcopy

import pytest

from energy_data_retrieval.bess_oem_catalogue.solarmd import LABELS, MODELS, parse_ss70xx


def table():
    rows = [[label] for label in LABELS]
    for i, model in enumerate(MODELS):
        values = [
            model,
            "100 kWh",
            "40 kW",
            "400V",
            "300V - 500V",
            "CANBUS / RS485 / Ethernet",
            str(i + 5),
            "CB51x_HV-H8-R1",
            "600 kg",
            "400mm x 700mm x 1900mm",
        ]
        for row, value in zip(rows, values, strict=True):
            row.append(value)
    return rows


def test_preserves_native_ratings_and_boundaries():
    result = parse_ss70xx(table(), edition="2025-07 URL edition")
    assert len(result) == 13
    assert result[0]["module_count"] == 5
    assert result[-1]["module_count"] == 17
    assert result[0]["energy_kwh"] == 100
    assert result[0]["nominal_power_kw"] == 40
    assert result[0]["dimensions_wdh_mm"] == [400, 700, 1900]
    assert "duration_hours" not in result[0]
    assert "round_trip_efficiency_pct" not in result[0]


@pytest.mark.parametrize(
    "row,column,value",
    [
        (0, 2, MODELS[0]),
        (0, 1, "SS7008"),
        (1, 1, "100 kW"),
        (2, 1, "40 kVA"),
        (3, 1, "NaNV"),
        (4, 1, "500V - 300V"),
        (6, 1, "6"),
        (8, 1, "0 kg"),
        (9, 0, "Dimensions H x W x D"),
        (5, 1, None),
        (7, 1, "CB99"),
    ],
)
def test_rejects_shifted_identity_units_and_invalid_values(row, column, value):
    data = deepcopy(table())
    data[row][column] = value
    with pytest.raises(ValueError):
        parse_ss70xx(data, edition="2025-07 URL edition")


def test_requires_reviewed_edition_and_complete_table():
    with pytest.raises(ValueError):
        parse_ss70xx(table(), edition="2026-07")
    with pytest.raises(ValueError):
        parse_ss70xx(table()[:-1], edition="2025-07 URL edition")
    data = table()
    data[2].pop()
    with pytest.raises(ValueError):
        parse_ss70xx(data, edition="2025-07 URL edition")
