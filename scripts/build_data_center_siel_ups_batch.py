"""Build reviewed SIEL Safepower exact UPS rating configurations."""

# ruff: noqa: E501

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
from typing import Any

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.inventories import parse_ups_rating_matrix

RETRIEVED_AT = "2026-11-04T07:18:00Z"
AS_OF = "2026-11-04"

SOURCES = {
    "Safepower S": {
        "id": "siel-safepower-s-br074-rev03-202404",
        "url": "https://www.sielups.com/wp-content/uploads/2024/06/BR074-REV03-BROCHURE-FLYER-SAFEPOWER-S-series.pdf",
        "publication_date": "2024-04-03",
    },
    "Safepower Evo HF": {
        "id": "siel-safepower-evo-hf-br076-rev02-202404",
        "url": "https://www.sielups.com/wp-content/uploads/2024/06/BR076-REV02-BROCHURE-FLYER-SAFEPOWER-EVO-HF.pdf",
        "publication_date": "2024-04-03",
    },
    "Safepower Modular SPM": {
        "id": "siel-safepower-modular-spm-br075-rev03-202404",
        "url": "https://www.sielups.com/wp-content/uploads/2024/06/BR075-REV03-BROCHURE-FLYER-SAFEPOWER-MODULAR-SPM.pdf",
        "publication_date": "2024-04-03",
    },
}

