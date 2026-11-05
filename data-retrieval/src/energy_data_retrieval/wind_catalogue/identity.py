"""Conservative EIA identity review signals, never automatic additions or merges."""

from __future__ import annotations

import difflib
import json
import math
import re
import unicodedata
from typing import Any

_STOP = frozenset(
    [
        "wind",
        "windfarm",
        "windpower",
        "farm",
        "farms",
        "energy",
        "project",
        "llc",
        "ltd",
        "power",
        "center",
        "facility",
        "inc",
        "lp",
        "corp",
        "renewable",
        "generation",
        "the",
        "company",
    ]
)


def distinctive_name(value: str) -> str:
    """Remove generic site/legal words, retaining phase numbers and directions."""
    plain = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    return " ".join(w for w in re.sub(r"[^a-z0-9 ]", " ", plain).split() if w not in _STOP)


def _point(lat: Any, lon: Any) -> tuple[float, float] | None:
    if lat is None or lon is None or isinstance(lat, bool) or isinstance(lon, bool):
        return None
    try:
        lat, lon = float(lat), float(lon)
    except (ValueError, TypeError):
        return None
    if not math.isfinite(lat) or not math.isfinite(lon) or abs(lat) > 90 or abs(lon) > 180:
        return None
    return lat, lon


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 6371.0088 * 2 * math.asin(math.sqrt(min(1.0, h)))


def screen_eia_sites(
    candidates: list[dict[str, Any]], existing: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Return registry, name, alias and 10-km point flags for manual review.

    Distinctive-name similarity >=0.8 is a triage threshold, not identity proof.
    Missing coordinates, phases and cohort neighbours remain visible. No record
    is accepted, merged or assigned a farm boundary by this function.
    """
    codes = [c["plant_code"] for c in candidates]
    if len(set(codes)) != len(codes) or any(type(c) is not int or c <= 0 for c in codes):
        raise ValueError("Require unique positive EIA plant codes")
    projects = [
        r for r in existing if r["entity_type"] == "projects" and r["country_code"] == "USA"
    ]
    result = []
    for c in candidates:
        code, name = c["plant_code"], distinctive_name(c["name"])
        p = _point(c["plant_context"]["Latitude"], c["plant_context"]["Longitude"])
        ids, names, nearby, peers = [], [], [], []
        for r in projects:
            external = json.loads(r.get("external_ids_json") or "{}")
            if (
                str(external.get("eia_plant_code")) == str(code)
                or external.get("wri_gppd") == f"USA{code:07d}"
            ):
                ids.append(r["record_id"])
            for alias in [r["name"], *r.get("aliases", [])]:
                other = distinctive_name(alias)
                ratio = difflib.SequenceMatcher(None, name, other).ratio()
                if name and other and ratio >= 0.8:
                    names.append(
                        {
                            "record_id": r["record_id"],
                            "matched_name": alias,
                            "ratio": round(ratio, 4),
                        }
                    )
            q = _point(r.get("latitude"), r.get("longitude"))
            if p and q and (distance := _distance(p, q)) <= 10:
                nearby.append({"record_id": r["record_id"], "distance_km": round(distance, 4)})
        for peer in candidates:
            if peer["plant_code"] == code:
                continue
            other = distinctive_name(peer["name"])
            q = _point(peer["plant_context"]["Latitude"], peer["plant_context"]["Longitude"])
            similar = bool(
                name and other and difflib.SequenceMatcher(None, name, other).ratio() >= 0.8
            )
            near = bool(p and q and _distance(p, q) <= 10)
            if similar or near:
                peers.append(
                    {"plant_code": peer["plant_code"], "similar_name": similar, "nearby": near}
                )
        result.append(
            {
                "plant_code": code,
                "name": c["name"],
                "distinctive_name": name,
                "existing_registry_ids": sorted(ids),
                "name_matches": names,
                "nearby_projects": nearby,
                "cohort_peers": peers,
                "missing_coordinate": p is None,
                "phase_or_direction_flag": bool(
                    re.search(
                        r"\b([ivx]+|\d+|repower\w*|phase|hybrid|east|west|north|south)\b",
                        c["name"],
                        re.I,
                    )
                ),
                "empty_distinctive_name": not name,
                "decision": "manual_review_required",
            }
        )
    return result
