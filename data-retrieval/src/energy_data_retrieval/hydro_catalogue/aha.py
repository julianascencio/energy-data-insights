"""Historical AHA evidence with explicit reviewed crosswalks; never fuzzy merges."""

import copy
import io
import json
import math
from typing import Any

import openpyxl

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json

SHEET = "1 - Spatial and technical data"


def parse_inventory(data: bytes) -> list[dict[str, Any]]:
    """Bound reads to the 36-column technical table; exclude derived model columns."""
    book = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    sheet = book[SHEET]
    headers = next(sheet.iter_rows(min_row=3, max_row=3, max_col=36, values_only=True))
    if (
        headers[1:8]
        != ("Country", "Unit Name", "Status", "Latitude", "Longitude", "River Name", "River Basin")
        or headers[17] != "Capacity"
    ):
        raise ValueError("Unexpected AHA technical headers")
    result = []
    for index, values in enumerate(sheet.iter_rows(min_row=4, max_col=36, values_only=True), 4):
        if not values[1] and not values[2]:
            continue
        if not isinstance(values[1], str) or not isinstance(values[2], str):
            raise ValueError("Malformed AHA station row")
        raw = {headers[k]: values[k] for k in [*range(1, 18), *range(24, 36)]}
        result.append({"row": index, "raw": raw})
    book.close()
    return result


def enrich(
    existing: dict[str, Any],
    item: dict[str, Any],
    *,
    source_id: str,
    reviewed_record_id: str,
    reviewed_country_code: str,
    now: str,
) -> dict[str, Any]:
    """Apply an explicitly reviewed name/capacity/station-location crosswalk.

    Keep source status, capacity, ownership and hydraulic ratings as historical
    raw evidence. Do not infer current operation, reservoir energy or plant scope.
    """
    raw = item["raw"]
    if (
        existing["record_id"] != reviewed_record_id
        or existing["country_code"] != reviewed_country_code
    ):
        raise ValueError("Explicit identity review required")
    if raw.get("SharedPlant") or raw.get("SharedPlantSplit"):
        raise ValueError("Shared plant requires scope review")
    if existing["name"].strip().casefold() != raw["Unit Name"].strip().casefold():
        raise ValueError("Name requires review")
    for field, column in [
        ("latitude", "Latitude"),
        ("longitude", "Longitude"),
    ]:
        value = float(raw[column])
        if (
            not math.isfinite(value)
            or existing.get(field) is None
            or abs(existing[field] - value) > 0.01
        ):
            raise ValueError("Station coordinates require review")
    capacity = float(raw["Capacity"])
    if not math.isfinite(capacity) or capacity != existing.get("historical_capacity_mw"):
        raise ValueError("Historical capacity/scope requires review")
    row = copy.deepcopy(existing)
    ext = json.loads(row["extensions_json"])
    obs = {**item, "source_id": source_id, "release_year": 2024}
    history = ext.setdefault("aha_historical_inventory", [])
    prior = [x for x in history if x["source_id"] == source_id]
    if prior:
        if prior != [obs]:
            raise ValueError("Immutable AHA observation changed")
        return row
    history.append(obs)
    facts = {"extensions_json": canonical_json(ext)}
    for field, column in [("river", "River Name"), ("basin", "River Basin")]:
        value = str(raw.get(column) or "").strip()
        if value and value.casefold() not in {"local", "local stream"}:
            if row.get(field) not in (None, "", value):
                raise ValueError("Conflicting hydraulic metadata")
            facts[field] = value
    fs, ev = json.loads(row["field_sources_json"]), json.loads(row["evidence_json"])
    for field, value in facts.items():
        row[field] = value
        fs[field] = sorted({*fs.get(field, []), source_id})
        ev[field] = {
            "locator": f"{SHEET}, Excel row {item['row']}",
            "confidence": "high",
            "original_value": value,
            "normalization": (
                "Explicit name/capacity/station-coordinate review; historical AHA v2.3 evidence"
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
