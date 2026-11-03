"""Check that station staging retains scope, identity and evidence."""

import json
from datetime import datetime

import pytest

from energy_data_retrieval.pv_catalogue.australia import _HEADERS, stage_australian_stations


def _inputs():
    feature = {
        "globalid": "ga-id",
        "objectid": 42,
        "feature_name": "Example Solar Farm",
        "technology_type": "Solar Photovoltaic",
        "state": "NSW",
        "spatial_confidence": 5,
        "generation_capacity_mw": 80,
        "locality": "EXAMPLE",
        "latitude": -33.0,
        "longitude": 149.0,
    }
    header = tuple(_HEADERS.get(i) for i in range(22))
    row = [None] * 22
    for i, value in {
        0: 123,
        1: "Example",
        5: "NSW1",
        9: "Solar PV",
        12: "EXASF1",
        17: 100,
        18: 80,
        20: "In Service",
        21: datetime(2023, 4, 10),
    }.items():
        row[i] = value
    decision = {
        "ga_globalid": "ga-id",
        "ga_objectid": 42,
        "aemo_duid": "EXASF1",
        "survey_row": 5,
        "locality": "Example",
        "approve_nameplate": ["capacity_ac_mw"],
    }
    return {"features": [{"attributes": feature}]}, [(), (), (), header, tuple(row)], decision


def _stage(stations, survey, decisions, existing=()):
    return stage_australian_stations(
        stations,
        survey,
        decisions,
        list(existing),
        ga_source="ga",
        survey_source="aemo",
        survey_date="2026-10-30",
    )


def test_new_station_uses_only_reviewed_nameplate_and_source_date():
    ga, survey, decision = _inputs()
    (record,) = _stage(ga, survey, [decision])
    assert record["capacity_ac_mw"] == 80
    assert "capacity_dc_mw" not in record
    assert "capacity_unspecified_mw" not in record
    assert record["commissioning_date"] == "2023-04-10"
    assert json.loads(record["external_ids_json"])["aemo_duid"] == "EXASF1"
    assert json.loads(record["field_sources_json"])["capacity_ac_mw"] == "aemo"


def test_rejects_mixed_survey_scope_even_with_matching_pv_duid():
    ga, survey, decision = _inputs()
    row = list(survey[-1])
    row[9] = "Battery"
    row[12] = "EXABAT1"
    with pytest.raises(ValueError, match="Unresolved station boundary"):
        _stage(ga, [*survey, tuple(row)], [decision])


def test_rejects_existing_alias_for_new_station_and_unreviewed_location():
    ga, survey, decision = _inputs()
    old = {
        "record_id": "existing",
        "name": "Another name",
        "aliases": ["Example Solar Farm"],
        "country_code": "AUS",
        "region": "New South Wales",
        "latitude": -33.0,
        "longitude": 149.08,
    }
    with pytest.raises(ValueError, match="New identity"):
        _stage(ga, survey, [decision], [old])
    with pytest.raises(ValueError, match="positions differ"):
        _stage(ga, survey, [dict(decision, record_id="existing")], [old])


def test_existing_station_only_fills_missing_locality():
    ga, survey, decision = _inputs()
    old = {
        "record_id": "existing",
        "name": "Example Solar Farm",
        "country_code": "AUS",
        "region": "New South Wales",
        "latitude": -33.002,
        "longitude": 149.005,
        "capacity_ac_mw": 75,
    }
    decision["record_id"] = "existing"
    (record,) = _stage(ga, survey, [decision], [old])
    assert record["locality"] == "Example"
    assert "capacity_ac_mw" not in record
    assert _stage(ga, survey, [decision], [dict(old, locality="Example")]) == []
