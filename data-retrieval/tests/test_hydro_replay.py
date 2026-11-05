"""Synthetic two-shard replay verifies failure leaves every file untouched."""

import json

import pytest

from energy_data_retrieval.hydro_catalogue.replay import replay_reviewed
from energy_data_retrieval.pv_catalogue.catalogue import canonical_json


@pytest.fixture
def catalogue(tmp_path):
    folder = tmp_path / "records/projects"
    folder.mkdir(parents=True)
    for name in ("a", "b"):
        row = {"record_id": name, "created_at": "2020-01-01T00:00:00Z", "name": name}
        (folder / f"{name}.jsonl").write_text(canonical_json(row) + "\n")
    return tmp_path


def snapshot(root):
    return {p: p.read_bytes() for p in root.rglob("*.jsonl")}


@pytest.mark.parametrize(
    "failure", ["duplicate", "missing", "late_conflict", "identity", "creation"]
)
def test_rejects_entire_batch_before_any_write(catalogue, failure):
    before = snapshot(catalogue)
    entries = [{"record_id": "a"}, {"record_id": "b"}]
    if failure == "duplicate":
        entries.append({"record_id": "a"})
    if failure == "missing":
        entries.append({"record_id": "absent"})

    def transform(row, entry):
        if entry["record_id"] == "b":
            if failure == "late_conflict":
                raise ValueError("Conflicting capacity")
            if failure == "identity":
                row["record_id"] = "wrong"
            if failure == "creation":
                row["created_at"] = "2026-01-01T00:00:00Z"
        return {**row, "name": "reviewed"}

    with pytest.raises(ValueError):
        replay_reviewed(catalogue, entries, transform)
    assert snapshot(catalogue) == before


def test_replay_preserves_unreviewed_shard_and_is_idempotent(catalogue):
    before = snapshot(catalogue)
    entries = [{"record_id": "a"}]

    def transform(row, entry):
        return {**row, "name": "reviewed"}

    assert replay_reviewed(catalogue, entries, transform) == 1
    after = snapshot(catalogue)
    assert json.loads((catalogue / "records/projects/a.jsonl").read_text())["name"] == "reviewed"
    unreviewed = catalogue / "records/projects/b.jsonl"
    assert after[unreviewed] == before[unreviewed]
    replay_reviewed(catalogue, entries, transform)
    assert snapshot(catalogue) == after


def test_rejects_duplicate_canonical_identity(catalogue):
    first = catalogue / "records/projects/a.jsonl"
    (catalogue / "records/projects/b.jsonl").write_bytes(first.read_bytes())
    before = snapshot(catalogue)
    with pytest.raises(ValueError, match="Duplicate canonical"):
        replay_reviewed(catalogue, [], lambda row, entry: row)
    assert snapshot(catalogue) == before
