"""Synthetic public-projection/identity/privacy regressions, not source documents."""

import hashlib
import json

import pytest

from energy_data_retrieval.pv_catalogue.plandata import FIELDS, read_pv_plan_projection


def payload():
    p = dict.fromkeys(FIELDS)
    p.update(planid=123, komnr=101, plannavn="Synthetic PV plan", status="V", anvspec1=8135)
    p["datovedt"] = 19000101
    return {
        "type": "FeatureCollection",
        "numberReturned": 1,
        "timeStamp": "2026-11-04T13:00:00Z",
        "features": [{"type": "Feature", "geometry": None, "properties": p}],
    }


def read(data):
    content = json.dumps(data).encode()
    return read_pv_plan_projection(content, sha256=hashlib.sha256(content).hexdigest())


def test_no_plant_or_date_inference():
    rows = read(payload())
    assert rows[0]["adoption_native"] == 19000101
    assert rows[0]["planned_capacity_cells_native"] == [None]
    assert "record_id" not in rows[0] and "capacity_ac_mw" not in rows[0]
    assert "Sentinel/missing adoption date" in rows[0]["review_flags"]


@pytest.mark.parametrize("kind", ["privacy", "technology", "duplicate", "date", "count"])
def test_invalid_projection_or_identity_rejected(kind):
    d = payload()
    p = d["features"][0]["properties"]
    if kind == "privacy":
        p["owner_email"] = "synthetic@example.test"
    elif kind == "technology":
        p["anvspec1"] = 8130
    elif kind == "duplicate":
        d["features"] *= 2
        d["numberReturned"] = 2
    elif kind == "date":
        p["datovedt"] = 20260230
    else:
        d["numberReturned"] = 2
    with pytest.raises(ValueError):
        read(d)


def test_checksum_rejected_before_parse():
    with pytest.raises(ValueError, match="checksum"):
        read_pv_plan_projection(b"not-json", sha256="0" * 64)
