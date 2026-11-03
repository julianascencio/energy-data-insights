"""Build reviewed Envicool direct-to-chip and immersion configurations."""

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

RETRIEVED_AT = "2026-11-03T19:18:00Z"
AS_OF = "2026-11-03"
CDU_URL = "https://en.envicool.com/upload/file/20250402/1743565940169841.pdf"
IMMERSION_URL = "https://en.envicool.com/upload/file/20250321/1742550035252697.pdf"
SOURCES = {
    "envicool-cdu-20250402": {"url": CDU_URL, "publication_date": "2025-04-02"},
    "envicool-fullchain-20250321": {
        "url": IMMERSION_URL,
        "publication_date": "2025-03-21",
    },
}


def row(**values: Any) -> dict[str, Any]:
    return values


ROWS: list[dict[str, Any]] = []

# Direct-to-chip rows: each published model column is one exact configuration.
for model, capacity, airflow, flow, dims, form, power in (
    ("XCRow006", 6, 1000, 9, (450, 850, 175), "4U in-rack liquid-to-air CDU", "220 V AC, 50 Hz"),
    ("XCRow016", 16, 2600, 24, (450, 860, 350), "8U in-rack liquid-to-air CDU", "220 V AC, 50 Hz"),
):
    ROWS.append(
        row(
            source="envicool-cdu-20250402",
            manufacturer="Envicool",
            model=model,
            variant="cold-plate; liquid-to-air",
            category="direct_to_chip",
            cooling_capacity_kw=capacity,
            cooling_rating_conditions=(
                "25 degC primary supply air; 40 degC secondary supply liquid; SoluKing PG25"
            ),
            airflow_m3_h=airflow,
            liquid_flow_l_min=flow,
            width_mm=dims[0],
            depth_mm=dims[1],
            height_mm=dims[2],
            form_factor=form,
            locator=f"page 4, in-rack liquid-to-air table, {model}",
            extras=[
                ("nominal_power_supply", power, None),
                ("pump_redundancy", "dual pumps", None),
                ("secondary_filtration", "100 mesh", None),
            ],
        )
    )

ROWS.append(
    row(
        source="envicool-cdu-20250402",
        manufacturer="Envicool",
        model="XCRow120",
        variant="cold-plate; liquid-to-air",
        category="direct_to_chip",
        cooling_capacity_kw=120,
        cooling_rating_conditions="25 degC inlet air; supply coolant <=45 degC; PG25",
        width_mm=600,
        depth_mm=1200,
        height_mm=2200,
        form_factor="floor-standing in-row liquid-to-air CDU",
        locator="page 4, in-row liquid-to-air table, XCRow120",
        extras=[],
    )
)

for model, capacity, flow, dims, power, filtration in (
    ("XCRow040", 40, 60, (450, 850, 175), "220 V AC", "100 mesh"),
    ("XCRow080", 80, 99, (535, 850, 165), "48 V DC", "not stated"),
):
    ROWS.append(
        row(
            source="envicool-cdu-20250402",
            manufacturer="Envicool",
            model=model,
            variant="cold-plate; liquid-to-liquid",
            category="direct_to_chip",
            cooling_capacity_kw=capacity,
            cooling_rating_conditions=(
                "35 degC primary supply liquid; softened water; 40 degC secondary "
                "supply liquid; SoluKing PG25"
            ),
            liquid_flow_l_min=flow,
            width_mm=dims[0],
            depth_mm=dims[1],
            height_mm=dims[2],
            form_factor="OCP ORV3 in-rack liquid-to-liquid CDU",
            locator=f"page 4, in-rack liquid-to-liquid table, {model}",
            extras=[
                ("nominal_power_supply", power, None),
                ("pump_redundancy", "dual pumps", None),
                ("secondary_filtration", filtration, None),
            ],
        )
    )

central = (
    ("XCRow300", 300, 450, (600, 1200, 1200), "single pump"),
    ("XCRow400", 400, 600, (1000, 1400, 2200), "single pump"),
    ("XCRow500", 500, 750, (1200, 1200, 2200), "single pump"),
    ("XCRow630", 630, 945, (1200, 1400, 2200), "single pump"),
    ("XCRow300-B", 300, 450, (600, 1200, 2200), "dual pumps"),
    ("XCRow600", 600, 900, (800, 2000, 2200), "dual pumps"),
    ("XCRow2000", 2000, 3000, (1200, 2000, 2200), "dual pumps"),
    ("XCRow1400", 1400, 1200, (1200, 1200, 2200), "four pumps"),
)
for model, capacity, flow, dims, pumps in central:
    ROWS.append(
        row(
            source="envicool-cdu-20250402",
            manufacturer="Envicool",
            model=model,
            variant="cold-plate; centralized liquid-to-liquid",
            category="direct_to_chip",
            cooling_capacity_kw=capacity,
            cooling_rating_conditions=(
                "35 degC primary supply liquid; 40 degC secondary supply liquid; "
                "OEM-listed water/PG25/EG25 coolant choices"
            ),
            liquid_flow_l_min=flow,
            width_mm=dims[0],
            depth_mm=dims[1],
            height_mm=dims[2],
            form_factor="floor-standing in-row liquid-to-liquid CDU",
            locator=f"page 6, centralized in-row CDU table, {model}",
            extras=[
                ("pump_configuration", pumps, None),
                ("power_supply_choices", "480/400 V AC, 3-phase, 50/60 Hz", None),
            ],
        )
    )

