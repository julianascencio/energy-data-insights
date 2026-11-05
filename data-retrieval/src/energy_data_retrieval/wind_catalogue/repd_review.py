"""Bounded, offline review of saved REPD application identities, never farm import."""

from __future__ import annotations

import csv
import hashlib
import io
from typing import Any

REASON = "No unique explicit WRI crosswalk; review as a separate application/phase candidate"
FIELDS = (
    "Site Name",
    "Technology Type",
    "Development Status",
    "Planning Authority",
    "Planning Application Reference",
    "Appeal Reference",
    "Secretary of State Reference",
    "Are they re-applying (New REPD Ref)",
    "Are they re-applying (Old REPD Ref) ",
)


def review_unlinked_applications(
    original: bytes,
    decisions: list[dict[str, Any]],
    *,
    sha256: str,
    offset: int,
    limit: int,
) -> list[dict[str, Any]]:
    """Return review facts in saved ledger order, retaining all identity holds.

    The checksum pins the Windows-1252 release. Offsets apply only to the exact
    unresolved-crosswalk reason, not all decisions. Empty cells are unknown;
    application IDs and replacement references do not establish physical farms.
    No lifecycle, capacity, coordinate or equipment scalar is assigned.
    """
    if hashlib.sha256(original).hexdigest() != sha256:
        raise ValueError("REPD checksum mismatch")
    if type(offset) is not int or type(limit) is not int or offset < 0 or limit <= 0:
        raise ValueError("Invalid partition bounds")
    candidates = [d for d in decisions if d.get("reason") == REASON]
    ids = [d["repd_id"] for d in candidates]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate saved candidate ID")
    reader = csv.DictReader(io.StringIO(original.decode("cp1252")))
    if not {"Ref ID", *FIELDS} <= set(reader.fieldnames or []):
        raise ValueError("Missing REPD review headers")
    rows: dict[str, tuple[int, dict[str, str]]] = {}
    for line, raw in enumerate(reader, 2):
        ref = raw["Ref ID"]
        if ref in rows:
            raise ValueError("Duplicate release ID")
        rows[ref] = (line, raw)
    result = []
    for decision in candidates[offset : offset + limit]:
        ref = decision["repd_id"]
        if ref not in rows:
            raise ValueError("Saved candidate missing from pinned release")
        line, raw = rows[ref]
        if raw["Site Name"] != decision["name"] or raw["Technology Type"] not in {
            "Wind Onshore",
            "Wind Offshore",
        }:
            raise ValueError("Saved candidate differs from release identity")
        result.append(
            dict(
                repd_id=ref,
                locator=f"CSV record {line}; Ref ID={ref}",
                source_id=decision["source_id"],
                decision="deferred_identity",
                reason=REASON,
                facts={field: raw[field].strip() or None for field in FIELDS},
                scope="Planning application only; no farm identity or current-status inference",
            )
        )
    return result
