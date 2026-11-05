"""Historical IHA India evidence; explicit reviewed crosswalks, never fuzzy merges."""

import copy
import csv
import io
import json
import math
from typing import Any

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json


def parse_inventory(data: bytes) -> list[dict[str, Any]]:
    """Read Windows-1252 CSV with original row locators and distinct asset classes."""
    reader = csv.DictReader(io.StringIO(data.decode("cp1252")))
    required = {
        "ID",
        "Database Status",
        "Hydropower Station Name",
        "Lat (hydropower station 1)",
        "Long (hydropower station 1)",
        "HPP_elec_cap",
        "River",
        "Main_basin",
    }
    if not required.issubset(reader.fieldnames or []):
        raise ValueError("Missing IHA columns")
    result, seen = [], set()
    for index, row in enumerate(reader, 2):
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f"Malformed IHA row {index}")
        identity = int(row["ID"])
        if identity < 1 or identity in seen:
            raise ValueError("Invalid or duplicate IHA identity")
        seen.add(identity)
        result.append({"id": identity, "row": index, "raw": dict(row)})
    return sorted(result, key=lambda r: r["id"])


def enrich(
    existing: dict[str, Any],
    item: dict[str, Any],
    *,
    source_id: str,
    reviewed_record_id: str,
    now: str,
) -> dict[str, Any]:
    """Apply an explicitly reviewed name/capacity/station-location crosswalk.

    Keep source status, capacity, ownership and hydraulic ratings as historical
    raw evidence. Do not infer current operation, reservoir energy or plant scope.
    """
    raw = item["raw"]
    if existing["record_id"] != reviewed_record_id or existing["country_code"] != "IND":
        raise ValueError("Explicit identity review required")
    if raw["Database Status"].strip() != "Matched with hydro station":
        raise ValueError("Not a matched generating station")
    if existing["name"].strip().casefold() != raw["Hydropower Station Name"].strip().casefold():
        raise ValueError("Name requires review")
    for field, column in [
        ("latitude", "Lat (hydropower station 1)"),
        ("longitude", "Long (hydropower station 1)"),
    ]:
        value = float(raw[column])
        if (
            not math.isfinite(value)
            or existing.get(field) is None
            or abs(existing[field] - value) > 0.001
        ):
            raise ValueError("Station coordinates require review")
    capacity = float(raw["HPP_elec_cap"])
    if not math.isfinite(capacity) or capacity != existing.get("historical_capacity_mw"):
        raise ValueError("Historical capacity/scope requires review")
    row = copy.deepcopy(existing)
    ext = json.loads(row["extensions_json"])
    obs = {**item, "source_id": source_id, "release_year": 2019}
    history = ext.setdefault("iha_india_historical_inventory", [])
    prior = [x for x in history if x["source_id"] == source_id]
    if prior:
        if prior != [obs]:
            raise ValueError("Immutable IHA observation changed")
        return row
    history.append(obs)
    ids = json.loads(row["external_ids_json"])
    if ids.get("iha_india_2019", str(item["id"])) != str(item["id"]):
        raise ValueError("Conflicting IHA identity")
    ids["iha_india_2019"] = str(item["id"])
    facts = {"extensions_json": canonical_json(ext), "external_ids_json": canonical_json(ids)}
    for field, column in [("river", "River"), ("basin", "Main_basin")]:
        value = raw[column].strip()
        if value and value.casefold() not in {"local", "local stream"}:
            if row.get(field) not in (None, "", value):
                raise ValueError("Conflicting hydraulic metadata")
            facts[field] = value
    fs, ev = json.loads(row["field_sources_json"]), json.loads(row["evidence_json"])
    for field, value in facts.items():
        row[field] = value
        fs[field] = sorted({*fs.get(field, []), source_id})
        ev[field] = {
            "locator": f"IHA CSV row {item['row']}; ID={item['id']}",
            "confidence": "high",
            "original_value": value,
            "normalization": (
                "Explicit name/capacity/station-coordinate review; historical 2019 evidence"
            ),
        }
    row.update(
        field_sources_json=canonical_json(fs),
        evidence_json=canonical_json(ev),
        sources=sorted(set(row["sources"] + [source_id])),
        updated_at=now,
        last_verified_at=now,
    )
    return row
