"""Synthetic evidence-basis boundaries; no live provider access."""

import copy
import json

import pytest

from energy_data_retrieval.hydro_catalogue.aha_provenance import enrich_provenance


def test_units_dates_and_profile_are_not_promoted_to_measurements():
    old = dict(
        extensions_json=json.dumps(
            {
                "aha_historical_inventory": [
                    {
                        "source_id": "synthetic",
                        "row": 4,
                        "raw": {
                            "Capacity": 10,
                            "Reservoir Size": 0,
                            "First Year": 2030,
                            "Mean Annual Discharge": 4,
                            "Availability": "Generic",
                            "Source_capacity": "example citation",
                        },
                    }
                ]
            }
        ),
        field_sources_json='{"extensions_json":["synthetic"]}',
        evidence_json="{}",
        created_at="2020-01-01",
        sources=["synthetic"],
        status="unknown",
    )
    original = copy.deepcopy(old)
    new = enrich_provenance(old, now="2026-11-06T00:00:00Z")
    assert old == original
    assert new["created_at"] == old["created_at"]
    assert new["status"] == "unknown"
    assert (
        not {
            "commissioning_date",
            "reservoir_volume_m3",
            "design_flow_m3_s",
            "installed_capacity_mw",
        }
        & new.keys()
    )
    obs = {x["column"]: x for x in json.loads(new["extensions_json"])["aha_field_provenance"]}
    assert obs["Reservoir Size"]["value"] == 0
    assert obs["Reservoir Size"]["unit"] == "million m3"
    assert obs["Capacity"]["upstream_reference"] == "example citation"
    assert obs["First Year"]["upstream_independently_verified"] is False
    assert enrich_provenance(new, now="2026-11-07T00:00:00Z") == new
    ext = json.loads(new["extensions_json"])
    ext["aha_historical_inventory"][0]["raw"]["Capacity"] = 11
    new["extensions_json"] = json.dumps(ext)
    with pytest.raises(ValueError, match="review"):
        enrich_provenance(new, now="2026-11-07T00:00:00Z")


def test_requires_previously_accepted_identity():
    with pytest.raises(ValueError, match="accepted"):
        enrich_provenance({"extensions_json": "{}"}, now="2026-11-06T00:00:00Z")
