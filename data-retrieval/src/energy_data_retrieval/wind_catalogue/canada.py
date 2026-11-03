"""Offline NRCan inventory reconciliation; no current-status or scope inference."""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from typing import Any

REFERENCE_IDS = ("nrcan_wind_turbine_database_2026",)


def normalized_name(value: str) -> str:
    """Normalize a name for candidate screening, never as sole identity evidence."""
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    for phrase in ("wind farm", "wind power", "wind project"):
        value = value.replace(phrase, "")
    return re.sub("[^a-z0-9]", "", value)


def reconcile_group(
    rows: list[dict[str, Any]], existing: list[dict[str, Any]]
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Corroborate one province/name group and retain a bounded inventory summary.

    Require a unique normalized Canadian project name, every turbine within 10 km
    of the historical project coordinate and capacity agreement within 1% (0.1 MW
    floor). These checks do not resolve phases, repowering or current operation.
    Duplicate identifiers block acceptance, rather than inflate fleet counts.
    """
    if not rows:
        raise ValueError("Empty inventory group")
    name = rows[0]["Project Name"]
    province = rows[0]["Province_Territory"]
    if any((r["Project Name"], r["Province_Territory"]) != (name, province) for r in rows):
        raise ValueError("Mixed inventory groups")
    decision: dict[str, Any] = {"name": name, "province": province, "decision": "deferred"}
    candidates = [
        r
        for r in existing
        if r.get("country_code") == "CAN" and normalized_name(r["name"]) == normalized_name(name)
    ]
    if len(candidates) != 1:
        return None, {**decision, "reason": "No unique name candidate"}
    old = candidates[0]
    decision["record_id"] = old["record_id"]
    identifiers = [r.get("Turbine Identifier") for r in rows]
    if any(not i for i in identifiers) or len(identifiers) != len(set(identifiers)):
        return None, {**decision, "reason": "Missing or repeated turbine identifiers within group"}
    capacities = {r.get("Total Project Capacity (MW)") for r in rows}
    historical = old.get("historical_capacity_mw")
    if len(capacities) != 1 or None in capacities or historical is None:
        return None, {**decision, "reason": "Missing or conflicting project capacity"}
    raw_capacity = next(iter(capacities))
    assert raw_capacity is not None
    capacity = float(raw_capacity)
    if (
        not math.isfinite(capacity)
        or capacity < 0
        or abs(capacity - historical) > max(0.1, historical * 0.01)
    ):
        return None, {**decision, "reason": "Historical and inventory capacity mismatch"}
    distances = []
    for row in rows:
        lat, lon = row.get("Latitude"), row.get("Longitude")
        if (
            lat is None
            or lon is None
            or old.get("latitude") is None
            or old.get("longitude") is None
        ):
            return None, {**decision, "reason": "Missing coordinate corroboration"}
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return None, {**decision, "reason": "Invalid coordinate"}
        a, b = math.radians(lat), math.radians(old["latitude"])
        delta = math.radians(lon - old["longitude"])
        h = math.sin((a - b) / 2) ** 2 + math.cos(a) * math.cos(b) * math.sin(delta / 2) ** 2
        distances.append(6371.0088 * 2 * math.asin(math.sqrt(min(1, max(0, h)))))
    if max(distances) > 10:
        return None, {
            **decision,
            "reason": "At least one turbine exceeds 10 km coordinate boundary",
        }
    fields = (
        "Manufacturer",
        "Model",
        "Turbine Rated Capacity (kW)",
        "Rotor Diameter (m)",
        "Hub Height (m)",
        "Commissioning",
    )
    fleets = Counter(tuple(r.get(k) for k in fields) for r in rows)
    summary = {
        "source_project_name": name,
        "province": province,
        "reported_project_capacity_mw": capacity,
        "inventory_turbine_rows": len(rows),
        "reported_turbine_counts": sorted(
            {
                r["Number of Turbines in Project"]
                for r in rows
                if r.get("Number of Turbines in Project") is not None
            }
        ),
        "fleet_groups": [
            {**dict(zip(fields, values, strict=True)), "inventory_count": count}
            for values, count in fleets.items()
        ],
        "fleet_completeness": "unknown; inventory snapshot is not a current asset census",
        "maximum_distance_to_historical_coordinate_km": round(max(distances), 4),
        "identity_basis": (
            "unique normalized name + all coordinates within 10 km + capacity tolerance"
        ),
        "scope_note": "Phase, repowering, lifecycle and aggregation eligibility unchanged",
    }
    return summary, {**decision, "decision": "enriched", "reason": summary["identity_basis"]}
