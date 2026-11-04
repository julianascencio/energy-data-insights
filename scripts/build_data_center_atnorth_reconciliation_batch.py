"""Add FIN03 and reconcile reviewed atNorth Denmark/Sweden project evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from energy_data_retrieval.data_center_catalogue import stable_id

RETRIEVED_AT = "2026-11-04T09:20:00Z"
AS_OF = "2026-11-04"

FIN03 = stable_id("projects", "atNorth", "FIN03")
DEN01 = "917049f9-887f-502b-a4f8-4a11a707a6a6"
DEN02 = "34a77a78-c1c9-5cef-b171-8dc1123ad259"
SWE04 = "037414f4-36e7-5e55-a76a-48019a8979d4"
ATNORTH_ORG = stable_id("organization", "atNorth")

SOURCES = {
    "atnorth-esg2025-20261103": {
        "url": "https://www.atnorth.com/wp-content/uploads/2026/06/Sustainability-Report-2025.pdf",
        "publication_date": None,
    },
    "atnorth-fin03-acquisition-20230104": {
        "url": "https://www.atnorth.com/news/atnorth-acquires-two-additional-nordic-data-centers/",
        "publication_date": "2023-01-04",
    },
    "advania-finland-divestment-20230104": {
        "url": "https://www.advania.com/article/advania-divests-two-data-centres-in-finland",
        "publication_date": "2023-01-04",
    },
    "dcd-atnorth-finland-acquisition-20230104": {
        "url": "https://www.datacenterdynamics.com/en/news/atnorth-acquires-two-data-centers-in-finland-from-advania/",
        "publication_date": "2023-01-04",
    },
    "atnorth-fin03-identity-20261104": {
        "url": "https://www.atnorth.com/news/atnorth-announces-heat-reuse-partnership-with-kesko-corporation/",
        "publication_date": None,
    },
    "atnorth-den01-current-20261104": {
        "url": "https://www.atnorth.com/nordic-data-centers/denmark-data-centers/copenhagen-metro-site/",
        "publication_date": None,
    },
    "atnorth-den02-varde-approval-20261007": {
        "url": "https://www.atnorth.com/atnorth-i-varde/",
        "publication_date": "2026-10-07",
    },
    "solleftea-swe04-status-20260528": {
        "url": "https://www.solleftea.se/Naringsliv--arbete/etablera-dig-i-solleftea-kommun/hamre-industripark/atnorth",
        "publication_date": "2026-05-28",
    },
    "solleftea-swe04-grid-20260528": {
        "url": "https://www.solleftea.se/Kommun--politik/kommun--politik-nyheter/kommun--politik/2026-05-28-atnorths-etablering-i-langsele-tar-nasta-steg-nar-e.on-ansluter-200-mw",
        "publication_date": "2026-05-28",
    },
}


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def observation(
    source_id: str,
    field: str,
    value: object,
    *,
    boundary: str,
    locator: str,
    unit: str | None = None,
    kind: str = "reported",
    qualifier: str | None = None,
    as_of: str = AS_OF,
) -> dict[str, object]:
    item: dict[str, object] = {
        "as_of": as_of,
        "boundary": boundary,
        "field": field,
        "kind": kind,
        "locator": locator,
        "source_id": source_id,
        "unit": unit,
        "value": value,
    }
    if qualifier:
        item["qualifier"] = qualifier
    return item


def add_sources(record: dict[str, Any], source_ids: list[str]) -> None:
    record["sources"] = sorted(set(record["sources"] + source_ids))
    record["source_urls"] = sorted(
        set(record.get("source_urls", []) + [SOURCES[source_id]["url"] for source_id in source_ids])
    )
    record["updated_at"] = RETRIEVED_AT
    record["last_verified_at"] = RETRIEVED_AT


def add_evidence(
    record: dict[str, Any],
    field: str,
    source_ids: list[str],
    locator: str,
    *,
    unit: str | None = None,
    confidence: str = "high",
) -> None:
    evidence = json.loads(record["evidence_json"])
    item: dict[str, object] = {
        "confidence": confidence,
        "locator": locator,
        "source_publication_dates": {
            source_id: SOURCES[source_id]["publication_date"] for source_id in source_ids
        },
    }
    if unit:
        item["unit"] = unit
    evidence[field] = item
    record["evidence_json"] = compact(evidence)
    field_sources = json.loads(record["field_sources_json"])
    field_sources[field] = sorted(set(field_sources.get(field, []) + source_ids))
    record["field_sources_json"] = compact(field_sources)


def new_fin03() -> dict[str, Any]:
    sources = [
        "advania-finland-divestment-20230104",
        "atnorth-esg2025-20261103",
        "atnorth-fin03-acquisition-20230104",
        "atnorth-fin03-identity-20261104",
        "dcd-atnorth-finland-acquisition-20230104",
    ]
    locators = {
        "aggregation_role": "independent acquired facility identity",
        "capacity_scope": "reviewed sources disclose no FIN03-only capacity",
        "country_code": "2023 acquisition release and 2025 sustainability report",
        "entities_json": "operator acquisition and operation statements",
        "external_ids_json": "operator article names FIN03",
        "facility_id": "stable operator facility code FIN03",
        "facility_type": "Advania colocation agreement and atNorth operation",
        "locality": "DCD operator-confirmed update identifies Espoo",
        "name": "operator article names FIN03",
        "observations_json": "reviewed acquisition and locality boundaries",
        "official_url": "operator acquisition release",
        "operator_names": "operator acquisition release",
        "owner_names": "operator acquisition release",
        "record_scope": "separately named acquired facility",
        "status": "2025 sustainability report operational map",
        "status_as_of": "2025 sustainability report operational map; verified 2026-11-04",
        "status_date_basis": "report status and retrieval date",
    }
    evidence: dict[str, object] = {}
    field_sources: dict[str, list[str]] = {}
    for field, locator in locators.items():
        if field == "locality":
            ids = ["dcd-atnorth-finland-acquisition-20230104"]
            confidence = "medium"
        elif field in {"status", "status_as_of", "status_date_basis"}:
            ids = ["atnorth-esg2025-20261103"]
            confidence = "high"
        elif field in {"owner_names", "operator_names", "entities_json", "official_url"}:
            ids = ["atnorth-fin03-acquisition-20230104", "advania-finland-divestment-20230104"]
            confidence = "high"
        elif field == "observations_json":
            ids = [
                "atnorth-fin03-acquisition-20230104",
                "advania-finland-divestment-20230104",
                "dcd-atnorth-finland-acquisition-20230104",
            ]
            confidence = "high"
        else:
            ids = ["atnorth-fin03-identity-20261104", "atnorth-esg2025-20261103"]
            confidence = "high"
        evidence[field] = {
            "confidence": confidence,
            "locator": locator,
            "source_publication_dates": {
                source_id: (
                    SOURCES[source_id]["publication_date"] if source_id in SOURCES else None
                )
                for source_id in ids
            },
        }
        field_sources[field] = sorted(ids)
    observations = [
        observation(
            "atnorth-fin03-acquisition-20230104",
            "acquisition",
            "atNorth definitive agreement to acquire two Finnish facilities from Advania",
            boundary=(
                "FIN01 and FIN03 transaction; no facility-specific price or capacity disclosed"
            ),
            locator="opening and transaction description",
            as_of="2023-01-04",
        ),
        observation(
            "dcd-atnorth-finland-acquisition-20230104",
            "combined_portfolio_capacity",
            3.2,
            unit="MW",
            boundary="FIN01 and FIN03 combined; not allocated to FIN03",
            locator="operator-confirmed update",
            as_of="2023-01-04",
        ),
        observation(
            "dcd-atnorth-finland-acquisition-20230104",
            "combined_portfolio_racks",
            500,
            unit="racks",
            boundary="FIN01 and FIN03 combined; not allocated to FIN03",
            locator="operator-confirmed update",
            as_of="2023-01-04",
        ),
    ]
    return {
        "aggregation_role": "independent",
        "capacity_scope": (
            "FIN03 facility only; no FIN03-only IT, grid or facility capacity is disclosed; "
            "combined FIN01/FIN03 observations are excluded from normalized capacities"
        ),
        "country_code": "FIN",
        "created_at": RETRIEVED_AT,
        "entities_json": compact(
            [
                {"name": "atNorth", "organization_id": ATNORTH_ORG, "role": "owner"},
                {"name": "atNorth", "organization_id": ATNORTH_ORG, "role": "operator"},
            ]
        ),
        "entity_type": "projects",
        "evidence_json": compact(evidence),
        "external_ids_json": compact({"atnorth": "FIN03"}),
        "facility_id": stable_id("facility", "atNorth", "FIN03"),
        "facility_type": "colocation",
        "field_sources_json": compact(field_sources),
        "last_verified_at": RETRIEVED_AT,
        "locality": "Espoo",
        "name": "atNorth FIN03 Helsinki metro",
        "observations_json": compact(observations),
        "official_url": SOURCES["atnorth-fin03-acquisition-20230104"]["url"],
        "operator_names": ["atNorth"],
        "owner_names": ["atNorth"],
        "quality_status": "source_backed",
        "record_id": FIN03,
        "record_scope": "facility",
        "source_urls": sorted(
            {
                str(SOURCES[source_id]["url"])
                if source_id in SOURCES
                else "https://www.atnorth.com/wp-content/uploads/2026/06/Sustainability-Report-2025.pdf"
                for source_id in sources
            }
        ),
        "sources": sorted(sources),
        "status": "operational",
        "status_as_of": AS_OF,
        "status_date_basis": (
            "FIN03 is operational on the June 2026 operator sustainability map; "
            "status verified from the report on 2026-11-04"
        ),
        "updated_at": RETRIEVED_AT,
    }


def enrich_den01(record: dict[str, Any]) -> dict[str, Any]:
    record = dict(record)
    source = "atnorth-den01-current-20261104"
    observations = [
        item
        for item in json.loads(record["observations_json"])
        if item.get("field") not in {"first_phase_live", "campus_operational"}
    ]
    observations.extend(
        [
            observation(
                source,
                "first_phase_live",
                "Q4 2025",
                boundary="DEN01 first phase; quarter precision",
                locator="site introduction",
            ),
            observation(
                "atnorth-esg2025-20261103",
                "campus_operational",
                "Q1 2026",
                boundary="DEN01 campus operational milestone; phase boundary not specified",
                locator="report page 6 footnote",
            ),
        ]
    )
    record["observations_json"] = compact(observations)
    record.pop("conflicts_json", None)
    evidence = json.loads(record["evidence_json"])
    evidence.pop("conflicts_json", None)
    record["evidence_json"] = compact(evidence)
    field_sources = json.loads(record["field_sources_json"])
    field_sources.pop("conflicts_json", None)
    record["field_sources_json"] = compact(field_sources)
    add_sources(record, [source])
    add_evidence(
        record,
        "observations_json",
        [source, "atnorth-esg2025-20261103"],
        "first-phase and campus operational milestones with distinct boundaries",
    )
    return record


def enrich_den02(record: dict[str, Any]) -> dict[str, Any]:
    record = dict(record)
    source = "atnorth-den02-varde-approval-20261007"
    observations = [
        item for item in json.loads(record["observations_json"]) if item.get("source_id") != source
    ]
    observations.extend(
        [
            observation(
                source,
                "planning_approval",
                "Varde council local plan approved 2026-10-06",
                boundary="DEN02 campus planning milestone; not a construction-start event",
                locator="dated introduction",
                as_of="2026-10-07",
            ),
            observation(
                source,
                "construction_start_forecast",
                "Q4 2026",
                boundary="DEN02 first phase forecast; actual start not evidenced",
                locator="approval milestone paragraph",
                kind="target",
                as_of="2026-10-07",
            ),
            observation(
                source,
                "first_phase_power",
                60,
                unit="MW",
                boundary="DEN02 first phase; electrical boundary not specified",
                locator="About DEN02 paragraph",
                as_of="2026-10-07",
            ),
            observation(
                source,
                "campus_power",
                500,
                unit="MW",
                boundary="DEN02 total design; electrical boundary not specified",
                locator="About DEN02 paragraph",
                qualifier="up to",
                as_of="2026-10-07",
            ),
            observation(
                source,
                "campus_area",
                174,
                unit="ha",
                boundary="DEN02 whole greenfield campus",
                locator="About DEN02 paragraph",
                as_of="2026-10-07",
            ),
            observation(
                source,
                "heat_reuse_partner",
                (
                    "Selected Group greenhouse project; district-heating feasibility MoU with "
                    "Olgod Tekniske Vaerker"
                ),
                boundary="DEN02 planned heat reuse; no delivered heat quantity",
                locator="local energy system paragraphs",
                as_of="2026-10-07",
            ),
        ]
    )
    record["observations_json"] = compact(observations)
    record["contractor_names"] = sorted(set([*record.get("contractor_names", []), "TSL"]))
    record["status"] = "permitted"
    record["status_as_of"] = "2026-10-07"
    record["status_date_basis"] = (
        "Dated operator notice reports Varde council local-plan approval on 2026-10-06; "
        "construction start remains a Q4 2026 forecast"
    )
    renewable = json.loads(record["renewable_supply_json"])
    renewable["contractual_procurement"] = [
        {
            "as_of": "2026-10-07",
            "boundary": "DEN02 planned procurement; no executed PPA, volume or term disclosed",
            "claim": "Operator plans long-term PPAs with local energy suppliers",
            "source_id": source,
            "status": "planned",
        }
    ]
    record["renewable_supply_json"] = compact(renewable)
    add_sources(record, [source])
    add_evidence(record, "contractor_names", [source], "general-contractor section")
    add_evidence(record, "status", [source], "dated local-plan approval")
    add_evidence(record, "status_as_of", [source], "dated operator notice")
    add_evidence(record, "status_date_basis", [source], "dated operator notice")
    add_evidence(record, "renewable_supply_json", [source], "planned PPA statement")
    add_evidence(record, "observations_json", [source], "dated planning and scope statements")
    return record


def enrich_swe04(record: dict[str, Any]) -> dict[str, Any]:
    record = dict(record)
    sources = ["solleftea-swe04-status-20260528", "solleftea-swe04-grid-20260528"]
    observations = [
        item
        for item in json.loads(record["observations_json"])
        if item.get("source_id") not in sources and item.get("field") != "stale_operator_page_land"
    ]
    observations.extend(
        [
            observation(
                sources[0],
                "project_power",
                300,
                unit="MW",
                boundary="SWE04 planned establishment; electrical boundary not specified",
                locator="project introduction and current-status list",
                qualifier="up to",
                as_of="2026-05-28",
            ),
            observation(
                sources[0],
                "campus_land",
                50,
                unit="ha",
                boundary="municipal land sale for SWE04; approximate",
                locator="land-sale paragraph",
                qualifier="approximately",
                as_of="2026-05-28",
            ),
            observation(
                sources[0],
                "land_purchase_price",
                175_000_000,
                unit="SEK",
                boundary="municipal sale of approximately 50 ha; January 2026 valuation",
                locator="land-sale paragraph",
                as_of="2026-05-28",
            ),
            observation(
                sources[1],
                "grid_connection",
                200,
                unit="MW",
                boundary="SWE04 phase 1 contracted E.ON connection; not IT or facility demand",
                locator="connection agreement paragraph",
                as_of="2026-05-28",
            ),
            observation(
                sources[0],
                "industrial_park_power_capacity",
                500,
                unit="MW",
                boundary="Hamre industrial park under stated conditions; not SWE04 site capacity",
                locator="current-status list",
                qualifier="up to",
                as_of="2026-05-28",
            ),
            observation(
                sources[1],
                "grid_connection_voltage",
                130,
                unit="kV",
                boundary="new approximately 5 km line from Hamre to Nasen grid station",
                locator="grid infrastructure paragraph",
                as_of="2026-05-28",
            ),
            observation(
                sources[0],
                "operation_target",
                "H1 2028",
                boundary="SWE04 municipal target; not an actual commissioning event",
                locator="responsibility and next-steps paragraph",
                kind="target",
                as_of="2026-05-28",
            ),
            observation(
                sources[1],
                "operation_target",
                "autumn 2028",
                boundary="SWE04 grid-connection article forecast; conflicts with H1 2028 target",
                locator="grid completion paragraph",
                kind="target",
                as_of="2026-05-28",
            ),
            observation(
                "atnorth-swe04-20261103",
                "stale_operator_page_land",
                4,
                unit="ha",
                boundary=(
                    "operator FAQ text contradicted by current operator and municipal "
                    "50 ha evidence"
                ),
                locator="capacity-to-scale FAQ",
                as_of="2026-11-03",
            ),
        ]
    )
    record["observations_json"] = compact(observations)
    record["grid_capacity_mw"] = 200
    record["grid_capacity_basis"] = "ultimate_planned"
    record["capacity_scope"] = (
        "SWE04 campus aggregate excluded from sums; 200 MW is the contracted phase-one grid "
        "connection, 300 MW is unclassified planned project power, and 500 MW belongs to the "
        "wider Hamre industrial park"
    )
    record["status"] = "permitted"
    record["status_as_of"] = "2026-05-28"
    record["status_date_basis"] = (
        "Municipal page reports legally effective detailed plan, signed land sale and contracted "
        "phase-one grid connection; construction start is not yet evidenced"
    )
    record["grid_utility"] = "E.ON Energidistribution"
    record["conflicts_json"] = compact(
        {
            "commissioning_date": [
                {
                    "boundary": "SWE04 municipal project target",
                    "field": "commissioning_period",
                    "locator": "responsibility and next-steps paragraph",
                    "observed_at": RETRIEVED_AT,
                    "source_publication_date": "2026-05-28",
                    "sources": [sources[0]],
                    "value": "H1 2028",
                },
                {
                    "boundary": "SWE04 grid-connection article forecast",
                    "field": "commissioning_period",
                    "locator": "grid completion paragraph",
                    "observed_at": RETRIEVED_AT,
                    "source_publication_date": "2026-05-28",
                    "sources": [sources[1]],
                    "value": "autumn 2028",
                },
            ],
        }
    )
    record["quality_status"] = "needs_review"
    add_sources(record, sources)
    add_evidence(record, "capacity_scope", sources, "municipal boundary reconciliation")
    add_evidence(record, "grid_capacity_mw", sources, "phase-one connection agreement", unit="MW")
    add_evidence(record, "grid_capacity_basis", sources, "contracted future connection")
    add_evidence(
        record, "grid_utility", sources, "municipal responsibility and agreement statements"
    )
    add_evidence(record, "status", sources, "legally effective plan, signed sale and connection")
    add_evidence(record, "status_as_of", sources, "municipal pages updated 2026-05-28")
    add_evidence(record, "status_date_basis", sources, "municipal status statements")
    add_evidence(record, "conflicts_json", sources, "dated commissioning targets and stale FAQ")
    add_evidence(record, "observations_json", sources, "reviewed municipal field locators")
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    records = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines()]
    by_id = {record["record_id"]: record for record in records}
    if len(by_id) != len(records):
        raise ValueError("Duplicate project IDs in input shard")
    if FIN03 in by_id:
        by_id.pop(FIN03)
    for target in (DEN01, DEN02, SWE04):
        if target not in by_id:
            raise ValueError(f"Missing atNorth target {target}")
    by_id[DEN01] = enrich_den01(by_id[DEN01])
    by_id[DEN02] = enrich_den02(by_id[DEN02])
    by_id[SWE04] = enrich_swe04(by_id[SWE04])
    by_id[FIN03] = new_fin03()
    ordered = sorted(by_id.values(), key=lambda record: record["record_id"])
    args.output.write_text("".join(f"{compact(record)}\n" for record in ordered), encoding="utf-8")
    print("Added FIN03 and reconciled DEN01, DEN02 and SWE04")


if __name__ == "__main__":
    main()
