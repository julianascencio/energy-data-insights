"""Explicitly reviewed new ONS identities; no automatic name matching or MW sums."""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from typing import Any

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json, load_records

from .catalogue import SCHEMA, stable_id, upsert_records, validate_catalogue
from .gppd import evidence_record
from .ons import CEG, enrich_dispatch_metadata, wri_id


def name_key(value: str) -> str:
    """Conservative collision screen only; this key never authorizes a merge."""
    value = unicodedata.normalize("NFKD", value).casefold()
    return "".join(c for c in value if c.isalnum())


def new_record(entry: dict[str, Any], *, now: str) -> dict[str, Any]:
    """Build a CEG-keyed record from reviewed unit evidence and attributed facts."""
    item, review = entry["inventory"], entry["review"]
    ceg, units = item["ceg"], item["units"]
    if not CEG.fullmatch(ceg) or not units:
        raise ValueError("Require full hydro CEG and units")
    names = {u["nom_usina"] for u in units}
    if (
        review.get("decision") != "reviewed_new_identity"
        or review.get("ceg") != ceg
        or names != {review.get("source_name")}
        or not review.get("identity_basis")
    ):
        raise ValueError("Explicit new-identity review does not match inputs")
    equipment = [u["cod_equipamento"] for u in units]
    if len(set(equipment)) != len(equipment) or any(u["ceg"] != ceg for u in units):
        raise ValueError("Duplicate equipment or mixed registry identity")
    sid = entry["source_id"]
    ext = {
        "ons_new_identity_review": review,
        "ons_hydro_unit_inventory": [
            {**item, "source_id": sid, "retrieved_at": entry["source_retrieved_at"]}
        ],
    }
    row = evidence_record(
        {
            "record_id": stable_id("projects", "ANEEL-CEG", ceg),
            "entity_type": "projects",
            "name": review["source_name"],
            "country_code": "BRA",
            "record_scope": "plant",
            "capacity_scope": "CEG facility; unit observations are not a complete plant rating",
            "aggregation_role": "unresolved",
            "status": "unknown",
            "status_as_of": now[:10],
            "status_date_basis": "Review date; inventory does not establish current lifecycle",
            "technology": "unknown",
            "external_ids_json": canonical_json({"aneel_ceg": ceg}),
            "owner_names": sorted(
                {u["nom_agenteproprietario"] for u in units if u["nom_agenteproprietario"]}
            ),
            "operator_names": sorted(
                {u["nom_agenteoperador"] for u in units if u["nom_agenteoperador"]}
            ),
            "extensions_json": canonical_json(ext),
        },
        source_id=sid,
        now=now,
        locator="CAPACIDADE_GERACAO.csv rows " + ",".join(str(u["_row"]) for u in units),
    )
    row = enrich_dispatch_metadata(row, now=now)
    fs, ev = json.loads(row["field_sources_json"]), json.loads(row["evidence_json"])
    allowed = {
        "installed_capacity_mw",
        "river",
        "basin",
        "technology",
        "turbine_type",
        "turbine_count",
        "reservoir_volume_m3",
        "commissioning_date",
        "environmental_constraints",
    }
    for field, fact in entry.get("facts", {}).items():
        if field not in allowed or not fact.get("locator") or not fact.get("basis"):
            raise ValueError("Unsupported or unattributed reviewed fact")
        row[field] = fact["value"]
        fs[field] = [fact["source_id"]]
        ev[field] = {
            "locator": fact["locator"],
            "confidence": "high",
            "original_value": fact["original_value"],
            "unit": SCHEMA["fields"][field].get("unit"),
            "normalization": fact["basis"],
        }
        row["sources"] = sorted(set(row["sources"] + [fact["source_id"]]))
    row.update(field_sources_json=canonical_json(fs), evidence_json=canonical_json(ev))
    return row


def accept_new(root: Path, batch: dict[str, Any], output: Path) -> int:
    """Preflight the whole batch, then append only new records to one reviewable shard.

    Exact CEGs, historical CEG-derived WRI IDs and normalized names/aliases all
    block new acceptance. A replay of an identical record is a no-op. Changed
    evidence or another record with the same identity needs a separate review.
    """
    existing = load_records(root)
    lookup = {r["record_id"]: r for r in existing}
    incoming = [new_record(e, now=batch["reviewed_at"]) for e in batch["accepted"]]
    if len({r["record_id"] for r in incoming}) != len(incoming):
        raise ValueError("Duplicate incoming identity")
    new = []
    for row in incoming:
        if row["record_id"] in lookup:
            if lookup[row["record_id"]] != row:
                raise ValueError("Existing record differs; conflict review required")
            continue
        ceg = json.loads(row["external_ids_json"])["aneel_ceg"]
        for prior in existing + new:
            ids = json.loads(prior.get("external_ids_json") or "{}")
            if ids.get("aneel_ceg") == ceg or ids.get("wri_gppd") == wri_id(ceg):
                raise ValueError("Existing registry identity; enrich rather than insert")
            if prior["country_code"] == "BRA" and name_key(row["name"]) in {
                name_key(n) for n in [prior["name"], *prior.get("aliases", [])]
            }:
                raise ValueError("Name collision requires explicit identity review")
        new.append(row)
    combined, conflicts = upsert_records(existing, new, now=batch["reviewed_at"])
    if conflicts:
        raise ValueError("Unexpected insertion conflict")
    validate_catalogue(combined, json.loads((root / "sources.json").read_text()))
    if new:
        if output.exists():
            raise ValueError("Refuse to overwrite an existing shard")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            "".join(canonical_json(r) + "\n" for r in sorted(new, key=lambda r: r["record_id"]))
        )
    return len(new)
