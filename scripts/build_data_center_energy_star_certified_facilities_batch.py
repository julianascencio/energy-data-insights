"""Build a reviewed ENERGY STAR certified data-center facility year partition."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.data_center_catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.inventories import (
    parse_energy_star_certified_data_centers,
)

SOURCE_ID = "epa-energy-star-certified-data-centers-20261105"
SOURCE_URL = "https://www.energystar.gov/buildings/certified-data-centers"
RETRIEVED_AT = "2026-11-05T12:20:00Z"
AS_OF = "2026-11-05"
EXPECTED_TOTAL_COUNT = 337
EXPECTED_SELECTED_COUNTS = {2025: 50, 2026: 133}


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def observation(
    *, field: str, value: object, boundary: str, locator: str, unit: str | None = None
) -> dict[str, object]:
    return {
        "as_of": AS_OF,
        "boundary": boundary,
        "field": field,
        "kind": "reported",
        "locator": locator,
        "source_id": SOURCE_ID,
        "unit": unit,
        "value": value,
    }


def build_record(candidate: dict[str, object], *, certification_year: int) -> dict[str, object]:
    name = str(candidate["facility_name"])
    state = str(candidate["state"])
    owner = str(candidate["owner"])
    manager = candidate["property_manager"]
    identity = (name, state, owner)
    facility_id = stable_id("facility", "EPA ENERGY STAR registry", *identity)
    entities = [
        {
            "name": owner,
            "organization_id": stable_id("organization", owner),
            "role": "owner",
        }
    ]
    if manager:
        entities.append(
            {
                "name": manager,
                "organization_id": stable_id("organization", str(manager)),
                "role": "property_manager",
            }
        )
    observations = [
        observation(
            field="energy_star_certification_history",
            value={
                "label_years": candidate["label_years"],
                "certification_count": candidate["certification_count"],
                "most_recent_certification_year": candidate["most_recent_certification_year"],
            },
            boundary=(
                "one issuer-verified facility identity; label years are certification "
                "observations, not lifecycle dates or continuous certification"
            ),
            locator=str(candidate["locator"]),
        ),
        observation(
            field="reported_total_floor_space",
            value=candidate["reported_floor_space"],
            boundary=(
                "total floor-space value as printed; the public table does not label a unit, "
                "so no square-foot or square-metre normalization is made"
            ),
            locator=str(candidate["locator"]),
        ),
        observation(
            field="reported_construction_year",
            value=candidate["constructed_year"],
            boundary=(
                "year reported at certification application; year precision retained and "
                "not promoted to a construction or commissioning date"
            ),
            locator=str(candidate["locator"]),
            unit="year",
        ),
    ]
    if manager:
        observations.append(
            observation(
                field="property_manager",
                value=manager,
                boundary="property manager reported for this certification registry entry",
                locator=str(candidate["locator"]),
            )
        )
    fields = [
        "aggregation_role",
        "capacity_scope",
        "country_code",
        "entities_json",
        "facility_id",
        "facility_type",
        "location_accuracy",
        "name",
        "notes",
        "observations_json",
        "official_url",
        "owner_names",
        "record_scope",
        "region",
        "status",
        "status_as_of",
        "status_date_basis",
    ]
    evidence = {
        field: {
            "confidence": "high",
            "locator": str(candidate["locator"]),
            "source_publication_dates": {SOURCE_ID: None},
        }
        for field in fields
    }
    is_current = certification_year == 2026
    return {
        "aggregation_role": "independent",
        "capacity_scope": (
            "one issuer-certified facility identity; no IT, grid, facility, backup or battery "
            "capacity is disclosed"
        ),
        "country_code": "USA",
        "created_at": RETRIEVED_AT,
        "entities_json": compact(entities),
        "entity_type": "projects",
        "evidence_json": compact(evidence),
        "facility_id": facility_id,
        "facility_type": "unknown",
        "field_sources_json": compact({field: [SOURCE_ID] for field in fields}),
        "last_verified_at": RETRIEVED_AT,
        "location_accuracy": (
            "state only; EPA intentionally withholds locality for security. Address-like text "
            "inside the public facility name is not promoted to an address or coordinate"
        ),
        "name": name,
        "notes": (
            "EPA states that the registry reflects building information verified and submitted "
            f"at certification application. The {certification_year} certification supports "
            + ("operation in the label year" if is_current else "operation in that label year")
            + " but does not disclose commissioning date, operator, "
            "capacity, energy use, PUE or equipment deployment."
            + (
                ""
                if is_current
                else " It does not establish the facility's lifecycle after the label year."
            )
        ),
        "observations_json": compact(observations),
        "official_url": SOURCE_URL,
        "owner_names": [owner],
        "quality_status": "source_backed",
        "record_id": stable_id("projects", "EPA ENERGY STAR registry", *identity),
        "record_scope": "facility",
        "region": state,
        "source_urls": [SOURCE_URL],
        "sources": [SOURCE_ID],
        "status": "operational" if is_current else "unknown",
        "status_as_of": AS_OF,
        "status_date_basis": (
            "current issuer registry retrieved 2026-11-05 and most-recent certification label "
            "year 2026; exact certification date is undisclosed"
            if is_current
            else (
                "current issuer registry retrieved 2026-11-05; most-recent certification "
                f"label year {certification_year}; exact certification date is undisclosed; "
                "post-certification lifecycle is unknown"
            )
        ),
        "updated_at": RETRIEVED_AT,
    }


def write_shards(
    records: list[dict[str, object]],
    *,
    output_dir: Path,
    shard_size: int,
    certification_year: int,
) -> list[Path]:
    paths: list[Path] = []
    for index in range(0, len(records), shard_size):
        part = index // shard_size + 1
        path = output_dir / (
            f"2026-11-05-energy-star-facilities-{certification_year}-part-{part:02d}.jsonl"
        )
        shard = records[index : index + shard_size]
        path.write_text("".join(f"{compact(record)}\n" for record in shard), encoding="utf-8")
        paths.append(path)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html_path", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument(
        "--certification-year",
        type=int,
        choices=sorted(EXPECTED_SELECTED_COUNTS),
        default=2026,
    )
    parser.add_argument("--shard-size", type=int, default=25)
    args = parser.parse_args()
    if args.shard_size < 1:
        raise ValueError("--shard-size must be positive")
    expected_selected_count = EXPECTED_SELECTED_COUNTS[args.certification_year]
    staged = parse_energy_star_certified_data_centers(
        args.html_path.read_bytes(),
        source_url=SOURCE_URL,
        certification_year=args.certification_year,
        expected_total_count=EXPECTED_TOTAL_COUNT,
        expected_selected_count=expected_selected_count,
    )
    records = sorted(
        (
            build_record(candidate, certification_year=args.certification_year)
            for candidate in staged["candidates"]
        ),
        key=lambda record: (str(record["region"]), str(record["name"]), str(record["record_id"])),
    )
    if len(records) != expected_selected_count:
        raise ValueError("Unexpected ENERGY STAR facility record count")
    if len({record["record_id"] for record in records}) != len(records):
        raise ValueError("Duplicate ENERGY STAR facility record ID")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    paths = write_shards(
        records,
        output_dir=args.output_dir,
        shard_size=args.shard_size,
        certification_year=args.certification_year,
    )
    print(f"Wrote {len(records)} certified facilities to {len(paths)} shards")


if __name__ == "__main__":
    main()
