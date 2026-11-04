"""Offline NEM wind survey staging; registry sites are not reconciled farm totals."""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json

from .catalogue import stable_id
from .gppd import evidence_record

REFERENCE_IDS = ("aemo_nem_oct2026_bess",)
REGIONS = {
    "NSW1": "New South Wales / ACT NEM region",
    "QLD1": "Queensland",
    "SA1": "South Australia",
    "TAS1": "Tasmania",
    "VIC1": "Victoria",
}
FUTURE = {"Publicly Announced", "Anticipated", "Committed", "Committed*"}
REQUIRED = {
    "AEMO Survey ID",
    "Site Name",
    "Site Owner",
    "Region",
    "Gen Info Unit ID",
    "Technology Type",
    "Technology Detail",
    "Commitment Status",
    "Agg Nameplate Capacity (MW AC)",
    "Unit Count",
}


def read_wind_units(path: Path) -> list[dict[str, Any]]:
    """Read all wind rows, retaining original Excel row locators and native dates.

    Only the first 26 identity/technical columns are selected; seasonal dispatch
    forecasts are deliberately outside this adapter's boundary.
    """
    import openpyxl

    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        rows = workbook["Generator Information"].iter_rows(values_only=True)
        for _ in range(3):
            next(rows)
        headers = list(next(rows))[:26]
        if not set(headers) >= REQUIRED:
            raise ValueError("AEMO workbook headers changed")
        result = []
        for number, values in enumerate(rows, 5):
            row = {
                k: v.isoformat() if hasattr(v, "isoformat") else v
                for k, v in zip(headers, values, strict=False)
            }
            if row["Technology Type"] == "Wind":
                result.append({**row, "source_row": number})
        return result
    finally:
        workbook.close()


def _id(value: Any) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value <= 0
        or int(value) != value
    ):
        raise ValueError("Invalid AEMO numeric registry ID")
    return int(value)


def _sum(rows: list[dict[str, Any]], field: str) -> float | None:
    values = [r.get(field) for r in rows]
    for value in values:
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, (float, int))
            or not math.isfinite(value)
            or value < 0
        ):
            raise ValueError(f"Invalid AEMO {field}")
    return (
        None
        if not values or None in values
        else sum(v for v in values if isinstance(v, (int, float)))
    )


