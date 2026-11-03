"""Evidence-bound data center projects and exact OEM models, using JSONL/Parquet.

Reuse the PV catalogue's canonical encoding, shard reader and non-overwriting
upsert. No network access, geocoding or inferred IT capacity occurs here.
"""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import date
from importlib.resources import files
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from energy_data_retrieval.bess_catalogue.catalogue import _timestamp
from energy_data_retrieval.catalogue_common import validate_common, write_snapshot
from energy_data_retrieval.pv_catalogue.catalogue import (
    ADMIN as PV_ADMIN,
)
from energy_data_retrieval.pv_catalogue.catalogue import (
    canonical_json,
    load_records,
)
from energy_data_retrieval.pv_catalogue.catalogue import (
    upsert_records as pv_upsert,
)

SCHEMA: dict[str, Any] = json.loads(files(__package__).joinpath("schema.json").read_text())
ADMIN = PV_ADMIN | {"evidence_json", "conflicts_json"}
CAPACITIES = ("it_capacity_mw", "grid_capacity_mw", "facility_capacity_mw")


def stable_id(entity_type: str, *identity: str) -> str:
    """Choose immutable external identity once; keep model punctuation/case."""
    if entity_type not in {*SCHEMA["entity_types"], "campus", "facility", "organization"}:
        raise ValueError("Unknown identity type")
    parts = [" ".join(unicodedata.normalize("NFKC", s).split()) for s in identity]
    if not parts or not all(parts):
        raise ValueError("Nonempty identity components required")
    return str(
        uuid5(
            NAMESPACE_URL,
            canonical_json(["energy-data-insights/data-centers", entity_type, *parts]),
        )
    )


def _json(value: str) -> Any:
    return json.loads(value, parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))


def validate_record(row: dict[str, Any], sources: dict[str, Any]) -> None:
    """Validate units, evidence, scope and nullable ratings before any publication."""
    validate_common(row, sources, SCHEMA)
    verified = _timestamp(row["last_verified_at"])
    renewable = _json(row.get("renewable_supply_json") or "{}")
    if renewable:
        groups = {"physical_generation", "contractual_procurement", "environmental_claims"}
        if set(renewable) != groups or any(not isinstance(renewable[k], list) for k in groups):
            raise ValueError("Separate physical, contractual and environmental supply claims")
        for item in (item for group in renewable.values() for item in group):
            if not isinstance(item, dict) or item.get("source_id") not in row["sources"]:
                raise ValueError("Renewable supply observations need registered sources")
    for quantity, conditions in (
        *((k, (k.removesuffix("_mw") + "_basis",)) for k in CAPACITIES),
        ("accelerator_power_w", ("power_rating_kind", "power_conditions")),
        ("input_power_kw", ("power_rating_kind", "power_conditions")),
        ("output_power_kw", ("power_rating_kind", "power_conditions")),
        ("peak_power_kw", ("power_conditions",)),
        ("cooling_capacity_kw", ("cooling_rating_conditions",)),
        ("efficiency_pct", ("efficiency_conditions",)),
        ("runtime_minutes", ("runtime_load_kw", "power_conditions")),
        ("warranty_years", ("warranty_conditions",)),
    ):
        if row.get(quantity) is not None and any(row.get(k) is None for k in conditions):
            raise ValueError(f"{quantity} requires {conditions}")
    if row.get("efficiency_pct") is not None and row["efficiency_pct"] > 100:
        raise ValueError("Efficiency outside 0..100")
    if (
        row.get("temperature_min_c") is not None
        and row.get("temperature_max_c") is not None
        and row["temperature_min_c"] > row["temperature_max_c"]
    ):
        raise ValueError("Invalid temperature range")
    for obs in _json(row.get("observations_json") or "[]"):
        required = {"field", "value", "unit", "source_id", "locator", "boundary", "as_of", "kind"}
        if (
            not isinstance(obs, dict)
            or not required <= obs.keys()
            or obs["source_id"] not in row["sources"]
        ):
            raise ValueError("Incomplete observation evidence")
        if obs["field"] in {"pue", "wue"} and (
            obs["kind"] not in {"measured", "design", "target", "unspecified"}
            or "measurement_period" not in obs
        ):
            raise ValueError(
                "PUE/WUE require metric kind and measurement period (null if undisclosed)"
            )
    if row["entity_type"] == "projects":
        required = (
            "country_code",
            "facility_id",
            "aggregation_role",
            "status",
            "status_as_of",
            "status_date_basis",
            "facility_type",
        )
        if any(not row.get(k) for k in required):
            raise ValueError("Incomplete project identity/status")
        if not re.fullmatch(r"[A-Z]{3}", row["country_code"]):
            raise ValueError("Projects require ISO alpha-3 country")
        if row["record_scope"] not in {"facility", "phase", "campus"}:
            raise ValueError("Invalid project scope")
        if row["record_scope"] == "campus" and row["aggregation_role"] != "aggregate":
            raise ValueError("Campus totals must be aggregate")
        if row["record_scope"] == "phase" and not row.get("phase_id"):
            raise ValueError("Phase identifier required")
        if date.fromisoformat(row["status_as_of"]) > verified.date():
            raise ValueError("Future status evidence")
        if (row.get("latitude") is None) != (row.get("longitude") is None):
            raise ValueError("Both coordinates required")
        if row.get("latitude") is not None and not row.get("location_accuracy"):
            raise ValueError("Coordinates require precision")
    elif row["record_scope"] not in {"model", "configuration"} or any(
        not row.get(k) for k in ("manufacturer", "model", "variant", "equipment_category")
    ):
        raise ValueError("Equipment requires exact model/configuration")


