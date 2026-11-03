"""Build Dell PowerEdge GPU shipping-limit records and enrich exact matches."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id

RETRIEVED_AT = "2026-11-03T16:24:18Z"
AS_OF = "2026-11-03"
SOURCE_ID = "dell-poweredge-gpu-matrix-202509"
SOURCE_DATE = "2026-10"
SOURCE_URL = (
    "https://www.delltechnologies.com/asset/en-us/products/servers/"
    "briefs-summaries/poweredge-server-gpu-matrix.pdf"
)

ShippingRow = tuple[str, int, str, str, str, int | None, str | None]
SHIPPING: list[ShippingRow] = []


def add(
    generation: str,
    page: int,
    vendor: str,
    accelerator: str,
    platforms: dict[str, int | None],
    *,
    existing_accelerator: str | None = None,
) -> None:
    SHIPPING.extend(
        (
            generation,
            page,
            server,
            vendor,
            accelerator,
            quantity,
            existing_accelerator,
        )
        for server, quantity in platforms.items()
    )


add("17th", 8, "NVIDIA", "RTX Pro 6000 BSE", {"XR8720t": None, "R9815": None})
add("17th", 8, "NVIDIA", "RTX Pro 4500 BSE", {"R9815": None})
add("17th", 8, "NVIDIA", "H200 NVL", {"R9815": None})
add("17th", 8, "NVIDIA", "GB200 NVL4", {"XE8712": None})
add("17th", 8, "NVIDIA", "GB300 NVL72", {"XE9712": 4})
add("17th", 8, "NVIDIA", "B300 AC (x8)", {"XE9785": None, "XE9780": None})
add(
    "17th",
    8,
    "NVIDIA",
    "B200 AC (x8)",
    {"XE9780": None},
    existing_accelerator="B200 AC",
)
add("17th", 8, "NVIDIA", "B300 DLC (x8)", {"XE9785L": None, "XE9780L (GNR SP)": None})
add("17th", 8, "NVIDIA", "B200 DLC (x8)", {"XE9780L (GNR SP)": None})
add(
    "17th",
    8,
    "NVIDIA",
    "RTX Pro 6000 BSE",
    {
        "XE9780L (GNR AP)": None,
        "XE9780L (GNR SP)": None,
        "XE7745": 8,
        "XE7740": 8,
        "R770": 2,
        "R7725": 2,
        "R7715": 3,
    },
    existing_accelerator="RTX Pro 6000 BSE",
)
add(
    "17th",
    8,
    "NVIDIA",
    "RTX Pro 4500 BSE",
    {"XE7745": 8, "XE7740": 8, "R770": 2, "R570": 3, "R7725": 2, "R7715": 3},
)
add(
    "17th",
    8,
    "NVIDIA",
    "H200 NVL",
    {"XE7745": 8, "XE7740": 8, "R770": 2, "R7725": 2, "R7715": 3},
    existing_accelerator="H200 NVL",
)
add("17th", 9, "NVIDIA", "L4", {"R9815": None, "R9825": None})
add(
    "17th",
    9,
    "NVIDIA",
    "L40S",
    {"XE7745": 8, "R770": 2, "R7725": 2, "R7715": 3},
    existing_accelerator="L40S",
)
add(
    "17th",
    9,
    "NVIDIA",
    "L4",
    {
        "R770": 6,
        "R670": 3,
        "R570": 4,
        "R470": 4,
        "R7725": 6,
        "R7715": 6,
        "R6725": 3,
        "R6715": 3,
    },
)
add(
    "17th",
    9,
    "NVIDIA",
    "A16",
    {"R770": 2, "R7725": 2, "R7715": 3},
    existing_accelerator="A16",
)
add(
    "16th",
    9,
    "NVIDIA",
    "L40S",
    {"R760xa": 4, "R760": 2, "R7625": 2, "R7615": 3},
    existing_accelerator="L40S",
)
add(
    "16th",
    9,
    "NVIDIA",
    "L4",
    {"R760xa": 8, "R760": 4, "R760xd2": 2, "R660": 3, "R7625": 4, "R7615": 4},
)
add(
    "16th",
    9,
    "NVIDIA",
    "A16",
    {"R760xa": 4, "R760": 2, "R7625": 2, "R7615": 3},
    existing_accelerator="A16",
)
add("16th", 10, "NVIDIA", "L4", {"R6625": 3, "R6615": 2, "T560": 5})
add(
    "16th",
    10,
    "NVIDIA",
    "L40S",
    {"R960": 4, "XR7620": 2},
    existing_accelerator="L40S",
)
add(
    "16th",
    10,
    "NVIDIA",
    "A16",
    {"R960": 4},
    existing_accelerator="A16",
)
add("16th", 10, "NVIDIA", "L4", {"XR7620": 5, "XR5610": 2, "XR8620t": 3})
add("15th", 10, "NVIDIA", "L4", {"R750": 6, "R650": 3, "R7525": 6})
add(
    "15th",
    10,
    "NVIDIA",
    "A16",
    {"R750": 2, "R7525": 3},
    existing_accelerator="A16",
)
add("17th", 11, "AMD", "MI350P", {"R9815": None, "XE7745": 8, "R7725": 2})
add("17th", 11, "AMD", "MI355X AC (x8)", {"XE9785": None})
add("17th", 11, "AMD", "MI355X DLC (x8)", {"XE9785L": None})
add(
    "17th",
    11,
    "Intel",
    "Gaudi 3 PCIe (x8)",
    {"XE7740": None},
    existing_accelerator="Gaudi 3 PCIe",
)
add(
    "16th",
    11,
    "AMD",
    "MI210",
    {"R760xa": 4, "R7625": 2, "R7615": 3},
    existing_accelerator="MI210",
)
add(
    "15th",
    11,
    "AMD",
    "MI210",
    {"R7525": 3},
    existing_accelerator="MI210",
)

SPECS: dict[str, dict[str, object]] = {
    "RTX Pro 6000 BSE": {
        "summary": "96 GB GDDR7; 1.8 TB/sec; 600 W; PCIe Gen 5x16 (128 GB/sec); DW/FHFL; AI / HPC",
        "power_w": 600,
        "page": 1,
    },
    "RTX Pro 4500 BSE": {
        "summary": "32 GB GDDR7; 800 GB/sec; 165 W; PCIe Gen 5x16 (128 GB/sec); SW/FHFL; AI / HPC",
        "power_w": 165,
        "page": 1,
    },
    "H200 NVL": {
        "summary": (
            "141 GB HBM3e; 4.8 TB/sec; 600 W; PCIe Gen 5x16 (128 GB/sec); "
            "NVLink 4th Gen 900 GB/s; DW/FHFL; AI/HPC"
        ),
        "power_w": 600,
        "page": 1,
    },
    "GB200 NVL4": {
        "summary": (
            "186 GB HBM3; 8 TB/sec; 700 W; PCIe Gen 5x16 (128 GB/sec); NVLink 5th Gen 1.8 TB/s"
        ),
        "power_w": None,
        "page": 1,
    },
    "GB300 NVL72": {
        "summary": (
            "279 GB HBM3; 3 TB/sec; 700 W; PCIe Gen 5x16 (128 GB/sec); NVLink 5th Gen 1.8 TB/s"
        ),
        "power_w": None,
        "page": 1,
    },
    "B300 AC (x8)": {
        "summary": "B300 SXM (x8) AC; 2.1 TB HBM3e; 14.4 TB/sec; 1000 W",
        "power_w": None,
        "page": 1,
    },
    "B200 AC (x8)": {
        "summary": "B200 SXM (x8) AC; 141 GB HBM3e; 7.7 TB/sec; 1000 W",
        "power_w": None,
        "page": 1,
    },
    "B300 DLC (x8)": {
        "summary": "B300 SXM (x8) DLC; 180 GB HBM3e; 7.7 TB/sec; 1000 W",
        "power_w": None,
        "page": 1,
    },
    "B200 DLC (x8)": {
        "summary": "B200 SXM (x8) DLC; 180 GB HBM3e; 7.7 TB/sec; 1000 W",
        "power_w": None,
        "page": 1,
    },
    "L40S": {
        "summary": (
            "48 GB GDDR6; 864 GB/sec; 350 W; PCIe Gen4 x16 (64 GB/sec); "
            "DW/FHFL; AI/Performance graphics/VDI"
        ),
        "power_w": 350,
        "page": 2,
    },
    "L4": {
        "summary": (
            "24 GB GDDR6; 300 GB/s; 72 W; PCIe Gen4 x16 (64GB/sec); SW; "
            "HHHL and FHHL rows; Inferencing/Edge/VDI"
        ),
        "power_w": 72,
        "page": 2,
    },
    "A16": {
        "summary": "64 GB GDDR6; 800 GB/sec; 250 W; PCIe Gen4 x16 (64GB/sec); DW/FHFL; VDI",
        "power_w": 250,
        "page": 2,
    },
    "MI350P": {
        "summary": "144 GB HBM3e; 4 TB/sec; 600 W; PCIe Gen5x16 (128 GB/sec); DW/FHFL; AI / HPC",
        "power_w": 600,
        "page": 1,
    },
    "MI355X AC (x8)": {
        "summary": (
            "MI355X AC; 288 GB HBM3; 8 TB/sec; 1400 W; PCIe Gen5x16 "
            "(128 GB/sec); Infinity Fabric Link 4th Gen 896 GB/sec"
        ),
        "power_w": None,
        "page": 1,
    },
    "MI355X DLC (x8)": {
        "summary": (
            "MI355X DLC (x8); 288 GB HBM3; 8 TB/sec; 1400 W; PCIe Gen5x16 "
            "(128 GB/sec); Infinity Fabric Link 4th Gen 896 GB/sec"
        ),
        "power_w": None,
        "page": 1,
    },
    "Gaudi 3 PCIe (x8)": {
        "summary": (
            "Gaudi 3 PCIe; 128 GB HBM3; 3.7 TB/s; 600 W; PCIe Gen5x16 "
            "(128 GB/sec); RoCE 900GB/s; DW/FHFL; AI / HPC"
        ),
        "power_w": 600,
        "page": 1,
    },
    "MI210": {
        "summary": (
            "64 GB HBM2e; 1638 GB/sec; 300 W; PCIe Gen4x16 (64 GB/sec); "
            "Infinity Fabric Link bridge; DW/FHFL; HPC/Machine learning training"
        ),
        "power_w": 300,
        "page": 1,
    },
}


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def observation(*, field: str, value: object, locator: str, boundary: str) -> dict[str, object]:
    return {
        "as_of": AS_OF,
        "boundary": boundary,
        "field": field,
        "kind": "reported",
        "locator": locator,
        "source_id": SOURCE_ID,
        "unit": None,
        "value": value,
    }


def shipping_observations(
    page: int, server: str, accelerator: str, quantity: int | None
) -> list[dict[str, object]]:
    locator = f"page {page}, shipping table, {server} row / {accelerator} column"
    boundary = f"Dell PowerEdge {server} / {accelerator}; shipping availability"
    rows = [
        observation(field="shipping_status", value="Shipping", locator=locator, boundary=boundary)
    ]
    if quantity is not None:
        rows.append(
            observation(
                field="maximum_shipping_accelerator_quantity",
                value=quantity,
                locator=locator,
                boundary=(
                    f"Dell PowerEdge {server}; OEM maximum number allowed; may differ "
                    "between configurations on the same platform; not installed quantity"
                ),
            )
        )
    if server == "R760xa" and page in {9, 11}:
        rows.append(
            observation(
                field="sku_association_note",
                value=(
                    "Different SKUs are mentioned because platforms might support different "
                    "SKUs; the sheet does not specifically identify platform-SKU associations"
                ),
                locator="page 11, footnote 3",
                boundary=f"Dell PowerEdge {server} shipping quantity footnote",
            )
        )
    return rows


def enrich_record(
    record: dict[str, Any], page: int, accelerator: str, quantity: int | None
) -> None:
    server = str(record["model"]).removeprefix("PowerEdge ")
    observations = json.loads(str(record["observations_json"]))
    existing_keys = {(item.get("field"), item.get("locator")) for item in observations}
    observations.extend(
        item
        for item in shipping_observations(page, server, accelerator, quantity)
        if (item["field"], item["locator"]) not in existing_keys
    )
    record["observations_json"] = compact(observations)
    record["product_status"] = "supported and listed Shipping in Dell October 2026 matrix"
    record["last_verified_at"] = RETRIEVED_AT
    record["updated_at"] = RETRIEVED_AT
    qualifier = (
        f" The shipping table reports a configuration-dependent maximum of {quantity}; "
        "this is not an installed quantity."
        if quantity is not None
        else " The shipping table reports availability without a numeric maximum."
    )
    if qualifier.strip() not in str(record.get("notes", "")):
        record["notes"] = str(record.get("notes", "")) + qualifier


def build_new_record(
    generation: str,
    page: int,
    server: str,
    vendor: str,
    accelerator: str,
    quantity: int | None,
) -> dict[str, Any]:
    spec = SPECS[accelerator]
    identity_accelerator = (
        "L4 (shipping table; SKU unspecified)" if accelerator == "L4" else accelerator
    )
    shipping_locator = f"page {page}, shipping table, {server} row / {accelerator} column"
    spec_locator = f"page {spec['page']}, GPU specification table, {accelerator} row"
    boundary = (
        f"Dell PowerEdge {server} {generation}-generation shipping configuration for "
        f"{vendor} {accelerator}; shipping quantity is an OEM platform maximum, not deployment"
    )
    fields = [
        "capacity_scope",
        "equipment_category",
        "evidence_json",
        "manufacturer",
        "model",
        "name",
        "observations_json",
        "official_url",
        "product_status",
        "record_scope",
        "variant",
    ]
    if spec["power_w"] is not None:
        fields.extend(["accelerator_power_w", "power_conditions", "power_rating_kind"])
    evidence: dict[str, dict[str, object]] = {}
    for field in fields:
        evidence[field] = {
            "confidence": "high",
            "locator": spec_locator if field == "accelerator_power_w" else shipping_locator,
            "source_publication_dates": {SOURCE_ID: SOURCE_DATE},
        }
        if field == "accelerator_power_w":
            evidence[field]["unit"] = "W"
    observations = shipping_observations(page, server, accelerator, quantity)
    observations.append(
        observation(
            field="accelerator_specification_summary",
            value=spec["summary"],
            locator=spec_locator,
            boundary=(
                f"{vendor} {accelerator}; exact source text retained; integrated x8 labels "
                "are not decomposed into per-GPU or server totals"
            ),
        )
    )
    if accelerator == "L4":
        observations.append(
            observation(
                field="platform_sku_binding",
                value="Unspecified between the HHHL and FHHL L4 rows",
                locator="page 11, footnote 3 and page 2 L4 rows",
                boundary=f"Dell PowerEdge {server} / NVIDIA L4 shipping row",
            )
        )
    variant = f"{generation} Generation shipping configuration for {vendor} {accelerator}"
    quantity_note = (
        f" The source reports a maximum of {quantity}, which may differ across "
        "configurations on the platform and is not an installed quantity."
        if quantity is not None
        else " The source reports Shipping without a numeric maximum; quantity remains null."
    )
    record: dict[str, Any] = {
        "capacity_scope": boundary,
        "created_at": RETRIEVED_AT,
        "entity_type": "equipment",
        "equipment_category": "server",
        "evidence_json": compact(evidence),
        "field_sources_json": compact({field: [SOURCE_ID] for field in fields}),
        "last_verified_at": RETRIEVED_AT,
        "manufacturer": "Dell",
        "model": f"PowerEdge {server}",
        "name": f"Dell PowerEdge {server} shipping configuration for {vendor} {accelerator}",
        "notes": (
            "Shipping is an OEM catalogue status, not evidence of customer deployment. "
            "Accelerator labels, specifications and quantities are not multiplied into "
            "server or rack input." + quantity_note
        ),
        "observations_json": compact(observations),
        "official_url": SOURCE_URL,
        "product_status": "listed Shipping in Dell October 2026 matrix",
        "quality_status": "source_backed",
        "record_id": stable_id(
            "equipment",
            "Dell",
            "PowerEdge",
            server,
            vendor,
            identity_accelerator,
            f"{generation} Generation",
        ),
        "record_scope": "configuration",
        "source_urls": [SOURCE_URL],
        "sources": [SOURCE_ID],
        "updated_at": RETRIEVED_AT,
        "variant": variant,
    }
    if spec["power_w"] is not None:
        record["accelerator_power_w"] = spec["power_w"]
        record["power_conditions"] = (
            f"{spec['power_w']} W OEM accelerator maximum; not server or rack input"
        )
        record["power_rating_kind"] = "maximum accelerator power per device"
    return record


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    rows.sort(key=lambda item: str(item["record_id"]))
    path.write_text("".join(f"{compact(row)}\n" for row in rows), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("existing_17g", type=Path)
    parser.add_argument("existing_legacy", type=Path)
    parser.add_argument("new_output", type=Path)
    parser.add_argument("enriched_17g_output", type=Path)
    parser.add_argument("enriched_legacy_output", type=Path)
    args = parser.parse_args()
    rows_17 = read_jsonl(args.existing_17g)
    rows_legacy = read_jsonl(args.existing_legacy)
    by_id = {row["record_id"]: row for row in [*rows_17, *rows_legacy]}
    new_rows: list[dict[str, Any]] = []
    enriched_ids: set[str] = set()
    for generation, page, server, vendor, accelerator, quantity, existing in SHIPPING:
        existing_id = None
        if existing is not None:
            existing_id = stable_id(
                "equipment",
                "Dell",
                "PowerEdge",
                server,
                vendor,
                existing,
                f"{generation} Generation",
            )
        if existing_id is not None and existing_id in by_id:
            enrich_record(by_id[existing_id], page, accelerator, quantity)
            enriched_ids.add(existing_id)
        else:
            new_rows.append(
                build_new_record(generation, page, server, vendor, accelerator, quantity)
            )
    unknown_quantities = sum(quantity is None for *_, quantity, _existing in SHIPPING)
    if len(SHIPPING) != 85 or unknown_quantities != 19:
        raise ValueError(
            f"Unexpected shipping table shape: {len(SHIPPING)} rows, "
            f"{unknown_quantities} without quantities"
        )
    if len(enriched_ids) != 32 or len(new_rows) != 53:
        raise ValueError(
            f"Expected 32 enrichments and 53 additions, got {len(enriched_ids)} and {len(new_rows)}"
        )
    all_ids = [row["record_id"] for row in [*rows_17, *rows_legacy, *new_rows]]
    if len(all_ids) != len(set(all_ids)):
        raise ValueError("Duplicate Dell equipment identities after shipping merge")
    write_jsonl(args.enriched_17g_output, rows_17)
    write_jsonl(args.enriched_legacy_output, rows_legacy)
    write_jsonl(args.new_output, new_rows)
    print(
        f"Processed 85 shipping cells: {len(new_rows)} additions, {len(enriched_ids)} enrichments"
    )


if __name__ == "__main__":
    main()
