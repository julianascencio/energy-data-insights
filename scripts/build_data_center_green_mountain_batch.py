"""Build the reviewed current Green Mountain seven-site portfolio batch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.portfolios import (
    parse_green_mountain_facility_page,
    parse_green_mountain_portfolio,
)

RETRIEVED_AT = "2026-11-06T00:24:00Z"
AS_OF = "2026-11-06"
ORG_NAME = "Green Mountain"
ORG_ID = stable_id("organization", ORG_NAME)
PORTFOLIO_SOURCE = "green-mountain-portfolio-current-20261106"
PORTFOLIO_URL = "https://greenmountain.no/data-centers/"

SITES: dict[str, dict[str, Any]] = {
    "SVG-Rennesøy": {
        "name": "Green Mountain SVG-Rennesøy",
        "country": "NOR",
        "locality": "Rennesøy",
        "scope": "facility",
        "facility_type": "colocation",
        "it_capacity_basis": "design_maximum",
        "filename": "data-center-svg-rennesoy.html",
        "slug": "svg-rennesoy",
    },
    "TEL-Rjukan": {
        "name": "Green Mountain TEL-Rjukan campus",
        "country": "NOR",
        "locality": "Rjukan",
        "scope": "campus",
        "facility_type": "colocation",
        "it_capacity_basis": "ultimate_planned",
        "filename": "data-center-tel-rjukan.html",
        "slug": "tel-rjukan",
    },
    "OSL-Enebakk": {
        "name": "Green Mountain OSL-Enebakk campus",
        "country": "NOR",
        "locality": "Enebakk",
        "scope": "campus",
        "facility_type": "colocation",
        "it_capacity_basis": "ultimate_planned",
        "filename": "data-center-osl-enebakk.html",
        "slug": "osl-enebakk",
    },
    "OSL-Hamar": {
        "name": "Green Mountain OSL-Hamar campus",
        "country": "NOR",
        "locality": "Hamar",
        "scope": "campus",
        "facility_type": "hyperscale",
        "it_capacity_basis": "ultimate_planned",
        "filename": "data-center-osl-hamar.html",
        "slug": "osl-hamar",
    },
    "LON-East": {
        "name": "Green Mountain LON-East campus",
        "country": "GBR",
        "locality": "Romford",
        "scope": "campus",
        "facility_type": "colocation",
        "filename": "data-center-lon-east.html",
        "slug": "lon-east",
    },
    "FRA-Mainz": {
        "name": "Green Mountain FRA-Mainz campus",
        "country": "DEU",
        "locality": "Mainz",
        "scope": "campus",
        "facility_type": "hyperscale",
        "filename": "data-center-fra-mainz.html",
        "slug": "fra-mainz",
        "joint_owner": "KMW",
    },
    "SVG-Undheim": {
        "name": "Green Mountain SVG-Undheim campus",
        "country": "NOR",
        "locality": "Undheim",
        "scope": "campus",
        "facility_type": "hyperscale",
        "it_capacity_basis": "ultimate_planned",
        "filename": "data-center-svg-undheim.html",
        "slug": "svg-undheim",
    },
}


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def observation(
    *, field: str, value: object, unit: str | None, source_id: str, boundary: str, **extra: object
) -> dict[str, object]:
    return {
        "as_of": AS_OF,
        "boundary": boundary,
        "field": field,
        "kind": "reported",
        "locator": "current site page / public metric cards and narrative",
        "source_id": source_id,
        "unit": unit,
        "value": value,
        **extra,
    }


def evidence(fields: list[str], sources: list[str]) -> tuple[str, str]:
    details = {
        field: {
            "confidence": "high",
            "locator": "current operator portfolio and site page",
            "source_publication_dates": {source: None for source in sources},
            **({"unit": "MW"} if field == "it_capacity_mw" else {}),
            **({"unit": "m2"} if field == "data_hall_area_m2" else {}),
        }
        for field in fields
    }
    return compact({field: sources for field in fields}), compact(details)


def load_inputs(capture_dir: Path) -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
    portfolio = parse_green_mountain_portfolio(
        (capture_dir / "data-centers.html").read_bytes(), source_url=PORTFOLIO_URL
    )
    statuses = {row["external_id"]: row["status"] for row in portfolio["candidates"]}
    if set(statuses) != set(SITES):
        raise ValueError("Changed Green Mountain portfolio inventory")
    candidates: dict[str, dict[str, Any]] = {}
    for code, meta in SITES.items():
        url = f"https://greenmountain.no/data-center/{meta['slug']}/"
        candidates[code] = parse_green_mountain_facility_page(
            (capture_dir / meta["filename"]).read_bytes(),
            source_url=url,
            expected_code=code,
        )["candidate"]
    return statuses, candidates


def build_record(code: str, status: str, candidate: dict[str, Any]) -> dict[str, object]:
    meta = SITES[code]
    site_source = f"green-mountain-{meta['slug']}-current-20261106"
    site_url = f"https://greenmountain.no/data-center/{meta['slug']}/"
    sources = [PORTFOLIO_SOURCE, site_source]
    observations: list[dict[str, object]] = []

    if candidate.get("campus_area_m2") is not None:
        observations.append(
            observation(
                field="reported_campus_footprint",
                value=candidate["campus_area_m2"],
                unit="m2",
                source_id=site_source,
                boundary=f"{code} site/campus footprint; never normalized as data-hall area",
            )
        )
    if candidate.get("building_count") is not None:
        observations.append(
            observation(
                field="reported_building_count",
                value=int(candidate["building_count"]),
                unit="buildings",
                source_id=site_source,
                boundary=f"{code} printed existing/planned site boundary; not facility records",
            )
        )
    if candidate.get("average_pue") is not None:
        observations.append(
            observation(
                field="average_pue",
                value=candidate["average_pue"],
                unit="ratio",
                source_id=site_source,
                boundary=f"{code} operator-labelled average PUE with no measurement period",
                measurement_period=None,
            )
        )
    if candidate.get("average_pue_min") is not None:
        observations.append(
            observation(
                field="average_pue_range",
                value=[candidate["average_pue_min"], candidate["average_pue_max"]],
                unit="ratio",
                source_id=site_source,
                boundary=f"{code} operator-labelled range; no scalar PUE inferred",
                measurement_period=None,
            )
        )
    if candidate.get("grid_supplies") is not None:
        observations.append(
            observation(
                field="grid_supply_count",
                value=int(candidate["grid_supplies"]),
                unit="supplies",
                source_id=site_source,
                boundary=f"{code} count only; no voltage or grid MW inferred",
            )
        )

    normalized_it = candidate.get("total_it_capacity_mw")
    if code == "TEL-Rjukan":
        normalized_it = candidate["potential_site_capacity_mw"]
    data_hall_area = candidate.get("it_space_m2") or candidate.get("existing_it_space_m2")
    for field, key, boundary in (
        ("reported_total_site_capacity", "total_site_capacity_mw", "site capacity, not IT/grid"),
        ("reported_secured_power_capacity", "secured_power_capacity_mw", "secured power, not IT"),
        ("reported_power_capacity", "power_capacity_mw", "power capacity, not IT/grid"),
        ("reported_new_secured_capacity", "new_secured_capacity_mw", "new secured capacity"),
        ("reported_maximum_cooling_capacity", "maximum_cooling_capacity_mw", "cooling, not IT"),
    ):
        if candidate.get(key) is not None:
            observations.append(
                observation(
                    field=field,
                    value=candidate[key],
                    unit="MW",
                    source_id=site_source,
                    boundary=f"{code} {boundary}; retained outside normalized capacity totals",
                )
            )

    if code == "OSL-Enebakk":
        observations.extend(
            [
                observation(
                    field="line_of_sight_capacity",
                    value=94,
                    unit="MW",
                    source_id=site_source,
                    boundary="OSL-Enebakk line-of-sight capacity; electrical basis unstated",
                ),
                observation(
                    field="completed_building_capacities",
                    value=[4, 14.5, 10],
                    unit="MW",
                    source_id=site_source,
                    boundary="Three separately dated completed buildings; no campus sum inferred",
                    completion_markers=["October 2020", "December 2022", "2024"],
                ),
            ]
        )
    elif code == "OSL-Hamar":
        observations.extend(
            [
                observation(
                    field="operational_building_capacity",
                    value=90,
                    unit="MW",
                    source_id=site_source,
                    boundary="Three complete operational buildings; campus aggregate observation",
                ),
                observation(
                    field="planned_it_space",
                    value=candidate["planned_it_space_m2"],
                    unit="m2",
                    source_id=site_source,
                    boundary="Two planned buildings; not normalized current data-hall area",
                ),
            ]
        )
    elif code == "FRA-Mainz":
        observations.extend(
            [
                observation(
                    field="future_power_capacity",
                    value=80,
                    unit="MW",
                    source_id=site_source,
                    boundary=(
                        "Parenthetical 2026 power statement; conflicts with 54 MW current card"
                    ),
                ),
                observation(
                    field="ready_for_service_target",
                    value="Q4 2026",
                    unit=None,
                    source_id=site_source,
                    boundary="Target quarter, not evidence of commissioning",
                ),
            ]
        )
    elif code == "SVG-Undheim":
        observations.append(
            observation(
                field="full_completion_target",
                value="2028",
                unit="year",
                source_id=site_source,
                boundary="Full-campus target year, not a commissioning date",
            )
        )
    elif code == "LON-East":
        observations.extend(
            [
                observation(
                    field="existing_building_space",
                    value=candidate["existing_space_m2"],
                    unit="m2",
                    source_id=site_source,
                    boundary="Existing-building total space; not normalized data-hall area",
                ),
                observation(
                    field="space_currently_in_construction",
                    value=candidate["construction_space_m2"],
                    unit="m2",
                    source_id=site_source,
                    boundary="Construction space; not normalized current data-hall area",
                ),
            ]
        )

    owner_names = [ORG_NAME]
    entities = [
        {"name": ORG_NAME, "organization_id": ORG_ID, "role": "owner"},
        {"name": ORG_NAME, "organization_id": ORG_ID, "role": "operator"},
    ]
    if meta.get("joint_owner"):
        joint_owner = str(meta["joint_owner"])
        owner_names.append(joint_owner)
        entities.append(
            {
                "name": joint_owner,
                "organization_id": stable_id("organization", joint_owner),
                "role": "joint_owner",
            }
        )
    fields = [
        "aliases",
        "aggregation_role",
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
    if meta["scope"] == "campus":
        fields.append("campus_id")
    if normalized_it is not None:
        fields.extend(["it_capacity_basis", "it_capacity_mw"])
    if data_hall_area is not None:
        fields.append("data_hall_area_m2")
    field_sources, evidence_json = evidence(fields, sources)
    aggregate = meta["scope"] == "campus"
    row: dict[str, object] = {
        "aliases": [code],
        "aggregation_role": "aggregate" if aggregate else "independent",
        "capacity_scope": (
            f"{code} campus aggregate; always excluded from capacity totals; building-level "
            "records remain unresolved"
            if aggregate
            else f"{code} independently identified facility design capability"
        ),
        "country_code": meta["country"],
        "created_at": RETRIEVED_AT,
        "entities_json": compact(entities),
        "entity_type": "projects",
        "evidence_json": evidence_json,
        "external_ids_json": compact({"green_mountain": code}),
        "facility_id": stable_id("facility", ORG_NAME, code),
        "facility_type": meta["facility_type"],
        "field_sources_json": field_sources,
        "last_verified_at": RETRIEVED_AT,
        "locality": meta["locality"],
        "name": meta["name"],
        "observations_json": compact(observations),
        "official_url": site_url,
        "operator_names": [ORG_NAME],
        "owner_names": owner_names,
        "quality_status": "needs_review"
        if code in {"OSL-Enebakk", "FRA-Mainz"}
        else "source_backed",
        "record_id": stable_id("projects", ORG_NAME, code),
        "record_scope": meta["scope"],
        "source_urls": sorted([PORTFOLIO_URL, site_url]),
        "sources": sources,
        "status": status,
        "status_as_of": AS_OF,
        "status_date_basis": "current operator portfolio lifecycle statement",
        "updated_at": RETRIEVED_AT,
    }
    if aggregate:
        row["campus_id"] = stable_id("campus", ORG_NAME, code)
    if normalized_it is not None:
        row["it_capacity_basis"] = meta["it_capacity_basis"]
        row["it_capacity_mw"] = normalized_it
    if data_hall_area is not None:
        row["data_hall_area_m2"] = data_hall_area
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    statuses, candidates = load_inputs(args.capture_dir)
    rows = [build_record(code, statuses[code], candidates[code]) for code in SITES]
    args.output.write_text("".join(f"{compact(row)}\n" for row in rows), encoding="utf-8")
    print(f"Wrote {len(rows)} reviewed Green Mountain project records to {args.output}")


if __name__ == "__main__":
    main()
