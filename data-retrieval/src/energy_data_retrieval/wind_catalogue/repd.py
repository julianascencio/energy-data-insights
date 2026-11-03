"""Offline REPD reconciliation through WRI's explicit historical registry crosswalk.

Planning applications are not automatically new farms. This adapter enriches only
existing, singly linked historical identities with matching names; every other
selected candidate is retained in a decision ledger. Scope remains unresolved.
"""

from __future__ import annotations

import csv
import io
import json
import math
import re
from collections import Counter
from datetime import date, datetime
from typing import Any

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json

from .gppd import evidence_record

STATUS = {
    "Operational": "operational",
    "Under Construction": "under_construction",
    "Planning Permission Granted": "permitted",
    "Appeal Granted": "permitted",
    "Secretary of State - Granted": "permitted",
    "Planning Application Submitted": "announced",
    "Abandoned": "cancelled",
    "Decommissioned": "decommissioned",
}
REQUIRED = {
    "Ref ID",
    "Site Name",
    "Technology Type",
    "Development Status",
    "Installed Capacity (MWelec)",
    "Country",
    "No. of Turbines",
}


def _number(value: str) -> float | None:
    if not value.strip():
        return None
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError("Invalid nonnegative REPD quantity")
    return number


def _name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def reconcile_repd(
    text: str,
    crosswalk: str,
    existing: list[dict[str, Any]],
    *,
    source_id: str,
    crosswalk_source_id: str,
    now: str,
    as_of: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return reviewed enrichments and decisions for all Wind CSV rows.

    ``text`` is decoded by the caller (Q2 2026 uses Windows-1252). ``crosswalk``
    is WRI resources/GBR/matches_GBR.csv from a pinned commit. No ID-prefix
    inference, fuzzy merge, coordinate conversion, model inference, capacity
    substitution or aggregation approval occurs here. Dates are UTC ISO strings.
    """
    if date.fromisoformat(as_of) > date.fromisoformat(now[:10]):
        raise ValueError("Future REPD snapshot")
    reader = csv.DictReader(io.StringIO(text))
    if not set(reader.fieldnames or []) >= REQUIRED:
        raise ValueError("Missing REPD headers")
    raw_rows = [
        (line, dict(r))
        for line, r in enumerate(reader, 2)
        if r["Technology Type"] in {"Wind Onshore", "Wind Offshore"}
    ]
    ids = [r["Ref ID"] for _, r in raw_rows]
    if any(not x or not x.isdigit() for x in ids) or len(ids) != len(set(ids)):
        raise ValueError("Missing/duplicate/invalid REPD ID")
    cr = csv.DictReader(io.StringIO(crosswalk))
    if not {"gppd_id", "repd_id", "repd_id2", "repd_name", "fuel"} <= set(cr.fieldnames or []):
        raise ValueError("Missing WRI crosswalk headers")
    links: dict[str, list[dict[str, str]]] = {}
    for entry in cr:
        if entry["fuel"] == "Wind" and entry["repd_id"]:
            links.setdefault(entry["repd_id"], []).append(entry)
    baseline = {
        json.loads(r.get("external_ids_json") or "{}").get("wri_gppd"): r
        for r in existing
        if r.get("country_code") == "GBR"
    }
    names = Counter(_name(r["Site Name"]) for _, r in raw_rows)
    incoming, decisions = [], []
    for line, raw in raw_rows:
        ref = raw["Ref ID"]
        locator = f"CSV record {line}; Ref ID={ref}; Q2 2026"
        decision: dict[str, Any] = {
            "repd_id": ref,
            "name": raw["Site Name"],
            "locator": locator,
            "source_id": source_id,
            "decision": "deferred_identity",
        }
        candidates = links.get(ref, [])
        reason = None
        if len(candidates) != 1:
            reason = (
                "No unique explicit WRI crosswalk; review as a separate application/phase candidate"
            )
        else:
            link = candidates[0]
            old = baseline.get(link["gppd_id"])
            if old is None:
                reason = "Crosswalk identity absent from baseline"
            elif link["repd_id2"]:
                reason = "Crosswalk has a second REPD application; scope review required"
            elif _name(raw["Site Name"]) != _name(link["repd_name"]):
                reason = "Registry name differs from explicit historical crosswalk"
            elif names[_name(raw["Site Name"])] != 1:
                reason = "Repeated registry name; application/phase identity review required"
            elif old.get("status") != "unknown":
                reason = (
                    "Already has primary lifecycle evidence; reconcile dated observations manually"
                )
            elif (
                raw.get("Are they re-applying (New REPD Ref)", "").strip()
                or raw.get("Are they re-applying (Old REPD Ref) ", "").strip()
                or raw["Development Status"] == "Revised"
            ):
                reason = (
                    "Revised/replacement planning application; not a new generation by inference"
                )
        if reason:
            decision["reason"] = reason
            decisions.append(decision)
            continue
        assert old is not None
        try:
            capacity = _number(raw["Installed Capacity (MWelec)"])
            count = _number(raw["No. of Turbines"])
            unit = _number(raw.get("Turbine Capacity (MW)", ""))
            if count is not None and not count.is_integer():
                raise ValueError("Nonintegral turbine count")
            status = STATUS.get(raw["Development Status"], "unknown")
            milestones = []
            for column in (
                "Planning Application Submitted",
                "Planning Permission  Granted",
                "Under Construction",
                "Operational",
                "Planning Permission Expired",
            ):
                if raw.get(column):
                    value = datetime.strptime(raw[column], "%d/%m/%Y").date().isoformat()
                    milestones.append(
                        {
                            "event": column.strip(),
                            "date": value,
                            "basis": "REPD application milestone; future dates are not achieved",
                            "source_id": source_id,
                            "locator": locator,
                        }
                    )
            observation = {
                "field": "registry_application_capacity",
                "value": capacity,
                "unit": "MW",
                "kind": "reported",
                "period": as_of,
                "boundary": (
                    "REPD application; source column does not itself establish commissioned MW"
                ),
                "source_id": source_id,
                "locator": locator + "; Installed Capacity (MWelec)",
            }
            observations = json.loads(old.get("observations_json") or "[]")
            if capacity is not None:
                observations.append(observation)
            if unit is not None:
                observations.append(
                    {
                        **observation,
                        "field": "registry_unit_rating",
                        "value": unit,
                        "boundary": (
                            "Registry unit rating; exact model and mixed-fleet composition unknown"
                        ),
                        "locator": locator + "; Turbine Capacity (MW)",
                    }
                )
            extension = json.loads(old.get("extensions_json") or "{}")
            extension["repd"] = {
                "record_updated_original": raw.get("Record Last Updated (dd/mm/yyyy)"),
                "development_status_original": raw["Development Status"],
                "operator_or_applicant": raw.get("Operator (or Applicant)") or None,
                "address": raw.get("Address") or None,
                "county": raw.get("County") or None,
                "country_within_uk": raw["Country"],
                "x_coordinate_original": raw.get("X-coordinate") or None,
                "y_coordinate_original": raw.get("Y-coordinate") or None,
                "coordinate_note": (
                    "Original grid values retained; CRS not reconciled; no lat/lon conversion"
                ),
                "height_of_turbines_m_original": raw.get("Height of Turbines (m)") or None,
                "height_note": "Hub/tip definition not established; neither scalar populated",
            }
            values = {
                "record_id": old["record_id"],
                "external_ids_json": canonical_json(
                    {**json.loads(old["external_ids_json"]), "uk_repd": ref}
                ),
                "status": status,
                "status_as_of": as_of,
                "status_date_basis": (
                    "REPD Q2 2026 snapshot published 2026-08-03; not retrieval-date operation"
                ),
                "technology": "onshore"
                if raw["Technology Type"] == "Wind Onshore"
                else "offshore_unspecified",
                "turbine_count": int(count) if count is not None else None,
                "region": raw.get("Region") or raw["Country"],
                "milestones_json": canonical_json(milestones),
                "observations_json": canonical_json(observations),
                "extensions_json": canonical_json(extension),
                "permits_json": canonical_json(
                    {
                        k: raw.get(k) or None
                        for k in (
                            "Planning Authority",
                            "Planning Application Reference",
                            "Appeal Reference",
                            "Secretary of State Reference",
                        )
                    }
                ),
                "offtake_json": canonical_json(
                    {
                        k: raw.get(k) or None
                        for k in (
                            "CfD Allocation Round",
                            "CfD Capacity (MW)",
                            "RO Banding (ROC/MWh)",
                            "FiT Tariff (p/kWh)",
                        )
                    }
                ),
            }
            if status == "operational":
                values["installed_capacity_mw"] = capacity
            elif status in {"announced", "permitted", "under_construction"}:
                values["planned_capacity_mw"] = capacity
            update = evidence_record(values, source_id=source_id, now=now, locator=locator)
            merged = dict(old)
            for key, value in values.items():
                if value is not None:
                    merged[key] = value
            merged.update(
                updated_at=now,
                last_verified_at=now,
                sources=sorted(set(old["sources"]) | {source_id, crosswalk_source_id}),
            )
            for key in ("field_sources_json", "evidence_json"):
                evidence: dict[str, Any] = {**json.loads(old[key]), **json.loads(update[key])}
                if key == "field_sources_json":
                    evidence["external_ids_json"] = sorted(
                        set(old["sources"]) | {source_id, crosswalk_source_id}
                    )
                    for compound in ("observations_json", "extensions_json"):
                        evidence[compound] = sorted(set(old["sources"]) | {source_id})
                else:
                    evidence["external_ids_json"]["locator"] += (
                        f"; WRI crosswalk gppd_id={link['gppd_id']}"
                    )
                    for detail in json.loads(update[key]):
                        evidence[detail]["source_revision"] = "Q2 2026"
                        evidence[detail]["source_publication_date"] = "2026-08-03"
                        if detail.endswith("_json"):
                            evidence[detail].pop("original_value", None)
                merged[key] = canonical_json(evidence)
            if old.get("source_urls") is not None:
                merged.pop("source_urls")  # Optional; source IDs remain authoritative.
            incoming.append(merged)
            decision.update(
                decision="enriched",
                record_id=old["record_id"],
                wri_gppd=link["gppd_id"],
                aggregation_role=old["aggregation_role"],
                deferred_fields=[
                    "phase_scope",
                    "repowering",
                    "exact_fleet",
                    "coordinate_crs",
                    "turbine_height_basis",
                ],
            )
        except ValueError as exc:
            decision.update(decision="deferred_invalid_value", reason=str(exc))
        decisions.append(decision)
    return incoming, decisions
