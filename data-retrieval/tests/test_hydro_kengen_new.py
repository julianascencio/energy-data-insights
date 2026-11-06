"""Synthetic tests for accession stability, collision refusal and replay."""

import copy

import pytest

from energy_data_retrieval.hydro_catalogue.kengen_new import new_record


def entry():
    return {
        "review": {
            "decision": "reviewed_new_identity",
            "source_name": "Synthetic station",
            "accession": "synthetic-001",
            "identity_basis": "Synthetic owner review",
        },
        "inventory": {"source_name": "Synthetic station", "observations": []},
    }


def test_accession_is_not_name_rating_or_national_id():
    e = entry()
    row = new_record(e, now="2026-11-06T00:00:00Z")
    changed = copy.deepcopy(e)
    changed["review"]["source_name"] = changed["inventory"]["source_name"] = "Renamed station"
    assert new_record(changed, now="2026-11-06T00:00:00Z")["record_id"] == row["record_id"]
    assert row["external_ids_json"] == "{}"
    assert row["aggregation_role"] == "unresolved"
    assert row["status"] == "unknown"
    assert row.get("latitude") is None
    assert row.get("installed_capacity_mw") is None
    assert row.get("storage_capacity_mwh") is None


@pytest.mark.parametrize("field", ["decision", "source_name", "accession", "identity_basis"])
def test_review_required(field):
    e = entry()
    e["review"][field] = ""
    with pytest.raises(ValueError, match="identity review"):
        new_record(e, now="2026-11-06T00:00:00Z")


def test_duplicate_accessions_and_existing_name_collision_fail_before_write(tmp_path, monkeypatch):
    from energy_data_retrieval.hydro_catalogue import kengen_new

    monkeypatch.setattr(kengen_new, "load_records", lambda root: [])
    batch = {"reviewed_at": "2026-11-06T00:00:00Z", "accepted": [entry(), entry()]}
    output = tmp_path / "new.jsonl"
    with pytest.raises(ValueError, match="Duplicate"):
        kengen_new.accept_new(tmp_path, batch, output)
    assert not output.exists()
    prior = new_record(entry(), now=batch["reviewed_at"])
    prior["record_id"] = "another-id"
    monkeypatch.setattr(kengen_new, "load_records", lambda root: [prior])
    batch["accepted"] = [entry()]
    with pytest.raises(ValueError, match="Name collision"):
        kengen_new.accept_new(tmp_path, batch, output)
    assert not output.exists()
