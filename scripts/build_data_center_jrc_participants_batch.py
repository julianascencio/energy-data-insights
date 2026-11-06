"""Build the bounded 2024 JRC Digital Realty participant-facility batch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id

RETRIEVED_AT = "2026-11-06T08:15:44Z"
AS_OF = "2026-11-06"
SOURCE_ID = "jrc-data-centre-code-of-conduct-participants-20261106"
SOURCE_URL = (
    "https://e3p.jrc.ec.europa.eu/en/groups/data-centres-code-conduct/"
    "participants?order=field_adhesion_date&page=3&partner_search=&sort=asc"
)
PARTITIONS = {
    "Digital Realty Spain": ("ESP", [f"ESP{i}" for i in range(1, 5)]),
    "Digital Realty Sweden": ("SWE", [f"STO{i}" for i in range(1, 7)]),
}


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def build_record(participant: str, country_code: str, facility_code: str) -> dict[str, object]:
    name = f"{participant} {facility_code}"
    fields = [
        "aggregation_role",
        "aliases",
        "capacity_scope",
        "country_code",
        "external_ids_json",
        "facility_id",
        "facility_type",
        "name",
        "observations_json",
        "official_url",
        "record_scope",
        "status",
        "status_as_of",
        "status_date_basis",
    ]
    locator = f"Participants table / {participant} / {name}"
    field_sources = {field: [SOURCE_ID] for field in fields}
    evidence = {
        field: {
            "confidence": "high",
            "locator": locator,
            "source_publication_dates": {SOURCE_ID: None},
        }
        for field in fields
    }
    observations = [
        {
            "as_of": AS_OF,
            "boundary": (
                "European Commission JRC participant-registry identity and adhesion year only; "
                "not evidence of current lifecycle, ownership, operation, capacity or "
                "certification."
            ),
            "field": "eu_code_of_conduct_participant",
            "kind": "reported",
            "locator": locator,
            "source_id": SOURCE_ID,
            "unit": None,
            "value": {"adhesion_year": 2024, "participant": participant},
        }
    ]
    return {
        "aggregation_role": "unresolved",
        "aliases": [facility_code],
        "capacity_scope": (
            f"{facility_code} is an exact JRC participant-registry data-centre identity. "
            "Its physical aggregation and all IT, grid and facility-demand boundaries are "
            "unresolved, so it is excluded from capacity totals under every filter."
        ),
        "country_code": country_code,
        "created_at": RETRIEVED_AT,
        "entity_type": "projects",
        "evidence_json": compact(evidence),
        "external_ids_json": compact({"eu_jrc_code_of_conduct": facility_code}),
        "facility_id": stable_id("facility", participant, facility_code),
        "facility_type": "unknown",
        "field_sources_json": compact(field_sources),
        "last_verified_at": RETRIEVED_AT,
        "name": name,
        "observations_json": compact(observations),
        "official_url": SOURCE_URL,
        "quality_status": "source_backed",
        "record_id": stable_id("projects", participant, facility_code),
        "record_scope": "facility",
        "source_urls": [SOURCE_URL],
        "sources": [SOURCE_ID],
        "status": "unknown",
        "status_as_of": AS_OF,
        "status_date_basis": (
            "Current JRC participant registry retrieved through an indexed public copy; "
            "the registry listing does not establish facility lifecycle."
        ),
        "updated_at": RETRIEVED_AT,
    }


def build() -> list[dict[str, object]]:
    rows = [
        build_record(participant, country_code, facility_code)
        for participant, (country_code, facility_codes) in PARTITIONS.items()
        for facility_code in facility_codes
    ]
    if len(rows) != 10 or len({row["record_id"] for row in rows}) != 10:
        raise ValueError("Expected 10 unique JRC participant-facility records")
    return sorted(rows, key=lambda row: str(row["record_id"]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = build()
    args.output.write_text(
        "".join(compact(row) + "\n" for row in rows), encoding="utf-8", newline="\n"
    )
    print("Wrote 10 reviewed JRC participant-facility records")


if __name__ == "__main__":
    main()
