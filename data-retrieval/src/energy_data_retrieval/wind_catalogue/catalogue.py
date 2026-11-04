"""Wind-specific identity, capacity and performance boundaries. No implicit network I/O."""

from __future__ import annotations

import json
import math
import re
import unicodedata
from datetime import date
from importlib.resources import files
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from energy_data_retrieval.catalogue_common import validate_common, write_snapshot
from energy_data_retrieval.data_center_catalogue.catalogue import upsert_records as _upsert_records
from energy_data_retrieval.pv_catalogue.catalogue import canonical_json, load_records

SCHEMA: dict[str, Any] = json.loads(files(__package__).joinpath("schema.json").read_text())
CAPACITIES = (
    "installed_capacity_mw",
    "commissioned_capacity_mw",
    "planned_capacity_mw",
    "awarded_capacity_mw",
    "export_capacity_mw",
    "historical_capacity_mw",
)


def stable_id(entity_type: str, *identity: str) -> str:
    """Freeze an external ID or reviewed natural identity; never include mutable ratings."""
    parts = [" ".join(unicodedata.normalize("NFKC", s).split()) for s in identity]
    if entity_type not in SCHEMA["entity_types"] or not parts or not all(parts):
        raise ValueError("Require entity type and nonempty identity")
    return str(
        uuid5(NAMESPACE_URL, canonical_json(["energy-data-insights/wind", entity_type, *parts]))
    )


def validate_record(row: dict[str, Any], sources: dict[str, Any]) -> None:
    """Require provenance and explicit periods, units, modes and physical boundaries."""
    validate_common(row, sources, SCHEMA)
    entity = row["entity_type"]
    if entity == "projects":
        if not re.fullmatch(r"[A-Z]{3}", row.get("country_code", "")):
            raise ValueError("Require ISO alpha-3 country")
        if row["record_scope"] not in {"farm", "phase", "group", "repowering_generation"}:
            raise ValueError("Invalid project scope")
        if not all(
            row.get(k)
            for k in (
                "aggregation_role",
                "status",
                "status_as_of",
                "status_date_basis",
                "technology",
            )
        ):
            raise ValueError("Project requires dated status, technology and aggregation role")
        if date.fromisoformat(row["status_as_of"]) > date.fromisoformat(
            row["last_verified_at"][:10]
        ):
            raise ValueError("Future status observation")
        if row["record_scope"] == "group" and row["aggregation_role"] != "aggregate":
            raise ValueError("Groups must be aggregate")
        if row["record_scope"] == "phase" and not row.get("phase_id"):
            raise ValueError("Phase requires stable phase_id")
        if row["record_scope"] == "repowering_generation" and not row.get("generation_id"):
            raise ValueError("Repowering requires generation identity")
        if row.get("historical_capacity_mw") is not None and not row.get("capacity_reference_year"):
            raise ValueError("Historical capacity requires a reference year")
    elif entity == "equipment":
        if row["record_scope"] not in {"model", "configuration"} or not all(
            row.get(k) for k in ("manufacturer", "model", "variant", "equipment_category")
        ):
            raise ValueError("Require exact equipment identity")
    elif entity == "turbines":
        if row["record_scope"] != "turbine" or not row.get("project_record_id"):
            raise ValueError("Turbine requires a parent project")
    elif entity == "curves":
        _validate_curve(row)
    if (row.get("latitude") is None) != (row.get("longitude") is None):
        raise ValueError("Coordinates must be paired")
    if row.get("latitude") is not None and not row.get("location_accuracy"):
        raise ValueError("Coordinates require precision")
    for quantity, condition in (
        ("rated_power_kw", "rated_power_conditions"),
        ("sound_power_db_a", "acoustic_conditions"),
        ("warranty_years", "warranty_conditions"),
        ("design_life_years", "design_life_conditions"),
    ):
        if row.get(quantity) is not None and not row.get(condition):
            raise ValueError(f"{quantity} requires {condition}")
    for low, high in (
        ("temperature_min_c", "temperature_max_c"),
        ("water_depth_min_m", "water_depth_max_m"),
        ("rotor_speed_min_rpm", "rotor_speed_max_rpm"),
    ):
        if row.get(low) is not None and row.get(high) is not None and row[low] > row[high]:
            raise ValueError("Reversed range")
    fleet = json.loads(row.get("fleet_json") or "[]")
    if fleet and row.get("fleet_completeness") not in {"complete", "partial"}:
        raise ValueError("Fleet must declare completeness")
    for item in fleet:
        if (
            not isinstance(item, dict)
            or not all(item.get(k) for k in ("manufacturer", "model", "source_id"))
            or item["source_id"] not in row["sources"]
        ):
            raise ValueError("Fleet composition requires explicit model and provenance")
        count = item.get("count")
        if count is not None and (type(count) is not int or count < 0):
            raise ValueError("Invalid fleet count")
    if (
        fleet
        and all(x.get("count") is not None for x in fleet)
        and row.get("turbine_count") is not None
        and (
            sum(x["count"] for x in fleet) > row["turbine_count"]
            or (
                row.get("fleet_completeness") == "complete"
                and sum(x["count"] for x in fleet) != row["turbine_count"]
            )
        )
    ):
        raise ValueError("Mixed fleet count does not match reported turbine count")
    for key in ("observations_json", "resource_observations_json"):
        for obs in json.loads(row.get(key) or "[]"):
            required = {
                "field",
                "value",
                "unit",
                "kind",
                "period",
                "boundary",
                "source_id",
                "locator",
            }
            if (
                not isinstance(obs, dict)
                or not required <= obs.keys()
                or obs["source_id"] not in row["sources"]
            ):
                raise ValueError("Observation requires period, boundary and provenance")
            if obs["kind"] not in {"measured", "reported", "modeled", "design"}:
                raise ValueError("Invalid observation kind")
            if key == "resource_observations_json" and "height_m" not in obs:
                raise ValueError("Resource observation requires height (null if unknown)")


