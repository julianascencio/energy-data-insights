"""Synthetic identity ambiguities; no live registry data needed."""

import json

import pytest

from energy_data_retrieval.wind_catalogue.identity import distinctive_name, screen_eia_sites


def candidate(code=1, name="Synthetic Maple Wind Project", lat=60, lon=0):
    return dict(plant_code=code, name=name, plant_context={"Latitude": lat, "Longitude": lon})


def project(name="Synthetic Birch Wind Project", aliases=None, lat=60, lon=0.15, ids=None):
    return dict(
        record_id="test",
        entity_type="projects",
        country_code="USA",
        name=name,
        aliases=aliases or [],
        latitude=lat,
        longitude=lon,
        external_ids_json=json.dumps(ids or {}),
    )


def test_generic_words_do_not_match_but_alias_and_latitude_distance_do():
    assert distinctive_name("Élan Wind Project LLC") == "elan"
    row = screen_eia_sites([candidate()], [project()])[0]
    assert row["name_matches"] == []
    assert 8 < row["nearby_projects"][0]["distance_km"] < 9
    assert row["decision"] == "manual_review_required"
    row = screen_eia_sites([candidate()], [project(aliases=["Synthetic Maple"])])[0]
    assert row["name_matches"][0]["matched_name"] == "Synthetic Maple"


def test_registry_phase_cohort_and_unknown_geometry_remain_flags():
    rows = screen_eia_sites(
        [candidate(name="Test II"), candidate(2, "Elsewhere", lon=0.05)],
        [project(ids={"wri_gppd": "USA0000001"})],
    )
    assert rows[0]["existing_registry_ids"] == ["test"]
    assert rows[0]["phase_or_direction_flag"]
    assert rows[0]["cohort_peers"][0]["nearby"]
    row = screen_eia_sites([candidate(lat=None)], [])[0]
    assert row["missing_coordinate"]
    assert row["decision"] == "manual_review_required"
    with pytest.raises(ValueError, match="unique"):
        screen_eia_sites([candidate(), candidate()], [])


def test_empty_name_and_zero_coordinates_are_distinct():
    row = screen_eia_sites([candidate(name="Wind Project", lat=0, lon=0)], [])[0]
    assert row["empty_distinctive_name"]
    assert not row["missing_coordinate"]