# Immersion rows retain OEM IT-device power boundaries as observations. They are
# not normalized as cooling capacity or electrical input power.
immersion = (
    (
        "TK21C30F3",
        "single-phase immersion cabinet",
        (1050, 800, 1250),
        200,
        [
            ("rack_capacity", 21, "U"),
            ("it_device_power_range", "10-30", "kW"),
            ("liquid_volume_range", "280-420", "L"),
        ],
    ),
    (
        "TK42C60F3",
        "single-phase immersion cabinet",
        (2100, 800, 1250),
        400,
        [
            ("rack_capacity", 42, "U"),
            ("it_device_power_range", "20-60", "kW"),
            ("liquid_volume_range", "560-840", "L"),
        ],
    ),
    (
        "TK52C80F3",
        "single-phase immersion cabinet",
        (2550, 800, 1250),
        550,
        [
            ("rack_capacity", 52, "U"),
            ("it_device_power_range", "25-80", "kW"),
            ("liquid_volume_range", "690-1000", "L"),
        ],
    ),
    (
        "TK11S10F3",
        "integrated single-phase immersion cabinet",
        (1000, 800, 1300),
        220,
        [
            ("rack_capacity", 11, "U"),
            ("it_device_power", 10, "kW"),
            ("minimum_facility_water_flow", 241, "L/min"),
        ],
    ),
    (
        "TK20S20F3",
        "integrated single-phase immersion cabinet",
        (1550, 800, 1300),
        300,
        [
            ("rack_capacity", 21, "U"),
            ("it_device_power", 20, "kW"),
            ("minimum_facility_water_flow", 362, "L/min"),
        ],
    ),
    (
        "TK32S35F3",
        "integrated single-phase immersion cabinet",
        (2100, 800, 1300),
        400,
        [
            ("rack_capacity", 32, "U"),
            ("it_device_power", 35, "kW"),
            ("minimum_facility_water_flow", 602, "L/min"),
        ],
    ),
    (
        "CDU80J5S3",
        "immersion liquid CDU",
        (1000, 800, 1500),
        400,
        [
            ("it_device_power", 80, "kW"),
            ("circulation_volume_oil_fluorinated", "36/32", "m3/h"),
            ("minimum_facility_water_flow", 241, "L/min"),
        ],
    ),
    (
        "CDU120J5S3",
        "immersion liquid CDU",
        (1200, 800, 1500),
        500,
        [
            ("it_device_power", 120, "kW"),
            ("circulation_volume_oil_fluorinated", "54/49", "m3/h"),
            ("minimum_facility_water_flow", 362, "L/min"),
        ],
    ),
    (
        "CDU200J5S3",
        "immersion liquid CDU",
        (1500, 1000, 1800),
        650,
        [
            ("it_device_power", 200, "kW"),
            ("circulation_volume_oil_fluorinated", "90/81", "m3/h"),
            ("minimum_facility_water_flow", 602, "L/min"),
        ],
    ),
    (
        "CDU320J5S3",
        "immersion liquid CDU",
        (1600, 1200, 1800),
        850,
        [
            ("it_device_power", 320, "kW"),
            ("circulation_volume_oil_fluorinated", "144/130", "m3/h"),
            ("minimum_facility_water_flow", 965, "L/min"),
        ],
    ),
    (
        "TK21D50F3",
        "phase-change immersion integrated cabinet",
        (1100, 880, 1550),
        320,
        [
            ("rack_capacity", 21, "U"),
            ("it_device_power", 50, "kW"),
            ("minimum_facility_water_flow", 72, "L/min"),
        ],
    ),
    (
        "TK32D80F3",
        "phase-change immersion integrated cabinet",
        (1650, 880, 1550),
        450,
        [
            ("rack_capacity", 32, "U"),
            ("it_device_power", 80, "kW"),
            ("minimum_facility_water_flow", 144, "L/min"),
        ],
    ),
    (
        "TK42D100F3",
        "phase-change immersion integrated cabinet",
        (2250, 880, 1550),
        600,
        [
            ("rack_capacity", 42, "U"),
            ("it_device_power", 100, "kW"),
            ("minimum_facility_water_flow", 179, "L/min"),
        ],
    ),
)
for model, variant, dims, weight, extras in immersion:
    ROWS.append(
        row(
            source="envicool-fullchain-20250321",
            manufacturer="Envicool",
            model=model,
            variant=variant,
            category="immersion",
            cooling_capacity_kw=None,
            cooling_rating_conditions=(
                "OEM IT-device power boundary; chilled-water source with supply "
                "water <=35 degC where stated"
            ),
            width_mm=dims[0],
            depth_mm=dims[1],
            height_mm=dims[2],
            weight_kg=weight,
            form_factor=variant,
            locator=f"pages 3-4, immersion product specification, {model}",
            extras=[
                *extras,
                ("nominal_power_supply", "380 V AC, 3-phase, 50 Hz", None),
                ("it_equipment_envelope", "19-inch; depth <=900 mm", None),
            ],
        )
    )

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


