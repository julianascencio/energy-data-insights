"""Pinned Madrid municipal PV inventories: building identities need explicit review."""

from __future__ import annotations

import csv
import io
import json
import math
import re
from collections import Counter
from datetime import date, datetime
from typing import Any

from .catalogue import canonical_json, stable_id
from .odre import normal_name
from .sam import verify_sha256

COLUMNS = {
    "Número",
    "Código Ayto",
    "Centro",
    "Dirección",
    "Coordenada-X",
    "Coordenada-Y",
    "Latitud",
    "Longitud",
    "Superficie (m2)",
    "Uso del edificio",
    "Adscripción",
    "Distrito",
    "Potencia KWp",
    "Empresa instaladora",
    "Puesta en servicio",
    "",
}


def _number(value: str) -> float:
    value = value.strip()
    if not re.fullmatch(r"-?\d+(?:[.,]\d+)?", value):
        raise ValueError("Invalid Madrid number")
    result = float(value.replace(",", "."))
    if not math.isfinite(result):
        raise ValueError("Nonfinite Madrid number")
    return result


def read_madrid_csv(content: bytes, *, sha256: str) -> list[dict[str, str]]:
    """Verify bytes, schema and sequence locators; never use sequence as plant ID."""
    verify_sha256(content, sha256)
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")), delimiter=";")
    if (
        reader.fieldnames is None
        or set(reader.fieldnames) != COLUMNS
        or len(reader.fieldnames) != len(COLUMNS)
    ):
        raise ValueError("Madrid schema changed; re-review")
    rows = list(reader)
    if any(None in row or any(v is None for v in row.values()) or row[""] for row in rows):
        raise ValueError("Malformed Madrid CSV row")
    sequence = [r["Número"] for r in rows]
    if len(set(sequence)) != len(sequence) or any(not s.isdigit() for s in sequence):
        raise ValueError("Invalid or duplicate Madrid sequence locator")
    return rows


def screen_madrid_identities(
    rows: list[dict[str, str]], *, existing: list[dict[str, Any]]
) -> dict[str, list[str]]:
    """Hold repeated building/name/pin identities and nearby canonical assets.

    Proximity is a conservative review flag, never a merge or coordinate transform.
    A building code identifies a municipal building, not a national PV plant.
    """
    codes = Counter(r["Código Ayto"].strip() for r in rows)
    names = Counter(normal_name(r["Centro"]) for r in rows)
    canonical_names = {
        normal_name(n)
        for r in existing
        if r.get("country_code") == "ESP"
        for n in [r["name"], *r.get("aliases", [])]
    }
    canonical_codes = {
        json_code
        for r in existing
        if (json_code := json.loads(r.get("external_ids_json", "{}")).get("madrid_building_code"))
    }
    pins: dict[str, tuple[float, float]] = {}
    risks: dict[str, list[str]] = {}
    for row in rows:
        key = row["Número"]
        reasons = []
        code = row["Código Ayto"].strip()
        if not code.isdigit() or codes[code] != 1:
            reasons.append("missing_or_repeated_building_code")
        if not row["Centro"].strip() or names[normal_name(row["Centro"])] != 1:
            reasons.append("missing_or_repeated_building_name")
        if code in canonical_codes or normal_name(row["Centro"]) in canonical_names:
            reasons.append("existing_canonical_identity_requires_crosswalk")
        try:
            if _number(row["Potencia KWp"]) <= 0:
                reasons.append("nonpositive_capacity")
            lat, lon = _number(row["Latitud"]), _number(row["Longitud"])
            if not (40 <= lat <= 41 and -4.1 <= lon <= -3.2):
                reasons.append("outside_published_Madrid_location_scope")
            else:
                pins[key] = (lat, lon)
        except ValueError:
            reasons.append("invalid_capacity_or_location")
        if reasons:
            risks[key] = reasons
    for key, (lat, lon) in pins.items():
        # Local approximation is solely a hold screen; no inferred precision/datum.
        def near(a: float, b: float, threshold: float, lat: float = lat, lon: float = lon) -> bool:
            return math.hypot((lat - a) * 111, (lon - b) * 85) < threshold

        if any(other != key and near(a, b, 0.1) for other, (a, b) in pins.items()):
            risks.setdefault(key, []).append("incoming_buildings_within_100m_scope_review")
        if any(
            r.get("country_code") == "ESP"
            and r.get("latitude") is not None
            and r.get("longitude") is not None
            and near(r["latitude"], r["longitude"], 0.25)
            for r in existing
        ):
            risks.setdefault(key, []).append("canonical_asset_within_250m_scope_review")
    return risks


