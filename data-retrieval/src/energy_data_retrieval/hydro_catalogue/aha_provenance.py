"""Expose historical AHA field bases without promoting model inputs to measurements."""

import copy
import json
from typing import Any

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json

FIELDS = {
    "Status": (None, "Source_status", "historical inventory classification"),
    "Latitude": ("degree", "Source_location", "dataset station coordinate"),
    "Longitude": ("degree", "Source_location", "dataset station coordinate"),
    "Capacity": ("MW", "Source_capacity", "historical rated capacity; physical scope unresolved"),
    "Reservoir Size": (
        "million m3",
        "Source_reservoir_size",
        "reservoir volume; usable fraction unknown",
    ),
    "Mean Annual Discharge": (
        "m3/s",
        "Source_mean_annual_discharge",
        "multiannual river discharge; not turbine design flow",
    ),
    "Design Discharge": (
        "m3/s",
        "Source_design_discharge",
        "design discharge; not measured operating flow",
    ),
    "First Year": ("year", None, "earliest expected entry year; not verified commissioning"),
    "Availability": (
        None,
        "Source_availability",
        "availability profile selection; not operational status",
    ),
    "River Name": (None, "Source_river", "dataset river name"),
    "River Basin": (None, "Source_river_basin", "dataset basin name"),
}


def enrich_provenance(existing: dict[str, Any], *, now: str) -> dict[str, Any]:
    """Retain raw values, per-field upstream citations and explicit unverified bases."""
    row = copy.deepcopy(existing)
    ext = json.loads(row["extensions_json"])
    history = ext.get("aha_historical_inventory", [])
    if not history:
        raise ValueError("Requires accepted AHA identity evidence")
    observations = []
    for obs in history:
        raw = obs["raw"]
        for field, (unit, source_column, basis) in FIELDS.items():
            if raw.get(field) in (None, ""):
                continue
            observations.append(
                {
                    "column": field,
                    "value": raw[field],
                    "unit": unit,
                    "basis": basis,
                    "source_id": obs["source_id"],
                    "excel_row": obs["row"],
                    "upstream_reference": raw.get(source_column) if source_column else None,
                    "fallback_reference": raw.get("SingleSource"),
                    "upstream_independently_verified": False,
                    "uncertainty": (
                        "Source-specific uncertainty unknown; historical/model input, "
                        "not current measured evidence"
                    ),
                }
            )
    key = "aha_field_provenance"
    if key in ext:
        if ext[key] != observations:
            raise ValueError("Changed AHA field evidence requires review")
        return row
    ext[key] = observations
    row["extensions_json"] = canonical_json(ext)
    fs, ev = json.loads(row["field_sources_json"]), json.loads(row["evidence_json"])
    fs["extensions_json"] = sorted(set(fs["extensions_json"] + [o["source_id"] for o in history]))
    ev["extensions_json"] = {
        "locator": "AHA technical sheet; per-column Excel rows retained in aha_field_provenance",
        "confidence": "high",
        "original_value": row["extensions_json"],
        "normalization": (
            "Explicit dataset units/bases and unverified upstream citations; "
            "no rating/status promotion"
        ),
    }
    row.update(
        field_sources_json=canonical_json(fs),
        evidence_json=canonical_json(ev),
        updated_at=now,
        last_verified_at=now,
    )
    return row
