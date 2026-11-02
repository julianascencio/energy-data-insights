"""Evidence-bound data center projects and exact OEM models, using JSONL/Parquet.

Reuse the PV catalogue's canonical encoding, shard reader and non-overwriting
upsert. No network access, geocoding or inferred IT capacity occurs here.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tempfile
import unicodedata
from datetime import date
from importlib.resources import files
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

import pyarrow as pa
import pyarrow.parquet as pq

from energy_data_retrieval.bess_catalogue.catalogue import _source, _timestamp
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
            key not in SCHEMA["fields"]
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
            SCHEMA["fields"][key].get("unit")
            and detail.get("unit") != SCHEMA["fields"][key]["unit"]
        ):
            raise ValueError(f"Evidence unit mismatch: {key}")
    for key, value in row.items():
        if value is not None and key not in ADMIN and key not in evidence:
            raise ValueError(f"Missing evidence for {key}")
    conflicts = _json(row.get("conflicts_json") or "{}")
    if conflicts and row["quality_status"] != "needs_review":
        raise ValueError("Conflicts require needs_review")
    for key in conflicts:
        if key not in SCHEMA["fields"] or row.get(key) is not None:
            raise ValueError("Unresolved conflicting fields must be null")
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
                        }
                    ],
                )
                observation = {
                    "value": value,
                    "sources": new["sources"],
                    "evidence": new_evidence.get(key),
                    "observed_at": now,
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
        metadata={"schema_version": SCHEMA["version"], "catalogue": "data_centers"},
    )
    report: dict[str, Any] = {
        "schema_version": SCHEMA["version"],
        "input_sha256": hashlib.sha256(
            canonical_json({"rows": rows, "sources": sources, "schema": SCHEMA}).encode()
        ).hexdigest(),
        "tables": {},
        "capacity_summaries": {k: capacity_summary(rows, k) for k in CAPACITIES},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError("Use a new snapshot output directory")
    with tempfile.TemporaryDirectory(dir=output.parent) as temporary:
        stage = Path(temporary) / "snapshot"
        stage.mkdir()
        for entity in SCHEMA["entity_types"]:
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
                    k: sum(r.get(k) is not None for r in selected) for k in SCHEMA["fields"]
                },
            }
        for name, data in (("schema", SCHEMA), ("sources", sources), ("manifest", report)):
            (stage / f"{name}.json").write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        os.replace(stage, output)
    return report
