"""BOE partition completeness and wind/solar/auxiliary decision boundaries."""

import hashlib
import json
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


def test_separate_extensions_share_notice_not_identity_or_capacity():
    r = review()
    projects = []
    for name in ["Extension A", "Extension B"]:
        child = review()
        child["identity"] = name
        child["values"].update(name=name, record_scope="phase", phase_id=name)
        child["locators"].update(record_scope="Extension scope", phase_id="Extension scope")
        projects.append(child)
    r["projects"] = projects
    rows, ledger = stage(r)
    assert len(rows) == len(ledger) == 2
    assert len({x["record_id"] for x in rows}) == 2
    assert all(x["record_scope"] == "phase" for x in rows)
    assert all(x["aggregation_role"] == "unresolved" for x in rows)
    projects[1]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="provenance"):
        stage(r)


def test_series_b_is_explicit_and_cannot_be_mixed_with_decisions():
    html = FIXTURE.read_text().replace("BOE-A-", "BOE-B-")
    assert select_wind_notices(html) == []
    assert len(select_wind_notices(html, series="B")) == 4
    with pytest.raises(ValueError, match="exactly one"):
        select_wind_notices(html, series="AB")


def test_multiple_daily_issues_discovery_keeps_same_day_only():
    from energy_data_retrieval.wind_catalogue.boe import issue_urls

    base = "https://www.boe.es/boe/dias/2026/10/28/"
    html = '<a href="index.php?d=267">Regular</a><a href="index.php?d=267">Duplicate</a>'
    html += '<a href="../27/index.php?d=266">Previous</a><a href="https://evil.example/index.php?d=1">Other</a>'
    assert issue_urls(html, base) == [base, base + "index.php?d=267"]
    with pytest.raises(ValueError):
        issue_urls(html, "https://evil.example/boe/dias/2026/10/28/")


def test_public_consultation_is_not_permission_or_operation():
    for status in ["permitted", "operational", "cancelled"]:
        with pytest.raises(ValueError, match="Public consultation"):
            stage(review(effect="public_consultation", status=status))


def test_registry_stops_renamed_farm_without_merging_distinct_scopes():
    first = review()
    first["values"]["external_ids_json"] = json.dumps({"gencat_expediente": "FUE-1"})
    first["locators"]["external_ids_json"] = "Expediente"
    rows, _ = stage(first)
    renamed = review()
    renamed["identity"] = "different-natural-identity"
    renamed["values"].update(
        name="Renamed or separate phase", external_ids_json=first["values"]["external_ids_json"]
    )
    renamed["locators"]["external_ids_json"] = "Expediente"
    new, decisions = stage(renamed, rows)
    assert new == []
    assert decisions[0]["decision"] == "existing_registry_review"
    assert rows[0]["name"] == "Synthetic A"


@pytest.mark.parametrize("namespace", ["boe_notice", "different_registry"])
def test_shared_notice_or_different_registry_is_not_project_identity(namespace):
    first = review()
    first["values"]["external_ids_json"] = json.dumps(
        {"gencat_expediente": "FUE-1", "boe_notice": "shared"}
    )
    first["locators"]["external_ids_json"] = "Identifiers"
    rows, _ = stage(first)
    second = review()
    second["identity"] = "separate-farm"
    second["values"].update(
        name="Separate farm",
        external_ids_json=json.dumps(
            {namespace: "shared" if namespace == "boe_notice" else "FUE-1"}
        ),
    )
    second["locators"]["external_ids_json"] = "Identifiers"
    assert len(stage(second, rows)[0]) == 1


def test_registry_guard_also_catches_collisions_within_a_multi_project_notice():
    r = review()
    r["projects"] = []
    for name in ["Farm A", "Farm B"]:
        child = review()
        child["identity"] = name
        child["values"].update(
            name=name, external_ids_json=json.dumps({"miteco_expediente": "PEol-1"})
        )
        child["locators"]["external_ids_json"] = "Shared procedure, scope unresolved"
        r["projects"].append(child)
    rows, decisions = stage(r)
    assert len(rows) == 1
    assert decisions[-1]["decision"] == "existing_registry_review"


def test_repowering_authorization_never_promotes_replacement_operation():
    for status in ["operational", "retired", "cancelled"]:
        with pytest.raises(ValueError, match="Repowering authorization"):
            stage(review(effect="repowering_authorization", status=status))
    rows, _ = stage(review(effect="repowering_authorization", status="permitted"))
    assert rows[0]["aggregation_role"] == "unresolved"
    assert rows[0].get("installed_capacity_mw") is None


def test_daily_scan_requires_empty_extra_issue_and_deduplicates_aliases():
    from energy_data_retrieval.wind_catalogue.boe import review_daily_indexes

    url = "https://www.boe.es/boe/dias/2026/09/02/"
    empty = b'<html>sumario<li class="dispo"><p>Other</p></li></html>'
    default = empty + b'<a href="index.php?d=216">Ordinary issue</a>'
    with pytest.raises(ValueError, match="issue URLs"):
        review_daily_indexes(url, {url: default})
    result = review_daily_indexes(url, {url: default, url + "index.php?d=216": empty})
    assert result["notices"] == []
    assert len(result["captures"]) == 2
    wind = FIXTURE.read_bytes()
    result = review_daily_indexes(url, {url: wind + default, url + "index.php?d=216": wind})
    assert len(result["notices"]) == 4
    with pytest.raises(ValueError, match="Conflicting notice"):
        review_daily_indexes(
            url,
            {url: wind + default, url + "index.php?d=216": wind.replace(b"72,6", b"73,6")},
        )


def test_application_refusal_is_not_operation_or_retirement():
    for status in ["operational", "retired", "permitted"]:
        with pytest.raises(ValueError, match="Application refusal"):
            stage(review(effect="application_refusal", status=status))
    rows, _ = stage(review(effect="application_refusal", status="cancelled"))
    assert rows[0]["aggregation_role"] == "unresolved"


@pytest.mark.parametrize("status", ["operational", "retired", "cancelled", "announced"])
def test_construction_authorization_does_not_prove_operation(status):
    with pytest.raises(ValueError, match="does not establish"):
        stage(review(effect="construction_authorization", status=status))
    row = stage(review(effect="construction_authorization", status="permitted"))[0][0]
    assert row["aggregation_role"] == "unresolved"
    assert row.get("installed_capacity_mw") is None


@pytest.mark.parametrize(
    "effect",
    [
        "public_consultation",
        "construction_authorization",
        "repowering_authorization",
        "environmental_conditions",
    ],
)
def test_unknown_status_cannot_bypass_proposed_capacity_boundary(effect):
    r = review(effect=effect, status="unknown")
    r["values"]["installed_capacity_mw"] = 33
    r["locators"]["installed_capacity_mw"] = "Synthetic proposal wording"
    with pytest.raises(ValueError, match="not installed capacity"):
        stage(r)


@pytest.mark.parametrize("field", ["planned_capacity_mw", "installed_capacity_mw", "turbine_count"])
def test_required_removals_do_not_publish_original_or_calculated_final_fleet(field):
    r = review()
    r["required_turbine_removals"] = ["Synthetic-2", "Synthetic-3"]
    r["values"].pop("planned_capacity_mw")
    r["locators"].pop("planned_capacity_mw")
    r["values"][field] = 21
    r["locators"][field] = "Superseded proposal or arithmetic"
    with pytest.raises(ValueError, match="separately reviewed revised design"):
        stage(r)
    r["values"].pop(field)
    r["locators"].pop(field)
    row = stage(r)[0][0]
    assert row.get(field) is None
    assert row["aggregation_role"] == "unresolved"
