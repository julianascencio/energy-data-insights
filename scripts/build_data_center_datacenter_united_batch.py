"""Build the reviewed 14-facility Datacenter United current directory batch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.portfolios import (
    parse_datacenter_united_directory,
    parse_datacenter_united_site_page,
)

RETRIEVED_AT = "2026-11-06T06:20:00Z"
AS_OF = "2026-11-06"
ORG_NAME = "Datacenter United"
ORG_ID = stable_id("organization", ORG_NAME)
DIRECTORY_URL = "https://datacenterunited.com/en/our-datacenters/"
META = {
    "DC Antwerp 1": (
        "Antwerp",
        "our-datacenters/dc-antwerp",
        "dc-antwerp.html",
        ["ANTW1"],
    ),
    "DC Antwerp 2": (
        "Antwerp",
        "our-datacenters/dc-antwerp",
        "dc-antwerp.html",
        ["ANTW2"],
    ),
    "DC Antwerp 3": (
        "Antwerp",
        "our-datacenters/dc-flanders",
        "dc-flanders.html",
        ["DC Flanders"],
    ),
    "DC Burcht": ("Burcht", "our-datacenters/dc-burcht", "dc-burcht.html", []),
    "DC Mechelen": ("Mechelen", "our-datacenters/dc-mechelen", "dc-mechelen.html", []),
    "DC Evere 1": ("Evere", "our-datacenters/dc-evere", "dc-evere.html", []),
    "DC Evere 2": ("Evere", "our-datacenters/dc-evere", "dc-evere.html", []),
    "DC Brussels": ("Zaventem", "our-datacenters/dc-brussels", "dc-brussels.html", []),
    "DC Machelen": ("Machelen", "our-datacenters/dc-machelen", "dc-machelen.html", []),
    "DC Ghent": ("Ghent", "our-datacenters/dc-ghent", "dc-ghent.html", []),
    "DC Ghent 2": ("Ghent", "our-datacenters/dc-ghent", "dc-ghent.html", []),
    "DC Hasselt 1": ("Hasselt", "our-datacenters/dc-hasselt-1", "dc-hasselt-1.html", []),
    "DC Oostkamp": (
        "Oostkamp",
        "our-datacenters/dc-oostkamp-bruges",
        "dc-oostkamp-bruges.html",
        [],
    ),
    "DC Mouscron": ("Mouscron", "our-datacenters/dc-moeskroen", "dc-moeskroen.html", []),
}
SOURCE_SLUG = {
    "our-datacenters/dc-antwerp": "antwerp",
    "our-datacenters/dc-flanders": "flanders",
    "our-datacenters/dc-burcht": "burcht",
    "our-datacenters/dc-mechelen": "mechelen",
    "our-datacenters/dc-evere": "evere",
    "our-datacenters/dc-brussels": "brussels",
    "our-datacenters/dc-machelen": "machelen",
    "our-datacenters/dc-ghent": "ghent",
    "our-datacenters/dc-hasselt-1": "hasselt-1",
    "our-datacenters/dc-oostkamp-bruges": "oostkamp",
    "our-datacenters/dc-moeskroen": "mouscron",
}


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def load_directory(capture_dir: Path) -> list[dict[str, Any]]:
    rows = parse_datacenter_united_directory(
        (capture_dir / "directory.html").read_bytes(), source_url=DIRECTORY_URL
    )["candidates"]
    if [row["external_id"] for row in rows] != list(META):
        raise ValueError("Changed Datacenter United directory identity set")
    validations = {
        "antwerp": (
            "dc-antwerp.html",
            "https://datacenterunited.com/en/our-datacenters/dc-antwerp/",
        ),
        "flanders": (
            "dc-flanders.html",
            "https://datacenterunited.com/en/our-datacenters/dc-flanders/",
        ),
        "evere": (
            "dc-evere.html",
            "https://datacenterunited.com/en/our-datacenters/dc-evere/",
        ),
        "ghent": (
            "dc-ghent.html",
            "https://datacenterunited.com/en/our-datacenters/dc-ghent/",
        ),
        "mouscron": (
            "dc-moeskroen.html",
            "https://datacenterunited.com/en/our-datacenters/dc-moeskroen/",
        ),
    }
    for group, (filename, url) in validations.items():
        parse_datacenter_united_site_page(
            (capture_dir / filename).read_bytes(), source_url=url, expected_group=group
        )
    return rows


def build_record(candidate: dict[str, Any]) -> dict[str, object]:
    external_id = candidate["external_id"]
    locality, path, _filename, extra_aliases = META[external_id]
    source_slug = SOURCE_SLUG[path]
    directory_source = "datacenter-united-directory-current-20261106"
    page_source = f"datacenter-united-{source_slug}-current-20261106"
    url = f"https://datacenterunited.com/en/{path}/"
    status = "under_construction" if external_id in {"DC Ghent 2", "DC Mouscron"} else "operational"
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
    source_ids = [directory_source, page_source]
    field_sources = compact({field: source_ids for field in fields})
    evidence = compact(
        {
            field: {
                "confidence": "high",
                "locator": "current directory card and linked facility page",
                "source_publication_dates": {
                    directory_source: None,
                    page_source: None,
                },
            }
            for field in fields
        }
    )
    boundary = (
        "Exact facility identity within a grouped operator location; no capacity scalar "
        "or sibling allocation is inferred."
        if external_id.startswith(("DC Antwerp", "DC Evere"))
        else "Exact facility identity; no boundary-qualified capacity scalar is reported."
    )
    observations = [
        {
            "as_of": AS_OF,
            "boundary": boundary,
            "field": "current_directory_identity",
            "kind": "reported",
            "locator": candidate["locator"],
            "source_id": directory_source,
            "unit": None,
            "value": external_id,
        }
    ]
    if external_id == "DC Antwerp 3":
        observations.append(
            {
                "as_of": AS_OF,
                "boundary": "Directory identity DC Antwerp 3 links to the exact DC Flanders page.",
                "field": "official_alias",
                "kind": "reported",
                "locator": "current directory card / linked page",
                "source_id": page_source,
                "unit": None,
                "value": "DC Flanders",
            }
        )
    if external_id == "DC Ghent 2":
        observations.append(
            {
                "as_of": AS_OF,
                "boundary": (
                    "Exact future facility at the Ghent location; no capacity or "
                    "commissioning date inferred."
                ),
                "field": "construction_status",
                "kind": "reported",
                "locator": "current directory card and Ghent page / Coming: Ghent 2",
                "source_id": page_source,
                "unit": None,
                "value": "under construction / coming",
            }
        )
    if external_id == "DC Mouscron":
        observations.append(
            {
                "as_of": AS_OF,
                "boundary": (
                    "Exact facility page says currently under development; no target date "
                    "is treated as commissioning."
                ),
                "field": "construction_status",
                "kind": "reported",
                "locator": "current DC Mouscron page / development narrative",
                "source_id": page_source,
                "unit": None,
                "value": "currently under development",
            }
        )
    aliases = [external_id, *extra_aliases]
    facility_id = stable_id("facility", ORG_NAME, external_id)
    return {
        "aggregation_role": "independent",
        "aliases": aliases,
        "capacity_scope": (
            f"{external_id} exact facility only; IT, grid and total facility-demand "
            "capacity remain null."
        ),
        "country_code": "BEL",
        "created_at": RETRIEVED_AT,
        "entities_json": compact(
            [
                {"name": ORG_NAME, "organization_id": ORG_ID, "role": "owner"},
                {"name": ORG_NAME, "organization_id": ORG_ID, "role": "operator"},
            ]
        ),
        "entity_type": "projects",
        "evidence_json": evidence,
        "external_ids_json": compact({"datacenter_united": external_id}),
        "facility_id": facility_id,
        "facility_type": "colocation",
        "field_sources_json": field_sources,
        "last_verified_at": RETRIEVED_AT,
        "locality": locality,
        "name": f"Datacenter United {external_id}",
        "notes": (
            "Operator availability, Tier, ISO, sustainability, connectivity and security "
            "claims remain source context; no issuer-registry certification, deployment, "
            "address, coordinate or access detail is normalized."
        ),
        "observations_json": compact(observations),
        "official_url": url,
        "operator_names": [ORG_NAME],
        "owner_names": [ORG_NAME],
        "quality_status": "source_backed",
        "record_id": stable_id("projects", ORG_NAME, external_id),
        "record_scope": "facility",
        "source_urls": [DIRECTORY_URL, url],
        "sources": source_ids,
        "status": status,
        "status_as_of": AS_OF,
        "status_date_basis": (
            "Current directory construction label and exact facility-page development narrative"
            if external_id in {"DC Ghent 2", "DC Mouscron"}
            else "Current public operator directory and active facility page"
        ),
        "updated_at": RETRIEVED_AT,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = [build_record(candidate) for candidate in load_directory(args.capture_dir)]
    args.output.write_text("".join(f"{compact(row)}\n" for row in rows), encoding="utf-8")
    print(f"Wrote {len(rows)} reviewed Datacenter United project records to {args.output}")


if __name__ == "__main__":
    main()
