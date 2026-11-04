"""Build reviewed Daikin EWAT-CZ 2026 chiller rating configurations."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
from typing import Any

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.inventories import (
    parse_precision_cooling_matrix,
)

RETRIEVED_AT = "2026-11-03T23:24:00Z"
AS_OF = "2026-11-03"
SOURCE_ID = "daikin-chillers-catalogue-2026-ecpen26-411"
SOURCE_URL = (
    "https://www.daikin.eu/content/dam/internet-denv/catalogues_brochures/"
    "industrial/Chillers_Catalogue_2026-ECPEN26-411.pdf"
)
RATING = "Cooling: entering water 12 degC; leaving water 7 degC; ambient 35 degC dry bulb"
SIZES = ("016", "021", "025", "032", "040-MONO", "040-DUAL", "050", "064", "090")
FLOW_L_S = (0.8, 1.0, 1.2, 1.6, 1.9, 2.0, 2.4, 3.1, 4.2)
MINIMUM_CAPACITY_PCT = (18, 14, 12, 19, 15, 14, 12, 15, 14)
IPLV = (5.83, 6.29, 6.05, 6.25, 5.87, 6.37, 5.92, 5.88, 5.61)
FAMILIES = {
    "EWAT-CZN": {
        "cooling": (15.9, 20.9, 25.6, 32.4, 39.6, 41.4, 50.8, 64.0, 88.3),
        "input": (5.50, 6.60, 8.50, 10.3, 13.4, 13.2, 17.0, 21.8, 31.0),
        "eer": (2.90, 3.16, 3.00, 3.13, 2.95, 3.12, 2.98, 2.93, 2.84),
    },
    "EWAT-CZP": {
        "cooling": (16.1, 21.1, 25.9, 32.7, 39.9, 41.7, 51.1, 64.4, 88.8),
        "input": (5.45, 6.56, 8.48, 10.3, 13.3, 13.2, 16.9, 21.9, 31.1),
        "eer": (2.96, 3.22, 3.05, 3.18, 3.00, 3.17, 3.03, 2.95, 2.85),
    },
    "EWAT-CZH": {
        "cooling": (16.2, 21.2, 25.9, 32.8, 40.1, 41.8, 51.3, 64.5, 88.9),
        "input": (5.60, 6.70, 8.70, 10.4, 13.5, 13.3, 17.0, 22.0, 31.2),
        "eer": (2.89, 3.15, 2.98, 3.14, 2.97, 3.15, 3.02, 2.93, 2.85),
    },
}
CSV_FIELDS = [
    "manufacturer",
    "model",
    "variant",
    "category",
    "cooling_capacity_kw",
    "cooling_rating_conditions",
    "airflow_m3_h",
    "input_power_kw",
    "input_current_a",
    "liquid_flow_l_min",
    "width_mm",
    "height_mm",
    "depth_mm",
    "weight_kg",
    "locator",
]


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def rows() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for family, ratings in FAMILIES.items():
        for index, size in enumerate(SIZES):
            result.append(
                {
                    "manufacturer": "Daikin",
                    "model": family,
                    "variant": f"{size}; cooling-only nominal rating",
                    "category": "chiller",
                    "cooling_capacity_kw": ratings["cooling"][index],
                    "cooling_rating_conditions": RATING,
                    "input_power_kw": ratings["input"][index],
                    "liquid_flow_l_min": FLOW_L_S[index] * 60,
                    "locator": f"{family} specification table / size {size}",
                    "size": size,
                    "flow_l_s": FLOW_L_S[index],
                    "minimum_capacity_pct": MINIMUM_CAPACITY_PCT[index],
                    "eer": ratings["eer"][index],
                    "iplv": IPLV[index],
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
    item: dict[str, Any], field: str, value: object, unit: str | None
) -> dict[str, object]:
    return {
        "as_of": AS_OF,
        "boundary": f"Exact {item['model']} size {item['size']} catalogue rating",
        "field": field,
        "kind": "reported",
        "locator": item["locator"],
        "source_id": SOURCE_ID,
        "unit": unit,
        "value": value,
    }


def build_record(item: dict[str, Any]) -> dict[str, object]:
    fields = [
        "capacity_scope",
        "cooling_capacity_kw",
        "cooling_rating_conditions",
        "equipment_category",
        "form_factor",
        "input_power_kw",
        "liquid_flow_l_min",
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
    units = {
        "cooling_capacity_kw": "kW",
        "input_power_kw": "kW",
        "liquid_flow_l_min": "L/min",
    }
    evidence: dict[str, dict[str, object]] = {}
    for field in fields:
        evidence[field] = {
            "confidence": "high",
            "locator": item["locator"],
            "source_publication_dates": {SOURCE_ID: None},
        }
        if field in units:
            evidence[field]["unit"] = units[field]
    observations = [
        observation(item, "nominal_water_flow", item["flow_l_s"], "L/s"),
        observation(item, "minimum_capacity", item["minimum_capacity_pct"], "%"),
        observation(item, "energy_efficiency_ratio", item["eer"], "ratio"),
        observation(item, "integrated_part_load_value", item["iplv"], "ratio"),
        observation(item, "refrigerant", "R-32; GWP 675", None),
        observation(item, "water_heat_exchanger", "brazed plate", None),
        observation(item, "compressor", "scroll; inverter controlled", None),
        observation(item, "fans", "axial; inverter controlled", None),
    ]
    size = str(item["size"])
    return {
        "capacity_scope": (
            f"Exact OEM {item['model']} size {size} cooling-only catalogue rating; "
            "no hydronic, electrical or ordered-option combination selected"
        ),
        "cooling_capacity_kw": item["cooling_capacity_kw"],
        "cooling_rating_conditions": RATING,
        "created_at": RETRIEVED_AT,
        "entity_type": "equipment",
        "equipment_category": "chiller",
        "evidence_json": compact(evidence),
        "field_sources_json": compact({field: [SOURCE_ID] for field in fields}),
        "form_factor": "air-cooled scroll inverter chiller",
        "input_power_kw": item["input_power_kw"],
        "last_verified_at": RETRIEVED_AT,
        "liquid_flow_l_min": item["liquid_flow_l_min"],
        "manufacturer": "Daikin",
        "model": item["model"],
        "name": f"Daikin {item['model']} size {size}",
        "notes": (
            "The exact nominal catalogue column is retained. Size 040-MONO and 040-DUAL "
            "are distinct published columns. Water flow is exactly converted from L/s to "
            "L/min. EER/IPLV remain ratios in observations; voltage, frequency, dimensions, "
            "weight, hydronic choices, SKU suffixes and data-center deployment are not inferred."
        ),
        "observations_json": compact(observations),
        "official_url": SOURCE_URL,
        "power_conditions": RATING,
        "power_rating_kind": "nominal cooling input at stated chiller rating condition",
        "product_status": "listed in Daikin Chillers Product Catalogue 2026",
        "quality_status": "source_backed",
        "record_id": stable_id("equipment", "Daikin", item["model"], str(item["variant"])),
        "record_scope": "configuration",
        "source_urls": [SOURCE_URL],
        "sources": [SOURCE_ID],
        "updated_at": RETRIEVED_AT,
        "variant": item["variant"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    items = rows()
    parse_precision_cooling_matrix(extracted_csv(items), source_url=SOURCE_URL, expected_count=27)
    records = sorted(
        (build_record(item) for item in items),
        key=lambda record: (record["model"], record["variant"]),
    )
    if len(records) != 27 or len({record["record_id"] for record in records}) != 27:
        raise ValueError("Expected 27 unique Daikin EWAT-CZ chiller configurations")
    args.output.write_text("".join(f"{compact(record)}\n" for record in records), encoding="utf-8")
    print("Wrote 27 reviewed Daikin EWAT-CZ chiller configurations")


if __name__ == "__main__":
    main()