def stage_wind_sites(
    units: list[dict[str, Any]],
    *,
    source_id: str,
    now: str,
    published_date: str,
    minimum_id: int = 0,
    maximum_id: int = 2000,
) -> list[dict[str, Any]]:
    """Stage the complete half-open survey-ID partition for human identity review.

    No commissioning capacity is promoted to installed MW; mixed lifecycle
    totals stay nested by status. Shared site dispatch limits never become wind
    nameplates. No model, coordinates, individual turbine or COD is inferred.
    """
    if minimum_id < 0 or maximum_id <= minimum_id:
        raise ValueError("Invalid half-open survey partition")
    groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    seen: set[int] = set()
    for unit in units:
        if not set(unit) >= REQUIRED:
            raise ValueError("Missing AEMO fields")
        if unit["Technology Type"] != "Wind":
            continue
        ident, site = _id(unit["Gen Info Unit ID"]), _id(unit["AEMO Survey ID"])
        if ident in seen:
            raise ValueError("Duplicate AEMO generating unit")
        seen.add(ident)
        if minimum_id <= site < maximum_id:
            groups[site].append(unit)
    output = []
    for site, rows in sorted(groups.items()):
        rows = sorted(rows, key=lambda r: r["Gen Info Unit ID"])
        first = rows[0]
        for key in ["Site Name", "Site Owner", "Region", "Technology Detail"]:
            if len({r[key] for r in rows}) != 1:
                raise ValueError(f"Inconsistent site {site}: {key}")
        if (
            not first["Site Name"]
            or first["Region"] not in REGIONS
            or first["Technology Detail"] not in {"Onshore", "Offshore - fixed"}
        ):
            raise ValueError("Unknown AEMO name/region/technology")
        for row in rows:
            count = _sum([row], "Unit Count")
            if count is not None and int(count) != count:
                raise ValueError("Fractional turbine count")
            _sum([row], "Unit Capacity (MW AC)")
        states = {r["Commitment Status"] for r in rows}
        if not states <= FUTURE | {"In Service", "In Commissioning"}:
            raise ValueError("Unreviewed commitment status")
        status = "announced"
        if "In Service" in states:
            status = "operational" if states == {"In Service"} else "partially_operational"
        elif "In Commissioning" in states:
            status = "commissioning"
        by_status = {}
        for state in sorted(states):
            selected = [r for r in rows if r["Commitment Status"] == state]
            count = _sum(selected, "Unit Count")
            if count is not None and int(count) != count:
                raise ValueError("Fractional turbine count")
            by_status[state] = {
                "nameplate_mw_ac": _sum(selected, "Agg Nameplate Capacity (MW AC)"),
                "turbine_count": count,
            }
        row_numbers = ",".join(str(r.get("source_row", "?")) for r in rows)
        locator = (
            f"Generator Information rows {row_numbers}; survey ID {site}; "
            "Background Information definitions"
        )
        total_count = _sum(rows, "Unit Count")
        values = {
            "record_id": stable_id("projects", "AEMO survey site", str(site)),
            "entity_type": "projects",
            "record_scope": "farm",
            "name": first["Site Name"],
            "country_code": "AUS",
            "region": REGIONS[first["Region"]],
            "owner_names": [first["Site Owner"]] if first["Site Owner"] else None,
            "technology": "onshore"
            if first["Technology Detail"] == "Onshore"
            else "fixed_bottom_offshore",
            "aggregation_role": "unresolved",
            "status": status,
            "status_as_of": published_date,
            "status_date_basis": (
                "AEMO publication snapshot; participant survey update dates retained separately"
            ),
            "capacity_scope": (
                "Wind-only generating units within AEMO survey site; farm/phase/repowering "
                "scope requires reconciliation before aggregation"
            ),
            "external_ids_json": canonical_json({"aemo_survey_id": str(site)}),
            "installed_capacity_mw": by_status["In Service"]["nameplate_mw_ac"]
            if states == {"In Service"}
            else None,
            "planned_capacity_mw": _sum(rows, "Agg Nameplate Capacity (MW AC)")
            if states <= FUTURE
            else None,
            "turbine_count": int(total_count)
            if len(states) == 1 and total_count is not None
            else None,
            "extensions_json": canonical_json(
                {
                    "capacity_by_aemo_status": by_status,
                    "unit_inventory": rows,
                    "inventory_completeness": (
                        "Complete wind rows within selected survey ID; OEM models unknown; "
                        "individual turbines not inventoried"
                    ),
                    "capacity_basis": (
                        "Reported generating-unit aggregate AC nameplates; "
                        "no multiplication by unit count"
                    ),
                    "site_limit_boundary": (
                        "Max Site Capacity includes other technologies and constraints; not "
                        "wind-only export capacity"
                    ),
                    "date_boundary": "FCUD is source indication/forecast; no project COD inferred",
                    "arithmetic_checks": [
                        {
                            "unit_id": r["Gen Info Unit ID"],
                            "calculated_mw": r["Unit Count"] * r["Unit Capacity (MW AC)"],
                            "reported_mw": r["Agg Nameplate Capacity (MW AC)"],
                        }
                        for r in rows
                        if r.get("Unit Count") is not None
                        and r.get("Unit Capacity (MW AC)") is not None
                    ],
                }
            ),
            "notes": (
                "AEMO participant-reported NEM survey, not independent operational "
                "verification or all Australia. Committed and Anticipated remain announced "
                "in the common lifecycle; original distinctions retained. No unknown treated "
                "as zero."
            ),
        }
        record = evidence_record(values, source_id=source_id, now=now, locator=locator)
        evidence = json.loads(record["evidence_json"])
        for field, source_column in (
            ("installed_capacity_mw", "Agg Nameplate Capacity (MW AC)"),
            ("planned_capacity_mw", "Agg Nameplate Capacity (MW AC)"),
            ("turbine_count", "Unit Count"),
        ):
            if field in evidence:
                evidence[field]["original_value"] = [
                    {"unit_id": r["Gen Info Unit ID"], "value": r[source_column]} for r in rows
                ]
                evidence[field]["normalization"] = (
                    "Sum complete reported unit values within stated lifecycle boundary; "
                    "no count-times-rating replacement and no shared site limit substitution"
                )
        record["evidence_json"] = canonical_json(evidence)
        output.append(record)
    return output
