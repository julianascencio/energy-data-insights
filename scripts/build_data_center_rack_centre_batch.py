"""Build the reviewed Rack Centre LGS1, LGS2 and Lagos campus batch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.portfolios import (
    parse_rack_centre_campus,
    parse_rack_centre_facility_page,
    parse_rack_centre_lgs2_commissioning,
    parse_uptime_rack_centre_story,
)

RETRIEVED_AT = "2026-11-06T07:23:39Z"
AS_OF = "2026-11-06"
ORG_NAME = "Rack Centre"
ORG_ID = stable_id("organization", ORG_NAME)
CAMPUS_URL = "https://rack-centre.com/lagos-data-centre-campus-expansion/"
LGS1_URL = f"{CAMPUS_URL}data-centre-campus-lgs-1/"
LGS2_URL = f"{CAMPUS_URL}data-centre-campus-lgs-2-expansion/"
COMMISSIONING_URL = "https://rack-centre.com/rack-centres-lgs2-12mw-data-centre-commissioned/"
UPTIME_URL = (
    "https://uptimeinstitute.com/clients/rack-centre-tier-iii-certification-of-constructed-facility"
)


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def observation(
    *, field: str, value: object, unit: str | None, source_id: str, locator: str, boundary: str
) -> dict[str, object]:
    return {
        "as_of": AS_OF,
        "boundary": boundary,
        "field": field,
        "kind": "reported",
        "locator": locator,
        "source_id": source_id,
        "unit": unit,
        "value": value,
    }


def evidence(fields: list[str], source_ids: list[str], locator: str) -> tuple[str, str]:
    publications = {
        "rack-centre-lgs2-commissioning-20250410": "2025-04-10",
        "uptime-rack-centre-tier-story": None,
    }
    field_sources = {field: source_ids for field in fields}
    details = {
        field: {
            "confidence": "high",
            "locator": locator,
            "source_publication_dates": {
                source_id: publications.get(source_id) for source_id in source_ids
            },
            **(
                {"unit": "MW"}
                if field == "it_capacity_mw"
                else {"unit": "m2"}
                if field == "technical_area_m2"
                else {}
            ),
        }
        for field in fields
    }
    return compact(field_sources), compact(details)


def common(
    *, name: str, external_id: str, scope: str, role: str, source_ids: list[str], url: str
) -> dict[str, object]:
    campus_id = stable_id("campus", ORG_NAME, "Lagos Campus")
    facility_id = stable_id("facility", ORG_NAME, external_id)
    record_id = stable_id("projects", ORG_NAME, external_id)
    fields = [
        "aggregation_role",
        "aliases",
        "campus_id",
        "capacity_scope",
        "country_code",
        "entities_json",
        "external_ids_json",
        "facility_id",
        "facility_type",
        "locality",
        "name",
        "observations_json",
        "official_url",
        "operator_names",
        "owner_names",
        "record_scope",
        "status",
        "status_as_of",
        "status_date_basis",
    ]
    if scope == "facility":
        fields.append("parent_record_id")
    field_sources, field_evidence = evidence(fields, source_ids, "current official page")
    row: dict[str, object] = {
        "aggregation_role": role,
        "aliases": [external_id],
        "campus_id": campus_id,
        "capacity_scope": (
            "Rack Centre Lagos Campus aggregate; explicit campus totals are excluded from "
            "capacity sums under every filter."
            if scope == "campus"
            else f"{external_id} exact facility only; no campus total is allocated."
        ),
        "country_code": "NGA",
        "created_at": RETRIEVED_AT,
        "entities_json": compact(
            [
                {"name": ORG_NAME, "organization_id": ORG_ID, "role": "owner"},
                {"name": ORG_NAME, "organization_id": ORG_ID, "role": "operator"},
            ]
        ),
        "entity_type": "projects",
        "evidence_json": field_evidence,
        "external_ids_json": compact({"rack_centre": external_id}),
        "facility_id": facility_id,
        "facility_type": "colocation",
        "field_sources_json": field_sources,
        "last_verified_at": RETRIEVED_AT,
        "locality": "Lagos",
        "name": name,
        "official_url": url,
        "operator_names": [ORG_NAME],
        "owner_names": [ORG_NAME],
        "quality_status": "source_backed",
        "record_id": record_id,
        "record_scope": scope,
        "source_urls": [url],
        "sources": source_ids,
        "status": "operational",
        "status_as_of": AS_OF,
        "status_date_basis": "Current active operator page and dated commissioning evidence",
        "updated_at": RETRIEVED_AT,
    }
    if scope == "facility":
        row["parent_record_id"] = stable_id("projects", ORG_NAME, "Lagos Campus")
    return row


def build(capture_dir: Path) -> list[dict[str, object]]:
    campus = parse_rack_centre_campus(
        (capture_dir / "campus.html").read_bytes(), source_url=CAMPUS_URL
    )["candidate"]
    lgs1 = parse_rack_centre_facility_page(
        (capture_dir / "lgs1.html").read_bytes(), source_url=LGS1_URL, expected_code="LGS1"
    )["candidate"]
    lgs2 = parse_rack_centre_facility_page(
        (capture_dir / "lgs2.html").read_bytes(), source_url=LGS2_URL, expected_code="LGS2"
    )["candidate"]
    commissioning = parse_rack_centre_lgs2_commissioning(
        (capture_dir / "commissioning.html").read_bytes(), source_url=COMMISSIONING_URL
    )["candidate"]
    issuer = parse_uptime_rack_centre_story(
        (capture_dir / "uptime-story.html").read_bytes(), source_url=UPTIME_URL
    )["candidate"]
    if lgs2["it_capacity_mw"] != commissioning["it_capacity_mw"]:
        raise ValueError("Changed LGS2 IT-capacity agreement")

    campus_sources = ["rack-centre-lagos-campus-current-20261106"]
    campus_row = common(
        name="Rack Centre Lagos Campus",
        external_id="Lagos Campus",
        scope="campus",
        role="aggregate",
        source_ids=campus_sources,
        url=CAMPUS_URL,
    )
    campus_row.update(
        {
            "it_capacity_basis": "operational",
            "it_capacity_mw": campus["it_capacity_mw"],
            "observations_json": compact(
                [
                    observation(
                        field="campus_net_lettable_space",
                        value=campus["technical_area_m2"],
                        unit="m2",
                        source_id=campus_sources[0],
                        locator=campus["locator"],
                        boundary=(
                            "Whole-campus net lettable space; not assumed to be technical area."
                        ),
                    )
                ]
            ),
            "notes": "Explicit two-facility campus aggregate; excluded from capacity totals.",
        }
    )
    campus_fields = json.loads(str(campus_row["field_sources_json"]))
    campus_evidence = json.loads(str(campus_row["evidence_json"]))
    for field in ("it_capacity_basis", "it_capacity_mw"):
        campus_fields[field] = campus_sources
        campus_evidence[field] = {
            "confidence": "high",
            "locator": campus["locator"],
            "source_publication_dates": {campus_sources[0]: None},
            **({"unit": "MW"} if field == "it_capacity_mw" else {}),
        }
    campus_row["field_sources_json"] = compact(campus_fields)
    campus_row["evidence_json"] = compact(campus_evidence)

    lgs1_sources = ["rack-centre-lgs1-current-20261106", "uptime-rack-centre-tier-story"]
    lgs1_row = common(
        name="Rack Centre LGS1",
        external_id="LGS1",
        scope="facility",
        role="child",
        source_ids=lgs1_sources,
        url=LGS1_URL,
    )
    lgs1_row.update(
        {
            "it_capacity_basis": "operational",
            "it_capacity_mw": lgs1["it_capacity_mw"],
            "technical_area_m2": lgs1["technical_area_m2"],
            "observations_json": compact(
                [
                    observation(
                        field="operational_since",
                        value=str(lgs1["status_year"]),
                        unit=None,
                        source_id="rack-centre-lgs1-current-20261106",
                        locator=lgs1["locator"],
                        boundary="Year precision only; no full commissioning date inferred.",
                    ),
                    {
                        "as_of": AS_OF,
                        "boundary": (
                            "Operator page omits measurement period and method; observation only."
                        ),
                        "field": "pue",
                        "kind": "unspecified",
                        "locator": lgs1["locator"],
                        "measurement_period": None,
                        "source_id": "rack-centre-lgs1-current-20261106",
                        "unit": None,
                        "value": 1.5,
                    },
                    observation(
                        field="issuer_certification_awards",
                        value=issuer["awards"],
                        unit=None,
                        source_id="uptime-rack-centre-tier-story",
                        locator=issuer["locator"],
                        boundary=(
                            "Issuer evidence supports the original Lagos facility, now "
                            "identified by the operator as LGS1. Month-only award dates do "
                            "not satisfy certifications_json full-date requirements."
                        ),
                    ),
                ]
            ),
            "notes": (
                "Issuer awards are retained as observations because only month precision "
                "is available; no LGS2 award is inferred."
            ),
        }
    )
    lgs1_fields = json.loads(str(lgs1_row["field_sources_json"]))
    lgs1_evidence = json.loads(str(lgs1_row["evidence_json"]))
    for field, sources, locator, unit in (
        ("it_capacity_basis", [lgs1_sources[0]], lgs1["locator"], None),
        ("it_capacity_mw", [lgs1_sources[0]], lgs1["locator"], "MW"),
        ("technical_area_m2", [lgs1_sources[0]], lgs1["locator"], "m2"),
    ):
        lgs1_fields[field] = sources
        lgs1_evidence[field] = {
            "confidence": "high",
            "locator": locator,
            "source_publication_dates": {source: None for source in sources},
            **({"unit": unit} if unit else {}),
        }
    lgs1_row["field_sources_json"] = compact(lgs1_fields)
    lgs1_row["evidence_json"] = compact(lgs1_evidence)
    lgs1_row["source_urls"] = sorted([LGS1_URL, UPTIME_URL])

    lgs2_sources = [
        "rack-centre-lgs2-current-20261106",
        "rack-centre-lgs2-commissioning-20250410",
        "rack-centre-lagos-campus-current-20261106",
    ]
    lgs2_row = common(
        name="Rack Centre LGS2",
        external_id="LGS2",
        scope="facility",
        role="child",
        source_ids=lgs2_sources,
        url=LGS2_URL,
    )
    lgs2_row.update(
        {
            "commissioning_date": commissioning["commissioning_date"],
            "it_capacity_basis": "operational",
            "it_capacity_mw": lgs2["it_capacity_mw"],
            "conflicts_json": compact(
                {
                    "technical_area_m2": [
                        {
                            "value": lgs2["reported_white_space_m2"],
                            "unit": "m2",
                            "sources": [lgs2_sources[0]],
                            "observed_at": RETRIEVED_AT,
                            "locator": lgs2["locator"],
                        },
                        {
                            "value": campus["lgs2_white_space_m2"],
                            "unit": "m2",
                            "sources": [lgs2_sources[2]],
                            "observed_at": RETRIEVED_AT,
                            "locator": campus["locator"],
                        },
                    ]
                }
            ),
            "observations_json": compact(
                [
                    observation(
                        field="utility_apparent_power",
                        value=lgs2["utility_apparent_power_mva"],
                        unit="MVA",
                        source_id=lgs2_sources[0],
                        locator=lgs2["locator"],
                        boundary="Utility apparent-power commitment; not converted to MW.",
                    ),
                    observation(
                        field="designed_pue",
                        value=1.35,
                        unit=None,
                        source_id=lgs2_sources[2],
                        locator=campus["locator"],
                        boundary="Design value, not measured operating PUE.",
                    ),
                ]
            ),
            "notes": (
                "Current pages conflict on LGS2 white space (7,200 versus 3,240 m2); "
                "technical_area_m2 remains null."
            ),
            "quality_status": "needs_review",
        }
    )
    lgs2_fields = json.loads(str(lgs2_row["field_sources_json"]))
    lgs2_evidence = json.loads(str(lgs2_row["evidence_json"]))
    for field, sources, locator, unit in (
        ("commissioning_date", [lgs2_sources[1]], commissioning["locator"], None),
        ("it_capacity_basis", lgs2_sources[:2], commissioning["locator"], None),
        ("it_capacity_mw", lgs2_sources[:2], commissioning["locator"], "MW"),
        (
            "conflicts_json",
            [lgs2_sources[0], lgs2_sources[2]],
            "conflicting current white-space cards",
            None,
        ),
    ):
        lgs2_fields[field] = sources
        lgs2_evidence[field] = {
            "confidence": "high",
            "locator": locator,
            "source_publication_dates": {
                source: ("2025-04-10" if source == lgs2_sources[1] else None) for source in sources
            },
            **({"unit": unit} if unit else {}),
        }
    lgs2_row["field_sources_json"] = compact(lgs2_fields)
    lgs2_row["evidence_json"] = compact(lgs2_evidence)
    lgs2_row["source_urls"] = sorted([LGS2_URL, COMMISSIONING_URL, CAMPUS_URL])
    return [campus_row, lgs1_row, lgs2_row]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = build(args.capture_dir)
    args.output.write_text("".join(f"{compact(row)}\n" for row in rows), encoding="utf-8")
    print(f"Wrote {len(rows)} reviewed Rack Centre project records to {args.output}")


if __name__ == "__main__":
    main()
