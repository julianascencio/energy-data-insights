"""Validate reviewable BESS records and publish immutable, typed Parquet snapshots.

One row represents a named project with an explicit capacity scope. Power (MW)
and energy (MWh) are separate; neither implies usable AC output unless sourced.
No network calls, inferred operating status or automatic conflict resolution.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tempfile
import unicodedata
from datetime import UTC, date, datetime
from importlib.resources import files
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from uuid import NAMESPACE_URL, UUID, uuid5

import pyarrow as pa
import pyarrow.parquet as pq

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json, load_records

SCHEMA: dict[str, Any] = json.loads(files(__package__).joinpath("schema.json").read_text())
ADMIN = {
    "record_id",
    "entity_type",
    "created_at",
    "updated_at",
    "last_verified_at",
    "sources",
    "source_urls",
    "field_sources_json",
    "quality_status",
    "notes",
}


def stable_id(country_code: str, locality: str, original_name: str) -> str:
    """Choose identity once; renames and capacity changes must retain the ID."""
    parts = [
        " ".join(unicodedata.normalize("NFKC", s).split())
        for s in (country_code, locality, original_name)
    ]
    if not re.fullmatch(r"[A-Z]{3}", country_code) or not all(parts):
        raise ValueError("Use an ISO alpha-3 country and nonempty locality/name")
    return str(uuid5(NAMESPACE_URL, canonical_json(["energy-data-insights/bess", *parts])))


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.utcoffset() != UTC.utcoffset(None):
        raise ValueError("Timestamps must be timezone-aware UTC")
    return parsed


def _source(source: dict[str, Any]) -> None:
    if not all(source.get(k) for k in ("url", "publisher", "title", "license", "retrieved_at")):
        raise ValueError("Incomplete source registration")
    url = urlsplit(source["url"])
    if url.scheme not in {"http", "https"} or not url.netloc:
        raise ValueError("Source must be an HTTP(S) URL")
    _timestamp(source["retrieved_at"])


def validate_record(row: dict[str, Any], sources: dict[str, Any]) -> None:
    """Reject unknown columns, invalid units, undated status and unsupported facts."""
    missing = [k for k in SCHEMA["required"] if row.get(k) is None]
    unknown = set(row) - SCHEMA["fields"].keys()
    if missing or unknown:
        raise ValueError(f"Missing fields {missing}; unregistered columns {sorted(unknown)}")
    if str(UUID(row["record_id"])) != row["record_id"]:
        raise ValueError("Invalid record ID")
    for key, value in row.items():
        if value is None:
            continue
        spec = SCHEMA["fields"][key]
        kind = spec["type"]
        valid = {
            "string": isinstance(value, str),
            "json": isinstance(value, str),
            "timestamp": isinstance(value, str),
            "bool": isinstance(value, bool),
            "int": isinstance(value, int) and not isinstance(value, bool),
            "float": isinstance(value, (int, float)) and not isinstance(value, bool),
            "list_string": isinstance(value, list) and all(isinstance(v, str) for v in value),
        }[kind]
        if not valid:
            raise ValueError(f"Wrong type for {key}: {kind}")
        if kind in {"int", "float"}:
            if not math.isfinite(value):
                raise ValueError(f"Non-finite {key}")
            if value < spec.get("minimum", -math.inf) or value > spec.get("maximum", math.inf):
                raise ValueError(f"Out of range: {key}")
        if "enum" in spec and value not in spec["enum"]:
            raise ValueError(f"Invalid {key}: {value}")
        if kind == "list_string" and len(set(value)) != len(value):
            raise ValueError(f"Duplicate entries in {key}")
        if kind == "timestamp":
            _timestamp(value)
        if kind == "json":
            decoded = json.loads(
                value, parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s))
            )
            if not isinstance(decoded, list if key == "phases_json" else dict):
                raise ValueError(f"Wrong JSON structure in {key}")
        if spec.get("format") == "date" and date.fromisoformat(value).isoformat() != value:
            raise ValueError(f"Use ISO date YYYY-MM-DD for {key}")
    if not row["name"].strip() or not row["capacity_scope"].strip():
        raise ValueError("Name and capacity scope must be nonempty")
    if not re.fullmatch(r"[A-Z]{3}", row["country_code"]):
        raise ValueError("Projects require ISO alpha-3 country code")
    created, updated, verified = (
        _timestamp(row[k]) for k in ("created_at", "updated_at", "last_verified_at")
    )
    if not created <= updated <= verified:
        raise ValueError("Require creation <= update <= verification")
    if date.fromisoformat(row["status_as_of"]) > verified.date():
        raise ValueError("Status cannot be dated after source verification")
    if (row.get("latitude") is None) != (row.get("longitude") is None):
        raise ValueError("Both coordinates are required together")
    if row.get("latitude") is not None and not row.get("location_accuracy"):
        raise ValueError("Coordinates require location accuracy")
    for quantity, basis in (
        ("power_capacity_mw", "power_basis"),
        ("energy_capacity_mwh", "energy_basis"),
    ):
        if row.get(quantity) is not None and not row.get(basis):
            raise ValueError(f"{quantity} requires an explicit {basis}, even if unspecified")
    if not row["sources"] or not set(row["sources"]) <= sources.keys():
        raise ValueError("Unknown or missing source references")
    for source_id in row["sources"]:
        _source(sources[source_id])
        if _timestamp(sources[source_id]["retrieved_at"]) > verified:
            raise ValueError("Source retrieval cannot be later than record verification")
    expected_urls = sorted({sources[s]["url"] for s in row["sources"]})
    if row.get("source_urls") is not None and row["source_urls"] != expected_urls:
        raise ValueError("Source URLs must match the source registry")
    evidence = json.loads(row["field_sources_json"])
    for key, refs in evidence.items():
        if key not in SCHEMA["fields"]:
            raise ValueError(f"Evidence refers to an unregistered column: {key}")
        if (
            not isinstance(refs, list)
            or not refs
            or any(not isinstance(s, str) or s not in row["sources"] for s in refs)
        ):
            raise ValueError("Evidence refers to an unlisted source")
    for key, value in row.items():
        if value is not None and key not in ADMIN and key not in evidence:
            raise ValueError(f"Missing evidence for {key}")
    if json.loads(row.get("conflicts_json") or "{}") and row["quality_status"] != "needs_review":
        raise ValueError("Conflicting values require needs_review status")


def validate_catalogue(rows: list[dict[str, Any]], sources: dict[str, Any]) -> None:
    """Check record identity and external registry crosswalks before publication."""
    ids: set[str] = set()
    names: set[tuple[str, str, str]] = set()
    external_ids: set[tuple[str, str]] = set()
    for row in rows:
        validate_record(row, sources)
        identity = (
            row["country_code"],
            (row.get("locality") or "").casefold(),
            row["name"].casefold(),
        )
        if row["record_id"] in ids or identity in names:
            raise ValueError("Duplicate project identity; reconcile project/phase scope")
        ids.add(row["record_id"])
        names.add(identity)
        for namespace, value in json.loads(row.get("external_ids_json") or "{}").items():
            if not isinstance(value, str) or not value:
                raise ValueError("External IDs must be nonempty strings")
            crosswalk = (namespace, value)
            if crosswalk in external_ids:
                raise ValueError("Duplicate external project ID")
            external_ids.add(crosswalk)


def build_parquet(root: Path, output: Path) -> dict[str, Any]:
    """Build a new Zstandard snapshot, preserving nulls and field/source metadata.

    Output must not exist. Canonical records remain in Git; the manifest identifies
    the exact schema, records and source registry used to reproduce the snapshot.
    """
    rows = load_records(root)
    sources = json.loads((root / "sources.json").read_text())
    validate_catalogue(rows, sources)
    types = {
        "string": pa.string(),
        "json": pa.string(),
        "float": pa.float64(),
        "int": pa.int64(),
        "bool": pa.bool_(),
        "list_string": pa.list_(pa.string()),
        "timestamp": pa.timestamp("us", tz="UTC"),
    }
    schema = pa.schema(
        [
            pa.field(
                k,
                types[v["type"]],
                metadata={"description": v["description"], "unit": v.get("unit", "")},
            )
            for k, v in SCHEMA["fields"].items()
        ],
        metadata={"schema_version": SCHEMA["version"], "catalogue": "bess"},
    )
    report: dict[str, Any] = {
        "schema_version": SCHEMA["version"],
        "input_sha256": hashlib.sha256(
            canonical_json({"rows": rows, "sources": sources, "schema": SCHEMA}).encode()
        ).hexdigest(),
        "tables": {},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError("Use a new snapshot output directory")
    with tempfile.TemporaryDirectory(dir=output.parent) as temporary:
        stage = Path(temporary) / "snapshot"
        stage.mkdir()
        selected = []
        for original in rows:
            row = dict(original)
            row["source_urls"] = sorted({sources[s]["url"] for s in row["sources"]})
            for key, spec in SCHEMA["fields"].items():
                if spec["type"] == "timestamp" and row.get(key) is not None:
                    row[key] = _timestamp(row[key])
            selected.append(row)
        path = stage / "projects.parquet"
        pq.write_table(
            pa.Table.from_pylist(selected, schema=schema), path, compression="zstd", version="2.6"
        )
        report["tables"]["projects"] = {
            "rows": len(rows),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "countries": sorted({r["country_code"] for r in rows}),
            "populated_fields": {
                k: sum(r.get(k) is not None for r in selected) for k in SCHEMA["fields"]
            },
        }
        for name, content in (("schema", SCHEMA), ("sources", sources), ("manifest", report)):
            (stage / f"{name}.json").write_text(
                json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        os.replace(stage, output)
    return report
