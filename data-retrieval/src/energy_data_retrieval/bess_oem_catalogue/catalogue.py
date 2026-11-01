"""Validate reviewable BESS records and publish immutable, typed Parquet snapshots.

One row represents an OEM model/configuration with an explicit product boundary.
Active MW, apparent MVA, nominal/usable MWh and test conditions remain separate.
No network calls, inferred operating status or automatic conflict resolution.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
import unicodedata
from datetime import UTC, datetime
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


def stable_id(manufacturer: str, model: str, variant: str) -> str:
    """Choose identity once; preserve model case and distinct configuration codes."""
    parts = [
        " ".join(unicodedata.normalize("NFKC", s).split()) for s in (manufacturer, model, variant)
    ]
    if not all(parts):
        raise ValueError("Manufacturer, model and explicit variant are required")
    return str(uuid5(NAMESPACE_URL, canonical_json(["energy-data-insights/bess-oem", *parts])))


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
    """Reject unknown columns, invalid units and unsupported product specifications."""
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
            if not isinstance(decoded, dict):
                raise ValueError(f"Wrong JSON structure in {key}")
    for key in ("name", "manufacturer", "model", "variant", "capacity_scope"):
        if not row[key].strip():
            raise ValueError(f"{key} must be nonempty")
    created, updated, verified = (
        _timestamp(row[k]) for k in ("created_at", "updated_at", "last_verified_at")
    )
    if not created <= updated <= verified:
        raise ValueError("Require creation <= update <= verification")
    for quantity, bases in (
        ("power_capacity_mw", ("power_basis", "power_rating_kind")),
        ("energy_capacity_mwh", ("energy_basis", "energy_boundary")),
        (
            "round_trip_efficiency_pct",
            ("efficiency_boundary", "efficiency_qualifier", "efficiency_conditions"),
        ),
        ("cycle_life", ("cycle_life_conditions",)),
        ("warranty_years", ("warranty_conditions",)),
    ):
        if row.get(quantity) is not None and any(not row.get(k) for k in bases):
            raise ValueError(f"{quantity} requires explicit {bases}")
    for low, high in (
        ("dc_voltage_min_v", "dc_voltage_max_v"),
        ("operating_temperature_min_c", "operating_temperature_max_c"),
    ):
        if row.get(low) is not None and row.get(high) is not None and row[low] > row[high]:
            raise ValueError(f"Invalid range: {low} > {high}")
    if row["record_scope"] == "family" and any(
        row.get(k) is not None
        for k in (
            "energy_capacity_mwh",
            "power_capacity_mw",
            "apparent_power_mva",
            "duration_hours",
        )
    ):
        raise ValueError(
            "Family rating ranges belong in extensions, not single-configuration ratings"
        )
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
    """Check stable IDs and exact model/configuration identity before publication."""
    ids: set[str] = set()
    identities: set[tuple[str, ...]] = set()
    for row in rows:
        validate_record(row, sources)
        identity = tuple(
            " ".join(unicodedata.normalize("NFKC", row[k]).split())
            for k in ("manufacturer", "model", "variant")
        )
        if row["record_id"] in ids or identity in identities:
            raise ValueError("Duplicate equipment identity; reconcile model and variant")
        ids.add(row["record_id"])
        identities.add(identity)


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
        metadata={"schema_version": SCHEMA["version"], "catalogue": "bess_oem"},
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
        path = stage / "systems.parquet"
        pq.write_table(
            pa.Table.from_pylist(selected, schema=schema), path, compression="zstd", version="2.6"
        )
        report["tables"]["systems"] = {
            "rows": len(rows),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "manufacturers": sorted({r["manufacturer"] for r in rows}),
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