def _validate_curve(row: dict[str, Any]) -> None:
    required = (
        "equipment_record_id",
        "curve_kind",
        "curve_origin",
        "curve_conditions",
        "curve_points_json",
        "curve_value_unit",
    )
    if row["record_scope"] != "curve" or any(row.get(k) is None for k in required):
        raise ValueError("Incomplete curve")
    unit = "kW" if row["curve_kind"] == "power" else "1"
    if row["curve_value_unit"] != unit:
        raise ValueError("Wrong curve unit")
    conditions = json.loads(row["curve_conditions"])
    if (
        not {"air_density_kg_m3", "operating_mode", "wind_speed_unit"} <= conditions.keys()
        or conditions["wind_speed_unit"] != "m/s"
    ):
        raise ValueError("Curve requires density/mode (null if undisclosed) and m/s")
    points = json.loads(row["curve_points_json"])
    previous = -math.inf
    if len(points) < 2:
        raise ValueError("Curve requires at least two points")
    for point in points:
        if set(point) != {"wind_speed_m_s", "value"} or any(
            type(v) not in {int, float} or not math.isfinite(v) or v < 0 for v in point.values()
        ):
            raise ValueError("Invalid curve point")
        if point["wind_speed_m_s"] <= previous:
            raise ValueError("Curve wind speeds must be strictly increasing")
        previous = point["wind_speed_m_s"]


