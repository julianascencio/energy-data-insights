"""Parse dated New Zealand dispatch observations without inferring plant totals."""

import csv
import io
import math
from datetime import datetime
from typing import Any

FIELDS = (
    "PlantName",
    "PointOfConnectionCode",
    "UnitCode",
    "TechnologyCode",
    "Technology",
    "FuelCode",
    "Fuel",
    "PeakingPlantFlag",
    "PlantOperatorCode",
    "PlantOperator",
    "DateCommissioned",
    "DateDecommissioned",
    "NameplateMegawatts",
    "EffectiveStartDate",
    "EffectiveEndDate",
)


def parse_inventory(data: bytes) -> list[dict[str, Any]]:
    """Retain original row locators and intervals, including sentinel dates.

    Multiple connections and effective periods are observations, not independent
    plants or generating units. Never sum their ratings or infer present status.
    """
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    if tuple(reader.fieldnames or ()) != FIELDS:
        raise ValueError("Unexpected NZ fleet columns")
    result = []
    seen = set()
    for index, row in enumerate(reader, 2):
        if None in row or any(v is None for v in row.values()):
            raise ValueError("Malformed NZ row")
        if row["TechnologyCode"] != "HYD":
            continue
        if row["FuelCode"] != "HYD":
            raise ValueError("Inconsistent hydro fuel")
        if any(not row[k].strip() for k in FIELDS[:3]):
            raise ValueError("Missing dispatch identity")
        key = tuple(row[k] for k in (*FIELDS[:3], "EffectiveStartDate", "EffectiveEndDate"))
        if key in seen:
            raise ValueError("Duplicate dispatch interval")
        seen.add(key)
        start = datetime.fromisoformat(row["EffectiveStartDate"])
        end = datetime.fromisoformat(row["EffectiveEndDate"])
        if start.tzinfo is None or end.tzinfo is None or start >= end:
            raise ValueError("Invalid dispatch interval")
        mw = float(row["NameplateMegawatts"])
        if not math.isfinite(mw) or mw < 0:
            raise ValueError("Invalid generating MW")
        result.append({"row": index, "raw": row})
    return result


def enrich_reviewed(
    existing: dict[str, Any],
    item: dict[str, Any],
    *,
    reviewed_record_id: str,
    owner_source_id: str,
    now: str,
) -> dict[str, Any]:
    """Attach one manually corroborated dispatch row; never sum or infer operation."""
    import copy
    import json

    from energy_data_retrieval.pv_catalogue.catalogue import canonical_json

    raw = item["raw"]
    if (
        existing["record_id"] != reviewed_record_id
        or existing["country_code"] != "NZL"
        or existing["name"] != raw["PlantName"]
        or not owner_source_id
    ):
        raise ValueError("Explicit owner-backed identity review required")
    if raw["TechnologyCode"] != "HYD" or raw["FuelCode"] != "HYD":
        raise ValueError("Not conventional hydro evidence")
    mw = float(raw["NameplateMegawatts"])
    if not math.isfinite(mw) or mw != existing.get("historical_capacity_mw"):
        raise ValueError("Historical capacity scope requires review")
    row = copy.deepcopy(existing)
    source_id = "nz-ea-fleet-20260702"
    ext = json.loads(row["extensions_json"])
    obs = {**item, "source_id": source_id, "identity_source_id": owner_source_id}
    history = ext.setdefault("nz_dispatch_observations", [])
    if history:
        if history != [obs]:
            raise ValueError("Existing dispatch history requires interval/scope review")
        return row
    history.append(obs)
    ids = json.loads(row["external_ids_json"])
    key = raw["PointOfConnectionCode"] + ":" + raw["UnitCode"]
    if ids.get("nz_ea_dispatch_connection", key) != key:
        raise ValueError("Conflicting dispatch identity")
    ids["nz_ea_dispatch_connection"] = key
    fs, ev = json.loads(row["field_sources_json"]), json.loads(row["evidence_json"])
    for field, value in {
        "external_ids_json": canonical_json(ids),
        "extensions_json": canonical_json(ext),
    }.items():
        row[field] = value
        fs[field] = sorted(set([*fs.get(field, []), source_id, owner_source_id]))
        ev[field] = {
            "locator": f"CSV record {item['row']}; owner station identity/rating section",
            "confidence": "high",
            "original_value": value,
            "normalization": "Owner/WRI/EA review; historical dispatch observation only",
        }
    row.update(
        field_sources_json=canonical_json(fs),
        evidence_json=canonical_json(ev),
        sources=sorted(set(row["sources"] + [source_id, owner_source_id])),
        updated_at=now,
        last_verified_at=now,
    )
    return row
