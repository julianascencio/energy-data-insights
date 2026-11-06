"""Build six non-overlapping, cross-language-stable JRC 2024 facilities."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id

RETRIEVED_AT = "2026-11-06T12:19:59Z"
AS_OF = "2026-11-06"
SOURCE_ID = "jrc-data-centre-code-of-conduct-2024-new-participants-20261106"
SOURCE_URL = (
    "https://e3p.jrc.ec.europa.eu/es/groups/data-centres-code-conduct/"
    "participants?order=field_adhesion_date&page=3&partner_search=&sort=asc"
)

ROWS = [
    ("Infomaniak Group SA", "CHE", "D3 Geneva", "Geneva"),
    ("Nation Data Center", "FRA", "Roazhon", None),
    (
        "General Secretariat of Information Systems and Digital Governance "
        "Hellenic Ministry of Digital Governance",
        "GRC",
        "G-Cloud Moschato",
        "Moschato",
    ),
    ("Liguria Digitale S.p.a", "ITA", "DCWTC Genova", "Genova"),
    ("Colt Data Services France", "FRA", "Les Ulis", "Les Ulis"),
    ("EYE IT Srl SB", "ITA", "Castel Sanpietro Terme (BO)", None),
]


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def build_record(
    *, participant: str, country_code: str, label: str, locality: str | None
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
        "location_accuracy",
        "name",
        "observations_json",
        "official_url",
        "record_scope",
        "status",
        "status_as_of",
        "status_date_basis",
    ]
    if locality is not None:
        fields.append("locality")
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
                "European Commission JRC participant-registry identity and 2024 adhesion "
                "year only; not evidence of current lifecycle, ownership, operation, "
                "capacity or certification. The row was accepted only where participant, "
                "count, facility label and year agreed across reviewed Spanish, Romanian, "
                "Gaelic and German official-language indexes. Digital Realty Spain and "
                "Sweden are excluded because their partition was completed previously."
            ),
            "field": "eu_code_of_conduct_participant",
            "kind": "reported",
            "locator": locator,
            "source_id": SOURCE_ID,
            "unit": None,
            "value": {"adhesion_year": 2024, "participant": participant},
        }
    ]
    record: dict[str, object] = {
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
        "location_accuracy": (
            "city only from the exact facility label; no company address or coordinates normalized"
            if locality is not None
            else "country only; the registry facility label is not promoted to a locality"
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
            "copies; the 2024 adhesion year is not a lifecycle date."
        ),
        "updated_at": RETRIEVED_AT,
    }
    if locality is not None:
        record["locality"] = locality
    return record


def build() -> list[dict[str, object]]:
    records = [
        build_record(
            participant=participant,
            country_code=country_code,
            label=label,
            locality=locality,
        )
        for participant, country_code, label, locality in ROWS
    ]
    if len(records) != 6 or len({row["record_id"] for row in records}) != 6:
        raise ValueError("Expected six unique JRC 2024 new-participant records")
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
    print("Wrote six reviewed cross-language-stable JRC 2024 facility records")


if __name__ == "__main__":
    main()
