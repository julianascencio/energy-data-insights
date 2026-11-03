"""Build reviewed Dell PowerEdge 17th-generation GPU compatibility records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id

RETRIEVED_AT = "2026-11-03T12:23:01Z"
VERIFIED_AT = "2026-11-03T15:21:40Z"
AS_OF = "2026-11-03"
SOURCE_ID = "dell-poweredge-gpu-matrix-202509"
SOURCE_URL = (
    "https://www.delltechnologies.com/asset/en-us/products/servers/"
    "briefs-summaries/poweredge-server-gpu-matrix.pdf"
)

# Compatibility checkmarks in the complete PowerEdge 17th Generation table.
COMPATIBILITY = {
    ("Intel", "Gaudi 3 PCIe"): ("XE7740",),
    ("NVIDIA", "H200 NVL"): ("XE7740", "XE7745", "R770"),
    ("NVIDIA", "H100 NVL"): ("XE7740", "XE7745", "R7715", "R7725", "R570", "R770"),
    ("NVIDIA", "RTX Pro 6000 BSE"): ("XE7740", "XE7745", "R7725", "R770"),
    ("NVIDIA", "B200 AC"): ("XE9780",),
    ("NVIDIA", "L40S"): ("XE7745", "R7715", "R7725", "R570"),
    ("NVIDIA", "A16"): ("XE7740", "R7715", "R7725", "R770"),
    ("NVIDIA", "L4 (HHHL)"): (
        "XE7740",
        "XE7745",
        "R6715",
        "R6725",
        "R7715",
        "R7725",
        "R570",
        "R470",
        "R670",
        "R770",
    ),
}

# Exact labels and conditions from the GPU specification table in the same PDF.
SPECS = {
    "Gaudi 3 PCIe": {
        "memory": "128 GB HBM3",
        "ecc": "Y",
        "bandwidth": "3.7 TB/s",
        "power_text": "600 W",
        "power_w": 600,
        "host": "PCIe Gen5x16 (128 GB/sec)",
        "peer": "RoCE (900GB/s)",
        "slot": "DW",
        "dimensions": "FHFL",
        "workload": "AI / HPC",
    },
    "H200 NVL": {
        "memory": "141GB HBM3e",
        "ecc": "Y",
        "bandwidth": "4.8 TB/sec",
        "power_text": "600 W",
        "power_w": 600,
        "host": "PCIe Gen 5x16 (128 GB/sec)",
        "peer": "NVLink (4th Gen - 900 GB/s)",
        "slot": "DW",
        "dimensions": "FHFL",
        "workload": "AI/HPC",
    },
    "H100 NVL": {
        "memory": "94 GB HBM3",
        "ecc": "Y",
        "bandwidth": "3.9 TB/sec",
        "power_text": "350W- 400W",
        "power_w": None,
        "host": "PCIe Gen 5x16 (128 GB/sec)",
        "peer": "NVLink (4th Gen - 900 GB/s)",
        "slot": "DW",
        "dimensions": "FHFL",
        "workload": "AI / HPC",
    },
    "RTX Pro 6000 BSE": {
        "memory": "96GB GDDR7",
        "ecc": "Y",
        "bandwidth": "1.8 TB/sec",
        "power_text": "600 W",
        "power_w": 600,
        "host": "PCIe Gen 5x16 (128 GB/sec)",
        "peer": "NA",
        "slot": "DW",
        "dimensions": "N/A",
        "workload": "AI / HPC",
    },
    "B200 AC": {
        "memory": "141 GB HBM3e",
        "ecc": "Y",
        "bandwidth": "7.7 TB/sec",
        "power_text": "1000 W",
        "power_w": 1000,
        "host": "PCIe Gen 5x16 (128 GB/sec)",
        "peer": "NVLink (5th Gen - 1.8 TB/s)",
        "slot": "N/A",
        "dimensions": "N/A",
        "workload": "AI / HPC",
        "spec_label": "B200 SXM (x8) AC",
    },
    "L40S": {
        "memory": "48 GB GDDR6",
        "ecc": "Y",
        "bandwidth": "864 GB/sec",
        "power_text": "350 W",
        "power_w": 350,
        "host": "PCIe Gen4 x16 (64 GB/sec)",
        "peer": "N/A",
        "slot": "DW",
        "dimensions": "FHFL",
        "workload": "AI/ Performance graphics/VDI",
    },
    "A16": {
        "memory": "64 GB GDDR6",
        "ecc": "Y",
        "bandwidth": "800 GB/sec",
        "power_text": "250 W",
        "power_w": 250,
        "host": "PCIe Gen4 x16 (64GB/sec)",
        "peer": "N/A",
        "slot": "DW",
        "dimensions": "FHHL",
        "workload": "VDI",
    },
    "L4 (HHHL)": {
        "memory": "24 GB GDDR6",
        "ecc": "Y",
        "bandwidth": "300 GB/s",
        "power_text": "72 W",
        "power_w": 72,
        "host": "PCIe Gen4 x16 (64GB/sec)",
        "peer": "N/A",
        "slot": "SW",
        "dimensions": "HHHL",
        "workload": "Inferencing/Edge/VDI",
        "spec_label": "L4",
    },
}


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def observation(
    *, field: str, value: object, unit: str | None, locator: str, boundary: str
) -> dict[str, object]:
    return {
        "as_of": AS_OF,
        "boundary": boundary,
        "field": field,
        "kind": "reported",
        "locator": locator,
        "source_id": SOURCE_ID,
        "unit": unit,
        "value": value,
    }


def build_record(vendor: str, accelerator: str, server: str) -> dict[str, object]:
    spec = SPECS[accelerator]
    compatibility_locator = (
        f"page 4, PowerEdge 17th Generation servers table, "
        f"{accelerator} row / {server} column checkmark"
    )
    spec_label = str(spec.get("spec_label", accelerator))
    spec_locator = f"page 1, GPU specification table, {spec_label} row"
    boundary = (
        f"Dell PowerEdge {server} support for {vendor} {accelerator}; "
        "accelerator count and server/rack input power undisclosed"
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
    power_w = spec["power_w"]
    if power_w is not None:
        fields.append("accelerator_power_w")
    evidence: dict[str, dict[str, object]] = {}
    for field in fields:
        locator = spec_locator if field == "accelerator_power_w" else compatibility_locator
        evidence[field] = {
            "confidence": "high",
            "locator": locator,
            "source_publication_dates": {SOURCE_ID: "2026-10"},
        }
        if field == "accelerator_power_w":
            evidence[field]["unit"] = "W"
    observations = [
        observation(
            field="server_accelerator_compatibility",
            value="supported",
            unit=None,
            locator=compatibility_locator,
            boundary=boundary,
        ),
        observation(
            field="accelerator_memory_per_device",
            value=spec["memory"],
            unit=None,
            locator=spec_locator,
            boundary=f"{vendor} {spec_label}; per accelerator",
        ),
        observation(
            field="memory_ecc",
            value=spec["ecc"],
            unit=None,
            locator=spec_locator,
            boundary=f"{vendor} {spec_label}; accelerator memory",
        ),
        observation(
            field="accelerator_memory_bandwidth",
            value=spec["bandwidth"],
            unit=None,
            locator=spec_locator,
            boundary=f"{vendor} {spec_label}; source precision retained",
        ),
        observation(
            field="accelerator_max_power",
            value=spec["power_text"],
            unit=None,
            locator=spec_locator,
            boundary=f"{vendor} {spec_label}; per accelerator, not server or rack input",
        ),
        observation(
            field="host_interface",
            value=spec["host"],
            unit=None,
            locator=spec_locator,
            boundary=f"{vendor} {spec_label}",
        ),
        observation(
            field="peer_interconnect",
            value=spec["peer"],
            unit=None,
            locator=spec_locator,
            boundary=f"{vendor} {spec_label}",
        ),
        observation(
            field="accelerator_form_factor",
            value=f"{spec['slot']} / {spec['dimensions']}",
            unit=None,
            locator=spec_locator,
            boundary=f"{vendor} {spec_label}",
        ),
        observation(
            field="suggested_workload",
            value=spec["workload"],
            unit=None,
            locator=spec_locator,
            boundary="OEM suggestion; not a measured performance result",
        ),
    ]
    variant = f"17th Generation support for {vendor} {accelerator}"
    record: dict[str, object] = {
        "capacity_scope": boundary,
        "created_at": RETRIEVED_AT,
        "entity_type": "equipment",
        "equipment_category": "server",
        "evidence_json": compact(evidence),
        "field_sources_json": compact({field: [SOURCE_ID] for field in fields}),
        "last_verified_at": VERIFIED_AT,
        "manufacturer": "Dell",
        "model": f"PowerEdge {server}",
        "name": f"Dell PowerEdge {server} with supported {vendor} {accelerator}",
        "notes": (
            "The OEM compatibility checkmark documents a supported pairing, not an "
            "installed configuration or accelerator quantity. Accelerator specifications "
            "remain per-device observations; server input power, rack power, CPU, system "
            "memory and performance are null. Suggested workloads are not benchmarks."
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
            "equipment", "Dell", "PowerEdge", server, vendor, accelerator, "17th Generation"
        ),
        "record_scope": "configuration",
        "source_urls": [SOURCE_URL],
        "sources": [SOURCE_ID],
        "updated_at": VERIFIED_AT,
        "variant": variant,
    }
    if power_w is not None:
        record["accelerator_power_w"] = power_w
    if accelerator == "B200 AC":
        record["notes"] = (
            str(record["notes"])
            + " The compatibility table abbreviates B200 AC; the specification table "
            "labels the corresponding air-cooled row B200 SXM (x8) AC. No count is "
            "normalized onto this server-pair record."
        )
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = [
        build_record(vendor, accelerator, server)
        for (vendor, accelerator), servers in COMPATIBILITY.items()
        for server in servers
    ]
    if len(rows) != 33 or len({row["record_id"] for row in rows}) != 33:
        raise ValueError("Expected 33 unique Dell server/accelerator records")
    rows.sort(key=lambda item: str(item["record_id"]))
    args.output.write_text("".join(f"{compact(row)}\n" for row in rows), encoding="utf-8")
    print(f"Wrote {len(rows)} reviewed Dell compatibility records to {args.output}")


if __name__ == "__main__":
    main()
