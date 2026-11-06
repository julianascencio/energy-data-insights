"""Build the reviewed three-site Bulk Infrastructure current portfolio batch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.portfolios import (
    parse_bulk_infrastructure_directory,
    parse_bulk_infrastructure_n01_expansion,
    parse_bulk_infrastructure_operations,
    parse_bulk_infrastructure_site_page,
)

RETRIEVED_AT = "2026-11-06T04:20:00Z"
AS_OF = "2026-11-06"
ORG_NAME = "Bulk Infrastructure"
ORG_ID = stable_id("organization", ORG_NAME)
DIRECTORY_URL = "https://bulkinfrastructure.com/data-centers/"
SERVICES_URL = "https://bulkinfrastructure.com/data-centers/services/"
EXPANSION_URL = (
    "https://bulkinfrastructure.com/newsroom/"
    "bulk-data-centers-unveils-plan-for-data-center-expansion-following-unprecedented-demand/"
)
META = {
    "OS-IX": (
        "Oslo",
        "NOR",
        "facility",
        "https://bulkinfrastructure.com/data-centers/locations/os-ix/",
    ),
    "N01": (
        "Kristiansand",
        "NOR",
        "campus",
        "https://bulkinfrastructure.com/data-centers/locations/n01/",
    ),
    "DK01": (
        "Esbjerg",
        "DNK",
        "campus",
        "https://bulkinfrastructure.com/data-centers/locations/dk01/",
    ),
}


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def observation(
    *,
    field: str,
    value: object,
    unit: str | None,
    source_id: str,
    boundary: str,
    as_of: str = AS_OF,
    kind: str = "reported",
) -> dict[str, object]:
    return {
        "as_of": as_of,
        "boundary": boundary,
        "field": field,
        "kind": kind,
        "locator": "current public page or dated expansion release",
        "source_id": source_id,
        "unit": unit,
        "value": value,
    }


def load_inputs(capture_dir: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    directory = parse_bulk_infrastructure_directory(
        (capture_dir / "directory.html").read_bytes(), source_url=DIRECTORY_URL
    )["candidates"]
    if [row["external_id"] for row in directory] != ["OS-IX", "N01", "DK01"]:
        raise ValueError("Changed Bulk Infrastructure current identity set")
    operations = parse_bulk_infrastructure_operations(
        (capture_dir / "services.html").read_bytes(), source_url=SERVICES_URL
    )
    if set(operations["operating_codes"]) != set(META):
        raise ValueError("Changed Bulk Infrastructure operating identity set")
    details = {
        code: parse_bulk_infrastructure_site_page(
            (capture_dir / f"{code.lower()}.html").read_bytes(),
            source_url=url,
            expected_code=code,
        )["candidate"]
        for code, (_locality, _country, _scope, url) in META.items()
    }
    expansion = parse_bulk_infrastructure_n01_expansion(
        (capture_dir / "n01-expansion.html").read_bytes(), source_url=EXPANSION_URL
    )["candidate"]
    return details, expansion


def observations(
    code: str, candidate: dict[str, Any], expansion: dict[str, Any]
) -> list[dict[str, object]]:
    site_source = f"bulk-{code.lower()}-current-20261106"
    if code == "OS-IX":
        return [
            observation(
                field="opened_year",
                value=candidate["opened_year"],
                unit="year",
                source_id=site_source,
                boundary="OS-IX opening year; no exact commissioning date inferred",
            ),
            observation(
                field="reported_redundant_power",
                value=candidate["reported_unclassified_power_mw"],
                unit="MW",
                source_id=site_source,
                boundary=(
                    "OS-IX 2N redundant power; source does not identify IT, grid or "
                    "total facility demand"
                ),
            ),
        ]
    if code == "DK01":
        return [
            observation(
                field="reported_secured_power",
                value=30.0,
                unit="MW",
                source_id="bulk-data-centers-directory-current-20261106",
                boundary=(
                    "DK01 directory card; source does not identify IT, grid or "
                    "total facility demand"
                ),
            )
        ]
    return [
        observation(
            field="campus_land",
            value=candidate["campus_land_hectares"],
            unit="ha",
            source_id=site_source,
            boundary="N01 zoned campus land; not technical or data-hall area",
        ),
        observation(
            field="reported_power_potential",
            value=candidate["reported_unclassified_power_mw"],
            unit="MW",
            source_id=site_source,
            boundary=(
                "N01 up-to campus power potential; source does not identify IT, grid "
                "or total facility demand"
            ),
        ),
        observation(
            field="primary_substation_apparent_power",
            value=candidate["substation_apparent_power_mva"],
            unit="MVA",
            source_id=site_source,
            boundary="N01 high-voltage primary substations; not normalized MW capacity",
        ),
        observation(
            field="existing_facility_capacity",
            value=expansion["existing_facility_mw"],
            unit="MW",
            source_id="bulk-n01-expansion-20240123",
            boundary=(
                "Unnamed N01 facility reported ready for service in 2023; exact child "
                "identity and electrical boundary are not established"
            ),
            as_of=expansion["publication_date"],
        ),
        observation(
            field="new_facility_it_space",
            value=expansion["expansion_it_space_mw"],
            unit="MW",
            source_id="bulk-n01-expansion-20240123",
            boundary=(
                "Unnamed N01 facility announced under construction in 2024; source calls "
                "this IT space, but current completion is not established"
            ),
            as_of=expansion["publication_date"],
        ),
        observation(
            field="new_facility_completion_target",
            value=expansion["expansion_target_year"],
            unit="year",
            source_id="bulk-n01-expansion-20240123",
            boundary="Stale 2024 target; not actual commissioning evidence",
            as_of=expansion["publication_date"],
            kind="target",
        ),
        observation(
            field="future_additional_power",
            value=expansion["future_power_mw"],
            unit="MW",
            source_id="bulk-n01-expansion-20240123",
            boundary="Future additional campus power; not IT capacity or an energised supply",
            as_of=expansion["publication_date"],
            kind="target",
        ),
    ]


def build_record(
    code: str, candidate: dict[str, Any], expansion: dict[str, Any]
) -> dict[str, object]:
    locality, country, scope, url = META[code]
    site_source = f"bulk-{code.lower()}-current-20261106"
    source_ids = [
        "bulk-data-centers-directory-current-20261106",
        "bulk-data-centers-services-current-20261106",
        site_source,
    ]
    if code == "N01":
        source_ids.append("bulk-n01-expansion-20240123")
    fields = [
        "aggregation_role",
        "aliases",
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
    if scope == "campus":
        fields.append("campus_id")
    if code == "DK01":
        fields.append("technical_area_m2")
    evidence = {
        field: {
            "confidence": "high",
            "locator": candidate["locator"],
            "source_publication_dates": {
                source: "2024-01-23" if source == "bulk-n01-expansion-20240123" else None
                for source in source_ids
            },
            **({"unit": "m2"} if field == "technical_area_m2" else {}),
        }
        for field in fields
    }
    record: dict[str, object] = {
        "aggregation_role": "independent" if scope == "facility" else "aggregate",
        "aliases": [code, locality],
        "capacity_scope": (
            f"{code} {scope}; generic power statements remain observations and all "
            "normalized IT, grid and facility capacity fields are null"
        ),
        "country_code": country,
        "created_at": RETRIEVED_AT,
        "entities_json": compact(
            [
                {"name": ORG_NAME, "organization_id": ORG_ID, "role": "owner"},
                {"name": ORG_NAME, "organization_id": ORG_ID, "role": "operator"},
            ]
        ),
        "entity_type": "projects",
        "evidence_json": compact(evidence),
        "external_ids_json": compact({"bulk_infrastructure": code}),
        "facility_id": stable_id("facility", ORG_NAME, code),
        "facility_type": "colocation",
        "field_sources_json": compact({field: source_ids for field in fields}),
        "last_verified_at": RETRIEVED_AT,
        "locality": locality,
        "name": f"Bulk Infrastructure {code}",
        "observations_json": compact(observations(code, candidate, expansion)),
        "official_url": url,
        "operator_names": [ORG_NAME],
        "owner_names": [ORG_NAME],
        "quality_status": "needs_review",
        "record_id": stable_id("projects", ORG_NAME, code),
        "record_scope": scope,
        "source_urls": sorted(
            [
                DIRECTORY_URL,
                SERVICES_URL,
                url,
                *([EXPANSION_URL] if code == "N01" else []),
            ]
        ),
        "sources": source_ids,
        "status": "operational",
        "status_as_of": AS_OF,
        "status_date_basis": (
            "Current operator services page explicitly says it is operating N01, DK01 "
            "and OS-IX; no child-facility commissioning is inferred"
        ),
        "updated_at": RETRIEVED_AT,
    }
    if scope == "campus":
        record["campus_id"] = stable_id("campus", ORG_NAME, code)
    if code == "DK01":
        record["technical_area_m2"] = candidate["technical_area_m2"]
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    candidates, expansion = load_inputs(args.capture_dir)
    rows = [build_record(code, candidates[code], expansion) for code in META]
    args.output.write_text("".join(f"{compact(row)}\n" for row in rows), encoding="utf-8")
    print(f"Wrote {len(rows)} reviewed Bulk Infrastructure records to {args.output}")


if __name__ == "__main__":
    main()
