"""Build one reviewed partner batch from EPA's Enterprise Servers inventory."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.inventories import (
    parse_energy_star_enterprise_servers_inventory,
)

SOURCE_ID = "epa-energy-star-certified-enterprise-servers-20261104"
SOURCE_URL = "https://data.energystar.gov/api/v3/views/qifb-fcj2/export.csv?accessType=DOWNLOAD"
DATASET_UPDATED = "2026-11-04T14:17:50Z"
RETRIEVED_AT = "2026-11-04T20:27:06Z"
PARTNER = "Cisco Systems"
MANUFACTURER = "Cisco"
EXPECTED_COUNT = 20

CONFIGURATION_LABELS = (
    "Low-end Performance Configuration",
    "Typical or Single Configuration",
    "High-end Performance Configuration",
)


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def normalized_header(value: str) -> str:
    return " ".join(value.split())


def source_value(row: dict[str, str], header: str) -> str:
    wanted = normalized_header(header)
    for key, value in row.items():
        if normalized_header(key) == wanted:
            return value.strip()
    return ""


def iso_date(value: str) -> str:
    return datetime.strptime(value, "%m/%d/%Y").strftime("%Y-%m-%d")


def snake(value: str) -> str:
    value = re.sub(r"\([^)]*\)", "", value)
    value = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_")
    return value.lower()


def observation(
    row: dict[str, str], field: str, value: object, unit: str | None, boundary: str
) -> dict[str, object]:
    return {
        "as_of": iso_date(row["Date Certified"]),
        "boundary": boundary,
        "field": field,
        "kind": "reported",
        "locator": f"ENERGY STAR Unique ID {row['ENERGY STAR Unique ID']} / {field}",
        "source_id": SOURCE_ID,
        "unit": unit,
        "value": value,
    }


def tested_configuration(row: dict[str, str], label: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for header, value in row.items():
        normalized = normalized_header(header)
        if not value.strip() or label not in normalized:
            continue
        cleaned = normalized.replace(f" for {label}", "").replace(label, "").strip()
        cleaned = re.sub(r"\bfor$", "", cleaned).strip()
        key = snake(cleaned)
        if not key or key in values:
            raise ValueError(f"Ambiguous {label} field {header!r}")
        values[key] = value.strip()
    if not values:
        raise ValueError(f"Missing {label} fields")
    return values


def socket_conflicts(row: dict[str, str]) -> dict[str, object] | None:
    model_number = row["Model Number"]
    attribute = row["Product Processor Socket Count"]
    claimed: int | None = None
    if re.search(r"\btwo CPU socket populated\b", model_number, re.IGNORECASE):
        claimed = 2
    elif re.search(r"\bfour CPU slot populated\b", model_number, re.IGNORECASE):
        claimed = 4
    if claimed is None or attribute == str(claimed):
        return None
    return {
        "processor_socket_count": [
            {
                "boundary": "exact Model Number label",
                "field": "processor_socket_count",
                "observed_at": RETRIEVED_AT,
                "sources": [SOURCE_ID],
                "unit": "socket",
                "value": claimed,
            },
            {
                "boundary": "Product Processor Socket Count attribute",
                "field": "processor_socket_count",
                "observed_at": RETRIEVED_AT,
                "sources": [SOURCE_ID],
                "unit": "socket",
                "value": attribute,
            },
        ]
    }


def build_record(row: dict[str, str]) -> dict[str, object]:
    uid = row["ENERGY STAR Unique ID"]
    model = row["Model Name"]
    model_number = row["Model Number"]
    certified = iso_date(row["Date Certified"])
    boundary = (
        f"ENERGY STAR enterprise-server certification {uid} for {model}; low-end, "
        "typical/single and high-end SERT configurations remain separately bounded"
    )
    form_factor = f"{row['Form Factor']} enterprise server"
    sert_version = source_value(row, "SERT Version")
    if sert_version == "Other":
        sert_version = source_value(row, "SERT Version Other") or "Other (unspecified)"

    general_fields = {
        "brand_name": row["Brand Name"],
        "model_number": model_number,
        "additional_model_information": row["Additional Model Information"],
        "processor_socket_count_attribute": row["Product Processor Socket Count"],
        "single_server": row["Single Server"],
        "storage_heavy_server": row["Storage Heavy Server"],
        "resilient_system": row["Resilient System"],
        "number_of_nodes_for_multi_node": row["Number of Nodes for Multi-node"],
        "error_correcting_code": row["Error Correcting Code"],
        "error_correcting_code_enabled_as_shipped": row[
            "Error Correcting Code Enabled in Hardware as Shipped"
        ],
        "available_expansion_slots": row["Available Expansion Slots"],
        "operating_systems_supported": row["Operating Systems Supported"],
        "operating_system_used_for_testing": row["Operating System Used for Testing"],
        "available_dimm_slots": row["Available DIMM Slots"],
        "maximum_memory_capacity_gb": row["Maximum Memory Capacity (GB)"],
        "sert_version": sert_version,
        "architecture": row["64-bit Architecture"],
        "date_available_on_market": iso_date(row["Date Available On Market"]),
        "markets": row["Markets"],
    }
    general_fields = {key: value for key, value in general_fields.items() if value}

    power_management_headers = (
        "Power Saving Features Available",
        "Power Saving Features Enabled",
        "End User Required Power Saving Features",
        "Processor Power Management Enabled in Hardware on Shipment",
        "Storage Power Management Enabled in Hardware on Shipment",
        "Memory Power Management Enabled in Hardware on Shipment",
        "I/O Power Management Enabled in Hardware on Shipment",
        "Processor Dynamic Voltage Scaling Enabled on Shipment",
        "Processor Dynamic Frequency Scaling Enabled on Shipment",
        "Processor or Core Reduced Power States Enabled on Shipment",
        "Power Capping Enabled on Shipment",
        "Variable Speed Fan Control Enabled on Shipment",
        "Low Power Memory States Enabled on Shipment",
        "Low Power I/O States Enabled on Shipment",
        "Liquid Cooling Capability Enabled on Shipment",
        "Liquid Cooling Capability End-User Enabling Required",
    )
    power_management = {
        snake(header): source_value(row, header)
        for header in power_management_headers
        if source_value(row, header)
    }
    observations = [
        observation(row, "certified_model_attributes", general_fields, None, boundary),
        observation(
            row,
            "power_management_attributes",
            power_management,
            None,
            "certified server-family entry; shipment and end-user-enablement states retained",
        ),
    ]
    for label in CONFIGURATION_LABELS:
        configuration = tested_configuration(row, label)
        observations.append(
            observation(
                row,
                f"sert_{snake(label)}",
                configuration,
                None,
                (
                    f"{label}; SERT {sert_version}; PSU nameplates, idle watts, workload "
                    "efficiency scores and total-server power scores remain test observations, "
                    "not rated server or rack input"
                ),
            )
        )

    conflict = socket_conflicts(row)
    socket_attribute = row["Product Processor Socket Count"]
    socket_count = int(socket_attribute) if not conflict and socket_attribute.isdigit() else None
    fields = [
        "capacity_scope",
        "certifications_json",
        "equipment_category",
        "external_ids_json",
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
    if conflict:
        fields.append("conflicts_json")
    elif socket_count is not None:
        fields.append("processor_socket_count")
    evidence = {
        field: {
            "confidence": "high",
            "locator": f"ENERGY STAR Unique ID {uid}",
            "source_publication_dates": {SOURCE_ID: DATASET_UPDATED[:10]},
        }
        for field in fields
    }
    certifications = {
        "energy_star": {
            "certificate": uid,
            "date": certified,
            "issuer": "U.S. Environmental Protection Agency ENERGY STAR",
            "scope": f"Enterprise-server certification entry for {model_number}",
            "source_id": SOURCE_ID,
        }
    }
    external_ids = {
        "energy_star_unique_id": uid,
        "energy_star_model_identifier": row["ENERGY STAR Model Identifier"],
    }
    record: dict[str, object] = {
        "capacity_scope": boundary,
        "certifications_json": compact(certifications),
        "created_at": RETRIEVED_AT,
        "entity_type": "equipment",
        "equipment_category": "server",
        "evidence_json": compact(evidence),
        "external_ids_json": compact(external_ids),
        "field_sources_json": compact({field: [SOURCE_ID] for field in fields}),
        "form_factor": form_factor,
        "last_verified_at": RETRIEVED_AT,
        "manufacturer": MANUFACTURER,
        "model": model,
        "name": f"Cisco {model} ENERGY STAR enterprise-server certification {uid}",
        "notes": (
            "This record represents one issuer-certified server-family entry, not an installed "
            "deployment. Low-end, typical/single and high-end CPU, memory, storage, PSU and SERT "
            "test values remain separately bounded observations. PSU nameplates and SERT power "
            "scores are not summed or normalized as server input or rack power. Maximum supported "
            "memory is not substituted for installed memory."
        ),
        "observations_json": compact(observations),
        "official_url": SOURCE_URL,
        "power_conditions": (
            f"SERT {sert_version} test observations by low-end, typical/single and high-end "
            "configuration; rated server input and rack input are undisclosed"
        ),
        "power_rating_kind": "SERT benchmark observations; no normalized rated input power",
        "processor_socket_count": socket_count,
        "product_status": (
            "listed in the current ENERGY STAR certified enterprise-server dataset snapshot "
            "updated 2026-11-04"
        ),
        "quality_status": "needs_review" if conflict else "source_backed",
        "record_id": stable_id("equipment", MANUFACTURER, "ENERGY STAR enterprise server", uid),
        "record_scope": "configuration",
        "source_urls": [SOURCE_URL],
        "sources": [SOURCE_ID],
        "updated_at": RETRIEVED_AT,
        "variant": f"ENERGY STAR {uid}; {model_number}",
    }
    if conflict:
        record["conflicts_json"] = compact(conflict)
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_csv", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--shard-size",
        type=int,
        default=0,
        help="Write numbered JSONL shards with at most this many records",
    )
    args = parser.parse_args()
    staged = parse_energy_star_enterprise_servers_inventory(
        args.source_csv.read_bytes(),
        source_url=SOURCE_URL,
        partner=PARTNER,
        expected_count=EXPECTED_COUNT,
    )
    records = sorted(
        (build_record(row) for row in staged["candidates"]),
        key=lambda record: (str(record["model"]), str(record["variant"])),
    )
    if (
        len(records) != EXPECTED_COUNT
        or len({record["record_id"] for record in records}) != EXPECTED_COUNT
    ):
        raise ValueError(f"Expected {EXPECTED_COUNT} unique {PARTNER} certifications")
    if args.shard_size < 0:
        raise ValueError("--shard-size must be zero or positive")
    if args.shard_size:
        shard_count = (len(records) + args.shard_size - 1) // args.shard_size
        for index in range(shard_count):
            shard = records[index * args.shard_size : (index + 1) * args.shard_size]
            shard_path = args.output.with_name(
                f"{args.output.stem}-part-{index + 1:02d}{args.output.suffix}"
            )
            shard_path.write_text(
                "".join(f"{compact(record)}\n" for record in shard), encoding="utf-8"
            )
        print(f"Wrote {EXPECTED_COUNT} {PARTNER} certifications in {shard_count} shards")
    else:
        args.output.write_text(
            "".join(f"{compact(record)}\n" for record in records), encoding="utf-8"
        )
        print(f"Wrote {EXPECTED_COUNT} {PARTNER} certifications")


if __name__ == "__main__":
    main()
