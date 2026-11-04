"""Stage reviewed component tables without manufacturing synthetic variants.

Input is a human-reviewed factual transcription, not a PDF text extractor.
Document hashes and complete row sets are checked before any model is staged.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json

from .catalogue import stable_id
from .gppd import evidence_record

REFERENCE_IDS = ("mnre_almm_wtc_20260602",)


def stage_components(
    documents: list[dict[str, Any]],
    originals: dict[str, bytes],
    existing: list[dict[str, Any]],
    *,
    now: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Stage exact transcribed models and explicit turbine links, with decisions.

    Missing model identifiers remain deferred. Ratings, geometry and compatibility
    cannot be inferred from type codes, turbine power or supplier names. Multiple
    factories and supported turbine configurations remain nested in one model.
    Existing identities are deferred for an explicit revision reconciliation.
    """
    targets = {r["record_id"]: r for r in existing}
    prior = {
        (r.get("manufacturer"), r.get("model")) for r in existing if r["entity_type"] == "equipment"
    }
    collected: dict[tuple[str, str], list[dict[str, Any]]] = {}
    ledger = []
    seen = set()
    allowed = {
        "blade_length_m",
        "rated_power_kw",
        "rated_power_conditions",
        "gearbox_type",
        "generator_type",
    }
    for doc in documents:
        sid = doc["source_id"]
        if sid in seen:
            raise ValueError("Duplicate document")
        seen.add(sid)
        if hashlib.sha256(originals[sid]).hexdigest() != doc["sha256"]:
            raise ValueError("Original document checksum mismatch")
        slots = doc["rows"]
        if len(slots) != len(doc["expected_rows"]) or {s["row"] for s in slots} != set(
            doc["expected_rows"]
        ):
            raise ValueError("Incomplete or duplicate document rows")
        for slot in slots:
            decision = {"source_id": sid, "row": slot["row"], "locator": slot["locator"]}
            if not slot["models"]:
                ledger.append(
                    {
                        **decision,
                        "decision": "deferred",
                        "reason": slot.get("defer_reason") or "No exact component model identifier",
                        "observation": slot["observation"],
                    }
                )
                continue
            ids = []
            for model in slot["models"]:
                if not model["manufacturer"] or not model["model"] or not model["links"]:
                    raise ValueError("Exact identity and explicit application required")
                if model["category"] not in {"blade", "gearbox", "generator", "converter"}:
                    raise ValueError("Unsupported reviewed component category")
                if set(model.get("values", {})) - allowed:
                    raise ValueError("Unsupported specification field")
                if "rated_power_kw" in model.get("values", {}) and not model["values"].get(
                    "rated_power_conditions"
                ):
                    raise ValueError("Power requires a mechanical/electrical boundary")
                for link in model["links"]:
                    target = targets.get(link["equipment_record_id"], {})
                    if target.get("equipment_category") != "wind_turbine" or not link["conditions"]:
                        raise ValueError(
                            "Compatibility requires an existing exact turbine and conditions"
                        )
                key = (model["manufacturer"], model["model"])
                if key in prior:
                    ledger.append(
                        {
                            **decision,
                            "decision": "existing_identity_review",
                            "manufacturer": key[0],
                            "model": key[1],
                        }
                    )
                    continue
                rid = stable_id("equipment", "documented-component", *key)
                ids.append(rid)
                collected.setdefault(key, []).append(
                    {
                        "source_id": sid,
                        "locator": slot["locator"],
                        "revision": doc["revision"],
                        **model,
                    }
                )
            if ids:
                ledger.append(
                    {**decision, "decision": "staged_exact_models", "record_ids": sorted(ids)}
                )
    records = []
    for (maker, model), observations in collected.items():
        first = observations[0]
        values = dict(first.get("values", {}))
        if any(
            o["category"] != first["category"] or o.get("values", {}) != values
            for o in observations
        ):
            raise ValueError("Conflicting component specifications require reconciliation")
        sources = sorted({o["source_id"] for o in observations})
        links = [
            {**link, "source_id": o["source_id"], "locator": o["locator"]}
            for o in observations
            for link in o["links"]
        ]
        row = evidence_record(
            {
                "record_id": stable_id("equipment", "documented-component", maker, model),
                "entity_type": "equipment",
                "record_scope": "configuration",
                "name": f"{maker} {model}",
                "manufacturer": maker,
                "model": model,
                "equipment_category": first["category"],
                "variant": (
                    "Exact disclosed type; manufacturing sites and turbine applications nested"
                ),
                "capacity_scope": (
                    "Exact component type; turbine application ratings are not component ratings"
                ),
                "compatibility_json": canonical_json(links),
                "extensions_json": canonical_json({"component_disclosures": observations}),
                "source_revision": "; ".join(sorted({o["revision"] for o in observations})),
                "notes": (
                    "Dated manufacturer-submitted disclosures; no current certification or "
                    "independent operational validation. Unreported geometry, rating, mass and "
                    "lifecycle remain null. Multiple listed factories do not create model variants."
                ),
                **values,
            },
            source_id=first["source_id"],
            now=now,
            locator=first["locator"],
        )
        row["sources"] = sources
        evidence = json.loads(row["evidence_json"])
        field_sources = json.loads(row["field_sources_json"])
        for field in evidence:
            field_sources[field] = sources
            evidence[field]["document_observations"] = [
                {"source_id": o["source_id"], "locator": o["locator"], "revision": o["revision"]}
                for o in observations
            ]
        row["evidence_json"] = canonical_json(evidence)
        row["field_sources_json"] = canonical_json(field_sources)
        records.append(row)
    return sorted(records, key=lambda r: r["record_id"]), ledger
