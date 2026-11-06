"""Stage checksum-pinned, reviewed operator tables with dated scope boundaries."""

from __future__ import annotations

import copy
import hashlib
import json
import math
from datetime import date
from typing import Any

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json

from .catalogue import stable_id
from .gppd import evidence_record


def stage_operator_portfolio(
    document: dict[str, Any], original: bytes, existing: list[dict[str, Any]], *, now: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Review every selected project; never derive installed MW or exact models.

    Explicit crosswalks enrich existing records with immutable observations only.
    Existing scalar facts, creation timestamps and aggregation roles are preserved.
    New farms remain aggregation-excluded pending registry/phase reconciliation.
    A reported fleet-average rating cannot become an exact turbine specification.
    """
    if hashlib.sha256(original).hexdigest() != document["sha256"]:
        raise ValueError("Operator original checksum mismatch")
    if date.fromisoformat(document["as_of"]) > date.fromisoformat(document["published_at"]):
        raise ValueError("Observation follows publication")
    entries = document["entries"]
    names = [e["source_name"] for e in entries]
    expected = document["expected_names"]
    if not names or len(set(names)) != len(names) or sorted(names) != sorted(expected):
        raise ValueError("Incomplete or duplicate operator partition")
    prior = {r["record_id"]: r for r in existing}
    if len(prior) != len(existing):
        raise ValueError("Duplicate existing identity")
    records, ledger, target_ids = [], [], set()
    for entry in entries:
        name, locator = entry["source_name"], entry["locator"]
        if not locator:
            raise ValueError("Page/table locator required")
        if entry.get("hold_reason"):
            ledger.append(
                dict(source_name=name, decision="deferred_identity", reason=entry["hold_reason"])
            )
            continue
        facts = copy.deepcopy(entry["facts"])
        count, rating = facts["turbine_count"], facts["turbine_rating_mw"]
        if (
            type(count) is not int
            or count <= 0
            or not isinstance(rating, (int, float))
            or not math.isfinite(rating)
            or rating <= 0
        ):
            raise ValueError("Positive reported turbine count and rating required")
        if facts["rating_basis"] not in {"reported_per_turbine", "reported_fleet_average"}:
            raise ValueError("Explicit turbine rating basis required")
        if facts["capacity_basis"] not in {"contracted", "gross_reported"}:
            raise ValueError("Keep contracted and gross capacity distinct")
        facts["count_times_rating_check"] = {
            "value": round(count * rating, 6),
            "unit": "MW",
            "kind": "arithmetic_check_only",
            "supplies_installed_capacity": False,
        }
        facts["exact_model_inventory"] = "unknown; OEM and rating do not identify a model"
        observation = dict(
            source_id=document["source_id"],
            published_at=document["published_at"],
            as_of=document["as_of"],
            source_name=name,
            locator=locator,
            facts=facts,
            confidence="high",
            normalization="Original MW, percent and date precision retained",
            boundary=(
                "Dated operator disclosure; not a current operating census "
                "or performance validation"
            ),
        )
        rid = entry.get("record_id")
        if rid:
            row = copy.deepcopy(prior[rid])
            if (row["entity_type"], row["name"], row["country_code"]) != (
                "projects",
                entry["expected_name"],
                entry["country_code"],
            ) or not entry.get("identity_basis"):
                raise ValueError("Explicit project crosswalk mismatch")
            decision = "enrichment"
        else:
            if not entry.get("identity_basis"):
                raise ValueError("Reviewed new project identity required")
            rid = stable_id("projects", document["operator"], name)
            if rid in prior or any(
                r["entity_type"] == "projects"
                and r["name"] == name
                and r.get("country_code") == entry["country_code"]
                for r in existing
            ):
                raise ValueError("Existing project needs an explicit crosswalk")
            row = evidence_record(
                dict(
                    record_id=rid,
                    entity_type="projects",
                    record_scope="farm",
                    name=name,
                    country_code=entry["country_code"],
                    technology=entry["technology"],
                    status="operational",
                    status_as_of=document["as_of"],
                    status_date_basis="Operator disclosure at stated historical date only",
                    aggregation_role="unresolved",
                    turbine_count=count,
                    fleet_completeness="partial",
                    capacity_scope=(
                        "Operator table boundary; contracted/gross MW retained in "
                        "dated observations; registry/phase scope unresolved"
                    ),
                    official_url=document["url"],
                ),
                source_id=document["source_id"],
                now=now,
                locator=locator,
            )
            evidence = json.loads(row["evidence_json"])
            for value in evidence.values():
                value.update(publication_date=document["published_at"], as_of=document["as_of"])
            row["evidence_json"] = canonical_json(evidence)
            decision = "addition"
        if rid in target_ids:
            raise ValueError("Multiple source rows mapped to one project")
        target_ids.add(rid)
        ext = json.loads(row.get("extensions_json") or "{}")
        history = ext.setdefault("operator_portfolio_observations", [])
        previous = [o for o in history if o["source_id"] == document["source_id"]]
        if previous:
            if previous != [observation]:
                raise ValueError("Immutable operator observation changed")
        else:
            history.append(observation)
            fs, ev = json.loads(row["field_sources_json"]), json.loads(row["evidence_json"])
            fs["extensions_json"] = sorted(
                set([*fs.get("extensions_json", []), document["source_id"]])
            )
            ev["extensions_json"] = dict(
                prior_observation=ev.get("extensions_json"),
                source_id=document["source_id"],
                locator=locator,
                confidence="high",
                publication_date=document["published_at"],
                normalization="Dated observation; no scalar capacity or status substitution",
            )
            row.update(
                extensions_json=canonical_json(ext),
                field_sources_json=canonical_json(fs),
                evidence_json=canonical_json(ev),
                sources=sorted(set(row["sources"] + [document["source_id"]])),
                updated_at=now,
                last_verified_at=now,
            )
        records.append(row)
        ledger.append(
            dict(
                source_name=name,
                record_id=rid,
                decision=decision,
                identity_basis=entry["identity_basis"],
            )
        )
    return sorted(records, key=lambda r: r["record_id"]), ledger
