"""Synthetic Aragón discovery guards never infer canonical identities or AC power."""

import hashlib
import json

import pytest

from energy_data_retrieval.pv_catalogue.aragon import read_aragon_geojson


def feature(**changes):
    p = {
        "objectid": 1,
        "nombre": "Example PV",
        "promotor": "Private name",
        "potencia_placas_mwp": 10,
        "potencia_inversior_mwp": 8,
    }
    p.update(changes)
    return {
        "type": "Feature",
        "properties": p,
        "geometry": {"type": "MultiPolygon", "coordinates": [[[[700000, 4500000]]]]},
    }


def read(features):
    b = json.dumps({"type": "FeatureCollection", "features": features}).encode()
    return read_aragon_geojson(b, sha256=hashlib.sha256(b).hexdigest())


def test_discovery_preserves_ratings_without_ac_coordinates_or_private_promoter():
    r = read([feature()])[0]
    assert r["panel_peak_mwp_as_reported"] == 10
    assert r["inverter_power_mwp_as_reported"] == 8
    assert r["identity_status"] == "review_only_not_accepted"
    assert (
        not {"record_id", "capacity_ac_mw", "latitude", "longitude", "owners", "developers"}
        & r.keys()
    )
    assert "Private name" not in json.dumps(r)


@pytest.mark.parametrize(
    "change",
    [
        {"objectid": True},
        {"objectid": -1},
        {"nombre": ""},
        {"potencia_placas_mwp": -1},
        {"potencia_inversior_mwp": True},
        {"extra": "schema drift"},
    ],
)
def test_invalid_source_cannot_stage(change):
    with pytest.raises(ValueError):
        read([feature(**change)])


def test_duplicates_and_geometry_fail_closed():
    with pytest.raises(ValueError, match="duplicate"):
        read([feature(), feature()])
    f = feature()
    f["geometry"]["type"] = "Point"
    with pytest.raises(ValueError, match="polygon"):
        read([f])
    with pytest.raises(ValueError, match="checksum"):
        read_aragon_geojson(b"{}", sha256="0" * 64)
    assert read([feature(potencia_placas_mwp=None)])[0]["panel_peak_mwp_as_reported"] is None
