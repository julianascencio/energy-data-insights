"""Hydropower identity, physical boundaries and deterministic offline snapshots."""

from __future__ import annotations

import json
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
    "operational_capacity_mw",
    "planned_capacity_mw",
    "pumping_capacity_mw",
    "historical_capacity_mw",
)


def stable_id(entity_type: str, *identity: str) -> str:
    """Use immutable registry identity, never mutable plant capacity or ownership."""
    parts = [" ".join(unicodedata.normalize("NFKC", s).split()) for s in identity]
    if entity_type not in SCHEMA["entity_types"] or not parts or not all(parts):
        raise ValueError("Require registered entity type and nonempty identity")
    return str(
        uuid5(NAMESPACE_URL, canonical_json(["energy-data-insights/hydro", entity_type, *parts]))
    )


def validate_record(row: dict[str, Any], sources: dict[str, Any]) -> None:
    """Validate provenance, coordinates, status dates and hydraulic quantities."""
    validate_common(row, sources, SCHEMA)
    if not re.fullmatch(r"[A-Z]{3}", row.get("country_code", "")):
        raise ValueError("Require ISO alpha-3 country")
    for key in ("status", "status_as_of", "status_date_basis", "technology", "aggregation_role"):
        if not row.get(key):
            raise ValueError(f"Require {key}")
    if date.fromisoformat(row["status_as_of"]) > date.fromisoformat(row["last_verified_at"][:10]):
        raise ValueError("Future status observation")
    if row["record_scope"] == "complex" and row["aggregation_role"] != "aggregate":
        raise ValueError("Complex must be aggregate")
    if row["aggregation_role"] == "child" and not row.get("parent_record_id"):
        raise ValueError("Child requires parent")
    if row.get("historical_capacity_mw") is not None and not row.get("capacity_reference_year"):
        raise ValueError("Historical capacity requires reference year")
    if (row.get("latitude") is None) != (row.get("longitude") is None):
        raise ValueError("Coordinates must be paired")
    if row.get("latitude") is not None and not row.get("location_accuracy"):
        raise ValueError("Coordinates require precision")
    for low, high in (
        ("net_head_m", "gross_head_m"),
        ("usable_reservoir_volume_m3", "reservoir_volume_m3"),
    ):
        if row.get(low) is not None and row.get(high) is not None and row[low] > row[high]:
            raise ValueError(f"{low} exceeds {high}")
    for obs in json.loads(row.get("observations_json") or "[]"):
        if (
            not {"field", "value", "unit", "kind", "period", "boundary", "source_id", "locator"}
            <= obs.keys()
        ):
            raise ValueError("Observation needs period, boundary and evidence")
        if obs["source_id"] not in row["sources"] or obs["kind"] not in {
            "reported",
            "measured",
            "modeled",
            "design",
        }:
            raise ValueError("Invalid observation provenance")


def validate_catalogue(rows: list[dict[str, Any]], sources: dict[str, Any]) -> None:
    """Reject duplicate IDs, external identities and invalid/cyclic hierarchy."""
    lookup = {r["record_id"]: r for r in rows}
    if len(lookup) != len(rows):
        raise ValueError("Duplicate record ID")
    seen: set[tuple[str, str]] = set()
    for row in rows:
        validate_record(row, sources)
        for registry, value in json.loads(row.get("external_ids_json") or "{}").items():
            key = (registry, str(value))
            if key in seen:
                raise ValueError("Duplicate registry identity")
            seen.add(key)
        visited = {row["record_id"]}
        child = row
        while parent := child.get("parent_record_id"):
            if parent not in lookup or parent in visited:
                raise ValueError("Invalid or cyclic parent")
            visited.add(parent)
            child = lookup[parent]
            if child["aggregation_role"] != "aggregate":
                raise ValueError("Parent capacity must be excluded as aggregate")


def capacity_summary(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    """Separate lifecycle, technology and historical vintage; exclude ambiguous scopes."""
    if field not in CAPACITIES:
        raise ValueError("Choose an explicit hydro capacity category")
    selected = [
        r
        for r in rows
        if r["aggregation_role"] in {"independent", "child"} and not r.get("overlap_group")
    ]
    result: dict[str, Any] = {
        "excluded": len(rows) - len(selected),
        "unknown": sum(r.get(field) is None for r in selected),
        "by_status": {},
    }
    for row in selected:
        if row.get(field) is None:
            continue
        key = row["status"] + "/" + row["technology"]
        if field == "historical_capacity_mw":
            key += f"@{row['capacity_reference_year']}"
        group = result["by_status"].setdefault(key, {"reported_mw": 0.0, "records": 0})
        group["reported_mw"] += row[field]
        group["records"] += 1
    return result


def build_parquet(root: Path, output: Path) -> dict[str, Any]:
    """Validate JSONL and publish an immutable, typed Zstandard snapshot."""
    rows = load_records(root)
    sources = json.loads((root / "sources.json").read_text())
    validate_catalogue(rows, sources)
    return write_snapshot(
        output, rows, sources, SCHEMA, "hydro", {k: capacity_summary(rows, k) for k in CAPACITIES}
    )


def upsert_records(
    existing: list[dict[str, Any]], incoming: list[dict[str, Any]], *, now: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Preserve creation dates and quarantine conflicts using the shared upsert."""
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
