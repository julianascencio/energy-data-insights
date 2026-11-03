"""Shared typed catalogue validation and immutable snapshot encoding.

Extracted from the data-center catalogue; sector-specific rules remain local.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tempfile
from datetime import date
from pathlib import Path
from typing import Any
from uuid import UUID

import pyarrow as pa
import pyarrow.parquet as pq

from energy_data_retrieval.bess_catalogue.catalogue import _source, _timestamp
from energy_data_retrieval.pv_catalogue.catalogue import ADMIN as PV_ADMIN
from energy_data_retrieval.pv_catalogue.catalogue import canonical_json

ADMIN = PV_ADMIN | {"evidence_json", "conflicts_json"}


def _json(value: str) -> Any:
    return json.loads(value, parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))


def validate_common(row: dict[str, Any], sources: dict[str, Any], schema: dict[str, Any]) -> None:
    """Enforce typed fields, units, dated provenance and null quarantines."""
    missing = [k for k in schema["required"] if row.get(k) is None]
    unknown = set(row) - schema["fields"].keys()
    if missing or unknown:
        raise ValueError(f"Missing fields {missing}; unregistered columns {sorted(unknown)}")
    if str(UUID(row["record_id"])) != row["record_id"]:
        raise ValueError("Invalid record ID")
    for key, value in row.items():
        if value is None:
            continue
        spec = schema["fields"][key]
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
            raise ValueError(f"Wrong type for {key}")
        if kind in {"float", "int"}:
            if not math.isfinite(value):
                raise ValueError(f"Non-finite {key}")
            if not spec.get("minimum", -math.inf) <= value <= spec.get("maximum", math.inf):
                raise ValueError(f"Out of range: {key}")
        if "enum" in spec and value not in spec["enum"]:
            raise ValueError(f"Invalid {key}")
        if kind == "list_string" and len(value) != len(set(value)):
            raise ValueError(f"Duplicate entries: {key}")
        if kind == "timestamp":
            _timestamp(value)
        if kind == "json" and not isinstance(
            _json(value), list if spec.get("json_container") == "list" else dict
        ):
            raise ValueError(f"Wrong JSON structure: {key}")
        if spec.get("format") == "date" and date.fromisoformat(value).isoformat() != value:
            raise ValueError(f"Use ISO date for {key}")
    created, updated, verified = (
        _timestamp(row[k]) for k in ("created_at", "updated_at", "last_verified_at")
    )
    if not created <= updated <= verified:
        raise ValueError("Require creation <= update <= verification")
    for key in ("name", "capacity_scope"):
        if not row[key].strip():
            raise ValueError(f"Empty {key}")
    if not row["sources"] or not set(row["sources"]) <= sources.keys():
        raise ValueError("Unknown or missing sources")
    for ref in row["sources"]:
        source = sources[ref]
        _source(source)
        if _timestamp(source["retrieved_at"]) > verified:
            raise ValueError("Source retrieval after verification")
        if not source.get("original_availability"):
            raise ValueError("Record original availability explicitly")
        if source.get("sha256") is not None and not re.fullmatch(r"[a-f0-9]{64}", source["sha256"]):
            raise ValueError("Invalid source checksum")
    if row.get("source_urls") is not None and row["source_urls"] != sorted(
        {sources[s]["url"] for s in row["sources"]}
    ):
        raise ValueError("Source URLs must match registry")
    evidence = _json(row["field_sources_json"])
    details = _json(row["evidence_json"])
    for key, refs in evidence.items():
        if (
            key not in schema["fields"]
            or not isinstance(refs, list)
            or not refs
            or not set(refs) <= set(row["sources"])
        ):
            raise ValueError(f"Invalid field evidence: {key}")
        detail = details.get(key)
        if (
            not isinstance(detail, dict)
            or not detail.get("locator")
            or detail.get("confidence") not in {"high", "medium", "low"}
        ):
            raise ValueError(f"Missing evidence detail: {key}")
        if (
            schema["fields"][key].get("unit")
            and detail.get("unit") != schema["fields"][key]["unit"]
        ):
            raise ValueError(f"Evidence unit mismatch: {key}")
    for key, value in row.items():
        if value is not None and key not in ADMIN and key not in evidence:
            raise ValueError(f"Missing evidence for {key}")
    conflicts = _json(row.get("conflicts_json") or "{}")
    if conflicts and row["quality_status"] != "needs_review":
        raise ValueError("Conflicts require needs_review")
    for key in conflicts:
        if key not in schema["fields"] or row.get(key) is not None:
            raise ValueError("Unresolved conflicting fields must be null")
    for observations in conflicts.values():
        if not isinstance(observations, list) or len(observations) < 2:
            raise ValueError("Conflicts require both dated observations")
        for observation in observations:
            if not isinstance(observation, dict) or "value" not in observation:
                raise ValueError("Invalid conflicting observation")
            refs = observation.get("sources")
            if not isinstance(refs, list) or not refs or not set(refs) <= set(row["sources"]):
                raise ValueError("Conflict sources must be registered on the record")
            _timestamp(observation.get("observed_at", ""))
    for estimate in _json(row.get("estimates_json") or "{}").values():
        if (
            not isinstance(estimate, dict)
            or not estimate.get("method")
            or not estimate.get("uncertainty")
        ):
            raise ValueError("Estimates require method and uncertainty")
    for certificate in _json(row.get("certifications_json") or "{}").values():
        if (
            not isinstance(certificate, dict)
            or not all(
                certificate.get(k) for k in ("issuer", "certificate", "scope", "date", "source_id")
            )
            or certificate["source_id"] not in row["sources"]
        ):
            raise ValueError("Certificates require issuer, scope, date and registered source")
        date.fromisoformat(certificate["date"])


def write_snapshot(
    output: Path,
    rows: list[dict[str, Any]],
    sources: dict[str, Any],
    spec: dict[str, Any],
    catalogue: str,
    summaries: dict[str, Any],
) -> dict[str, Any]:
    """Publish a validated, sorted JSONL projection as typed Zstandard Parquet."""
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
            for k, v in spec["fields"].items()
        ],
        metadata={"schema_version": spec["version"], "catalogue": catalogue},
    )
    report: dict[str, Any] = {
        "schema_version": spec["version"],
        "input_sha256": hashlib.sha256(
            canonical_json({"rows": rows, "sources": sources, "schema": spec}).encode()
        ).hexdigest(),
        "tables": {},
        "capacity_summaries": summaries,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError("Use a new snapshot output directory")
    with tempfile.TemporaryDirectory(dir=output.parent) as temporary:
        stage = Path(temporary) / "snapshot"
        stage.mkdir()
        for entity in spec["entity_types"]:
            selected = []
            for original in rows:
                if original["entity_type"] != entity:
                    continue
                row = dict(original)
                row["source_urls"] = sorted({sources[s]["url"] for s in row["sources"]})
                for key in ("created_at", "updated_at", "last_verified_at"):
                    row[key] = _timestamp(row[key])
                selected.append(row)
            path = stage / f"{entity}.parquet"
            pq.write_table(
                pa.Table.from_pylist(selected, schema=schema),
                path,
                compression="zstd",
                version="2.6",
                row_group_size=50000,
            )
            report["tables"][entity] = {
                "rows": len(selected),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "countries": sorted({r["country_code"] for r in selected if r.get("country_code")}),
                "manufacturers": sorted(
                    {r["manufacturer"] for r in selected if r.get("manufacturer")}
                ),
                "facilities": len(
                    {
                        r["facility_id"]
                        for r in selected
                        if r.get("facility_id") and r["record_scope"] != "campus"
                    }
                ),
                "populated_fields": {
                    k: sum(r.get(k) is not None for r in selected) for k in spec["fields"]
                },
            }
        for name, data in (("schema", spec), ("sources", sources), ("manifest", report)):
            (stage / f"{name}.json").write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        os.replace(stage, output)
    return report
