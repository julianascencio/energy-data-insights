"""Build reviewed Mitsubishi Electric current UPS rating configurations."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
from typing import Any

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.inventories import parse_ups_rating_matrix

RETRIEVED_AT = "2026-11-03T21:25:00Z"
AS_OF = "2026-11-03"
SOURCE_ID = "mitsubishi-electric-current-ups-comparison-20261103"
SOURCE_URL = "https://mitsubishicritical.com/uninterruptible-power-supplies/"
PUBLICATION_DATE = "2026-07-29"

FAMILIES: dict[str, dict[str, Any]] = {
    "7011B": {
        "voltage_text": "208 V",
        "input_voltage_v": 208,
        "ratings": [(6, 4.2), (8, 5.6), (10, 7.0), (12, 8.4)],
        "dimensions_weight": (
            "13.8 in W x 29.9 in D x 27.8 in H — 298 lb; 13.8 in W x 29.9 in D x 40.6 in H — 496 lb"
        ),
        "efficiency": ">91% AC-to-AC; load condition not stated",
        "batteries": "Internal VRLA; external VRLA",
        "peripherals": "Maintenance Bypass Switch; CS141; RSAP",
        "applications": "Edge/standalone IT racks and light industrial loads",
    },
    "1100A": {
        "voltage_text": "120/208 V",
        "input_voltage_v": None,
        "ratings": [(10, 9), (20, 18), (30, 27), (40, 36), (50, 45)],
        "dimensions_weight": ("19.7 in W x 27.0 in D x 55.1 in H; 290-730 lb family range"),
        "efficiency": "Up to 92.8% AC-to-AC; load condition not stated",
        "batteries": "VRLA; pure lead; internal VRLA for 10 and 20 kVA",
        "peripherals": "Maintenance bypass/transformer/distribution options; CS141; RSAP",
        "applications": "Data-center ancillary loads, edge, IT rooms and emergency lighting",
    },
    "1100B": {
        "voltage_text": "120/208 V",
        "input_voltage_v": None,
        "ratings": [(50, 45), (60, 54), (70, 63), (80, 72)],
        "dimensions_weight": ("31.5 in W x 27.0 in D x 67.3 in H; 499-807 lb family range"),
        "efficiency": "Up to 93.1% AC-to-AC; load condition not stated",
        "batteries": "Lithium-ion; VRLA; pure lead",
        "peripherals": "Maintenance bypass/transformer/distribution options; CS141; RSAP",
        "applications": "Data-center ancillary loads, edge, IT rooms and emergency lighting",
    },
    "9900AEGIS": {
        "voltage_text": "480 V",
        "input_voltage_v": 480,
        "ratings": [(80, 72), (100, 90), (150, 135), (160, 144), (225, 202.5)],
        "dimensions_weight": (
            "Three family cabinet/weight sets: 27.6 x 32.8 x 80.6 in at 772 lb; "
            "27.6 x 32.8 x 80.6 in at 860 lb; 35.4 x 32.8 x 80.6 in at 1080 lb"
        ),
        "efficiency": "Up to 96.6% AC-to-AC; ENERGY STAR claim; load not stated",
        "batteries": "Lithium-ion; VRLA; pure lead; VLA",
        "peripherals": (
            "Maintenance bypass, transformers, DC disconnects, paralleling gear, "
            "CS141, RSAP, LookUPS"
        ),
        "applications": "Data-center ancillary and enterprise/edge computing loads",
    },
    "9900B": {
        "voltage_text": "480 V",
        "input_voltage_v": 480,
        "ratings": [(300, 300), (500, 500), (750, 750)],
        "dimensions_weight": (
            "Three ordered family sets: 55.1 x 32.7 x 80.7 in at 2360 lb; "
            "88.35 x 32.7 x 80.7 in at 3605 lb; 106.9 x 32.7 x 80.7 in at 4525 lb"
        ),
        "efficiency": "Up to 96.5% AC-to-AC; load condition not stated",
        "batteries": "Lithium-ion; VRLA; pure lead; VLA",
        "peripherals": "Maintenance bypass, DC disconnects, paralleling gear, CS141, RSAP, LookUPS",
        "applications": "Enterprise and regional-edge data-center computing loads",
    },
    "SUMMIT Series": {
        "voltage_text": "480 V",
        "input_voltage_v": 480,
        "ratings": [(500, 500), (750, 750)],
        "dimensions_weight": (
            "Two ordered family sets: 79.4 x 33.5 x 80.4 in at 3072 lb; "
            "101.8 x 33.5 x 80.6 in at 4290 lb"
        ),
        "efficiency": "Up to 98.2% AC-to-AC; ENERGY STAR claim; load not stated",
        "batteries": "Lithium-ion; VRLA; pure lead; VLA",
        "peripherals": "Maintenance bypass, DC disconnect, CS141, RSAP, LookUPS",
        "applications": "Colocation, enterprise and regional-edge computing loads",
    },
    "9900CX": {
        "voltage_text": "480 V",
        "input_voltage_v": 480,
        "ratings": [(1050, 1000)],
        "dimensions_weight": "118.1 x 35.4 x 80.7 in; 6613 lb",
        "efficiency": "Up to 97.0% AC-to-AC; load condition not stated",
        "batteries": "Lithium-ion; VRLA; pure lead; VLA",
        "peripherals": "Maintenance bypass, DC disconnect, paralleling gear, RSAP, LookUPS",
        "applications": "Hyperscale and colocation data-center computing loads",
    },
    "9900D": {
        "voltage_text": "480 V",
        "input_voltage_v": 480,
        "ratings": [(1200, 1200), (1250, 1250)],
        "dimensions_weight": "133.9 x 35.4 x 80.7 in; 7270 lb family value",
        "efficiency": "Up to 97.0% AC-to-AC; load condition not stated",
        "batteries": "Lithium-ion; VRLA; pure lead; VLA",
        "peripherals": "Maintenance bypass, DC disconnect, paralleling gear, RSAP, LookUPS",
        "applications": "Hyperscale and colocation data-center computing loads",
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
                    "manufacturer": "Mitsubishi Electric",
                    "family": family,
                    "variant": f"{kva:g} kVA / {kw:g} kW; {metadata['voltage_text']}",
                    "apparent_power_kva": kva,
                    "output_power_kw": kw,
                    "voltage_text": metadata["voltage_text"],
                    "frequency_text": "not stated on current comparison table",
                    "locator": f"current UPS comparison table / {family} / {kva:g} kVA / {kw:g} kW",
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
    metadata = FAMILIES[family]
    locator = str(item["locator"])
    boundary = f"Exact published {family} {item['apparent_power_kva']:g} kVA rating"
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
    if metadata["input_voltage_v"] is not None:
        fields.append("input_voltage_v")
    evidence: dict[str, dict[str, object]] = {
        field: {
            "confidence": "high",
            "locator": locator,
            "source_publication_dates": {SOURCE_ID: PUBLICATION_DATE},
        }
        for field in fields
    }
    evidence["apparent_power_kva"]["unit"] = "kVA"
    evidence["output_power_kw"]["unit"] = "kW"
    if metadata["input_voltage_v"] is not None:
        evidence["input_voltage_v"]["unit"] = "V"
    observations = [
        observation(item, "input_voltage_configuration", item["voltage_text"], "V", boundary),
        observation(
            item,
            "family_dimensions_and_net_weight",
            metadata["dimensions_weight"],
            None,
            "Current family comparison cell; no unprinted rating-to-cabinet binding inferred",
        ),
        observation(
            item,
            "family_ac_to_ac_efficiency",
            metadata["efficiency"],
            None,
            "Current family maximum/threshold claim; load point not supplied",
        ),
        observation(
            item,
            "compatible_battery_types",
            metadata["batteries"],
            None,
            "Compatibility only; no battery model, energy or runtime configuration created",
        ),
        observation(
            item,
            "available_peripherals",
            metadata["peripherals"],
            None,
            "Family options; not selected or combined into this rating configuration",
        ),
        observation(
            item,
            "applications",
            metadata["applications"],
            None,
            "OEM application guidance; not deployment evidence",
        ),
    ]
    record: dict[str, object] = {
        "apparent_power_kva": item["apparent_power_kva"],
        "capacity_scope": (
            f"Exact current OEM {family} apparent/active output rating; optional battery, "
            "bypass, transformer, disconnect, communications and parallel choices excluded"
        ),
        "created_at": RETRIEVED_AT,
        "entity_type": "equipment",
        "equipment_category": "ups",
        "evidence_json": compact(evidence),
        "field_sources_json": compact({field: [SOURCE_ID] for field in fields}),
        "form_factor": "UPS system",
        "last_verified_at": RETRIEVED_AT,
        "manufacturer": "Mitsubishi Electric",
        "model": family,
        "name": f"Mitsubishi Electric {family} {item['apparent_power_kva']:g} kVA",
        "notes": (
            "The comparison table explicitly pairs kVA and kW. Family efficiency, "
            "dimensions/weight, battery compatibility and peripherals remain observations "
            "unless the table supplies an unambiguous rating-level binding."
        ),
        "observations_json": compact(observations),
        "official_url": SOURCE_URL,
        "output_power_kw": item["output_power_kw"],
        "power_conditions": (
            "Current OEM comparison-table rated UPS output; frequency and load-point "
            "conditions are not stated on the comparison page"
        ),
        "power_rating_kind": "rated UPS output apparent and active power",
        "product_status": "listed in current Mitsubishi Electric UPS comparison",
        "quality_status": "source_backed",
        "record_id": stable_id("equipment", "Mitsubishi Electric", family, str(item["variant"])),
        "record_scope": "configuration",
        "source_urls": [SOURCE_URL],
        "sources": [SOURCE_ID],
        "updated_at": RETRIEVED_AT,
        "variant": item["variant"],
    }
    if metadata["input_voltage_v"] is not None:
        record["input_voltage_v"] = metadata["input_voltage_v"]
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    items = rows()
    parse_ups_rating_matrix(extracted_csv(items), source_url=SOURCE_URL, expected_count=26)
    records = sorted(
        (build_record(item) for item in items),
        key=lambda record: (record["model"], record["apparent_power_kva"]),
    )
    if len(records) != 26 or len({record["record_id"] for record in records}) != 26:
        raise ValueError("Expected 26 unique Mitsubishi Electric UPS rating configurations")
    args.output.write_text("".join(f"{compact(record)}\n" for record in records), encoding="utf-8")
    print("Wrote 26 reviewed Mitsubishi Electric current UPS configurations")


if __name__ == "__main__":
    main()
