"""ONS hydro-unit evidence with exact CEG identity and conservative plant scope."""

from __future__ import annotations

import copy
import csv
import io
import json
import math
import re
from collections import defaultdict
from typing import Any

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json

CEG = re.compile(r"(?:UHE|PCH|CGH)\.PH\.[A-Z]{2}\.(\d{6})-\d\.\d{2}")
REQUIRED = {
    "ceg",
    "nom_tipousina",
    "nom_usina",
    "cod_equipamento",
    "val_potenciaefetiva",
    "nom_agenteproprietario",
    "nom_agenteoperador",
    "dat_entradaoperacao",
    "dat_desativacao",
}


def parse_inventory(text: str) -> list[dict[str, Any]]:
    """Group distinct generator equipment by full CEG; never aggregate code variants."""
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")), delimiter=";")
    if not REQUIRED.issubset(reader.fieldnames or []):
        raise ValueError("Missing required ONS columns")
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen: set[str] = set()
    for line, raw in enumerate(reader, 2):
        if raw["nom_tipousina"].strip() != "HIDROELÉTRICA":
            continue
        row: dict[str, Any] = {k: v.strip() if v else None for k, v in raw.items()}
        ceg, equipment = row["ceg"], row["cod_equipamento"]
        if not ceg or not CEG.fullmatch(ceg) or not equipment:
            raise ValueError(f"Missing or malformed ONS identity at row {line}")
        if equipment in seen:
            raise ValueError(f"Duplicate ONS equipment at row {line}")
        seen.add(equipment)
        value = float(row["val_potenciaefetiva"])
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"Invalid nominal MW at row {line}")
        row["nominal_mw"] = value
        row["_row"] = line
        groups[ceg].append(row)
    return [
        {"ceg": ceg, "units": sorted(units, key=lambda u: u["cod_equipamento"])}
        for ceg, units in sorted(groups.items())
    ]


def wri_id(ceg: str) -> str:
    """Reproduce WRI build_database_BRA.py CEG numeric identity mapping."""
    match = CEG.fullmatch(ceg)
    if not match:
        raise ValueError("Malformed hydro CEG")
    return f"BRA{int(match[1]):07d}"


def eligibility(existing: dict[str, Any] | None, item: dict[str, Any]) -> str:
    """Require registry identity and exact names allowing only case/whitespace changes."""
    if existing is None:
        return "missing_existing_id"
    if existing["country_code"] != "BRA" or json.loads(existing["external_ids_json"]).get(
        "wri_gppd"
    ) != wri_id(item["ceg"]):
        return "registry_id_review"
    name = " ".join(existing["name"].split()).casefold()
    if not item["units"] or any(
        " ".join(u["nom_usina"].split()).casefold() != name for u in item["units"]
    ):
        return "name_review"
    return "accepted_enrichment"


