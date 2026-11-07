"""Build the complete ten-identity JRC 2022 participant cohort."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id

RETRIEVED_AT = "2026-11-07T08:07:00Z"
AS_OF = "2026-11-07"
SOURCE_ID = "jrc-data-centre-code-of-conduct-2022-participants-20261107"
SOURCE_URL = (
    "https://e3p.jrc.ec.europa.eu/ga/groups/data-centres-code-conduct/"
    "participants?order=field_adhesion_date&page=0&partner_search=&sort=desc"
)

ROWS = [
    ("KDDI France", "FRA", "paris", "Paris"),
    ("Nantes Université", "FRA", "Nantes", "Nantes"),
    ("LCL Belgium NV", "BEL", "LCL Diegem (Belgium) 2", "Diegem"),
    ("LCL Belgium NV", "BEL", "LCL Antwerpen (Belgium) 3", "Antwerpen"),
    ("LCL Belgium NV", "BEL", "LCL Aalst (Belgium)", "Aalst"),
    ("Interxion Denmark", "DNK", "Ballerup", "Ballerup"),
    ("Qarnot computing", "FRA", "Montrouge", "Montrouge"),
    ("ATOS Netherlands B.V.", "NLD", "Eindhoven The Hurk", "Eindhoven"),
    ("Ikoula NET", "FRA", "Reims", "Reims"),
    ("Ikoula NET", "FRA", "Eppes", "Eppes"),
]


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def build_record(
    *, participant: str, country_code: str, label: str, locality: str
) -> dict[str, object]:
    locator = f"Participants table / {participant} / {label}"
    fields = [
        "aggregation_role",
        "aliases",
        "capacity_scope",
        "country_code",
        "external_ids_json",
        "facility_id",
        "facility_type",
        "locality",
        "location_accuracy",
        "name",
        "observations_json",
        "official_url",
        "record_scope",
        "status",
        "status_as_of",
        "status_date_basis",
    ]
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
                "European Commission JRC participant-registry identity and 2022 adhesion "
                "year only; not evidence of current lifecycle, ownership, operation, "
                "capacity, deployment, commissioning or certification. Participant, "
                "displayed count, facility labels and year agreed across reviewed "
                "official-language indexes. Exact source case is preserved."
            ),
            "field": "eu_code_of_conduct_participant",
            "kind": "reported",
            "locator": locator,
            "source_id": SOURCE_ID,
            "unit": None,
            "value": {"adhesion_year": 2022, "participant": participant},
        }
    ]
    return {
        "aggregation_role": "unresolved",
        "aliases": [label],
        "capacity_scope": (
            f"{label} is an exact JRC participant-registry data-centre identity. Its "
            "physical aggregation and all IT, grid and facility-demand boundaries are "
            "unresolved, so it is excluded from capacity totals under every filter."
        ),
        "country_code": country_code,
        "created_at": RETRIEVED_AT,
        "entity_type": "projects",
        "evidence_json": compact(evidence),
        "external_ids_json": compact({"eu_jrc_code_of_conduct": f"{participant}::{label}"}),
        "facility_id": stable_id("facility", participant, label),
        "facility_type": "unknown",
        "field_sources_json": compact(field_sources),
        "last_verified_at": RETRIEVED_AT,
        "locality": locality,
        "location_accuracy": (
            "city only from the exact facility label; company address and coordinates "
            "are not normalized"
        ),
        "name": f"{participant} {label}",
        "observations_json": compact(observations),
        "official_url": SOURCE_URL,
        "quality_status": "source_backed",
        "record_id": stable_id("projects", participant, label),
        "record_scope": "facility",
        "source_urls": [SOURCE_URL],
        "sources": [SOURCE_ID],
        "status": "unknown",
        "status_as_of": AS_OF,
        "status_date_basis": (
            "Current JRC participant registry retrieved through indexed official-language "
            "copies; the 2022 adhesion year is not a lifecycle date."
        ),
        "updated_at": RETRIEVED_AT,
    }


def build() -> list[dict[str, object]]:
    records = [
        build_record(participant=p, country_code=c, label=label, locality=loc)
        for p, c, label, loc in ROWS
    ]
    if len(records) != 10 or len({row["record_id"] for row in records}) != 10:
        raise ValueError("Expected ten unique JRC 2022 participant-facility records")
    return sorted(records, key=lambda row: str(row["record_id"]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.write_text(
        "".join(compact(row) + "\n" for row in build()),
        encoding="utf-8",
        newline="\n",
    )
    print("Wrote ten reviewed JRC 2022 participant-facility records")


if __name__ == "__main__":
    main()
