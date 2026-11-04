"""Offline review staging for Catalonia's named ground-mounted PV registry.

Application IDs are administrative identities, not automatic plant boundaries.
Municipality rows repeat plant-wide capacity and area: neither is summed.
The output omits applicants and cannot itself accept canonical records.
"""

from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from .sam import verify_sha256

DATASET_ID = "ggx8-jkp4"
PLANT_FIELDS = (
    "tramitat",
    "pot_ncia_mw",
    "superf_cie_ha",
    "estat",
    "tipus_de_s_l",
    "tr_mit_ambiental",
    "estat_ambiental",
    "data_pon_ncia",
    "sentit_acord",
)
GEOGRAPHY_FIELDS = (
    "municipi",
    "codi_municipi",
    "comarca",
    "codi_comarca",
    "vegueria",
    "superf_cie_al_municipi_ha",
)


def stage_catalonia_review(
    content: bytes,
    metadata: bytes,
    *,
    sha256: str,
    metadata_sha256: str,
    expected_rows: int,
) -> dict[str, Any]:
    """Group reviewed-source observations, preserving ambiguity and native units."""
    verify_sha256(content, sha256)
    verify_sha256(metadata, metadata_sha256)
    meta = json.loads(metadata)
    if meta.get("id") != DATASET_ID or meta.get("provenance") != "official":
        raise ValueError("Unexpected Catalonia dataset identity")
    if "fotovoltaiques" not in meta.get("name", "").casefold():
        raise ValueError("Positive photovoltaic dataset classification required")
    columns = {column["fieldName"] for column in meta["columns"]}
    if not {"sol_licitud", "nom", *PLANT_FIELDS, *GEOGRAPHY_FIELDS} <= columns:
        raise ValueError("Catalonia columns changed; review mapping")
    rows = json.loads(content)
    if not isinstance(rows, list) or len(rows) != expected_rows or expected_rows < 1:
        raise ValueError("Truncated or changed Catalonia export")
    updated = datetime.fromtimestamp(meta["rowsUpdatedAt"], UTC).isoformat()
    groups: dict[tuple[str, str], list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    id_names: dict[str, set[str]] = defaultdict(set)
    name_ids: dict[str, set[str]] = defaultdict(set)
    for line, row in enumerate(rows, 1):
        name = row.get("nom", "").strip()
        application = row.get("sol_licitud", "").strip()
        if not name:
            raise ValueError("Missing named PV installation")
        for field in ("pot_ncia_mw", "superf_cie_ha", "superf_cie_al_municipi_ha"):
            if field in row:
                number = float(row[field])
                if not math.isfinite(number) or number < 0:
                    raise ValueError("Invalid Catalonia capacity or area")
        groups[(application, name)].append((line, row))
        id_names[application].add(name)
        name_ids[name.casefold()].add(application)
    candidates = []
    for (application, name), entries in sorted(groups.items()):
        flags = ["manual_project_identity_and_existing_catalogue_review_required"]
        if not application:
            flags.append("missing_application_id")
        if len(id_names[application]) > 1:
            flags.append("application_shared_by_multiple_names")
        if len(name_ids[name.casefold()]) > 1:
            flags.append("name_has_multiple_applications")
        if re.search(r"ampliaci|\bbess\b|\betapa\b", name, re.IGNORECASE):
            flags.append("expansion_storage_or_phase_scope")
        facts = {}
        for field in PLANT_FIELDS:
            values = sorted({row[field] for _, row in entries if row.get(field) not in (None, "")})
            if len(values) > 1:
                flags.append(f"conflicting_{field}")
            if values:
                facts[field] = values
        if any(float(value) == 0 for value in facts.get("pot_ncia_mw", [])):
            flags.append("zero_capacity_requires_technology_scope_review")
        geographies = []
        for _, row in entries:
            geography = {field: row[field] for field in GEOGRAPHY_FIELDS if field in row}
            if geography not in geographies:
                geographies.append(geography)
        candidates.append(
            {
                "application_id": application or None,
                "name": name,
                "source_rows": [line for line, _ in entries],
                "native_plant_fields": facts,
                "geographies": geographies,
                "review_flags": sorted(set(flags)),
            }
        )
    return {
        "dataset_id": DATASET_ID,
        "source_sha256": sha256,
        "metadata_sha256": metadata_sha256,
        "source_updated_at": updated,
        "observations": len(rows),
        "grouped_candidates": len(candidates),
        "canonical_accepted": 0,
        "candidates": candidates,
        "scope": "Named ground PV >100 kW; in-service coverage only post-November 2019. "
        "Nominal MW has unspecified AC/DC basis. Application status is not construction. "
        "No applicants or precise coordinates exported; repeated plant values are not summed.",
    }
