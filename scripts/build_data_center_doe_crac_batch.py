"""Build the first 50 displayed DOE CCMS computer-room air-conditioner rows."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
from typing import Any

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.inventories import (
    parse_doe_crac_certification_matrix,
)

RETRIEVED_AT = "2026-11-05T20:24:00Z"
AS_OF = "2026-10-23"
SOURCE_ID = "doe-ccms-crac-page1-20261023"
SOURCE_URL = (
    "https://www.regulations.doe.gov/certification-data/"
    "CCMS-4-Air_Conditioners_and_Heat_Pumps_-_Computer_Room_Air_Conditioners.html"
)
BTU_H_TO_KW = 0.00029307107
SCFM_TO_M3_H = 1.69901082
CSV_FIELDS = [
    "brand",
    "basic_model",
    "indoor_model",
    "outdoor_model",
    "condenser_heat_rejection",
    "configuration",
    "net_total_btu_h",
    "net_sensible_btu_h",
    "rated_airflow_scfm",
    "nsencop",
    "locator",
]

ABOVEAIR_RATINGS = (
    ("053", "D", 37800, 129000, 5500, 2.12),
    ("042", "D", 36200, 124000, 5500, 2.33),
    ("035", "D", 29000, 98800, 5000, 2.24),
    ("028", "D", 24100, 82400, 4000, 2.41),
    ("021", "D", 19600, 66800, 3000, 2.42),
    ("018", "S", 15300, 52100, 2500, 2.64),
    ("014", "S", 12800, 43800, 2000, 2.78),
    ("011", "S", 9420, 32200, 1500, 2.47),
    ("009", "S", 8300, 28300, 1250, 2.56),
    ("007", "S", 6750, 23000, 1000, 2.86),
    ("005", "S", 5000, 17000, 750, 2.36),
    ("004", "S", 3720, 12700, 500, 2.41),
)
ABOVEAIR_FAMILIES = (
    ("HKA", None),
    ("HKH", "XCU"),
    ("HKE", "XCX"),
)
AIRSYS_ROWS = (
    (
        "OP2A*040V1T1BE-***",
        "OP2A*040V1T1BE-***",
        "VMEG60*",
        "Upflow Ducted",
        136000,
        136000,
        5890,
        3.10,
    ),
    ("OP2A*040V1D1BB****", "OP2A*040V1D1BB****", "VMEG60*", "Downflow", 136000, 136000, 5890, 2.96),
    (
        "OP2A*040V1T1BB****",
        "OP2A*040V1T1BB****",
        "VMEG60*",
        "Upflow Ducted",
        136000,
        136000,
        5890,
        2.96,
    ),
    ("OP2A*040V1D1BC-***", "OP2A*040V1D1BC-***", "VMEG60*", "Downflow", 136000, 136000, 5890, 3.16),
    (
        "OP2A*040V1T1BC-***",
        "OP2A*040V1T1BC-***",
        "VMEG60*",
        "Upflow Ducted",
        136000,
        136000,
        5890,
        3.16,
    ),
    ("OP2A*040V1D1AB-***", "OP2A*040V1D1AB-***", "VMEG60*", "Downflow", 136000, 136000, 5890, 2.75),
    (
        "OP2A*040V1T1AB-***",
        "OP2A*040V1T1AB-***",
        "VMEG60*",
        "Upflow Ducted",
        136000,
        136000,
        5890,
        2.75,
    ),
    ("OP2A*040V1D1AC-***", "OP2A*040V1D1AC-***", "VMEG60*", "Downflow", 136000, 136000, 5890, 2.84),
    (
        "OP2A*040V1T1AC-***",
        "OP2A*040V1T1AC-***",
        "VMEG60*",
        "Upflow Ducted",
        136000,
        136000,
        5890,
        2.84,
    ),
    (
        "UNI-EDG.20V1*1MR410CAC",
        "UNI-EDG.20V1*1MR410CAC",
        None,
        "Horizontal Flow",
        67900,
        65900,
        2520,
        2.85,
    ),
    (
        "UNI-EDG.20V1*1MR410BAC",
        "UNI-EDG.20V1*1MR410BAC",
        None,
        "Horizontal Flow",
        67900,
        65500,
        2470,
        2.80,
    ),
    (
        "UNI-EDG.20V1*1MR410AAC",
        "UNI-EDG.20V1*1MR410AAC",
        None,
        "Horizontal Flow",
        67900,
        65500,
        2470,
        2.80,
    ),
    (
        "UNI-EDG.40V1*3MR410BAC",
        "UNI-EDG.40V1*3MR410BAC",
        None,
        "Horizontal Flow",
        137000,
        132000,
        5410,
        2.93,
    ),
    (
        "UNI-EDG.40V1*3MR410CAC",
        "UNI-EDG.40V1*3MR410CAC",
        None,
        "Horizontal Flow",
        137000,
        133000,
        5290,
        2.90,
    ),
)


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def rows() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    row_number = 1
    for family, outdoor_family in ABOVEAIR_FAMILIES:
        for size, indoor_suffix, total, sensible, airflow, nsencop in ABOVEAIR_RATINGS:
            result.append(
                {
                    "brand": "AboveAir",
                    "basic_model": f"{family}-{size}(kW)*",
                    "indoor_model": f"{family}-{size}{indoor_suffix}(kW)*",
                    "outdoor_model": (
                        None
                        if outdoor_family is None
                        else f"{outdoor_family}-{size}{indoor_suffix}(kW)*"
                    ),
                    "condenser_heat_rejection": "Air-Cooled with Ducted Condenser",
                    "configuration": "Ceiling-Mounted Ducted",
                    "net_total_btu_h": total,
                    "net_sensible_btu_h": sensible,
                    "rated_airflow_scfm": airflow,
                    "nsencop": nsencop,
                    "locator": f"public results table / displayed row {row_number} of 50",
                }
            )
            row_number += 1
    for basic, indoor, outdoor, configuration, total, sensible, airflow, nsencop in AIRSYS_ROWS:
        result.append(
            {
                "brand": "AIRSYS",
                "basic_model": basic,
                "indoor_model": indoor,
                "outdoor_model": outdoor,
                "condenser_heat_rejection": "Air-Cooled",
                "configuration": configuration,
                "net_total_btu_h": total,
                "net_sensible_btu_h": sensible,
                "rated_airflow_scfm": airflow,
                "nsencop": nsencop,
                "locator": f"public results table / displayed row {row_number} of 50",
            }
        )
        row_number += 1
    return result


def extracted_csv(items: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for item in items:
        writer.writerow({field: item.get(field) or "" for field in CSV_FIELDS})
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
    brand = str(item["brand"])
    model = str(item["basic_model"])
    conflict = item["net_sensible_btu_h"] > item["net_total_btu_h"]
    cooling_capacity_kw = (
        None if conflict else round(float(item["net_total_btu_h"]) * BTU_H_TO_KW, 3)
    )
    airflow_m3_h = round(float(item["rated_airflow_scfm"]) * SCFM_TO_M3_H, 3)
    boundary = f"DOE CCMS public computer-room air-conditioner basic-model row for {brand} {model}"
    observations = [
        observation(item, "brand_name", brand, None, boundary),
        observation(item, "indoor_or_package_model", item["indoor_model"], None, boundary),
        observation(item, "outdoor_model", item["outdoor_model"], None, boundary),
        observation(
            item,
            "condenser_heat_rejection_medium",
            item["condenser_heat_rejection"],
            None,
            boundary,
        ),
        observation(item, "net_total_cooling_capacity", item["net_total_btu_h"], "Btu/h", boundary),
        observation(
            item, "net_sensible_cooling_capacity", item["net_sensible_btu_h"], "Btu/h", boundary
        ),
        observation(item, "rated_airflow", item["rated_airflow_scfm"], "SCFM", boundary),
        observation(
            item, "net_sensible_coefficient_of_performance", item["nsencop"], "ratio", boundary
        ),
        observation(
            item,
            "registry_disclaimer",
            "Public listing is not a DOE determination of standards compliance",
            None,
            "Issuer database status boundary",
        ),
    ]
    fields = [
        "airflow_m3_h",
        "capacity_scope",
        "cooling_capacity_kw",
        "cooling_rating_conditions",
        "equipment_category",
        "form_factor",
        "manufacturer",
        "model",
        "name",
        "notes",
        "observations_json",
        "official_url",
        "product_status",
        "record_scope",
        "variant",
    ]
    if conflict:
        fields.append("conflicts_json")
    evidence: dict[str, dict[str, object]] = {
        field: {
            "confidence": "high",
            "locator": item["locator"],
            "source_publication_dates": {SOURCE_ID: AS_OF},
        }
        for field in fields
    }
    evidence["airflow_m3_h"]["unit"] = "m3/h"
    evidence["cooling_capacity_kw"]["unit"] = "kW"
    record: dict[str, object] = {
        "airflow_m3_h": airflow_m3_h,
        "capacity_scope": (
            f"Exact current DOE CCMS CRAC basic-model row for {model}; cooling values, "
            "airflow and NSenCOP are equipment ratings, not facility cooling or IT capacity"
        ),
        "cooling_capacity_kw": cooling_capacity_kw,
        "cooling_rating_conditions": (
            "DOE CCMS represented net cooling capacities and rated airflow; the displayed "
            "table does not print the underlying test-point temperatures or humidity"
        ),
        "created_at": RETRIEVED_AT,
        "entity_type": "equipment",
        "equipment_category": "crac",
        "evidence_json": compact(evidence),
        "field_sources_json": compact({field: [SOURCE_ID] for field in fields}),
        "form_factor": str(item["configuration"]),
        "last_verified_at": RETRIEVED_AT,
        "manufacturer": brand,
        "model": model,
        "name": f"{brand} {model}",
        "notes": (
            "Exact manufacturer-represented public DOE CCMS basic-model row, not a deployment "
            "or DOE compliance determination. Btu/h and SCFM originals remain observations; "
            "NSenCOP is not normalized as percent efficiency. Voltage, frequency, input power, "
            "dimensions, refrigerant and installed quantity remain unknown."
        ),
        "observations_json": compact(observations),
        "official_url": SOURCE_URL,
        "product_status": "current DOE CCMS public representation updated 2026-10-23",
        "quality_status": "needs_review" if conflict else "source_backed",
        "record_id": stable_id("equipment", brand, "DOE CCMS CRAC", model),
        "record_scope": "configuration",
        "source_urls": [SOURCE_URL],
        "sources": [SOURCE_ID],
        "updated_at": RETRIEVED_AT,
        "variant": (
            f"{item['configuration']}; {item['condenser_heat_rejection']}; "
            f"indoor/package {item['indoor_model']}"
            + (f"; outdoor {item['outdoor_model']}" if item["outdoor_model"] else "")
        ),
    }
    if conflict:
        record["conflicts_json"] = compact(
            {
                "cooling_capacity_kw": [
                    {
                        "boundary": "DOE displayed Net Total Cooling Capacity column",
                        "field": "cooling_capacity_kw",
                        "observed_at": RETRIEVED_AT,
                        "sources": [SOURCE_ID],
                        "unit": "Btu/h",
                        "value": item["net_total_btu_h"],
                    },
                    {
                        "boundary": (
                            "DOE displayed Net Sensible Cooling Capacity column; value exceeds "
                            "the displayed net-total value, so scalar cooling capacity is withheld"
                        ),
                        "field": "cooling_capacity_kw",
                        "observed_at": RETRIEVED_AT,
                        "sources": [SOURCE_ID],
                        "unit": "Btu/h",
                        "value": item["net_sensible_btu_h"],
                    },
                ]
            }
        )
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    items = rows()
    parsed = parse_doe_crac_certification_matrix(
        extracted_csv(items), source_url=SOURCE_URL, expected_count=50
    )
    records = sorted(
        (build_record(item) for item in parsed["candidates"]),
        key=lambda record: (str(record["manufacturer"]), str(record["model"])),
    )
    if len(records) != 50 or len({record["record_id"] for record in records}) != 50:
        raise ValueError("Expected 50 unique DOE CCMS CRAC records")
    if sum("conflicts_json" in record for record in records) != 36:
        raise ValueError("Expected all 36 AboveAir rows to retain the printed capacity conflict")
    args.output.write_text("".join(f"{compact(record)}\n" for record in records), encoding="utf-8")
    print("Wrote 50 reviewed DOE CCMS computer-room air-conditioner records")


if __name__ == "__main__":
    main()
