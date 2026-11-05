"""Bounded EIA-860 hydro enrichment with exact registry identity and dated unit evidence."""

from __future__ import annotations

import copy
import json
import math
from collections import defaultdict
from typing import Any

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json
from energy_data_retrieval.wind_catalogue.eia import _rows

UNIT_FIELDS = (
    "Generator ID",
    "Prime Mover",
    "Technology",
    "Status",
    "Nameplate Capacity (MW)",
    "Summer Capacity (MW)",
    "Winter Capacity (MW)",
    "Operating Month",
    "Operating Year",
    "Utility ID",
    "Utility Name",
    "Energy Source 1",
    "Turbines or Hydrokinetic Buoys",
)
PLANT_FIELDS = (
    "Plant Code",
    "Plant Name",
    "Latitude",
    "Longitude",
    "State",
    "County",
    "Balancing Authority Code",
    "Balancing Authority Name",
    "Grid Voltage (kV)",
)


def parse_partition(
    plant_bytes: bytes, generator_bytes: bytes, *, year: int, first: int, last: int
) -> list[dict[str, Any]]:
    """Read every operable generator at each hydro-containing plant in an ID range.

    Operable includes standby/out-of-service units: eligibility is checked later.
    No generator ID is numerically normalized; leading zeroes are identity text.
    """
    if first < 1 or last < first:
        raise ValueError("Invalid plant-code partition")
    plants = _rows(plant_bytes, "Plant", PLANT_FIELDS, year)
    units = _rows(generator_bytes, "Operable", ("Plant Code", *UNIT_FIELDS), year)
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    seen = set()
    for unit in units:
        code = unit["Plant Code"]
        if code is None and str(unit.get("Utility ID", "")).startswith("NOTE:"):
            if any(v is not None for k, v in unit.items() if k not in {"Utility ID", "_row"}):
                raise ValueError("Malformed EIA footer")
            continue
        if type(code) is not int or code < 1:
            raise ValueError("Missing or invalid generator plant code")
        if not first <= code <= last:
            continue
        key = (code, str(unit["Generator ID"]))
        if key in seen or not unit["Generator ID"]:
            raise ValueError("Missing or duplicate generator identity")
        seen.add(key)
        grouped[code].append({k: unit[k] for k in (*UNIT_FIELDS, "_row")})
    results = []
    plant_ids = set()
    for plant in plants:
        code = plant["Plant Code"]
        if code in plant_ids:
            raise ValueError("Duplicate plant code")
        plant_ids.add(code)
        selected = grouped.get(code, [])
        if not any(u["Prime Mover"] in {"HY", "PS"} for u in selected):
            continue
        results.append(
            {
                "year": year,
                "plant_code": code,
                "plant": {k: plant[k] for k in (*PLANT_FIELDS, "_row")},
                "units": sorted(selected, key=lambda u: str(u["Generator ID"])),
            }
        )
    orphaned = [
        code
        for code, selected in grouped.items()
        if code not in plant_ids and any(u["Prime Mover"] in {"HY", "PS"} for u in selected)
    ]
    if orphaned:
        raise ValueError(f"Hydro generator plants absent from Plant sheet: {sorted(orphaned)}")
    return sorted(results, key=lambda r: r["plant_code"])


def eligibility(existing: dict[str, Any] | None, item: dict[str, Any]) -> str:
    """No fuzzy matching; different source scopes and ambiguous identities stay on hold."""
    if existing is None:
        return "missing_existing_id"
    if existing.get("status") != "unknown" and existing.get("status_as_of", "") > (
        f"{item['year']}-12-31"
    ):
        return "newer_status_review"
    ids = json.loads(existing["external_ids_json"])
    code = item["plant_code"]
    if existing["country_code"] != "USA" or ids.get("wri_gppd") != f"USA{code:07d}":
        return "registry_id_review"
    if existing["name"] != item["plant"]["Plant Name"]:
        return "name_review"
    for old, new in (("latitude", "Latitude"), ("longitude", "Longitude")):
        a, b = existing.get(old), item["plant"].get(new)
        if a is None or b is None or not math.isfinite(b) or abs(a - b) > 0.0001:
            return "coordinate_review"
    if not item["units"] or any(
        u["Prime Mover"] != "HY" or u["Status"] != "OP" for u in item["units"]
    ):
        return "mixed_technology_or_state"
    seen = set()
    for unit in item["units"]:
        identity = str(unit["Generator ID"])
        if not identity or identity in seen:
            return "duplicate_unit_review"
        seen.add(identity)
        value = unit["Nameplate Capacity (MW)"]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return "capacity_review"
        if not math.isfinite(value) or value < 0:
            return "capacity_review"
    return "accepted_enrichment"


