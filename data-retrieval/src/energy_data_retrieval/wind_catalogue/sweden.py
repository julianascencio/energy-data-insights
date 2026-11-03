"""Offline Vindbrukskollen GeoJSON adapter for explicit project/turbine identities.

Inputs are complete, bounded MapServer queries in EPSG:4326. Registry erection
status is not evidence of operation. Area counts and turbine maximum MW remain
inventory observations, never reported installed or export project capacity.
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import UTC, datetime
from typing import Any

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json

from .canada import normalized_name
from .catalogue import stable_id
from .gppd import evidence_record

REFERENCE_IDS = ("vindbrukskollen_open_inventory_2026",)


def features(
    document: dict[str, Any], *, expected_count: int | None = None
) -> list[dict[str, Any]]:
    """Reject failed/truncated responses instead of accepting incomplete partitions."""
    if document.get("type") != "FeatureCollection" or document.get("exceededTransferLimit"):
        raise ValueError("Require complete GeoJSON FeatureCollection")
    if expected_count is not None and len(document["features"]) != expected_count:
        raise ValueError("Feature count differs from independent source count")
    return document["features"]


def _label(value: Any) -> str | None:
    text = (value or "").strip()
    return text if text and text != "-" else None


def _positive(value: Any) -> float | None:
    if value is None or value == "":
        return None
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError("Invalid nonnegative inventory value")
    # These source dimensional/rating fields use zero for unreported data.
    return result or None


def _date(value: Any) -> str | None:
    if value is None or value == "":
        return None
    result = datetime.fromtimestamp(value / 1000, tz=UTC).date().isoformat()
    return None if result.startswith("1900-") else result


def _status(values: set[str]) -> str:
    return {
        frozenset({"Beviljat"}): "permitted",
        frozenset({"Nedmonterat"}): "decommissioned",
        frozenset({"Inte aktuellt eller återkallat"}): "cancelled",
    }.get(frozenset(values), "unknown")


def stage_partition(
    areas: list[dict[str, Any]],
    turbines: list[dict[str, Any]],
    existing: list[dict[str, Any]],
    *,
    now: str,
    source_prefix: str = "vbk-20261103",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Stage all defensible named areas and their explicit VERKID children.

    Hold repeated municipality/name scopes, unnamed areas, repeated IDs, or an
    existing Swedish name/spatial candidate (10 km of any inventory turbine).
    Never merge on name alone. Existing IDs require a separate enrichment review.
    Preserve raw statuses, organization roles and model labels without inferring
    current operation, ownership, commercial operation dates or OEM compatibility.
    """
    area_ids = [f["properties"].get("OMRID") for f in areas]
    turbine_ids = [f["properties"].get("VERKID") for f in turbines]
    if any(not x for x in area_ids + turbine_ids):
        raise ValueError("Missing registry identity")
    if len(set(area_ids)) != len(area_ids) or len(set(turbine_ids)) != len(turbine_ids):
        raise ValueError("Duplicate registry identity")
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    incoming: list[dict[str, Any]] = []
    ledger: list[dict[str, Any]] = []
    for feature in turbines:
        props = feature["properties"]
        if props["OMRID"] not in area_ids:
            ledger.append(
                {
                    "entity_type": "turbines",
                    "registry_id": props["VERKID"],
                    "parent_registry_id": props["OMRID"],
                    "decision": "deferred",
                    "reason": "Parent area absent from selected official project layers",
                }
            )
            continue
        geometry = feature.get("geometry")
        if not geometry or geometry.get("type") != "Point":
            raise ValueError("Require reported turbine point")
        lon, lat = geometry["coordinates"][:2]
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise ValueError("Invalid coordinate")
        groups[props["OMRID"]].append(feature)
    names = Counter(
        (f["properties"].get("KOMNAMN"), normalized_name(f["properties"].get("PROJNAMN") or ""))
        for f in areas
    )
    for area in sorted(areas, key=lambda f: f["properties"]["OMRID"]):
        props = area["properties"]
        identity, name = props["OMRID"], (props.get("PROJNAMN") or "").strip()
        children = sorted(groups[identity], key=lambda f: f["properties"]["VERKID"])
        candidates = []
        for old in existing:
            if old["entity_type"] != "projects" or old.get("country_code") != "SWE":
                continue
            same_id = (
                json.loads(old.get("external_ids_json") or "{}").get("vindbrukskollen") == identity
            )
            same_name = bool(name) and normalized_name(old["name"]) == normalized_name(name)
            near = False
            if old.get("latitude") is not None:
                for child in children:
                    lon, lat = child["geometry"]["coordinates"][:2]
                    a, b = math.radians(lat), math.radians(old["latitude"])
                    h = (
                        math.sin((a - b) / 2) ** 2
                        + math.cos(a)
                        * math.cos(b)
                        * math.sin(math.radians(lon - old["longitude"]) / 2) ** 2
                    )
                    near |= 12742.0176 * math.asin(math.sqrt(min(1, h))) <= 10
            if same_id or same_name or near:
                candidates.append(old["record_id"])
        reason = None
        if not name:
            reason = "Unnamed administrative area; identifiable farm name unresolved"
        elif names[(props.get("KOMNAMN"), normalized_name(name))] > 1:
            reason = "Repeated municipality/name; phase or replacement scope unresolved"
        elif candidates:
            reason = "Existing registry/name/spatial candidate requires explicit reconciliation"
        elif not children:
            reason = "No linked turbine evidence in selected partition"
        decision = {
            "registry_id": identity,
            "name": name,
            "turbine_rows": len(children),
            "candidate_record_ids": candidates,
        }
        if reason:
            ledger.append({**decision, "decision": "deferred", "reason": reason})
            continue
        pid = stable_id("projects", "Vindbrukskollen", identity)
        ps = f"{source_prefix}-layer-{area['_layer']}"
        source_ids = sorted({ps, *(f"{source_prefix}-layer-{f['_layer']}" for f in children)})
        status_counts = Counter(f["properties"]["STATUS"] for f in children)
        anchor = children[0]
        lon, lat = anchor["geometry"]["coordinates"][:2]
        inventory = [
            {**f["properties"], "source_id": f"{source_prefix}-layer-{f['_layer']}"}
            for f in children
        ]
        model_counts = Counter(
            (
                _label(f["properties"].get("FABRIKAT")),
                _label(f["properties"].get("MODELL")),
                f["_layer"],
            )
            for f in children
        )
        fleet = [
            {
                "manufacturer": m,
                "model": model,
                "count": count,
                "source_id": f"{source_prefix}-layer-{layer}",
            }
            for (m, model, layer), count in model_counts.items()
            if m and model and m != "-" and model != "-"
        ]
        values = {
            "record_id": pid,
            "entity_type": "projects",
            "record_scope": "farm",
            "name": name,
            "country_code": "SWE",
            "region": props.get("LANSNAMN"),
            "locality": props.get("KOMNAMN"),
            "external_ids_json": canonical_json({"vindbrukskollen": identity}),
            "capacity_scope": (
                "Explicit registry development area; phase/repowering boundaries not reconciled"
            ),
            "aggregation_role": "unresolved",
            "quality_status": "needs_review",
            "technology": "onshore",
            "status": _status(set(status_counts)),
            "status_as_of": now[:10],
            "status_date_basis": (
                "Registry snapshot retrieval; erection is not operational evidence; "
                "original record dates retained"
            ),
            "latitude": lat,
            "longitude": lon,
            "location_accuracy": (
                f"Reported linked turbine {anchor['properties']['VERKID']} anchor; not "
                f"an area centroid; source positional accuracy unquantified"
            ),
            "boundary_geojson": canonical_json(area["geometry"]) if area.get("geometry") else None,
            "official_url": "https://vbk.lansstyrelsen.se/",
            "fleet_json": canonical_json(fleet) if fleet else None,
            "fleet_completeness": "partial" if fleet else None,
            "extensions_json": canonical_json(
                {
                    "vindbrukskollen": {
                        "area_fields": props,
                        "turbine_inventory": inventory,
                        "status_counts": dict(status_counts),
                        "inventory_completeness": (
                            "All linked georeferenced rows in selected official layers; current "
                            "operating fleet completeness unknown"
                        ),
                        "units": {
                            "MAXEFFEKT": "MW maximum turbine rating, not farm installed MW",
                            "CALPROD": (
                                "GWh calculated annual production; period and gross/net boundary "
                                "unknown"
                            ),
                            "TOTALHOJD": "m",
                            "NAVHOJD": "m",
                            "ROTDIAMETER": "m",
                        },
                    }
                }
            ),
            "notes": (
                "Registry area identity; reported plans and historical turbine states "
                "retained. No installed project capacity derived from ratings; no "
                "current-operation inference or equipment catalogue link."
            ),
        }
        row = evidence_record(
            values,
            source_id=ps,
            now=now,
            locator=f"OMRID={identity}; EPSG:4326 MapServer GeoJSON query",
            confidence="medium",
        )
        row["sources"] = source_ids
        fs = json.loads(row["field_sources_json"])
        for key in [
            "extensions_json",
            "fleet_json",
            "latitude",
            "longitude",
            "location_accuracy",
            "status",
            "status_date_basis",
        ]:
            if key in fs:
                fs[key] = source_ids
        row["field_sources_json"] = canonical_json(fs)
        incoming.append(row)
        for feature in children:
            p = feature["properties"]
            sid = f"{source_prefix}-layer-{feature['_layer']}"
            lon, lat = feature["geometry"]["coordinates"][:2]
            maximum = _positive(p.get("MAXEFFEKT"))
            turbine_values = {
                "record_id": stable_id("turbines", "Vindbrukskollen", p["VERKID"]),
                "entity_type": "turbines",
                "record_scope": "turbine",
                "name": f"{name} — {p['VERKID']}",
                "project_record_id": pid,
                "external_ids_json": canonical_json({"vindbrukskollen": p["VERKID"]}),
                "capacity_scope": (
                    "One registry turbine observation; maximum rating not farm installed capacity"
                ),
                "country_code": "SWE",
                "technology": "onshore",
                "status": _status({p["STATUS"]}),
                "manufacturer": _label(p.get("FABRIKAT")),
                "turbine_model": _label(p.get("MODELL")),
                "latitude": lat,
                "longitude": lon,
                "location_accuracy": (
                    "Registry turbine point transformed by source MapServer to EPSG:4326; "
                    "accuracy unquantified"
                ),
                "rotor_diameter_m": _positive(p.get("ROTDIAMETER")),
                "hub_height_m": _positive(p.get("NAVHOJD")),
                "tip_height_m": _positive(p.get("TOTALHOJD")),
                "extensions_json": canonical_json(
                    {
                        "source_fields": p,
                        "maximum_power_mw": maximum,
                        "erection_date": _date(p.get("UPPFORT")),
                        "erection_date_basis": (
                            "Reported erection date; 1900 placeholder becomes null; not "
                            "commercial operation"
                        ),
                        "permit_expiry_date": _date(p.get("MB_Tillstand_TIDSBEGRANS_DAT")),
                        "source_updated_date": _date(p.get("SenasteUppdatering")),
                        "calculated_annual_generation_gwh": p.get("CALPROD"),
                        "generation_boundary": (
                            "Source estimate; period, method and gross/net scope unknown; no "
                            "capacity factor calculated"
                        ),
                    }
                ),
            }
            incoming.append(
                evidence_record(
                    turbine_values,
                    source_id=sid,
                    now=now,
                    locator=f"VERKID={p['VERKID']}; OMRID={identity}; EPSG:4326 query",
                    confidence="medium",
                )
            )
        ledger.append(
            {
                **decision,
                "record_id": pid,
                "decision": "added",
                "reason": (
                    "Explicit named area and linked registry turbine IDs; capacity "
                    "aggregation withheld"
                ),
            }
        )
    return incoming, ledger