def extracted_csv(rows: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for item in rows:
        writer.writerow({field: item.get(field, "") for field in CSV_FIELDS})
    return stream.getvalue().encode()


def observation(
    item: dict[str, Any], field: str, value: object, unit: str | None
) -> dict[str, object]:
    return {
        "as_of": AS_OF,
        "boundary": f"Exact {item['model']} {item['variant']} configuration",
        "field": field,
        "kind": "reported",
        "locator": item["locator"],
        "source_id": item["source"],
        "unit": unit,
        "value": value,
    }


def build_record(item: dict[str, Any]) -> dict[str, object]:
    source_id = item["source"]
    source = SOURCES[source_id]
    normalized = [
        "airflow_m3_h",
        "cooling_capacity_kw",
        "depth_mm",
        "height_mm",
        "liquid_flow_l_min",
        "weight_kg",
        "width_mm",
    ]
    fields = [
        "capacity_scope",
        "cooling_rating_conditions",
        "equipment_category",
        "form_factor",
        "manufacturer",
        "model",
        "name",
        "notes",
        "observations_json",
        "official_url",
        "record_scope",
        "variant",
    ] + [field for field in normalized if item.get(field) is not None]
    units = {
        "airflow_m3_h": "m3/h",
        "cooling_capacity_kw": "kW",
        "depth_mm": "mm",
        "height_mm": "mm",
        "liquid_flow_l_min": "L/min",
        "weight_kg": "kg",
        "width_mm": "mm",
    }
    evidence = {
        field: {
            "confidence": "high",
            "locator": item["locator"],
            "source_publication_dates": {source_id: source["publication_date"]},
            **({"unit": units[field]} if field in units else {}),
        }
        for field in fields
    }
    observations = [
        observation(item, field, value, unit) for field, value, unit in item.get("extras", [])
    ]
    record: dict[str, object] = {
        "capacity_scope": (
            f"Exact OEM {item['model']} {item['variant']} configuration; "
            "no optional combinations synthesized"
        ),
        "cooling_rating_conditions": item["cooling_rating_conditions"],
        "created_at": RETRIEVED_AT,
        "entity_type": "equipment",
        "equipment_category": item["category"],
        "evidence_json": compact(evidence),
        "field_sources_json": compact({field: [source_id] for field in fields}),
        "form_factor": item["form_factor"],
        "last_verified_at": RETRIEVED_AT,
        "manufacturer": item["manufacturer"],
        "model": item["model"],
        "name": f"Envicool {item['model']}",
        "notes": (
            "Exact published model column retained. IT-device power, coolant choices, "
            "optional power feeds and ranges remain source-bound observations and are "
            "not converted to cooling or electrical input power."
        ),
        "observations_json": compact(observations),
        "official_url": source["url"],
        "quality_status": "source_backed",
        "record_id": stable_id("equipment", item["manufacturer"], item["model"], item["variant"]),
        "record_scope": "configuration",
        "source_urls": [source["url"]],
        "sources": [source_id],
        "updated_at": RETRIEVED_AT,
        "variant": item["variant"],
    }
    for field in normalized:
        if item.get(field) is not None:
            record[field] = item[field]
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    for source_id, source in SOURCES.items():
        selected = [item for item in ROWS if item["source"] == source_id]
        parse_precision_cooling_matrix(
            extracted_csv(selected), source_url=str(source["url"]), expected_count=len(selected)
        )
    records = sorted(
        (build_record(item) for item in ROWS),
        key=lambda record: (record["model"], record["variant"]),
    )
    if len(records) != 26 or len({record["record_id"] for record in records}) != 26:
        raise ValueError("Expected 26 unique Envicool configurations")
    args.output.write_text("".join(f"{compact(record)}\n" for record in records), encoding="utf-8")
    print("Wrote 26 reviewed Envicool direct-to-chip/immersion configurations")


if __name__ == "__main__":
    main()
