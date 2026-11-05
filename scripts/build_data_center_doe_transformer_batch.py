"""Build exact DOE CCMS low-voltage dry-type transformer basic-model rows."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
from typing import Any

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.inventories import (
    parse_doe_transformer_certification_matrix,
)

RETRIEVED_AT = "2026-11-05T06:20:00Z"
AS_OF = "2026-10-23"
SOURCE_ID = "doe-ccms-lvdt-basic-model-page1-20261023"
SOURCE_URL = (
    "https://www.regulations.doe.gov/certification-data/"
    "CCMS-4-Distribution_Transformers_-_Low-Voltage__Dry-Type_"
    "Based_on_Basic_Model.html"
)
CSV_FIELDS = [
    "brand",
    "basic_model",
    "phase_count",
    "apparent_power_kva",
    "represented_efficiency_pct",
    "locator",
]

V15_MODELS = [
    "V15DA068",
    "V15DA065",
    "V15DA064",
    "V15DA062",
    "V15DA061",
    "V15DA060",
    "V15DA057",
    "V15DA055",
    "V15DA050",
    "V15DA049",
    "V15DA048",
    "V15DA046",
    "V15DA045",
    "V15DA044",
    "V15DA038",
    "V15DA037",
    "V15DA033",
    "V15DA031",
    "V15DA025",
    "V15DA019",
    "V15DA013",
    "V15DA008",
    "V15DA007",
    "V15DA005",
    "V15DA004",
    "V15DA003",
    "V15DA002",
]
V12_MODELS = [
    "V12E292",
    "V12DC072",
    "V12DC071",
    "V12DC056",
    "V12DC045",
    "V12DC032",
    "V12DC005",
    "V12DC003",
    "V12DA130",
    "V12DA072",
    "V12DA071",
    "V12DA033",
    "V12DA019",
    "V12911",
    "V12892",
]
T99_MODELS = [
    "T99E801",
    "T99E019",
    "T99E014",
    "T99E004",
    "T99E001",
    "T99E000",
    "T99DC001",
    "T99DA001",
]


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def rows() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    page_row = 1
    for models, phase_count, kva, efficiency in (
        (V15_MODELS, 3, 15.0, 97.9),
        (V12_MODELS, 3, 112.5, 98.7),
        (T99_MODELS, 1, 100.0, 98.6),
    ):
        for model in models:
            result.append(
                {
                    "brand": "EATON",
                    "model": model,
                    "phase_count": phase_count,
                    "kva": kva,
                    "efficiency": efficiency,
                    "locator": f"public results table / displayed row {page_row} of 50",
                }
            )
            page_row += 1
    return result


def extracted_csv(items: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for item in items:
        writer.writerow(
            {
                "brand": item["brand"],
                "basic_model": item["model"],
                "phase_count": item["phase_count"],
                "apparent_power_kva": item["kva"],
                "represented_efficiency_pct": item["efficiency"],
                "locator": item["locator"],
            }
        )
    return stream.getvalue().encode()


def evidence(fields: list[str], locator: str) -> str:
    values: dict[str, dict[str, object]] = {
        field: {
            "confidence": "high",
            "locator": locator,
            "source_publication_dates": {SOURCE_ID: "2026-10-23"},
        }
        for field in fields
    }
    values["apparent_power_kva"]["unit"] = "kVA"
    return compact(values)


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
    model = item["model"]
    boundary = f"DOE CCMS public basic-model row for EATON {model}"
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
    observations = [
        observation(
            item,
            "certification_database",
            "U.S. DOE Compliance Certification Management System public database",
            None,
            boundary,
        ),
        observation(item, "brand_name", "EATON", None, boundary),
        observation(item, "number_of_phases", item["phase_count"], None, boundary),
        observation(
            item,
            "represented_efficiency",
            item["efficiency"],
            "%",
            (
                "Manufacturer-represented efficiency in the DOE public table; the "
                "displayed result does not print a load/test condition, so no generic "
                "efficiency scalar is normalized"
            ),
        ),
        observation(
            item,
            "registry_disclaimer",
            (
                "DOE states that appearance in the public database is not a "
                "determination that the model complies with conservation standards"
            ),
            None,
            "Issuer database status boundary",
        ),
    ]
    return {
        "apparent_power_kva": item["kva"],
        "capacity_scope": (
            f"Exact current DOE CCMS low-voltage dry-type basic-model row for {model}; "
            "active kW, winding voltage and load/test condition are not reported"
        ),
        "created_at": RETRIEVED_AT,
        "entity_type": "equipment",
        "equipment_category": "transformer",
        "evidence_json": evidence(fields, item["locator"]),
        "field_sources_json": compact({field: [SOURCE_ID] for field in fields}),
        "form_factor": "low-voltage dry-type distribution transformer",
        "last_verified_at": RETRIEVED_AT,
        "manufacturer": "Eaton",
        "model": model,
        "name": f"Eaton {model}",
        "notes": (
            "This is an exact manufacturer-represented basic-model row in the public "
            "DOE CCMS table, not a deployment or a DOE compliance determination. "
            "Apparent kVA is not converted to active kW."
        ),
        "observations_json": compact(observations),
        "official_url": SOURCE_URL,
        "power_conditions": (
            "Manufacturer-represented transformer apparent-power rating in the DOE "
            "public basic-model table; active power and winding conditions are unknown"
        ),
        "power_rating_kind": "DOE CCMS represented transformer apparent-power rating",
        "product_status": (
            "current basic-model representation in DOE CCMS public snapshot updated 2026-10-23"
        ),
        "quality_status": "source_backed",
        "record_id": stable_id("equipment", "Eaton", "DOE CCMS low-voltage dry-type", model),
        "record_scope": "configuration",
        "source_urls": [SOURCE_URL],
        "sources": [SOURCE_ID],
        "updated_at": RETRIEVED_AT,
        "variant": (
            f"DOE CCMS low-voltage dry-type; {item['phase_count']}-phase; {item['kva']:g} kVA"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    items = rows()
    parsed = parse_doe_transformer_certification_matrix(
        extracted_csv(items), source_url=SOURCE_URL, expected_count=50
    )
    if len(parsed["candidates"]) != 50:
        raise ValueError("Expected all 50 displayed DOE CCMS rows")
    records = sorted((build_record(item) for item in items), key=lambda row: str(row["model"]))
    if len(records) != 50 or len({row["record_id"] for row in records}) != 50:
        raise ValueError("Expected 50 unique DOE CCMS transformer records")
    args.output.write_text("".join(f"{compact(record)}\n" for record in records), encoding="utf-8")
    print("Wrote 50 reviewed DOE CCMS transformer basic-model records")


if __name__ == "__main__":
    main()
