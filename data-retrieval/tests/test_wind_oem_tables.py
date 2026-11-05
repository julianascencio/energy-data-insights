"""OEM boundary tests use factual transcriptions and synthetic original bytes."""

import copy
import hashlib
import json
from pathlib import Path

import pytest

from energy_data_retrieval.wind_catalogue.oem_tables import stage_tables

ORIGINAL = b"Synthetic checksum fixture; actual factual columns separately attributed"
REVIEW = json.loads((Path(__file__).parent / "fixtures/wind_oem_tables.json").read_text())
NOW = "2026-11-05T20:45:00Z"


def run(review=None, existing=None):
    return stage_tables(review or copy.deepcopy(REVIEW), ORIGINAL, existing or [], now=NOW)


def test_boundary_specific_units_and_options():
    rows, _ = run()
    row = rows[0]
    assert row["rated_power_kw"] == 1500
    assert row["rotor_diameter_m"] == 77
    raw = json.loads(row["extensions_json"])["oem_table_observations"][0]["values"]
    assert raw["generator_power_kw"] == 1550
    assert raw["converter_power_kva_grid_turbine"] == [365, 695]
    assert raw["generator_rated_speed_rpm"] == 1800
    assert raw["hub_height_range_m"] == [65, 160]
    for field in ["hub_height_m", "cut_out_m_s", "rotor_speed_max_rpm", "frequency_hz"]:
        assert row.get(field) is None
    assert len(rows) == 2  # Option ranges do not multiply records.


def test_existing_model_requires_revision_review():
    rows, ledger = run(existing=[dict(manufacturer="Windey", model="WD77-1500")])
    assert len(rows) == 1
    assert ledger[0]["decision"] == "existing_revision_review"


@pytest.mark.parametrize(
    "case", ["checksum", "missing", "reordered", "duplicate", "range", "nan", "boolean"]
)
def test_reject_unreviewable_input(case):
    review = copy.deepcopy(REVIEW)
    table = review["tables"][0]
    raw = table["columns"][0]
    if case == "checksum":
        review["sha256"] = hashlib.sha256(b"other").hexdigest()
    elif case == "missing":
        table["columns"].pop()
    elif case == "reordered":
        table["columns"].reverse()
    elif case == "duplicate":
        table["columns"][1]["model"] = raw["model"]
        table["expected_models"][1] = raw["model"]
    elif case == "range":
        raw["hub_height_range_m"] = [160, 65]
    elif case == "nan":
        raw["rated_power_kw"] = float("nan")
    else:
        raw["rated_power_kw"] = True
    with pytest.raises(ValueError):
        run(review)


def test_middle_tables_preserve_column_specific_frequency_and_blade_values():
    review = json.loads(
        (Path(__file__).parent / "fixtures/wind_oem_middle_tables.json").read_text()
    )
    rows, _ = run(review)
    by = {r["model"]: r for r in rows}
    first = json.loads(by["WD164-3600"]["extensions_json"])["oem_table_observations"][0]
    second = json.loads(by["WD172-3600"]["extensions_json"])["oem_table_observations"][0]
    assert first["values"]["converter_frequency_range_hz"] == [47.5, 51.5]
    assert second["values"]["converter_frequency_range_hz"] == [47.5, 52.5]
    assert by["WD172-5500"]["blade_length_m"] == 80.5  # Printed, not inferred from rotor.
    assert by["WD172-5500"]["rated_power_kw"] == 5500
    assert by["WD172-5500"].get("frequency_hz") is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("generator_power_kw", -1),
        ("generator_rated_speed_rpm", True),
        ("converter_power_kva_grid_turbine", [695]),
        ("converter_current_a_grid_turbine", [352, float("nan")]),
        ("nacelle_dimensions_m", [11.4, 4.5]),
    ],
)
def test_component_quantity_boundary(field, value):
    review = copy.deepcopy(REVIEW)
    review["tables"][0]["columns"][0][field] = value
    with pytest.raises(ValueError, match="OEM component"):
        run(review)