def enrich(
    existing: dict[str, Any],
    item: dict[str, Any],
    *,
    source_id: str,
    identity_source_id: str,
    now: str,
) -> dict[str, Any]:
    """Retain plant UUID/history and all unit evidence; no promotion to 2026 operation.

    Aggregation stays unresolved, including split reporting facilities. Pumping
    power, storage energy, turbine count and hydraulic subtype are not inferred.
    """
    decision = eligibility(existing, item)
    if decision != "accepted_enrichment":
        raise ValueError(decision)
    row = copy.deepcopy(existing)
    ids = json.loads(row["external_ids_json"])
    code = str(item["plant_code"])
    if ids.get("eia_plant_code", code) != code:
        raise ValueError("Conflicting EIA plant identity")
    ext = json.loads(row.get("extensions_json") or "{}")
    observation = {**item, "source_id": source_id}
    history = ext.setdefault("eia_hydro_annual_inventory", [])
    prior = [x for x in history if x["source_id"] == source_id]
    if prior:
        if prior != [observation]:
            raise ValueError("Immutable EIA observation changed")
        return row
    history.append(observation)
    ids["eia_plant_code"] = code
    mw = math.fsum(u["Nameplate Capacity (MW)"] for u in item["units"])
    for key in ("installed_capacity_mw", "operational_capacity_mw"):
        if row.get(key) is not None and row[key] != mw:
            raise ValueError("Existing capacity requires conflict review")
    facts = {
        "external_ids_json": canonical_json(ids),
        "extensions_json": canonical_json(ext),
        "status": "operational",
        "status_as_of": f"{item['year']}-12-31",
        "status_date_basis": f"EIA final annual inventory for year {item['year']}; not live status",
        "installed_capacity_mw": mw,
        "operational_capacity_mw": mw,
        "capacity_scope": (
            f"EIA plant {code}; all Operable-tab units HY and OP at year-end {item['year']}; "
            "nameplate generating MW, not net seasonal capability; cross-plant scope unresolved"
        ),
        "operator_names": sorted({u["Utility Name"] for u in item["units"]}),
    }
    fs = json.loads(row["field_sources_json"])
    ev = json.loads(row["evidence_json"])
    for key, value in facts.items():
        row[key] = value
        refs = [source_id, identity_source_id]
        if key in {"external_ids_json", "extensions_json"}:
            refs = sorted(set(fs.get(key, []) + refs))
        fs[key] = refs
        ev[key] = {
            "locator": f"2___Plant_Y{item['year']}.xlsx Plant row {item['plant']['_row']}; "
            "3_1_Generator Operable row locators in extensions_json",
            "confidence": "high",
            "unit": "MW" if key.endswith("_mw") else None,
            "normalization": "Registry ID/name/coordinate checks; sum distinct OP/HY units",
            "original_value": value,
        }
    row.update(
        field_sources_json=canonical_json(fs),
        evidence_json=canonical_json(ev),
        sources=sorted(set(row["sources"] + [source_id, identity_source_id])),
        updated_at=now,
        last_verified_at=now,
        notes=f"EIA year-end {item['year']} generating inventory enriched; "
        "historical WRI facts retained. "
        "Aggregation unresolved; excludes pumping power and energy-storage inference.",
    )
    return row
