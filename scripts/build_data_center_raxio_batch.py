"""Build reviewed Raxio facility records from seven official page captures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.portfolios import (
    parse_raxio_facility_page,
)

RETRIEVED_AT = "2026-11-03T07:22:54Z"
AS_OF = "2026-11-03"
PORTFOLIO_SOURCE = "raxio-portfolio-20261103"
ORGANIZATION_ID = stable_id("organization", "Raxio Group")
FACILITIES = (
    ("AO1", "Angola", "angola", "AGO", "Luanda", "commissioned October 2025"),
    ("CIV1", "Côte d\u2019Ivoire", "cote-divoire", "CIV", "Grand Bassam", "opened 2024"),
    (
        "DRC1",
        "Democratic Republic of the Congo",
        "dr-congo",
        "COD",
        "Kinshasa",
        "launched 2024",
    ),
    ("ET1", "Ethiopia", "ethiopia", "ETH", "Addis Ababa", "opened 2023"),
    ("MZ1", "Mozambique", "mozambique", "MOZ", "Matola", "opened 2024-05-28"),
    (
        "TZ1",
        "Tanzania",
        "tanzania",
        "TZA",
        "Dar es Salaam",
        "under development; no construction milestone",
    ),
    ("UG1", "Uganda", "uganda", "UGA", "Namanve", "opened 2021"),
)


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def build_record(capture_dir: Path, item: tuple[str, ...]) -> dict[str, object]:
    code, country, slug, country_code, locality, lifecycle_marker = item
    url = f"https://www.raxiogroup.com/data-centres/{slug}/"
    source_id = f"raxio-{code.lower()}-current-20261103"
    candidate = parse_raxio_facility_page(
        (capture_dir / f"raxio-{slug}.html").read_bytes(),
        source_url=url,
        expected_code=code,
    )["candidate"]
    sources = [PORTFOLIO_SOURCE, source_id]
    source_urls = ["https://www.raxiogroup.com/data-centres/", url]
    publication_dates = {PORTFOLIO_SOURCE: None, source_id: None}
    if code == "MZ1":
        sources.append("raxio-mz1-launch-20240528")
        source_urls.append(
            "https://www.raxiogroup.com/raxio-strengthens-backbone-of-africas-"
            "digital-economy-with-launch-of-raxio-mozambique/"
        )
        publication_dates["raxio-mz1-launch-20240528"] = "2024-05-28"

    fields = [
        "aggregation_role",
        "capacity_scope",
        "country_code",
        "data_hall_area_m2",
        "entities_json",
        "external_ids_json",
        "facility_id",
        "facility_type",
        "it_capacity_basis",
        "it_capacity_mw",
        "locality",
        "name",
        "observations_json",
        "official_url",
        "operator_names",
        "record_scope",
        "status",
        "status_as_of",
        "status_date_basis",
    ]
    if code == "MZ1":
        fields.append("commissioning_date")

    locator = candidate["locator"]
    evidence = {
        field: {
            "confidence": "high",
            "locator": locator,
            "source_publication_dates": publication_dates,
        }
        for field in fields
    }
    evidence["it_capacity_mw"]["unit"] = "MW"
    evidence["data_hall_area_m2"]["unit"] = "m2"
    observations = [
        {
            "as_of": AS_OF,
            "boundary": f"{code} full-design capability; not measured installed load",
            "field": "rack_capacity_design",
            "kind": "reported",
            "locator": "current facility page specification cards",
            "source_id": source_id,
            "unit": "racks",
            "value": candidate["rack_capacity"],
        },
        {
            "as_of": AS_OF,
            "boundary": f"{code} utility connection voltage; not grid capacity",
            "field": "connection_voltage",
            "kind": "reported",
            "locator": "current facility page specification cards",
            "source_id": source_id,
            "unit": "kV",
            "value": candidate["connection_voltage_kv"],
        },
        {
            "as_of": AS_OF,
            "boundary": f"{code} cooling provision; not IT or facility electrical capacity",
            "field": "cooling_provision",
            "kind": "reported",
            "locator": "current facility page specification cards",
            "source_id": source_id,
            "unit": "MW",
            "value": candidate["cooling_provision_mw"],
        },
        {
            "as_of": AS_OF,
            "boundary": f"{code} UPS design autonomy; load and battery energy undisclosed",
            "field": "ups_autonomy",
            "kind": "reported",
            "locator": "current facility page specification cards",
            "source_id": source_id,
            "unit": "minutes",
            "value": 7,
        },
        {
            "as_of": AS_OF,
            "boundary": f"{code} lifecycle marker; source precision retained verbatim",
            "field": "lifecycle_marker",
            "kind": "reported",
            "locator": "current facility page status text",
            "source_id": source_id,
            "unit": None,
            "value": lifecycle_marker,
        },
    ]
    if candidate["pue"] is not None:
        observations.append(
            {
                "as_of": AS_OF,
                "boundary": (
                    f"{code} operator-disclosed PUE boundary and measurement period unspecified"
                ),
                "field": "pue",
                "kind": "unspecified",
                "locator": "current facility page specification cards",
                "measurement_period": None,
                "source_id": source_id,
                "unit": "ratio",
                "value": candidate["pue"],
            }
        )
    status = "announced" if code == "TZ1" else "operational"
    row: dict[str, object] = {
        "aggregation_role": "independent",
        "capacity_scope": (
            f"{code} facility only; IT capacity is operator design maximum, not measured demand"
        ),
        "country_code": country_code,
        "created_at": RETRIEVED_AT,
        "data_hall_area_m2": candidate["data_hall_area_m2"],
        "entities_json": compact(
            [
                {"name": "Raxio Group", "organization_id": ORGANIZATION_ID, "role": "owner"},
                {
                    "name": "Raxio Group",
                    "organization_id": ORGANIZATION_ID,
                    "role": "operator",
                },
            ]
        ),
        "entity_type": "projects",
        "evidence_json": compact(evidence),
        "external_ids_json": compact({"raxio": code}),
        "facility_id": stable_id("facility", "Raxio Group", code),
        "facility_type": "colocation",
        "field_sources_json": compact({field: sources for field in fields}),
        "it_capacity_basis": "design_maximum",
        "it_capacity_mw": candidate["it_design_mw"],
        "last_verified_at": RETRIEVED_AT,
        "locality": locality,
        "name": f"Raxio {code} {country}",
        "observations_json": compact(observations),
        "official_url": url,
        "operator_names": ["Raxio Group"],
        "quality_status": "source_backed",
        "record_id": stable_id("projects", "Raxio Group", code),
        "record_scope": "facility",
        "source_urls": source_urls,
        "sources": sources,
        "status": status,
        "status_as_of": AS_OF,
        "status_date_basis": (
            "retrieval of current operator page; lifecycle marker retained as observation"
        ),
        "updated_at": RETRIEVED_AT,
    }
    if code == "MZ1":
        row["commissioning_date"] = "2024-05-28"
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = [build_record(args.capture_dir, item) for item in FACILITIES]
    args.output.write_text("".join(f"{compact(row)}\n" for row in rows), encoding="utf-8")
    print(f"Wrote {len(rows)} reviewed Raxio facility records to {args.output}")


if __name__ == "__main__":
    main()
