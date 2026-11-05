"""Offline NVE candidate staging. Never merge source identities by plant name.

Attribution: Norwegian Water Resources and Energy Directorate (NVE), NLOD.
https://api.nve.no/doc/vannkraftdatabase/ documents the source field semantics.
Candidates require an explicit identity review before canonical acceptance.
"""

from __future__ import annotations

import json
import math
from typing import Any

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json

from .catalogue import stable_id
from .gppd import evidence_record


def _number(raw: dict[str, Any], key: str) -> float | None:
    value = raw.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError(f"Invalid numeric {key}")
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"Invalid numeric {key}")
    return value


def parse_nve(
    text: str, *, source_id: str, now: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Stage all generating assets and record exclusions/conflicts by registry ID.

    PK identifies pumped capability, not pure/mixed subtype. P is pump-only and
    cannot supply generating MW. Normal-period generation is not measured annual
    output. API January-1 commissioning dates are retained only as raw metadata.
    Every candidate has unresolved aggregation and remains outside the catalogue.
    """
    payload = json.loads(text)
    if not isinstance(payload, list):
        raise ValueError("Expected NVE JSON array")
    seen: set[int] = set()
    candidates, decisions = [], []
    for index, raw in enumerate(payload):
        external = raw.get("VannKraftverkID")
        if type(external) is not int or external in seen:
            raise ValueError("Missing/duplicate NVE registry ID")
        seen.add(external)
        locator = f"JSON array index {index}; VannKraftverkID={external}"
        decision = {"nve_id": external, "locator": locator}
        if raw.get("VannKVTypeID") == "P":
            decisions.append({**decision, "decision": "excluded_pump_only"})
            continue
        try:
            if raw.get("VannKVTypeID") not in {"K", "PK"} or not raw.get("Navn"):
                raise ValueError("Unknown type or missing name")
            operating = raw.get("ErIDrift")
            retired = raw.get("Kraftverkstatus") == "Ute av drift"
            building = raw.get("UnderBygging")
            if type(operating) is not bool or type(building) is not bool:
                raise ValueError("Missing lifecycle flags")
            if operating and (retired or building):
                raise ValueError("Conflicting lifecycle flags")
            status = (
                "operational"
                if operating
                else "under_construction"
                if building
                else "decommissioned"
                if retired
                else "unknown"
            )
            capacity = _number(raw, "MaksYtelse")
            generation = _number(raw, "MidProd_91_20")
            values = {
                "record_id": stable_id("projects", "NVE", str(external)),
                "entity_type": "projects",
                "record_scope": "plant",
                "name": raw["Navn"],
                "country_code": "NOR",
                "external_ids_json": canonical_json({"nve": str(external)}),
                "aggregation_role": "unresolved",
                "quality_status": "needs_review",
                "capacity_scope": "NVE registry asset; WRI and other catalogue overlap unresolved",
                "status": status,
                "status_as_of": now[:10],
                "status_date_basis": "Retrieval of continuously maintained official NVE API",
                "technology": "pumped_storage" if raw["VannKVTypeID"] == "PK" else "unknown",
                "installed_capacity_mw": capacity if operating else None,
                "operational_capacity_mw": capacity if operating else None,
                "gross_head_m": _number(raw, "BruttoFallhoyde_M"),
                "design_flow_m3_s": _number(raw, "Slukeevne"),
                "basin": raw.get("Nedborsfeltnavn") or None,
                "owner_names": [raw["HovedEier"]] if raw.get("HovedEier") else None,
                "operator_names": sorted(
                    {
                        o["Navn"]
                        for o in raw.get("Eiere", [])
                        if o.get("Driftselskap") and o.get("Navn")
                    }
                )
                or None,
                "observations_json": canonical_json(
                    [
                        {
                            "field": "mean_annual_generation",
                            "value": generation,
                            "unit": "GWh/year",
                            "kind": "modeled",
                            "period": "1991-2020",
                            "boundary": "NVE production referenced to inflow normal period",
                            "source_id": source_id,
                            "locator": locator + "; MidProd_91_20",
                        }
                    ]
                )
                if generation is not None
                else None,
                "extensions_json": canonical_json(
                    {
                        "region": raw.get("Fylke"),
                        "municipality": raw.get("Kommune"),
                        "regine_id": raw.get("RegineNr"),
                        "price_area_number": raw.get("ElspotomraadeNummer"),
                        "commissioning_date_raw": raw.get("IDriftDato"),
                        "commissioning_precision": "unverified; do not treat January 1 as precise",
                        "source_type": raw["VannKVTypeID"],
                        "pumped_subtype": "pure/mixed unresolved"
                        if raw["VannKVTypeID"] == "PK"
                        else None,
                        "reported_maximum_mw": capacity,
                        "head_basis": "Source gross head at 67 percent reservoir filling",
                        "flow_basis": "Maximum turbine water flow, not observed discharge",
                    }
                ),
            }
            candidates.append(
                evidence_record(values, source_id=source_id, now=now, locator=locator)
            )
            decisions.append({**decision, "decision": "candidate_identity_review_required"})
        except ValueError as exc:
            decisions.append({**decision, "decision": "quarantined", "reason": str(exc)})
    return candidates, decisions
