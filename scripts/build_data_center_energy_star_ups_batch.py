"""Build one reviewed partner batch from EPA's public ENERGY STAR UPS inventory."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import TypedDict

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.inventories import (
    parse_energy_star_ups_inventory,
)

SOURCE_ID = "epa-energy-star-certified-ups-20261104"
SOURCE_URL = "https://data.energystar.gov/api/v3/views/ifxy-2uty/export.csv?accessType=DOWNLOAD"


class PartnerBatch(TypedDict):
    partner: str
    manufacturer: str
    name_prefix: str | None
    expected_count: int
    retrieved_at: str
    include_maximum_configuration: bool


PARTNER_BATCHES: dict[str, PartnerBatch] = {
    "ablerex": {
        "partner": "Ablerex Electronics Co., Ltd.",
        "manufacturer": "Ablerex Electronics",
        "name_prefix": "Ablerex",
        "expected_count": 15,
        "retrieved_at": "2026-11-04T12:17:31Z",
        "include_maximum_configuration": False,
    },
    "adi": {
        "partner": "ADI",
        "manufacturer": "ADI",
        "name_prefix": None,
        "expected_count": 22,
        "retrieved_at": "2026-11-04T11:18:04Z",
        "include_maximum_configuration": False,
    },
    "minuteman": {
        "partner": "Para Systems, Inc./Minuteman Power Technologies",
        "manufacturer": "Para Systems / Minuteman Power Technologies",
        "name_prefix": "Minuteman",
        "expected_count": 33,
        "retrieved_at": "2026-11-04T10:26:21Z",
        "include_maximum_configuration": False,
    },
    "panduit": {
        "partner": "Panduit Corp.",
        "manufacturer": "Panduit",
        "name_prefix": "Panduit",
        "expected_count": 10,
        "retrieved_at": "2026-11-04T13:20:48Z",
        "include_maximum_configuration": False,
    },
    "appleton": {
        "partner": "Appleton Grp LLC d/b/a Appleton Group",
        "manufacturer": "Appleton Group / SolaHD",
        "name_prefix": "SolaHD",
        "expected_count": 7,
        "retrieved_at": "2026-11-04T13:20:48Z",
        "include_maximum_configuration": False,
    },
    "legrand_av": {
        "partner": "Legrand AV Inc.",
        "manufacturer": "Legrand AV",
        "name_prefix": None,
        "expected_count": 7,
        "retrieved_at": "2026-11-04T13:20:48Z",
        "include_maximum_configuration": False,
    },
    "delta_energy_star": {
        "partner": "Delta Electronics, Inc. Tainan Branch",
        "manufacturer": "Delta Electronics",
        "name_prefix": "Delta",
        "expected_count": 26,
        "retrieved_at": "2026-11-04T14:16:19Z",
        "include_maximum_configuration": False,
    },
    "cyberpower_energy_star": {
        "partner": "Cyber Power Systems, Inc.",
        "manufacturer": "CyberPower Systems",
        "name_prefix": None,
        "expected_count": 135,
        "retrieved_at": "2026-11-04T15:17:13Z",
        "include_maximum_configuration": True,
    },
}
DATASET_UPDATED = "2026-11-03T14:20:54Z"


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def number(value: str) -> float:
    return float(value.replace(",", ""))


def optional_number(value: str) -> float | None:
    stripped = value.strip()
    if stripped in {"", "N/A", "None", "Not Applicable"}:
        return None
    return number(stripped)


def single_range(value: str) -> float | None:
    parts = value.split("-")
    if len(parts) != 2:
        return None
    low, high = (number(part) for part in parts)
    return low if low == high else None


def iso_date(value: str) -> str:
    return datetime.strptime(value, "%m/%d/%Y").strftime("%Y-%m-%d")


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


def build_record(
    row: dict[str, str],
    *,
    manufacturer: str,
    name_prefix: str | None,
    retrieved_at: str,
    include_maximum_configuration: bool = False,
) -> dict[str, object]:
    uid = row["ENERGY STAR Unique ID"]
    model = row["Model Name"]
    tested = row["Minimum Configuration Tested Model Number"]
    tested_reported = tested.strip() not in {"", "N/A", "None", "Not Applicable"}
    maximum_tested = row["Maximum Configuration Tested Model Number"].strip()
    maximum_reported = include_maximum_configuration and maximum_tested not in {
        "",
        "N/A",
        "None",
        "Not Applicable",
    }
    output_kw = number(row["Active Output Power Rating Minimum Configuration (W)"]) / 1000
    apparent_kva = number(row["Apparent Output Power Rating Minimum Configuration (VA)"]) / 1000
    runtime = optional_number(row["Energy Storage System Runtime at 100% Load (min.)"])
    runtime_50 = optional_number(row["Energy Storage System Runtime at 50% Load (min.)"])
    warranty = optional_number(row["Energy Storage System Warranty (yrs)"])
    efficiency = number(row["Weighted Efficiency Calc Min Config Lowest Dependency"])
    rack_u = row["Rack Mount Height (U)"]
    form_factor = (
        f"rack-mountable {rack_u}U UPS"
        if row["Rack Mountable"] == "Yes" and rack_u
        else "rack-mountable UPS"
        if row["Rack Mountable"] == "Yes"
        else "non-rack-mountable UPS"
    )
    fields = [
        "apparent_power_kva",
        "capacity_scope",
        "certifications_json",
        "communication_protocols",
        "depth_mm",
        "efficiency_conditions",
        "efficiency_pct",
        "equipment_category",
        "form_factor",
        "height_mm",
        "manufacturer",
        "model",
        "name",
        "notes",
        "observations_json",
        "official_url",
        "output_power_kw",
        "power_conditions",
        "power_rating_kind",
        "product_status",
        "record_scope",
        "variant",
        "width_mm",
    ]
    normalized: dict[str, object] = {
        "apparent_power_kva": apparent_kva,
        "output_power_kw": output_kw,
        "efficiency_pct": efficiency,
        "height_mm": number(row["Height (mm)"]),
        "width_mm": number(row["Width (mm)"]),
        "depth_mm": number(row["Depth (mm)"]),
    }
    if runtime is not None:
        fields.extend(["runtime_load_kw", "runtime_minutes"])
        normalized["runtime_minutes"] = runtime
        normalized["runtime_load_kw"] = output_kw
    if warranty is not None:
        fields.extend(["warranty_conditions", "warranty_years"])
        normalized["warranty_years"] = warranty
    for field, source_field in {
        "input_voltage_v": "Rated Input Voltage (V rms)",
        "output_voltage_v": "Rated Output Voltage (V)",
        "frequency_hz": "Rated Output Frequency (Hz)",
    }.items():
        scalar = single_range(row[source_field])
        if scalar is not None:
            fields.append(field)
            normalized[field] = scalar
    protocols = [
        value.strip()
        for value in row["Communication Protocols"].split(",")
        if value.strip() not in {"", "None", "Other"}
    ]
    certifications = {
        "energy_star": {
            "certificate": uid,
            "date": iso_date(row["Date Certified"]),
            "issuer": "U.S. Environmental Protection Agency ENERGY STAR",
            "scope": (
                f"Ac-output UPS certification entry for {model}; tested minimum "
                f"configuration {tested}"
                if tested_reported
                else f"Ac-output UPS certification entry for {model}; minimum tested "
                "configuration identifier not reported"
            ),
            "source_id": SOURCE_ID,
        }
    }
    boundary = (
        f"ENERGY STAR certified minimum configuration {tested}; unique ID {uid}"
        if tested_reported
        else f"ENERGY STAR certified entry; minimum configuration identifier not reported; "
        f"unique ID {uid}"
    )
    observations = [
        observation(row, "brand_name", row["Brand Name"], None, boundary),
        observation(row, "model_number", row["Model Number"], None, boundary),
        observation(row, "tested_minimum_configuration", tested, None, boundary),
        observation(row, "application", row["Application"], None, boundary),
        observation(row, "topology", row["Topology and Product Type Combined"], None, boundary),
        observation(
            row, "rated_input_voltage_range", row["Rated Input Voltage (V rms)"], "V", boundary
        ),
        observation(
            row, "rated_input_frequency_range", row["Rated Input Frequency (Hz)"], "Hz", boundary
        ),
        observation(
            row, "rated_output_voltage_range", row["Rated Output Voltage (V)"], "V", boundary
        ),
        observation(
            row, "rated_output_frequency_range", row["Rated Output Frequency (Hz)"], "Hz", boundary
        ),
        observation(
            row,
            "test_electrical_conditions",
            (
                f"{row['Test Input Voltage (V rms)']} V input at "
                f"{row['Test Input Frequency (Hz)']} Hz; "
                f"{row['Test Output Voltage (V)']} V output at "
                f"{row['Test Output Frequency (Hz)']} Hz"
            ),
            None,
            boundary,
        ),
        observation(
            row,
            "efficiency_load_points",
            {
                "25_pct": row["Efficiency at 25% Load Min Config Lowest Dependency (ac)"],
                "50_pct": row["Efficiency at 50% Load Min Config Lowest Dependency (ac)"],
                "75_pct": row["Efficiency at 75% Load Min Config Lowest Dependency (ac)"],
                "100_pct": row["Efficiency at 100% Load Min Config Lowest Dependency (ac)"],
                "no_load_input_w": row[
                    "Total Input Power in W at 0% Load Min Config Lowest Dependency (ac)"
                ],
            },
            "% except no_load_input_w in W",
            "Minimum tested configuration; lowest-input-dependency normal mode",
        ),
        observation(
            row,
            "energy_storage",
            {
                "configuration": row["Energy Storage System Configuration"],
                "mechanism": row["Energy Storage Mechanism"],
                "removable_to_another_room": row["Energy Storage System Removable to Another Room"],
                "technology": row["Energy Storage System Technology"],
            },
            None,
            "Certified UPS configuration; no battery energy inferred",
        ),
        observation(row, "modular_ups", row["Modular UPS"], None, boundary),
        observation(
            row, "network_connections", row["Network Connections Available"], None, boundary
        ),
        observation(
            row, "communication_protocol_other", row["Communication Protocol Other"], None, boundary
        ),
        observation(
            row,
            "outlet_counts",
            {
                "total": row["Total Number of Outlets"],
                "battery_backup_and_surge": row[
                    "Number of Battery Backup and Surge Protected Outlets"
                ],
                "surge_only": row["Number of Surge Protected Only Outlets"],
            },
            None,
            boundary,
        ),
        observation(
            row,
            "date_available_on_market",
            iso_date(row["Date Available on Market"]),
            None,
            boundary,
        ),
        observation(row, "markets", row["Markets"], None, boundary),
        observation(row, "cb_model_identifier", row["CB Model Identifier"], None, boundary),
    ]
    if maximum_reported:
        observations.append(
            observation(
                row,
                "maximum_tested_configuration",
                {
                    "model": maximum_tested,
                    "active_output_w": optional_number(
                        row["Active Output Power Rating Maximum Configuration (W)"]
                    ),
                    "apparent_output_va": optional_number(
                        row["Apparent Output Power Rating Maximum Configuration (VA)"]
                    ),
                },
                None,
                "ENERGY STAR maximum tested configuration; values remain observations and "
                "are not normalized as the record's minimum-configuration rating",
            )
        )
    if runtime_50 is not None:
        observations.insert(
            11,
            observation(
                row,
                "runtime_at_50_pct_load",
                runtime_50,
                "min",
                f"50% of certified minimum-configuration active output ({output_kw / 2:g} kW)",
            ),
        )
    model_url = row["Model Web Page URL"]
    if model_url:
        observations.append(observation(row, "model_web_page", model_url, None, boundary))
    fields = sorted(set(fields))
    evidence = {
        field: {
            "confidence": "high",
            "locator": f"ENERGY STAR Unique ID {uid}",
            "source_publication_dates": {SOURCE_ID: DATASET_UPDATED[:10]},
            **(
                {"unit": unit}
                if (
                    unit := {
                        "apparent_power_kva": "kVA",
                        "depth_mm": "mm",
                        "efficiency_pct": "%",
                        "frequency_hz": "Hz",
                        "height_mm": "mm",
                        "input_voltage_v": "V",
                        "output_power_kw": "kW",
                        "output_voltage_v": "V",
                        "runtime_load_kw": "kW",
                        "runtime_minutes": "min",
                        "warranty_years": "years",
                        "width_mm": "mm",
                    }.get(field)
                )
                else {}
            ),
        }
        for field in fields
    }
    record: dict[str, object] = {
        **normalized,
        "capacity_scope": (
            f"Exact ENERGY STAR certification entry {uid} for minimum tested "
            f"configuration {tested}; maximum tested configuration {maximum_tested} is retained "
            "as a separate observation"
            if tested_reported and maximum_reported
            else f"Exact ENERGY STAR certification entry {uid} for minimum tested "
            f"configuration {tested}; maximum configuration is not stated"
            if tested_reported
            else f"Exact ENERGY STAR certification entry {uid}; minimum tested configuration "
            "identifier and maximum configuration are not stated"
        ),
        "certifications_json": compact(certifications),
        "communication_protocols": protocols,
        "created_at": retrieved_at,
        "efficiency_conditions": (
            "ENERGY STAR weighted efficiency for minimum configuration, "
            "lowest-input-dependency AC normal mode"
        ),
        "entity_type": "equipment",
        "equipment_category": "ups",
        "evidence_json": compact(evidence),
        "field_sources_json": compact({field: [SOURCE_ID] for field in fields}),
        "form_factor": form_factor,
        "last_verified_at": retrieved_at,
        "manufacturer": manufacturer,
        "model": model,
        "name": f"{name_prefix or row['Brand Name']} {model} ENERGY STAR configuration",
        "notes": (
            "This record is one third-party-certified minimum test configuration. "
            "W and VA remain separate; the normalized runtime is the reported 100% "
            "load runtime, with the load converted exactly from W to kW. Battery "
            "energy, optional accessories, deployments and maximum configurations "
            "are not inferred."
            if runtime is not None
            else "This record is one third-party-certified configuration entry. W and VA "
            "remain separate. The source reports no runtime value for this model, so "
            "runtime and runtime load remain null. Battery energy, optional accessories, "
            "deployments and maximum configurations are not inferred."
        ),
        "observations_json": compact(observations),
        "official_url": SOURCE_URL,
        "power_conditions": (
            f"Certified minimum configuration {tested}; active output converted "
            "exactly from W to kW and apparent output from VA to kVA"
            if tested_reported
            else "Certified entry with no reported minimum-configuration identifier; active "
            "output converted exactly from W to kW and apparent output from VA to kVA"
        ),
        "power_rating_kind": "ENERGY STAR certified minimum-configuration UPS output",
        "product_status": (
            "listed in the current ENERGY STAR certified UPS dataset snapshot updated 2026-11-03"
        ),
        "quality_status": "source_backed",
        "record_id": stable_id("equipment", manufacturer, "ENERGY STAR", uid),
        "record_scope": "configuration",
        "source_urls": [SOURCE_URL],
        "sources": [SOURCE_ID],
        "updated_at": retrieved_at,
        "variant": (
            f"ENERGY STAR {uid}; tested configuration {tested}"
            if tested_reported
            else f"ENERGY STAR {uid}; tested configuration identifier not reported"
        ),
    }
    if warranty is not None:
        record["warranty_conditions"] = "Certified entry's energy-storage-system warranty"
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_csv", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--partner-batch",
        choices=sorted(PARTNER_BATCHES),
        default="minuteman",
        help="Reviewed partner inventory to extract (default: minuteman)",
    )
    parser.add_argument(
        "--shard-size",
        type=int,
        default=0,
        help="Write numbered JSONL shards with at most this many records (default: one file)",
    )
    args = parser.parse_args()
    batch = PARTNER_BATCHES[args.partner_batch]
    expected_count = batch["expected_count"]
    staged = parse_energy_star_ups_inventory(
        args.source_csv.read_bytes(),
        source_url=SOURCE_URL,
        partner=batch["partner"],
        expected_count=expected_count,
    )
    records = sorted(
        (
            build_record(
                row,
                manufacturer=batch["manufacturer"],
                name_prefix=batch["name_prefix"],
                retrieved_at=batch["retrieved_at"],
                include_maximum_configuration=batch["include_maximum_configuration"],
            )
            for row in staged["candidates"]
        ),
        key=lambda record: (str(record["model"]), str(record["variant"])),
    )
    if (
        len(records) != expected_count
        or len({record["record_id"] for record in records}) != expected_count
    ):
        raise ValueError(f"Expected {expected_count} unique {batch['partner']} configurations")
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
        print(
            f"Wrote {expected_count} ENERGY STAR-certified {batch['partner']} "
            f"configurations in {shard_count} shards"
        )
    else:
        args.output.write_text(
            "".join(f"{compact(record)}\n" for record in records), encoding="utf-8"
        )
        print(f"Wrote {expected_count} ENERGY STAR-certified {batch['partner']} configurations")


if __name__ == "__main__":
    main()
