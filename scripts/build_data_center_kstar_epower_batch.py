"""Build reviewed KSTAR EPOWER, EPOWER-L and EPOWER-H UPS configurations."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
from typing import Any

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.inventories import parse_ups_rating_matrix

RETRIEVED_AT = "2026-11-04T03:30:00Z"
AS_OF = "2026-11-04"
SOURCE_ID = "kstar-transformer-ups-2025-20261104"
SOURCE_URL = "https://www.kstar.com/bocupload/2025/04/03/transfomerbasedups.pdf"
PUBLICATION_DATE = "2025-04-03"

# One row per printed model column. A null weight means the brochure prints multiple
# pole-count alternatives without an exact orderable suffix for that model column.
FAMILIES: dict[str, dict[str, Any]] = {
    "EPOWER": {
        "ratings": [
            ("EP10", 10, 9, 145),
            ("EP20", 20, 18, 165),
            ("EP30", 30, 27, 204),
            ("EP40", 40, 36, 255),
            ("EP60", 60, 54, 320),
            ("EP80", 80, 72, 450),
            ("EP100", 100, 90, None),
            ("EP120", 120, 108, None),
            ("EP160", 160, 144, None),
            ("EP200", 200, 180, None),
            ("EP300", 300, 270, None),
            ("EP400", 400, 360, None),
            ("EP500-12P", 500, 450, 3510),
            ("EP600-12P", 600, 540, 3950),
            ("EP800-12P", 800, 720, 4950),
        ],
        "input": "380/400/415 V (-25%/+20%); 3-phase plus protective earth",
        "output": "380/400/415 V +/-1%; 3-phase plus neutral and protective earth",
        "frequency": "50/60 Hz +/-5% input; 50/60 Hz +/-0.05% output",
        "battery": (
            "10-160 kVA table prints 384 V DC (360-384 V); 200-400 kVA table "
            "prints 384 V DC (360-408 V), EP500/EP600 480 V shared, and EP800 600 V"
        ),
        "efficiency": (
            "Published EPOWER maximum-efficiency row uses shared cells from up to 88% "
            "through up to 94%; no exact scalar is assigned where merged-cell binding is unclear"
        ),
        "dimensions": (
            "Published dimensions include shared cabinet groups and 6P/12P alternatives; "
            "no exact dimensions are normalized"
        ),
        "weights": (
            "EP10-EP80 have one printed net weight; EP100-EP400 print 6P/12P alternatives; "
            "EP500-12P, EP600-12P and EP800-12P have one printed net weight"
        ),
        "communications": "RS232 and RS485; EPO, dry contacts and SNMP are listed as options",
        "storage_temperature": "-25 to 55",
        "locator": "EPOWER technical specification table / model column",
    },
    "EPOWER-L": {
        "ratings": [
            ("EP10-L", 10, 8, 145),
            ("EP20-L", 20, 16, 155),
            ("EP30-L", 30, 24, 190),
            ("EP40-L", 40, 32, 242),
            ("EP60-L", 60, 48, 315),
            ("EP80-L", 80, 64, 365),
            ("EP100-L", 100, 80, 420),
            ("EP120-L", 120, 96, 635),
            ("EP160-L", 160, 128, 740),
        ],
        "input": "380/400/415 V (-25%/+20%); 3-phase plus protective earth",
        "output": "380/400/415 V +/-1%; 3-phase plus neutral and protective earth",
        "frequency": "50/60 Hz +/-5% input; 50/60 Hz +/-0.05% output",
        "battery": "384 V DC (360-384 V) shared family table cell",
        "efficiency": (
            "Published EPOWER-L maximum-efficiency row uses shared cells from up to 88% "
            "through up to 92.5%; no exact scalar is assigned where merged-cell binding is unclear"
        ),
        "dimensions": (
            "Published EPOWER-L dimensions use four shared cabinet groups; no exact model "
            "dimensions are normalized"
        ),
        "weights": "Exact net weight printed in each model column",
        "communications": "RS232 and RS485; EPO, dry contacts and SNMP are listed as options",
        "storage_temperature": "-25 to 55",
        "locator": "EPOWER-L technical specification table / model column",
    },
    "EPOWER-H": {
        "ratings": [
            ("EP10-H", 10, 9, 270),
            ("EP20-H", 20, 18, 300),
            ("EP30-H", 30, 27, 340),
            ("EP40-H", 40, 36, 365),
            ("EP60-H", 60, 54, 555),
            ("EP80-H", 80, 72, 625),
            ("EP100-H", 100, 90, 710),
            ("EP120-H", 120, 108, 925),
            ("EP160-H", 160, 144, 1065),
            ("EP200-H", 200, 180, 1260),
            ("EP300-H", 300, 270, 1650),
            ("EP400-H", 400, 360, 2150),
            ("EP500-H", 500, 450, 2800),
            ("EP600-H", 600, 540, 2960),
        ],
        "input": (
            "380/400/415 V nominal; 346-456 V range; 3-phase plus protective earth without neutral"
        ),
        "output": "380/400/415 V +/-1%; 3-phase plus neutral and protective earth",
        "frequency": "50/60 Hz nominal; 45-65 Hz input range; 50/60 Hz +/-0.05% output",
        "battery": "600 V DC shared family table cell; no battery energy or runtime stated",
        "efficiency": (
            "Published EPOWER-H maximum-efficiency row uses shared cells from up to 88% "
            "through up to 93.5%; no exact scalar is assigned where merged-cell binding is unclear"
        ),
        "dimensions": (
            "Published dimensions contain repeated or merged cabinet cells; exact values remain "
            "observations rather than normalized dimensions"
        ),
        "weights": "Exact net weight printed in each model column",
        "communications": "USB, RS485 and EPO; dry contacts and SNMP are listed as options",
        "storage_temperature": "-25 to 55 below 200 kVA; -20 to 55 from 200 kVA, without battery",
        "locator": "EPOWER-H technical specification table / model column",
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
        for model, kva, kw, weight in metadata["ratings"]:
            result.append(
                {
                    "manufacturer": "KSTAR",
                    "family": family,
                    "model": model,
                    "variant": f"{kva:g} kVA / {kw:g} kW",
                    "apparent_power_kva": kva,
                    "output_power_kw": kw,
                    "voltage_text": f"input {metadata['input']}; output {metadata['output']}",
                    "frequency_text": metadata["frequency"],
                    "locator": f"{metadata['locator']} {model}",
                    "weight_kg": weight,
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
    item: dict[str, Any], field: str, value: object, unit: str | None, boundary: str
) -> dict[str, object]:
    return {
        "as_of": AS_OF,
        "boundary": boundary,
        "field": field,
        "kind": "reported",
        "locator": item["locator"],
        "source_id": SOURCE_ID,
        "unit": unit,
        "value": value,
    }


def build_record(item: dict[str, Any]) -> dict[str, object]:
    family = str(item["family"])
    model = str(item["model"])
    metadata = FAMILIES[family]
    boundary = f"Exact published {family} {model} model column"
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
    if item["weight_kg"] is not None:
        fields.append("weight_kg")
    evidence: dict[str, dict[str, object]] = {
        field: {
            "confidence": "high",
            "locator": item["locator"],
            "source_publication_dates": {SOURCE_ID: PUBLICATION_DATE},
        }
        for field in fields
    }
    evidence["apparent_power_kva"]["unit"] = "kVA"
    evidence["output_power_kw"]["unit"] = "kW"
    if "weight_kg" in evidence:
        evidence["weight_kg"]["unit"] = "kg"
    observations = [
        observation(item, "input_voltage_configuration", metadata["input"], "V", boundary),
        observation(item, "output_voltage_configuration", metadata["output"], "V", boundary),
        observation(item, "frequency_configuration", metadata["frequency"], "Hz", boundary),
        observation(
            item,
            "efficiency_table_cells",
            metadata["efficiency"],
            None,
            "Shared table cells; no exact model-level efficiency scalar inferred",
        ),
        observation(
            item,
            "dimensions_table_cells",
            metadata["dimensions"],
            None,
            "Merged/shared cells; no exact model-level dimensions inferred",
        ),
        observation(
            item,
            "battery_table_cells",
            metadata["battery"],
            "Vdc",
            "No battery energy, usable energy or runtime configuration inferred",
        ),
        observation(item, "weight_table", metadata["weights"], "kg", boundary),
        observation(
            item,
            "communications",
            metadata["communications"],
            None,
            "Family options; not selected or synthesized",
        ),
        observation(item, "operating_temperature", "0 to 40", "degC", boundary),
        observation(
            item,
            "storage_temperature",
            metadata["storage_temperature"],
            "degC",
            boundary,
        ),
        observation(
            item,
            "standards_claims",
            "OEM brochure lists applicable IEC/EN 62040 and IEC/EN 62477 standards",
            None,
            "OEM conformance statement; not an issuer-registry certification",
        ),
    ]
    record: dict[str, object] = {
        "apparent_power_kva": item["apparent_power_kva"],
        "capacity_scope": (
            f"Exact KSTAR {family} {model} published rating column; voltage, frequency, "
            "battery, communications and merged-cell options are not synthesized"
        ),
        "created_at": RETRIEVED_AT,
        "entity_type": "equipment",
        "equipment_category": "ups",
        "evidence_json": compact(evidence),
        "field_sources_json": compact({field: [SOURCE_ID] for field in fields}),
        "form_factor": "transformer-based UPS system",
        "last_verified_at": RETRIEVED_AT,
        "manufacturer": "KSTAR",
        "model": model,
        "name": f"KSTAR {model}",
        "notes": (
            "The exact OEM model column is retained. kVA and kW stay separate; selectable "
            "voltages, frequencies, batteries, runtime, communications and merged table cells "
            "do not create inferred configurations."
        ),
        "observations_json": compact(observations),
        "official_url": SOURCE_URL,
        "output_power_kw": item["output_power_kw"],
        "power_conditions": (
            "Published transformer-based UPS output rating; voltage/frequency choices and "
            "efficiency load conditions remain observations"
        ),
        "power_rating_kind": "rated UPS apparent and active output",
        "product_status": "listed in current 2025 KSTAR transformer-based UPS brochure",
        "quality_status": "source_backed",
        "record_id": stable_id("equipment", "KSTAR", model, str(item["variant"])),
        "record_scope": "configuration",
        "source_urls": [SOURCE_URL],
        "sources": [SOURCE_ID],
        "updated_at": RETRIEVED_AT,
        "variant": item["variant"],
    }
    if item["weight_kg"] is not None:
        record["weight_kg"] = item["weight_kg"]
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    items = rows()
    parse_ups_rating_matrix(extracted_csv(items), source_url=SOURCE_URL, expected_count=38)
    records = sorted(
        (build_record(item) for item in items),
        key=lambda record: (record["model"], str(record["variant"])),
    )
    if len(records) != 38 or len({record["record_id"] for record in records}) != 38:
        raise ValueError("Expected 38 unique KSTAR EPOWER, EPOWER-L and EPOWER-H records")
    args.output.write_text("".join(f"{compact(record)}\n" for record in records), encoding="utf-8")
    print("Wrote 38 reviewed KSTAR EPOWER-family UPS configurations")


if __name__ == "__main__":
    main()
