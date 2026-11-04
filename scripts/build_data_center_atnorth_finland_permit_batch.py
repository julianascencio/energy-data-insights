"""Enrich reviewed atNorth Finland records from official municipal permit notices."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
from typing import Any

from energy_data_retrieval.data_center_catalogue.inventories import (
    parse_project_permit_matrix,
)

RETRIEVED_AT = "2026-11-04T00:42:00Z"
AS_OF = "2026-11-04"

FIN02_PHASE = "a110a486-dd8f-5aa1-b842-d03e61bf172b"
FIN04_CAMPUS = "97acac46-881e-5df5-baa1-ec16eacbc60f"
FIN05_CAMPUS = "8173a380-3306-5611-90c6-aed5b07fdec4"
FIN05_PHASE = "08f4ce47-dd1a-56eb-b2ad-bd99cce9d31e"

SOURCES = {
    "espoo-fin02-environmental-decision-20261006": {
        "url": "https://www.espoo.fi/fi/artikkelit/kuulutus-ilmoitus-paatoksesta-datakeskuksen-laajennuksen-ymparistolupa-ja-toiminnan-aloittamislupa",
        "publication_date": "2026-10-06",
    },
    "kouvola-fin04-building-permit-286-2025-165": {
        "url": "https://ep10.kouvola.fi/cgi/DREQUEST.PHP?id=20251261-11&page=meetingitem",
        "publication_date": "2025-06-03",
    },
    "kouvola-fin04-building-permit-286-2026-178": {
        "url": "https://ep10.kouvola.fi/cgi/DREQUEST.PHP?id=20261369-9&page=meetingitem",
        "publication_date": "2026-06-02",
    },
    "kouvola-fin04a-ph2-environmental-notice-20261020": {
        "url": "https://www.kouvola.fi/ilmoitukset-ja-kuulutukset/lupa-ja-valvontaviraston-ilmoitus-kuulutuksesta-myllykosken-datakeskuksen-fin04a-ph2-ymparistolupa-ja-toiminnan-aloittaminen-muutoksenhausta-huolimatta-kouvola/",
        "publication_date": "2026-10-20",
    },
    "salo-fin05-municipal-disclosure-20261005": {
        "url": "https://tiedotteet.salo.fi/atnorth-rakentaa-datakeskuksen-saloon/",
        "publication_date": "2026-10-05",
    },
}

ROWS = [
    {
        "record_id": FIN02_PHASE,
        "source_id": "espoo-fin02-environmental-decision-20261006",
        "authority_id": "LVV-U/18794/2026; decision 468/2026",
        "decision_date": "2026-10-06",
        "project_scope": "FIN02 data-center expansion environmental permit and start permit",
        "address": "Sinimäentie 6a, Espoo",
        "locator": "public notice sections 1-5",
    },
    {
        "record_id": FIN04_CAMPUS,
        "source_id": "kouvola-fin04-building-permit-286-2025-165",
        "authority_id": "286-2025-165",
        "decision_date": "2025-06-03",
        "project_scope": "one FIN04 data-center building and ancillary buildings",
        "building_area_m2": 40285,
        "address": "Jokisillantie 14, 46800 Myllykoski",
        "locator": "meeting item section 55 and area table",
    },
    {
        "record_id": FIN04_CAMPUS,
        "source_id": "kouvola-fin04-building-permit-286-2026-178",
        "authority_id": "286-2026-178",
        "decision_date": "2026-06-02",
        "project_scope": "a further FIN04 data-center building and ancillary buildings",
        "building_area_m2": 18737,
        "address": "Jokisillantie 14, 46800 Myllykoski",
        "locator": "meeting item section 54 and area table",
    },
    {
        "record_id": FIN04_CAMPUS,
        "source_id": "kouvola-fin04a-ph2-environmental-notice-20261020",
        "authority_id": "LVV-U/84381/2026",
        "decision_date": "2026-10-20",
        "project_scope": "FIN04A Phase 2 environmental-permit application",
        "address": "Myllykoski, Kouvola",
        "locator": "public notice lines 3-13",
    },
    {
        "record_id": FIN05_CAMPUS,
        "source_id": "salo-fin05-municipal-disclosure-20261005",
        "authority_id": "Salo release 2026-10-05 / whole campus",
        "decision_date": "2026-10-05",
        "project_scope": "FIN05 whole campus land, demand, connection and investment",
        "locator": "municipal release paragraphs 1-3",
    },
    {
        "record_id": FIN05_PHASE,
        "source_id": "salo-fin05-municipal-disclosure-20261005",
        "authority_id": "Salo release 2026-10-05 / first phase",
        "decision_date": "2026-10-05",
        "project_scope": "FIN05 first-phase electrical demand",
        "locator": "municipal release paragraph 3",
    },
]

CSV_FIELDS = [
    "record_id",
    "source_id",
    "authority_id",
    "decision_date",
    "project_scope",
    "building_area_m2",
    "address",
    "locator",
]


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def extracted_csv(rows: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})
    return stream.getvalue().encode()


def validate_inventory() -> None:
    for source_id, source in SOURCES.items():
        subset = [row for row in ROWS if row["source_id"] == source_id]
        parse_project_permit_matrix(
            extracted_csv(subset),
            source_url=source["url"],
            expected_count=len(subset),
        )


def observation(
    source_id: str,
    field: str,
    value: object,
    *,
    boundary: str,
    locator: str,
    unit: str | None = None,
    kind: str = "reported",
    qualifier: str | None = None,
    reference_year: int | None = None,
) -> dict[str, object]:
    item: dict[str, object] = {
        "as_of": AS_OF,
        "boundary": boundary,
        "field": field,
        "kind": kind,
        "locator": locator,
        "source_id": source_id,
        "unit": unit,
        "value": value,
    }
    if qualifier:
        item["qualifier"] = qualifier
    if reference_year:
        item["reference_year"] = reference_year
    return item


def add_evidence(record: dict[str, Any], field: str, source_ids: list[str], locator: str) -> None:
    evidence = json.loads(record["evidence_json"])
    evidence[field] = {
        "confidence": "high",
        "locator": locator,
        "source_publication_dates": {
            source_id: SOURCES[source_id]["publication_date"] for source_id in source_ids
        },
    }
    if field in {"facility_capacity_mw"}:
        evidence[field]["unit"] = "MW"
    record["evidence_json"] = compact(evidence)
    field_sources = json.loads(record["field_sources_json"])
    field_sources[field] = sorted(set(field_sources.get(field, []) + source_ids))
    record["field_sources_json"] = compact(field_sources)


def add_sources(record: dict[str, Any], source_ids: list[str]) -> None:
    record["sources"] = sorted(set(record["sources"] + source_ids))
    record["source_urls"] = sorted(
        set(record["source_urls"] + [SOURCES[source_id]["url"] for source_id in source_ids])
    )
    record["updated_at"] = RETRIEVED_AT
    record["last_verified_at"] = RETRIEVED_AT


def enrich(record: dict[str, Any]) -> dict[str, Any]:
    record = dict(record)
    observations = [
        item
        for item in json.loads(record["observations_json"])
        if item.get("source_id") not in SOURCES
    ]
    if record["record_id"] == FIN02_PHASE:
        source = "espoo-fin02-environmental-decision-20261006"
        record["address"] = "Sinimäentie 6a, Espoo"
        external = json.loads(record.get("external_ids_json", "{}"))
        external.update(
            environmental_case="LVV-U/18794/2026",
            environmental_decision="468/2026",
        )
        record["external_ids_json"] = compact(external)
        observations.append(
            observation(
                source,
                "environmental_permit_decision",
                "468/2026; case LVV-U/18794/2026",
                boundary="FIN02 expansion; permit decision and start permit, not capacity",
                locator="public notice sections 1-5",
            )
        )
        add_sources(record, [source])
        add_evidence(record, "address", [source], "public notice title")
        add_evidence(record, "external_ids_json", [source], "public notice sections 1-5")
    elif record["record_id"] == FIN04_CAMPUS:
        source_ids = [
            "kouvola-fin04-building-permit-286-2025-165",
            "kouvola-fin04-building-permit-286-2026-178",
            "kouvola-fin04a-ph2-environmental-notice-20261020",
        ]
        record["address"] = "Jokisillantie 14, 46800 Myllykoski"
        observations.extend(
            [
                observation(
                    source_ids[0],
                    "building_permit",
                    "286-2025-165",
                    boundary="one permitted FIN04 data-center building; not the campus total",
                    locator="meeting item section 55",
                ),
                observation(
                    source_ids[0],
                    "building_area",
                    40285,
                    unit="m2",
                    boundary=(
                        "permit 286-2025-165 Rak1; includes electrical containers, "
                        "transformers and generators"
                    ),
                    locator="meeting item section 55 area table",
                ),
                observation(
                    source_ids[1],
                    "building_permit",
                    "286-2026-178",
                    boundary=(
                        "a further permitted FIN04 data-center building; phase identity not assumed"
                    ),
                    locator="meeting item section 54",
                ),
                observation(
                    source_ids[1],
                    "building_area",
                    18737,
                    unit="m2",
                    boundary="permit 286-2026-178 Rak1 only; not campus or data-hall area",
                    locator="meeting item section 54 area table",
                ),
                observation(
                    source_ids[2],
                    "environmental_permit_application",
                    "FIN04A Ph2; case LVV-U/84381/2026",
                    boundary=(
                        "separately named phase; identity against existing YIT phases unresolved"
                    ),
                    locator="public notice lines 3-13",
                ),
            ]
        )
        conflict = json.loads(record.get("conflicts_json", "{}"))
        conflict.pop("phase_identity", None)
        conflict["phase_id"] = [
            {
                "boundary": "FIN04 campus child identity",
                "field": "phase_id",
                "locator": "public notice lines 3-13",
                "observed_at": RETRIEVED_AT,
                "source_publication_date": "2026-10-20",
                "sources": [source_ids[2]],
                "value": "FIN04A Ph2",
            },
            {
                "boundary": "Existing separately documented July 2026 YIT phase",
                "field": "phase_id",
                "locator": "No explicit cross-reference in reviewed municipal records",
                "observed_at": RETRIEVED_AT,
                "source_publication_date": None,
                "sources": ["yit-fin04-july-20261103"],
                "value": "identity relationship unresolved; no duplicate phase added",
            },
        ]
        record["conflicts_json"] = compact(conflict)
        record["quality_status"] = "needs_review"
        add_sources(record, source_ids)
        add_evidence(record, "address", source_ids[:2], "building-permit titles")
        add_evidence(record, "conflicts_json", source_ids, "permit identifiers and phase notice")
    elif record["record_id"] in {FIN05_CAMPUS, FIN05_PHASE}:
        source = "salo-fin05-municipal-disclosure-20261005"
        if record["record_id"] == FIN05_CAMPUS:
            observations.extend(
                [
                    observation(
                        source,
                        "operator_investment",
                        2_000_000_000,
                        unit="EUR",
                        boundary=(
                            "atNorth investment in FIN05; excludes customer-owned servers "
                            "and installation"
                        ),
                        locator="municipal release paragraph 1",
                        qualifier="approximately",
                        reference_year=2026,
                    ),
                    observation(
                        source,
                        "customer_equipment_investment",
                        10_000_000_000,
                        unit="EUR",
                        boundary=(
                            "possible customer investment in servers and installation; "
                            "not atNorth project investment"
                        ),
                        locator="municipal release paragraph 1",
                        qualifier="up to",
                        reference_year=2026,
                    ),
                    observation(
                        source,
                        "municipal_land_sale_area",
                        7,
                        unit="ha",
                        boundary="land sold by Salo to Regant DC1 Oy; not total campus area",
                        locator="municipal release paragraph 2",
                    ),
                    observation(
                        source,
                        "campus_area",
                        29,
                        unit="ha",
                        boundary="FIN05 whole project; approximate",
                        locator="municipal release paragraph 2",
                        qualifier="nearly",
                    ),
                    observation(
                        source,
                        "grid_connection_arrangement",
                        "connection through a Fingrid substation",
                        boundary="FIN05 whole project; voltage and contracted capacity not stated",
                        locator="municipal release paragraph 3",
                    ),
                ]
            )
        else:
            record["facility_capacity_mw"] = 75
            record["facility_capacity_basis"] = "ultimate_planned"
            record["capacity_scope"] = (
                "FIN05 first phase only: 60 MW reported IT capacity and separately reported "
                "75 MW first-phase electrical demand; neither is treated as grid capacity"
            )
            observations.append(
                observation(
                    source,
                    "first_phase_electrical_demand",
                    75,
                    unit="MW",
                    boundary=(
                        "FIN05 first phase; secured electrical need, not IT or "
                        "grid-connection rating"
                    ),
                    locator="municipal release paragraph 3",
                )
            )
            add_evidence(record, "facility_capacity_mw", [source], "municipal release paragraph 3")
            add_evidence(
                record, "facility_capacity_basis", [source], "municipal release paragraph 3"
            )
            add_evidence(
                record, "capacity_scope", [source], "municipal and operator phase boundaries"
            )
        add_sources(record, [source])
    else:
        return record
    record["observations_json"] = compact(observations)
    add_evidence(
        record,
        "observations_json",
        [source_id for source_id in record["sources"] if source_id in SOURCES],
        "reviewed field locators",
    )
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    validate_inventory()
    records = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines()]
    enriched = [enrich(record) for record in records]
    if len(enriched) != len(records):
        raise ValueError("Project count changed during enrichment")
    target_ids = {FIN02_PHASE, FIN04_CAMPUS, FIN05_CAMPUS, FIN05_PHASE}
    if {record["record_id"] for record in enriched} & target_ids != target_ids:
        raise ValueError("One or more target atNorth records are missing")
    args.output.write_text("".join(f"{compact(record)}\n" for record in enriched), encoding="utf-8")
    print("Enriched four atNorth Finland records from six bounded permit observations")


if __name__ == "__main__":
    main()