def validate_catalogue(
    rows: list[dict[str, Any]],
    sources: dict[str, Any],
    *,
    bess_projects: set[str] | None = None,
    bess_equipment: set[str] | None = None,
) -> None:
    """Reject duplicate identities, cycles, orphan links and unsafe aggregate roles."""
    lookup = {r["record_id"]: r for r in rows}
    if len(lookup) != len(rows):
        raise ValueError("Duplicate record IDs")
    identities: set[tuple[str, ...]] = set()
    external: set[tuple[str, str, str]] = set()
    for row in rows:
        validate_record(row, sources)
        identity = (
            (row["entity_type"], row["facility_id"], row.get("phase_id") or "")
            if row["entity_type"] == "projects"
            else (row["entity_type"], row["manufacturer"], row["model"], row["variant"])
        )
        normalized = tuple(" ".join(unicodedata.normalize("NFKC", x).split()) for x in identity)
        if normalized in identities:
            raise ValueError("Duplicate natural identity")
        identities.add(normalized)
        for key, value in _json(row.get("external_ids_json") or "{}").items():
            if not isinstance(value, str) or not value:
                raise ValueError("External IDs must be nonempty strings")
            crosswalk = row["entity_type"], key, value
            if crosswalk in external:
                raise ValueError("Duplicate external identity")
            external.add(crosswalk)
        for linked in row.get("equipment_record_ids") or []:
            if linked not in lookup or lookup[linked]["entity_type"] != "equipment":
                raise ValueError("Invalid equipment relationship")
        for key, known in (
            ("bess_project_record_ids", bess_projects),
            ("bess_equipment_record_ids", bess_equipment),
        ):
            if row.get(key) and (known is None or not set(row[key]) <= known):
                raise ValueError(f"Unverified cross-catalogue link: {key}")
        visited = {row["record_id"]}
        child = row
        while parent := child.get("parent_record_id"):
            if (
                parent in visited
                or parent not in lookup
                or lookup[parent]["entity_type"] != "projects"
            ):
                raise ValueError("Invalid or cyclic parent")
            visited.add(parent)
            child = lookup[parent]
            if child["aggregation_role"] != "aggregate":
                raise ValueError("Parent capacities must be excluded as aggregate")


