"""Deterministic JSONL source records and typed, compressed Parquet snapshots.

Network access is never implicit. Changes require field-level source references;
conflicting populated values are returned for review instead of overwritten.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import tempfile
import unicodedata
from collections import defaultdict
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from uuid import NAMESPACE_URL, UUID, uuid5

import pyarrow as pa
import pyarrow.parquet as pq

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


def canonical_json(value: Any) -> str:
    """Canonical nested JSON, rejecting non-finite numbers."""
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def stable_id(entity_type: str, *identity: str) -> str:
    """Stable identifier; keep all punctuation that may distinguish OEM models.

    Identity is chosen once. Renames become aliases; IDs never include mutable specs.
    Project identity should use a registry ID, or country + locality + original name.
    """
    if entity_type not in SCHEMA["entity_types"] or not identity or not all(identity):
        raise ValueError("An entity type and nonempty identity components are required")
    parts = [" ".join(unicodedata.normalize("NFKC", s).split()) for s in identity]
    return str(
        uuid5(NAMESPACE_URL, canonical_json(["energy-data-insights/pv", entity_type, *parts]))
    )


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.utcoffset() != UTC.utcoffset(None):
        raise ValueError("Timestamps must be timezone-aware UTC")
    return parsed


def validate_record(row: dict[str, Any], sources: dict[str, Any]) -> None:
    """Reject schema drift, unsupported values, invalid units/ranges and missing evidence."""
    missing = [key for key in SCHEMA["required"] if row.get(key) is None]
    unknown = set(row) - SCHEMA["fields"].keys()
    if missing or unknown:
        raise ValueError(f"Missing fields {missing}; unregistered columns {sorted(unknown)}")
    if row["entity_type"] not in SCHEMA["entity_types"]:
        raise ValueError("Unknown entity type")
    if str(UUID(row["record_id"])) != row["record_id"]:
        raise ValueError("Invalid record ID")
    for key, value in row.items():
        if value is None:
            continue
        kind = SCHEMA["fields"][key]["type"]
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
        if kind == "float" and not math.isfinite(value):
            raise ValueError(f"Non-finite {key}")
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
        if key.endswith("_pct") and key != "cec_adjust_pct" and not 0 <= value <= 100:
            raise ValueError(f"Percentage outside 0..100: {key}")
        if (key in {"latitude", "longitude"}) and abs(value) > (90 if key == "latitude" else 180):
            raise ValueError(f"Invalid coordinate: {key}")
        if (
            kind in {"int", "float"}
            and not key.startswith("sandia_")
            and (
                key.endswith(("_w", "_mw", "_mwh", "_m2", "_kg", "_ha", "_years", "_count"))
                or key in {"length_m", "width_m", "height_m", "capex", "cells_in_series"}
            )
            and value < 0
        ):
            raise ValueError(f"Negative physical quantity: {key}")
    created, updated, verified = (
        _timestamp(row[k]) for k in ("created_at", "updated_at", "last_verified_at")
    )
    if created > updated or created > verified:
        raise ValueError("Creation must precede update and verification")
    if not row["sources"] or not set(row["sources"]) <= sources.keys():
        raise ValueError("Unknown or missing source references")
    for source_id in row["sources"]:
        source = sources[source_id]
        if not all(source.get(k) for k in ("url", "publisher", "title", "license", "retrieved_at")):
            raise ValueError(f"Incomplete source registration: {source_id}")
        if urlsplit(source["url"]).scheme not in {"http", "https"}:
            raise ValueError("Source must be an HTTP(S) URL")
        _timestamp(source["retrieved_at"])
    evidence = json.loads(row["field_sources_json"])
    if any(k != "*" and k not in SCHEMA["fields"] for k in evidence):
        raise ValueError("Evidence refers to an unregistered column")
    if any(
        not isinstance(v, (str, list))
        or not v
        or any(source_id not in row["sources"] for source_id in (v if isinstance(v, list) else [v]))
        for v in evidence.values()
    ):
        raise ValueError("Evidence refers to an unlisted source")
    for key, value in row.items():
        if value is not None and key not in ADMIN and key not in evidence and "*" not in evidence:
            raise ValueError(f"Missing evidence for {key}")
    for low, high in (
        ("mppt_min_v", "mppt_max_v"),
        ("tracking_min_deg", "tracking_max_deg"),
        ("operating_temperature_min_c", "operating_temperature_max_c"),
    ):
        if row.get(low) is not None and row.get(high) is not None and row[low] > row[high]:
            raise ValueError(f"Invalid range: {low} > {high}")
    if row["entity_type"] == "projects":
        if not re.fullmatch(r"[A-Z]{3}", row.get("country_code", "")):
            raise ValueError("Projects require ISO alpha-3 country code")
        if row.get("technology") != "photovoltaic":
            raise ValueError("Only confirmed photovoltaic projects belong in this catalogue")
        if (row.get("latitude") is None) != (row.get("longitude") is None):
            raise ValueError("Both coordinates are required together")
        if row.get("latitude") is not None and not row.get("location_accuracy"):
            raise ValueError("Coordinates require location accuracy")
    elif not row.get("manufacturer") or not row.get("model"):
        raise ValueError("Equipment requires manufacturer and exact model")


def validate_catalogue(rows: list[dict[str, Any]], sources: dict[str, Any]) -> None:
    """Validate uniqueness, natural equipment keys and referenced equipment types."""
    lookup = {row["record_id"]: row for row in rows}
    if len(lookup) != len(rows):
        raise ValueError("Duplicate record IDs")
    natural_keys: set[tuple[str, str, str, str]] = set()
    eia_codes: set[str] = set()
    links = {
        "module_record_ids": "modules",
        "inverter_record_ids": "inverters",
        "tracker_record_ids": "trackers",
        "combiner_record_ids": "combiner_boxes",
    }
    for row in rows:
        validate_record(row, sources)
        if row["entity_type"] != "projects":
            key = (row["entity_type"], row["manufacturer"], row["model"], row.get("variant", ""))
            if key in natural_keys:
                raise ValueError("Duplicate equipment identity; reconcile source records")
            natural_keys.add(key)
        external = json.loads(row.get("external_ids_json", "{}"))
        if code := external.get("eia_plant_code"):
            if code in eia_codes:
                raise ValueError("Duplicate EIA plant crosswalk")
            eia_codes.add(code)
        for column, expected in links.items():
            for identifier in row.get(column, []):
                if identifier not in lookup or lookup[identifier]["entity_type"] != expected:
                    raise ValueError(f"Invalid equipment reference: {column}")


def load_records(root: Path) -> list[dict[str, Any]]:
    """Read the sharded, sorted JSONL working dataset."""
    rows = []
    for path in sorted((root / "records").glob("*/*.jsonl")):
        rows.extend(json.loads(line) for line in path.read_text().splitlines() if line.strip())
    ids = [row["record_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate record IDs")
    return sorted(rows, key=lambda row: row["record_id"])


def _atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", dir=path.parent, delete=False, encoding="utf-8"
    ) as f:
        f.write(content)
        temporary = Path(f.name)
    os.replace(temporary, path)


def write_records(root: Path, rows: list[dict[str, Any]]) -> None:
    """Write stable hash shards (<2 MB at launch); validate before any mutation.

    Single-writer operation: automation must use an isolated Git branch and a push
    lease. Git is the transaction/history boundary; do not share a working tree.
    """
    sources = json.loads((root / "sources.json").read_text())
    validate_catalogue(rows, sources)
    shards: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen: set[str] = set()
    for row in rows:
        validate_record(row, sources)
        if row["record_id"] in seen:
            raise ValueError("Duplicate record IDs")
        seen.add(row["record_id"])
        shard = f"{row['entity_type']}/{row['record_id'][:2]}.jsonl"
        shards[shard].append(row)
    # Full snapshot replacement. Callers must supply all retained records.
    expected = set()
    for shard, records in sorted(shards.items()):
        path = root / "records" / shard
        expected.add(path)
        content = "".join(
            canonical_json(r) + "\n" for r in sorted(records, key=lambda r: r["record_id"])
        )
        if not path.exists() or path.read_text() != content:
            _atomic_text(path, content)
    for obsolete in (root / "records").glob("*/*.jsonl"):
        if obsolete not in expected:
            obsolete.unlink()


def upsert_records(
    existing: list[dict[str, Any]], incoming: list[dict[str, Any]], *, now: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Fill nulls, preserve creation and quarantine conflicting populated fields.

    No deletion, no silent winner, no last-writer-wins. Identical observations do not
    change updated_at. Conflicts leave the entire existing record unchanged. Resolving
    one requires a reviewed explicit edit with evidence and an updated timestamp.
    """
    _timestamp(now)
    records = {r["record_id"]: dict(r) for r in existing}
    if len(records) != len(existing):
        raise ValueError("Duplicate existing IDs")
    conflicts = []
    for new in incoming:
        identifier = new["record_id"]
        old = records.get(identifier)
        if old is None:
            records[identifier] = {
                **new,
                "created_at": now,
                "updated_at": now,
                "last_verified_at": now,
            }
            continue
        if _timestamp(now) < _timestamp(old["last_verified_at"]):
            raise ValueError("Cannot upsert an older verification")
        changed = {
            k: v for k, v in new.items() if k not in ADMIN and v is not None and old.get(k) != v
        }
        collisions = {
            k: {"existing": old[k], "incoming": v}
            for k, v in changed.items()
            if old.get(k) is not None
        }
        if collisions or new["entity_type"] != old["entity_type"]:
            conflicts.append(
                {"record_id": identifier, "detected_at": now, "fields": collisions, "incoming": new}
            )
            continue
        evidence = json.loads(old["field_sources_json"])
        incoming_evidence = json.loads(new["field_sources_json"])
        for key in changed:
            evidence[key] = incoming_evidence.get(key, incoming_evidence.get("*"))
        source_ids = sorted(set(old["sources"]) | set(new["sources"]))
        content_changed = bool(changed) or source_ids != sorted(old["sources"])
        records[identifier] = {
            **old,
            **changed,
            "sources": source_ids,
            "field_sources_json": canonical_json(evidence),
            "updated_at": now if content_changed else old["updated_at"],
            "last_verified_at": now,
        }
    return sorted(records.values(), key=lambda r: r["record_id"]), conflicts


