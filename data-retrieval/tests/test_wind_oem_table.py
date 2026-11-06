"""Synthetic offline numeric cells; not manufacturer performance data."""

import copy

import pytest

from energy_data_retrieval.wind_catalogue.oem_table import (
    NUMERIC_CELLS,
    normalize_oem_partition,
)


@pytest.fixture
def table():
    values = [5, 100, 7854, 3, 10, 25, 20, -30, 40]
    return {
        "model": "Synthetic-X",
        "source_id": "synthetic",
        "locator": "Synthetic technical table",
        "cells": {
            field: {"value": value, "unit": unit}
            for (field, (unit, _)), value in zip(NUMERIC_CELLS.items(), values, strict=True)
        },
    }


def run(table):
    return normalize_oem_partition([table], expected_models=["Synthetic-X"])[0]


def test_units_missing_and_zero_are_distinct(table):
    table["cells"]["rated_wind_speed_m_s"]["value"] = None
    table["cells"]["temperature_min_c"]["value"] = 0
    result = run(table)
    assert result["values"]["rated_power_kw"] == 5000
    assert result["values"]["rated_wind_speed_m_s"] is None
    assert result["values"]["temperature_min_c"] == 0
    assert result["values"]["swept_area_m2"] == 7854
    assert result["provenance"]["rated_power_kw"]["original_value"] == 5


def test_printed_errors_are_retained_not_corrected(table):
    table["cells"]["swept_area_m2"]["value"] = 9000
    table["cells"]["cut_out_m_s"]["value"] = 3
    original = copy.deepcopy(table)
    result = run(table)
    assert table == original
    assert result["values"]["swept_area_m2"] is None
    assert result["values"]["cut_out_m_s"] is None
    assert result["conflicts"]["swept_area_m2"]["original_value"] == 9000
    assert result["conflicts"]["cut_out_m_s"]["original_value"] == 3


def test_unknown_diameter_does_not_create_a_geometry_check(table):
    table["cells"]["rotor_diameter_m"]["value"] = None
    assert run(table)["conflicts"] == {}


@pytest.mark.parametrize("fault", ["unit", "missing", "nan", "negative", "boolean", "reversed"])
def test_malformed_cells_fail_before_publication(table, fault):
    if fault == "unit":
        table["cells"]["rated_power_kw"]["unit"] = "kW"
    elif fault == "missing":
        del table["cells"]["swept_area_m2"]
    elif fault == "reversed":
        table["cells"]["temperature_min_c"]["value"] = 41
    else:
        table["cells"]["rated_power_kw"]["value"] = {
            "nan": float("nan"),
            "negative": -1,
            "boolean": True,
        }[fault]
    with pytest.raises(ValueError):
        run(table)


def test_incomplete_or_duplicate_partition_is_not_complete(table):
    for rows, expected in [
        ([table], ["Other"]),
        ([table, table], ["Synthetic-X"]),
        ([table], ["Synthetic-X", "Synthetic-X"]),
    ]:
        with pytest.raises(ValueError, match="partition"):
            normalize_oem_partition(rows, expected_models=expected)
