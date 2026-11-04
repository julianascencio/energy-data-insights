"""Build reviewed KSTAR GP800, MASTER and EPI UPS rating configurations."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
from typing import Any

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.inventories import parse_ups_rating_matrix

RETRIEVED_AT = "2026-11-04T02:30:00Z"
AS_OF = "2026-11-04"
SOURCE_ID = "kstar-transformer-ups-2025-20261104"
SOURCE_URL = "https://www.kstar.com/bocupload/2025/04/03/transfomerbasedups.pdf"
PUBLICATION_DATE = "2025-04-03"

FAMILIES: dict[str, dict[str, Any]] = {
    "GP800": {
        "ratings": [
            ("GP801", 1, 0.8, None),
            ("GP802", 2, 1.6, None),
            ("GP803", 3, 2.4, None),
            ("GP804", 4, 3.2, None),
            ("GP806", 6, 4.8, None),
            ("GP808", 8, 6.4, None),
            ("GP810", 10, 8, None),
            ("GP812", 12, 9.6, 115),
            ("GP815", 15, 12, 130),
            ("GP820", 20, 16, 145),
        ],
        "input": "220/230 V nominal; 165-275 V range; single phase",
        "output": "220/230 V +/-0.5%; single phase",
        "frequency": "50/60 Hz +/-5% input; 50/60 Hz +/-0.5% output",
        "efficiency": (
            "Published GP800 efficiency row has shared cells whose exact model binding is ambiguous"
        ),
        "dimensions": (
            "Published GP800 dimensions use shared standard/long-run groups; no exact "
            "model-to-group binding normalized"
        ),
        "battery": (
            "Published standard/long-run DC-voltage and internal-battery rows use shared "
            "cells; no battery configuration or runtime inferred"
        ),
        "weights": (
            "GP801-GP810 publish standard/long-run paired net weights (80/32, 85/36, "
            "99/40, 102/45, 108/50, 110/60, 115/65 kg); GP812, GP815 and GP820 print "
            "single 115, 130 and 145 kg values"
        ),
        "locator": "GP800 specification table / model column",
    },
    "MASTER": {
        "ratings": [
            ("M6K", 6, 4.8, 100),
            ("M8K", 8, 6.4, 110),
            ("M10K", 10, 8, 115),
            ("M15K", 15, 12, 130),
            ("M20K", 20, 16, 145),
            ("M30K", 30, 24, 205),
            ("M40K", 40, 32, 255),
        ],
        "input": "380/400 V +/-20%; 3-phase plus neutral and protective earth",
        "output": "220/230 V +/-0.5%; single phase",
        "frequency": "50/60 Hz +/-5% input; 50/60 Hz +/-0.5% output",
        "efficiency": (
            "Up to 86% / up to 88% shared efficiency cells; exact rating binding is ambiguous"
        ),
        "dimensions": (
            "305 x 585 x 864 mm and 350 x 650 x 1050 mm are shared table groups; no "
            "exact model binding normalized"
        ),
        "battery": (
            "192/240 V DC shared table groups; no exact model binding, battery energy "
            "or runtime normalized"
        ),
        "weights": "Exact model-column net weights",
        "locator": "MASTER specification table / model column",
    },
    "EPI": {
        "ratings": [
            ("EPI 8K", 8, 6.4, 110),
            ("EPI 10K", 10, 8, 115),
            ("EPI 15K", 15, 12, 130),
            ("EPI 20K", 20, 16, 145),
            ("EPI 30K", None, 24, 205),
            ("EPI 40K", 40, 32, 255),
        ],
        "input": "380/400 V +/-20%; 3-phase plus neutral and protective earth",
        "output": "220 V +/-1%; single phase",
        "frequency": "50/60 Hz +/-5% input; 50/60 Hz +/-0.5% output",
        "efficiency": (
            "Published EPI efficiency row uses shared cells whose exact rating binding is ambiguous"
        ),
        "dimensions": (
            "Published EPI dimensions use shared groups; no exact model-to-group binding normalized"
        ),
        "battery": (
            "Published DC-voltage row uses shared groups; no exact model binding, battery "
            "energy or runtime normalized"
        ),
        "weights": "Exact model-column net weights",
        "locator": "EPI specification table / model column",
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
            printed_kva = "3" if model == "EPI 30K" else f"{kva:g}"
            result.append(
                {
                    "manufacturer": "KSTAR",
                    "family": family,
                    "model": model,
                    "variant": (
                        f"{printed_kva} kVA / {kw:g} kW published column"
                        if model == "EPI 30K"
                        else f"{kva:g} kVA / {kw:g} kW"
                    ),
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
    if item["apparent_power_kva"] is not None:
        fields.append("apparent_power_kva")
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
    evidence["output_power_kw"]["unit"] = "kW"
    if "apparent_power_kva" in evidence:
        evidence["apparent_power_kva"]["unit"] = "kVA"
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
            "Shared table cells; no exact model-level scalar inferred",
        ),
        observation(
            item,
            "dimensions_table_cells",
            metadata["dimensions"],
            None,
            "Shared table cells; no exact model-level dimensions inferred",
        ),
        observation(
            item,
            "battery_table_cells",
            metadata["battery"],
            None,
            "No battery energy, usable energy or runtime configuration inferred",
        ),
        observation(item, "weight_table", metadata["weights"], "kg", boundary),
        observation(
            item,
            "communications",
            "RS232 standard; RS485, EPO, dry contact and SNMP are optional",
            None,
            "Family options; not selected or synthesized",
        ),
        observation(item, "operating_temperature", "0 to 40", "degC", boundary),
        observation(item, "storage_temperature", "-25 to 55", "degC", boundary),
        observation(
            item,
            "standards_claims",
            "OEM brochure lists applicable safety and EMC standards",
            None,
            "OEM conformance statement; not an issuer-registry certification",
        ),
    ]
    if model == "EPI 30K":
        observations.append(
            observation(
                item,
                "printed_apparent_power",
                3,
                "kVA",
                "EPI 30K column prints 3 kVA alongside 24 kW; unresolved source inconsistency",
            )
        )
    record: dict[str, object] = {
        "capacity_scope": (
            f"Exact KSTAR {family} {model} published rating column; voltage, frequency, "
            "battery, communications and shared-cell options are not synthesized"
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
            "voltages, frequencies, batteries, runtime, communications and shared table cells "
            "do not create inferred configurations."
        ),
        "observations_json": compact(observations),
        "official_url": SOURCE_URL,
        "output_power_kw": item["output_power_kw"],
        "power_conditions": (
            "Published transformer-based UPS output rating; voltage/frequency choices and "
            "efficiency load conditions remain observations"
        ),
        "power_rating_kind": (
            "rated UPS active output; apparent rating quarantined"
            if model == "EPI 30K"
            else "rated UPS apparent and active output"
        ),
        "product_status": "listed in current 2025 KSTAR transformer-based UPS brochure",
        "quality_status": "needs_review" if model == "EPI 30K" else "source_backed",
        "record_id": stable_id("equipment", "KSTAR", model, str(item["variant"])),
        "record_scope": "configuration",
        "source_urls": [SOURCE_URL],
        "sources": [SOURCE_ID],
        "updated_at": RETRIEVED_AT,
        "variant": item["variant"],
    }
    if item["apparent_power_kva"] is not None:
        record["apparent_power_kva"] = item["apparent_power_kva"]
    if item["weight_kg"] is not None:
        record["weight_kg"] = item["weight_kg"]
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    items = rows()
    parse_ups_rating_matrix(extracted_csv(items), source_url=SOURCE_URL, expected_count=23)
    records = sorted(
        (build_record(item) for item in items),
        key=lambda record: (record["model"], str(record["variant"])),
    )
    if len(records) != 23 or len({record["record_id"] for record in records}) != 23:
        raise ValueError("Expected 23 unique KSTAR GP800, MASTER and EPI configurations")
    args.output.write_text("".join(f"{compact(record)}\n" for record in records), encoding="utf-8")
    print("Wrote 23 reviewed KSTAR transformer-based UPS configurations")


if __name__ == "__main__":
    main()
