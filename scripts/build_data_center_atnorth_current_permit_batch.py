"""Reconcile current FIN04 permit identities and SWE04 infrastructure evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

RETRIEVED_AT = "2026-11-05T17:20:00Z"
AS_OF = "2026-11-05"

FIN04 = "97acac46-881e-5df5-baa1-ec16eacbc60f"
SWE04 = "037414f4-36e7-5e55-a76a-48019a8979d4"

SOURCES = {
    "kouvola-fin04a-ph2-building-permit-286-2025-384": {
        "url": "https://ep10.kouvola.fi/kokous/20261365.PDF",
        "publication_date": "2026-02-11",
    },
    "kouvola-fin04a-ph3-building-permit-286-2026-281": {
        "url": "https://ep10.kouvola.fi/cgi/DREQUEST.PHP?id=8E24F686X599BX41B9XB293X75D7173CDF7D-8&page=meetingitem",
        "publication_date": "2026-09-09",
    },
    "kouvola-fin04b-modification-permit-286-2026-282": {
        "url": "https://ep10.kouvola.fi/cgi/DREQUEST.PHP?id=8E24F686X599BX41B9XB293X75D7173CDF7D-7&page=meetingitem",
        "publication_date": "2026-09-09",
    },
    "kouvola-fin04c-ph2-building-permit-286-2026-277": {
        "url": "https://ep10.kouvola.fi/cgi/DREQUEST.PHP?id=8E24F686X599BX41B9XB293X75D7173CDF7D-10&page=meetingitem",
        "publication_date": "2026-09-09",
    },
    "atnorth-swe04-consultation-v2-20260616": {
        "url": "https://www.atnorth.com/wp-content/uploads/2026/06/SWE04-Samradsunderlag-260616.pdf",
        "publication_date": "2026-06-16",
    },
    "enersense-swe04-grid-lines-20261103": {
        "url": "https://enersense.com/releases/enersense-signs-two-power-line-contracts-in-sweden-including-one-supporting-data-centre-development/",
        "publication_date": "2026-11-03",
    },
    "atnorth-calentix-swe04-heat-reuse-20261104": {
        "url": "https://www.atnorth.com/blog/why-heat-reuse-starts-with-planning/",
        "publication_date": "2026-11-04",
    },
}


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def observation(
    source_id: str,
    field: str,
    value: object,
    *,
    boundary: str,
    locator: str,
    unit: str | None = None,
    kind: str = "reported",
    as_of: str = AS_OF,
) -> dict[str, object]:
    return {
        "as_of": as_of,
        "boundary": boundary,
        "field": field,
        "kind": kind,
        "locator": locator,
        "source_id": source_id,
        "unit": unit,
        "value": value,
    }


def add_sources(record: dict[str, Any], source_ids: list[str]) -> None:
    record["sources"] = sorted(set(record["sources"] + source_ids))
    record["source_urls"] = sorted(
        set(record["source_urls"] + [SOURCES[source_id]["url"] for source_id in source_ids])
    )
    record["updated_at"] = RETRIEVED_AT
    record["last_verified_at"] = RETRIEVED_AT


def add_evidence(record: dict[str, Any], field: str, source_ids: list[str], locator: str) -> None:
    evidence = json.loads(record["evidence_json"])
    evidence[field] = {
        "confidence": "high",
        "locator": locator,
        "source_publication_dates": {
            source_id: SOURCES[source_id]["publication_date"] for source_id in source_ids
        },
    }
    record["evidence_json"] = compact(evidence)
    field_sources = json.loads(record["field_sources_json"])
    field_sources[field] = sorted(set(field_sources.get(field, []) + source_ids))
    record["field_sources_json"] = compact(field_sources)


def enrich_fin04(record: dict[str, Any]) -> dict[str, Any]:
    record = dict(record)
    source_ids = [source_id for source_id in SOURCES if source_id.startswith("kouvola-")]
    observations = [
        item
        for item in json.loads(record["observations_json"])
        if item.get("source_id") not in source_ids
    ]
    observations.extend(
        [
            observation(
                source_ids[0],
                "building_permit",
                "286-2025-384",
                boundary=(
                    "FIN04A Phase 2; three data-center buildings and two transformer buildings"
                ),
                locator="meeting item section 6 and FIN04A ph2 attachment label",
                as_of="2026-02-11",
            ),
            observation(
                source_ids[0],
                "building_floor_area",
                38220,
                boundary=(
                    "FIN04A Phase 2; sum of three separately printed 12,740 m2 "
                    "data-center floor areas only"
                ),
                locator="meeting item section 6 area table",
                unit="m2",
                as_of="2026-02-11",
            ),
            observation(
                source_ids[0],
                "building_count",
                3,
                boundary=(
                    "FIN04A Phase 2 data-center buildings; transformer and ancillary "
                    "buildings excluded"
                ),
                locator="meeting item section 6 project summary",
                unit="count",
                as_of="2026-02-11",
            ),
            observation(
                source_ids[1],
                "building_permit",
                "286-2026-281",
                boundary="FIN04A Phase 3; exact permit identity",
                locator="meeting item section 66 title and decision",
                as_of="2026-09-09",
            ),
            observation(
                source_ids[1],
                "building_floor_area",
                8900,
                boundary=(
                    "FIN04A Phase 3 data-center Rak1 floor area only; total area including "
                    "technical yards remains separate"
                ),
                locator="meeting item section 66 area table",
                unit="m2",
                as_of="2026-09-09",
            ),
            observation(
                source_ids[2],
                "building_permit_modification",
                "286-2026-282 modifies 286-2025-165",
                boundary="FIN04B exact modification permit; not FIN04 campus total",
                locator="meeting item section 65 title and opening paragraph",
                as_of="2026-09-09",
            ),
            observation(
                source_ids[2],
                "building_floor_area",
                20993,
                boundary=(
                    "FIN04B modified data-center Rak1 floor area only; total area including "
                    "technical equipment remains separate"
                ),
                locator="meeting item section 65 area table",
                unit="m2",
                as_of="2026-09-09",
            ),
            observation(
                source_ids[3],
                "building_permit",
                "286-2026-277",
                boundary="FIN04C Phase 2; exact permit identity",
                locator="meeting item section 68 title and decision",
                as_of="2026-09-09",
            ),
            observation(
                source_ids[3],
                "building_floor_area",
                18737,
                boundary=(
                    "FIN04C Phase 2 two-storey DC2 floor area only; 40,697 m2 total includes "
                    "technical equipment"
                ),
                locator="meeting item section 68 area table",
                unit="m2",
                as_of="2026-09-09",
            ),
        ]
    )
    record["observations_json"] = compact(observations)
    record["notes"] = (
        "Official permits now bind FIN04A Phase 2, FIN04A Phase 3, FIN04B and FIN04C Phase 2 "
        "identities and areas to exact properties. Their relationship to the two generic "
        "YIT contract records remains unresolved; no duplicate physical phase, capacity or "
        "contractor assignment is inferred."
    )
    add_sources(record, source_ids)
    add_evidence(record, "observations_json", source_ids, "official permit titles and area tables")
    add_evidence(record, "notes", source_ids, "permit identity reconciliation")
    return record


def enrich_swe04(record: dict[str, Any]) -> dict[str, Any]:
    record = dict(record)
    source_ids = [source_id for source_id in SOURCES if not source_id.startswith("kouvola-")]
    observations = [
        item
        for item in json.loads(record["observations_json"])
        if item.get("source_id") not in source_ids
    ]
    observations.extend(
        [
            observation(
                source_ids[0],
                "environmental_consultation",
                "Version 2.0 delimitation consultation",
                boundary="SWE04 permit application consultation; not a permit grant",
                locator="cover, contents and administrative details",
                as_of="2026-06-16",
            ),
            observation(
                source_ids[0],
                "backup_combustion_input",
                1200,
                boundary=(
                    "SWE04 planned combustion installation total fuel input; not electrical "
                    "output, grid demand or IT load"
                ),
                locator="section 1.1 background",
                unit="MW",
                as_of="2026-06-16",
            ),
            observation(
                source_ids[1],
                "grid_line_contract",
                "two new Hamre-Nässe 130 kV overhead lines, each approximately 2.5 km",
                boundary=(
                    "regional grid infrastructure supporting SWE04; not a facility "
                    "energisation event"
                ),
                locator="new power lines section",
                as_of="2026-11-03",
            ),
            observation(
                source_ids[1],
                "grid_line_construction_period",
                "November 2026 to March 2029",
                boundary="Enersense line-project schedule; not SWE04 commissioning",
                locator="release schedule paragraphs",
                as_of="2026-11-03",
            ),
            observation(
                source_ids[2],
                "heat_reuse_development_agreement",
                "atNorth-Calentix project development agreement",
                boundary=(
                    "SWE04 feasibility and development work; no delivered heat or final "
                    "investment decision"
                ),
                locator="Collaboration: From feasibility to development at SWE04",
                as_of="2026-11-04",
            ),
            observation(
                source_ids[2],
                "heat_reuse_destination",
                "Långsele district heating network operated by Adven",
                boundary=(
                    "potential SWE04 heat-recovery connection; delivery quantity and start "
                    "remain uncommitted"
                ),
                locator="planning for the ecosystem section",
                as_of="2026-11-04",
            ),
        ]
    )
    record["observations_json"] = compact(observations)
    record["heat_rejection"] = "District heat reuse under development; no delivered heat evidenced"
    record["status_as_of"] = "2026-11-03"
    record["status_date_basis"] = (
        "November 2026 grid-line contract and June consultation evidence development and "
        "permitting; "
        "neither establishes physical SWE04 construction or commissioning"
    )
    add_sources(record, source_ids)
    add_evidence(
        record,
        "observations_json",
        source_ids,
        "consultation, grid-contract and heat-reuse sections",
    )
    add_evidence(
        record, "heat_rejection", [source_ids[2]], "SWE04 feasibility and development agreement"
    )
    add_evidence(record, "status_as_of", [source_ids[1]], "dated grid-infrastructure contract")
    add_evidence(record, "status_date_basis", source_ids, "latest dated development evidence")
    return record


def build(input_path: Path, output_path: Path) -> None:
    records = [json.loads(line) for line in input_path.read_text().splitlines() if line.strip()]
    found: set[str] = set()
    for index, record in enumerate(records):
        if record["record_id"] == FIN04:
            records[index] = enrich_fin04(record)
            found.add(FIN04)
        elif record["record_id"] == SWE04:
            records[index] = enrich_swe04(record)
            found.add(SWE04)
    if found != {FIN04, SWE04}:
        raise ValueError(f"Expected FIN04 and SWE04 records, found {sorted(found)}")
    output_path.write_text("".join(compact(record) + "\n" for record in records))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    build(args.input, args.output)
    print("Reconciled current FIN04 permits and SWE04 infrastructure evidence")


if __name__ == "__main__":
    main()
