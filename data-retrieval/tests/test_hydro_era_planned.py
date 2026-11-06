"""Synthetic project-vs-installed, accession and collision regression checks."""

import copy
import json

import pytest

from energy_data_retrieval.hydro_catalogue import era
from energy_data_retrieval.hydro_catalogue.era_planned import new_record


def entry():
    return dict(
        inventory=dict(
            capacity_mw=0.31,
            commissioning=None,
            lifecycle_group="construction_or_licensed",
            grid="On-grid",
        ),
        review=dict(
            decision="reviewed_new_identity",
            accession="synthetic-001",
            name="Synthetic",
            identity_basis="Synthetic review",
            locator="p1 row1",
        ),
    )


def test_project_rating_never_becomes_current_capacity_or_status():
    e = entry()
    r = new_record(e, now="2026-11-06T00:00:00Z")
    assert r["status"] == "unknown"
    assert r["aggregation_role"] == "unresolved"
    for field in [
        "installed_capacity_mw",
        "operational_capacity_mw",
        "latitude",
        "commissioning_date",
    ]:
        assert r.get(field) is None
    assert json.loads(r["observations_json"])[0]["field"] == "planned_capacity_mw"
    changed = copy.deepcopy(e)
    changed["review"]["name"] = "Renamed"
    changed["inventory"]["capacity_mw"] = 5
    assert new_record(changed, now="2026-11-06T00:00:00Z")["record_id"] == r["record_id"]


@pytest.mark.parametrize("value", [-1, float("nan"), True])
def test_invalid_capacity(value):
    e = entry()
    e["inventory"]["capacity_mw"] = value
    with pytest.raises(ValueError):
        new_record(e, now="2026-11-06T00:00:00Z")


def test_joint_category_and_unknown_commissioning_required():
    e = entry()
    e["inventory"]["lifecycle_group"] = "operational"
    with pytest.raises(ValueError):
        new_record(e, now="2026-11-06T00:00:00Z")


def test_procurement_kw_separate_from_report_mw():
    e = entry()
    e["review"]["corroboration"] = dict(
        source_id="ueccc-orio-tender-20200929",
        project_kw=339,
        period="2020-09-29",
        locator="Synthetic row",
        basis="Procurement design",
    )
    r = new_record(e, now="2026-11-06T00:00:00Z")
    obs = json.loads(r["observations_json"])
    assert [(o["value"], o["unit"], o["period"]) for o in obs] == [
        (0.31, "MW", "2023"),
        (339, "kW", "2020-09-29"),
    ]
    e["review"]["corroboration"]["project_kw"] = -1
    with pytest.raises(ValueError):
        new_record(e, now="2026-11-06T00:00:00Z")


def test_null_aliases_supported_and_collision_rejected(tmp_path, monkeypatch):
    prior = dict(record_id="other", country_code="UGA", name="Synthetic", aliases=None)
    monkeypatch.setattr(era, "load_records", lambda root: [prior])
    batch = dict(reviewed_at="2026-11-06T00:00:00Z", accepted=[entry()])
    with pytest.raises(ValueError, match="Name collision"):
        era.accept_new(tmp_path, batch, tmp_path / "new.jsonl", record_factory=new_record)
    assert not (tmp_path / "new.jsonl").exists()
