"""Build the bounded cross-language-stable JRC 2015--2018 batch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id

RETRIEVED_AT = "2026-11-06T11:16:48Z"
AS_OF = "2026-11-06"
SOURCE_ID = "jrc-data-centre-code-of-conduct-2015-2018-crosscopy-20261106"
SOURCE_URL = (
    "https://e3p.jrc.ec.europa.eu/fr/groups/data-centres-code-conduct/"
    "participants?order=field_adhesion_date&page=2&partner_search=&sort=asc"
)

ROWS = [
    ("AIMES Grid Services", 2015, "GBR", "kilby house", None),
    ("CGI IT UK limited", 2015, "GBR", "Bridgend-Waterton", "Bridgend"),
    ("CGI IT UK limited", 2015, "GBR", "Bridgend Science Park", "Bridgend"),
    ("DataCentred Limited", 2015, "GBR", "Unit 4&5, Salford", "Salford"),
    ("EUMETSAT", 2016, "DEU", "Darmstadt", "Darmstadt"),
    ("Euroclear Bank SA/NV", 2016, "FRA", "DC1: Bry sur Marne (France", "Bry sur Marne"),
    ("Euroclear Bank SA/NV", 2016, "FRA", "DC2: ZAC de BUSSY SUD (France)", None),
    ("FCO Services", 2016, "GBR", "FCO CDC - Milton Keynes", "Milton Keynes"),
    (
        "FCO Services",
        2016,
        "GBR",
        "FCO Services DC 25 - Milton Keynes",
        "Milton Keynes",
    ),
    ("Interxion Carrier Hotel, Ltd.", 2017, "GBR", "LON1", None),
    ("Interxion Carrier Hotel, Ltd.", 2017, "GBR", "LON2", None),
    ("Interxion Carrier Hotel, Ltd.", 2017, "GBR", "LON3", None),
    ("University of Strasbourg", 2018, "FRA", "ESPE meinau", None),
    ("University of Strasbourg", 2018, "FRA", "Campus Esplanade", None),
    ("Atos IT services", 2018, "GBR", "Andover DC, Hants, England", "Andover"),
    ("Atos IT services", 2018, "GBR", "Birmingham Business Park", "Birmingham"),
    ("Atos IT services", 2018, "GBR", "Longbridge Data Centre", "Longbridge"),
]


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def build_record(
    *, participant: str, year: int, country_code: str, label: str, locality: str | None
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
                "European Commission JRC participant-registry identity and adhesion year "
                "only; not evidence of current lifecycle, ownership, operation, capacity "
                "or certification. The row was accepted only where the participant, count, "
                "facility labels and year were stable across reviewed official-language "
                "indexed copies."
            ),
            "field": "eu_code_of_conduct_participant",
            "kind": "reported",
            "locator": locator,
            "source_id": SOURCE_ID,
            "unit": None,
            "value": {"adhesion_year": year, "participant": participant},
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
            f"copies; the {year} adhesion year is not a lifecycle date."
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
            year=year,
            country_code=country_code,
            label=label,
            locality=locality,
        )
        for participant, year, country_code, label, locality in ROWS
    ]
    if len(records) != 17 or len({row["record_id"] for row in records}) != 17:
        raise ValueError("Expected 17 unique cross-language-stable JRC records")
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
    print("Wrote 17 reviewed cross-language-stable JRC participant-facility records")


if __name__ == "__main__":
    main()
