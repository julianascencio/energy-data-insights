"""Synthetic IHA identity and historical scope boundaries."""

import copy
import json

import pytest

from energy_data_retrieval.hydro_catalogue.gppd import parse_gppd
from energy_data_retrieval.hydro_catalogue.iha import enrich, parse_inventory


def sample():
    old = parse_gppd(
        "country,name,gppd_idnr,primary_fuel,capacity_mw,latitude,longitude\nIND,Synthetic,IND1,Hydro,10,20,80\n",
        source_id="wri",
        now="2026-01-01T00:00:00Z",
    )[0][0]
    item = {
        "id": 1,
        "row": 2,
        "raw": {
            "Database Status": "Matched with hydro station",
            "Hydropower Station Name": "Synthetic",
            "Lat (hydropower station 1)": "20",
            "Long (hydropower station 1)": "80",
            "HPP_elec_cap": "10",
            "River": "River",
            "Main_basin": "",
        },
    }
    return (
        old,
        item,
        dict(source_id="iha", reviewed_record_id=old["record_id"], now="2026-11-05T00:00:00Z"),
    )


def test_historical_evidence_preserves_lifecycle_capacity_coordinates_and_creation():
    old, item, kw = sample()
    new = enrich(old, item, **kw)
    for field in [
        "status",
        "status_as_of",
        "historical_capacity_mw",
        "latitude",
        "longitude",
        "created_at",
        "aggregation_role",
    ]:
        assert new[field] == old[field]
    assert new["river"] == "River"
    assert json.loads(new["external_ids_json"])["iha_india_2019"] == "1"
    assert enrich(new, item, **kw) == new
    assert "storage_capacity_mwh" not in new


@pytest.mark.parametrize(
    "field,value",
    [
        ("Database Status", "Not hydro"),
        ("Hydropower Station Name", "Other"),
        ("Lat (hydropower station 1)", "nan"),
        ("Long (hydropower station 1)", "81"),
        ("HPP_elec_cap", "20"),
    ],
)
def test_ambiguous_station_cannot_be_accepted(field, value):
    old, item, kw = sample()
    item["raw"][field] = value
    with pytest.raises(ValueError):
        enrich(old, item, **kw)


def test_csv_identity_and_encoding():
    data = (
        b"ID,Database Status,Hydropower Station Name,Lat (hydropower station 1),"
        b"Long (hydropower station 1),HPP_elec_cap,River,Main_basin\n"
        b"1,Not hydro,Test\x96dam,,,,,\n"
    )
    assert parse_inventory(data)[0]["raw"]["Hydropower Station Name"] == "Test\u2013dam"
    with pytest.raises(ValueError, match="duplicate"):
        parse_inventory(data + data.splitlines()[1] + b"\n")
    with pytest.raises(ValueError, match="columns"):
        parse_inventory(b"ID\n1\n")


def test_explicit_crosswalk_and_immutable_observation():
    old, item, kw = sample()
    with pytest.raises(ValueError, match="Explicit"):
        enrich(old, item, **{**kw, "reviewed_record_id": "other"})
    new = enrich(old, item, **kw)
    changed = copy.deepcopy(item)
    changed["raw"]["River"] = "Other"
    with pytest.raises(ValueError, match="Immutable"):
        enrich(new, changed, **kw)
