"""Conservative offline staging of explicit MaStR named wind-park groups.

A reported park label is not a registry farm ID. Freeze reviewed group identities;
retain unit registry IDs, partial inventory scope and exclusion from MW totals.
"""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json

from .canada import normalized_name
from .catalogue import stable_id
from .gppd import evidence_record

REFERENCE_IDS = ("mastr_full_export_20261103",)
STATES = {
    "1411": "Schleswig-Holstein",
    "1408": "Niedersachsen",
    "1409": "Nordrhein-Westfalen",
    "1400": "Brandenburg",
    "1414": "Sachsen-Anhalt",
}


def distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Great-circle separation in km for latitude/longitude degrees."""
    lat1, lat2 = math.radians(a[0]), math.radians(b[0])
    h = (
        math.sin((lat1 - lat2) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(math.radians(a[1] - b[1]) / 2) ** 2
    )
    return 12742.0176 * math.asin(math.sqrt(min(1, max(0, h))))


def point(row: dict[str, str]) -> tuple[float, float] | None:
    """Reject missing and out-of-country coordinates rather than geocode them."""
    try:
        lat, lon = float(row["Breitengrad"]), float(row["Laengengrad"])
    except (ValueError, KeyError, TypeError):
        return None
    return (lat, lon) if 47 <= lat <= 56 and 5 <= lon <= 16 else None


def stage(
    units: list[dict[str, str]],
    dictionary: dict[str, str],
    existing: list[dict[str, Any]],
    *,
    source_id: str,
    now: str,
    state_code: str = "1411",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Review the full selected state, retaining all rejected group decisions.

    Accept only explicit park labels with at least three units, one municipality,
    one operator, activated onshore records and a maximum 15 km extent. Hold any
    other park label within 500 m or prior catalogue project within 10 km.
    These conservative screens support inventory identity, not phase reconciliation.
    """
    ids = [r.get("EinheitMastrNummer") for r in units]
    if any(not x for x in ids) or len(ids) != len(set(ids)):
        raise ValueError("Missing or duplicate MaStR unit ID")
    if state_code not in STATES or dictionary.get(state_code) != STATES[state_code]:
        raise ValueError("State dictionary code/revision mismatch")
    if any(r.get("Bundesland") != state_code for r in units):
        raise ValueError("Require complete selected state partition")
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in units:
        groups[(r.get("NameWindpark") or "").strip()].append(r)
    located = [(name, point(r)) for name, group in groups.items() for r in group]
    incoming, ledger = [], []
    for name, group in sorted(groups.items()):
        reason = None
        coords = [point(r) for r in group]
        operators = {r.get("AnlagenbetreiberMastrNummer") for r in group}
        municipalities = {r.get("Gemeindeschluessel") for r in group}
        if not name or "park" not in name.casefold() or len(group) < 3:
            reason = "Missing explicit park label or fewer than three units; manual identity review"
        elif (
            len(operators) != 1
            or not all(operators)
            or len(municipalities) != 1
            or not all(municipalities)
        ):
            reason = "Multiple or missing operator/municipality scopes"
        elif any(
            r.get("EinheitSystemstatus") != "472" or r.get("WindAnLandOderAufSee") != "888"
            for r in group
        ):
            reason = "Non-activated or non-onshore scope requires separate reconciliation"
        elif None in coords:
            reason = "Missing or invalid coordinate"
        else:
            valid = [p for p in coords if p is not None]
            if max(distance(a, b) for a in valid for b in valid) > 15:
                reason = "Park label spans more than 15 km"
            elif any(
                other != name and p is not None and any(distance(p, q) < 0.5 for q in valid)
                for other, p in located
            ):
                reason = "Another registry park label within 500 m; alias/phase reconciliation"
            elif any(
                r.get("country_code") == "DEU"
                and r["entity_type"] == "projects"
                and (
                    normalized_name(r["name"]) == normalized_name(name)
                    or (
                        r.get("latitude") is not None
                        and any(distance((r["latitude"], r["longitude"]), q) < 10 for q in valid)
                    )
                )
                for r in existing
            ):
                reason = "Existing German name/spatial candidate"
        decision = {
            "name": name,
            "unit_count": len(group),
            "unit_ids": sorted(r["EinheitMastrNummer"] for r in group),
        }
        if reason:
            ledger.append({**decision, "decision": "deferred", "reason": reason})
            continue
        ordered = sorted(group, key=lambda r: r["EinheitMastrNummer"])
        pid = stable_id(
            "projects",
            "MaStR-reviewed-park",
            name,
            str(next(iter(municipalities))),
            str(next(iter(operators))),
        )
        anchor = ordered[0]
        coord = point(anchor)
        assert coord is not None
        fleet = Counter(
            (dictionary.get(r.get("Hersteller", "")), r.get("Typenbezeichnung")) for r in group
        )
        vals = {
            "record_id": pid,
            "entity_type": "projects",
            "record_scope": "farm",
            "name": name,
            "country_code": "DEU",
            "region": STATES[state_code],
            "locality": anchor.get("Gemeinde"),
            "capacity_scope": (
                "Explicit named registry park inventory; phases and repowering unresolved"
            ),
            "aggregation_role": "unresolved",
            "status": "unknown",
            "status_as_of": now[:10],
            "status_date_basis": (
                "Unit lifecycle observations retained; no farm-wide lifecycle inferred"
            ),
            "technology": "onshore",
            "quality_status": "needs_review",
            "latitude": coord[0],
            "longitude": coord[1],
            "location_accuracy": (
                f"Reported unit {anchor['EinheitMastrNummer']} anchor, not a farm centroid"
            ),
            "fleet_completeness": "partial",
            "fleet_json": canonical_json(
                [
                    {"manufacturer": m, "model": model, "count": count, "source_id": source_id}
                    for (m, model), count in fleet.items()
                    if m and model
                ]
            ),
            "extensions_json": canonical_json(
                {
                    "mastr_inventory": {
                        "unit_ids": decision["unit_ids"],
                        "operator_registry_id": next(iter(operators)),
                        "municipality_code": next(iter(municipalities)),
                        "unit_status_counts": dict(
                            Counter(
                                dictionary.get(r.get("EinheitBetriebsstatus", ""), "unknown")
                                for r in group
                            )
                        ),
                        "scope": (
                            "All matching named rows in selected state; current physical fleet "
                            "completeness unknown; no sum substituted for farm MW"
                        ),
                    }
                }
            ),
            "notes": (
                "Natural group identity frozen at first review; no invented farm "
                "registry ID. Reconcile unit links before future additions or "
                "ownership/name changes."
            ),
        }
        incoming.append(
            evidence_record(
                vals,
                source_id=source_id,
                now=now,
                locator=f"EinheitenWind.xml; NameWindpark={name}; unit IDs in extensions",
                confidence="medium",
            )
        )
        for unit in ordered:
            p = point(unit)
            assert p is not None
            fields = {
                k: unit.get(k)
                for k in (
                    "EinheitMastrNummer",
                    "LokationMaStRNummer",
                    "AnlagenbetreiberMastrNummer",
                    "NameWindpark",
                    "Gemeindeschluessel",
                    "EinheitBetriebsstatus",
                    "Inbetriebnahmedatum",
                    "DatumLetzteAktualisierung",
                    "Bruttoleistung",
                    "Nettonennleistung",
                    "Nabenhoehe",
                    "Rotordurchmesser",
                    "Hersteller",
                    "Typenbezeichnung",
                    "EegMaStRNummer",
                    "GenMastrNummer",
                    "NetzbetreiberpruefungStatus",
                    "NetzbetreiberpruefungDatum",
                )
            }
            values = {
                "record_id": stable_id("turbines", "MaStR", unit["EinheitMastrNummer"]),
                "entity_type": "turbines",
                "record_scope": "turbine",
                "name": unit.get("NameStromerzeugungseinheit") or unit["EinheitMastrNummer"],
                "project_record_id": pid,
                "external_ids_json": canonical_json({"mastr": unit["EinheitMastrNummer"]}),
                "capacity_scope": (
                    "Single registered wind unit; gross and net kW preserved separately"
                ),
                "country_code": "DEU",
                "technology": "onshore",
                "latitude": p[0],
                "longitude": p[1],
                "location_accuracy": "Original registry point; positional precision unquantified",
                "manufacturer": dictionary.get(unit.get("Hersteller", "")),
                "turbine_model": unit.get("Typenbezeichnung"),
                "extensions_json": canonical_json(
                    {
                        "source_fields": fields,
                        "decoded_lifecycle": dictionary.get(unit.get("EinheitBetriebsstatus", "")),
                        "units": {
                            "Bruttoleistung": "kW gross",
                            "Nettonennleistung": "kW net",
                            "Nabenhoehe": "m",
                            "Rotordurchmesser": "m",
                        },
                        "note": (
                            "Registry ratings and model labels are not independent OEM "
                            "specifications; commissioning date retains unit boundary"
                        ),
                    }
                ),
            }
            incoming.append(
                evidence_record(
                    values,
                    source_id=source_id,
                    now=now,
                    locator=(
                        f"EinheitenWind.xml; EinheitMastrNummer={unit['EinheitMastrNummer']}; "
                        "Katalogwerte.xml for code labels"
                    ),
                    confidence="medium",
                )
            )
        ledger.append({**decision, "decision": "added", "record_id": pid})
    return incoming, ledger


def read_partition(
    wind_xml: Path,
    dictionary_xml: Path,
    *,
    expected_total: int,
    expected_selected: int,
    state_code: str = "1411",
) -> tuple[list[dict[str, str]], dict[str, str]]:
    """Read the complete pinned member; reject incomplete XML or row counts.

    Callers verify original member SHA-256 before parsing. The current adapter is
    bounded to explicitly supported states rather than silently broadening.
    """
    dictionary = {
        str(e.findtext("Id")): str(e.findtext("Wert")) for e in ET.parse(dictionary_xml).getroot()
    }
    if state_code not in STATES or dictionary.get(state_code) != STATES[state_code]:
        raise ValueError("State dictionary code/revision mismatch")
    units = []
    total = 0
    for _, element in ET.iterparse(wind_xml, events=["end"]):
        if element.tag != "EinheitWind":
            continue
        total += 1
        if element.findtext("Bundesland") == state_code:
            units.append({child.tag: child.text for child in element if child.text is not None})
        element.clear()
    if total != expected_total or len(units) != expected_selected:
        raise ValueError("Independent full-export/partition count mismatch")
    return units, dictionary
