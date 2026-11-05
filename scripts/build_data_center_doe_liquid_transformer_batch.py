"""Build the first 50 displayed DOE CCMS liquid-immersed transformer rows."""

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

RETRIEVED_AT = "2026-11-05T08:20:00Z"
AS_OF = "2026-10-23"
SOURCE_ID = "doe-ccms-liquid-transformer-basic-model-page1-20261023"
SOURCE_URL = (
    "https://www.regulations.doe.gov/certification-data/"
    "CCMS-4-Distribution_Transformers_-_Liquid-Immersed_Based_on_Basic_Model.html"
)
CSV_FIELDS = [
    "brand",
    "basic_model",
    "phase_count",
    "apparent_power_kva",
    "represented_efficiency_pct",
    "locator",
]

# Exact public-table rows 1-50. Model-number suffixes are identities, not parsed options.
RAW_ROWS: list[tuple[str, str, int, float, float]] = [
    ("CMI", "1632500125", 3, 2500, 99.53),
    ("CMI", "1632500095", 3, 2500, 99.53),
    ("CMI", "1632000095", 3, 2000, 99.51),
    ("CMI", "1631500150", 3, 1500, 99.48),
    ("CMI", "1631500125", 3, 1500, 99.48),
    ("CMI", "1631500095", 3, 1500, 99.48),
    ("CMI", "1631000125", 3, 1000, 99.43),
    ("CMI", "1631000095", 3, 1000, 99.43),
    ("CMI", "1630750125", 3, 750, 99.40),
    ("CMI", "1630750095", 3, 750, 99.40),
    ("CMI", "1630500150", 3, 500, 99.35),
    ("CMI", "1630500125", 3, 500, 99.35),
    ("CMI", "1630500095", 3, 500, 99.35),
    ("CMI", "1630300150", 3, 300, 99.27),
    ("CMI", "1630300125", 3, 300, 99.27),
    ("CMI", "1630300095", 3, 300, 99.27),
    ("CMI", "1630225125", 3, 225, 99.23),
    ("CMI", "1630225095", 3, 225, 99.23),
    ("CMI", "1630150125", 3, 150, 99.16),
    ("CMI", "1630150095", 3, 150, 99.16),
    ("CMI", "1630112125", 3, 112.5, 99.11),
    ("CMI", "1630112095", 3, 112.5, 99.11),
    ("CMI", "1630075125", 3, 75, 99.03),
    ("CMI", "1630075095", 3, 75, 99.03),
    ("CMI", "1630045125", 3, 45, 98.92),
    ("CMI", "1630045095", 3, 45, 98.92),
    ("CMI", "1610833095", 1, 833, 99.55),
    ("CMI", "1610500150", 1, 500, 99.49),
    ("CMI", "1610500125", 1, 500, 99.49),
    ("CMI", "1610500095", 1, 500, 99.49),
    ("CMI", "1610333150", 1, 333, 99.43),
    ("CMI", "1610333125", 1, 333, 99.43),
    ("CMI", "1610333095", 1, 333, 99.43),
    ("CMI", "1610250150", 1, 250, 99.39),
    ("CMI", "1610250125", 1, 250, 99.39),
    ("CMI", "1610250095", 1, 250, 99.39),
    ("CMI", "1610167150", 1, 167, 99.33),
    ("CMI", "1610167125", 1, 167, 99.33),
    ("CMI", "1610167095", 1, 167, 99.33),
    ("CMI", "1610100150", 1, 100, 99.25),
    ("CMI", "1610100125", 1, 100, 99.25),
    ("CMI", "1610100095", 1, 100, 99.25),
    ("CMI", "1610075150", 1, 75, 99.19),
    ("CMI", "1610075125", 1, 75, 99.19),
    ("CMI", "1610075095", 1, 75, 99.19),
    ("CMI", "1610050150", 1, 50, 99.11),
    ("CMI", "1610050125", 1, 50, 99.11),
    ("CMI", "1610050095", 1, 50, 99.11),
    ("CMI", "1610037150", 1, 37.5, 99.05),
    ("CMI", "1610037125", 1, 37.5, 99.05),
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
            "efficiency": efficiency,
            "locator": f"public results table / displayed row {number} of 50",
        }
        for number, (brand, model, phases, kva, efficiency) in enumerate(RAW_ROWS, start=1)
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
            f"Exact current DOE CCMS liquid-immersed basic-model row for {model}; "
            "active kW, winding voltage, dielectric fluid and load/test condition are not reported"
        ),
        "created_at": RETRIEVED_AT,
        "entity_type": "equipment",
        "equipment_category": "transformer",
        "evidence_json": evidence(fields, str(item["locator"])),
        "field_sources_json": compact({field: [SOURCE_ID] for field in fields}),
        "form_factor": "liquid-immersed distribution transformer",
        "last_verified_at": RETRIEVED_AT,
        "manufacturer": brand,
        "model": model,
        "name": f"{brand} {model}",
        "notes": (
            "Exact manufacturer-represented public DOE CCMS basic-model row, not a "
            "deployment or DOE compliance determination. The model string is preserved "
            "without decoding suffixes, and apparent kVA is not active kW."
        ),
        "observations_json": compact(observations),
        "official_url": SOURCE_URL,
        "power_conditions": (
            "Manufacturer-represented transformer apparent-power rating; active power, "
            "winding voltage, dielectric fluid and load/test conditions are unknown"
        ),
        "power_rating_kind": "DOE CCMS represented transformer apparent-power rating",
        "product_status": "current DOE CCMS public representation updated 2026-10-23",
        "quality_status": "source_backed",
        "record_id": stable_id("equipment", brand, "DOE CCMS liquid-immersed", model),
        "record_scope": "configuration",
        "source_urls": [SOURCE_URL],
        "sources": [SOURCE_ID],
        "updated_at": RETRIEVED_AT,
        "variant": (f"DOE CCMS liquid-immersed; {item['phase_count']}-phase; {item['kva']:g} kVA"),
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
    print("Wrote 50 reviewed DOE CCMS liquid-immersed transformer records")


if __name__ == "__main__":
    main()
