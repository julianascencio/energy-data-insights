"""BOE partition completeness and wind/solar/auxiliary decision boundaries."""

import hashlib
from pathlib import Path

import pytest

from energy_data_retrieval.wind_catalogue.boe import select_wind_notices, stage_boe_notices

FIXTURE = Path(__file__).parent / "fixtures/wind/boe_synthetic.html"


def review(target="wind", effect="environmental_conditions", status="announced"):
    values = {
        "name": "Synthetic A",
        "status": status,
        "planned_capacity_mw": 33.0,
        "country_code": "ESP",
        "technology": "onshore",
        "notes": "Synthetic reviewed note",
    }
    return {
        "notice_id": "BOE-A-2026-1",
        "sha256": hashlib.sha256(b"original").hexdigest(),
        "published_at": "2026-11-02",
        "identity": "synthetic-permit-1",
        "decision_target": target,
        "decision_effect": effect,
        "locator": "Description and final resolution",
        "values": values,
        "locators": dict.fromkeys(values, "Final five-turbine configuration"),
    }


def stage(r, existing=None):
    return stage_boe_notices(
        [r],
        {r["notice_id"]: b"original"},
        existing or [],
        expected_ids=[r["notice_id"]],
        now="2026-11-04T12:40:00Z",
    )


def test_index_selects_all_wind_mentions_without_inferring_lifecycle_or_capacity():
    result = select_wind_notices(FIXTURE.read_text())
    assert [r["notice_id"] for r in result] == [f"BOE-A-2026-{n}" for n in (1, 2, 3)]
    assert all(set(r) == {"notice_id", "title"} for r in result)


@pytest.mark.parametrize("kind", ["duplicate", "truncated", "error", "missing_id"])
def test_bad_index_fails_closed(kind):
    html = FIXTURE.read_text()
    if kind == "duplicate":
        html = html.replace("BOE-A-2026-2", "BOE-A-2026-1")
    elif kind == "truncated":
        html += '<li class="dispo">'
    elif kind == "missing_id":
        html = html.replace("/diario_boe/txt.php?id=BOE-A-2026-1", "/missing")
    else:
        html = "<html>Access error</html>"
    with pytest.raises(ValueError):
        select_wind_notices(html)


def test_final_proposal_is_not_installed_or_export_capacity():
    rows, _ = stage(review())
    r = rows[0]
    assert r["planned_capacity_mw"] == 33
    assert "installed_capacity_mw" not in r and "export_capacity_mw" not in r
    assert "turbine_model" not in r and "latitude" not in r
    assert r["aggregation_role"] == "unresolved"
    assert stage(review()) == stage(review())


@pytest.mark.parametrize("target", ["solar", "auxiliary"])
def test_rejects_cancellation_from_nonwind_decision(target):
    with pytest.raises(ValueError, match="cannot cancel"):
        stage(review(target, "withdrawn", "cancelled"))
    assert stage(review(target, "withdrawn", "unknown"))[0][0]["status"] == "unknown"


def test_environmental_decision_is_not_full_permission():
    with pytest.raises(ValueError, match="construction authorization"):
        stage(review(status="permitted"))


@pytest.mark.parametrize("kind", ["checksum", "locator", "installed", "missing", "duplicate"])
def test_review_checks_originals_completeness_and_semantics(kind):
    r = review()
    if kind == "checksum":
        r["sha256"] = "0" * 64
    elif kind == "locator":
        r["locators"].pop("status")
    elif kind == "installed":
        r["values"]["installed_capacity_mw"] = 33
    elif kind in {"missing", "duplicate"}:
        with pytest.raises(ValueError):
            stage_boe_notices(
                [] if kind == "missing" else [r, r],
                {},
                [],
                expected_ids=[r["notice_id"]],
                now="2026-11-04T12:40:00Z",
            )
        return
    with pytest.raises(ValueError):
        stage(r)


def test_replay_defers_existing_identity_instead_of_duplicating_it():
    rows, _ = stage(review())
    new, decisions = stage(review(), rows)
    assert not new and decisions[0]["decision"] == "existing_identity_review"


def test_supporting_correction_is_linked_without_creating_another_project():
    r = review()
    r["supporting_evidence"] = {
        "name": [{"source_id": "correction", "locator": "Numbering correction only"}]
    }
    correction = {
        "notice_id": "correction",
        "sha256": hashlib.sha256(b"correction").hexdigest(),
        "values": {},
        "reason": "Supporting correction, not another farm",
    }
    rows, decisions = stage_boe_notices(
        [r, correction],
        {r["notice_id"]: b"original", "correction": b"correction"},
        [],
        expected_ids=[r["notice_id"], "correction"],
        now="2026-11-04T12:40:00Z",
    )
    assert len(rows) == 1 and len(decisions) == 2
    assert set(rows[0]["sources"]) == {r["notice_id"], "correction"}
    with pytest.raises(ValueError, match="Supporting notice"):
        stage(r)
