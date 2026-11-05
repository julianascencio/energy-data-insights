"""Apply explicitly reviewed NVE/WRI crosswalks; never discover or fuzzy-merge identities."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json


def enrich_reviewed(
    existing: dict[str, Any], candidate: dict[str, Any], review: dict[str, Any], *, now: str
) -> dict[str, Any]:
    """Preserve WRI identity/history and add NVE facts after explicit identity review.

    Aggregation remains unresolved. Different historical/current capacity ratings
    are separate observations, not evidence of uprating or a common scope.
    """
    ids = json.loads(existing["external_ids_json"])
    nve_ids = json.loads(candidate["external_ids_json"])
    if (
        review.get("decision") != "reviewed_identity_match"
        or review["record_id"] != existing["record_id"]
        or review["nve_id"] != nve_ids.get("nve")
        or existing["name"] != candidate["name"]
        or review["name"] != existing["name"]
        or existing["country_code"] != "NOR"
        or not 0 <= review["distance_m"] <= 250
    ):
        raise ValueError("Crosswalk identity review does not match inputs")
    if ids.get("nve") not in {None, review["nve_id"]}:
        raise ValueError("Conflicting existing NVE identity")
    row = deepcopy(existing)
    fs = json.loads(row["field_sources_json"])
    evidence = json.loads(row["evidence_json"])
    incoming_fs = json.loads(candidate["field_sources_json"])
    incoming_evidence = json.loads(candidate["evidence_json"])
    for key in (
        "status",
        "status_as_of",
        "status_date_basis",
        "installed_capacity_mw",
        "operational_capacity_mw",
        "gross_head_m",
        "design_flow_m3_s",
        "basin",
        "owner_names",
        "operator_names",
    ):
        if key not in candidate:
            continue
        if (
            key in row
            and row[key] != candidate[key]
            and key not in {"status", "status_as_of", "status_date_basis"}
        ):
            raise ValueError(f"Existing factual value needs conflict review: {key}")
        row[key] = candidate[key]
        fs[key] = incoming_fs[key]
        evidence[key] = incoming_evidence[key]
    row["sources"] = sorted(set(row["sources"] + candidate["sources"] + [review["source_id"]]))
    # Historical generation and API normal-period generation retain distinct bases.
    observations = json.loads(row.get("observations_json") or "[]")
    for obs in json.loads(candidate.get("observations_json") or "[]"):
        if obs not in observations:
            observations.append(obs)
    combined = {
        "external_ids_json": canonical_json({**ids, **nve_ids}),
        "observations_json": canonical_json(observations),
    }
    ext = json.loads(row.get("extensions_json") or "{}")
    ext["nve_registry"] = json.loads(candidate["extensions_json"])
    ext["identity_review"] = review
    ext["capacity_comparison"] = (
        "WRI historical and NVE current ratings retained separately; differences are not "
        "attributed to uprating. Scope unresolved; excluded from capacity sums."
    )
    combined["extensions_json"] = canonical_json(ext)
    for key, value in combined.items():
        row[key] = value
        fs[key] = row["sources"]
        evidence[key] = {
            "locator": review["locator"],
            "confidence": "high",
            "unit": None,
            "normalization": "Explicit reviewed identity; preserve original observations",
            "original_value": value,
        }
    row["field_sources_json"] = canonical_json(fs)
    row["evidence_json"] = canonical_json(evidence)
    row["notes"] = (
        "NVE identity/lifecycle enriched; historical WRI ratings retained. "
        "Aggregation scope remains unresolved; not included in current capacity sums."
    )
    if {k: v for k, v in row.items() if k not in {"updated_at", "last_verified_at"}} != {
        k: v for k, v in existing.items() if k not in {"updated_at", "last_verified_at"}
    }:
        row["updated_at"] = now
    row["last_verified_at"] = now
    return row
