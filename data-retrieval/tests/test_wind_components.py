"""Synthetic component identity, source completeness and application boundaries."""

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from energy_data_retrieval.wind_catalogue.components import stage_components

NOW = "2026-11-04T08:50:52Z"


def inputs():
    docs = json.loads(
        (Path(__file__).parent / "fixtures/wind/components_synthetic.json").read_text()
    )
    docs[0]["sha256"] = hashlib.sha256(b"synthetic original").hexdigest()
    return docs


def stage(docs, existing=None):
    target = {
        "record_id": "synthetic-turbine",
        "entity_type": "equipment",
        "equipment_category": "wind_turbine",
    }
    return stage_components(
        docs, {"synthetic": b"synthetic original"}, [target, *(existing or [])], now=NOW
    )


def test_no_geometry_from_model_or_equipment_from_generic_types():
    docs = inputs()
    before = deepcopy(docs)
    records, ledger = stage(docs)
    assert docs == before
    assert len(records) == 1 and records[0]["model"] == "B99"
    assert "blade_length_m" not in records[0] and "rated_power_kw" not in records[0]
    assert ledger[1]["decision"] == "deferred"
    links = json.loads(records[0]["compatibility_json"])
    assert len(links) == 1 and links[0]["conditions"] == "Only synthetic tower option A"
    assert stage(docs) == (records, ledger)


@pytest.mark.parametrize(
    "mutation",
    ["hash", "missing", "duplicate", "target", "condition", "power_boundary", "extra_field"],
)
def test_reject_incomplete_or_unsupported_transcription(mutation):
    docs = inputs()
    model = docs[0]["rows"][0]["models"][0]
    if mutation == "hash":
        docs[0]["sha256"] = "0" * 64
    elif mutation == "missing":
        docs[0]["rows"].pop()
    elif mutation == "duplicate":
        docs[0]["rows"][1]["row"] = "1"
    elif mutation == "target":
        model["links"][0]["equipment_record_id"] = "absent"
    elif mutation == "condition":
        model["links"][0]["conditions"] = ""
    elif mutation == "power_boundary":
        model["values"] = {"rated_power_kw": 1000}
    else:
        model["values"] = {"turbine_count": 3}
    with pytest.raises(ValueError):
        stage(docs)


def test_shared_model_keeps_one_identity_and_multiple_applications():
    docs = inputs()
    second = deepcopy(docs[0]["rows"][0])
    second["row"] = "2"
    second["models"][0]["links"][0]["conditions"] = "Only synthetic tower option B"
    docs[0]["rows"][1] = second
    records, _ = stage(docs)
    assert len(records) == 1
    assert len(json.loads(records[0]["compatibility_json"])) == 2
    second["models"][0]["values"] = {"blade_length_m": 30}
    with pytest.raises(ValueError, match="Conflicting"):
        stage(docs)


def test_existing_component_is_held_for_revision_review():
    records, _ = stage(inputs())
    new, decisions = stage(inputs(), records)
    assert not new
    assert decisions[0]["decision"] == "existing_identity_review"


def test_exact_out_of_category_identity_keeps_its_hold_reason():
    docs = inputs()
    docs[0]["rows"][1]["defer_reason"] = "Exact bearing code retained; category mapping pending"
    _, ledger = stage(docs)
    assert ledger[1]["reason"] == "Exact bearing code retained; category mapping pending"


def test_exact_converter_does_not_inherit_turbine_rating():
    docs = inputs()
    model = docs[0]["rows"][0]["models"][0]
    model.update(category="converter", model="Synthetic-C900")
    records, _ = stage(docs)
    assert records[0]["equipment_category"] == "converter"
    assert "rated_power_kw" not in records[0]
    assert (
        json.loads(records[0]["compatibility_json"])[0]["equipment_record_id"]
        == "synthetic-turbine"
    )
