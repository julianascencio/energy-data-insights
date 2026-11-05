"""Append reviewed EPD observations without turning LCA scenarios into projects.

Original declarations qualify modeled lifetime flows, not operational output or
independently validated turbine performance. Only explicit model mappings apply.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from typing import Any

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json

from .catalogue import SCHEMA

REFERENCE_IDS = ("goldwind_epditaly0508", "goldwind_epditaly0852")


def enrich_from_epd(
    review: dict[str, Any], original: bytes, existing: list[dict[str, Any]], *, now: str
) -> list[dict[str, Any]]:
    """Replay a complete reviewed model partition, preserving dated discrepancies.

    ``scalar_observations`` may qualify geometry or design life. Differing values
    quarantine the scalar; equal values add provenance. LCA reference service life
    is never promoted to design life. Lifetime generation stays in an explicitly
    modeled, per-turbine, net-to-grid scenario with its own exposure and location.
    """
    if hashlib.sha256(original).hexdigest() != review["sha256"]:
        raise ValueError("Original EPD checksum mismatch")
    expected = review["expected_models"]
    models = [x["model"] for x in review["models"]]
    if not expected or len(set(models)) != len(models) or sorted(models) != sorted(expected):
        raise ValueError("Require complete unique explicit model partition")
    source = review["source_id"]
    result = []
    for item in review["models"]:
        matches = [
            x
            for x in existing
            if x["entity_type"] == "equipment"
            and x.get("manufacturer") == review["manufacturer"]
            and x.get("model") == item["model"]
        ]
        if len(matches) != 1:
            raise ValueError("EPD model requires one exact existing identity")
        if not item.get("locator") or not item.get("technical"):
            raise ValueError("Require technical observations and original locator")
        for scenario in item["scenarios"]:
            if (
                scenario.get("kind") != "modeled"
                or scenario.get("boundary") != "one turbine; net electricity delivered to grid"
                or scenario.get("unit") != "MWh"
                or not scenario.get("location")
                or not scenario.get("locator")
                or not scenario.get("reference_period")
            ):
                raise ValueError("Require modeled per-turbine net lifetime boundary")
            for key in ("value", "reference_service_life_years", "mean_wind_speed_m_s"):
                value = scenario.get(key)
                if type(value) not in {int, float} or not math.isfinite(value) or value <= 0:
                    raise ValueError("Require positive finite scenario quantity")
        row = copy.deepcopy(matches[0])
        ext = json.loads(row.get("extensions_json") or "{}")
        observation = {
            **copy.deepcopy(item),
            "source_id": source,
            "declaration": review["declaration"],
            "publication_date": review["published_at"],
            "scope": (
                "EPD technical and modeled LCA observations; not a project inventory or power curve"
            ),
        }
        declarations = ext.setdefault("environmental_product_declarations", [])
        prior = [x for x in declarations if x["source_id"] == source]
        if prior:
            if prior != [observation]:
                raise ValueError("Immutable source observation changed; review a new revision")
            result.append(row)
            continue
        fs = json.loads(row["field_sources_json"])
        evidence = json.loads(row["evidence_json"])
        conflicts = json.loads(row.get("conflicts_json") or "{}")
        for field, obs in item.get("scalar_observations", {}).items():
            if field not in {"swept_area_m2", "design_life_years"}:
                raise ValueError("Unsupported EPD scalar promotion")
            if obs.get("unit") != SCHEMA["fields"][field]["unit"] or not obs.get("locator"):
                raise ValueError("Scalar observation requires exact unit and locator")
            value = obs["value"]
            if type(value) not in {int, float} or not math.isfinite(value) or value <= 0:
                raise ValueError("Invalid scalar observation")
            added = {**obs, "sources": [source], "observed_at": now}
            if field in conflicts or (row.get(field) is not None and row[field] != value):
                history = conflicts.setdefault(field, [])
                if not history:
                    history.append(
                        {
                            "value": row[field],
                            "sources": fs[field],
                            "observed_at": row["last_verified_at"],
                            "unit": obs["unit"],
                            "evidence": evidence[field],
                        }
                    )
                history.append(added)
                row[field] = None
                row["quality_status"] = "needs_review"
            else:
                row[field] = value
            fs[field] = sorted(set([*fs.get(field, []), source]))
            evidence[field] = {
                "prior_observation": evidence.get(field),
                "added_observation": added,
                "unit": obs["unit"],
                "locator": obs["locator"],
                "confidence": "high",
                "normalization": "Preserve dated revisions; null unresolved scalar conflicts",
            }
        declarations.append(observation)
        row["extensions_json"] = canonical_json(ext)
        if conflicts:
            row["conflicts_json"] = canonical_json(conflicts)
        for field in ["extensions_json"] + (["conflicts_json"] if conflicts else []):
            fs[field] = sorted(set([*fs.get(field, []), source]))
            evidence[field] = {
                "prior_observation": evidence.get(field),
                "added_observation": observation,
                "locator": item["locator"],
                "confidence": "high",
                "normalization": "Append explicitly qualified declaration observations",
            }
        row.update(
            sources=sorted(set(row["sources"] + [source])),
            updated_at=now,
            last_verified_at=now,
            field_sources_json=canonical_json(fs),
            evidence_json=canonical_json(evidence),
        )
        result.append(row)
    return sorted(result, key=lambda x: x["record_id"])
