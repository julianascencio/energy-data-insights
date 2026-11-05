"""Build the complete current ENERGY STAR large-network-equipment inventory."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.inventories import (
    parse_energy_star_large_network_equipment_inventory,
)

RETRIEVED_AT = "2026-11-05T10:20:00Z"
SOURCE_ID = "epa-energy-star-large-network-equipment-20261027"
SOURCE_URL = "https://data.energystar.gov/api/v3/views/n8cx-m62r/export.csv?accessType=DOWNLOAD"
DATASET_UPDATED = "2026-10-27"
EXPECTED_COUNT = 96
PREFIXES = ("Min Power Config ", "Typ Power Config ", "Max Power Config ")

MANUFACTURERS = {
    "Cisco Systems": "Cisco",
    "Dell Inc.": "Dell",
    "EXTREME NETWORKS, INC.": "Extreme Networks",
    "Huawei Technologies Co., Ltd.": "Huawei",
}


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def snake(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def iso_date(value: str) -> str:
    return datetime.strptime(value, "%m/%d/%Y").strftime("%Y-%m-%d")


def grouped_values(row: dict[str, str]) -> dict[str, dict[str, str]]:
    grouped: dict[str, dict[str, str]] = {}
    for prefix, label in (
        ("Min Power Config ", "minimum_power_configuration"),
        ("Typ Power Config ", "typical_power_configuration"),
        ("Max Power Config ", "maximum_power_configuration"),
    ):
        values: dict[str, str] = {}
        for header, raw in row.items():
            if not header.startswith(prefix) or not raw:
                continue
            key = snake(header[len(prefix) :])
            if not key or key in values:
                raise ValueError(f"Ambiguous {prefix.strip()} field {header!r}")
            values[key] = raw
        if values:
            grouped[label] = values
    return grouped


def registry_values(row: dict[str, str]) -> dict[str, str]:
    excluded = {
        "ENERGY STAR Unique ID",
        "ENERGY STAR Partner",
        "Brand Name",
        "Model Name",
        "Model Number",
        "Additional Model Information",
        "UPC",
        "Date Available on Market",
        "Date Certified",
        "Markets",
        "CB Model Identifier",
    }
    values: dict[str, str] = {}
    for header, raw in row.items():
        if not raw or header in excluded or header.startswith(PREFIXES):
            continue
        key = snake(header)
        if not key or key in values:
            raise ValueError(f"Ambiguous registry field {header!r}")
        values[key] = raw
    return values


def observation(
    *, uid: str, certified: str, field: str, value: object, boundary: str
) -> dict[str, object]:
    return {
        "as_of": certified,
        "boundary": boundary,
        "field": field,
        "kind": "reported",
        "locator": f"ENERGY STAR certification {uid} / {field}",
        "source_id": SOURCE_ID,
        "unit": None,
        "value": value,
    }


def build_record(row: dict[str, str]) -> dict[str, object]:
    uid = row["ENERGY STAR Unique ID"]
    partner = row["ENERGY STAR Partner"]
    try:
        manufacturer = MANUFACTURERS[partner]
    except KeyError as exc:
        raise ValueError(f"Unreviewed ENERGY STAR network-equipment partner {partner!r}") from exc
    model = row["Model Name"]
    model_number = row["Model Number"]
    product_type = row["Product Type"]
    classification = row["Product Classification"]
    characteristics = row["Product Characteristics"]
    certified = iso_date(row["Date Certified"])
    available = iso_date(row["Date Available on Market"])
    configurations = grouped_values(row)
    registry = registry_values(row)
    boundary = (
        f"ENERGY STAR Large Network Equipment certification {uid}; {product_type}; "
        f"{classification}; certified test groups: {', '.join(configurations) or 'none printed'}"
    )
    observations = [
        observation(
            uid=uid,
            certified=certified,
            field="issuer_identity",
            value={
                "partner": partner,
                "brand_name": row["Brand Name"],
                "model_name": model,
                "model_number": model_number,
                "additional_model_information": row["Additional Model Information"],
                "cb_model_identifier": row["CB Model Identifier"],
            },
            boundary="one immutable ENERGY STAR certification entry",
        ),
        observation(
            uid=uid,
            certified=certified,
            field="registry_attributes",
            value=registry,
            boundary=(
                "issuer product type, classification, management, topology, modular and "
                "firmware attributes; certification observations, not deployment claims"
            ),
        ),
        observation(
            uid=uid,
            certified=certified,
            field="certified_test_configurations",
            value=configurations,
            boundary=(
                "minimum, typical and maximum configurations remain separate; measured watts "
                "apply only to the printed port topology, throughput, utilization, voltage and "
                "frequency; PSU outputs are nameplates"
            ),
        ),
        observation(
            uid=uid,
            certified=certified,
            field="market_lifecycle",
            value={
                "date_available_on_market": available,
                "date_certified": certified,
                "markets": row["Markets"],
            },
            boundary="issuer certification entry; current deployment and sales status unknown",
        ),
    ]
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
    evidence = {
        field: {
            "confidence": "high",
            "locator": f"ENERGY STAR certification {uid}",
            "source_publication_dates": {SOURCE_ID: DATASET_UPDATED},
        }
        for field in fields
    }
    certifications = {
        "energy_star": {
            "certificate": uid,
            "date": certified,
            "issuer": "U.S. Environmental Protection Agency ENERGY STAR",
            "scope": f"Large Network Equipment {product_type} certification for {model_number}",
            "source_id": SOURCE_ID,
        }
    }
    external_ids = {
        "energy_star_unique_id": uid,
        "energy_star_cb_model_identifier": row["CB Model Identifier"],
    }
    record: dict[str, object] = {
        "capacity_scope": boundary,
        "certifications_json": compact(certifications),
        "created_at": RETRIEVED_AT,
        "entity_type": "equipment",
        "equipment_category": "other",
        "evidence_json": compact(evidence),
        "external_ids_json": compact(external_ids),
        "field_sources_json": compact({field: [SOURCE_ID] for field in fields}),
        "form_factor": f"{product_type}; {classification}; {characteristics}",
        "last_verified_at": RETRIEVED_AT,
        "manufacturer": manufacturer,
        "model": model,
        "name": f"{manufacturer} {model} ENERGY STAR network certification {uid}",
        "notes": (
            "This record is one issuer-certified large-network-equipment entry, not an "
            "installed deployment. Minimum, typical and maximum configuration observations "
            "retain exact ports, PoE, modules, throughput, utilization and test conditions. "
            "Measured watts are not a generic rated device or rack input; PSU outputs are "
            "nameplates; certified port, module and PoE quantities are not deployed counts."
        ),
        "observations_json": compact(observations),
        "official_url": SOURCE_URL,
        "power_conditions": (
            "ENERGY STAR topology-, throughput-, utilization-, voltage- and frequency-qualified "
            "test observations; rated equipment input and rack input are undisclosed"
        ),
        "power_rating_kind": (
            "configuration-qualified measured test watts and PSU nameplates; no normalized input"
        ),
        "product_status": (
            "listed in the current ENERGY STAR certified Large Network Equipment dataset "
            f"snapshot updated {DATASET_UPDATED}"
        ),
        "quality_status": "source_backed",
        "record_id": stable_id(
            "equipment", manufacturer, "ENERGY STAR large network equipment", uid
        ),
        "record_scope": "configuration",
        "source_urls": [SOURCE_URL],
        "sources": [SOURCE_ID],
        "updated_at": RETRIEVED_AT,
        "variant": f"ENERGY STAR {uid}; {model_number}; {classification}",
    }
    return record


def write_shards(
    records: list[dict[str, object]], *, output_dir: Path, shard_size: int
) -> list[Path]:
    paths: list[Path] = []
    for index in range(0, len(records), shard_size):
        part = index // shard_size + 1
        path = output_dir / f"2026-11-05-energy-star-network-part-{part:02d}.jsonl"
        shard = records[index : index + shard_size]
        path.write_text("".join(f"{compact(record)}\n" for record in shard), encoding="utf-8")
        paths.append(path)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--shard-size", type=int, default=25)
    args = parser.parse_args()
    if args.shard_size < 1:
        raise ValueError("--shard-size must be positive")
    staged = parse_energy_star_large_network_equipment_inventory(
        args.csv_path.read_bytes(),
        source_url=SOURCE_URL,
        expected_count=EXPECTED_COUNT,
    )
    records = sorted(
        (build_record(row) for row in staged["candidates"]),
        key=lambda record: (
            str(record["manufacturer"]),
            str(record["model"]),
            str(record["variant"]),
        ),
    )
    if len(records) != EXPECTED_COUNT or len({record["record_id"] for record in records}) != len(
        records
    ):
        raise ValueError("Expected 96 unique large-network-equipment certifications")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    paths = write_shards(records, output_dir=args.output_dir, shard_size=args.shard_size)
    print(f"Wrote {len(records)} certifications to {len(paths)} shards")


if __name__ == "__main__":
    main()
