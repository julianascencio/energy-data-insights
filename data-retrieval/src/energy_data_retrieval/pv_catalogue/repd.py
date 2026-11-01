"""Offline DESNZ REPD staging, with explicit reviewed identities before acceptance.

REPD rows describe planning applications, not necessarily distinct physical plants.
The screening function only flags candidates: it never merges names or phases.
"""

from __future__ import annotations

import csv
import io
import math
import re
from collections import Counter
from datetime import date, datetime
from typing import Any

from .catalogue import canonical_json, stable_id
from .sam import verify_sha256

REQUIRED = {
    "Ref ID",
    "Site Name",
    "Technology Type",
    "Country",
    "Region",
    "County",
    "Installed Capacity (MWelec)",
    "Development Status (short)",
    "Record Last Updated (dd/mm/yyyy)",
    "Mounting Type for Solar",
    "Operational",
    "X-coordinate",
    "Y-coordinate",
    "Planning Authority",
    "Planning Application Reference",
    "Are they re-applying (New REPD Ref)",
    "Are they re-applying (Old REPD Ref)",
    "Solar Site Area (sqm)",
}
MISSING = {"", "NA", "N/A", "Not set"}


def read_repd_csv(content: bytes, *, sha256: str) -> list[dict[str, str]]:
    """Check pinned bytes and schema; decode the publisher's Windows-1252 CSV."""
    verify_sha256(content, sha256)
    if len(content) > 25_000_000:
        raise ValueError("REPD extract exceeds size limit")
    reader = csv.DictReader(io.StringIO(content.decode("cp1252")))
    headers = [key.strip() for key in reader.fieldnames or []]
    if len(set(headers)) != len(headers) or not set(headers) >= REQUIRED:
        raise ValueError("REPD columns changed; review adapter")
    rows = []
    for line, native in enumerate(reader, 2):
        if None in native or any(value is None for value in native.values()):
            raise ValueError(f"Malformed REPD CSV row {line}")
        row = {str(key).strip(): str(value).strip() for key, value in native.items()}
        if not row["Ref ID"].isdigit():
            raise ValueError(f"Invalid REPD Ref ID at row {line}")
        row["_csv_row"] = str(line)
        rows.append(row)
    if any(n > 1 for n in Counter(row["Ref ID"] for row in rows).values()):
        raise ValueError("Duplicate REPD Ref IDs; reconcile extract")
    return rows


def _normal_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def _number(value: str) -> float | None:
    if value in MISSING:
        return None
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError("Invalid REPD nonnegative number")
    return result


def _point(row: dict[str, str]) -> tuple[float, float] | None:
    x, y = _number(row["X-coordinate"]), _number(row["Y-coordinate"])
    return (x, y) if x is not None and y is not None else None


def _date(value: str, snapshot_date: str) -> str | None:
    if value in MISSING:
        return None
    parsed = datetime.strptime(value, "%d/%m/%Y").date()
    if parsed > date.fromisoformat(snapshot_date):
        raise ValueError("REPD date exceeds snapshot date")
    return parsed.isoformat()


def screen_repd_identities(
    rows: list[dict[str, str]], selected_ids: set[str]
) -> dict[str, list[dict[str, str]]]:
    """Flag name/application/link/nearby risks against the full solar extract.

    Grid distances are a conservative screening heuristic in native coordinates,
    not proof of a common project or a surveyed location. Missing coordinates,
    explicit phases/hybrids and sub-MW sites need separate review. Never fuzzy-merge.
    """
    solar = [row for row in rows if row["Technology Type"] == "Solar Photovoltaics"]
    lookup = {row["Ref ID"]: row for row in solar}
    if not selected_ids <= lookup.keys():
        raise ValueError("Selected REPD ID is missing or not explicitly photovoltaic")
    risks: dict[str, list[dict[str, str]]] = {}
    for ref in sorted(selected_ids, key=int):
        row = lookup[ref]
        flags = []
        if re.search(r"phase|extension|previous|formerly|battery", row["Site Name"], re.I):
            flags.append({"reason": "phase_alias_or_hybrid_name"})
        for field in ("Are they re-applying (New REPD Ref)", "Are they re-applying (Old REPD Ref)"):
            if row[field] not in MISSING:
                flags.append({"reason": "reapplication_link", "related_ref": row[field]})
        point = _point(row)
        if point is None:
            flags.append({"reason": "missing_grid_point_for_identity_screen"})
        capacity = _number(row["Installed Capacity (MWelec)"])
        if capacity is not None and capacity < 1:
            flags.append({"reason": "sub_mw_site_requires_privacy_review"})
        for other in solar:
            if other["Ref ID"] == ref:
                continue
            matches = []
            if _normal_name(row["Site Name"]) == _normal_name(other["Site Name"]):
                matches.append("same_normalized_name")
            if (
                row["Planning Application Reference"] not in MISSING
                and row["Planning Application Reference"] == other["Planning Application Reference"]
                and row["Planning Authority"] == other["Planning Authority"]
            ):
                matches.append("same_planning_application")
            other_point = _point(other)
            if point and other_point and math.dist(point, other_point) < 1000:
                matches.append("nearby_native_grid_point")
            if matches:
                flags.append({"reason": ";".join(matches), "related_ref": other["Ref ID"]})
        if flags:
            risks[ref] = flags
    return risks


