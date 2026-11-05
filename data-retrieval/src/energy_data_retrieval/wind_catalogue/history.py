"""Stage complete, reviewed OEM history tables without inventing model variants.

The input is a factual transcription checked against original pages. This adapter
checks the original checksum and row inventory; it does not extract PDF layout.
"""

from __future__ import annotations

import hashlib
import math
from typing import Any

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json

from .catalogue import stable_id
from .gppd import evidence_record


def stage_history(
    document: dict[str, Any], original: bytes, existing: list[dict[str, Any]], *, now: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return new exact types and all row decisions; preserve ranges and conflicts.

    A reviewed identity suffix distinguishes explicitly printed rating versions.
    It must not encode a Cartesian combination of optional towers or operating modes.
    Existing models require separate revision review and are never overwritten.
    """
    if hashlib.sha256(original).hexdigest() != document["sha256"]:
        raise ValueError("Original checksum mismatch")
    slots = document["rows"]
    if len(slots) != len(document["expected_rows"]) or {s["row"] for s in slots} != set(
        document["expected_rows"]
    ):
        raise ValueError("Incomplete or duplicate table rows")
    prior = {
        (r.get("manufacturer"), r.get("model")) for r in existing if r["entity_type"] == "equipment"
    }
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    ledger = []
    for slot in slots:
        decision = {"row": slot["row"], "locator": slot["locator"], "type": slot["model"]}
        if slot.get("hold_reason"):
            ledger.append(
                {**decision, "decision": "deferred_conflict", "reason": slot["hold_reason"]}
            )
            continue
        if (slot["manufacturer"], slot["model"]) in prior:
            ledger.append({**decision, "decision": "existing_model_revision_review"})
            continue
        key = (slot["manufacturer"], slot["model"], slot["identity_suffix"])
        if not all(key) or not slot["locator"]:
            raise ValueError("Require reviewed exact type identity and locator")
        for field in ("rated_power_kw", "rotor_diameter_m"):
            value = slot.get(field)
            if value is not None and (not math.isfinite(value) or value <= 0):
                raise ValueError("Nonpositive/nonfinite specification")
        groups.setdefault(key, []).append(slot)
        ledger.append(
            {**decision, "decision": "addition_or_same_type_observation", "identity": key}
        )
    records = []
    for (maker, model, suffix), observations in groups.items():
        powers = {o.get("rated_power_kw") for o in observations}
        diameters = {o["rotor_diameter_m"] for o in observations}
        if len(powers) != 1 or len(diameters) != 1:
            raise ValueError("Conflicting same-type observations require review")
        records.append(
            evidence_record(
                dict(
                    record_id=stable_id("equipment", "reviewed-oem-history", maker, model, suffix),
                    entity_type="equipment",
                    record_scope="model",
                    name=f"{maker} {model} ({suffix})",
                    manufacturer=maker,
                    model=model,
                    variant=suffix,
                    equipment_category="wind_turbine",
                    rotor_diameter_m=next(iter(diameters)),
                    rated_power_kw=next(iter(powers)),
                    rated_power_conditions=(
                        "OEM history table type capacity; operating mode, density and "
                        "rating standard unspecified; not field-validated performance"
                    ),
                    capacity_scope=(
                        "Exact printed type/rating identity; "
                        "optional towers remain nested observations"
                    ),
                    extensions_json=canonical_json(
                        {
                            "oem_history_observations": observations,
                            "publication_date": document.get("published_at"),
                            "revision": document.get("revision"),
                            "source_id": document["source_id"],
                            "year_semantics": (
                                "OEM table Year column; not assumed certification, "
                                "manufacture or installation date"
                            ),
                            "product_status_semantics": (
                                "Historical/current headings belong to an undated "
                                "document, not a current availability guarantee"
                            ),
                        }
                    ),
                ),
                source_id=document["source_id"],
                now=now,
                locator="; ".join(o["locator"] for o in observations),
            )
        )
    return sorted(records, key=lambda r: r["record_id"]), ledger