def capacity_summary(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    """Sum compatible basis groups only; exclude overlaps and keep unknown as null.

    Unresolved overlap groups are conservatively excluded even after filtering. Aggregate
    exclusions are persistent, independent of filters, so filtering out children
    cannot turn an overlapping campus total into an eligible facility.
    """
    if field not in CAPACITIES:
        raise ValueError("Select an explicit IT, grid or facility capacity")
    projects = [r for r in rows if r["entity_type"] == "projects"]
    eligible = [r for r in projects if r.get("aggregation_role") in {"independent", "child"}]
    selected = [r for r in eligible if not r.get("overlap_group")]
    result: dict[str, Any] = {
        "excluded": len(projects) - len(selected),
        "unknown": sum(r.get(field) is None for r in selected),
        "by_basis": {},
    }
    basis_key = field.removesuffix("_mw") + "_basis"
    for row in selected:
        if row.get(field) is not None:
            basis = row[basis_key]
            item = result["by_basis"].setdefault(basis, {"reported_mw": 0.0, "records": 0})
            item["reported_mw"] += row[field]
            item["records"] += 1
    return result


def upsert_records(
    existing: list[dict[str, Any]], incoming: list[dict[str, Any]], *, now: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Reuse PV upsert for safe facts; quarantine only conflicting fields.

    Source dates/boundaries travel with both observations. Creation timestamps
    survive. Empty incoming values never erase facts. Identical rows do not churn
    updated_at. Explicit review is needed to resolve quarantined fields.
    """
    records = {r["record_id"]: dict(r) for r in existing}
    if len(records) != len(existing) or len({r["record_id"] for r in incoming}) != len(incoming):
        raise ValueError("Duplicate incoming/existing identity")
    conflicts = []
    for candidate in incoming:
        new = dict(candidate)
        old = records.get(new["record_id"])
        if old is None:
            records[new["record_id"]] = {
                **new,
                "created_at": now,
                "updated_at": now,
                "last_verified_at": now,
            }
            continue
        if old["entity_type"] != new["entity_type"]:
            raise ValueError("Cannot change entity type")
        quarantine = _json(old.get("conflicts_json") or "{}")
        old_evidence, new_evidence = _json(old["evidence_json"]), _json(new["evidence_json"])
        safe = {k: v for k, v in new.items() if k not in {"evidence_json", "conflicts_json"}}
        clean_old = {k: v for k, v in old.items() if k not in {"evidence_json", "conflicts_json"}}
        for key, value in new.items():
            if key in ADMIN or value is None:
                continue
            if key in quarantine or (old.get(key) is not None and old[key] != value):
                observations = quarantine.setdefault(
                    key,
                    [
                        {
                            "value": old.get(key),
                            "sources": old["sources"],
                            "evidence": old_evidence.get(key),
                            "observed_at": old["last_verified_at"],
                            "boundary": old["capacity_scope"],
                        }
                    ],
                )
                observation = {
                    "value": value,
                    "sources": new["sources"],
                    "evidence": new_evidence.get(key),
                    "observed_at": now,
                    "boundary": new["capacity_scope"],
                }
                if not any(
                    o["value"] == value and o["sources"] == new["sources"] for o in observations
                ):
                    observations.append(observation)
                safe.pop(key, None)
                clean_old[key] = None
        merged, unexpected = pv_upsert([clean_old], [safe], now=now)
        if unexpected:
            raise ValueError("Unexpected upsert conflict")
        result = merged[0]
        details = {
            **old_evidence,
            **{k: v for k, v in new_evidence.items() if k in safe and safe[k] is not None},
        }
        result["evidence_json"] = canonical_json(details)
        if quarantine:
            result["conflicts_json"] = canonical_json(quarantine)
            result["quality_status"] = "needs_review"
            conflicts.append({"record_id": result["record_id"], "fields": quarantine})
        changed = any(
            result.get(k) != old.get(k)
            for k in set(result) | set(old)
            if k not in {"last_verified_at", "updated_at"}
        )
        result["updated_at"] = now if changed else old["updated_at"]
        records[result["record_id"]] = result
    return sorted(records.values(), key=lambda r: r["record_id"]), conflicts


def build_parquet(root: Path, output: Path) -> dict[str, Any]:
    """Build both immutable Zstandard tables and a reproducible coverage manifest."""
    rows = load_records(root)
    sources = json.loads((root / "sources.json").read_text())

    def ids(path: Path) -> set[str]:
        return {r["record_id"] for r in load_records(path)}

    validate_catalogue(
        rows,
        sources,
        bess_projects=ids(root.parent / "bess"),
        bess_equipment=ids(root.parent / "bess_oem"),
    )
    return write_snapshot(
        output,
        rows,
        sources,
        SCHEMA,
        "data_centers",
        {k: capacity_summary(rows, k) for k in CAPACITIES},
    )
