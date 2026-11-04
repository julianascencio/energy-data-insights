"""Offline French wind registry staging with conservative installation scope.

EICs identify network installations, not automatically whole farms. The complete
national wind extract is required for name/commune screening. Current operating
status is never extrapolated beyond the dated registry snapshot.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from typing import Any

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json
from energy_data_retrieval.pv_catalogue.odre import normal_name, read_odre_json

from .catalogue import stable_id
from .gppd import evidence_record

REFERENCE_IDS = ("odre_wind_20260831", "odre_glossary_20261102")


def read_inventory(content: bytes, *, sha256: str, expected_count: int) -> list[dict[str, Any]]:
    """Verify original bytes, national count, schema and unique EIC identities."""
    rows = read_odre_json(content, sha256=sha256)
    if len(rows) != expected_count or any(r.get("codefiliere") != "EOLIE" for r in rows):
        raise ValueError("Require complete national EOLIE extract")
    return rows


def _date(value: str | None, snapshot: str) -> str | None:
    if not value:
        return None
    result = datetime.strptime(value, "%d/%m/%Y").date().isoformat()
    if result > snapshot:
        raise ValueError("Source date exceeds registry snapshot")
    return result


def stage_inventory(
    rows: list[dict[str, Any]],
    existing: list[dict[str, Any]],
    *,
    source_id: str,
    now: str,
    snapshot: str = "2026-08-31",
    service_start: str = "2022-01-01",
    service_end: str | None = None,
    residual: bool = False,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Screen national identities and stage a bounded industrial-service cohort.

    This bounded cohort avoids automatically treating historical WRI municipality
    aggregates as modern EICs. Shared communes, repeated names, phase markers and
    prior name/commune candidates are held. No fuzzy merge, turbine count from
    nbGroupes, surveyed coordinates from administrative codes, or capacity factor.
    All accepted capacities remain excluded until farm/phase scope is reconciled.
    The residual partition selects missing service dates or missing/sub-1-MW
    installed ratings; missing/nonpositive ratings remain held. Other cohorts
    still participate in the national identity screen.
    Bounds are inclusive ISO dates; the default preserves the original 2022+
    cohort. Filtering never removes other years from the national identity screen.
    """
    start = datetime.strptime(service_start, "%Y-%m-%d").date().isoformat()
    end = datetime.strptime(service_end or snapshot, "%Y-%m-%d").date().isoformat()
    if start > end or end > snapshot:
        raise ValueError("Service cohort must be ordered and within the snapshot")
    names = Counter(normal_name(r["nominstallation"] or "") for r in rows)
    communes = Counter(r["codeinseecommuneimplantation"] for r in rows)
    old = [r for r in existing if r["entity_type"] == "projects" and r.get("country_code") == "FRA"]
    old_names = {
        normal_name(n): r["record_id"] for r in old for n in [r["name"], *r.get("aliases", [])]
    }
    old_eics = {json.loads(r.get("external_ids_json") or "{}").get("odre_eic") for r in old}
    accepted, ledger = [], []
    for raw in sorted(rows, key=lambda r: r.get("codeeicresourceobject") or ""):
        eic = raw["codeeicresourceobject"]
        name = raw["nominstallation"] or ""
        normalized = normal_name(name)
        commune = raw["codeinseecommuneimplantation"]
        service = _date(raw["datemiseenservice"], snapshot)
        installed = raw["puismaxinstallee"]
        reasons = []
        if residual:
            if service and installed is not None and installed >= 1000:
                reasons.append("outside_residual_partition")
            if installed is None or installed <= 0:
                reasons.append("missing_or_nonpositive_installed_capacity")
        elif not service or not start <= service <= end or installed is None or installed < 1000:
            reasons.append(
                "outside_2022_plus_ge1MW_service_cohort"
                if service_start == "2022-01-01" and service_end is None
                else "outside_selected_ge1MW_service_cohort"
            )
        if raw["codetechnologie"] != "TERRE":
            reasons.append("not_explicit_onshore")
        if raw["nbinstallations"] != 1:
            reasons.append("aggregate_not_individual_installation")
        if raw["regime"] != "En service" or raw.get("datederaccordement"):
            reasons.append("service_or_disconnection_requires_review")
        if not normalized or normalized in {"confidentiel", "prive"}:
            reasons.append("anonymous_or_missing_name")
        if normalized in {"hangar", "eolienne", "eoliennes", "parc eolien"}:
            reasons.append("generic_name_requires_identity_review")
        if not commune or commune.startswith(("97", "98")):
            reasons.append("missing_or_overseas_location")
        if communes[commune] > 1:
            reasons.append("shared_commune_scope")
        if names[normalized] > 1:
            reasons.append("repeated_name")
        if re.search(
            r"\b(?:ADP|PDL|TRANCHE|EXTENSION|PHASE|II|III|IV|V|VI|IX)\b|\d\s*$", name, re.I
        ):
            reasons.append("unit_phase_or_numbered_name")
        candidates = sorted(
            {
                rid
                for n, rid in old_names.items()
                if n == normalized
                or n == normal_name(raw["commune"] or "")
                or (len(n) >= 6 and n in normalized)
            }
        )
        if candidates or eic in old_eics:
            reasons.append("existing_identity_candidate")
        decision = {
            "registry_id": eic,
            "name": name,
            "commune": raw["commune"],
            "service_date": service,
            "candidate_record_ids": candidates,
            "decision": "deferred" if reasons else "added",
            "reasons": reasons,
        }
        if reasons:
            ledger.append(decision)
            continue
        values = {
            "record_id": stable_id("projects", "ODRE-EIC", eic),
            "entity_type": "projects",
            "record_scope": "farm",
            "name": name,
            "country_code": "FRA",
            "region": raw["region"],
            "locality": raw["commune"],
            "technology": "onshore",
            "status": "operational",
            "status_as_of": snapshot,
            "status_date_basis": (
                "ODRE En service at registry snapshot; not retrieval-day confirmation"
            ),
            "aggregation_role": "unresolved",
            "quality_status": "needs_review",
            "capacity_scope": (
                "Single EIC network installation; whole-farm/phase/repowering scope unverified"
            ),
            "external_ids_json": canonical_json({"odre_eic": eic}),
            "installed_capacity_mw": installed / 1000,
            "export_capacity_mw": raw["puismaxrac"] / 1000
            if raw.get("puismaxrac") is not None
            else None,
            "grid_utility": raw["gestionnaire"],
            "substation": raw["postesource"],
            "commissioning_date": service,
            "location_accuracy": (
                "Administrative delivery/installation commune; no surveyed coordinates"
            ),
            "extensions_json": canonical_json(
                {
                    "odre": {
                        "source_fields": raw,
                        "snapshot_date": snapshot,
                        "connection_date": _date(raw.get("dateraccordement"), snapshot),
                        "source_version_date": _date(raw.get("datedebutversion"), snapshot),
                        "commissioning_basis": (
                            "Industrial service as viewed by network manager; not whole-farm COD"
                        ),
                        "generation_basis": (
                            "Native rolling 12-month kWh; exact per-row period endpoints "
                            "unspecified; production excludes self-consumption, injection is "
                            "network boundary. No CF calculated."
                        ),
                        "group_count_basis": (
                            "nbGroupes is installed generating groups; "
                            "not promoted to turbine count"
                        ),
                        "voltage_basis": "HTA/HTB are categories; no numeric voltage inferred",
                    }
                }
            ),
            "notes": (
                "Dated registry observation, not independently verified performance. EIC scope "
                "reconciliation required before capacity aggregation; no owner/model inferred "
                "from installation name."
            ),
        }
        record = evidence_record(
            values,
            source_id=source_id,
            now=now,
            locator=f"codeeicresourceobject={eic}; national EOLIE JSON export",
            confidence="medium",
        )
        evidence = json.loads(record["evidence_json"])
        for target, field in [
            ("installed_capacity_mw", "puismaxinstallee"),
            ("export_capacity_mw", "puismaxrac"),
        ]:
            if target in evidence:
                evidence[target].update(
                    original_value=raw[field],
                    original_unit="kW",
                    normalization="original kW / 1000 = MW",
                )
        record["evidence_json"] = canonical_json(evidence)
        accepted.append(record)
        ledger.append({**decision, "record_id": record["record_id"]})
    return accepted, ledger
