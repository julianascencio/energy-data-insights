"""Build reviewed Tescom exact UPS rating configurations."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
from typing import Any

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.inventories import parse_ups_rating_matrix

RETRIEVED_AT = "2026-11-04T08:32:00Z"
AS_OF = "2026-11-04"

SOURCES = {
    "DS POWER 300HT": {
        "id": "tescom-ds-power-300ht-current-20261104",
        "url": "https://www.tescom-ups.com/es/producto/ds-power-300ht-8",
    },
    "DS POWER": {
        "id": "tescom-ds-power-500-600-current-20261104",
        "url": "https://www.tescom-ups.com/es/producto/ds-power-5",
    },
    "DS POWER SH": {
        "id": "tescom-ds-power-sh-current-20261104",
        "url": "https://www.tescom-ups.com/es/producto/ds-power-sh-38",
    },
    "MTI250": {
        "id": "tescom-mti250-current-20261104",
        "url": "https://www.tescom-ups.com/es/producto/mti250-modular-ups-82",
    },
}

DS300HT = [
    ("DS310HT", 10, 9, 187, (400, 815, 1040)),
    ("DS315HT", 15, 13.5, 198.5, (400, 815, 1040)),
    ("DS320HT", 20, 18, 244, (400, 815, 1040)),
    ("DS330HT", 30, 27, 270, (400, 815, 1040)),
    ("DS340HT", 40, 36, 393, (515, 855, 1440)),
    ("DS360HT", 60, 54, 457, (515, 855, 1440)),
    ("DS380HT", 80, 72, 536, (515, 855, 1440)),
    ("DS3100HT", 100, 90, 539, (825, 855, 1770)),
    ("DS3120HT", 120, 108, 595, (825, 855, 1770)),
    ("DS3160HT", 160, 144, 647, (825, 855, 1770)),
    ("DS3200HT", 200, 180, 910.5, (825, 855, 1770)),
    ("DS3250HT", 250, 225, 1150, (1250, 1055, 1900)),
    ("DS3300HT", 300, 270, 1283, (1250, 1055, 1900)),
    ("DS3400HT", 400, 360, 1497, (1250, 1055, 1900)),
    ("DS3500HT", 500, 400, 2402, (2020, 2250, 770)),
]

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
    for model, kva, kw, weight, dimensions in DS300HT:
        result.append(
            {
                "family": "DS POWER 300HT",
                "model": model,
                "kva": kva,
                "kw": kw,
                "weight": weight,
                "dimensions": dimensions,
                "form": "floor-standing transformer-based three-phase UPS",
                "efficiency": "up to 94% at 100% load",
                "locator": f"current product technical table / {kva:g} kVA model",
            }
        )
    for kva in (500, 600):
        result.append(
            {
                "family": "DS POWER",
                "model": f"DS POWER {kva:g} kVA",
                "kva": kva,
                "kw": kva,
                "weight": 1452,
                "dimensions": (1610, 1050, 1940),
                "form": "floor-standing transformer-based three-phase UPS",
                "efficiency": "up to 95% at 100% load",
                "locator": f"current 500-600 kVA product technical table / {kva:g} kVA model",
            }
        )
    for model, kva, kw, weight in (
        ("DS310SH", 10, 9, 47.5),
        ("DS315SH", 15, 13.5, 49.5),
        ("DS320SH", 20, 18, 51),
    ):
        result.append(
            {
                "family": "DS POWER SH",
                "model": model,
                "kva": kva,
                "kw": kw,
                "weight": weight,
                "dimensions": None,
                "dimension_options": (
                    "700x300x770 mm without batteries; 1000x300x800 mm with 5 Ah "
                    "batteries; 1170x300x800 mm with 7-9 Ah batteries"
                ),
                "form": "floor-standing transformer-free three-phase UPS",
                "efficiency": "94% at 100% load",
                "locator": f"current 10-20 kVA product technical table / {kva:g} kVA model",
            }
        )
    for kva, weight, dimensions, dual_input in (
        (150, 140, (931, 482, 916), "optional"),
        (200, 160, (1550, 482, 916), "standard"),
    ):
        result.append(
            {
                "family": "MTI250",
                "model": f"MTI250 {kva:g} kVA cabinet",
                "kva": kva,
                "kw": kva,
                "weight": weight,
                "dimensions": dimensions,
                "form": "modular rack-format three-phase UPS cabinet",
                "efficiency": "96% AC mode; 98% ECO mode; 95.5% battery mode",
                "dual_input": dual_input,
                "locator": f"current MTI250 product technical table / {kva:g} kVA cabinet",
            }
        )
    return result


def extracted_csv(items: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for item in items:
        writer.writerow(
            {
                "manufacturer": "Tescom",
                "family": item["family"],
                "variant": f"{item['model']}; {item['kva']:g} kVA / {item['kw']:g} kW",
                "apparent_power_kva": item["kva"],
                "output_power_kw": item["kw"],
                "voltage_text": "380/400 Vac three-phase plus neutral and ground; 415 Vac optional",
                "frequency_text": "50/60 Hz; retain published input tolerance/range",
                "locator": item["locator"],
            }
        )
    return stream.getvalue().encode()


def observation(
    item: dict[str, Any], field: str, value: object, unit: str | None, boundary: str
) -> dict[str, object]:
    source_id = SOURCES[item["family"]]["id"]
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
    family = item["family"]
    source = SOURCES[family]
    source_id = source["id"]
    boundary = f"Exact Tescom {item['model']} published rating row"
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
        "weight_kg",
    ]
    if item["dimensions"] is not None:
        fields.extend(["height_mm", "width_mm", "depth_mm"])
    evidence = {
        field: {
            "confidence": "high",
            "locator": item["locator"],
            "source_publication_dates": {source_id: None},
        }
        for field in fields
    }
    for field, unit in {
        "apparent_power_kva": "kVA",
        "output_power_kw": "kW",
        "weight_kg": "kg",
        "height_mm": "mm",
        "width_mm": "mm",
        "depth_mm": "mm",
    }.items():
        if field in evidence:
            evidence[field]["unit"] = unit
    observations = [
        observation(
            item,
            "input_voltage_configuration",
            "380/400 Vac three-phase plus neutral and ground; 415 Vac optional",
            "V",
            boundary,
        ),
        observation(
            item,
            "output_voltage_configuration",
            "380/400 Vac three-phase plus neutral; 415 Vac optional",
            "V",
            boundary,
        ),
        observation(
            item,
            "frequency_configuration",
            "50/60 Hz; published input tolerance/range retained without selecting a frequency",
            "Hz",
            boundary,
        ),
        observation(
            item,
            "efficiency",
            item["efficiency"],
            "%",
            "Published mode/load statement; not normalized as a generic efficiency scalar",
        ),
        observation(
            item,
            "battery_configuration",
            (
                "Family table lists VRLA AGM, GEL and NiCd choices; battery voltage/block "
                "choices are retained without inferring energy or runtime"
                if family != "MTI250"
                else (
                    "40 blocks stated; even 32-44 block setting range; no energy or "
                    "runtime inferred"
                )
            ),
            None,
            "Family/model table; no battery SKU synthesized",
        ),
        observation(
            item,
            "communications",
            (
                "RS-232 and dry contacts; RS-485, SNMP, Modbus and remote-panel options"
                if family != "MTI250"
                else "RS-232, RS-485 and programmable dry contacts; SNMP optional"
            ),
            None,
            "Published interfaces/options; no accessory configuration synthesized",
        ),
        observation(item, "operating_temperature", "0 to 40", "degC", boundary),
        observation(
            item,
            "standards_claims",
            "OEM table lists EN/IEC 62040-1, -2 and -3",
            None,
            "OEM conformance statement; not an issuer-registry certification",
        ),
    ]
    if item.get("dimension_options"):
        observations.append(
            observation(
                item,
                "dimension_options",
                item["dimension_options"],
                "mm",
                "Battery-qualified alternatives; no scalar dimensions normalized",
            )
        )
    if family == "MTI250":
        observations.extend(
            [
                observation(
                    item,
                    "power_module",
                    "TPM25C 25 kVA / 25 kW module",
                    None,
                    "Published module type; module combinations are not synthesized",
                ),
                observation(
                    item,
                    "dual_input",
                    item["dual_input"],
                    None,
                    boundary,
                ),
            ]
        )
    record: dict[str, object] = {
        "apparent_power_kva": item["kva"],
        "capacity_scope": (
            f"Exact Tescom {item['model']} published rating row; voltage, frequency, "
            "battery, communications and module options are not synthesized"
        ),
        "created_at": RETRIEVED_AT,
        "entity_type": "equipment",
        "equipment_category": "ups",
        "evidence_json": compact(evidence),
        "field_sources_json": compact({field: [source_id] for field in fields}),
        "form_factor": item["form"],
        "last_verified_at": RETRIEVED_AT,
        "manufacturer": "Tescom",
        "model": item["model"],
        "name": f"Tescom {item['model']}",
        "notes": (
            "The exact OEM model/cabinet rating is retained. Apparent kVA and active kW "
            "remain separate reported values. Optional electrical, battery, communications "
            "and modular choices do not create inferred configurations."
        ),
        "observations_json": compact(observations),
        "official_url": source["url"],
        "output_power_kw": item["kw"],
        "power_conditions": (
            "Published UPS rated apparent and active output; efficiency remains a "
            "mode/load-qualified observation"
        ),
        "power_rating_kind": "rated UPS apparent and active output",
        "product_status": "listed in current official Tescom product table reviewed 2026-11-04",
        "quality_status": "source_backed",
        "record_id": stable_id("equipment", "Tescom", family, item["model"]),
        "record_scope": "configuration",
        "source_urls": [source["url"]],
        "sources": [source_id],
        "updated_at": RETRIEVED_AT,
        "variant": f"{item['kva']:g} kVA / {item['kw']:g} kW",
        "weight_kg": item["weight"],
    }
    if item["dimensions"] is not None:
        height, width, depth = item["dimensions"]
        record.update({"height_mm": height, "width_mm": width, "depth_mm": depth})
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    items = rows()
    for family, source in SOURCES.items():
        family_rows = [item for item in items if item["family"] == family]
        parse_ups_rating_matrix(
            extracted_csv(family_rows),
            source_url=source["url"],
            expected_count=len(family_rows),
        )
    records = sorted(
        (build_record(item) for item in items),
        key=lambda record: (str(record["model"]), str(record["variant"])),
    )
    if len(records) != 22 or len({record["record_id"] for record in records}) != 22:
        raise ValueError("Expected 22 unique Tescom UPS configurations")
    args.output.write_text("".join(f"{compact(record)}\n" for record in records), encoding="utf-8")
    print("Wrote 22 reviewed Tescom UPS configurations")


if __name__ == "__main__":
    main()
