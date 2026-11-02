"""Offline ODRE PV registry staging with a pinned, explicitly reviewed identity set.

An EIC identifies a network installation, not necessarily a whole project. This
adapter rejects aggregates and obvious phase/alias risks; it never fuzzy-merges.
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter
from datetime import date, datetime
from typing import Any

from .catalogue import canonical_json, stable_id
from .sam import verify_sha256

IDENTITY_FIELDS = {
    "codeeicresourceobject",
    "nominstallation",
    "codeinseecommuneimplantation",
    "codeinseecommune",
    "puismaxinstallee",
}
REQUIRED = IDENTITY_FIELDS | {
    "codetechnologie",
    "nbinstallations",
    "regime",
    "datemiseenservice",
    "gestionnaire",
    "region",
    "commune",
    "tensionraccordement",
    "postesource",
}


def normal_name(value: str) -> str:
    """Conservative exact normalized-name screen; never an identity merge key."""
    ascii_name = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", ascii_name.casefold())


def read_odre_json(
    content: bytes, *, sha256: str, identities_only: bool = False
) -> list[dict[str, Any]]:
    """Verify downloaded bytes, required columns and unique valid EIC identifiers."""
    verify_sha256(content, sha256)
    if len(content) > 100_000_000:
        raise ValueError("ODRE extract exceeds size limit")
    rows = json.loads(content, parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))
    required = IDENTITY_FIELDS if identities_only else REQUIRED
    if not isinstance(rows, list) or any(
        not isinstance(r, dict) or not required <= r.keys() for r in rows
    ):
        raise ValueError("ODRE schema changed; review adapter")
    seen = set()
    for index, row in enumerate(rows):
        if not identities_only:
            count = row["nbinstallations"]
            if isinstance(count, bool) or not isinstance(count, int) or count < 1:
                raise ValueError("Invalid ODRE installation count")
        eic = row["codeeicresourceobject"]
        if eic is None and not identities_only and (row.get("nbinstallations") or 0) > 1:
            row["_review_key"] = f"aggregate:json-array-index:{index}"
            _number(row["puismaxinstallee"])
            continue
        if not isinstance(eic, str) or not re.fullmatch(r"[A-Z0-9-]{16}", eic) or eic in seen:
            raise ValueError("Invalid or duplicate ODRE EIC")
        seen.add(eic)
        _number(row["puismaxinstallee"])
    return rows


def _number(value: Any) -> float | None:
    if value is None:
        return None
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < 0
    ):
        raise ValueError("Invalid ODRE nonnegative number")
    return float(value)


def _date(value: str | None, snapshot: str) -> str | None:
    if not value:
        return None
    parsed = datetime.strptime(value, "%d/%m/%Y").date()
    if parsed > date.fromisoformat(snapshot):
        raise ValueError("ODRE date exceeds snapshot")
    return parsed.isoformat()


def screen_odre_identities(
    rows: list[dict[str, Any]],
    identities: list[dict[str, Any]],
    *,
    existing: list[dict[str, Any]],
    minimum_kw: float = 10000,
    maximum_kw: float | None = None,
) -> dict[str, list[str]]:
    """Screen a bounded cohort against national names and >=1 MW communes.

    A shared commune is a review flag, not proof of duplication. Sub-MW entries
    participate in exact-name screening but not the conservative commune screen.
    Registry administrative codes are not promoted to surveyed plant coordinates.
    """
    if _number(minimum_kw) is None or minimum_kw < 1000:
        raise ValueError("ODRE minimum capacity must be at least 1000 kW")
    if maximum_kw is not None and (_number(maximum_kw) is None or maximum_kw <= minimum_kw):
        raise ValueError("ODRE upper capacity must exceed minimum")
    names = Counter(normal_name(r["nominstallation"] or "") for r in identities)
    communes = Counter(
        r["codeinseecommuneimplantation"]
        for r in identities
        if (_number(r["puismaxinstallee"]) or 0) >= 1000
    )
    by_eic = {r["codeeicresourceobject"]: r for r in identities}
    old_names = {
        normal_name(name)
        for r in existing
        if r.get("country_code") == "FRA"
        for name in [r["name"], *r.get("aliases", [])]
    }
    old_eics = {json.loads(r.get("external_ids_json", "{}")).get("odre_eic") for r in existing}
    risks = {}
    for row in rows:
        eic, name = row["codeeicresourceobject"], row["nominstallation"] or ""
        commune = row["codeinseecommuneimplantation"] or ""
        reasons = []
        if row["codetechnologie"] != "PHOTV":
            reasons.append("not_explicit_photovoltaic")
        if row["nbinstallations"] != 1:
            reasons.append("aggregate_not_single_project")
        elif eic not in by_eic or any(by_eic[eic][k] != row[k] for k in IDENTITY_FIELDS):
            reasons.append("identity_extract_mismatch")
        if not name or normal_name(name) in {"confidentiel", "prive"}:
            reasons.append("anonymous_or_missing_name")
        if not commune or commune.startswith(("97", "98")):
            reasons.append("missing_or_overseas_location_review")
        if communes[commune] > 1:
            reasons.append("shared_commune_requires_project_scope_review")
        if names[normal_name(name)] > 1:
            reasons.append("duplicate_normalized_name")
        if re.search(
            r"\b(?:ADP|PDL|TRANCHE|EXTENSION|PHASE)\b|\d\s*$|\b(?:II|III|IV)\b", name, re.I
        ):
            reasons.append("unit_phase_or_numbered_name")
        if "eolien" in normal_name(name):
            reasons.append("technology_name_conflict")
        capacity = _number(row["puismaxinstallee"]) or 0
        if (
            row["regime"] != "En service"
            or capacity < minimum_kw
            or (maximum_kw is not None and capacity >= maximum_kw)
        ):
            reasons.append("outside_operational_capacity_scope")
        if (
            normal_name(name) in old_names
            or eic in old_eics
            or commune == "33122"
            or "cestas" in normal_name(name)
        ):
            reasons.append("existing_project_requires_crosswalk")
        if reasons:
            risks[row.get("_review_key", eic)] = reasons
    return risks


def reviewed_odre_records(
    rows: list[dict[str, Any]],
    identities: list[dict[str, Any]],
    *,
    reviewed_ids: set[str],
    existing: list[dict[str, Any]],
    source_id: str,
    retrieved_at: str,
    snapshot_date: str,
    minimum_kw: float = 10000,
    maximum_kw: float | None = None,
) -> list[dict[str, Any]]:
    """Stage the reviewed cohort, preserving capacity basis and registry semantics."""
    risks = screen_odre_identities(
        rows, identities, existing=existing, minimum_kw=minimum_kw, maximum_kw=maximum_kw
    )
    lookup = {r.get("_review_key", r["codeeicresourceobject"]): r for r in rows}
    if not reviewed_ids <= lookup.keys() or reviewed_ids & risks.keys():
        raise ValueError("Missing or unresolved ODRE identity review")
    result = []
    for eic in sorted(reviewed_ids):
        row = lookup[eic]
        native = {
            k: row[k]
            for k in (
                "codeinseecommuneimplantation",
                "codeinseecommune",
                "commune",
                "region",
                "tensionraccordement",
                "moderaccordement",
                "puismaxrac",
                "nbgroupes",
                "energieannuelleglissanteinjectee",
                "energieannuelleglissanteproduite",
            )
            if row.get(k) is not None
        }
        native.update(
            locator=f"codeeicresourceobject={eic}; native field names in this object",
            snapshot_date=snapshot_date,
            connection_date=_date(row.get("dateraccordement"), snapshot_date),
            location_note=(
                "Delivery/substation administrative geography, not surveyed plant position; "
                "glossary and schema disagree on implantation code semantics."
            ),
            capacity_note=(
                "puismaxinstallee is maximum active installed kW; AC/DC basis unspecified. "
                "puismaxrac is maximum injection kW, not plant AC capacity."
            ),
            energy_note=(
                "Rolling 12-month measured kWh, not expected generation; period end is "
                "installation-specific. Produced-energy inclusion of self-consumption conflicts "
                "between schema and glossary."
            ),
            group_note=(
                "nbgroupes may mean inverters or converter stations; no equipment count inferred."
            ),
        )
        record = {
            "record_id": stable_id("projects", "ODRE", eic),
            "entity_type": "projects",
            "name": row["nominstallation"],
            "country_code": "FRA",
            "technology": "photovoltaic",
            "status": "operational_registry_snapshot",
            "source_date": snapshot_date,
            "capacity_unspecified_mw": float(row["puismaxinstallee"]) / 1000,
            "capacity_basis": (
                "ODRE puismaxinstallee, maximum active installed kW; AC/DC unspecified"
            ),
            "commissioning_date": _date(row["datemiseenservice"], snapshot_date),
            "grid_operator": row["gestionnaire"],
            "substation": row["postesource"],
            "external_ids_json": canonical_json({"odre_eic": eic}),
            "extensions_json": canonical_json({"odre": native}),
            "sources": [source_id],
            "field_sources_json": canonical_json({"*": source_id}),
            "quality_status": "official_registry_reviewed",
            "created_at": retrieved_at,
            "updated_at": retrieved_at,
            "last_verified_at": retrieved_at,
            "notes": (
                "Network-operator registry observation as of source_date; no present-operation, "
                "owner, AC/DC split or precise location inferred. Commissioning is the registry "
                "industrial-service date."
            ),
        }
        voltage = re.fullmatch(r"(\d+(?:[.,]\d+)?) kV", row["tensionraccordement"] or "")
        if voltage:
            record["grid_voltage_kv"] = float(voltage[1].replace(",", "."))
        result.append({k: v for k, v in record.items() if v is not None and v != ""})
    return result
