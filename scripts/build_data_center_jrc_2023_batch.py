"""Build the complete 35-identity JRC 2023 participant cohort."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id

RETRIEVED_AT = "2026-11-06T13:22:47Z"
AS_OF = "2026-11-06"
SOURCE_ID = "jrc-data-centre-code-of-conduct-2023-participants-20261106"
SOURCE_URL = (
    "https://e3p.jrc.ec.europa.eu/es/groups/data-centres-code-conduct/"
    "participants?order=field_adhesion_date&page=3&partner_search=&sort=asc"
)

ROWS = [
    ("A1 Telekom Austria AG", "AUT", "Wien 1", "Wien"),
    ("A1 Telekom Austria AG", "AUT", "Wien 2", "Wien"),
    ("OVH Groupe", "FRA", "Gravelines", "Gravelines"),
    ("OVH Groupe", "FRA", "Roubaix", "Roubaix"),
    ("OVH Groupe", "FRA", "Strasbourg", "Strasbourg"),
    ("OVH Groupe", "GBR", "Erith", "Erith"),
    ("OVH Groupe", "POL", "Varsaw", None),
    ("OVH Groupe", "DEU", "Limburg An Der Lahn", "Limburg An Der Lahn"),
    ("OVH Groupe", "CAN", "Beauharnois", "Beauharnois"),
    ("OVH Groupe", "USA", "Vint Hill (Virginia)", "Vint Hill"),
    ("OVH Groupe", "USA", "Hillsboro (Oregon)", "Hillsboro"),
    ("Interxion Detuschland GmbH", "DEU", "Frankfurt FRA08", "Frankfurt"),
    ("Interxion Detuschland GmbH", "DEU", "Frankfurt FRA10", "Frankfurt"),
    ("Interxion Detuschland GmbH", "DEU", "Frankfurt FRA11", "Frankfurt"),
    ("Interxion Detuschland GmbH", "DEU", "Frankfurt FRA12", "Frankfurt"),
    ("Interxion Detuschland GmbH", "DEU", "Frankfurt FRA13", "Frankfurt"),
    ("Interxion Detuschland GmbH", "DEU", "Frankfurt FRA15", "Frankfurt"),
    ("Irideos S.p.A.", "ITA", "Settimo Milanese (Avalon 2)", "Settimo Milanese"),
    ("Cegedim Group", "FRA", "ET1 Labege", "Labege"),
    ("Cegedim Group", "FRA", "EB4 Boulogne Biliancourt", None),
    ("BBBELL S.p.a", "ITA", "Torino", "Torino"),
    ("Information Tecchnology hosting SAS", "FRA", "Mamoudzo", None),
    ("KDCR (Ireland) Limited", "IRL", "DUB 1", None),
    ("KDCR (Ireland) Limited", "IRL", "DUB 2", None),
    ("BNP Paribas", "FRA", "Marne Est 1 MAE 1", None),
    ("BNP Paribas", "FRA", "Marne Nord MN", None),
    ("BNP Paribas", "FRA", "Marne Sud MS", None),
    ("Thales Servvice Numerique", "FRA", "Elancourt", "Elancourt"),
    ("Thales Servvice Numerique", "FRA", "Touluse", None),
    ("Aruba S.p.a", "ITA", "IT3.DC-A", None),
    ("Aruba S.p.a", "ITA", "IT3.DC-B", None),
    ("Aruba S.p.a", "ITA", "IT3.DC-C", None),
    ("Aruba S.p.a", "ITA", "IT1", None),
    ("Opiquad Srl", "ITA", "Merate", "Merate"),
    ("Stellium datacenters Ltd", "GBR", "Cobalt Park Way, Wallsend", "Wallsend"),
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
    observations: list[dict[str, object]] = [
        {
            "as_of": AS_OF,
            "boundary": (
                "European Commission JRC participant-registry identity and 2023 adhesion "
                "year only; not evidence of current lifecycle, ownership, operation, "
                "capacity or certification. Participant, displayed count, facility labels "
                "and year agreed across reviewed Spanish, Romanian and Gaelic official-"
                "language indexes. Exact source spellings are preserved."
            ),
            "field": "eu_code_of_conduct_participant",
            "kind": "reported",
            "locator": locator,
            "source_id": SOURCE_ID,
            "unit": None,
            "value": {"adhesion_year": 2023, "participant": participant},
        }
    ]
    if participant == "Interxion Detuschland GmbH" and label == "Frankfurt FRA08":
        observations.append(
            {
                "as_of": AS_OF,
                "boundary": (
                    "The registry repeats this exact facility label twice; one facility "
                    "identity is emitted."
                ),
                "field": "source_row_occurrences",
                "kind": "reported",
                "locator": locator,
                "source_id": SOURCE_ID,
                "unit": "rows",
                "value": 2,
            }
        )
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
            "copies; the 2023 adhesion year is not a lifecycle date."
        ),
        "updated_at": RETRIEVED_AT,
    }
    if locality is not None:
        record["locality"] = locality
    return record


def build() -> list[dict[str, object]]:
    records = [
        build_record(participant=p, country_code=c, label=label, locality=loc)
        for p, c, label, loc in ROWS
    ]
    if len(records) != 35 or len({row["record_id"] for row in records}) != 35:
        raise ValueError("Expected 35 unique JRC 2023 participant-facility records")
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
    print("Wrote 35 reviewed JRC 2023 participant-facility records")


if __name__ == "__main__":
    main()
