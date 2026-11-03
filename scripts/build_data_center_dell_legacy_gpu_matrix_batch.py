"""Build reviewed Dell PowerEdge 16th/15th-generation GPU support records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id

RETRIEVED_AT = "2026-11-03T15:21:40Z"
AS_OF = "2026-11-03"
# Retain the established source identifier so existing field evidence remains stable.
SOURCE_ID = "dell-poweredge-gpu-matrix-202509"
SOURCE_URL = (
    "https://www.delltechnologies.com/asset/en-us/products/servers/"
    "briefs-summaries/poweredge-server-gpu-matrix.pdf"
)
SOURCE_DATE = "2026-10"

# Every supported checkmark in the complete tables on printed pages 5-7.
COMPATIBILITY: dict[tuple[str, str, str, int], tuple[str, ...]] = {
    ("16th", "AMD", "MI210", 5): ("R760xa",),
    ("16th", "Intel", "Flex 140", 5): ("R760xa", "R760", "R660"),
    ("16th", "NVIDIA", "H100 NVL", 5): ("R760xa",),
    ("16th", "NVIDIA", "L40S", 5): ("R760xa", "R760"),
    ("16th", "NVIDIA", "L40", 5): ("R760xa", "R760"),
    ("16th", "NVIDIA", "A16", 5): ("R760xa", "R760"),
    ("16th", "NVIDIA", "L4 (HHHL)", 5): ("R660",),
    ("16th", "NVIDIA", "L4 (FHHL)", 5): (
        "R760xa",
        "R760",
        "R760xd2",
        "R660",
    ),
    ("16th", "NVIDIA", "A2 (v2) (HHHL)", 5): ("R760xa", "R760xs"),
    ("16th", "AMD", "MI210", 6): ("R7625", "R7615"),
    ("16th", "NVIDIA", "H100 NVL", 6): ("R7625", "R7615"),
    ("16th", "NVIDIA", "L40S", 6): ("R7625", "R7615", "R960", "XR7620"),
    ("16th", "NVIDIA", "L40", 6): ("R7625", "R7615", "T560"),
    ("16th", "NVIDIA", "A16", 6): ("R7625", "R7615", "R960"),
    ("16th", "NVIDIA", "L4 (HHHL)", 6): ("XR7620",),
    ("16th", "NVIDIA", "L4 (FHHL)", 6): (
        "R7625",
        "R7615",
        "R6625",
        "R6615",
        "T560",
        "XR8620t",
        "XR7620",
        "XR5610",
    ),
    ("16th", "NVIDIA", "A2 (v2) (HHHL)", 6): ("C6620", "XR7620", "HS5620"),
    ("16th", "NVIDIA", "A2 (v2) (FHHL)", 6): (
        "R7625",
        "R7615",
        "R6625",
        "R6615",
        "T360",
        "T560",
        "XR7620",
        "XR5610",
    ),
    ("15th", "AMD", "MI210", 7): ("R7525",),
    ("15th", "Intel", "Flex 140", 7): ("R750", "R650"),
    ("15th", "NVIDIA", "L40", 7): ("R750", "R7525"),
    ("15th", "NVIDIA", "A16", 7): ("R750", "R7525"),
    ("15th", "NVIDIA", "L4 (HHHL)", 7): ("R750", "R650", "R7525"),
    ("15th", "NVIDIA", "L4 (FHHL)", 7): ("R750", "R650", "R7525"),
    ("15th", "NVIDIA", "A2 (v2) (HHHL)", 7): (
        "R750",
        "R650",
        "R6525",
        "R7525",
    ),
    ("15th", "NVIDIA", "A2 (v2) (FHHL)", 7): (
        "R750",
        "R650",
        "R6525",
        "R7525",
    ),
    ("15th", "NVIDIA", "A10", 7): ("R750", "R7525"),
}

SPECS: dict[str, dict[str, object]] = {
    "MI210": {
        "memory": "64 GB HBM2e",
        "ecc": "Y",
        "bandwidth": "1638 GB/sec",
        "power_text": "300W",
        "power_w": 300,
        "host": "PCIe Gen4x16 (64 GB/sec)",
        "peer": "Infinity Fabric Link bridge",
        "form": "DW / FHFL",
        "auxiliary": "CPU 8 pin",
        "workload": "HPC/Machine learning training",
    },
    "Flex 140": {
        "memory": "12 GB GDDR6",
        "ecc": "Y",
        "bandwidth": "336 GB/Sec",
        "power_text": "75W",
        "power_w": 75,
        "host": "PCIe Gen4 x8 (32 GB/sec)",
        "peer": "XeLink bridge (336 GB/sec)",
        "form": "SW / HHHL/FHHL",
        "auxiliary": "N/A",
        "workload": "Inferencing/Edge",
    },
    "H100 NVL": {
        "memory": "94 GB HBM3",
        "ecc": "Y",
        "bandwidth": "3.9 TB/sec",
        "power_text": "350W- 400W",
        "power_w": None,
        "host": "PCIe Gen 5x16 (128 GB/sec)",
        "peer": "NVLink (4th Gen - 900 GB/s)",
        "form": "DW / FHFL",
        "auxiliary": "PCIe 16 pin",
        "workload": "AI / HPC",
    },
    "L40S": {
        "memory": "48 GB GDDR6",
        "ecc": "Y",
        "bandwidth": "864 GB/sec",
        "power_text": "350W",
        "power_w": 350,
        "host": "PCIe Gen4 x16 (64 GB/sec)",
        "peer": "N/A",
        "form": "DW / FHFL",
        "auxiliary": "PCIe 16 pin",
        "workload": "AI/Performance graphics/VDI",
    },
    "L40": {
        "memory": "48 GB GDDR6",
        "ecc": "Y",
        "bandwidth": "864 GB/sec",
        "power_text": "300W",
        "power_w": 300,
        "host": "PCIe Gen4 x16 (64 GB/sec)",
        "peer": "N/A",
        "form": "DW / FHFL",
        "auxiliary": "PCIe 16 pin",
        "workload": "Performance graphics/VDI",
    },
    "A16": {
        "memory": "64 GB GDDR6",
        "ecc": "Y",
        "bandwidth": "800 GB/sec",
        "power_text": "250W",
        "power_w": 250,
        "host": "PCIe Gen4 x16 (64GB/sec)",
        "peer": "N/A",
        "form": "DW / FHFL",
        "auxiliary": "CPU 8 pin",
        "workload": "VDI",
    },
    "L4 (HHHL)": {
        "memory": "24 GB GDDR6",
        "ecc": "Y",
        "bandwidth": "300 GB/s",
        "power_text": "72W",
        "power_w": 72,
        "host": "PCIe Gen4 x16 (64GB/sec)",
        "peer": "N/A",
        "form": "SW / HHHL",
        "auxiliary": "N/A",
        "workload": "Inferencing/Edge/VDI",
        "spec_label": "L4",
    },
    "L4 (FHHL)": {
        "memory": "24 GB GDDR6",
        "ecc": "Y",
        "bandwidth": "300 GB/s",
        "power_text": "72W",
        "power_w": 72,
        "host": "PCIe Gen4 x16 (64GB/sec)",
        "peer": "N/A",
        "form": "SW / FHHL",
        "auxiliary": "N/A",
        "workload": "Inferencing/Edge/VDI",
        "spec_label": "L4",
    },
    "A2 (v2) (HHHL)": {
        "memory": "16 GB GDDR6",
        "ecc": "Y",
        "bandwidth": "200 GB/sec",
        "power_text": "60W",
        "power_w": 60,
        "host": "PCIe Gen4 x8 (32 GB/sec)",
        "peer": "N/A",
        "form": "SW / HHHL",
        "auxiliary": "N/A",
        "workload": "Inferencing/Edge/VDI",
        "spec_label": "A2 (v2)",
    },
    "A2 (v2) (FHHL)": {
        "memory": "16 GB GDDR6",
        "ecc": "Y",
        "bandwidth": "200 GB/sec",
        "power_text": "60W",
        "power_w": 60,
        "host": "PCIe Gen4 x8 (32 GB/sec)",
        "peer": "N/A",
        "form": "SW / FHHL",
        "auxiliary": "N/A",
        "workload": "Inferencing/Edge/VDI",
        "spec_label": "A2 (v2)",
    },
    "A10": {
        "memory": "24 GB GDDR6",
        "ecc": "Y",
        "bandwidth": "600 GB/sec",
        "power_text": "150W",
        "power_w": 150,
        "host": "PCIe Gen4 x16 (64GB/sec)",
        "peer": "N/A",
        "form": "SW / FHFL",
        "auxiliary": "PCIe 8 pin",
        "workload": "mainstream graphics/VDI",
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


def build_record(
    generation: str, vendor: str, accelerator: str, page: int, server: str
) -> dict[str, object]:
    spec = SPECS[accelerator]
    compatibility_locator = (
        f"page {page}, PowerEdge {generation} Generation servers table, "
        f"{accelerator} row / {server} column checkmark"
    )
    spec_label = str(spec.get("spec_label", accelerator))
    spec_page = 1 if accelerator in {"MI210", "Flex 140", "H100 NVL"} else 2
    spec_locator = f"page {spec_page}, GPU specification table, {spec_label} row"
    boundary = (
        f"Dell PowerEdge {server} {generation}-generation support for "
        f"{vendor} {accelerator}; accelerator count and server/rack input undisclosed"
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
        "power_conditions",
        "power_rating_kind",
        "product_status",
        "record_scope",
        "variant",
    ]
    if spec["power_w"] is not None:
        fields.append("accelerator_power_w")
    evidence: dict[str, dict[str, object]] = {}
    for field in fields:
        evidence[field] = {
            "confidence": "high",
            "locator": spec_locator if field == "accelerator_power_w" else compatibility_locator,
            "source_publication_dates": {SOURCE_ID: SOURCE_DATE},
        }
        if field == "accelerator_power_w":
            evidence[field]["unit"] = "W"
    observations = [
        observation(
            field="server_accelerator_compatibility",
            value="supported",
            locator=compatibility_locator,
            boundary=boundary,
        )
    ]
    for field, value, suffix in (
        ("accelerator_memory_per_device", spec["memory"], "; per accelerator"),
        ("memory_ecc", spec["ecc"], "; accelerator memory"),
        ("accelerator_memory_bandwidth", spec["bandwidth"], "; source precision retained"),
        (
            "accelerator_max_power",
            spec["power_text"],
            "; per accelerator, not server or rack input",
        ),
        ("host_interface", spec["host"], ""),
        ("peer_interconnect", spec["peer"], ""),
        ("accelerator_form_factor", spec["form"], ""),
        ("auxiliary_power_cable", spec["auxiliary"], ""),
        ("suggested_workload", spec["workload"], "; OEM suggestion, not a benchmark"),
    ):
        observations.append(
            observation(
                field=field,
                value=value,
                locator=spec_locator,
                boundary=f"{vendor} {spec_label}{suffix}",
            )
        )
    variant = f"{generation} Generation support for {vendor} {accelerator}"
    record: dict[str, object] = {
        "capacity_scope": boundary,
        "created_at": RETRIEVED_AT,
        "entity_type": "equipment",
        "equipment_category": "server",
        "evidence_json": compact(evidence),
        "field_sources_json": compact({field: [SOURCE_ID] for field in fields}),
        "last_verified_at": RETRIEVED_AT,
        "manufacturer": "Dell",
        "model": f"PowerEdge {server}",
        "name": f"Dell PowerEdge {server} with supported {vendor} {accelerator}",
        "notes": (
            "The OEM checkmark establishes a generation-specific supported pairing, not "
            "an installed configuration or accelerator quantity. Per-device specifications "
            "remain observations; server input, rack input, CPU, system memory and measured "
            "performance are null. Suggested workloads are not benchmarks."
        ),
        "observations_json": compact(observations),
        "official_url": SOURCE_URL,
        "power_conditions": (
            f"{spec['power_text']} OEM maximum per {vendor} {spec_label} accelerator; "
            "accelerator count, server input and rack input undisclosed"
        ),
        "power_rating_kind": "maximum accelerator power per device",
        "product_status": "supported in Dell October 2026 PowerEdge GPU matrix",
        "quality_status": "source_backed",
        "record_id": stable_id(
            "equipment",
            "Dell",
            "PowerEdge",
            server,
            vendor,
            accelerator,
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
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = [
        build_record(generation, vendor, accelerator, page, server)
        for (generation, vendor, accelerator, page), servers in COMPATIBILITY.items()
        for server in servers
    ]
    generation_counts = {
        generation: sum(str(row["variant"]).startswith(generation) for row in rows)
        for generation in ("16th", "15th")
    }
    if generation_counts != {"16th": 52, "15th": 23}:
        raise ValueError(f"Unexpected generation counts: {generation_counts}")
    if len(rows) != 75 or len({row["record_id"] for row in rows}) != 75:
        raise ValueError("Expected 75 unique Dell server/accelerator records")
    rows.sort(key=lambda item: str(item["record_id"]))
    args.output.write_text("".join(f"{compact(row)}\n" for row in rows), encoding="utf-8")
    print(f"Wrote {len(rows)} reviewed Dell compatibility records to {args.output}")


if __name__ == "__main__":
    main()
