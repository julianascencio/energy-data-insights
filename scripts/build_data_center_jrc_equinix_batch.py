"""Build the bounded JRC Equinix EMEA participant-facility batch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id

RETRIEVED_AT = "2026-11-06T09:25:46Z"
AS_OF = "2026-11-06"
SOURCE_ID = "jrc-data-centre-code-of-conduct-equinix-20261106"
SOURCE_URL = (
    "https://e3p.jrc.ec.europa.eu/en/groups/data-centres-code-conduct/"
    "participants?order=field_adhesion_date&page=2&partner_search=&sort=desc"
)
PARTICIPANT = "Equinix, EMEA (Corporate Level)"
FACILITIES = [
    ("BGR", "SO1", "Sofia", "Bulgaria: SO1, Sofia"),
    *(("FRA", f"PA{i}", "Paris", f"France: PA{i}, Paris") for i in range(3, 8)),
    ("DEU", "FR4", "Frankfurt", "Germany: FR4, Frankfurt"),
    ("DEU", "FR7", "Frankfurt", "Germany: FR7, Frankfurt"),
    *(("IRL", f"DB{i}", "Dublin", f"Ireland: DB{i}, Dublin") for i in range(1, 5)),
    *(("ITA", f"ML{i}", "Milan", f"Italy: ML{i}, Milan") for i in range(1, 4)),
    ("NLD", "AM3", "Amsterdam", "The Netherlands: AM3, Amsterdam"),
    ("NLD", "AM5", "Amsterdam", "The Netherlands: AM5, Amsterdam"),
    ("NLD", "AM6", "Amsterdam", "The Netherlands: AM6, Amsterdam"),
    ("NLD", "AM7", "Amsterdam", "The Netherlands: AM7, Amsterdam"),
    *(("SWE", f"SK{i}", "Stockholm", f"Sweden: SK{i}, Stockholm") for i in range(1, 4)),
    ("CHE", "ZH4", "Zurich", "Switzerland: ZH4, Zurich"),
    ("TUR", "IS1", "Istanbul", "Turkey: IS1, Istanbul"),
    ("POL", "WA1", "Warsaw", "Poland: WA1, Warsaw"),
    ("POL", "WA2", "Warsaw", "Poland: WA2, Warsaw"),
    ("GBR", "LD4", "Slough", "United Kingdom: LD4, Slough"),
    ("GBR", "LD5", "London", "United Kingdom: LD5, London"),
    ("GBR", "LD9", "London", "United Kingdom: LD9, London"),
    ("GBR", "LD8", "London", "United Kingdom: LD8, London"),
    *(("GBR", f"MA{i}", "Manchester", f"United Kingdom: MA{i}, Manchester") for i in range(1, 5)),
]


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def build_record(
    country_code: str, facility_code: str, locality: str, registry_label: str
) -> dict[str, object]:
    name = f"Equinix EMEA {facility_code}"
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
    locator = f"Participants table / {PARTICIPANT} / {registry_label}"
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
                "European Commission JRC participant-registry identity, city and adhesion "
                "year only; not evidence of current lifecycle, ownership, operation, "
                "capacity or certification."
            ),
            "field": "eu_code_of_conduct_participant",
            "kind": "reported",
            "locator": locator,
            "source_id": SOURCE_ID,
            "unit": None,
            "value": {"adhesion_year": 2013, "participant": PARTICIPANT},
        }
    ]
    if facility_code == "AM7":
        observations.append(
            {
                "as_of": AS_OF,
                "boundary": (
                    "The registry prints the exact AM7 row twice. Both copies are identical; "
                    "one facility identity is normalized and no second record is synthesized."
                ),
                "field": "registry_row_occurrences",
                "kind": "reported",
                "locator": locator,
                "source_id": SOURCE_ID,
                "unit": "rows",
                "value": 2,
            }
        )
    return {
        "aggregation_role": "unresolved",
        "aliases": [facility_code, registry_label],
        "capacity_scope": (
            f"{facility_code} is an exact JRC participant-registry data-centre identity. "
            "Its physical aggregation and all IT, grid and facility-demand boundaries are "
            "unresolved, so it is excluded from capacity totals under every filter."
        ),
        "country_code": country_code,
        "created_at": RETRIEVED_AT,
        "entity_type": "projects",
        "evidence_json": compact(evidence),
        "external_ids_json": compact({"eu_jrc_code_of_conduct": f"{PARTICIPANT}::{facility_code}"}),
        "facility_id": stable_id("facility", PARTICIPANT, facility_code),
        "facility_type": "unknown",
        "field_sources_json": compact(field_sources),
        "last_verified_at": RETRIEVED_AT,
        "locality": locality,
        "location_accuracy": (
            "city only from the JRC participant registry; no address or coordinates normalized"
        ),
        "name": name,
        "observations_json": compact(observations),
        "official_url": SOURCE_URL,
        "quality_status": "source_backed",
        "record_id": stable_id("projects", PARTICIPANT, facility_code),
        "record_scope": "facility",
        "source_urls": [SOURCE_URL],
        "sources": [SOURCE_ID],
        "status": "unknown",
        "status_as_of": AS_OF,
        "status_date_basis": (
            "Current JRC participant registry retrieved through indexed public copies; "
            "the 2013 adhesion year is not a lifecycle date."
        ),
        "updated_at": RETRIEVED_AT,
    }


def build() -> list[dict[str, object]]:
    rows = [build_record(*facility) for facility in FACILITIES]
    if len(rows) != 34 or len({row["record_id"] for row in rows}) != 34:
        raise ValueError("Expected 34 unique JRC Equinix participant-facility records")
    if [row["aliases"][0] for row in rows].count("AM7") != 1:  # type: ignore[index,union-attr]
        raise ValueError("Expected duplicated AM7 source row to normalize once")
    return sorted(rows, key=lambda row: str(row["record_id"]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = build()
    args.output.write_text(
        "".join(compact(row) + "\n" for row in rows), encoding="utf-8", newline="\n"
    )
    print("Wrote 34 reviewed JRC Equinix participant-facility records")


if __name__ == "__main__":
    main()
