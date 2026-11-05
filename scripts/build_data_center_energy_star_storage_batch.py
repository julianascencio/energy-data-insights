"""Build the complete current ENERGY STAR data-center-storage inventories."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import TypedDict

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.inventories import (
    parse_energy_star_data_center_storage_inventory,
)

RETRIEVED_AT = "2026-11-05T09:20:00Z"


class DatasetSpec(TypedDict):
    source_id: str
    source_url: str
    dataset_updated: str
    expected_count: int
    id_field: str
    type_field: str
    controller_field: str
    model_identifier_field: str
    label: str
    prefixes: tuple[str, ...]
    slug: str


DATASETS: dict[str, DatasetSpec] = {
    "block_io": {
        "source_id": "epa-energy-star-data-center-storage-block-20261104",
        "source_url": (
            "https://data.energystar.gov/api/v3/views/3uec-2gqf/export.csv?accessType=DOWNLOAD"
        ),
        "dataset_updated": "2026-11-04T14:24:14Z",
        "expected_count": 84,
        "id_field": "ENERGY STAR Unique ID",
        "type_field": "Product Type",
        "controller_field": "Storage Controller Configuration",
        "model_identifier_field": "CB Model Identifier",
        "label": "Block I/O",
        "prefixes": ("Trans ", "Stream "),
        "slug": "block",
    },
    "file_io": {
        "source_id": "epa-energy-star-data-center-storage-file-20261104",
        "source_url": (
            "https://data.energystar.gov/api/v3/views/put7-uu67/export.csv?accessType=DOWNLOAD"
        ),
        "dataset_updated": "2026-11-04T14:23:01Z",
        "expected_count": 36,
        "id_field": "PD_ID",
        "type_field": "SNIA Online Taxonomy Category",
        "controller_field": "Storage Controller Implementation",
        "model_identifier_field": "ENERGY STAR Model Identifier",
        "label": "File I/O",
        "prefixes": ("Trans ", "Comp "),
        "slug": "file",
    },
}

MANUFACTURERS = {
    "Dell Inc.": "Dell",
    "NetApp, Inc.": "NetApp",
    "Hewlett Packard Enterprise": "Hewlett Packard Enterprise",
    "IBM Corporation": "IBM",
    "Pure Storage, Inc.": "Pure Storage",
    "Hitachi Vantara LLC": "Hitachi Vantara",
    "Lenovo Group Limited": "Lenovo",
    "Huawei Technologies Co., Ltd.": "Huawei",
    "Seagate Technologies LLC": "Seagate",
    "EMC Corporation": "EMC Corporation",
    "Viking Enterprise Solutions, a division of Sanmina Corp": ("Viking Enterprise Solutions"),
}


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def snake(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def iso_date(value: str) -> str:
    for pattern in ("%m/%d/%Y", "%Y %b %d %I:%M:%S %p"):
        try:
            return datetime.strptime(value, pattern).strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValueError(f"Unsupported ENERGY STAR date {value!r}")


def grouped_values(row: dict[str, str], prefixes: tuple[str, ...]) -> dict[str, object]:
    grouped: dict[str, object] = {}
    for prefix in prefixes:
        values: dict[str, str] = {}
        for header, raw in row.items():
            if not header.startswith(prefix) or not raw:
                continue
            key = snake(header[len(prefix) :])
            if not key or key in values:
                raise ValueError(f"Ambiguous {prefix.strip()} field {header!r}")
            values[key] = raw
        if values:
            grouped[snake(prefix)] = values
    return grouped


def registry_values(row: dict[str, str], prefixes: tuple[str, ...]) -> dict[str, str]:
    excluded = {
        "ENERGY STAR Unique ID",
        "PD_ID",
        "ENERGY STAR Partner",
        "Brand Name",
        "Model Name",
        "Model Number",
        "Additional Model Information",
        "UPC",
        "Date Available On Market",
        "Date Qualified",
        "Markets",
        "CB Model Identifier",
        "ENERGY STAR Model Identifier",
    }
    values: dict[str, str] = {}
    for header, raw in row.items():
        if not raw or header in excluded or header.startswith(prefixes):
            continue
        key = snake(header)
        if not key or key in values:
            raise ValueError(f"Ambiguous registry field {header!r}")
        values[key] = raw
    return values


def observation(
    *, source_id: str, uid: str, qualified: str, field: str, value: object, boundary: str
) -> dict[str, object]:
    return {
        "as_of": qualified,
        "boundary": boundary,
        "field": field,
        "kind": "reported",
        "locator": f"ENERGY STAR certification {uid} / {field}",
        "source_id": source_id,
        "unit": None,
        "value": value,
    }


def build_record(row: dict[str, str], *, dataset_kind: str) -> dict[str, object]:
    dataset = DATASETS[dataset_kind]
    source_id = dataset["source_id"]
    source_url = dataset["source_url"]
    dataset_updated = dataset["dataset_updated"]
    uid = row[str(dataset["id_field"])]
    partner = row["ENERGY STAR Partner"]
    try:
        manufacturer = MANUFACTURERS[partner]
    except KeyError as exc:
        raise ValueError(f"Unreviewed ENERGY STAR storage partner {partner!r}") from exc
    label = str(dataset["label"])
    model = row["Model Name"]
    model_number = row["Model Number"]
    product_type = row[str(dataset["type_field"])]
    controller = row[str(dataset["controller_field"])]
    model_identifier = row[str(dataset["model_identifier_field"])]
    prefixes = dataset["prefixes"]
    qualified = iso_date(row["Date Qualified"])
    available = iso_date(row["Date Available On Market"])
    configurations = grouped_values(row, prefixes)
    registry = registry_values(row, prefixes)
    configuration_labels = ", ".join(configurations) if configurations else "none printed"
    boundary = (
        f"ENERGY STAR Data Center Storage {label} certification {uid}; "
        f"tested configuration groups: {configuration_labels}"
    )
    observations = [
        observation(
            source_id=source_id,
            uid=uid,
            qualified=qualified,
            field="issuer_identity",
            value={
                "partner": partner,
                "brand_name": row["Brand Name"],
                "model_name": model,
                "model_number": model_number,
                "additional_model_information": row["Additional Model Information"],
                "model_identifier": model_identifier,
            },
            boundary=f"one immutable {label} certification entry",
        ),
        observation(
            source_id=source_id,
            uid=uid,
            qualified=qualified,
            field="registry_attributes",
            value=registry,
            boundary=(
                f"{label} product/controller/software/cooling/reporting attributes; values "
                "are certification-entry observations, not deployment claims"
            ),
        ),
        observation(
            source_id=source_id,
            uid=uid,
            qualified=qualified,
            field="tested_configurations",
            value=configurations,
            boundary=(
                f"{label} ENERGY STAR tested configurations; PSU outputs are nameplates, "
                "cache/device counts are test quantities, and workload metrics retain "
                "their source units and workload labels"
            ),
        ),
        observation(
            source_id=source_id,
            uid=uid,
            qualified=qualified,
            field="market_lifecycle",
            value={
                "date_available_on_market": available,
                "date_qualified": qualified,
                "markets": row["Markets"],
            },
            boundary="issuer certification entry; current deployment and sales status unknown",
        ),
    ]
    cooling = row["Active or Passive Cooling Enabled in Hardware on Shipment"]
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
    if cooling:
        fields.append("cooling_technology")
    evidence = {
        field: {
            "confidence": "high",
            "locator": f"ENERGY STAR certification {uid}",
            "source_publication_dates": {source_id: dataset_updated[:10]},
        }
        for field in fields
    }
    certifications = {
        "energy_star": {
            "certificate": uid,
            "date": qualified,
            "issuer": "U.S. Environmental Protection Agency ENERGY STAR",
            "scope": f"Data Center Storage {label} certification for {model_number}",
            "source_id": source_id,
        }
    }
    external_ids = {
        "energy_star_unique_id": uid,
        "energy_star_model_identifier": model_identifier,
    }
    record: dict[str, object] = {
        "capacity_scope": boundary,
        "certifications_json": compact(certifications),
        "cooling_technology": cooling or None,
        "created_at": RETRIEVED_AT,
        "entity_type": "equipment",
        "equipment_category": "other",
        "evidence_json": compact(evidence),
        "external_ids_json": compact(external_ids),
        "field_sources_json": compact({field: [source_id] for field in fields}),
        "form_factor": f"{product_type}; {controller}",
        "last_verified_at": RETRIEVED_AT,
        "manufacturer": manufacturer,
        "model": model,
        "name": f"{manufacturer} {model} ENERGY STAR storage {label} certification {uid}",
        "notes": (
            "This record is one issuer-certified data-center-storage entry, not an installed "
            "deployment. Tested controller, PSU, cache, storage-device, redundancy and workload "
            "facts remain configuration-bounded observations. PSU nameplates are not normalized "
            "as equipment or rack input; device capacity/counts are not treated as deployed "
            "storage; workload scores are not converted into a generic efficiency percentage."
        ),
        "observations_json": compact(observations),
        "official_url": source_url,
        "power_conditions": (
            f"ENERGY STAR {label} workload-test observations; rated equipment input and rack "
            "input are undisclosed"
        ),
        "power_rating_kind": (
            "PSU nameplates and workload-efficiency observations; no normalized input power"
        ),
        "product_status": (
            "listed in the current ENERGY STAR certified Data Center Storage "
            f"{label} dataset snapshot updated {dataset_updated[:10]}"
        ),
        "quality_status": "source_backed",
        "record_id": stable_id(
            "equipment", manufacturer, "ENERGY STAR data center storage", dataset_kind, uid
        ),
        "record_scope": "configuration",
        "source_urls": [source_url],
        "sources": [source_id],
        "updated_at": RETRIEVED_AT,
        "variant": f"ENERGY STAR {label} {uid}; {model_number}",
    }
    return {key: value for key, value in record.items() if value is not None}


def write_shards(
    records: list[dict[str, object]], *, output_dir: Path, slug: str, shard_size: int
) -> list[Path]:
    paths: list[Path] = []
    for index in range(0, len(records), shard_size):
        part = index // shard_size + 1
        path = output_dir / f"2026-11-05-energy-star-storage-{slug}-part-{part:02d}.jsonl"
        shard = records[index : index + shard_size]
        path.write_text("".join(f"{compact(record)}\n" for record in shard), encoding="utf-8")
        paths.append(path)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("block_csv", type=Path)
    parser.add_argument("file_csv", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--shard-size", type=int, default=25)
    args = parser.parse_args()
    if args.shard_size < 1:
        raise ValueError("--shard-size must be positive")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    all_records: list[dict[str, object]] = []
    for dataset_kind, source_path in (
        ("block_io", args.block_csv),
        ("file_io", args.file_csv),
    ):
        dataset = DATASETS[dataset_kind]
        staged = parse_energy_star_data_center_storage_inventory(
            source_path.read_bytes(),
            source_url=dataset["source_url"],
            dataset_kind=dataset_kind,
            expected_count=dataset["expected_count"],
        )
        records = sorted(
            (build_record(row, dataset_kind=dataset_kind) for row in staged["candidates"]),
            key=lambda record: (
                str(record["manufacturer"]),
                str(record["model"]),
                str(record["variant"]),
            ),
        )
        if len({record["record_id"] for record in records}) != len(records):
            raise ValueError(f"Duplicate {dataset_kind} record IDs")
        paths = write_shards(
            records,
            output_dir=args.output_dir,
            slug=dataset["slug"],
            shard_size=args.shard_size,
        )
        print(f"Wrote {len(records)} {dataset['label']} certifications to {len(paths)} shards")
        all_records.extend(records)
    if len(all_records) != 120 or len({record["record_id"] for record in all_records}) != 120:
        raise ValueError("Expected 120 unique Data Center Storage certifications")


if __name__ == "__main__":
    main()
