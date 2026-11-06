"""Accept explicitly reviewed owner-identified plants without invented registry IDs."""

import json
from pathlib import Path
from typing import Any

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json, load_records

from .catalogue import stable_id, upsert_records, validate_catalogue
from .gppd import evidence_record
from .kengen import SOURCE_ID
from .ons_new import name_key


def new_record(entry: dict[str, Any], *, now: str) -> dict[str, Any]:
    """Use a frozen catalogue accession, not a purported national licence ID."""
    review, item = entry["review"], entry["inventory"]
    if (
        review.get("decision") != "reviewed_new_identity"
        or review.get("source_name") != item["source_name"]
        or not review.get("identity_basis")
        or not review.get("accession")
    ):
        raise ValueError("Explicit owner identity review required")
    return evidence_record(
        {
            "record_id": stable_id("projects", "reviewed-accession", review["accession"]),
            "entity_type": "projects",
            "name": item["source_name"],
            "country_code": "KEN",
            "record_scope": "plant",
            "capacity_scope": "Owner station; unresolved physical overlap",
            "aggregation_role": "unresolved",
            "status": "unknown",
            "status_as_of": now[:10],
            "status_date_basis": (
                "Review date; historical statistics do not establish current status"
            ),
            "technology": "unknown",
            "owner_names": ["Kenya Electricity Generating Company PLC"],
            "external_ids_json": "{}",
            "observations_json": canonical_json(item["observations"]),
            "extensions_json": canonical_json(
                {
                    "kengen_new_identity_review": review,
                    "owner_identity_source": "kengen-portfolio-20261106",
                    "registry_id_status": "Unknown; EPRA download returned HTTP 503",
                }
            ),
        },
        source_id=SOURCE_ID,
        now=now,
        locator="KenGen report pp. 246/249; per-cell observation locators",
    )


def accept_new(root: Path, batch: dict[str, Any], output: Path) -> int:
    """Preflight every identity and name collision before writing one new shard."""
    existing = load_records(root)
    lookup = {r["record_id"]: r for r in existing}
    incoming = [new_record(e, now=batch["reviewed_at"]) for e in batch["accepted"]]
    if len({r["record_id"] for r in incoming}) != len(incoming):
        raise ValueError("Duplicate incoming accession")
    new = []
    for row in incoming:
        # The portfolio corroborates identity only, not the report's numeric cells.
        fs, ev = json.loads(row["field_sources_json"]), json.loads(row["evidence_json"])
        fs["extensions_json"].append("kengen-portfolio-20261106")
        ev["extensions_json"]["locator"] = "Named station sections; review basis in extensions_json"
        row.update(
            field_sources_json=canonical_json(fs),
            evidence_json=canonical_json(ev),
            sources=sorted(set(row["sources"] + ["kengen-portfolio-20261106"])),
        )
        if row["record_id"] in lookup:
            if lookup[row["record_id"]] != row:
                raise ValueError("Existing accession differs; conflict review required")
            continue
        for prior in existing + new:
            if prior["country_code"] == "KEN" and name_key(row["name"]) in {
                name_key(n) for n in [prior["name"], *prior.get("aliases", [])]
            }:
                raise ValueError("Name collision requires identity review")
        new.append(row)
    combined, conflicts = upsert_records(existing, new, now=batch["reviewed_at"])
    if conflicts:
        raise ValueError("Insertion conflict")
    validate_catalogue(combined, json.loads((root / "sources.json").read_text()))
    if new:
        if output.exists():
            raise ValueError("Refuse to overwrite existing shard")
        output.write_text(
            "".join(canonical_json(r) + "\n" for r in sorted(new, key=lambda r: r["record_id"]))
        )
    return len(new)
