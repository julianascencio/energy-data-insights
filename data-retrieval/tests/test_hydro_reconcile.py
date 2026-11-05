"""Synthetic reviewed-crosswalk cases, with no network or real-plant assertions."""

import json

import pytest

from energy_data_retrieval.hydro_catalogue.gppd import parse_gppd
from energy_data_retrieval.hydro_catalogue.nve import parse_nve
from energy_data_retrieval.hydro_catalogue.reconcile import enrich_reviewed


def inputs():
    old, _ = parse_gppd(
        "country,name,gppd_idnr,primary_fuel,capacity_mw,latitude,longitude\n"
        "NOR,Synthetic,wri-test,Hydro,10,60,10\n",
        source_id="wri",
        now="2026-11-01T00:00:00Z",
    )
    new, _ = parse_nve(
        json.dumps(
            [
                {
                    "VannKraftverkID": 1,
                    "Navn": "Synthetic",
                    "VannKVTypeID": "K",
                    "ErIDrift": True,
                    "UnderBygging": False,
                    "MaksYtelse": 8,
                }
            ]
        ),
        source_id="nve",
        now="2026-11-02T00:00:00Z",
    )
    review = {
        "record_id": old[0]["record_id"],
        "nve_id": "1",
        "name": "Synthetic",
        "distance_m": 12,
        "decision": "reviewed_identity_match",
        "source_id": "gis",
        "locator": "synthetic fixture",
    }
    return old[0], new[0], review


def test_identity_history_and_capacity_boundaries():
    old, new, review = inputs()
    result = enrich_reviewed(old, new, review, now="2026-11-03T00:00:00Z")
    assert result["record_id"] == old["record_id"]
    assert result["created_at"] == old["created_at"]
    assert result["historical_capacity_mw"] == 10
    assert result["installed_capacity_mw"] == 8
    assert result["aggregation_role"] == "unresolved"
    assert json.loads(result["external_ids_json"]) == {"wri_gppd": "wri-test", "nve": "1"}


def test_idempotent_reverification_does_not_change_updated_at():
    old, new, review = inputs()
    first = enrich_reviewed(old, new, review, now="2026-11-03T00:00:00Z")
    second = enrich_reviewed(first, new, review, now="2026-11-04T00:00:00Z")
    assert first["updated_at"] == second["updated_at"]
    assert second["last_verified_at"] == "2026-11-04T00:00:00Z"


@pytest.mark.parametrize(
    "change",
    [
        {"decision": "candidate"},
        {"nve_id": "2"},
        {"name": "Different"},
        {"distance_m": 251},
        {"distance_m": -1},
        {"record_id": "other"},
    ],
)
def test_unreviewed_or_mismatched_identity_rejected(change):
    old, new, review = inputs()
    with pytest.raises(ValueError, match="identity review"):
        enrich_reviewed(old, new, {**review, **change}, now="2026-11-03T00:00:00Z")


def test_existing_conflicting_fact_is_not_overwritten():
    old, new, review = inputs()
    old["installed_capacity_mw"] = 12
    with pytest.raises(ValueError, match="conflict review"):
        enrich_reviewed(old, new, review, now="2026-11-03T00:00:00Z")
