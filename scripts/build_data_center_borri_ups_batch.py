"""Build reviewed Borri current three-phase monolithic UPS configurations."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
from typing import Any

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.inventories import parse_ups_rating_matrix

RETRIEVED_AT = "2026-11-04T04:20:00Z"
AS_OF = "2026-11-04"

SOURCES: dict[str, dict[str, object]] = {
    "INGENIO PLUS": {
        "id": "borri-ingenio-plus-current-20261104",
        "url": "https://www.borri.it/product/ingenio-plus-ups/",
        "publication_date": None,
    },
    "INGENIO MAX": {
        "id": "borri-ingenio-max-current-20261104",
        "url": "https://www.borri.it/product/ingenio-max-ups/",
        "publication_date": None,
        "catalogue_id": "borri-ingenio-max-catalogue-202501",
        "catalogue_url": (
            "https://www.borri.it/pdf/brochure/en/Catalogue_Borri_EN_OMG60326revD_01-25.pdf"
        ),
        "catalogue_publication_date": "2025-01-01",
    },
    "B9000FXS": {
        "id": "borri-b9000fxs-current-20261104",
        "url": "https://www.borri.it/product/b9000fxs/",
        "publication_date": None,
    },
    "B9600FXS": {
        "id": "borri-b9600fxs-current-20261104",
        "url": "https://www.borri.it/product/b9600fxs-ups/",
        "publication_date": None,
    },
}

FAMILIES: dict[str, dict[str, Any]] = {
    "INGENIO PLUS": {
        "ratings": [
            (30, 30, 120),
            (40, 40, 140),
            (60, 60, 190),
            (80, 80, 215),
            (100, 100, 280),
            (125, 125, 290),
            (160, 160, 315),
        ],
        "form_factor": "floor-standing transformer-free three-phase UPS",
        "input": (
            "400 Vac three-phase with neutral rectifier; 380/400/415 Vac "
            "three-phase with neutral bypass; -20%/+20% rectifier and +/-10% bypass"
        ),
        "output": "380/400/415 Vac three-phase with neutral",
        "frequency": "50/60 Hz; 45-65 Hz input range",
        "battery": (
            "30-80 kVA: internal or external 360-372 cell VRLA; "
            "100-160 kVA: external 360-372 cell VRLA; other battery options stated"
        ),
        "efficiency": "Up to 99% AC/AC according to IEC/EN 62040-3; load point not stated",
        "dimensions": (
            "The current table prints 460x650x1230 and 560x940x1500 mm as merged "
            "cabinet cells; exact model binding is not normalized"
        ),
        "overload": "Inverter 110% for 10 min, 125% for 5 min, 150% for 30 s; conditions apply",
        "runtime": {30: 11, 40: 7, 60: 12, 80: 8},
        "internal_battery_weight": {30: 365, 40: 385, 60: 770, 80: 785},
        "locator": "current INGENIO PLUS technical-specification table",
    },
    "INGENIO MAX": {
        "ratings": [
            (200, 200, 530),
            (250, 250, None),
            (300, 300, 675),
            (400, 400, 1080),
            (500, 500, None),
            (600, 600, 1400),
        ],
        "form_factor": "floor-standing transformer-free three-phase UPS",
        "input": (
            "400 Vac three-phase with neutral rectifier; 380/400/415 Vac "
            "three-phase with neutral bypass; -20%/+15% rectifier and +/-10% bypass"
        ),
        "output": "380/400/415 Vac three-phase with neutral",
        "frequency": "50/60 Hz; 45-65 Hz input range",
        "battery": "External 360-372 cell VRLA; OEM also states Ni-Cd and Li-ion compatibility",
        "efficiency": "Up to 99% AC/AC according to IEC/EN 62040-3; load point not stated",
        "dimensions": (
            "The current table prints 880x970x1978, 1430x970x1978 and "
            "1630x970x1978 mm as merged cabinet cells; exact model binding is not normalized"
        ),
        "overload": "Inverter 110% for 10 min, 125% for 5 min, 150% for 30 s",
        "weight_conflicts": {
            250: (745, 630),
            500: (1250, 1150),
        },
        "locator": "current INGENIO MAX technical-specification table",
    },
    "B9000FXS": {
        "ratings": [
            (60, 54, 570),
            (80, 72, 600),
            (100, 90, 625),
            (125, 112.5, 660),
            (160, 144, 715),
            (200, 180, 970),
            (250, 225, 1090),
            (300, 270, 1170),
        ],
        "form_factor": "floor-standing transformer-based three-phase UPS",
        "input": (
            "400 Vac three-phase rectifier; 380/400/415 Vac three-phase with neutral bypass; "
            "-20%/+15% rectifier and +10% bypass"
        ),
        "output": "380/400/415 Vac three-phase with neutral",
        "frequency": "50/60 Hz; 45-65 Hz input range",
        "battery": "External 300-312 cell VRLA; other options stated",
        "efficiency": "Up to 98% AC/AC according to IEC/EN 62040-3; load point not stated",
        "dimensions": (
            "The current table prints 815x825x1670 and 1217x853x1900 mm as merged "
            "cabinet cells; exact model binding is not normalized"
        ),
        "overload": "Inverter 125% for 10 min, 150% for 1 min, 199% for 10 s",
        "locator": "current B9000FXS technical-specification table",
    },
    "B9600FXS": {
        "ratings": [
            (400, 360, 1955, (1990, 950, 1920)),
            (500, 450, 2482, (2440, 950, 2020)),
            (600, 540, 2535, (2440, 950, 2020)),
            (800, 720, 3600, (3640, 950, 1920)),
        ],
        "form_factor": "floor-standing transformer-based three-phase UPS",
        "input": (
            "400 Vac three-phase rectifier; 380/400/415 Vac three-phase with neutral bypass; "
            "-20%/+15% rectifier and +10% bypass"
        ),
        "output": "380/400/415 Vac three-phase with neutral",
        "frequency": "50/60 Hz; 45-65 Hz input range",
        "battery": "External 300-312 cell VRLA; other options stated",
        "efficiency": "Up to 98% AC/AC according to IEC/EN 62040-3; load point not stated",
        "dimensions": "Exact dimensions are printed in each B9600FXS model-rating column",
        "overload": "Inverter 125% for 10 min, 150% for 1 min, 199% for 10 s",
        "locator": "current B9600FXS technical-specification table",
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
        for values in metadata["ratings"]:
            kva, kw, weight, *dimension = values
            dims = dimension[0] if dimension else None
            result.append(
                {
                    "manufacturer": "Borri",
                    "family": family,
                    "model": f"{family} {kva:g} kVA",
                    "variant": f"{kva:g} kVA / {kw:g} kW",
                    "apparent_power_kva": kva,
                    "output_power_kw": kw,
                    "weight_kg": weight,
                    "dimensions": dims,
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
    source_ids = [source_id]
    source_urls = [str(source["url"])]
    publication_date = source.get("publication_date")
    source_dates: dict[str, str | None] = {
        source_id: publication_date if isinstance(publication_date, str) else None
    }
    if family == "INGENIO MAX":
        source_ids.append(str(source["catalogue_id"]))
        source_urls.append(str(source["catalogue_url"]))
        source_dates[str(source["catalogue_id"])] = str(source["catalogue_publication_date"])

    boundary = f"Exact current Borri {family} {kva:g} kVA rating column"
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
    if item["dimensions"] is not None:
        fields.extend(("width_mm", "depth_mm", "height_mm"))

    conflicts: dict[str, list[dict[str, object]]] = {}
    conflict = metadata.get("weight_conflicts", {}).get(int(kva))
    if conflict:
        fields.append("conflicts_json")
        current_weight, catalogue_weight = conflict
        conflicts["weight_kg"] = [
            {
                "boundary": "current official product-page model column",
                "field": "weight_kg",
                "observed_at": RETRIEVED_AT,
                "sources": [source_id],
                "unit": "kg",
                "value": current_weight,
            },
            {
                "boundary": "official January 2025 catalogue model column",
                "field": "weight_kg",
                "observed_at": RETRIEVED_AT,
                "sources": [str(source["catalogue_id"])],
                "unit": "kg",
                "value": catalogue_weight,
            },
        ]

    evidence = {
        field: {
            "confidence": "high",
            "locator": item["locator"],
            "source_publication_dates": source_dates,
        }
        for field in fields
    }
    evidence["apparent_power_kva"]["unit"] = "kVA"
    evidence["output_power_kw"]["unit"] = "kW"
    if "weight_kg" in evidence:
        evidence["weight_kg"]["unit"] = "kg"
    for field in ("width_mm", "depth_mm", "height_mm"):
        if field in evidence:
            evidence[field]["unit"] = "mm"

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
            "maximum_efficiency",
            metadata["efficiency"],
            "%",
            "Family table claim without a published load point; no scalar normalized",
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
            "dimensions_table",
            metadata["dimensions"],
            "mm",
            boundary
            if item["dimensions"] is not None
            else "Merged table cells; no scalar dimensions inferred",
            source_id,
        ),
        observation(item, "overload_capability", metadata["overload"], None, boundary, source_id),
        observation(
            item,
            "communications",
            (
                "Included and optional serial, USB, SNMP, Ethernet and Modbus "
                "interfaces vary by family"
            ),
            None,
            "Family options; no accessory combination synthesized",
            source_id,
        ),
        observation(item, "operating_temperature", "0 to 40", "degC", boundary, source_id),
        observation(
            item,
            "standards_claims",
            "OEM page lists IEC/EN 62040 series, IEC 60529 and CE marking",
            None,
            "OEM conformance statement; not an issuer-registry certification",
            source_id,
        ),
    ]
    runtime = metadata.get("runtime", {}).get(int(kva))
    if runtime is not None:
        observations.append(
            observation(
                item,
                "internal_battery_autonomy",
                runtime,
                "min",
                "Maximum autonomy with internal battery at 70% load; not a generic runtime",
                source_id,
            )
        )
        observations.append(
            observation(
                item,
                "weight_with_internal_battery",
                metadata["internal_battery_weight"][int(kva)],
                "kg",
                "Published internal-battery configuration; separate from base UPS weight",
                source_id,
            )
        )

    record: dict[str, object] = {
        "apparent_power_kva": item["apparent_power_kva"],
        "capacity_scope": (
            f"Exact Borri {family} {kva:g} kVA published rating column; selectable voltage, "
            "battery, communications and parallel options are not synthesized"
        ),
        "created_at": RETRIEVED_AT,
        "entity_type": "equipment",
        "equipment_category": "ups",
        "evidence_json": compact(evidence),
        "field_sources_json": compact({field: source_ids for field in fields}),
        "form_factor": metadata["form_factor"],
        "last_verified_at": RETRIEVED_AT,
        "manufacturer": "Borri",
        "model": item["model"],
        "name": f"Borri {item['model']}",
        "notes": (
            "The exact current OEM rating column is retained. Apparent kVA and active kW "
            "remain separate reported values. Voltage, frequency, batteries, runtime, "
            "communications, parallel arrangements and optional transformers do not create "
            "inferred configurations."
        ),
        "observations_json": compact(observations),
        "official_url": source["url"],
        "output_power_kw": item["output_power_kw"],
        "power_conditions": (
            "Published UPS rated apparent and active output; maximum efficiency lacks a load "
            "point and remains an observation"
        ),
        "power_rating_kind": "rated UPS apparent and active output",
        "product_status": "listed on current official Borri product page as of 2026-11-04",
        "quality_status": "needs_review" if conflict else "source_backed",
        "record_id": stable_id("equipment", "Borri", family, f"{kva:g} kVA"),
        "record_scope": "configuration",
        "source_urls": sorted(source_urls),
        "sources": source_ids,
        "updated_at": RETRIEVED_AT,
        "variant": item["variant"],
    }
    if item["weight_kg"] is not None:
        record["weight_kg"] = item["weight_kg"]
    if item["dimensions"] is not None:
        width, depth, height = item["dimensions"]
        record.update(width_mm=width, depth_mm=depth, height_mm=height)
    if conflicts:
        record["conflicts_json"] = compact(conflicts)
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    items = rows()
    parse_ups_rating_matrix(
        extracted_csv(items),
        source_url="https://www.borri.it/product/ingenio-plus-ups/",
        expected_count=25,
    )
    records = sorted(
        (build_record(item) for item in items),
        key=lambda record: (record["model"], str(record["variant"])),
    )
    if len(records) != 25 or len({record["record_id"] for record in records}) != 25:
        raise ValueError("Expected 25 unique current Borri three-phase UPS configurations")
    args.output.write_text("".join(f"{compact(record)}\n" for record in records), encoding="utf-8")
    print("Wrote 25 reviewed Borri three-phase UPS configurations")


if __name__ == "__main__":
    main()
