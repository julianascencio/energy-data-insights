"""Synthetic tests for hydraulic and replacement-equipment evidence boundaries."""

import copy
import json

import pytest

from energy_data_retrieval.hydro_catalogue.era_report import enrich_reviewed


def inputs():
    row = dict(
        record_id="synthetic",
        name="Synthetic",
        country_code="UGA",
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
        record_id="synthetic",
        name="Synthetic",
        decision="reviewed_regulator_assertions",
        facts=facts,
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
    facts = json.loads(result["extensions_json"])["era_2023_assertions"]["facts"]
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


def synthetic_annex():
    return (
        "Operational Hydropower Projects\n"
        + "\n".join(f"Station {i}  1950s  0.06  Off-grid" for i in range(36))
        + "\nHydropower Projects Under Construction or Licensed to Start Construction\n"
        + "\n".join(f"Planned {i}  4.2  On-grid" for i in range(23))
        + "\nHydropower Projects Undergoing Feasibility Studies\nExcluded  900  On-grid"
    )


def test_parser_preserves_decade_null_and_joint_lifecycle():
    from energy_data_retrieval.hydro_catalogue.era_report import parse_annex

    rows = parse_annex(synthetic_annex())
    assert len(rows) == 59
    assert rows["Station 0"]["commissioning"] == "1950s"
    assert rows["Station 0"]["capacity_mw"] == 0.06
    assert rows["Planned 0"]["commissioning"] is None
    assert rows["Planned 0"]["lifecycle_group"] == "construction_or_licensed"
    assert "Excluded" not in rows


@pytest.mark.parametrize("change", ["duplicate", "missing", "negative"])
def test_parser_refuses_drift(change):
    from energy_data_retrieval.hydro_catalogue.era_report import parse_annex

    text = synthetic_annex()
    if change == "duplicate":
        text = text.replace("Station 1 ", "Station 0 ")
    elif change == "missing":
        text = text.replace("Station 0  1950s  0.06  Off-grid", "")
    else:
        text = text.replace("0.06", "-0.06", 1)
    with pytest.raises(ValueError):
        parse_annex(text)
