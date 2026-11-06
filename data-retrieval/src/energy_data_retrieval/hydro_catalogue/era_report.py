"""Retain reviewed regulator historical assertions with explicit equipment boundaries."""

import copy
import json
import re
from typing import Any

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json

SOURCE_ID = "uganda-era-environment-2023"


def enrich_reviewed(existing: dict[str, Any], entry: dict[str, Any], *, now: str) -> dict[str, Any]:
    """Append dated regulator assertions without resolving current fields or conflicts."""
    if (
        existing["record_id"] != entry["record_id"]
        or existing["country_code"] != "UGA"
        or existing["name"] != entry["name"]
        or entry.get("decision") != "reviewed_regulator_assertions"
    ):
        raise ValueError("Explicit regulator identity review required")
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
            "Regulator statements; dates/boundaries retained; no additive rating or current status"
        ),
    }
    if "era_2023_assertions" in ext:
        if ext["era_2023_assertions"] != assertions:
            raise ValueError("Changed technical evidence requires conflict review")
        return row
    ext["era_2023_assertions"] = assertions
    fs, ev = json.loads(row["field_sources_json"]), json.loads(row["evidence_json"])
    row["extensions_json"] = canonical_json(ext)
    fs["extensions_json"] = sorted(set([*fs.get("extensions_json", []), SOURCE_ID]))
    ev["extensions_json"] = {
        "locator": "ERA Annex 3 station row; per-assertion locators retained",
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


def parse_annex(text: str) -> dict[str, dict[str, Any]]:
    """Parse Annex 3's two bounded hydro tables from pdftotext -layout output.

    Commissioning precision and the joint construction/licensed group are retained.
    No planned capacity is mapped to installed capacity.
    """
    start = text.rfind("Operational Hydropower Projects")
    if start < 0:
        raise ValueError("Missing operational hydro table")
    operational, tail = text[start:].split(
        "Hydropower Projects Under Construction or Licensed to Start Construction", 1
    )
    construction = tail.split("Hydropower Projects Undergoing Feasibility Studies", 1)[0]
    result = {}
    patterns = [
        (
            operational,
            r"^\s*(.*?)\s{2,}(\d{4}s?)\s+([\d.]+)\s+(On-grid|Off-grid)\s*$",
            "operational",
        ),
        (
            construction,
            r"^\s*(.*?)\s{2,}([\d.]+)\s+(On-grid|Off-grid)\s*$",
            "construction_or_licensed",
        ),
    ]
    for block, pattern, status in patterns:
        for match in re.finditer(pattern, block, re.MULTILINE):
            parts = match.groups()
            name = parts[0].rstrip("*")
            if name in result:
                raise ValueError("Duplicate Annex identity")
            result[name] = dict(
                commissioning=parts[1] if status == "operational" else None,
                capacity_mw=float(parts[-2]),
                grid=parts[-1],
                lifecycle_group=status,
            )
    if len(result) != 59:
        raise ValueError(f"Unexpected Annex row count: {len(result)}")
    return result
