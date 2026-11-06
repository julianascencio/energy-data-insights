"""Synthetic component scope, immutable evidence and non-additive capacity tests."""

import copy
import json

import pytest

from energy_data_retrieval.hydro_catalogue.components import enrich_components
from energy_data_retrieval.hydro_catalogue.gppd import parse_gppd


def inputs():
    row = parse_gppd(
        "country,name,gppd_idnr,primary_fuel,capacity_mw,latitude,longitude\n"
        "BRA,Synthetic complex,BRA0002547,Hydro,4,-10,-50\n",
        source_id="wri",
        now="2026-01-01T00:00:00Z",
    )[0][0]
    units = [
        dict(
            nom_usina=name,
            cod_equipamento=f"G{i}",
            _row=i + 2,
            nom_agenteproprietario="Owner",
            nom_agenteoperador="Operator",
            id_estado="MT",
        )
        for i, name in enumerate(["EXTERNAL", "UNDERGROUND"])
    ]
    review = dict(
        record_id=row["record_id"],
        canonical_name=row["name"],
        ceg="PCH.PH.MT.002547-0.01",
        source_names=["EXTERNAL", "UNDERGROUND"],
        decision="reviewed_component_relationships",
        scope_source_id="owner",
    )
    return row, dict(inventory=dict(ceg=review["ceg"], units=units), review=review, source_id="ons")


def test_components_are_stable_non_additive_and_not_aliases():
    row, entry = inputs()
    original = copy.deepcopy(row)
    new = enrich_components(row, entry, now="2026-11-06T05:40:00Z")
    ext = json.loads(new["extensions_json"])
    assert row == original
    assert new["created_at"] == row["created_at"]
    assert new["status"] == row["status"]
    assert new.get("installed_capacity_mw") is None
    assert new.get("aliases") == row.get("aliases")
    assert new["aggregation_role"] == "unresolved"
    components = ext["ons_components"]
    assert len({c["component_id"] for c in components}) == 2
    assert all(c["parent_record_id"] == row["record_id"] for c in components)
    assert [c["generating_unit_ids"] for c in components] == [["G0"], ["G1"]]
    assert enrich_components(new, entry, now="2026-11-06T05:40:00Z") == new
    with pytest.raises(ValueError, match="Immutable"):
        enrich_components(new, entry, now="2026-11-07T05:40:00Z")


@pytest.mark.parametrize(
    "key", ["record_id", "canonical_name", "ceg", "source_names", "scope_source_id"]
)
def test_review_mismatch_rejected(key):
    row, entry = inputs()
    entry["review"][key] = None
    with pytest.raises(ValueError, match="scope review"):
        enrich_components(row, entry, now="2026-11-06T05:40:00Z")


def test_duplicate_equipment_rejected():
    row, entry = inputs()
    entry["inventory"]["units"][1]["cod_equipamento"] = "G0"
    with pytest.raises(ValueError, match="scope review"):
        enrich_components(row, entry, now="2026-11-06T05:40:00Z")