def build_parquet(root: Path, output: Path) -> dict[str, Any]:
    """Build an immutable snapshot, checksums and coverage; output must not exist.

    All five tables use an explicit union schema, including empty/all-null columns.
    Nested sources remain lists. Timestamps are native UTC Arrow timestamps.
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
        metadata={"schema_version": SCHEMA["version"]},
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError("Use a new snapshot output directory")
    report: dict[str, Any] = {"schema_version": SCHEMA["version"], "tables": {}}
    report["input_sha256"] = hashlib.sha256(
        canonical_json({"rows": rows, "sources": sources, "schema": SCHEMA}).encode()
    ).hexdigest()
    with tempfile.TemporaryDirectory(dir=output.parent) as temporary:
        stage = Path(temporary) / "snapshot"
        stage.mkdir()
        for entity in SCHEMA["entity_types"]:
            selected = [dict(row) for row in rows if row["entity_type"] == entity]
            for row in selected:
                row["source_urls"] = sorted({sources[s]["url"] for s in row["sources"]})
                for key in ("created_at", "updated_at", "last_verified_at"):
                    row[key] = _timestamp(row[key])
            path = stage / f"{entity}.parquet"
            pq.write_table(
                pa.Table.from_pylist(selected, schema=schema),
                path,
                compression="zstd",
                row_group_size=50000,
                version="2.6",
            )
            report["tables"][entity] = {
                "rows": len(selected),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "manufacturers": len(
                    {r["manufacturer"] for r in selected if r.get("manufacturer")}
                ),
                "countries": sorted({r["country_code"] for r in selected if r.get("country_code")}),
                "populated_fields": {
                    k: sum(r.get(k) is not None for r in selected) for k in SCHEMA["fields"]
                },
            }
        (stage / "schema.json").write_text(json.dumps(SCHEMA, indent=2) + "\n")
        if (root / "licenses").exists():
            shutil.copytree(root / "licenses", stage / "licenses")
        (stage / "sources.json").write_text(canonical_json(sources) + "\n")
        (stage / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
        os.replace(stage, output)
    return report