def main() -> None:
    """Stage downloaded layers without modifying canonical records or fetching data."""
    import argparse
    from pathlib import Path

    from energy_data_retrieval.pv_catalogue.catalogue import load_records

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Directory of vbk-layerN.geojson")
    parser.add_argument("--root", type=Path, default=Path("catalogues/wind"))
    parser.add_argument("--source-prefix", required=True)
    parser.add_argument("--timestamp", required=True, help="UTC retrieval/verification timestamp")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    args = parser.parse_args()
    areas, turbines = [], []
    for layer in (2, 3, 5, 6, 7, 8, 9, 10, 11, 12):
        selected = features(json.loads((args.input / f"vbk-layer{layer}.geojson").read_text()))
        for feature in selected:
            feature["_layer"] = layer
        (areas if layer in (2, 3) else turbines).extend(selected)
    rows, ledger = stage_partition(
        areas,
        turbines,
        load_records(args.root),
        now=args.timestamp,
        source_prefix=args.source_prefix,
    )
    for destination, values in ((args.output, rows), (args.ledger, ledger)):
        with destination.open("x") as stream:
            stream.writelines(canonical_json(row) + "\n" for row in values)
    print(f"Staged {len(rows)} records; {len(ledger)} review decisions")


if __name__ == "__main__":
    main()
