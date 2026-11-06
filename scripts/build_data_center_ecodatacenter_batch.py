"""Build the reviewed current EcoDataCenter three-site Swedish portfolio."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.portfolios import (
    parse_ecodatacenter_portfolio,
    parse_ecodatacenter_site_page,
    parse_ecodatacenter_smedjebacken_announcement,
)

RETRIEVED_AT = "2026-11-06T02:30:00Z"
AS_OF = "2026-11-06"
ORG_NAME = "EcoDataCenter"
ORG_ID = stable_id("organization", ORG_NAME)
DIRECTORY_SOURCE = "ecodatacenter-directory-current-20261106"
DIRECTORY_URL = "https://ecodatacenter.tech/data-center"
SOURCES = {
    "ecodatacenter-1": (
        "ecodatacenter-falun-current-20261106",
        "https://ecodatacenter.tech/data-center/sweden-falun",
    ),
    "ecodatacenter-2": (
        "ecodatacenter-borlange-current-20261106",
        "https://ecodatacenter.tech/data-center/ecodatacenter2",
    ),
    "ecodatacenter-3": (
        "ecodatacenter-smedjebacken-announcement-20260825",
        "https://ecodatacenter.tech/press/"
        "ecodatacenter-to-establish-third-datacenter-campus-in-sweden-3462219",
    ),
}
META = {
    "ecodatacenter-1": {
        "name": "EcoDataCenter 1 - Falun",
        "locality": "Falun",
        "scope": "facility",
        "status": "operational",
        "status_basis": "current operator directory and exact current facility page",
    },
    "ecodatacenter-2": {
        "name": "EcoDataCenter 2 - Borlänge",
        "locality": "Borlänge",
        "scope": "campus",
        "status": "under_construction",
        "status_basis": "current operator directory and September 2025 construction statement",
    },
    "ecodatacenter-3": {
        "name": "EcoDataCenter 3 - Smedjebacken",
        "locality": "Smedjebacken",
        "scope": "campus",
        "status": "announced",
        "status_basis": "2026-08-25 land-purchase announcement; permits remain pending",
    },
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
    locator: str,
    publication_date: str | None = None,
) -> dict[str, object]:
    row: dict[str, object] = {
        "as_of": AS_OF,
        "boundary": boundary,
        "field": field,
        "kind": "reported",
        "locator": locator,
        "source_id": source_id,
        "unit": unit,
        "value": value,
    }
    if publication_date is not None:
        row["publication_date"] = publication_date
    return row


def load_inputs(capture_dir: Path) -> dict[str, dict[str, Any]]:
    portfolio = parse_ecodatacenter_portfolio(
        (capture_dir / "directory.html").read_bytes(), source_url=DIRECTORY_URL
    )
    directory = {row["external_id"]: row for row in portfolio["candidates"]}
    if set(directory) != {"ecodatacenter-1", "ecodatacenter-2"}:
        raise ValueError("Changed EcoDataCenter current directory")
    falun = parse_ecodatacenter_site_page(
        (capture_dir / "falun.html").read_bytes(),
        source_url=SOURCES["ecodatacenter-1"][1],
        expected_site="EcoDataCenter 1",
    )["candidate"]
    borlange = parse_ecodatacenter_site_page(
        (capture_dir / "borlange.html").read_bytes(),
        source_url=SOURCES["ecodatacenter-2"][1],
        expected_site="EcoDataCenter 2",
    )["candidate"]
    smedjebacken = parse_ecodatacenter_smedjebacken_announcement(
        (capture_dir / "smedjebacken.html").read_bytes(),
        source_url=SOURCES["ecodatacenter-3"][1],
    )["candidate"]
    return {
        "ecodatacenter-1": falun,
        "ecodatacenter-2": borlange,
        "ecodatacenter-3": smedjebacken,
    }


def observations(slug: str, candidate: dict[str, Any]) -> list[dict[str, object]]:
    source_id = SOURCES[slug][0]
    locator = candidate["locator"]
    if slug == "ecodatacenter-1":
        return [
            observation(
                field="reported_unclassified_available_power",
                value=candidate["reported_power_mw"],
                unit="MW",
                source_id=source_id,
                boundary=(
                    "Falun available power; source does not identify IT, grid or total "
                    "facility demand"
                ),
                locator=locator,
            ),
            observation(
                field="reported_pue",
                value=candidate["reported_pue"],
                unit="ratio",
                source_id=source_id,
                boundary=(
                    "Falun operator claim; measurement period is unstated and ISO wording "
                    "is not an issuer-registry certification"
                ),
                locator=locator,
            ),
            observation(
                field="reported_renewable_electricity_share",
                value=candidate["renewable_electricity_pct"],
                unit="percent",
                source_id=source_id,
                boundary=(
                    "Falun on-site electricity sourcing statement; not a grid-emissions factor"
                ),
                locator=locator,
            ),
            observation(
                field="reported_renewable_electricity_mix",
                value={
                    "hydropower_pct": candidate["hydropower_pct"],
                    "wind_pct": candidate["wind_power_pct"],
                },
                unit="percent",
                source_id=source_id,
                boundary="Falun operator-reported sourcing mix",
                locator=locator,
            ),
        ]
    if slug == "ecodatacenter-2":
        return [
            observation(
                field="reported_unclassified_available_power_upper_bound",
                value=candidate["reported_power_upper_bound_mw"],
                unit="MW",
                source_id=source_id,
                boundary=(
                    "Borlänge up-to site claim; not identified as IT, grid or total facility demand"
                ),
                locator=locator,
            ),
            observation(
                field="reported_land_area",
                value=candidate["reported_land_area_m2"],
                unit="m2",
                source_id=source_id,
                boundary="Borlänge plot/available-land statement; not normalized as data-hall area",
                locator=locator,
            ),
            observation(
                field="construction_start",
                value=candidate["construction_start"],
                unit=None,
                source_id=source_id,
                boundary="Borlänge construction began September 2025",
                locator=locator,
            ),
            observation(
                field="first_phase_completion_target",
                value=candidate["first_phase_target"],
                unit=None,
                source_id=source_id,
                boundary="Borlänge operator target, not completed commissioning",
                locator=locator,
            ),
            observation(
                field="environmental_permit_status",
                value=candidate["environmental_permits"],
                unit=None,
                source_id=source_id,
                boundary="Borlänge operator statement; permit identifiers not published",
                locator=locator,
            ),
            observation(
                field="reported_renewable_electricity_share",
                value=candidate["renewable_electricity_pct"],
                unit="percent",
                source_id=source_id,
                boundary="Borlänge on-site electricity sourcing statement",
                locator=locator,
            ),
        ]
    return [
        observation(
            field="land_purchase_area",
            value=candidate["reported_land_area_hectares"],
            unit="hectares",
            source_id=source_id,
            boundary="Smedjebacken municipal land-purchase agreement",
            locator=locator,
            publication_date=candidate["publication_date"],
        ),
        observation(
            field="reported_unclassified_immediate_power",
            value=candidate["reported_unclassified_power_mw"],
            unit="MW",
            source_id=source_id,
            boundary=(
                "Announcement wording does not identify IT, grid or total facility demand; "
                "permits remain pending"
            ),
            locator=locator,
            publication_date=candidate["publication_date"],
        ),
        observation(
            field="construction_start_target",
            value=candidate["construction_target"],
            unit=None,
            source_id=source_id,
            boundary="Expected only after building and environmental permits are finalized",
            locator=locator,
            publication_date=candidate["publication_date"],
        ),
    ]


def build_record(slug: str, candidate: dict[str, Any]) -> dict[str, object]:
    meta = META[slug]
    source_id, url = SOURCES[slug]
    source_ids = [source_id] if slug == "ecodatacenter-3" else [DIRECTORY_SOURCE, source_id]
    source_urls = [url] if slug == "ecodatacenter-3" else [DIRECTORY_URL, url]
    aggregate = meta["scope"] == "campus"
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
    if aggregate:
        fields.append("campus_id")
    publication_dates = {
        sid: ("2026-08-25" if sid.endswith("20260825") else None) for sid in source_ids
    }
    evidence = {
        field: {
            "confidence": "high",
            "locator": "current exact operator page"
            if slug != "ecodatacenter-3"
            else "dated operator announcement",
            "source_publication_dates": publication_dates,
        }
        for field in fields
    }
    row: dict[str, object] = {
        "aggregation_role": "aggregate" if aggregate else "independent",
        "aliases": [meta["locality"]],
        "capacity_scope": (
            f"{meta['locality']} campus aggregate; always excluded from capacity totals; "
            "all MW statements remain unclassified"
            if aggregate
            else "Falun independently identified facility; available-power claim remains "
            "unclassified and excluded from normalized capacity fields"
        ),
        "country_code": "SWE",
        "created_at": RETRIEVED_AT,
        "entities_json": compact(
            [
                {"name": ORG_NAME, "organization_id": ORG_ID, "role": "owner"},
                {"name": ORG_NAME, "organization_id": ORG_ID, "role": "operator"},
            ]
        ),
        "entity_type": "projects",
        "evidence_json": compact(evidence),
        "external_ids_json": compact({"ecodatacenter": slug}),
        "facility_id": stable_id("facility", ORG_NAME, slug),
        "facility_type": "colocation",
        "field_sources_json": compact({field: source_ids for field in fields}),
        "last_verified_at": RETRIEVED_AT,
        "locality": meta["locality"],
        "name": meta["name"],
        "observations_json": compact(observations(slug, candidate)),
        "official_url": url,
        "operator_names": [ORG_NAME],
        "owner_names": [ORG_NAME],
        "quality_status": "needs_review",
        "record_id": stable_id("projects", ORG_NAME, slug),
        "record_scope": meta["scope"],
        "source_urls": sorted(source_urls),
        "sources": source_ids,
        "status": meta["status"],
        "status_as_of": AS_OF,
        "status_date_basis": meta["status_basis"],
        "updated_at": RETRIEVED_AT,
    }
    if aggregate:
        row["campus_id"] = stable_id("campus", ORG_NAME, slug)
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    candidates = load_inputs(args.capture_dir)
    rows = [build_record(slug, candidates[slug]) for slug in META]
    args.output.write_text("".join(f"{compact(row)}\n" for row in rows), encoding="utf-8")
    print(f"Wrote {len(rows)} reviewed EcoDataCenter project records to {args.output}")


if __name__ == "__main__":
    main()
