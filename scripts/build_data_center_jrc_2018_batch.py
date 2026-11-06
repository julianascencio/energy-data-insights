"""Build the bounded JRC DxC Technology and Digital Reality 2018 batch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id

RETRIEVED_AT = "2026-11-06T09:58:36Z"
AS_OF = "2026-11-06"
SOURCE_ID = "jrc-data-centre-code-of-conduct-2018-participants-20261106"
SOURCE_URL = (
    "https://e3p.jrc.ec.europa.eu/fr/groups/data-centres-code-conduct/"
    "participants?order=field_adhesion_date&page=2&partner_search=&sort=asc"
)

DXC_LABELS = [
    "Aylesford",
    "Maidstone",
    "Royal Tunbridge Wells",
    "Northern Data Centre",
    "Sevenoaks Data Centre",
    "Doxfrod Park",
    "Mitcheldean",
    "Swindon",
    "Winyard",
    "Watford",
    "Norwich",
]
DIGITAL_REALITY = [
    ("DEU", "FRA11", "Frankfurt", "Germany: FRA11, Frankfurt"),
    ("NLD", "AMS17", "Amsterdam", "The Netherlands: AMS17, Amsterdam"),
    ("NLD", "AMS18", "Amsterdam", "The Netherlands: AMS18, Amsterdam"),
    ("GBR", "LHR17", "London", "United Kingdom: LHR17, London"),
    ("GBR", "LHR18", "London", "United Kingdom: LHR18, London"),
    ("GBR", "LHR19", "London", "United Kingdom: LHR19, London"),
    ("GBR", "LHR20", "London", "United Kingdom: LHR20, London"),
    ("GBR", "LHR21", "London", "United Kingdom: LHR21, London"),
]


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def build_record(
    *, participant: str, country_code: str, label: str, code: str, locality: str | None
) -> dict[str, object]:
    name = f"{participant} {code}" if participant == "Digital Reality" else f"{participant} {label}"
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
                "European Commission JRC participant-registry identity and adhesion year "
                "only; not evidence of current lifecycle, ownership, operation, capacity "
                "or certification."
            ),
            "field": "eu_code_of_conduct_participant",
            "kind": "reported",
            "locator": locator,
            "source_id": SOURCE_ID,
            "unit": None,
            "value": {"adhesion_year": 2018, "participant": participant},
        }
    ]
    if participant == "Digital Reality":
        observations.append(
            {
                "as_of": AS_OF,
                "boundary": (
                    "Participant spelling retained exactly as printed by the JRC registry; "
                    "it is not silently corrected or promoted to an owner/operator identity."
                ),
                "field": "registry_participant_spelling",
                "kind": "reported",
                "locator": locator,
                "source_id": SOURCE_ID,
                "unit": None,
                "value": "Digital Reality",
            }
        )
    aliases = [code] if code == label else [code, label]
    record: dict[str, object] = {
        "aggregation_role": "unresolved",
        "aliases": aliases,
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
            "city only from the JRC participant registry; no address or coordinates normalized"
            if locality is not None
            else "country only; the registry facility label is not promoted to a locality"
        ),
        "name": name,
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
            "copies; the 2018 adhesion year is not a lifecycle date."
        ),
        "updated_at": RETRIEVED_AT,
    }
    if locality is not None:
        record["locality"] = locality
    return record


def build() -> list[dict[str, object]]:
    rows = [
        build_record(
            participant="DxC Technology",
            country_code="GBR",
            label=label,
            code=label,
            locality=None,
        )
        for label in DXC_LABELS
    ]
    rows.extend(
        build_record(
            participant="Digital Reality",
            country_code=country_code,
            label=label,
            code=code,
            locality=locality,
        )
        for country_code, code, locality, label in DIGITAL_REALITY
    )
    if len(rows) != 19 or len({row["record_id"] for row in rows}) != 19:
        raise ValueError("Expected 19 unique JRC 2018 participant-facility records")
    return sorted(rows, key=lambda row: str(row["record_id"]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = build()
    args.output.write_text(
        "".join(compact(row) + "\n" for row in rows), encoding="utf-8", newline="\n"
    )
    print("Wrote 19 reviewed JRC 2018 participant-facility records")


if __name__ == "__main__":
    main()
