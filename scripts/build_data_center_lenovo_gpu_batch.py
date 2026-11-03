"""Build reviewed Lenovo current GPU-option records from captured official HTML."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.inventories import (
    parse_lenovo_gpu_comparison,
)

RETRIEVED_AT = "2026-11-03T13:26:00Z"
AS_OF = "2026-11-03"
SOURCE_ID = "lenovo-thinksystem-gpu-comparison-20261103"
SOURCE_URL = "https://lenovopress.lenovo.com/lp2265-thinksystem-gpu-comparison"
SOURCE_SHA256 = "6da0a8ad63d22b7ab9d2295225f1456c0afeedd72dee38c858c374d255627c19"


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def observation(*, field: str, value: object, unit: str | None, boundary: str) -> dict[str, object]:
    return {
        "as_of": AS_OF,
        "boundary": boundary,
        "field": field,
        "kind": "reported",
        "locator": "current comparison row and named attribute",
        "source_id": SOURCE_ID,
        "unit": unit,
        "value": value,
    }


def performance_unit(label: str) -> str | None:
    match = re.search(r"\((TFLOPS|TOPS|PFLOPS)\)$", label)
    return match.group(1) if match else None


def performance_field(label: str) -> str:
    value = label.casefold().replace("bfloat16", "bf16")
    precision = next(
        (
            token
            for token in ("fp64", "fp32", "tf32", "fp16", "bf16", "fp8", "int8", "fp4")
            if token in value
        ),
        "unspecified",
    )
    return f"peak_{precision}_{'sparse_' if 'sparsity' in value else ''}performance"


def build_record(candidate: dict[str, Any]) -> dict[str, object]:
    model = str(candidate["description"])
    feature = str(candidate["feature_code"])
    part = str(candidate["part_number"])
    identity = feature if part == "CTO Only" else part
    gpu_count = int(candidate["gpu_count"])
    tdp = float(candidate["tdp_w_per_gpu"])
    power_conflict = candidate["product_name"] == "NVIDIA HGX H200 4-GPU Board"
    fields = [
        "capacity_scope",
        "equipment_category",
        "evidence_json",
        "external_ids_json",
        "form_factor",
        "manufacturer",
        "memory_bandwidth_gb_s",
        "memory_gb",
        "memory_type",
        "model",
        "name",
        "observations_json",
        "official_url",
        "power_conditions",
        "power_rating_kind",
        "product_status",
        "record_scope",
        "variant",
        "accelerator_count",
    ]
    if not power_conflict:
        fields.append("accelerator_power_w")
    else:
        fields.append("conflicts_json")
    evidence = {
        field: {
            "confidence": "high",
            "locator": f"current comparison row {candidate['product_name']} ({identity})",
            "source_publication_dates": {SOURCE_ID: "2026-10-26"},
        }
        for field in fields
    }
    if "accelerator_power_w" in evidence:
        evidence["accelerator_power_w"]["unit"] = "W"
    evidence["memory_gb"]["unit"] = "GB"
    evidence["memory_bandwidth_gb_s"]["unit"] = "GB/s"
    boundary = (
        f"Lenovo ThinkSystem orderable option {identity}; {gpu_count} GPUs on the option; "
        "values described per GPU remain per GPU"
    )
    observations = [
        observation(field="availability", value="Available", unit=None, boundary=boundary),
        observation(
            field="announcement_date",
            value=candidate["announcement_date"],
            unit=None,
            boundary=boundary,
        ),
        observation(
            field="accelerator_quantity_in_option",
            value=gpu_count,
            unit="GPU",
            boundary="OEM option assembly; not evidence of an installed deployment",
        ),
        observation(
            field="accelerator_form_factor",
            value=candidate["form_factor"],
            unit=None,
            boundary=boundary,
        ),
        observation(
            field="accelerator_architecture",
            value=candidate["architecture"],
            unit=None,
            boundary="per GPU",
        ),
        observation(
            field="accelerator_memory_per_gpu",
            value=candidate["memory_gb_per_gpu"],
            unit="GB",
            boundary=f"{candidate['memory_type']}; per GPU, not option total",
        ),
        observation(
            field="accelerator_memory_bandwidth_per_gpu",
            value=candidate["memory_bandwidth_gbps_per_gpu"],
            unit="GB/s",
            boundary="per GPU, source precision retained",
        ),
        observation(
            field="accelerator_tdp_max",
            value=tdp,
            unit="W",
            boundary="per GPU; not server or rack input power",
        ),
        observation(
            field="cooling_method",
            value=candidate["cooling_method"],
            unit=None,
            boundary="GPU option cooling method",
        ),
    ]
    optional = {
        "host_interface": candidate.get("host_interface"),
        "nvlink": candidate.get("nvlink"),
        "interconnect_bandwidth": candidate.get("interconnect"),
        "multi_instance_gpu": candidate.get("mig"),
        "withdrawal_date": candidate.get("withdrawal_date"),
    }
    for field, value in optional.items():
        if value is not None:
            observations.append(
                observation(field=field, value=value, unit=None, boundary="per GPU option")
            )
    for label, value in candidate["performance"].items():
        observations.append(
            observation(
                field=performance_field(label),
                value=value,
                unit=performance_unit(label),
                boundary=(
                    "per GPU; theoretical OEM comparison value; "
                    + (
                        "with sparsity"
                        if "sparsity" in label.casefold()
                        else "without stated sparsity"
                    )
                ),
            )
        )
    if power_conflict:
        observations.append(
            observation(
                field="description_power_claim",
                value="700W",
                unit=None,
                boundary="product description; conflicts with 350 W TDP attribute",
            )
        )
    external_ids = {"lenovo_feature_code": feature}
    if part != "CTO Only":
        external_ids["lenovo_part_number"] = part
    variant = f"{identity}; {gpu_count}-GPU option; {candidate['cooling_method']}"
    notes = (
        "This is an exact Lenovo orderable GPU option or CTO feature, not an installed "
        "deployment. GPU quantity describes the option assembly. Per-GPU TDP, memory, "
        "bandwidth and performance are not multiplied into option, server or rack totals. "
        "Performance values retain the OEM table's precision and sparsity labels; no "
        "workload benchmark or test result is inferred."
    )
    if power_conflict:
        notes += (
            " The H200 4-GPU description says 700W while the TDP attribute says 350 W; "
            "both are retained as observations and accelerator_power_w remains null."
        )
    record: dict[str, object] = {
        "capacity_scope": boundary,
        "created_at": RETRIEVED_AT,
        "entity_type": "equipment",
        "equipment_category": "gpu_accelerator",
        "evidence_json": compact(evidence),
        "external_ids_json": compact(external_ids),
        "field_sources_json": compact({field: [SOURCE_ID] for field in fields}),
        "last_verified_at": RETRIEVED_AT,
        "manufacturer": "Lenovo",
        "memory_bandwidth_gb_s": candidate["memory_bandwidth_gbps_per_gpu"],
        "memory_gb": candidate["memory_gb_per_gpu"],
        "memory_type": candidate["memory_type"],
        "model": model,
        "name": f"Lenovo {model}",
        "notes": notes,
        "observations_json": compact(observations),
        "official_url": SOURCE_URL,
        "power_conditions": (
            f"{tdp:g} W TDP maximum per GPU in Lenovo comparison; {gpu_count}-GPU option "
            "quantity is not multiplied; server and rack input undisclosed"
        ),
        "power_rating_kind": "maximum accelerator TDP per GPU",
        "product_status": f"Available in Lenovo comparison as of {AS_OF}",
        "quality_status": "source_backed",
        "record_id": stable_id("equipment", "Lenovo", model, identity),
        "record_scope": "configuration",
        "accelerator_count": gpu_count,
        "form_factor": candidate["form_factor"],
        "source_urls": [SOURCE_URL],
        "sources": [SOURCE_ID],
        "updated_at": RETRIEVED_AT,
        "variant": variant,
    }
    if not power_conflict:
        record["accelerator_power_w"] = tdp
    else:
        record["conflicts_json"] = compact(
            {
                "accelerator_power_w": [
                    {
                        "boundary": "Lenovo feature C3V2; product description",
                        "field": "accelerator_power_w",
                        "observed_at": RETRIEVED_AT,
                        "sources": [SOURCE_ID],
                        "unit": "W",
                        "value": 700,
                    },
                    {
                        "boundary": "Lenovo feature C3V2; TDP attribute",
                        "field": "accelerator_power_w",
                        "observed_at": RETRIEVED_AT,
                        "sources": [SOURCE_ID],
                        "unit": "W",
                        "value": 350,
                    },
                ]
            }
        )
        record["quality_status"] = "needs_review"
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_html", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    staged = parse_lenovo_gpu_comparison(
        args.source_html.read_bytes(), source_url=SOURCE_URL, expected_count=20
    )
    if staged["sha256"] != SOURCE_SHA256:
        raise ValueError("Lenovo source bytes differ from reviewed capture")
    rows = [build_record(candidate) for candidate in staged["candidates"]]
    if len(rows) != 20 or len({row["record_id"] for row in rows}) != 20:
        raise ValueError("Expected 20 unique Lenovo current GPU options")
    rows.sort(key=lambda item: str(item["record_id"]))
    args.output.write_text("".join(f"{compact(row)}\n" for row in rows), encoding="utf-8")
    print(f"Wrote {len(rows)} reviewed Lenovo GPU-option records to {args.output}")


if __name__ == "__main__":
    main()
