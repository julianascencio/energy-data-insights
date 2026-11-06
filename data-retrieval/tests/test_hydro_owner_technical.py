"""Synthetic tests for hydraulic and replacement-equipment evidence boundaries."""

import copy
import json

import pytest

from energy_data_retrieval.hydro_catalogue.owner_technical import enrich_reviewed


def inputs():
    row = dict(
        record_id="synthetic",
        name="Synthetic",
        country_code="KEN",
        extensions_json="{}",
        field_sources_json="{}",
        evidence_json="{}",
        sources=[],
        created_at="2020-01-01",
        installed_capacity_mw=None,
        net_head_m=None,
        storage_capacity_mwh=None,
        status="unknown",
    )
    facts = [
        dict(
            key="original_generator",
            value={"each_mva": 85, "count": 2},
            unit=None,
            basis="Apparent power, not active MW",
            locator="Synthetic original group",
            uncertainty="unknown",
        ),
        dict(
            key="replacement",
            value={"mw": 80, "year": 1999},
            unit=None,
            basis="Replacement not additive",
            locator="Synthetic new group",
            uncertainty="unknown",
        ),
    ]
    return row, dict(
        record_id="synthetic", name="Synthetic", decision="reviewed_owner_assertions", facts=facts
    )


def test_no_sums_or_current_promotions_and_idempotent_dates():
    row, entry = inputs()
    original = copy.deepcopy(row)
    result = enrich_reviewed(row, entry, now="2026-11-06T00:00:00Z")
    assert row == original
    assert result["installed_capacity_mw"] is None
    assert result["net_head_m"] is None
    assert result["storage_capacity_mwh"] is None
    assert result["created_at"] == row["created_at"]
    facts = json.loads(result["extensions_json"])["kengen_technical_assertions"]["facts"]
    assert facts[0]["value"]["each_mva"] == 85
    assert enrich_reviewed(result, entry, now="2026-11-07T00:00:00Z") == result
    entry["facts"][1]["value"]["mw"] = 81
    with pytest.raises(ValueError, match="conflict"):
        enrich_reviewed(result, entry, now="2026-11-07T00:00:00Z")


@pytest.mark.parametrize("change", ["identity", "provenance", "duplicate"])
def test_invalid_review_rejected(change):
    row, entry = inputs()
    if change == "identity":
        entry["record_id"] = "wrong"
    elif change == "provenance":
        entry["facts"][0]["locator"] = ""
    else:
        entry["facts"].append(entry["facts"][0])
    with pytest.raises(ValueError):
        enrich_reviewed(row, entry, now="2026-11-06T00:00:00Z")
