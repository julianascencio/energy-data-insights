"""Reviewed new identities from ERA's historical construction/licensed table."""

import json
import math
from typing import Any

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json

from .catalogue import stable_id
from .gppd import evidence_record

SOURCE_ID = "uganda-era-environment-2023"


def new_record(entry: dict[str, Any], *, now: str) -> dict[str, Any]:
    """Retain planned generating MW as a dated observation, never installed power."""
    review, item = entry["review"], entry["inventory"]
    if (
        review.get("decision") != "reviewed_new_identity"
        or not review.get("name")
        or not review.get("accession")
        or not review.get("identity_basis")
        or not review.get("locator")
        or item.get("lifecycle_group") != "construction_or_licensed"
        or item.get("commissioning") is not None
    ):
        raise ValueError("Explicit construction/licensed identity review required")
    mw = item["capacity_mw"]
    if isinstance(mw, bool) or not isinstance(mw, (float, int)) or not math.isfinite(mw) or mw < 0:
        raise ValueError("Invalid project capacity")
    obs = dict(
        field="planned_capacity_mw",
        value=mw,
        unit="MW",
        kind="reported",
        period="2023",
        boundary="Named project in joint construction/licensed table; stage not disaggregated",
        source_id=SOURCE_ID,
        locator=review["locator"] + "; Capacity (MW)",
        uncertainty="Unquantified; historical project rating, not operating capacity",
    )
    row = evidence_record(
        dict(
            record_id=stable_id("projects", "reviewed-accession", review["accession"]),
            entity_type="projects",
            name=review["name"],
            aliases=[],
            country_code="UGA",
            record_scope="plant",
            capacity_scope="Project; physical overlap unresolved",
            aggregation_role="unresolved",
            status="unknown",
            status_as_of=now[:10],
            status_date_basis=(
                "Review date; 2023 construction/licensed category is not current status"
            ),
            technology="unknown",
            external_ids_json="{}",
            observations_json=canonical_json([obs]),
            extensions_json=canonical_json(
                dict(
                    era_planned_inventory=item,
                    era_planned_review=review,
                    registry_id_status="Catalogue accession, not an official licence ID",
                )
            ),
        ),
        source_id=SOURCE_ID,
        now=now,
        locator=review["locator"],
    )

    if extra := review.get("corroboration"):
        kw = extra["project_kw"]
        if (
            isinstance(kw, bool)
            or not isinstance(kw, (float, int))
            or not math.isfinite(kw)
            or kw < 0
            or extra.get("source_id") != "ueccc-orio-tender-20200929"
            or extra.get("period") != "2020-09-29"
            or not extra.get("locator")
            or not extra.get("basis")
        ):
            raise ValueError("Invalid corroborating procurement evidence")
        observations = json.loads(row["observations_json"])
        observations.append(
            dict(
                field="planned_capacity_kw",
                value=extra["project_kw"],
                unit="kW",
                kind="reported",
                period=extra["period"],
                boundary=extra["basis"],
                source_id=extra["source_id"],
                locator=extra["locator"],
                uncertainty="Unquantified",
            )
        )
        row["observations_json"] = canonical_json(observations)
        fs, ev = json.loads(row["field_sources_json"]), json.loads(row["evidence_json"])
        for field in ("name", "observations_json", "extensions_json"):
            fs[field].append(extra["source_id"])
            ev[field]["original_value"] = row[field]
            ev[field]["locator"] += "; " + extra["locator"]
        row.update(
            field_sources_json=canonical_json(fs),
            evidence_json=canonical_json(ev),
            sources=sorted(set(row["sources"] + [extra["source_id"]])),
        )
    return row