def validate_catalogue(rows: list[dict[str, Any]], sources: dict[str, Any]) -> None:
    """Reject duplicate identities, dangling links, parent cycles and unsafe sums."""
    lookup = {r["record_id"]: r for r in rows}
    if len(lookup) != len(rows):
        raise ValueError("Duplicate record ID")
    external: set[tuple[str, str, str]] = set()
    equipment: set[tuple[str, ...]] = set()
    for row in rows:
        validate_record(row, sources)
        for namespace, value in json.loads(row.get("external_ids_json") or "{}").items():
            if not isinstance(value, str) or not value:
                raise ValueError("Invalid registry identity")
            key = row["entity_type"], namespace, value
            if key in external:
                raise ValueError("Duplicate external ID")
            external.add(key)
        if row["entity_type"] == "equipment":
            natural = tuple(
                " ".join(unicodedata.normalize("NFKC", row[k]).split())
                for k in ("manufacturer", "model", "variant")
            )
            if natural in equipment:
                raise ValueError("Duplicate exact model")
            equipment.add(natural)
        for key, target in (
            ("project_record_id", "projects"),
            ("equipment_record_id", "equipment"),
            ("replaces_record_id", "projects"),
        ):
            linked = row.get(key)
            if linked and (
                linked == row["record_id"]
                or linked not in lookup
                or lookup[linked]["entity_type"] != target
            ):
                raise ValueError(f"Invalid {key}")
        links = (row.get("equipment_record_ids") or []) + [
            x["equipment_record_id"]
            for x in json.loads(row.get("fleet_json") or "[]")
            if x.get("equipment_record_id")
        ]
        if any(k not in lookup or lookup[k]["entity_type"] != "equipment" for k in links):
            raise ValueError("Invalid equipment link")
        for link in json.loads(row.get("compatibility_json") or "[]"):
            if (
                not isinstance(link, dict)
                or link.get("equipment_record_id") == row["record_id"]
                or link.get("equipment_record_id") not in lookup
                or lookup[link["equipment_record_id"]]["entity_type"] != "equipment"
                or link.get("source_id") not in row["sources"]
                or not link.get("locator")
                or not link.get("conditions")
            ):
                raise ValueError("Compatibility requires an exact target and explicit evidence")
        if replaced := row.get("replaces_record_id"):
            old = lookup[replaced]
            if old.get("status") != "decommissioned" and (
                not row.get("overlap_group") or row.get("overlap_group") != old.get("overlap_group")
            ):
                raise ValueError("Unresolved repowering generations need a shared overlap group")
        for relationship in ("parent_record_id", "replaces_record_id"):
            visited = {row["record_id"]}
            child = row
            while parent := child.get(relationship):
                if (
                    parent in visited
                    or parent not in lookup
                    or lookup[parent]["entity_type"] != "projects"
                ):
                    raise ValueError("Invalid or cyclic project relationship")
                visited.add(parent)
                child = lookup[parent]
                if relationship == "parent_record_id" and child["aggregation_role"] != "aggregate":
                    raise ValueError("Parent must be aggregate")


def capacity_summary(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    """Exclude parent/overlap scopes; keep retired generations in their own lifecycle."""
    if field not in CAPACITIES:
        raise ValueError("Choose an explicit wind capacity category")
    projects = [r for r in rows if r["entity_type"] == "projects"]
    selected = [
        r
        for r in projects
        if r.get("aggregation_role") in {"independent", "child"} and not r.get("overlap_group")
    ]
    result: dict[str, Any] = {
        "excluded": len(projects) - len(selected),
        "unknown": sum(r.get(field) is None for r in selected),
        "by_status": {},
    }
    for row in selected:
        if row.get(field) is None:
            continue
        key = row["status"] + (
            f"@{row['capacity_reference_year']}" if field == "historical_capacity_mw" else ""
        )
        group = result["by_status"].setdefault(key, {"reported_mw": 0.0, "records": 0})
        group["reported_mw"] += row[field]
        group["records"] += 1
    return result


def build_parquet(root: Path, output: Path) -> dict[str, Any]:
    """Reuse canonical JSONL and typed, deterministic immutable snapshot writer."""
    rows = load_records(root)
    sources = json.loads((root / "sources.json").read_text())
    validate_catalogue(rows, sources)
    return write_snapshot(
        output, rows, sources, SCHEMA, "wind", {k: capacity_summary(rows, k) for k in CAPACITIES}
    )


def upsert_records(
    existing: list[dict[str, Any]], incoming: list[dict[str, Any]], *, now: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Reuse dated conflict quarantine, preserving record creation and defensible fields."""
    return _upsert_records(existing, incoming, now=now)


__all__ = [
    "SCHEMA",
    "build_parquet",
    "capacity_summary",
    "stable_id",
    "upsert_records",
    "validate_catalogue",
    "validate_record",
]
