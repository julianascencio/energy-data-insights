"""Offline review staging for a bounded public Danish municipal PV-plan projection.

A municipal plan is not a generating asset, licence or operating installation.
No canonical records or automatic crosswalks are produced here.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

FIELDS = {"planid", "plannr", "plannavn", "komnr", "datovedt", "status", "datoopdt"} | {
    f"{prefix}{i}" for prefix in ["anvspec", "plankap"] for i in range(1, 11)
}


def read_pv_plan_projection(content: bytes, *, sha256: str) -> list[dict[str, Any]]:
    """Verify pinned projection/schema/IDs and stage explicit8135 plans for review."""
    if hashlib.sha256(content).hexdigest() != sha256:
        raise ValueError("Source checksum changed")
    data = json.loads(content)
    features = data.get("features", [])
    if data.get("type") != "FeatureCollection" or data.get("numberReturned") != len(features):
        raise ValueError("Feature count/type mismatch")
    if not features or len(features) > 100:
        raise ValueError("Expected a bounded partition of 1 to 100 features")
    datetime.fromisoformat(data["timeStamp"].replace("Z", "+00:00"))
    seen = set()
    rows = []
    for feature in features:
        p = feature["properties"]
        if set(p) != FIELDS or feature.get("geometry") is not None:
            raise ValueError("Unexpected projection or geometry; no private fields permitted")
        identifier = p["planid"]
        if not isinstance(identifier, int) or identifier <= 0 or identifier in seen:
            raise ValueError("Missing/repeated plan ID; review source grouping")
        seen.add(identifier)
        slots = [i for i in range(1, 11) if p[f"anvspec{i}"] == 8135]
        if not slots or p["status"] != "V":
            raise ValueError("Not an explicitly classified adopted PV plan")
        date = p["datovedt"]
        if date not in {None, 19000101}:
            datetime.strptime(str(date), "%Y%m%d")
        rows.append(
            {
                "plan_id": identifier,
                "municipality_code": p["komnr"],
                "public_plan_name": p["plannavn"],
                "adoption_native": date,
                "source_updated_native": p["datoopdt"],
                "response_timestamp": data["timeStamp"],
                "pv_slots": slots,
                "planned_capacity_cells_native": [p[f"plankap{i}"] for i in slots],
                "review_flags": [
                    "Municipal plan boundary is not a canonical project identity",
                    "Adoption is not construction, commissioning or current operation",
                    "Capacity units/basis and mixed uses need original plan evidence",
                    *(["Sentinel/missing adoption date"] if date in {None, 19000101} else []),
                ],
            }
        )
    return rows
