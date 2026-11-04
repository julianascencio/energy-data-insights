"""Checksum-pinned DGEG polygon staging; never infer a canonical plant or AC power.

The CS service includes park blocks, sub-parks and non-PV components. Its licence
states and kW/kVA fields must survive review without arithmetic or status inference.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from typing import Any

FIELDS = {
    "objectid",
    "processo",
    "nome",
    "subparque",
    "tipo_central",
    "subtipo_instalacao",
    "potencia_geradorkw",
    "potencia_instaladakva",
    "potencia_ligacaokva",
    "concelho",
    "distrito",
    "lic_producao",
    "lic_exploracao",
    "inspireid",
}
POWER_FIELDS = {"potencia_geradorkw", "potencia_instaladakva", "potencia_ligacaokva"}


def read_dgeg_page(content: bytes, *, sha256: str) -> dict[str, Any]:
    """Validate a projected ArcGIS page and stage explicit PV features only.

    Raw geometry, owners and other unrequested fields never enter staged output.
    Row identifiers identify source polygons, not independent generating projects.
    """
    if hashlib.sha256(content).hexdigest() != sha256:
        raise ValueError("DGEG source checksum mismatch")
    data = json.loads(content)
    if not isinstance(data, dict) or "error" in data or not isinstance(data.get("features"), list):
        raise ValueError("DGEG response is not a feature page")
    definitions = data.get("fields")
    if not isinstance(definitions, list):
        raise ValueError("DGEG field definitions missing")
    if any(
        not isinstance(item, dict) or not isinstance(item.get("name"), str) for item in definitions
    ):
        raise ValueError("DGEG field definitions malformed")
    names = [item["name"] for item in definitions]
    if len(names) != len(set(names)) or not set(names) >= FIELDS:
        raise ValueError("DGEG projected schema changed")
    more = data.get("exceededTransferLimit", False)
    if not isinstance(more, bool):
        raise ValueError("DGEG pagination flag is not boolean")
    rows, excluded, identifiers = [], [], set()
    for feature in data["features"]:
        if not isinstance(feature, dict):
            raise ValueError("DGEG feature malformed")
        attributes = feature.get("attributes")
        if not isinstance(attributes, dict) or not attributes.keys() >= FIELDS:
            raise ValueError("DGEG feature attributes changed")
        identifier = attributes["objectid"]
        if type(identifier) is not int or identifier <= 0 or identifier in identifiers:
            raise ValueError("DGEG polygon ID missing, invalid or duplicated")
        identifiers.add(identifier)
        if (
            attributes["tipo_central"] != "CS"
            or attributes["subtipo_instalacao"] != "Solar fotovoltaico"
        ):
            excluded.append({"objectid": identifier, "reason": "not_explicit_photovoltaic"})
            continue
        if type(attributes["processo"]) is not int or attributes["processo"] <= 0:
            raise ValueError("DGEG PV licensing process ID invalid")
        for name in POWER_FIELDS:
            value = attributes[name]
            if value is not None and (
                type(value) not in (int, float) or not math.isfinite(value) or value < 0
            ):
                raise ValueError("DGEG native power value invalid")
        row = {name: attributes[name] for name in sorted(FIELDS)}
        if any(
            value is not None and not isinstance(value, str)
            for key, value in row.items()
            if key not in POWER_FIELDS | {"objectid", "processo"}
        ):
            raise ValueError("DGEG text field type changed")
        rows.append(row)
    return {
        "sha256": sha256,
        "object_ids": sorted(identifiers),
        "pv_features": rows,
        "excluded_features": excluded,
        "exceeded_transfer_limit": more,
    }


def group_dgeg_pages(
    pages: list[dict[str, Any]], *, expected_object_ids: set[int] | None = None
) -> list[dict[str, Any]]:
    """Group evidence by licensing process, retaining every native block value.

    Completeness needs an independently reviewed full-scope ID set. A final page
    or matching name does not prove a complete plant. Groups remain review-only.
    """
    identifiers: set[int] = set()
    groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for page in pages:
        ids = set(page["object_ids"])
        if identifiers & ids:
            raise ValueError("DGEG polygon repeated across pages")
        identifiers.update(ids)
        for row in page["pv_features"]:
            groups[row["processo"]].append(row)
    if expected_object_ids is not None and identifiers != expected_object_ids:
        raise ValueError("DGEG reviewed source coverage incomplete")
    result = []
    for process, rows in sorted(groups.items()):
        holds = ["licensing_process_is_not_a_reviewed_plant_identity"]
        if expected_object_ids is None:
            holds.append("source_coverage_not_proven")
        if len(rows) > 1:
            holds.append("multiple_polygons_or_blocks_do_not_establish_separate_plants")
        if len({r["nome"] for r in rows}) > 1:
            holds.append("multiple_names_in_process")
        if any(not r["nome"] or not r["inspireid"] for r in rows):
            holds.append("missing_public_name_or_polygon_reference")
        if any(len({r[k] for r in rows if r[k] is not None}) > 1 for k in POWER_FIELDS):
            holds.append("native_power_scope_or_values_differ")
        result.append(
            {
                "processo": process,
                "features": sorted(rows, key=lambda row: row["objectid"]),
                "source_coverage_complete": expected_object_ids is not None,
                "held_reasons": holds,
                "accepted": False,
            }
        )
    return result
