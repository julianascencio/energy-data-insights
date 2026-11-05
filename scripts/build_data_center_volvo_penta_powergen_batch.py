"""Build reviewed current Volvo Penta power-generation engine configurations."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
from typing import Any, NamedTuple

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.inventories import (
    parse_volvo_penta_powergen_matrix,
)

RETRIEVED_AT = "2026-11-05T18:20:00Z"
STAGE_IIIA_RETRIEVED_AT = "2026-11-05T19:20:00Z"
AS_OF = "2026-11-05"


class Source(NamedTuple):
    source_id: str
    slug: str
    family: str
    emissions: str
    expected: int


SOURCES = (
    Source("volvo-penta-d8-stage-v-current-20261105", "d8-eu-stage-v", "D8", "EU Stage V", 6),
    Source("volvo-penta-d13-stage-v-current-20261105", "d13-eu-stage-v", "D13", "EU Stage V", 6),
    Source(
        "volvo-penta-d16-stage-v-current-20261105",
        "d16-eu-stage-v",
        "D16",
        "EU Stage V/EPA Tier 4f",
        2,
    ),
    Source(
        "volvo-penta-d16-stage-ii-current-20261105",
        "d16-eu-stage-ii-epa-tier-2",
        "D16",
        "EU Stage II/EPA Tier 2",
        8,
    ),
)
STAGE_IIIA_SOURCES = (
    Source(
        "volvo-penta-d8-stage-iiia-current-20261105",
        "d8-eu-stage-iiia-epa-tier-3",
        "D8",
        "EU Stage IIIA/EPA Tier 3",
        6,
    ),
    Source(
        "volvo-penta-d13-stage-iiia-current-20261105",
        "d13-eu-stage-iiia-epa-tier-3",
        "D13",
        "EU Stage IIIA/EPA Tier 3",
        10,
    ),
    Source(
        "volvo-penta-d16-stage-iiia-current-20261105",
        "d16-eu-stage-iiia-epa-tier-3",
        "D16",
        "EU Stage IIIA/EPA Tier 3",
        6,
    ),
)
URL_PREFIX = (
    "https://www.volvopenta.com/industrial/power-generation-engines/power-generation-engine-range/"
)


class Rating(NamedTuple):
    model: str
    frequency: int
    prime_kwm: int | None
    prime_kw: int
    prime_kva: int
    standby_kwm: int | None
    standby_kw: int
    standby_kva: int


RATINGS: dict[str, tuple[Rating, ...]] = {
    "d8-eu-stage-iiia-epa-tier-3": (
        Rating("TAD851GE", 50, 220, 202, 253, 242, 223, 278),
        Rating("TAD851GE", 60, 225, 207, 259, 248, 228, 285),
        Rating("TAD852GE", 50, 248, 231, 289, 273, 254, 317),
        Rating("TAD852GE", 60, 247, 230, 287, 272, 253, 316),
        Rating("TAD853GE", 50, 248, 233, 291, 273, 257, 321),
        Rating("TAD853GE", 60, 266, 250, 313, 293, 275, 344),
    ),
    "d13-eu-stage-iiia-epa-tier-3": (
        Rating("TAD1350GE", 60, 245, 228, 285, 269, 250, 313),
        Rating("TAD1351GE", 50, 279, 259, 324, 306, 285, 356),
        Rating("TAD1351GE", 60, 294, 273, 342, 323, 300, 375),
        Rating("TAD1352GE", 50, 314, 292, 365, 345, 321, 401),
        Rating("TAD1352GE", 60, 344, 320, 400, 376, 350, 437),
        Rating("TAD1353GE", 60, 391, 364, 455, 430, 400, 500),
        Rating("TAD1354GE", 50, 328, 305, 381, 361, 336, 420),
        Rating("TAD1354GE", 60, 344, 320, 400, 376, 350, 437),
        Rating("TAD1355GE", 50, 355, 330, 413, 390, 363, 453),
        Rating("TAD1355GE", 60, 344, 320, 400, 376, 350, 437),
    ),
    "d16-eu-stage-iiia-epa-tier-3": (
        Rating("TAD1650GE", 50, 393, 369, 462, 433, 407, 509),
        Rating("TAD1650GE", 60, 439, 413, 516, 483, 454, 568),
        Rating("TAD1651GE", 50, 430, 404, 505, 473, 445, 556),
        Rating("TAD1651GE", 60, 494, 464, 580, 546, 513, 642),
        Rating("TWD1652GE", 50, 505, 480, 600, 557, 529, 661),
        Rating("TWD1653GE", 50, 547, 520, 650, 603, 573, 716),
    ),
    "d8-eu-stage-v": (
        Rating("TAD880GE", 50, 129, 120, 150, 142, 132, 165),
        Rating("TAD880GE", 60, 151, 140, 175, 166, 154, 193),
        Rating("TAD881GE", 50, 172, 160, 200, 189, 176, 220),
        Rating("TAD881GE", 60, 198, 184, 230, 218, 202, 253),
        Rating("TAD882GE", 50, 215, 200, 250, 240, 224, 279),
        Rating("TAD882GE", 60, 218, 203, 254, 240, 224, 279),
    ),
    "d13-eu-stage-v": (
        Rating("TAD1380GE", 50, 260, 242, 302, 286, 266, 332),
        Rating("TAD1380GE", 60, 274, 254, 318, 301, 280, 350),
        Rating("TAD1381GE", 50, 303, 282, 352, 333, 310, 387),
        Rating("TAD1381GE", 60, 315, 283, 367, 347, 323, 403),
        Rating("TAD1382GE", 50, 345, 320, 401, 379, 352, 441),
        Rating("TAD1382GE", 60, 355, 330, 412, 390, 363, 453),
    ),
    "d16-eu-stage-v": (
        Rating("TWD1683GE", 50, None, 528, 660, None, 581, 726),
        Rating("TWD1683GE", 60, None, 560, 700, None, 616, 770),
    ),
    "d16-eu-stage-ii-epa-tier-2": (
        Rating("TAD1641GE", 50, 430, 404, 505, 473, 445, 556),
        Rating("TAD1641GE", 60, 485, 456, 570, 546, 513, 642),
        Rating("TAD1642GE", 50, 503, 473, 591, 554, 521, 651),
        Rating("TAD1642GE", 60, 532, 500, 625, 585, 550, 687),
        Rating("TWD1644GE", 50, 555, 521, 652, 610, 573, 717),
        Rating("TWD1644GE", 60, 582, 574, 684, 640, 602, 752),
        Rating("TWD1645GE", 50, 595, 560, 700, 655, 616, 770),
        Rating("TWD1645GE", 60, 619, 582, 727, 681, 640, 800),
    ),
}

FIELDS = [
    "family",
    "emission_level",
    "model",
    "frequency_hz",
    "prime_mechanical_kw",
    "prime_output_kw",
    "prime_apparent_kva",
    "standby_mechanical_kw",
    "standby_output_kw",
    "standby_apparent_kva",
    "fuel_type",
    "cylinders",
    "locator",
]


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def url(source: Source) -> str:
    return f"{URL_PREFIX}{source.slug}/"


def extracted_csv(source: Source) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    for row in RATINGS[source.slug]:
        writer.writerow(
            {
                "family": source.family,
                "emission_level": source.emissions,
                "model": row.model,
                "frequency_hz": row.frequency,
                "prime_mechanical_kw": "" if row.prime_kwm is None else row.prime_kwm,
                "prime_output_kw": row.prime_kw,
                "prime_apparent_kva": row.prime_kva,
                "standby_mechanical_kw": "" if row.standby_kwm is None else row.standby_kwm,
                "standby_output_kw": row.standby_kw,
                "standby_apparent_kva": row.standby_kva,
                "fuel_type": "Diesel/HVO",
                "cylinders": 6,
                "locator": (
                    f"{source.family} {source.emissions} table / {row.model} / {row.frequency} Hz"
                ),
            }
        )
    return stream.getvalue().encode()


def observation(
    candidate: dict[str, Any], source: Source, field: str, value: object, unit: str | None
) -> dict[str, object]:
    return {
        "as_of": AS_OF,
        "boundary": (
            f"{candidate['model']} {candidate['frequency_hz']:g} Hz exact current "
            f"{source.family} {source.emissions} table row"
        ),
        "field": field,
        "kind": "reported",
        "locator": candidate["locator"],
        "source_id": source.source_id,
        "unit": unit,
        "value": value,
    }


def build_record(
    candidate: dict[str, Any], source: Source, *, retrieved_at: str = RETRIEVED_AT
) -> dict[str, object]:
    model = candidate["model"]
    frequency = candidate["frequency_hz"]
    observations = [
        observation(
            candidate, source, "standby_output_power", candidate["standby_output_kw"], "kW"
        ),
        observation(
            candidate,
            source,
            "standby_apparent_power",
            candidate["standby_apparent_kva"],
            "kVA",
        ),
        observation(candidate, source, "fuel_type", candidate["fuel_type"], None),
        observation(candidate, source, "number_of_cylinders", candidate["cylinders"], None),
        observation(candidate, source, "emission_level", source.emissions, None),
    ]
    for field, key in (
        ("prime_mechanical_power", "prime_mechanical_kw"),
        ("standby_mechanical_power", "standby_mechanical_kw"),
    ):
        if candidate[key] is not None:
            observations.append(observation(candidate, source, field, candidate[key], "kWm"))
    fields = [
        "apparent_power_kva",
        "capacity_scope",
        "equipment_category",
        "form_factor",
        "frequency_hz",
        "manufacturer",
        "model",
        "name",
        "notes",
        "observations_json",
        "official_url",
        "output_power_kw",
        "power_conditions",
        "power_rating_kind",
        "record_scope",
        "variant",
    ]
    evidence = {
        field: {
            "confidence": "high",
            "locator": candidate["locator"],
            "source_publication_dates": {source.source_id: None},
        }
        for field in fields
    }
    for field, unit in (
        ("apparent_power_kva", "kVA"),
        ("frequency_hz", "Hz"),
        ("output_power_kw", "kW"),
    ):
        evidence[field]["unit"] = unit
    return {
        "apparent_power_kva": candidate["prime_apparent_kva"],
        "capacity_scope": (
            f"Exact current Volvo Penta {model} {frequency:g} Hz prime rating row; normalized "
            "kW is generator electrical output and kVA is generator apparent output, not engine "
            "mechanical power, standby output or facility backup capacity"
        ),
        "created_at": retrieved_at,
        "entity_type": "equipment",
        "equipment_category": "backup_generator",
        "evidence_json": compact(evidence),
        "field_sources_json": compact({field: [source.source_id] for field in fields}),
        "form_factor": "power-generation engine rating configuration",
        "frequency_hz": frequency,
        "last_verified_at": retrieved_at,
        "manufacturer": "Volvo Penta",
        "model": model,
        "name": f"Volvo Penta {model} {frequency:g} Hz prime power configuration",
        "notes": (
            "Prime electrical kW/kVA, standby electrical kW/kVA and engine mechanical kWm "
            "remain distinct. Fuel and emissions labels are OEM observations. No complete "
            "genset BOM, alternator, voltage, deployment or issuer certification is inferred."
        ),
        "observations_json": compact(observations),
        "official_url": url(source),
        "output_power_kw": candidate["prime_output_kw"],
        "power_conditions": "OEM prime power rating; exact model and frequency row",
        "power_rating_kind": "prime generator electrical output active/apparent power",
        "quality_status": "source_backed",
        "record_id": stable_id("equipment", "Volvo Penta", model, f"{frequency:g} Hz", "prime"),
        "record_scope": "configuration",
        "source_urls": [url(source)],
        "sources": [source.source_id],
        "updated_at": retrieved_at,
        "variant": f"{source.emissions}; {frequency:g} Hz; prime",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--inventory",
        choices=("baseline", "stage-iiia"),
        default="baseline",
        help="Select a non-overlapping reviewed table inventory",
    )
    args = parser.parse_args()
    sources = SOURCES if args.inventory == "baseline" else STAGE_IIIA_SOURCES
    retrieved_at = RETRIEVED_AT if args.inventory == "baseline" else STAGE_IIIA_RETRIEVED_AT
    records: list[dict[str, object]] = []
    for source in sources:
        staged = parse_volvo_penta_powergen_matrix(
            extracted_csv(source), source_url=url(source), expected_count=source.expected
        )
        records.extend(
            build_record(candidate, source, retrieved_at=retrieved_at)
            for candidate in staged["candidates"]
        )
    if len(records) != 22 or len({record["record_id"] for record in records}) != 22:
        raise ValueError("Expected 22 unique Volvo Penta power-generation configurations")
    records.sort(key=lambda record: (record["model"], record["frequency_hz"]))
    args.output.write_text("".join(f"{compact(record)}\n" for record in records), encoding="utf-8")
    print(f"Wrote {len(records)} reviewed Volvo Penta power-generation configurations")


if __name__ == "__main__":
    main()