def reviewed_repd_records(
    rows: list[dict[str, str]],
    *,
    reviewed_ids: set[str],
    source_id: str,
    retrieved_at: str,
    snapshot_date: str,
) -> list[dict[str, Any]]:
    """Map reviewed, unambiguous operating ground-mounted entries; no automatic ingest.

    A separate phase crosswalk is required before accepting any flagged identity.
    Applicant/operator is deliberately not promoted to owner/operator. Addresses,
    contact details and free-form applicant names are omitted for privacy. MWelec
    is retained as AC/DC-unspecified; operational date is a registry milestone.
    """
    risks = screen_repd_identities(rows, reviewed_ids)
    if risks:
        raise ValueError(f"Unresolved REPD identity review: {sorted(risks)}")
    result = []
    for row in rows:
        ref = row["Ref ID"]
        if ref not in reviewed_ids:
            continue
        if (
            row["Country"] not in {"England", "Wales", "Scotland", "Northern Ireland"}
            or row["Development Status (short)"] != "Operational"
            or row["Mounting Type for Solar"] != "Ground"
            or not row["Site Name"]
        ):
            raise ValueError(f"REPD identity outside reviewed scope: {ref}")
        native: dict[str, Any] = {
            key: row[key]
            for key in (
                "Old Ref ID",
                "Planning Authority",
                "Planning Application Reference",
                "X-coordinate",
                "Y-coordinate",
                "Country",
                "Development Status",
                "Storage Co-location REPD Ref ID",
                "Solar Site Area (sqm)",
            )
            if row.get(key, "") not in MISSING
        }
        native.update(
            csv_row=int(row["_csv_row"]),
            snapshot_date=snapshot_date,
            row_updated_date=_date(row["Record Last Updated (dd/mm/yyyy)"], retrieved_at[:10]),
            operational_milestone_date=_date(row["Operational"], snapshot_date),
            coordinate_note="Native grid coordinates only; datum/accuracy not asserted.",
            role_note="Operator (or Applicant) is ambiguous and intentionally not promoted.",
        )
        record: dict[str, Any] = {
            "record_id": stable_id("projects", "REPD", ref),
            "entity_type": "projects",
            "name": row["Site Name"],
            "country_code": "GBR",
            "region": row["Region"],
            "locality": row["County"],
            "technology": "photovoltaic",
            "status": "operational_registry_snapshot",
            "source_date": snapshot_date,
            "mounting_type": "ground",
            "capacity_basis": "REPD Installed Capacity (MWelec); AC/DC basis unspecified",
            "external_ids_json": canonical_json({"repd_ref_id": ref}),
            "extensions_json": canonical_json({"repd": native}),
            "sources": [source_id],
            "field_sources_json": canonical_json({"*": source_id}),
            "quality_status": "official_registry_reviewed",
            "created_at": retrieved_at,
            "updated_at": retrieved_at,
            "last_verified_at": retrieved_at,
            "notes": (
                "Historical registry status, not current physical inspection. "
                "No inferred owner, AC/DC split or surveyed coordinates."
            ),
        }
        capacity = _number(row["Installed Capacity (MWelec)"])
        area = _number(row["Solar Site Area (sqm)"])
        if capacity is not None:
            record["capacity_unspecified_mw"] = capacity
        if area is not None:
            record["land_area_ha"] = area / 10000
        result.append({key: value for key, value in record.items() if value != ""})
    return result
