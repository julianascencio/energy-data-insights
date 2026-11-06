"""Explicit ONS powerhouse relationships without additive capacity inference."""

import copy
import json
from typing import Any
from uuid import UUID, uuid5

from energy_data_retrieval.hydro_catalogue.ons import enrich_dispatch_metadata, wri_id
from energy_data_retrieval.pv_catalogue.catalogue import canonical_json


def enrich_components(
    existing: dict[str, Any], entry: dict[str, Any], *, now: str
) -> dict[str, Any]:
    """Attach reviewed components to a plant; never promote component MW to totals."""
    item, review = entry["inventory"], entry["review"]
    ids = json.loads(existing["external_ids_json"])
    names = sorted({u["nom_usina"] for u in item["units"]})
    equipment = [u["cod_equipamento"] for u in item["units"]]
    if (
        existing["country_code"] != "BRA"
        or ids.get("wri_gppd") != wri_id(item["ceg"])
        or review.get("record_id") != existing["record_id"]
        or review.get("canonical_name") != existing["name"]
        or review.get("ceg") != item["ceg"]
        or review.get("source_names") != names
        or review.get("decision") != "reviewed_component_relationships"
        or not review.get("scope_source_id")
        or len(names) < 2
        or len(equipment) != len(set(equipment))
    ):
        raise ValueError("Component identity/scope review does not match inputs")
    if ids.get("aneel_ceg", item["ceg"]) != item["ceg"]:
        raise ValueError("Conflicting CEG")
    row = copy.deepcopy(existing)
    ext = json.loads(row["extensions_json"])
    observation = {**item, "source_id": entry["source_id"], "retrieved_at": now}
    if "ons_component_review" in ext:
        if ext["ons_component_review"] != review or ext["ons_hydro_unit_inventory"] != [
            observation
        ]:
            raise ValueError("Immutable component evidence changed")
        return row
    if "ons_hydro_unit_inventory" in ext:
        raise ValueError("Existing unit evidence requires conflict review")
    source_ids = sorted({entry["source_id"], "wri_brazil_identity", review["scope_source_id"]})
    ext["ons_component_review"] = review
    ext["ons_hydro_unit_inventory"] = [observation]
    ext["ons_components"] = [
        {
            "component_id": str(uuid5(UUID(row["record_id"]), f"ons/{item['ceg']}/{name}")),
            "parent_record_id": row["record_id"],
            "name": name,
            "relationship": "powerhouse_of",
            "generating_unit_ids": sorted(
                u["cod_equipamento"] for u in item["units"] if u["nom_usina"] == name
            ),
            "source_ids": source_ids,
            "aggregation_role": "excluded_component_evidence",
        }
        for name in names
    ]
    ids["aneel_ceg"] = item["ceg"]
    facts = {
        "extensions_json": canonical_json(ext),
        "external_ids_json": canonical_json(ids),
        "owner_names": sorted(
            {u["nom_agenteproprietario"] for u in item["units"] if u["nom_agenteproprietario"]}
        ),
        "operator_names": sorted(
            {u["nom_agenteoperador"] for u in item["units"] if u["nom_agenteoperador"]}
        ),
    }
    fs, evidence = json.loads(row["field_sources_json"]), json.loads(row["evidence_json"])
    for key, value in facts.items():
        if key == "owner_names" and row.get(key):
            evidence.setdefault(
                "historical_owner_names", {"original_value": row[key], "sources": fs.get(key, [])}
            )
        row[key] = value
        fs[key] = sorted(set(fs.get(key, []) + source_ids))
        evidence[key] = {
            "locator": "ONS CSV rows " + ",".join(str(u["_row"]) for u in item["units"]),
            "confidence": "high",
            "unit": None,
            "normalization": (
                "Explicit registry/component review; "
                "components are not aliases or additive plant capacity"
            ),
            "original_value": value,
        }
    row.update(
        field_sources_json=canonical_json(fs),
        evidence_json=canonical_json(evidence),
        sources=sorted(set(row["sources"] + source_ids)),
        updated_at=now,
        last_verified_at=now,
    )
    return enrich_dispatch_metadata(row, now=now)
