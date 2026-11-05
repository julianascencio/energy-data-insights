"""Review checksum-pinned FGW reference-yield tables without synthesizing variants.

A table row is one modeled reference-site/hub/power observation, never an installed
machine or measured generation. Exact identity mappings are reviewed externally.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from typing import Any

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json

from .gppd import evidence_record


def stage_reference_yields(
    document: dict[str, Any], original: bytes, existing: list[dict[str, Any]], *, now: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Apply a complete reviewed table with immutable source-bounded observations.

    Original units and note restrictions travel with each row. Unknown diameter,
    density or operating mode stays null. Repeated hubs and power settings do not
    create equipment identities. Existing scalar facts and creation times survive.
    """
    if hashlib.sha256(original).hexdigest() != document["sha256"]:
        raise ValueError("Original checksum mismatch")
    slots = document["rows"]
    keys = [s["row"] for s in slots]
    if not keys or len(set(keys)) != len(keys) or sorted(keys) != sorted(document["expected_rows"]):
        raise ValueError("Incomplete or duplicate reference table rows")
    if not document.get("source_id") or not document.get("revision"):
        raise ValueError("Require source and revision boundary")
    conditions = document["reference_conditions"]
    if not conditions.get("profile") or document.get("period_years") != 5:
        raise ValueError("Require explicit reference site and five-year period")
    if not document.get("period_source_id"):
        raise ValueError("Require reference-period provenance")
    groups: dict[str, list[dict[str, Any]]] = {}
    identities: dict[str, dict[str, Any]] = {}
    ledger = []
    for slot in slots:
        for field in ("rated_power_kw", "hub_height_m", "rotor_area_m2", "reference_yield_kwh"):
            v = slot[field]
            if (
                isinstance(v, bool)
                or not isinstance(v, (int, float))
                or not math.isfinite(v)
                or v <= 0
            ):
                raise ValueError("Nonpositive/nonfinite reference quantity")
        d = slot.get("rotor_diameter_m")
        if d is not None and (not math.isfinite(d) or d <= 0):
            raise ValueError("Invalid rotor diameter")
        if not all(slot.get(k) for k in ("locator", "type_label", "note", "original_values")):
            raise ValueError("Require original values, locator and note restriction")
        if slot["decision"] == "deferred_conflict":
            if not slot.get("reason"):
                raise ValueError("Require deferral reason")
            ledger.append({k: slot[k] for k in ("row", "type_label", "decision", "reason")})
            continue
        if slot["decision"] not in ("addition", "enrichment"):
            raise ValueError("Unreviewed row decision")
        identity = slot["identity"]
        rid = identity["record_id"]
        if not all(identity.get(k) for k in ("record_id", "model", "manufacturer", "variant")):
            raise ValueError("Require exact reviewed equipment identity")
        if rid in identities and identities[rid] != identity:
            raise ValueError("Inconsistent reviewed identity")
        identities[rid] = identity
        groups.setdefault(rid, []).append(slot)
        ledger.append(
            dict(
                row=slot["row"],
                type_label=slot["type_label"],
                record_id=rid,
                decision=slot["decision"],
                withdrawn=slot.get("withdrawn", False),
            )
        )
    by_id = {r["record_id"]: r for r in existing}
    if len(by_id) != len(existing):
        raise ValueError("Duplicate existing identity")
    result = []
    for rid, group in groups.items():
        identity = identities[rid]
        sid = document["source_id"]
        observation = {
            "source_id": sid,
            "published_at": document.get("published_at"),
            "revision": document["revision"],
            "reference_site": document["reference_site"],
            "reference_conditions": conditions,
            "period_years": 5,
            "period_source_id": document["period_source_id"],
            "quantity_kind": "modeled reference energy",
            "unit": "kWh",
            "boundary": (
                "One turbine at a hypothetical reference site for five years; gross/net unspecified"
            ),
            "validation_status": (
                "Published calculated reference yield; "
                "not independently validated field performance"
            ),
            "rows": [
                {k: v for k, v in g.items() if k not in ("identity", "decision")} for g in group
            ],
        }
        if rid in by_id:
            row = copy.deepcopy(by_id[rid])
            if (
                any(
                    row.get(k) != identity.get(k)
                    for k in (
                        "manufacturer",
                        "model",
                        "variant",
                        "rated_power_kw",
                        "rotor_diameter_m",
                    )
                )
                or row["entity_type"] != "equipment"
            ):
                raise ValueError("Reviewed configuration identity mismatch")
        else:
            if any(g["decision"] != "addition" for g in group):
                raise ValueError("Enrichment target missing")
            for field in ("rated_power_kw", "rotor_diameter_m"):
                if any(g.get(field) is not None and g[field] != identity.get(field) for g in group):
                    raise ValueError("New identity cannot substitute conflicting table scalars")
            row = evidence_record(
                dict(
                    **identity,
                    entity_type="equipment",
                    record_scope="model",
                    name=f"{identity['manufacturer']} {identity['model']} ({identity['variant']})",
                    equipment_category="wind_turbine",
                    rated_power_conditions=(
                        "FGW printed type nameplate; density and operating mode undisclosed"
                    ),
                    capacity_scope=(
                        "Exact printed type/revision; hub options are nested reference calculations"
                    ),
                ),
                source_id=sid,
                now=now,
                locator="; ".join(g["locator"] for g in group),
            )
        ext = json.loads(row.get("extensions_json") or "{}")
        observations = ext.setdefault("reference_yield_observations", [])
        prior = [o for o in observations if o["source_id"] == sid]
        if prior:
            if prior != [observation]:
                raise ValueError("Immutable reference observation changed")
            result.append(row)
            continue
        observations.append(observation)
        sources = sorted({*row["sources"], sid, document["period_source_id"]})
        fs = json.loads(row["field_sources_json"])
        ev = json.loads(row["evidence_json"])
        fs["extensions_json"] = sorted(
            {*fs.get("extensions_json", []), sid, document["period_source_id"]}
        )
        ev["extensions_json"] = dict(
            prior_observation=ev.get("extensions_json"),
            source_id=sid,
            locator="; ".join(g["locator"] for g in group),
            confidence="high",
            normalization=(
                "German decimal commas/thousands dots parsed; "
                "original strings retained; no annualization"
            ),
        )
        row.update(
            extensions_json=canonical_json(ext),
            field_sources_json=canonical_json(fs),
            evidence_json=canonical_json(ev),
            sources=sources,
            updated_at=now,
            last_verified_at=now,
        )
        result.append(row)
    return sorted(result, key=lambda x: x["record_id"]), ledger
