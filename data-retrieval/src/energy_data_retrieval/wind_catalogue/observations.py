"""Attach reviewed dated OEM observations without replacing configuration facts."""

from __future__ import annotations

import copy
import datetime
import hashlib
import json
from typing import Any

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json


def enrich_oem_history(
    document: dict[str, Any], original: bytes, existing: list[dict[str, Any]], *, now: str
) -> list[dict[str, Any]]:
    """Apply an explicit record-ID/model crosswalk and checksum-pinned transcription.

    Observations describe their historical boundary and original units. The caller
    reviews every mapping; neither model-name similarity nor table position creates
    an identity. Scalar specifications, aliases and creation times are preserved.
    Replaying identical observations is idempotent; changing the same dated source
    on an existing record raises instead of silently replacing the observation.
    """
    if hashlib.sha256(original).hexdigest() != document["sha256"]:
        raise ValueError("OEM original checksum mismatch")
    datetime.date.fromisoformat(document["published_at"])
    source = document["source_id"]
    if not source or not document.get("revision"):
        raise ValueError("Require source identity and revision boundary")
    entries = document["entries"]
    ids = [e["record_id"] for e in entries]
    if (
        not ids
        or len(set(ids)) != len(ids)
        or sorted(ids) != sorted(document["expected_record_ids"])
    ):
        raise ValueError("Incomplete or duplicate reviewed mapping")
    by_id = {x["record_id"]: x for x in existing}
    if len(by_id) != len(existing):
        raise ValueError("Duplicate catalogue identity")
    result = []
    for e in entries:
        row = copy.deepcopy(by_id[e["record_id"]])
        if (row["entity_type"], row["manufacturer"], row["model"]) != (
            "equipment",
            e["manufacturer"],
            e["model"],
        ) or row.get("rated_power_kw") != e["identity_rated_power_kw"]:
            raise ValueError("Reviewed configuration identity mismatch")
        if not e.get("locator") or not e.get("boundary") or not e.get("facts"):
            raise ValueError("Require locator, boundary and substantive facts")
        observation = {
            "source_id": source,
            "published_at": document["published_at"],
            "revision": document["revision"],
            "locator": e["locator"],
            "boundary": e["boundary"],
            "facts": e["facts"],
            "normalization": e.get(
                "normalization", "Original units retained; no scalar substitution"
            ),
            "confidence": "high",
            "validation_status": "OEM statement; not independently validated performance",
        }
        ext = json.loads(row.get("extensions_json") or "{}")
        history = ext.setdefault("oem_historical_observations", [])
        prior = [o for o in history if o["source_id"] == source]
        if prior:
            if prior != [observation]:
                raise ValueError("Immutable OEM observation changed")
            result.append(row)
            continue
        history.append(observation)
        fs = json.loads(row["field_sources_json"])
        ev = json.loads(row["evidence_json"])
        fs["extensions_json"] = sorted(set([*fs.get("extensions_json", []), source]))
        ev["extensions_json"] = {
            "prior_observation": ev.get("extensions_json"),
            "source_id": source,
            "locator": e["locator"],
            "confidence": "high",
            "normalization": "Dated nested historical observation; prior scalar facts preserved",
        }
        row.update(
            extensions_json=canonical_json(ext),
            field_sources_json=canonical_json(fs),
            evidence_json=canonical_json(ev),
            sources=sorted(set([*row["sources"], source])),
            updated_at=now,
            last_verified_at=now,
        )
        result.append(row)
    return sorted(result, key=lambda x: x["record_id"])
