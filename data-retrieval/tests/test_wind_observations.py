"""Synthetic historical revisions remain distinct from selected specifications."""

import copy
import hashlib
import json

import pytest

from energy_data_retrieval.wind_catalogue.observations import enrich_oem_history


def fixture():
    original = b"SYNTHETIC OEM history: no real turbine claims"
    row = dict(
        record_id="synthetic",
        entity_type="equipment",
        manufacturer="Test",
        model="A",
        rated_power_kw=100,
        created_at="2001-01-01T00:00:00Z",
        updated_at="2001-01-01T00:00:00Z",
        sources=["older"],
        extensions_json="{}",
        field_sources_json="{}",
        evidence_json="{}",
    )
    entry = dict(
        record_id="synthetic",
        manufacturer="Test",
        model="A",
        identity_rated_power_kw=100,
        locator="Synthetic paragraph1",
        boundary="Prototype only; not series configuration",
        facts={"prototype_power_kw": 90, "current_certification": None},
    )
    doc = dict(
        source_id="synthetic_history",
        sha256=hashlib.sha256(original).hexdigest(),
        published_at="2025-01-01",
        revision="Dated article, no revision number",
        entries=[entry],
        expected_record_ids=["synthetic"],
    )
    return doc, original, [row]


def test_dated_conflict_keeps_scalar_and_creation_and_replay_timestamp():
    doc, data, old = fixture()
    result = enrich_oem_history(doc, data, old, now="2026-01-01T00:00:00Z")
    assert result[0]["rated_power_kw"] == 100
    assert result[0]["created_at"] == old[0]["created_at"]
    assert old[0]["extensions_json"] == "{}"
    observation = json.loads(result[0]["extensions_json"])["oem_historical_observations"][0]
    assert observation["facts"]["prototype_power_kw"] == 90
    assert observation["facts"]["current_certification"] is None
    assert enrich_oem_history(doc, data, result, now="2026-02-01T00:00:00Z") == result
    doc["entries"][0]["facts"]["prototype_power_kw"] = 91
    with pytest.raises(ValueError, match="Immutable"):
        enrich_oem_history(doc, data, result, now="2026-02-01T00:00:00Z")


@pytest.mark.parametrize("fault", ["hash", "identity", "missing", "duplicate", "boundary"])
def test_rejects_unreviewed_or_incomplete_transcription(fault):
    doc, data, rows = fixture()
    doc = copy.deepcopy(doc)
    if fault == "hash":
        data += b"changed"
    if fault == "identity":
        doc["entries"][0]["identity_rated_power_kw"] = 101
    if fault == "missing":
        doc["expected_record_ids"].append("missing")
    if fault == "duplicate":
        doc["entries"] *= 2
    if fault == "boundary":
        doc["entries"][0]["boundary"] = ""
    with pytest.raises(ValueError):
        enrich_oem_history(doc, data, rows, now="2026-01-01T00:00:00Z")