def reviewed_madrid_records(
    rows: list[dict[str, str]],
    *,
    reviewed_sequences: set[str],
    existing: list[dict[str, Any]],
    source_id: str,
    snapshot_date: str,
) -> list[dict[str, Any]]:
    """Map explicitly reviewed distinct sites; preserve kWp and building-pin scope."""
    snapshot = date.fromisoformat(snapshot_date)
    risks = screen_madrid_identities(rows, existing=existing)
    lookup = {r["Número"]: r for r in rows}
    if len(lookup) != len(rows):
        raise ValueError("Duplicate Madrid sequence locator")
    if not reviewed_sequences <= lookup.keys() or reviewed_sequences & risks.keys():
        raise ValueError("Unresolved Madrid identity review")
    result = []
    for sequence in sorted(reviewed_sequences, key=int):
        row = lookup[sequence]
        code = row["Código Ayto"].strip()
        service = row["Puesta en servicio"].strip()
        commissioning = datetime.strptime(service, "%d/%m/%Y").date() if service else None
        if commissioning and commissioning > snapshot:
            raise ValueError("Madrid service date exceeds snapshot")
        result.append(
            {
                "record_id": stable_id("projects", "MadridMunicipalPV", code),
                "entity_type": "projects",
                "name": row["Centro"].strip(),
                "country_code": "ESP",
                "region": "Comunidad de Madrid",
                "locality": "Madrid",
                "technology": "photovoltaic",
                "status": "active_municipal_inventory_snapshot",
                "source_date": snapshot_date,
                "capacity_dc_mw": _number(row["Potencia KWp"]) / 1000,
                "capacity_basis": "Municipal inventory Potencia KWp; published PV peak kWp /1000",
                "latitude": _number(row["Latitud"]),
                "longitude": _number(row["Longitud"]),
                "location_accuracy": (
                    "Published municipal-building point; datum/CRS and positional accuracy "
                    "unspecified; not surveyed PV-array coordinates"
                ),
                **({"commissioning_date": commissioning.isoformat()} if commissioning else {}),
                "external_ids_json": canonical_json({"madrid_building_code": code}),
                "extensions_json": canonical_json(
                    {
                        "madrid_inventory": {
                            "source_id": source_id,
                            "sequence_locator": sequence,
                            "building_code_scope": (
                                "Municipal building code, not national PV registry ID; "
                                "repeated buildings "
                                "held for phase/site review"
                            ),
                            "building_use": row["Uso del edificio"],
                            "district": row["Distrito"],
                            "administrative_assignment": row["Adscripción"],
                            "assignment_scope": (
                                "Published building administrative assignment; "
                                "no PV ownership, operator "
                                "or EPC inferred"
                            ),
                            "capacity_kwp_as_reported": row["Potencia KWp"],
                            "service_date_as_reported": service or None,
                            "area_as_reported_m2": row["Superficie (m2)"] or None,
                            "area_scope": (
                                "Undefined source Superficie; "
                                "not promoted to array area or project land "
                                "area"
                            ),
                            "native_grid_x": row["Coordenada-X"],
                            "native_grid_y": row["Coordenada-Y"],
                            "coordinate_scope": (
                                "Original decimal latitude/longitude copied; no CRS assumed or "
                                "transformed; precision does not establish accuracy"
                            ),
                            "privacy": (
                                "Street address and installer names omitted; "
                                "building names are public "
                                "municipal entities"
                            ),
                        }
                    }
                ),
                "sources": [source_id],
                "field_sources_json": canonical_json({"*": source_id}),
                "quality_status": "official_registry_reviewed",
                "notes": (
                    "Active PV inventory at the dated snapshot; no present-operation "
                    "assertion, PV ownership, equipment assignment or AC rating inferred. "
                    "Public municipal-building installation, not a city-centre coordinate."
                ),
            }
        )
    return result