def enrich(
    existing: dict[str, Any],
    item: dict[str, Any],
    *,
    source_id: str,
    identity_source_id: str,
    now: str,
    review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Add an immutable dated unit observation without inferring current operation."""
    decision = eligibility(existing, item)
    if review is not None:
        names = {u["nom_usina"] for u in item["units"]}
        if (
            review.get("decision") != "reviewed_registry_alias"
            or review.get("record_id") != existing["record_id"]
            or review.get("canonical_name") != existing["name"]
            or review.get("ceg") != item["ceg"]
            or names != {review.get("source_name")}
        ):
            raise ValueError("Alias review does not match inputs")
        # Only a recorded review may authorize a name difference. Registry checks remain.
        checked = {**existing, "name": review["source_name"]}
        decision = eligibility(checked, item)
    if decision != "accepted_enrichment":
        raise ValueError(decision)
    row = copy.deepcopy(existing)
    ids = json.loads(row["external_ids_json"])
    if ids.get("aneel_ceg", item["ceg"]) != item["ceg"]:
        raise ValueError("Conflicting CEG")
    ext = json.loads(row["extensions_json"])
    if review is not None:
        if ext.get("ons_alias_review", review) != review:
            raise ValueError("Conflicting alias review")
        ext["ons_alias_review"] = review
    history = ext.setdefault("ons_hydro_unit_inventory", [])
    observation = {**item, "source_id": source_id, "retrieved_at": now}
    prior = [o for o in history if o["source_id"] == source_id]
    if prior:
        if prior != [observation]:
            raise ValueError("Immutable ONS observation changed")
        return row
    history.append(observation)
    ids["aneel_ceg"] = item["ceg"]
    # Unit power and dates stay in evidence, not a claim of complete plant capacity/status.
    facts = {
        "external_ids_json": canonical_json(ids),
        "extensions_json": canonical_json(ext),
        "owner_names": sorted(
            {u["nom_agenteproprietario"] for u in item["units"] if u["nom_agenteproprietario"]}
        ),
        "operator_names": sorted(
            {u["nom_agenteoperador"] for u in item["units"] if u["nom_agenteoperador"]}
        ),
    }
    if review is not None:
        facts["aliases"] = sorted({*row.get("aliases", []), review["source_name"]})
    fs, ev = json.loads(row["field_sources_json"]), json.loads(row["evidence_json"])
    for key, value in facts.items():
        # Preserve historical owner observations in the nested evidence before replacement.
        if key == "owner_names" and row.get(key):
            ev.setdefault(
                "historical_owner_names", {"original_value": row[key], "sources": fs.get(key, [])}
            )
        row[key] = value
        fs[key] = sorted({*fs.get(key, []), source_id, identity_source_id})
        ev[key] = {
            "locator": "CAPACIDADE_GERACAO.csv rows "
            + ",".join(str(u["_row"]) for u in item["units"]),
            "confidence": "high",
            "normalization": (
                (
                    "CEG registry identity; explicit reviewed alias; "
                    if review
                    else "CEG registry identity; exact name ignoring case/whitespace; "
                )
                + "no capacity/status inference"
            ),
            "original_value": value,
        }
    row.update(
        field_sources_json=canonical_json(fs),
        evidence_json=canonical_json(ev),
        sources=sorted(set(row["sources"] + [source_id, identity_source_id])),
        updated_at=now,
        last_verified_at=now,
    )
    return row


def enrich_dispatch_metadata(existing: dict[str, Any], *, now: str) -> dict[str, Any]:
    """Expose source-reported state/subsystem/mode without inferring a grid connection.

    Multiple values remain explicit sets. Existing unit observations are immutable;
    the derived metadata retains their original source IDs and row locators.
    """
    row = copy.deepcopy(existing)
    ext = json.loads(row["extensions_json"])
    history = ext.get("ons_hydro_unit_inventory", [])
    if not history or row["country_code"] != "BRA":
        raise ValueError("Requires reviewed Brazilian ONS evidence")
    fields = (
        "id_estado",
        "nom_estado",
        "id_subsistema",
        "nom_subsistema",
        "nom_modalidadeoperacao",
    )
    metadata = {}
    for field in fields:
        observations = [
            {"value": unit[field], "source_id": obs["source_id"], "row": unit["_row"]}
            for obs in history
            for unit in obs["units"]
            if unit.get(field)
        ]
        metadata[field] = {
            "values": sorted({o["value"] for o in observations}),
            "evidence": observations,
        }
    if not any(value["values"] for value in metadata.values()):
        raise ValueError("No dispatch metadata in reviewed evidence")
    key = "ons_dispatch_metadata"
    if key in ext:
        if ext[key] != metadata:
            raise ValueError("Existing dispatch metadata requires conflict review")
        return row
    ext[key] = metadata
    row["extensions_json"] = canonical_json(ext)
    fs, ev = json.loads(row["field_sources_json"]), json.loads(row["evidence_json"])
    fs["extensions_json"] = sorted(
        set(fs.get("extensions_json", []) + [o["source_id"] for o in history])
    )
    ev["extensions_json"] = {
        "locator": "ONS unit rows retained in ons_dispatch_metadata.*.evidence",
        "confidence": "high",
        "unit": None,
        "normalization": (
            "Distinct reported state, subsystem and dispatch mode values; "
            "no inferred connection point or lifecycle"
        ),
        "original_value": row["extensions_json"],
    }
    row.update(
        field_sources_json=canonical_json(fs),
        evidence_json=canonical_json(ev),
        updated_at=now,
        last_verified_at=now,
    )
    return row
