"""Retain reviewed owner technical assertions with explicit equipment boundaries."""

import copy
import json
from typing import Any

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json

SOURCE_ID = "kengen-technical-20261106"


def enrich_reviewed(existing: dict[str, Any], entry: dict[str, Any], *, now: str) -> dict[str, Any]:
    """Append source assertions; never sum replacement units or promote current MW.

    MVA remains apparent power. Unqualified head remains unqualified. A stated
    commissioning year is an owner assertion, not a resolution of conflicting
    historical dates. A water volume never becomes storage energy.
    """
    if (
        existing["record_id"] != entry["record_id"]
        or existing["country_code"] != "KEN"
        or existing["name"] != entry["name"]
        or entry.get("decision") != "reviewed_owner_assertions"
    ):
        raise ValueError("Explicit owner identity review required")
    facts = entry["facts"]
    required = {"key", "value", "unit", "basis", "locator", "uncertainty"}
    if not facts or any(
        not required <= f.keys() or not f["basis"] or not f["locator"] for f in facts
    ):
        raise ValueError("Require complete field provenance")
    if len({f["key"] for f in facts}) != len(facts):
        raise ValueError("Duplicate technical assertion key")
    row = copy.deepcopy(existing)
    ext = json.loads(row["extensions_json"])
    assertions = {
        "source_id": SOURCE_ID,
        "facts": facts,
        "scope": (
            "Owner statements; dates/boundaries retained; no additive rating or current status"
        ),
    }
    if "kengen_technical_assertions" in ext:
        if ext["kengen_technical_assertions"] != assertions:
            raise ValueError("Changed technical evidence requires conflict review")
        return row
    ext["kengen_technical_assertions"] = assertions
    fs, ev = json.loads(row["field_sources_json"]), json.loads(row["evidence_json"])
    row["extensions_json"] = canonical_json(ext)
    fs["extensions_json"] = sorted(set([*fs.get("extensions_json", []), SOURCE_ID]))
    ev["extensions_json"] = {
        "locator": "Named owner station section; per-assertion locators retained",
        "confidence": "high",
        "original_value": row["extensions_json"],
        "normalization": "Source assertions only; no current rating or date conflict resolution",
    }
    row.update(
        field_sources_json=canonical_json(fs),
        evidence_json=canonical_json(ev),
        sources=sorted(set(row["sources"] + [SOURCE_ID])),
        updated_at=now,
        last_verified_at=now,
    )
    return row
