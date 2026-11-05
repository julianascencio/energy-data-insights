"""Exact DUID and power-basis guards for AEMO null-field enrichment."""

import copy
import json
import math

import pytest

from energy_data_retrieval.pv_catalogue.australia import (
    _HEADERS,
    stage_aemo_exact_enrichment,
)


def inputs():
    header = [None] * 26
    for i, label in (
        _HEADERS
        | {
            3: "Site Owner",
            6: "Max Site Capacity (AC)",
            7: "Gen Info Unit ID",
            10: "Technology Detail",
        }
    ).items():
        header[i] = label
    row = [None] * 26
    for i, value in {
        0: 7,
        1: "Example Solar",
        3: "Example Pty Ltd",
        6: 80,
        7: 701,
        9: "Solar PV",
        12: "EXAMPLE1",
        17: 120,
        18: 100,
        20: "In Service",
    }.items():
        row[i] = value
    rows = [(), (), (), tuple(header), tuple(row)]
    old = {
        "record_id": "one",
        "entity_type": "projects",
        "country_code": "AUS",
        "external_ids_json": '{"aemo_duid":"EXAMPLE1","aemo_survey_id":7}',
    }
    decisions = [
        {
            "record_id": "one",
            "duid": "EXAMPLE1",
            "survey_row": 5,
            "survey_id": 7,
            "fields": ["capacity_ac_mw", "capacity_dc_mw", "owners"],
        }
    ]
    return rows, decisions, [old]


def stage(rows, decisions, old):
    return stage_aemo_exact_enrichment(
        rows, decisions, old, source_id="source", survey_date="2026-10-30"
    )


def test_nameplate_not_dispatch_and_no_source_mutation():
    rows, decisions, old = inputs()
    saved = copy.deepcopy(old)
    result, review = stage(rows, decisions, old)
    assert result[0]["capacity_ac_mw"] == 100
    assert result[0]["capacity_dc_mw"] == 120
    assert result[0]["owners"] == ["Example Pty Ltd"]
    assert "commissioning_date" not in result[0]
    assert (
        json.loads(result[0]["extensions_json"])["aemo_generation_information"][
            "max_site_dispatch_ac_mw"
        ]
        == 80
    )
    assert review[0]["conflicts"] == {}
    assert old == saved


def test_existing_values_context_and_conflicts_preserved():
    rows, decisions, old = inputs()
    old[0].update(
        capacity_ac_mw=90,
        capacity_dc_mw=120,
        owners=["Earlier owner"],
        extensions_json='{"prior":true}',
    )
    result, review = stage(rows, decisions, old)
    assert result == []
    assert set(review[0]["conflicts"]) == {"capacity_ac_mw", "owners"}
    assert old[0]["extensions_json"] == '{"prior":true}'


@pytest.mark.parametrize(
    "change",
    [
        "name_only",
        "two_phases",
        "foreign",
        "survey_id",
        "row",
        "technology",
        "other_unit",
        "duplicate_duid",
        "other_canonical",
        "bad_field",
        "bad_header",
    ],
)
def test_unresolved_identity_or_schema_rejected(change):
    rows, decisions, old = inputs()
    row = list(rows[4])
    if change == "name_only":
        old[0]["external_ids_json"] = "{}"
        old[0]["name"] = row[1]
    elif change == "two_phases":
        old[0]["phases_json"] = '[{"Phase Name":"EXAMPLE1"},{"Phase Name":"OTHER"}]'
    elif change == "foreign":
        old[0]["country_code"] = "USA"
    elif change == "survey_id":
        decisions[0]["survey_id"] = 8
    elif change == "row":
        decisions[0]["survey_row"] = 6
    elif change == "technology":
        row[9] = "Solar Thermal"
    elif change == "other_unit":
        other = row.copy()
        other[9], other[12] = "Battery Storage", "BATT1"
        rows.append(tuple(other))
    elif change == "duplicate_duid":
        rows.append(tuple(row))
    elif change == "other_canonical":
        old.append(dict(old[0], record_id="two"))
    elif change == "bad_field":
        decisions[0]["fields"] = ["status"]
    else:
        header = list(rows[3])
        header[18] = "Generic capacity"
        rows[3] = tuple(header)
    rows[4] = tuple(row)
    with pytest.raises(ValueError):
        stage(rows, decisions, old)


def test_exact_single_native_phase_identity():
    rows, decisions, old = inputs()
    old[0]["external_ids_json"] = "{}"
    old[0]["phases_json"] = '[{"Phase Name":"EXAMPLE1"}]'
    assert len(stage(rows, decisions, old)[0]) == 1


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf"), True, "100"])
def test_invalid_power_not_coerced(value):
    rows, decisions, old = inputs()
    row = list(rows[4])
    row[18] = value
    rows[4] = tuple(row)
    if type(value) is float and not math.isfinite(value):
        with pytest.raises(ValueError, match="Nonfinite"):
            stage(rows, decisions, old)
    else:
        result, _ = stage(rows, decisions, old)
        assert "capacity_ac_mw" not in result[0]
