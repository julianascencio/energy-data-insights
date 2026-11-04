"""Build reviewed Makelsan LEVELUPS three-phase UPS rating configurations."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
from typing import Any

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.inventories import parse_ups_rating_matrix

RETRIEVED_AT = "2026-11-04T06:18:00Z"
AS_OF = "2026-11-04"

SOURCES: dict[str, dict[str, object]] = {
    "LEVELUPS": {
        "id": "makelsan-levelups-10-1000-2025",
        "url": "https://www.makelsanjenerator.com.tr/katalog/levelups-series-10---1000-kva.pdf",
        "publication_date": "2025-01-01",
    },
    "LEVELUPS T3": {
        "id": "makelsan-levelups-t3-10-200-2025",
        "url": "https://www.makelsan.com.tr/katalog/levelups-t3-series-10---200-kva.pdf",
        "publication_date": "2025-01-01",
    },
    "LEVELUPS T4": {
        "id": "makelsan-levelups-t4-80-200-2025",
        "url": "https://www.makelsan.com.tr/katalog/levelups-t4-series-80-200-kva-en.pdf",
        "publication_date": "2025-01-01",
    },
}

FAMILIES: dict[str, dict[str, Any]] = {
    "LEVELUPS": {
        "ratings": [
            (10, 10),
            (15, 15),
            (20, 20),
            (30, 30),
            (40, 40),
            (60, 60),
            (80, 80),
            (100, 100),
            (120, 120),
            (160, 160),
            (200, 200),
            (250, 225),
            (300, 270),
            (400, 360),
            (500, 450),
            (600, 540),
            (800, 720),
            (1000, 900),
        ],
        "form_factor": "floor-standing transformer-free three-phase UPS",
        "input": (
            "380/400/415 Vac three-phase plus neutral; optional 220/380 Vac input "
            "configuration; -20%/+15% standard voltage tolerance"
        ),
        "output": "380/400/415 Vac three-phase plus neutral",
        "frequency": "50/60 Hz selectable; +/-10% input; +/-0.01% battery-mode output",
        "efficiency": "96% online; up to 99% Eco; exact load points not stated",
        "battery": (
            "60 x 12 V cells; VRLA/GEL battery types and external battery choices are "
            "family-level options"
        ),
        "locator": "LEVELUPS SERIES 10-1000 kVA technical table",
    },
    "LEVELUPS T3": {
        "ratings": [
            (10, 10),
            (15, 15),
            (20, 20),
            (30, 30),
            (40, 40),
            (60, 60),
            (80, 80),
            (100, 100),
            (120, 120),
            (160, 160),
            (200, 200),
        ],
        "form_factor": "floor-standing transformer-based three-phase UPS",
        "input": (
            "380/400/415 Vac three-phase plus neutral; optional 220/380 Vac input "
            "configuration; 45-65 Hz input range"
        ),
        "output": "380/400/415 Vac three-phase plus neutral",
        "frequency": "45-65 Hz input; 50/60 Hz +/-0.01% battery-mode output",
        "efficiency": "94.5% family-table efficiency; exact load point not stated",
        "battery": "60 x 12 V VRLA cells; configuration and runtime are not stated per model",
        "locator": "LEVELUPS T3 SERIES 10-200 kVA technical table",
    },
    "LEVELUPS T4": {
        "ratings": [(80, 72), (100, 90), (120, 108), (160, 144), (200, 180)],
        "form_factor": "floor-standing transformer-based three-phase UPS",
        "input": (
            "380/400/415 Vac three-phase; optional 220/380 Vac input configuration; "
            "45-65 Hz input range"
        ),
        "output": "380/400/415 Vac three-phase plus neutral",
        "frequency": "45-65 Hz input; 50/60 Hz +/-0.01% battery-mode output",
        "efficiency": "92% family-table efficiency; exact load point not stated",
        "battery": "50 x 12 V VRLA cells; configuration and runtime are not stated per model",
        "locator": "LEVELUPS T4 SERIES 80-200 kVA technical table",
    },
}

CSV_FIELDS = [
    "manufacturer",
    "family",
    "variant",
    "apparent_power_kva",
    "output_power_kw",
    "voltage_text",
    "frequency_text",
    "locator",
]


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def rows() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for family, metadata in FAMILIES.items():
        for kva, kw in metadata["ratings"]:
            result.append(
                {
                    "manufacturer": "Makelsan",
                    "family": family,
                    "model": f"{family} {kva:g} kVA",
                    "variant": f"{kva:g} kVA / {kw:g} kW",
                    "apparent_power_kva": kva,
                    "output_power_kw": kw,
                    "voltage_text": f"input {metadata['input']}; output {metadata['output']}",
                    "frequency_text": metadata["frequency"],
                    "locator": f"{metadata['locator']} / {kva:g} kVA column",
                }
            )
    return result


def extracted_csv(items: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for item in items:
        writer.writerow({field: item.get(field, "") for field in CSV_FIELDS})
    return stream.getvalue().encode()


def observation(
    item: dict[str, Any],
    field: str,
    value: object,
    unit: str | None,
    boundary: str,
    source_id: str,
) -> dict[str, object]:
    return {
        "as_of": AS_OF,
        "boundary": boundary,
        "field": field,
        "kind": "reported",
        "locator": item["locator"],
        "source_id": source_id,
        "unit": unit,
        "value": value,
    }


def build_record(item: dict[str, Any]) -> dict[str, object]:
    family = str(item["family"])
    kva = float(item["apparent_power_kva"])
    metadata = FAMILIES[family]
    source = SOURCES[family]
    source_id = str(source["id"])
    boundary = f"Exact Makelsan {family} {kva:g} kVA published rating column"
    fields = [
        "apparent_power_kva",
        "capacity_scope",
        "equipment_category",
        "form_factor",
        "manufacturer",
        "model",
        "name",
        "notes",
        "observations_json",
        "official_url",
        "output_power_kw",
        "power_conditions",
        "power_rating_kind",
        "product_status",
        "record_scope",
        "variant",
    ]
    evidence = {
        field: {
            "confidence": "high",
            "locator": item["locator"],
            "source_publication_dates": {source_id: source["publication_date"]},
        }
        for field in fields
    }
    evidence["apparent_power_kva"]["unit"] = "kVA"
    evidence["output_power_kw"]["unit"] = "kW"
    observations = [
        observation(
            item, "input_voltage_configuration", metadata["input"], "V", boundary, source_id
        ),
        observation(
            item, "output_voltage_configuration", metadata["output"], "V", boundary, source_id
        ),
        observation(
            item, "frequency_configuration", metadata["frequency"], "Hz", boundary, source_id
        ),
        observation(
            item,
            "efficiency",
            metadata["efficiency"],
            "%",
            "Family table; no load-point scalar is normalized",
            source_id,
        ),
        observation(
            item,
            "battery_configuration",
            metadata["battery"],
            None,
            "Family table; no battery energy, usable energy or runtime inferred",
            source_id,
        ),
        observation(
            item,
            "overload_capability",
            "125% load for 10 minutes; 150% load for 1 minute",
            None,
            boundary,
            source_id,
        ),
        observation(
            item,
            "communications",
            "RS232 standard; RS485 and SNMP adapter options",
            None,
            "Family options; no accessory configuration synthesized",
            source_id,
        ),
        observation(item, "operating_temperature", "0 to 40", "degC", boundary, source_id),
        observation(
            item,
            "standards_claims",
            "OEM table lists EN 62040 performance and EMC/LVD statements",
            None,
            "OEM conformance statement; not an issuer-registry certification",
            source_id,
        ),
    ]
    return {
        "apparent_power_kva": item["apparent_power_kva"],
        "capacity_scope": (
            f"Exact Makelsan {family} {kva:g} kVA published rating column; selectable "
            "voltage, frequency, battery and communications options are not synthesized"
        ),
        "created_at": RETRIEVED_AT,
        "entity_type": "equipment",
        "equipment_category": "ups",
        "evidence_json": compact(evidence),
        "field_sources_json": compact({field: [source_id] for field in fields}),
        "form_factor": metadata["form_factor"],
        "last_verified_at": RETRIEVED_AT,
        "manufacturer": "Makelsan",
        "model": item["model"],
        "name": f"Makelsan {item['model']}",
        "notes": (
            "The exact OEM rating column is retained. Apparent kVA and active kW remain "
            "separate reported values. Voltage, frequency, batteries, communications and "
            "possible output-power-factor choices do not create inferred configurations."
        ),
        "observations_json": compact(observations),
        "official_url": source["url"],
        "output_power_kw": item["output_power_kw"],
        "power_conditions": (
            "Published UPS rated apparent and active output; efficiency remains an "
            "observation because the exact load point is not stated"
        ),
        "power_rating_kind": "rated UPS apparent and active output",
        "product_status": "listed in official Makelsan technical table reviewed 2026-11-04",
        "quality_status": "source_backed",
        "record_id": stable_id("equipment", "Makelsan", family, f"{kva:g} kVA"),
        "record_scope": "configuration",
        "source_urls": [str(source["url"])],
        "sources": [source_id],
        "updated_at": RETRIEVED_AT,
        "variant": item["variant"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    items = rows()
    for family, source in SOURCES.items():
        family_rows = [item for item in items if item["family"] == family]
        parse_ups_rating_matrix(
            extracted_csv(family_rows),
            source_url=str(source["url"]),
            expected_count=len(family_rows),
        )
    records = sorted(
        (build_record(item) for item in items),
        key=lambda record: (str(record["model"]), str(record["variant"])),
    )
    if len(records) != 34 or len({record["record_id"] for record in records}) != 34:
        raise ValueError("Expected 34 unique Makelsan LEVELUPS configurations")
    args.output.write_text("".join(f"{compact(record)}\n" for record in records), encoding="utf-8")
    print("Wrote 34 reviewed Makelsan LEVELUPS configurations")


if __name__ == "__main__":
    main()
