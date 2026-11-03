"""Offline WRI GPPD v1.3 wind baseline; no claim of current operation or phase scope.

Data attribution: World Resources Institute, Global Power Plant Database, CC BY 4.0.
The upstream inventory is historical and is not maintained after early 2022.
"""

from __future__ import annotations

import csv
import io
import math
from typing import Any

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json

from .catalogue import SCHEMA, stable_id


def evidence_record(
    values: dict[str, Any], *, source_id: str, now: str, locator: str, confidence: str = "high"
) -> dict[str, Any]:
    """Wrap reviewed facts in the existing field-source/evidence conventions."""
    from energy_data_retrieval.catalogue_common import ADMIN

    values = {k: v for k, v in values.items() if v is not None}
    evidence = {}
    for key, value in values.items():
        if key in ADMIN:
            continue
        evidence[key] = {
            "locator": locator,
            "confidence": confidence,
            "original_value": value,
            "unit": SCHEMA["fields"][key].get("unit"),
            "normalization": "none; curated facts or explicitly documented mapping",
        }
    return {
        **values,
        "created_at": now,
        "updated_at": now,
        "last_verified_at": now,
        "sources": [source_id],
        "quality_status": values.get("quality_status", "source_backed"),
        "field_sources_json": canonical_json({k: [source_id] for k in evidence}),
        "evidence_json": canonical_json(evidence),
    }


def _number(value: str | None) -> float | None:
    if value is None or not value.strip():
        return None
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Nonfinite source number")
    return result


def parse_gppd(
    text: str, *, source_id: str, now: str, snapshot_year: int = 2021
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Process every primary-fuel Wind row, preserving source IDs and unknown status.

    Capacity sums exclude these records until independent phase/generation scope
    reconciliation. Source generation and modeled generation stay separate; no CF
    is computed from an uncertain commissioning or capacity boundary.
    """
    reader = csv.DictReader(io.StringIO(text))
    required = {
        "country",
        "name",
        "gppd_idnr",
        "primary_fuel",
        "capacity_mw",
        "latitude",
        "longitude",
    }
    if not required <= set(reader.fieldnames or []):
        raise ValueError("Missing GPPD headers")
    rows, ledger = [], []
    seen = set()
    for line, raw in enumerate(reader, 2):
        if raw["primary_fuel"] != "Wind":
            continue
        external = raw["gppd_idnr"]
        if not external or external in seen:
            raise ValueError(f"Missing/duplicate GPPD ID at line {line}")
        seen.add(external)
        locator = f"CSV data row {line}; gppd_idnr={external}"
        record_id = stable_id("projects", "WRI-GPPD", external)
        try:
            capacity = _number(raw["capacity_mw"])
            lat, lon = _number(raw["latitude"]), _number(raw["longitude"])
            if capacity is not None and capacity < 0:
                raise ValueError("Negative capacity")
            if (lat is not None and not -90 <= lat <= 90) or (
                lon is not None and not -180 <= lon <= 180
            ):
                raise ValueError("Invalid coordinates")
            if (lat is None) != (lon is None):
                raise ValueError("Unpaired coordinates")
            year = _number(raw.get("year_of_capacity_data"))
            if year is not None and (not year.is_integer() or not 1900 <= year <= snapshot_year):
                raise ValueError("Invalid capacity year")
            observations = []
            for prefix, kind in (
                ("generation_gwh_", "reported"),
                ("estimated_generation_gwh_", "modeled"),
            ):
                for key, value in raw.items():
                    if key.startswith(prefix) and value:
                        observations.append(
                            {
                                "field": "generation",
                                "value": _number(value),
                                "unit": "GWh",
                                "kind": kind,
                                "period": key.removeprefix(prefix),
                                "boundary": "source plant; gross/net unspecified",
                                "source_id": source_id,
                                "locator": locator + f"; column {key}",
                            }
                        )
            values = {
                "record_id": record_id,
                "entity_type": "projects",
                "name": raw["name"],
                "record_scope": "farm",
                "capacity_scope": (
                    "Historical GPPD plant row; phase and repowering boundaries unverified"
                ),
                "country_code": raw["country"],
                "external_ids_json": canonical_json({"wri_gppd": external}),
                "aggregation_role": "unresolved",
                "quality_status": "needs_review",
                "technology": "unknown",
                "status": "unknown",
                "status_as_of": now[:10],
                "status_date_basis": (
                    "review date: historical inventory does not establish current status"
                ),
                "historical_capacity_mw": capacity,
                "capacity_reference_year": int(year) if year is not None else snapshot_year,
                "latitude": lat,
                "longitude": lon,
                "location_accuracy": "WRI compiled point; positional accuracy unquantified"
                if lat is not None
                else None,
                "owner_names": [raw["owner"]] if raw.get("owner") else None,
                "observations_json": canonical_json(observations) if observations else None,
                "extensions_json": canonical_json(
                    {
                        "upstream_source": raw.get("source"),
                        "upstream_url": raw.get("url"),
                        "geolocation_source": raw.get("geolocation_source"),
                        "commissioning_year_original": raw.get("commissioning_year") or None,
                        "capacity_year_original": raw.get("year_of_capacity_data") or None,
                        "capacity_year_basis": "reported"
                        if year is not None
                        else "2021 dataset snapshot only; actual capacity observation year unknown",
                        "generation_data_source": raw.get("generation_data_source"),
                        "estimated_generation_methods": {
                            k: v
                            for k, v in raw.items()
                            if k.startswith("estimated_generation_note_") and v
                        },
                    }
                ),
                "notes": (
                    "Historical discovery baseline, not a current operating census. "
                    "Scope reconciliation required before capacity aggregation; "
                    "original upstream URLs have not been independently reverified."
                ),
            }
            rows.append(
                evidence_record(
                    values, source_id=source_id, now=now, locator=locator, confidence="medium"
                )
            )
            ledger.append(
                {
                    "external_id": external,
                    "record_id": record_id,
                    "decision": "added_historical",
                    "locator": locator,
                    "deferred_fields": [
                        "current_status",
                        "technology",
                        "phase_scope",
                        "repowering",
                        "turbine_inventory",
                    ],
                }
            )
        except ValueError as exc:
            ledger.append(
                {
                    "external_id": external,
                    "decision": "deferred",
                    "reason": str(exc),
                    "locator": locator,
                }
            )
    return sorted(rows, key=lambda r: r["record_id"]), ledger
