"""Build DOE CCMS UPS displayed rows 1-50 and enrich exact catalogue matches."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
from typing import Any

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.inventories import (
    parse_doe_ups_certification_matrix,
)

RETRIEVED_AT = "2026-11-05T21:23:00Z"
AS_OF = "2026-10-23"
SOURCE_ID = "doe-ccms-ups-page1-20261023"
SOURCE_URL = (
    "https://www.regulations.doe.gov/certification-data/CCMS-4-Uninterruptible_Power_Supplies.html"
)
NEW_FILENAME = "2026-11-05-doe-ccms-ups-page1.jsonl"
CSV_FIELDS = [
    "brand",
    "basic_model",
    "individual_model",
    "input_voltage_v",
    "output_voltage_v",
    "lowest_mode",
    "lowest_active_w",
    "lowest_apparent_va",
    "highest_mode",
    "highest_active_w",
    "highest_apparent_va",
    "lowest_efficiency_pct",
    "third_mode",
    "highest_efficiency_pct",
    "locator",
]

ABB_ROWS = (
    ("UPS POWERVALUE 11RT G2 1 kVA B UL", 1000, 1000),
    ("UPS POWERVALUE 11RT G2 1 KVA S UL", 1000, 1000),
    ("UPS POWERVALUE 11RT G2 1.5 kVA B UL", 1300, 1500),
    ("UPS POWERVALUE 11RT G2 1.5 KVA S UL", 1300, 1500),
)
APC_FAMILIES = (
    (
        "BR1500RM2U",
        ("BR1500RM2UW", "BR1500RM2UR", "BR1500RM2UQ", "BR1500RM2U"),
        "VI",
        900,
        1500,
        98.8,
    ),
    (
        "BR1500MS",
        ("BR1500MS2W", "BR1500MS2R", "BR1500MS2Q", "BR1500MS2"),
        "VI",
        900,
        1500,
        99.1,
    ),
    ("BR1500G", ("BR1500GW", "BR1500GR", "BR1500GQ", "BR1500G"), "VI", 865, 1500, 98.9),
    (
        "BR1350MS",
        ("BR1350MSW", "BR1350MSR", "BR1350MSQ", "BR1350MS"),
        "VI",
        810,
        1350,
        99.1,
    ),
    (
        "BR1000MS",
        ("BR1000MSW", "BR1000MSR", "BR1000MSQ", "BR1000MS"),
        "VI",
        600,
        1000,
        99.0,
    ),
    ("BR700G", ("BR700GW", "BR700GR", "BR700GQ", "BR700G"), "VI", 420, 700, 98.9),
    (
        "BN1500M2",
        (
            "BN1500M2-CAW",
            "BN1500M2-CAR",
            "BN1500M2-CAQ",
            "BN1500M2-CA",
            "BN1500M2W",
            "BN1500M2R",
            "BN1500M2Q",
            "BN1500M2",
        ),
        "VFD",
        900,
        1500,
        98.9,
    ),
    (
        "BN1375M2",
        (
            "BN1350M2-CAW",
            "BN1350M2-CAR",
            "BN1350M2-CAQ",
            "BN1350M2-CA",
            "BN1350M2W",
            "BN1350M2R",
            "BN1350M2Q",
            "BN1350M2",
        ),
        "VFD",
        810,
        1350,
        98.8,
    ),
    (
        "BN1100M2",
        ("BN1100M2-CAW", "BN1100M2-CAR", "BN1100M2-CAQ", "BN1100M2-CA"),
        "VFD",
        600,
        1100,
        98.8,
    ),
    ("BN450M", ("BN450M-CAW", "BN450M-CAR"), "VFD", 255, 450, 97.7),
)

EXISTING = {
    "BR1500RM2U": (
        "407a3fa8-7e83-5ca1-bcbf-4871a40bf184",
        "2026-11-04-energy-star-schneider-ups-part-06.jsonl",
    ),
    "BR1500MS2": (
        "f99c686d-c759-5dbf-9fb1-beaeafdfcd4e",
        "2026-11-04-energy-star-schneider-ups-part-31.jsonl",
    ),
    "BR1500G": (
        "559b18db-4366-57e9-ac9d-87345734af7d",
        "2026-11-04-energy-star-schneider-ups-part-07.jsonl",
    ),
    "BR1350MS": (
        "56d7c08c-a5d2-5769-b53f-930b5841bff6",
        "2026-11-04-energy-star-schneider-ups-part-31.jsonl",
    ),
    "BR1000MS": (
        "d7beb470-1471-51d5-9537-e1da3910458c",
        "2026-11-04-energy-star-schneider-ups-part-30.jsonl",
    ),
    "BR700G": (
        "e5b65695-d3d7-5258-987f-79418541afee",
        "2026-11-04-energy-star-schneider-ups-part-07.jsonl",
    ),
    "BN1500M2-CA": (
        "26ab0e13-58a7-51f2-ab11-d2c509c0cf45",
        "2026-11-04-energy-star-schneider-ups-part-05.jsonl",
    ),
    "BN1500M2": (
        "f29dfa1b-8ba4-5296-ae5b-b22a6b589235",
        "2026-11-04-energy-star-schneider-ups-part-06.jsonl",
    ),
    "BN1350M2-CA": (
        "79dbf8d5-ed43-58d1-8dda-8bc36e1bd721",
        "2026-11-04-energy-star-schneider-ups-part-05.jsonl",
    ),
    "BN1350M2": (
        "cd6bbc31-9dd4-5798-831b-17752adca95f",
        "2026-11-04-energy-star-schneider-ups-part-30.jsonl",
    ),
    "BN1100M2-CA": (
        "a39b4f09-1ad8-5f24-9e99-363e0d55e86c",
        "2026-11-04-energy-star-schneider-ups-part-06.jsonl",
    ),
}


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def rows() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    row_number = 1
    for model, active_w, apparent_va in ABB_ROWS:
        result.append(
            {
                "brand": "ABB",
                "basic_model": model,
                "individual_model": model,
                "input_voltage_v": 120,
                "output_voltage_v": 120,
                "lowest_mode": "VFI",
                "lowest_active_w": active_w,
                "lowest_apparent_va": apparent_va,
                "highest_mode": None,
                "highest_active_w": None,
                "highest_apparent_va": None,
                "lowest_efficiency_pct": 91.2,
                "third_mode": None,
                "highest_efficiency_pct": None,
                "locator": f"public results table / displayed row {row_number} of 50",
            }
        )
        row_number += 1
    for basic, models, mode, active_w, apparent_va, efficiency in APC_FAMILIES:
        for model in models:
            result.append(
                {
                    "brand": "APC",
                    "basic_model": basic,
                    "individual_model": model,
                    "input_voltage_v": 120,
                    "output_voltage_v": 120,
                    "lowest_mode": mode,
                    "lowest_active_w": active_w,
                    "lowest_apparent_va": apparent_va,
                    "highest_mode": None,
                    "highest_active_w": None,
                    "highest_apparent_va": None,
                    "lowest_efficiency_pct": efficiency,
                    "third_mode": None,
                    "highest_efficiency_pct": None,
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


def observations(item: dict[str, Any]) -> list[dict[str, object]]:
    boundary = (
        f"DOE CCMS public UPS row for {item['brand']} {item['individual_model']}; "
        f"lowest supported input dependency mode {item['lowest_mode']}"
    )
    result = [
        observation(item, "brand_name", item["brand"], None, boundary),
        observation(item, "basic_model", item["basic_model"], None, boundary),
        observation(item, "individual_model", item["individual_model"], None, boundary),
        observation(item, "rated_input_voltage", item["input_voltage_v"], "V", boundary),
        observation(item, "rated_output_voltage", item["output_voltage_v"], "V", boundary),
        observation(
            item, "lowest_supported_input_dependency_mode", item["lowest_mode"], None, boundary
        ),
        observation(item, "lowest_mode_active_power", item["lowest_active_w"], "W", boundary),
        observation(item, "lowest_mode_apparent_power", item["lowest_apparent_va"], "VA", boundary),
        observation(
            item,
            "average_load_adjusted_efficiency_lowest_mode",
            item["lowest_efficiency_pct"],
            "%",
            boundary,
        ),
    ]
    if item.get("highest_mode"):
        result.extend(
            [
                observation(
                    item,
                    "highest_supported_input_dependency_mode",
                    item["highest_mode"],
                    None,
                    boundary,
                ),
                observation(
                    item, "highest_mode_active_power", item["highest_active_w"], "W", boundary
                ),
                observation(
                    item, "highest_mode_apparent_power", item["highest_apparent_va"], "VA", boundary
                ),
                observation(
                    item,
                    "average_load_adjusted_efficiency_highest_mode",
                    item["highest_efficiency_pct"],
                    "%",
                    boundary,
                ),
            ]
        )
    if item.get("third_mode"):
        result.append(
            observation(
                item, "third_supported_input_dependency_mode", item["third_mode"], None, boundary
            )
        )
    return result


def certification(item: dict[str, Any]) -> dict[str, object]:
    return {
        "certificate": str(item["individual_model"]),
        "date": AS_OF,
        "issuer": "U.S. Department of Energy CCMS",
        "scope": (
            f"Public manufacturer-represented UPS certification row for basic model "
            f"{item['basic_model']} and individual model {item['individual_model']}"
        ),
        "source_id": SOURCE_ID,
        "status": "public listing; not a DOE compliance determination",
    }


def manufacturer(item: dict[str, Any]) -> str:
    return "Schneider Electric" if item["brand"] == "APC" else str(item["brand"])


def build_record(item: dict[str, Any]) -> dict[str, Any]:
    maker = manufacturer(item)
    model = str(item["individual_model"])
    locator = str(item["locator"])
    fields = [
        "apparent_power_kva",
        "capacity_scope",
        "certifications_json",
        "efficiency_conditions",
        "efficiency_pct",
        "entity_type",
        "equipment_category",
        "evidence_json",
        "input_voltage_v",
        "manufacturer",
        "model",
        "name",
        "notes",
        "observations_json",
        "official_url",
        "output_power_kw",
        "output_voltage_v",
        "power_conditions",
        "power_rating_kind",
        "product_status",
        "record_scope",
        "variant",
    ]
    units = {
        "apparent_power_kva": "kVA",
        "efficiency_pct": "%",
        "input_voltage_v": "V",
        "output_power_kw": "kW",
        "output_voltage_v": "V",
    }
    evidence = {
        field: {
            "confidence": "high",
            "locator": locator,
            "source_publication_dates": {SOURCE_ID: AS_OF},
            **({"unit": units[field]} if field in units else {}),
        }
        for field in fields
    }
    brand_label = "APC by Schneider Electric" if item["brand"] == "APC" else maker
    boundary = (
        f"Exact DOE CCMS individual model {model}; {item['lowest_mode']} lowest supported mode"
    )
    return {
        "apparent_power_kva": float(item["lowest_apparent_va"]) / 1000,
        "capacity_scope": boundary,
        "certifications_json": compact({"doe_ccms_public_listing": certification(item)}),
        "created_at": RETRIEVED_AT,
        "efficiency_conditions": (
            f"DOE average load-adjusted efficiency; {item['lowest_mode']} lowest supported "
            "input dependency mode"
        ),
        "efficiency_pct": float(item["lowest_efficiency_pct"]),
        "entity_type": "equipment",
        "equipment_category": "ups",
        "evidence_json": compact(evidence),
        "field_sources_json": compact({field: [SOURCE_ID] for field in fields}),
        "input_voltage_v": float(item["input_voltage_v"]),
        "last_verified_at": RETRIEVED_AT,
        "manufacturer": maker,
        "model": model,
        "name": f"{brand_label} {model} DOE CCMS configuration",
        "notes": (
            "Exact public DOE CCMS individual-model row, not evidence of deployment or a DOE "
            "compliance determination. Active W and apparent VA remain separate. Battery "
            "energy, runtime, frequency, dimensions, optional accessories and deployment "
            "remain unknown."
        ),
        "observations_json": compact(observations(item)),
        "official_url": SOURCE_URL,
        "output_power_kw": float(item["lowest_active_w"]) / 1000,
        "output_voltage_v": float(item["output_voltage_v"]),
        "power_conditions": (
            f"DOE CCMS {item['lowest_mode']} lowest supported mode; active output in W and "
            "apparent output in VA are separately reported"
        ),
        "power_rating_kind": "DOE CCMS lowest-supported-mode UPS output",
        "product_status": "current DOE CCMS public representation updated 2026-10-23",
        "quality_status": "source_backed",
        "record_id": stable_id("equipment", maker, "DOE CCMS UPS", model),
        "record_scope": "configuration",
        "source_urls": [SOURCE_URL],
        "sources": [SOURCE_ID],
        "updated_at": RETRIEVED_AT,
        "variant": f"DOE CCMS basic model {item['basic_model']}; exact individual model {model}",
    }


def enrich_record(record: dict[str, Any], item: dict[str, Any]) -> None:
    if SOURCE_ID in record.get("sources", []):
        return
    expected = {
        "input_voltage_v": float(item["input_voltage_v"]),
        "output_voltage_v": float(item["output_voltage_v"]),
        "output_power_kw": float(item["lowest_active_w"]) / 1000,
        "apparent_power_kva": float(item["lowest_apparent_va"]) / 1000,
        "efficiency_pct": float(item["lowest_efficiency_pct"]),
    }
    scalar_conflicts = {
        field: (record.get(field), value)
        for field, value in expected.items()
        if record.get(field) is not None and abs(float(record[field]) - value) > 1e-9
    }
    unexpected_conflicts = scalar_conflicts.keys() - {"efficiency_pct"}
    if unexpected_conflicts:
        raise ValueError(
            f"DOE/ENERGY STAR scalar conflict for {item['individual_model']}: {scalar_conflicts}"
        )
    current_observations = json.loads(str(record["observations_json"]))
    existing_keys = {
        (entry.get("source_id"), entry.get("field"), entry.get("locator"))
        for entry in current_observations
    }
    current_observations.extend(
        entry
        for entry in observations(item)
        if (entry["source_id"], entry["field"], entry["locator"]) not in existing_keys
    )
    record["observations_json"] = compact(current_observations)
    certifications = json.loads(str(record.get("certifications_json", "{}")))
    certifications["doe_ccms_public_listing"] = certification(item)
    record["certifications_json"] = compact(certifications)
    for key, value in expected.items():
        if record.get(key) is None:
            record[key] = value
    evidence = json.loads(str(record["evidence_json"]))
    field_sources = json.loads(str(record["field_sources_json"]))
    for field in [*expected, "certifications_json", "observations_json", "product_status"]:
        sources = field_sources.setdefault(field, [])
        if SOURCE_ID not in sources:
            sources.append(SOURCE_ID)
        item_evidence = evidence.setdefault(
            field,
            {
                "confidence": "high",
                "locator": item["locator"],
                "source_publication_dates": {},
            },
        )
        item_evidence.setdefault("source_publication_dates", {})[SOURCE_ID] = AS_OF
    record["evidence_json"] = compact(evidence)
    record["field_sources_json"] = compact(field_sources)
    record["sources"] = sorted(set([*record.get("sources", []), SOURCE_ID]))
    record["source_urls"] = sorted(set([*record.get("source_urls", []), SOURCE_URL]))
    record["product_status"] = (
        str(record.get("product_status", "")).rstrip("; ")
        + "; current DOE CCMS public representation updated 2026-10-23"
    )
    note = (
        " The exact individual model is also present in the DOE CCMS current public UPS "
        "listing; that listing is not a DOE compliance determination."
    )
    if note.strip() not in str(record.get("notes", "")):
        record["notes"] = str(record.get("notes", "")) + note
    if "efficiency_pct" in scalar_conflicts:
        previous, current = scalar_conflicts["efficiency_pct"]
        conflicts = json.loads(str(record.get("conflicts_json", "{}")))
        conflicts["efficiency_pct"] = [
            {
                "boundary": str(record.get("efficiency_conditions")),
                "field": "efficiency_pct",
                "observed_at": str(record.get("created_at")),
                "sources": ["epa-energy-star-certified-ups-20261104"],
                "unit": "%",
                "value": previous,
            },
            {
                "boundary": (
                    f"DOE average load-adjusted efficiency; {item['lowest_mode']} lowest "
                    "supported input dependency mode"
                ),
                "field": "efficiency_pct",
                "observed_at": RETRIEVED_AT,
                "sources": [SOURCE_ID],
                "unit": "%",
                "value": current,
            },
        ]
        record["conflicts_json"] = compact(conflicts)
        record["efficiency_pct"] = None
        record["efficiency_conditions"] = (
            "Quarantined: ENERGY STAR and current DOE CCMS average load-adjusted efficiency "
            "values conflict; both dated observations are preserved"
        )
        record["quality_status"] = "needs_review"
        for field in ["conflicts_json", "efficiency_conditions"]:
            field_sources.setdefault(field, [])
            field_sources[field] = sorted(
                set(
                    [
                        *field_sources[field],
                        "epa-energy-star-certified-ups-20261104",
                        SOURCE_ID,
                    ]
                )
            )
            evidence[field] = {
                "confidence": "high",
                "locator": item["locator"],
                "source_publication_dates": {
                    "epa-energy-star-certified-ups-20261104": "2026-11-03",
                    SOURCE_ID: AS_OF,
                },
            }
        record["evidence_json"] = compact(evidence)
        record["field_sources_json"] = compact(field_sources)
    record["last_verified_at"] = RETRIEVED_AT
    record["updated_at"] = RETRIEVED_AT


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    records.sort(key=lambda record: str(record["record_id"]))
    path.write_text("".join(f"{compact(record)}\n" for record in records), encoding="utf-8")


def build(existing_dir: Path, output_dir: Path) -> tuple[list[dict[str, Any]], set[str]]:
    items = rows()
    parsed = parse_doe_ups_certification_matrix(
        extracted_csv(items), source_url=SOURCE_URL, expected_count=50
    )
    target_filenames = sorted({filename for _record_id, filename in EXISTING.values()})
    records_by_file = {
        filename: read_jsonl(existing_dir / filename) for filename in target_filenames
    }
    by_id = {
        record["record_id"]: record for records in records_by_file.values() for record in records
    }
    new_records: list[dict[str, Any]] = []
    enriched_ids: set[str] = set()
    for item in parsed["candidates"]:
        model = str(item["individual_model"])
        if model in EXISTING:
            record_id, filename = EXISTING[model]
            record = by_id.get(record_id)
            if record is None or record not in records_by_file[filename]:
                raise ValueError(f"Missing exact catalogue record for {model}")
            enrich_record(record, item)
            enriched_ids.add(record_id)
        else:
            new_records.append(build_record(item))
    if len(new_records) != 39 or len(enriched_ids) != 11:
        raise ValueError(
            f"Expected 39 additions and 11 enrichments, got {len(new_records)} and "
            f"{len(enriched_ids)}"
        )
    all_ids = [record["record_id"] for record in new_records]
    if len(all_ids) != len(set(all_ids)):
        raise ValueError("Duplicate DOE CCMS UPS identities")
    for filename, records in records_by_file.items():
        write_jsonl(output_dir / filename, records)
    write_jsonl(output_dir / NEW_FILENAME, new_records)
    return new_records, enriched_ids


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("existing_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    new_records, enriched_ids = build(args.existing_dir, args.output_dir)
    print(
        f"Processed 50 DOE CCMS UPS rows: {len(new_records)} additions, "
        f"{len(enriched_ids)} exact enrichments"
    )


if __name__ == "__main__":
    main()
