"""Offline tests of MaStR identity screens and capacity boundaries."""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from energy_data_retrieval.wind_catalogue.mastr import stage


def inputs():
    return json.loads((Path(__file__).parent / "fixtures/wind/mastr_synthetic.json").read_text())


def run(data, existing=None):
    return stage(
        data["units"],
        data["dictionary"],
        existing or [],
        source_id="synthetic",
        now="2026-11-03T12:45:00Z",
    )


def test_unit_ratings_and_retired_units_do_not_imply_farm_capacity():
    data = inputs()
    before = deepcopy(data)
    rows, ledger = run(data)
    assert data == before
    assert len(rows) == 4 and ledger[0]["decision"] == "added"
    project = rows[0]
    assert project["aggregation_role"] == "unresolved"
    assert project["status"] == "unknown" and project["fleet_completeness"] == "partial"
    assert "installed_capacity_mw" not in project and "turbine_count" not in project
    assert all(r["project_record_id"] == project["record_id"] for r in rows[1:])
    assert "rated_power_kw" not in rows[1]
    details = json.loads(rows[1]["extensions_json"])
    assert details["source_fields"]["Bruttoleistung"] == "3000"
    assert details["source_fields"]["Nettonennleistung"] == "2900"
    assert json.loads(rows[-1]["extensions_json"])["decoded_lifecycle"] == "Endgültig stillgelegt"
    assert "anchor" in project["location_accuracy"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("AnlagenbetreiberMastrNummer", "OTHER"),
        ("Gemeindeschluessel", ""),
        ("Breitengrad", None),
        ("WindAnLandOderAufSee", "889"),
        ("EinheitSystemstatus", "OTHER"),
        ("Laengengrad", "14"),
    ],
)
def test_incoherent_scopes_are_held(field, value):
    data = inputs()
    data["units"][0][field] = value
    rows, ledger = run(data)
    assert not rows and ledger[0]["decision"] == "deferred"


def test_adjacent_different_label_is_not_a_separate_farm():
    data = inputs()
    alias = deepcopy(data["units"][0])
    alias.update(EinheitMastrNummer="ALIAS", NameWindpark="Different label")
    data["units"].append(alias)
    rows, ledger = run(data)
    assert not rows
    assert len(ledger) == 2
    assert any("alias/phase" in x["reason"] for x in ledger)


@pytest.mark.parametrize("change", ["duplicate", "wrong_state"])
def test_invalid_partition_rejected(change):
    data = inputs()
    if change == "duplicate":
        data["units"].append(deepcopy(data["units"][0]))
    else:
        data["units"][0]["Bundesland"] = "1410"
    with pytest.raises(ValueError):
        run(data)


def test_replay_is_stable_and_does_not_readd_existing_projects():
    data = inputs()
    rows, _ = run(data)
    assert run(data)[0] == rows
    data["units"].reverse()
    assert run(data)[0] == rows
    assert not run(data, rows)[0]


def test_historical_nearby_project_is_held_despite_different_name():
    old = {
        "record_id": "historical",
        "entity_type": "projects",
        "name": "Old name",
        "country_code": "DEU",
        "latitude": 54.05,
        "longitude": 9,
    }
    assert not run(inputs(), [old])[0]


def test_xml_partition_count_and_dictionary_guard(tmp_path):
    from energy_data_retrieval.wind_catalogue.mastr import read_partition

    wind = tmp_path / "wind.xml"
    dictionary = tmp_path / "codes.xml"
    wind.write_text("<root><EinheitWind><Bundesland>1411</Bundesland></EinheitWind></root>")
    dictionary.write_text(
        "<root><entry><Id>1411</Id><Wert>Schleswig-Holstein</Wert></entry></root>"
    )
    units, _ = read_partition(wind, dictionary, expected_total=1, expected_selected=1)
    assert len(units) == 1
    with pytest.raises(ValueError, match="count mismatch"):
        read_partition(wind, dictionary, expected_total=2, expected_selected=1)
    dictionary.write_text("<root/>")
    with pytest.raises(ValueError, match="dictionary"):
        read_partition(wind, dictionary, expected_total=1, expected_selected=1)


@pytest.mark.parametrize(
    "state_code,state_name",
    [
        ("1408", "Niedersachsen"),
        ("1409", "Nordrhein-Westfalen"),
        ("1400", "Brandenburg"),
        ("1414", "Sachsen-Anhalt"),
    ],
)
def test_selected_state_preserves_scope(state_code, state_name):
    data = inputs()
    data["dictionary"][state_code] = state_name
    for unit in data["units"]:
        unit["Bundesland"] = state_code
    rows, _ = stage(
        data["units"],
        data["dictionary"],
        [],
        source_id="synthetic",
        now="2026-11-03T13:40:00Z",
        state_code=state_code,
    )
    assert rows[0]["region"] == state_name
    assert rows[0]["aggregation_role"] == "unresolved"
    with pytest.raises(ValueError, match="selected state"):
        run(data)
