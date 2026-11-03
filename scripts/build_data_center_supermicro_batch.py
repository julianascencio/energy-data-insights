"""Build reviewed current Supermicro HGX B200/B300 system configurations."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.inventories import (
    parse_supermicro_nvidia_systems,
)

RETRIEVED_AT = "2026-11-03T14:19:14Z"
AS_OF = "2026-11-03"
TABLE_SOURCE_ID = "supermicro-nvidia-certified-systems-20261103"
TABLE_URL = "https://www.supermicro.com/en/accelerators/nvidia-certified-systems"
TABLE_SHA256 = "48053551be2d5fef3269682da3a16f41631e45f88d382f6eb42e22bdc8a89d44"
PRODUCT_SOURCES = {
    "SYS-422GS-NBRT-LCC": {
        "id": "supermicro-sys-422gs-nbrt-lcc-20261103",
        "url": "https://www.supermicro.com/en/products/system/gpu/4u/sys-422gs-nbrt-lcc",
        "sha256": "25b23774c3714bd026bce32da4f2ac79ebac2a0a8736ebb0eb6f9c72683f7396",
    },
    "SYS-822GS-NBRT": {
        "id": "supermicro-sys-822gs-nbrt-20261103",
        "url": "https://www.supermicro.com/en/products/system/gpu/8u/sys-822gs-nbrt",
        "sha256": "d20475f77fd0e3677735d194fd6cda1536eb37930ec140c479baf2b9f0386556",
    },
}
PRODUCT_DETAILS = {
    "SYS-422GS-NBRT-LCC": {
        "accelerator_model": "NVIDIA SXM HGX B200 8-GPU (180GB)",
        "accelerator_count": 8,
        "accelerator_form_factor": "SXM",
        "accelerator_power_w_per_gpu": None,
        "memory_gb_per_gpu": 180.0,
        "memory_type": "HBM3E",
        "cpu_family": "Intel Xeon 6700 series processors with P-cores",
        "cpu_count": 2,
        "cooling_method": "direct-to-chip liquid cooling",
        "form_factor": "4U rackmount",
        "width_mm": 448.0,
        "height_mm": 174.0,
        "depth_mm": 991.4,
        "weight_kg": 85.0,
        "temperature_min_c": 10.0,
        "temperature_max_c": 35.0,
        "redundancy": "four 6600 W hot-plug PSUs, 2+2 redundant",
        "psu_efficiency": "Titanium Level (96%)",
        "psu_input": "5900-6600 W across stated 200-240 Vac ranges at 50-60 Hz",
        "locator": "current product page key features and specifications tables",
    },
    "SYS-822GS-NBRT": {
        "form_factor": "8U rackmount",
        "width_mm": 449.0,
        "height_mm": 356.0,
        "depth_mm": 950.0,
        "weight_kg": 133.0,
        "temperature_min_c": 10.0,
        "temperature_max_c": 35.0,
        "redundancy": "six 6600 W PSUs, 3+3 redundant",
        "psu_efficiency": "Titanium Level (96%)",
        "psu_input": "5900-6600 W across stated 200-240 Vac ranges at 50-60 Hz",
        "cooling_method": "air-cooled",
        "locator": "current product page key features and specifications tables",
    },
}


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def observation(
    *, source_id: str, field: str, value: object, unit: str | None, locator: str, boundary: str
) -> dict[str, object]:
    return {
        "as_of": AS_OF,
        "boundary": boundary,
        "field": field,
        "kind": "reported",
        "locator": locator,
        "source_id": source_id,
        "unit": unit,
        "value": value,
    }


def model_memory_from_label(label: str) -> float | None:
    match = re.search(r"\((\d+)GB\)", label)
    return float(match.group(1)) if match else None


def build_record(candidate: dict[str, Any]) -> dict[str, object]:
    model = str(candidate["model"])
    product = PRODUCT_SOURCES.get(model)
    details = PRODUCT_DETAILS.get(model, {})
    sources = [TABLE_SOURCE_ID] if model != "SYS-422GS-NBRT-LCC" else []
    urls = [TABLE_URL] if sources else []
    if product:
        sources.append(str(product["id"]))
        urls.append(str(product["url"]))
    source_id = sources[0]
    locator = str(candidate["locator"])
    if model == "SYS-422GS-NBRT-LCC":
        locator = str(details["locator"])
    boundary = (
        f"Supermicro {model} integrated system with {candidate['accelerator_count']} "
        f"{candidate['accelerator_model']}; per-GPU values are not server or rack input"
    )
    label_memory = model_memory_from_label(str(candidate["accelerator_model"]))
    table_memory = float(candidate["memory_gb_per_gpu"])
    memory_conflict = label_memory is not None and label_memory != table_memory
    fields = [
        "accelerator_count",
        "accelerator_power_w",
        "capacity_scope",
        "equipment_category",
        "evidence_json",
        "external_ids_json",
        "manufacturer",
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
    ]
    if candidate.get("accelerator_power_w_per_gpu") is None:
        fields.remove("accelerator_power_w")
    if not memory_conflict:
        fields.append("memory_gb")
    else:
        fields.append("conflicts_json")
    for key in (
        "cooling_method",
        "form_factor",
        "width_mm",
        "height_mm",
        "depth_mm",
        "weight_kg",
        "temperature_min_c",
        "temperature_max_c",
        "redundancy",
    ):
        if key in details:
            fields.append("cooling_technology" if key == "cooling_method" else key)
    fields = sorted(set(fields))
    evidence: dict[str, dict[str, object]] = {}
    for field in fields:
        field_source = (
            str(product["id"])
            if product
            and field
            in {
                "cooling_technology",
                "form_factor",
                "width_mm",
                "height_mm",
                "depth_mm",
                "weight_kg",
                "temperature_min_c",
                "temperature_max_c",
                "redundancy",
            }
            else source_id
        )
        evidence[field] = {
            "confidence": "high",
            "locator": str(details["locator"]) if field_source != TABLE_SOURCE_ID else locator,
            "retrieved_at": RETRIEVED_AT,
            "source_publication_dates": {},
        }
        units = {
            "accelerator_power_w": "W",
            "memory_gb": "GB",
            "width_mm": "mm",
            "height_mm": "mm",
            "depth_mm": "mm",
            "weight_kg": "kg",
            "temperature_min_c": "degC",
            "temperature_max_c": "degC",
        }
        if field in units:
            evidence[field]["unit"] = units[field]
    observations = [
        observation(
            source_id=source_id,
            field="integrated_accelerator",
            value=candidate["accelerator_model"],
            unit=None,
            locator=locator,
            boundary=boundary,
        ),
        observation(
            source_id=source_id,
            field="accelerator_quantity_in_system",
            value=candidate["accelerator_count"],
            unit="GPU",
            locator=locator,
            boundary="exact integrated system; not installed deployment evidence",
        ),
        observation(
            source_id=source_id,
            field="accelerator_form_factor",
            value=candidate["accelerator_form_factor"],
            unit=None,
            locator=locator,
            boundary="accelerator within exact system",
        ),
        observation(
            source_id=source_id,
            field="accelerator_memory_per_gpu",
            value=table_memory,
            unit="GB",
            locator=locator,
            boundary=f"{candidate['memory_type']}; per GPU, table memory column",
        ),
        observation(
            source_id=source_id,
            field="accelerator_configurable_power_limit",
            value=candidate.get("accelerator_power_w_per_gpu"),
            unit="W",
            locator=locator,
            boundary="per GPU; not server or rack input",
        )
        if candidate.get("accelerator_power_w_per_gpu") is not None
        else observation(
            source_id=source_id,
            field="accelerator_power_limit",
            value="not stated",
            unit=None,
            locator=locator,
            boundary="per GPU; no value inferred from related systems",
        ),
        observation(
            source_id=source_id,
            field="host_cpu_family",
            value=candidate["cpu_family"],
            unit=None,
            locator=locator,
            boundary=f"{candidate['cpu_count']}-CPU system",
        ),
    ]
    if sources and TABLE_SOURCE_ID in sources:
        observations.append(
            observation(
                source_id=TABLE_SOURCE_ID,
                field="oem_certification_table_status",
                value=candidate["certification_states"],
                unit=None,
                locator=locator,
                boundary=(
                    "Supermicro table label; not independently normalized as an "
                    "issuer-registry certificate"
                ),
            )
        )
    if details:
        assert product is not None
        detail_source = str(product["id"])
        observations.extend(
            [
                observation(
                    source_id=detail_source,
                    field="power_supply_configuration",
                    value=details["redundancy"],
                    unit=None,
                    locator=str(details["locator"]),
                    boundary="power-supply modules; not normalized as system input power",
                ),
                observation(
                    source_id=detail_source,
                    field="power_supply_efficiency",
                    value=details["psu_efficiency"],
                    unit=None,
                    locator=str(details["locator"]),
                    boundary="power-supply module efficiency; not server efficiency",
                ),
                observation(
                    source_id=detail_source,
                    field="power_supply_input_range",
                    value=details["psu_input"],
                    unit=None,
                    locator=str(details["locator"]),
                    boundary="power-supply rating choices; not a nominal configured server input",
                ),
            ]
        )
    variant = (
        f"{candidate['accelerator_model']}; {candidate['cooling_method'] or 'cooling undisclosed'}"
    )
    notes = (
        "Exact current integrated system configuration. Accelerator count is the "
        "system design, not evidence of an installed deployment. Accelerator "
        "configurable power is per GPU and is not multiplied into server or rack "
        "input. CPU options and PSU module ratings are not synthesized into an "
        "input-power configuration. Supermicro certification-table labels remain "
        "observations rather than issuer-registry certifications."
    )
    record: dict[str, object] = {
        "capacity_scope": boundary,
        "created_at": RETRIEVED_AT,
        "entity_type": "equipment",
        "equipment_category": "server",
        "evidence_json": compact(evidence),
        "external_ids_json": compact({"supermicro_sku": model}),
        "field_sources_json": compact(
            {
                field: [str(product["id"])]
                if product
                and field
                in {
                    "cooling_technology",
                    "form_factor",
                    "width_mm",
                    "height_mm",
                    "depth_mm",
                    "weight_kg",
                    "temperature_min_c",
                    "temperature_max_c",
                    "redundancy",
                }
                else [source_id]
                for field in fields
            }
        ),
        "last_verified_at": RETRIEVED_AT,
        "manufacturer": "Supermicro",
        "memory_type": str(candidate["memory_type"]),
        "model": model,
        "name": f"Supermicro {model} with {candidate['accelerator_model']}",
        "notes": notes,
        "observations_json": compact(observations),
        "official_url": str(product["url"]) if product else TABLE_URL,
        "power_conditions": (
            "configurable accelerator limit per GPU; server and rack input "
            "undisclosed; PSU module nameplates are not summed"
        ),
        "power_rating_kind": "configurable maximum accelerator power per GPU"
        if candidate.get("accelerator_power_w_per_gpu") is not None
        else "accelerator power undisclosed",
        "product_status": f"current official Supermicro page as of {AS_OF}",
        "quality_status": "needs_review" if memory_conflict else "source_backed",
        "record_id": stable_id(
            "equipment", "Supermicro", model, str(candidate["accelerator_model"])
        ),
        "record_scope": "configuration",
        "accelerator_count": int(candidate["accelerator_count"]),
        "source_urls": urls,
        "sources": sources,
        "updated_at": RETRIEVED_AT,
        "variant": variant,
    }
    if candidate.get("accelerator_power_w_per_gpu") is not None:
        record["accelerator_power_w"] = float(candidate["accelerator_power_w_per_gpu"])
    if not memory_conflict:
        record["memory_gb"] = table_memory
    else:
        record["conflicts_json"] = compact(
            {
                "memory_gb": [
                    {
                        "boundary": "accelerator model label, per GPU",
                        "field": "memory_gb",
                        "observed_at": RETRIEVED_AT,
                        "sources": [source_id],
                        "unit": "GB",
                        "value": label_memory,
                    },
                    {
                        "boundary": "table memory column, per GPU",
                        "field": "memory_gb",
                        "observed_at": RETRIEVED_AT,
                        "sources": [source_id],
                        "unit": "GB",
                        "value": table_memory,
                    },
                ]
            }
        )
        record["notes"] += (
            " B300 model labels say 288 GB while the same rows' memory column says "
            "270 GB; normalized memory remains null."
        )
    mapping = {
        "cooling_method": "cooling_technology",
        "form_factor": "form_factor",
        "width_mm": "width_mm",
        "height_mm": "height_mm",
        "depth_mm": "depth_mm",
        "weight_kg": "weight_kg",
        "temperature_min_c": "temperature_min_c",
        "temperature_max_c": "temperature_max_c",
        "redundancy": "redundancy",
    }
    for detail_key, field in mapping.items():
        if detail_key in details:
            record[field] = details[detail_key]
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("table_html", type=Path)
    parser.add_argument("b200_liquid_html", type=Path)
    parser.add_argument("b200_air_html", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    table = parse_supermicro_nvidia_systems(
        args.table_html.read_bytes(), source_url=TABLE_URL, expected_count=13
    )
    if table["sha256"] != TABLE_SHA256:
        raise ValueError("Supermicro table bytes differ from reviewed capture")
    for model, path in (
        ("SYS-422GS-NBRT-LCC", args.b200_liquid_html),
        ("SYS-822GS-NBRT", args.b200_air_html),
    ):
        import hashlib

        if hashlib.sha256(path.read_bytes()).hexdigest() != PRODUCT_SOURCES[model]["sha256"]:
            raise ValueError(f"Supermicro product bytes differ for {model}")
    candidates = list(table["candidates"])
    candidates.append(
        {
            "model": "SYS-422GS-NBRT-LCC",
            **{
                key: value
                for key, value in PRODUCT_DETAILS["SYS-422GS-NBRT-LCC"].items()
                if key
                in {
                    "accelerator_model",
                    "accelerator_count",
                    "accelerator_form_factor",
                    "accelerator_power_w_per_gpu",
                    "memory_gb_per_gpu",
                    "memory_type",
                    "cpu_family",
                    "cpu_count",
                    "cooling_method",
                    "locator",
                }
            },
            "integration": "Onboard",
            "certification_states": [],
        }
    )
    rows = [build_record(candidate) for candidate in candidates]
    if len(rows) != 14 or len({row["record_id"] for row in rows}) != 14:
        raise ValueError("Expected 14 unique current Supermicro system configurations")
    rows.sort(key=lambda item: str(item["record_id"]))
    args.output.write_text("".join(f"{compact(row)}\n" for row in rows), encoding="utf-8")
    print(f"Wrote {len(rows)} reviewed Supermicro system records to {args.output}")


if __name__ == "__main__":
    main()
