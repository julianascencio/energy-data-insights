"""Build the first 50 displayed DOE CCMS medium-voltage dry-type transformer rows."""

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

RETRIEVED_AT = "2026-11-05T07:20:00Z"
AS_OF = "2026-10-23"
SOURCE_ID = "doe-ccms-mvdt-basic-model-page1-20261023"
SOURCE_URL = (
    "https://www.regulations.doe.gov/certification-data/"
    "CCMS-4-Distribution_Transformers_-_Medium-Voltage__Dry-Type_"
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

# Exact public-table rows 1-50. BIL is a group rating, not a winding voltage.
RAW_ROWS: list[tuple[str, str, int, float, float, float]] = [
    ("Hitachi", "SCLB-2500/13.8-S", 3, 2500, 110, 99.38),
    ("Hitachi", "SCB-1000/13.8", 3, 1000, 95, 99.23),
    ("Hitran Corporation", "WC250K-01", 1, 250, 20, 99.18),
    ("Hitran Corporation", "WC050K-01", 1, 50, 20, 98.76),
    ("HOWARD INDUSTRIES", "5237-100000-007", 3, 112.5, 30, 98.52),
    ("HOWARD INDUSTRIES", "5450-000000-006", 3, 150, 20, 98.65),
    ("HOWARD INDUSTRIES", "5585-000000-003", 3, 500, 60, 98.99),
    ("HOWARD INDUSTRIES", "5465-000000-002", 1, 200, 60, 98.88),
    ("JEI", "228-4907-557", 3, 2000, 125, 99.30),
    ("JEI", "228-4908-507", 3, 2500, 95, 99.51),
    ("JEI", "228-4908-946", 3, 875, 95, 99.27),
    ("JEI", "227-4908-105", 3, 1500, 60, 99.39),
    ("JEI", "227-4905-561", 3, 1000, 30, 99.40),
    ("JEI", "228-4908-530", 3, 1500, 95, 99.39),
    ("JEI", "228-4907-400", 3, 2500, 95, 99.50),
    ("JEI", "228-4907-408", 3, 500, 95, 99.07),
    ("JEI", "228-4908-103", 3, 1000, 95, 99.28),
    ("JEI", "228-4908-101", 3, 300, 95, 98.95),
    ("JEI", "228-4907-702", 3, 1250, 95, 99.39),
    ("JEI", "228-4908-102", 3, 750, 60, 99.24),
    ("JEI", "227-4907-100", 3, 2000, 60, 99.43),
    ("JEI", "228-4907-755", 3, 750, 95, 99.20),
    ("JEI", "227-4907-406", 3, 1500, 60, 99.42),
    ("JEI", "228-4907-700", 3, 275, 95, 98.91),
    ("JEI", "228-4907-701", 3, 1250, 95, 99.31),
    ("JEI", "227-4907-405", 3, 300, 30, 99.05),
    ("JEI", "228-4907-820", 3, 2000, 60, 99.43),
    ("JEI", "228-4905-815", 3, 750, 60, 99.27),
    ("JEI", "227-4905-975", 3, 500, 30, 99.20),
    ("JEI", "228-4907-860", 3, 1500, 95, 99.47),
    ("JEI", "228-4907-555", 3, 1250, 95, 99.37),
    ("MGM", "MGMDOET2500096-150", 3, 2500, 150, 99.34),
    ("MGM", "MGMDOET2000096-150", 3, 2000, 150, 99.29),
    ("MGM", "MGMDOET1500096-150", 3, 1500, 150, 99.22),
    ("MGM", "MGMDOET1000096-150", 3, 1000, 150, 99.11),
    ("MGM", "MGMDOET0500096-150", 3, 500, 150, 98.89),
    ("MGM", "MGMDOET2500046-095", 3, 2500, 95, 99.42),
    ("MGM", "MGMDOET2000046-095", 3, 2000, 95, 99.37),
    ("MGM", "MGMDOET1500046-095", 3, 1500, 95, 99.31),
    ("MGM", "MGMDOET1000046-095", 3, 1000, 95, 99.21),
    ("MGM", "MGMDOET0750046-095", 3, 750, 95, 99.12),
    ("MGM", "MGMDOET0500046-095", 3, 500, 95, 98.99),
    ("MGM", "MGMDOET0300046-095", 3, 300, 95, 98.81),
    ("MGM", "MGMDOET0225046-095", 3, 225, 95, 98.69),
    ("MGM", "MGMDOET0150046-095", 3, 150, 95, 98.51),
    ("MGM", "MGMDOET0112046-095", 3, 112, 95, 98.36),
    ("MGM", "MGMDOET0075046-095", 3, 75, 95, 98.13),
    ("MGM", "MGMDOET2500025-045", 3, 2500, 45, 99.48),
    ("MGM", "MGMDOET2000025-045", 3, 2000, 45, 99.44),
    ("MGM", "MGMDOET1500025-045", 3, 1500, 45, 99.37),
]


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def rows() -> list[dict[str, Any]]:
    return [
        {
            "brand": brand,
            "model": model,
            "phase_count": phases,
            "kva": kva,
            "bil_kv": bil,
            "efficiency": efficiency,
            "locator": f"public results table / displayed row {number} of 50",
        }
        for number, (brand, model, phases, kva, bil, efficiency) in enumerate(RAW_ROWS, start=1)
    ]


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
    values = {
        field: {
            "confidence": "high",
            "locator": locator,
            "source_publication_dates": {SOURCE_ID: AS_OF},
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
    brand = str(item["brand"])
    model = str(item["model"])
    boundary = f"DOE CCMS public basic-model row for {brand} {model}"
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
        observation(item, "brand_name", brand, None, boundary),
        observation(item, "number_of_phases", item["phase_count"], None, boundary),
        observation(
            item,
            "basic_impulse_insulation_level_group_rating",
            item["bil_kv"],
            "kV",
            "DOE table BIL group rating; not an exact winding or nominal input voltage",
        ),
        observation(
            item,
            "represented_efficiency",
            item["efficiency"],
            "%",
            "Manufacturer representation; displayed table omits load/test condition",
        ),
        observation(
            item,
            "registry_disclaimer",
            "Public listing is not a DOE determination of standards compliance",
            None,
            "Issuer database status boundary",
        ),
    ]
    return {
        "apparent_power_kva": item["kva"],
        "capacity_scope": (
            f"Exact current DOE CCMS medium-voltage dry-type basic-model row for {model}; "
            "active kW, winding voltage and load/test condition are not reported"
        ),
        "created_at": RETRIEVED_AT,
        "entity_type": "equipment",
        "equipment_category": "transformer",
        "evidence_json": evidence(fields, str(item["locator"])),
        "field_sources_json": compact({field: [SOURCE_ID] for field in fields}),
        "form_factor": "medium-voltage dry-type distribution transformer",
        "last_verified_at": RETRIEVED_AT,
        "manufacturer": brand,
        "model": model,
        "name": f"{brand} {model}",
        "notes": (
            "Exact manufacturer-represented public DOE CCMS basic-model row, not a "
            "deployment or DOE compliance determination. BIL group rating is not "
            "normalized as winding voltage and apparent kVA is not active kW."
        ),
        "observations_json": compact(observations),
        "official_url": SOURCE_URL,
        "power_conditions": (
            "Manufacturer-represented transformer apparent-power rating; active power, "
            "winding voltage and load/test conditions are unknown"
        ),
        "power_rating_kind": "DOE CCMS represented transformer apparent-power rating",
        "product_status": "current DOE CCMS public representation updated 2026-10-23",
        "quality_status": "source_backed",
        "record_id": stable_id("equipment", brand, "DOE CCMS medium-voltage dry-type", model),
        "record_scope": "configuration",
        "source_urls": [SOURCE_URL],
        "sources": [SOURCE_ID],
        "updated_at": RETRIEVED_AT,
        "variant": (
            f"DOE CCMS medium-voltage dry-type; {item['phase_count']}-phase; "
            f"{item['kva']:g} kVA; BIL group {item['bil_kv']:g} kV"
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
    print("Wrote 50 reviewed DOE CCMS medium-voltage transformer records")


if __name__ == "__main__":
    main()
