"""Synthetic reference tables test boundaries; no real OEM claims or network access."""

import copy
import hashlib
import json

import pytest

from energy_data_retrieval.wind_catalogue.reference_yield import stage_reference_yields

NOW = "2026-11-05T00:00:00Z"


def fixture():
    original = b"SYNTHETIC reference table: A,100kW,50m/60m; second yield withdrawn"
    identity = dict(
        record_id="test-a",
        manufacturer="Synthetic",
        model="A",
        variant="v1",
        rated_power_kw=100,
        rotor_diameter_m=20,
    )
    rows = [
        dict(
            row=f"p1r{i}",
            locator=f"Synthetic page1 row{i}",
            type_label="A",
            rotor_diameter_m=20 if i == 1 else None,
            rotor_area_m2=314.2,
            rated_power_kw=100,
            hub_height_m=hub,
            reference_yield_kwh=value,
            note="Withdrawn2024-09-02" if i == 2 else "Same type only",
            withdrawn=i == 2,
            operating_mode=None,
            original_values={"yield_kwh": "1.000.000" if i == 1 else "1.100.000"},
            decision="addition",
            identity=identity,
        )
        for i, hub, value in [(1, 50, 1000000), (2, 60, 1100000)]
    ]
    doc = dict(
        source_id="synthetic-table",
        sha256=hashlib.sha256(original).hexdigest(),
        published_at=None,
        revision="Undated synthetic",
        expected_rows=["p1r1", "p1r2"],
        reference_site="synthetic-old",
        reference_conditions={"profile": "logarithmic", "air_density_kg_m3": None},
        period_years=5,
        period_source_id="synthetic-method",
        rows=rows,
    )
    return doc, original


def test_hubs_are_observations_and_withdrawal_and_missing_diameter_survive():
    doc, data = fixture()
    rows, ledger = stage_reference_yields(doc, data, [], now=NOW)
    assert len(rows) == 1 and len(ledger) == 2
    obs = json.loads(rows[0]["extensions_json"])["reference_yield_observations"][0]
    assert obs["period_years"] == 5 and obs["unit"] == "kWh"
    assert obs["reference_conditions"]["air_density_kg_m3"] is None
    assert obs["rows"][1]["withdrawn"] is True
    assert obs["rows"][1]["rotor_diameter_m"] is None
    assert rows[0].get("hub_height_m") is None
    assert rows[0].get("capacity_factor") is None
    assert stage_reference_yields(doc, data, rows, now="2026-11-06T00:00:00Z")[0] == rows


def test_conflicting_observation_preserves_existing_scalars_and_creation_time():
    doc, data = fixture()
    old, _ = stage_reference_yields(doc, data, [], now=NOW)
    doc["source_id"] = "synthetic-new"
    doc["reference_site"] = "synthetic-new-site"
    for r in doc["rows"]:
        r["decision"] = "enrichment"
        r["rated_power_kw"] = 110
        r["rotor_diameter_m"] = 21
    result, _ = stage_reference_yields(doc, data, old, now="2026-11-06T00:00:00Z")
    assert result[0]["rated_power_kw"] == 100
    assert result[0]["rotor_diameter_m"] == 20
    assert result[0]["created_at"] == NOW
    assert len(json.loads(result[0]["extensions_json"])["reference_yield_observations"]) == 2
    changed = copy.deepcopy(doc)
    changed["rows"][0]["reference_yield_kwh"] = 999
    with pytest.raises(ValueError, match="Immutable"):
        stage_reference_yields(changed, data, result, now=NOW)


@pytest.mark.parametrize(
    "fault",
    [
        "hash",
        "missing",
        "duplicate",
        "nan",
        "negative",
        "period",
        "period_source",
        "identity",
        "note",
    ],
)
def test_incomplete_or_unreviewed_evidence_is_rejected(fault):
    doc, data = fixture()
    if fault == "hash":
        data += b"changed"
    elif fault == "missing":
        doc["rows"].pop()
    elif fault == "duplicate":
        doc["rows"][1]["row"] = "p1r1"
    elif fault == "nan":
        doc["rows"][0]["reference_yield_kwh"] = float("nan")
    elif fault == "negative":
        doc["rows"][0]["hub_height_m"] = -1
    elif fault == "period":
        doc["period_years"] = None
    elif fault == "period_source":
        doc["period_source_id"] = None
    elif fault == "identity":
        doc["rows"][0]["decision"] = "enrichment"
    else:
        doc["rows"][0]["note"] = ""
    with pytest.raises(ValueError):
        stage_reference_yields(doc, data, [], now=NOW)


def test_new_identity_cannot_replace_printed_rating_with_an_invented_mode():
    doc, data = fixture()
    doc["rows"][0]["identity"]["rated_power_kw"] = 200
    with pytest.raises(ValueError, match="New identity"):
        stage_reference_yields(doc, data, [], now=NOW)
