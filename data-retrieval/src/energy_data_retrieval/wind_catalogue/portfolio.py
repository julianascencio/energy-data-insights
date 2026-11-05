"""Offline staging of complete, reviewed OEM turbine specification columns.

Input is an attributed transcription checked against the rendered original,
not a text-extraction heuristic. Column identity never supplies missing values.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json

from .catalogue import SCHEMA, stable_id
from .gppd import evidence_record

REFERENCE_IDS = ("goldwind_portfolio_2025q3",)
SPECIFICATIONS = {
    "platform",
    "rated_power_kw",
    "rated_power_conditions",
    "rotor_diameter_m",
    "swept_area_m2",
    "blade_count",
    "iec_class",
    "cut_in_m_s",
    "cut_out_m_s",
    "rated_wind_speed_m_s",
    "design_life_years",
    "design_life_conditions",
    "temperature_min_c",
    "temperature_max_c",
    "generator_type",
    "gearbox_type",
    "converter_type",
    "pitch_yaw_control",
    "tower_options",
    "hub_height_options_json",
    "extensions_json",
    "certifications_json",
}


def stage_portfolio(
    review: dict[str, Any], original: bytes, existing: list[dict[str, Any]], *, now: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Stage every explicit column once; defer existing models for revision review.

    Unreported quantities remain absent (typed null in snapshots). Hub choices,
    electrical boundaries and certification observations stay nested. Neither
    model-code geometry nor generator voltage becomes a turbine output claim.
    """
    if hashlib.sha256(original).hexdigest() != review["sha256"]:
        raise ValueError("Original portfolio checksum mismatch")
    expected, columns = review["expected_models"], review["columns"]
    names = [c["model"] for c in columns]
    if (
        not expected
        or len(set(expected)) != len(expected)
        or len(set(names)) != len(names)
        or set(names) != set(expected)
    ):
        raise ValueError("Incomplete or duplicate portfolio columns")
    if not review["manufacturer"] or not review["revision"]:
        raise ValueError("Manufacturer and document revision required")
    prior = {
        (r.get("manufacturer"), r.get("model")) for r in existing if r["entity_type"] == "equipment"
    }
    records, ledger = [], []
    for column in columns:
        model, values = column["model"], dict(column["values"])
        if not model or not column["locator"] or set(values) - SPECIFICATIONS:
            raise ValueError("Explicit model, locator and supported specifications required")
        if set(values) != set(column["original_units"]):
            raise ValueError("Every transcribed field requires original units")
        for field, condition in [
            ("rated_power_kw", "rated_power_conditions"),
            ("design_life_years", "design_life_conditions"),
        ]:
            if values.get(field) is not None and not values.get(condition):
                raise ValueError(f"{field} requires source conditions")
        key = (review["manufacturer"], model)
        if key in prior:
            ledger.append(
                {
                    "model": model,
                    "decision": "existing_identity_review",
                    "reason": "Reconcile source revision; do not create a second model",
                }
            )
            continue
        row = evidence_record(
            {
                "record_id": stable_id("equipment", "OEM portfolio", *key),
                "entity_type": "equipment",
                "record_scope": "model",
                "name": " ".join(key),
                "manufacturer": key[0],
                "model": model,
                "equipment_category": "wind_turbine",
                "source_revision": review["revision"],
                "variant": "Explicit published column; site-specific options nested",
                "capacity_scope": "Manufacturer specification, not an installed fleet",
                "notes": "Not independently validated performance; no numerical curves, "
                "component models or compatibility inferred from platform labels.",
                **values,
            },
            source_id=review["source_id"],
            now=now,
            locator=column["locator"],
        )
        evidence = json.loads(row["evidence_json"])
        for field, unit in column["original_units"].items():
            if field in evidence:
                evidence[field].update(
                    unit=SCHEMA["fields"][field].get("unit", unit),
                    original_unit=unit,
                    revision=review["revision"],
                    confidence="high",
                    normalization="Reviewed table value; no model-code inference",
                )
        row["evidence_json"] = canonical_json(evidence)
        records.append(row)
        ledger.append(
            {
                "model": model,
                "decision": "addition",
                "record_id": row["record_id"],
                "source_id": review["source_id"],
                "locator": column["locator"],
            }
        )
    return sorted(records, key=lambda r: r["record_id"]), ledger