FAMILIES: dict[str, dict[str, Any]] = {
    "Safepower S": {
        "id": "siel-safepower-s-br074-rev03-202404",
        "url": "https://www.sielups.com/wp-content/uploads/2024/06/BR074-REV03-BROCHURE-FLYER-SAFEPOWER-S-series.pdf",
        "revision": "BR074 REV.03",
        "locator": "TECHNICAL DATA / Model and Output Nominal Power table",
        "ratings": [10, 20, 30, 40, 60, 80, 120, 150, 200],
        "weights": [None, None, None, 73, 83, 147, 155, 190, 230],
        "weightAlt": [
            "115/57 kg with/without internal batteries",
            "171/64 kg with/without internal batteries",
            "223/71 kg with/without internal batteries",
            None,
            None,
            None,
            None,
            None,
            None,
        ],
        "form": "floor-standing transformer-free three-phase UPS",
        "input": "380/400/415 Vac three-phase plus neutral; 50/60 Hz",
        "output": "380/400/415 Vac three-phase plus neutral; 50/60 Hz selectable",
        "eff": "up to 96.5% online and up to 99% ECO; exact load points not stated",
        "battery": "Adjustable battery voltage and block-count choices; no energy or runtime inferred",
        "dimensions": "250x900x868, 442x850x1100 and 442x850x1200 mm are printed as merged table groups and are not assigned to individual model columns",
    },
    "Safepower Evo HF": {
        "id": "siel-safepower-evo-hf-br076-rev02-202404",
        "url": "https://www.sielups.com/wp-content/uploads/2024/06/BR076-REV02-BROCHURE-FLYER-SAFEPOWER-EVO-HF.pdf",
        "revision": "BR076 REV.02",
        "locator": "TECHNICAL DATA / Model and Output Nominal Power table",
        "ratings": [10, 20, 30, 40, 60, 80, 100, 120, 160, 200],
        "weights": [None, None, None, None, None, 172, 180, 198, 450, 460],
        "weightAlt": [
            "263/103 kg with/without internal batteries",
            "265/105 kg with/without internal batteries",
            "267/107 kg with/without internal batteries",
            "272/112 kg with/without internal batteries",
            "290/130 kg with/without internal batteries",
            None,
            None,
            None,
            None,
            None,
        ],
        "form": "floor-standing transformer-free three-phase UPS",
        "input": "380/400/415 Vac three-phase plus neutral; 50/60 Hz",
        "output": "380/400/415 Vac three-phase plus neutral; 50/60 Hz selectable",
        "eff": "up to 96.6% online for printed lower-capacity group and up to 96.2% for printed upper-capacity group; up to 99% ECO; exact model/load-point binding not normalized",
        "battery": "Standard VRLA; optional LiFePO4; internal battery and charge-current choices remain observations",
        "dimensions": "440x840x1320, 500x830x1600 and 840x1050x1900 mm are printed as merged table groups and are not assigned to individual model columns",
    },
    "Safepower Modular SPM": {
        "id": "siel-safepower-modular-spm-br075-rev03-202404",
        "url": "https://www.sielups.com/wp-content/uploads/2024/06/BR075-REV03-BROCHURE-FLYER-SAFEPOWER-MODULAR-SPM.pdf",
        "revision": "BR075 REV.03",
        "locator": "FRAME SYSTEM / Size Cabinet in kVA table",
        "ratings": [150, 300, 400, 500, 600, 840, 1080, 1200],
        "weights": [285, 506, 808, 840, 950, 1525, 1750, 1845],
        "modules": [
            "3 x 50 kVA; alternative 2+1 x 60 kVA",
            "6 x 50 kVA; alternative 5 x 60 kVA",
            "8 x 50 kVA; alternative 7+1 x 60 kVA",
            "10 x 50 kVA; alternative 8+2 x 60 kVA",
            "12 x 50 kVA; alternative 10 x 60 kVA",
            "16 x 50 kVA; alternative 14+2 x 60 kVA",
            "20 x 50 kVA; alternative 18+2 x 60 kVA",
            "20 x 60 kVA",
        ],
        "form": "modular transformer-free three-phase UPS cabinet",
        "input": "380/400/415 Vac three-phase plus neutral selectable; 50/60 Hz",
        "output": "380/400/415 Vac three-phase plus neutral selectable; 50/60 Hz",
        "eff": "up to 96.5% online and 99% ECO; exact load points not stated",
        "battery": "Standard VRLA or optional LiFePO4; voltage/block choices remain observations",
        "dimensions": "600x850x1200, 600x850x2000, 1200x850x2000, 2000x850x2000 and 2200x850x2000 mm are printed in merged cells and are not assigned to individual cabinet columns",
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
    result = []
    for family, metadata in FAMILIES.items():
        for index, kva in enumerate(metadata["ratings"]):
            kw = None if family == "Safepower Modular SPM" else kva
            result.append(
                {
                    "manufacturer": "SIEL",
                    "family": family,
                    "model": f"{family} {kva:g} kVA",
                    "variant": f"{kva:g} kVA cabinet" if kw is None else f"{kva:g} kVA / {kw:g} kW",
                    "apparent_power_kva": kva,
                    "output_power_kw": kw,
                    "weight_kg": metadata["weights"][index],
                    "weight_alt": (metadata.get("weightAlt") or [None] * len(metadata["ratings"]))[
                        index
                    ],
                    "module_configuration": (
                        metadata.get("modules") or [None] * len(metadata["ratings"])
                    )[index],
                    "voltage_text": f"input {metadata['input']}; output {metadata['output']}",
                    "frequency_text": "50/60 Hz; retain selectable/range conditions exactly as printed",
                    "locator": f"{metadata['locator']} / {kva:g} kVA column",
                }
            )
    return result


def extracted_csv(items: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for item in items:
        writer.writerow(
            {field: "" if item.get(field) is None else item.get(field, "") for field in CSV_FIELDS}
        )
    return stream.getvalue().encode()


def observation(
    item: dict[str, Any], field: str, value: object, unit: str | None, boundary: str, source_id: str
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
    kva = item["apparent_power_kva"]
    kw = item["output_power_kw"]
    metadata = FAMILIES[family]
    source = SOURCES[family]
    source_id = source["id"]
    boundary = f"Exact SIEL {family} {kva:g} kVA published rating column"
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
        "power_conditions",
        "power_rating_kind",
        "product_status",
        "record_scope",
        "variant",
    ]
    if kw is not None:
        fields.append("output_power_kw")
    if item["weight_kg"] is not None:
        fields.append("weight_kg")
    evidence = {
        field: {
            "confidence": "high",
            "locator": item["locator"],
            "source_publication_dates": {source_id: source["publication_date"]},
        }
        for field in fields
    }
    evidence["apparent_power_kva"]["unit"] = "kVA"
    if kw is not None:
        evidence["output_power_kw"]["unit"] = "kW"
    if item["weight_kg"] is not None:
        evidence["weight_kg"]["unit"] = "kg"
    observations = [
        observation(
            item, "input_voltage_configuration", metadata["input"], "V", boundary, source_id
        ),
        observation(
            item, "output_voltage_configuration", metadata["output"], "V", boundary, source_id
        ),
        observation(
            item,
            "frequency_configuration",
            "50/60 Hz; retain selectable/range conditions exactly as printed",
            "Hz",
            boundary,
            source_id,
        ),
        observation(
            item,
            "efficiency",
            metadata["eff"],
            "%",
            "Family table; no load-point scalar is normalized",
            source_id,
        ),
        observation(
            item,
            "dimensions",
            metadata["dimensions"],
            "mm",
            "Merged family-table cells; no model dimensions normalized",
            source_id,
        ),
        observation(
            item,
            "battery_configuration",
            metadata["battery"],
            None,
            "No battery energy, usable energy or runtime inferred",
            source_id,
        ),
        observation(
            item,
            "overload_capability",
            "110% for 60 min; 125% for 10 min; 150% for 1 min; 1000% for one bypass cycle"
            if family == "Safepower Modular SPM"
            else "110% for 60 min; 125% for 10 min; 150% for 1 min",
            None,
            boundary,
            source_id,
        ),
        observation(
            item,
            "communications",
            "RS-232, RS-485, LAN/Modbus, dry contacts and intelligent-slot options",
            None,
            "Family options; no accessory configuration synthesized",
            source_id,
        ),
        observation(item, "operating_temperature", "0 to 40", "degC", boundary, source_id),
        observation(
            item,
            "standards_claims",
            "OEM brochure lists CE and IEC/EN 62040-1/-2/-3; EN 50171 is an OEM claim",
            None,
            "OEM conformance statement; not an issuer-registry certification",
            source_id,
        ),
    ]
    if item["weight_alt"]:
        observations.append(
            observation(
                item,
                "weight_with_without_internal_batteries",
                item["weight_alt"],
                "kg",
                "Two printed alternatives; normalized weight remains null",
                source_id,
            )
        )
    if item["module_configuration"]:
        observations.append(
            observation(
                item,
                "module_configuration",
                item["module_configuration"],
                None,
                "Printed cabinet module configurations; no module option combination synthesized",
                source_id,
            )
        )
    record = {
        "apparent_power_kva": kva,
        "capacity_scope": f"Exact SIEL {family} {kva:g} kVA published rating column; selectable voltage, frequency, battery, module and communications options are not synthesized",
        "created_at": RETRIEVED_AT,
        "entity_type": "equipment",
        "equipment_category": "ups",
        "evidence_json": compact(evidence),
        "field_sources_json": compact({field: [source_id] for field in fields}),
        "form_factor": metadata["form"],
        "last_verified_at": RETRIEVED_AT,
        "manufacturer": "SIEL",
        "model": item["model"],
        "name": f"SIEL {item['model']}",
        "notes": "The exact cabinet kVA column is retained. Active kW remains null because the frame table does not print cabinet kW. Module alternatives, voltage/frequency, batteries, communications and merged dimensions do not create inferred configurations."
        if family == "Safepower Modular SPM"
        else "The exact OEM kVA/kW column is retained. Apparent kVA and active kW remain separate reported values. Voltage/frequency, batteries, communications, merged dimensions and alternative with/without-battery weights do not create inferred configurations.",
        "observations_json": compact(observations),
        "official_url": source["url"],
        "power_conditions": "Published frame-system cabinet apparent rating; no cabinet active kW inferred from module power factor"
        if family == "Safepower Modular SPM"
        else "Published UPS rated apparent and active output; efficiency remains an observation because exact load point/model binding is not stated",
        "power_rating_kind": "rated UPS cabinet apparent output"
        if family == "Safepower Modular SPM"
        else "rated UPS apparent and active output",
        "product_status": f"listed in official SIEL {metadata['revision']} technical table reviewed 2026-11-04",
        "quality_status": "source_backed",
        "record_id": stable_id("equipment", "SIEL", family, f"{kva:g} kVA"),
        "record_scope": "configuration",
        "source_urls": [source["url"]],
        "sources": [source_id],
        "updated_at": RETRIEVED_AT,
        "variant": item["variant"],
    }
    if kw is not None:
        record["output_power_kw"] = kw
    if item["weight_kg"] is not None:
        record["weight_kg"] = item["weight_kg"]
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    items = rows()
    for family, source in SOURCES.items():
        family_rows = [item for item in items if item["family"] == family]
        parse_ups_rating_matrix(
            extracted_csv(family_rows), source_url=source["url"], expected_count=len(family_rows)
        )
    records = sorted(
        (build_record(item) for item in items),
        key=lambda record: (record["model"], record["variant"]),
    )
    if len(records) != 27 or len({record["record_id"] for record in records}) != 27:
        raise ValueError("Expected 27 unique SIEL Safepower configurations")
    args.output.write_text(
        "\n".join(compact(record) for record in records) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
