"""Build reviewed Fuji Electric current data-center UPS configurations."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
from typing import Any

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.inventories import parse_ups_rating_matrix

RETRIEVED_AT = "2026-11-03T22:26:00Z"
AS_OF = "2026-11-03"
PORTFOLIO_ID = "fuji-electric-americas-ups-portfolio-20261103"
PORTFOLIO_URL = "https://americas.fujielectric.com/products/ups/"

SOURCES = {
    "UPS7000HX-T3U": {
        "id": "fuji-electric-ups7000hx-t3u-021116",
        "url": (
            "https://americas.fujielectric.com/files/"
            "UPS%20Data%20Sheet%20-%20UPS7000HX-T3U%20021616.pdf"
        ),
        "publication_date": "2016-02-11",
    },
    "UPS7300WX-T3U": {
        "id": "fuji-electric-ups7300wx-t3u-102b-202409",
        "url": (
            "https://americas.fujielectric.com/wp-content/uploads/2024/10/"
            "FEA-UPS-DS-102b-UPS7300.pdf"
        ),
        "publication_date": "2024-09-01",
    },
    "UPS7400WX-T3U": {
        "id": "fuji-electric-ups7400wx-t3u-100d-202409",
        "url": (
            "https://americas.fujielectric.com/wp-content/uploads/2024/10/"
            "FEA-UPS-DS-100d-UPS7400.pdf"
        ),
        "publication_date": "2024-09-01",
    },
    "UPS7500WX-T4": {
        "id": "fuji-electric-ups7500wx-current-20261103",
        "url": (
            "https://www.fujielectric.com/products/power_supply/ups/product_detail/"
            "large_ups7500wx.html"
        ),
        "publication_date": None,
    },
}

FAMILY_NOTES = {
    "UPS7000HX-T3U": {
        "topology": "Online double conversion; transformer-less",
        "battery": "VRLA; 480 VDC rated / 540 VDC nominal; 240 cells",
        "overload": "Not stated in the reviewed data-sheet table",
        "protocols": "Optional Web/SNMP and Modbus; not selected",
        "standards": "OEM states UL 1778 5th Edition and CSA 22.2 107.3",
    },
    "UPS7300WX-T3U": {
        "topology": "Online double conversion with RB-IGBT technology",
        "battery": "480 VDC / 545 VDC; 240 cells at 2.27 V per cell; table labels nominal/rated",
        "overload": "125% for 10 minutes; 150% for 1 minute",
        "protocols": "Not stated in the reviewed data sheet",
        "standards": (
            "OEM states UL 1778 5th Edition, CSA 22.2 No.107.3-14 3rd Edition, "
            "IEC 62040-2 Category C3, EnergyStar and OSHPD"
        ),
    },
    "UPS7400WX-T3U": {
        "topology": "Online double conversion with RB-IGBT technology; modular UPM architecture",
        "battery": "VRLA, Li-ion battery or flywheel; 480 VDC / 545 VDC; 240 cells",
        "overload": "125% for 10 minutes; 150% for 1 minute",
        "protocols": "SNMP, Modbus RTU and Modbus TCP/IP; two card slots standard",
        "standards": (
            "OEM states UL 1778 5th Edition, CSA 22.2 No.107.3-14 3rd Edition "
            "and IEC 62040-2 Category C3"
        ),
    },
    "UPS7500WX-T4": {
        "topology": "Normal inverter feeding; modular UPM architecture",
        "battery": "480/528 VDC; 240/264 cells; alternatives not selected",
        "overload": "Not stated in the reviewed current web table",
        "protocols": "Not stated in the reviewed current web table",
        "standards": "No issuer-registry certification normalized from the reviewed current page",
    },
}

CSV_FIELDS = [
    "manufacturer",
    "family",
    "variant",
    "apparent_power_kva",
    "output_power_kw",
    "voltage_text",
    "frequency_text",
    "locator",
]


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def rows() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    def add(family: str, **values: Any) -> None:
        source = SOURCES[family]
        values.update(
            family=family,
            manufacturer="Fuji Electric",
            source_id=source["id"],
            source_url=source["url"],
            publication_date=source["publication_date"],
        )
        result.append(values)

    for kva, nominal, maximum, output, efficiency, width, weight in zip(
        (300, 400, 500),
        (372, 496, 620),
        (409, 546, 682),
        (361, 481, 601),
        (97.4, 97.5, 97.5),
        (2000, 2000, 2300),
        (1850, 1850, 1900),
        strict=True,
    ):
        add(
            "UPS7000HX-T3U",
            apparent_power_kva=kva,
            output_power_kw=kva,
            voltage_text="480 V, 3-phase, 3-wire plus ground",
            frequency_text="60 Hz",
            input_voltage_v=480,
            output_voltage_v=480,
            frequency_hz=60,
            input_current_a=nominal,
            max_input_current_a=maximum,
            output_current_a=output,
            efficiency_profile=f"Up to {efficiency}% AC-to-AC; load point not stated",
            width_mm=width,
            depth_mm=900,
            height_mm=2000,
            weight_kg=weight,
            upm_count=1,
            variant=f"{kva} kVA / {kva} kW; 480 V; 60 Hz; fixed capacity",
            locator=f"UPS7000HX-T3U data sheet page 2 / {kva} kVA fixed capacity",
        )

    profiles_7300 = {
        225: (
            "Online mode 95.3/96.9/97.3/97.4% at 25/50/75/100% load; "
            "HE mode 98.8% at 100%; ENERGY STAR average 96.6%"
        ),
        300: (
            "Online mode 96.1/97.2/97.4/97.3% at 25/50/75/100% load; "
            "HE mode 98.9% at 100%; ENERGY STAR average 96.9%"
        ),
        330: (
            "Online mode 96.3/97.3/97.4/97.3% at 25/50/75/100% load; "
            "HE mode 99.0% at 100%; ENERGY STAR average 97.1%"
        ),
    }
    full_load_efficiency_7300 = {225: 97.4, 300: 97.3, 330: 97.3}
    for kva, nominal, maximum, output in zip(
        (225, 300, 330), (279, 372, 410), (307, 399, 439), (271, 361, 397), strict=True
    ):
        add(
            "UPS7300WX-T3U",
            apparent_power_kva=kva,
            output_power_kw=None,
            voltage_text="480 V, 3-phase, 3-wire plus ground",
            frequency_text="60 Hz",
            input_voltage_v=480,
            output_voltage_v=480,
            frequency_hz=60,
            input_current_a=nominal,
            max_input_current_a=maximum,
            output_current_a=output,
            efficiency_pct=full_load_efficiency_7300[kva],
            efficiency_conditions="Online double-conversion mode at 100% load; 480 V; 60 Hz",
            efficiency_profile=profiles_7300[kva],
            width_mm=1500,
            depth_mm=830,
            height_mm=2020,
            weight_kg=1100,
            upm_count=1,
            variant=f"{kva} kVA; 480 V; 60 Hz; one UPS module",
            locator=f"FEA-UPS-DS-102b page 2 / {kva} kVA column",
        )

    ratings_7400 = (225, 300, 330, 500, 600, 660, 750, 900, 1000, 1000)
    upms_7400 = (1, 1, 1, 2, 2, 2, 3, 3, 3, 4)
    nominal_7400 = (280, 373, 410, 621, 745, 819, 931, 1117, 1241, 1241)
    maximum_7400 = (307, 399, 439, 683, 820, 878, 1024, 1228, 1327, 1327)
    output_7400 = (271, 361, 397, 602, 722, 794, 903, 1083, 1203, 1203)
    group_dimensions = {
        1: (2150, 830, 2020, 1490),
        2: (2750, 830, 2020, 2100),
        3: (3350, 830, 2020, 2710),
        4: (3950, 830, 2020, 3320),
    }
    group_efficiency = {
        1: "330 kW UPM group: online 96.2/97.1/97.2/97.1% at 25/50/75/100% load",
        2: "660 kW UPM group: online 97.2% at 75% load and 97.0% at 100% load",
        3: "1000 kW three-UPM group: online 97.2% at 75% load and 96.9% at 100% load",
        4: "1000 kW four-UPM group: online 97.1% at the table's 75% load point",
    }
    for kva, upms, nominal, maximum, output in zip(
        ratings_7400, upms_7400, nominal_7400, maximum_7400, output_7400, strict=True
    ):
        width, depth, height, weight = group_dimensions[upms]
        add(
            "UPS7400WX-T3U",
            apparent_power_kva=kva,
            output_power_kw=kva,
            voltage_text="480 V, 3-phase, 3-wire plus ground",
            frequency_text="60 Hz",
            input_voltage_v=480,
            output_voltage_v=480,
            frequency_hz=60,
            input_current_a=nominal,
            max_input_current_a=maximum,
            output_current_a=output,
            efficiency_profile=group_efficiency[upms],
            width_mm=width,
            depth_mm=depth,
            height_mm=height,
            weight_kg=weight,
            upm_count=upms,
            communication_protocols=["SNMP", "Modbus RTU", "Modbus TCP/IP"],
            variant=f"{kva} kVA / {kva} kW; 480 V; 60 Hz; {upms} UPM",
            locator=f"FEA-UPS-DS-100d page 2 / {kva} kVA / {upms} UPM column",
        )

    for kva, voltage_text, voltage, upms, width, weight, efficiency, heat in (
        (1140, "380 V", 380, 2, 2500, 2150, None, None),
        (1200, "400/415/420 V", None, 2, 2500, 2150, 96.0, 50.4),
        (2280, "380 V", 380, 4, 3500, 3450, None, None),
        (2400, "400/415/420 V", None, 4, 3500, 3450, 95.8, 105.5),
    ):
        add(
            "UPS7500WX-T4",
            apparent_power_kva=kva,
            output_power_kw=None,
            voltage_text=f"{voltage_text}, 3-phase 4-wire input; 3-phase 3/4-wire output",
            frequency_text="50/60 Hz choice",
            input_voltage_v=voltage,
            output_voltage_v=voltage,
            frequency_hz=None,
            input_current_a=None,
            max_input_current_a=None,
            output_current_a=None,
            efficiency_pct=efficiency,
            efficiency_conditions=(
                f"Normal inverter feeding at 100% load; {voltage_text}; 50/60 Hz"
                if efficiency is not None
                else None
            ),
            efficiency_profile=(
                f"Normal inverter mode {efficiency}% at 100% load; {kva} kVA, "
                f"{voltage_text} configuration"
                if efficiency is not None
                else "No exact efficiency row printed for this voltage-specific capacity"
            ),
            thermal_output_kw=heat,
            width_mm=width,
            depth_mm=900,
            height_mm=2150,
            weight_kg=weight,
            upm_count=upms,
            variant=f"{kva} kVA; {voltage_text}; 50/60 Hz; UPM x{upms}",
            locator=f"current main specifications / UPS7500WX-T4 / {kva} kVA / {voltage_text}",
        )
    return result


def extracted_csv(items: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for item in items:
        writer.writerow({field: item.get(field, "") for field in CSV_FIELDS})
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
        "source_id": item["source_id"],
        "unit": unit,
        "value": value,
    }


def build_record(item: dict[str, Any]) -> dict[str, object]:
    family = str(item["family"])
    exact_source = str(item["source_id"])
    source_ids = [exact_source] if family == "UPS7500WX-T4" else [exact_source, PORTFOLIO_ID]
    source_urls = [str(item["source_url"])]
    if family != "UPS7500WX-T4":
        source_urls.append(PORTFOLIO_URL)
    boundary = f"Exact published {family} {item['variant']} configuration"
    observations = [
        observation(
            item, "input_output_voltage_configuration", item["voltage_text"], "V", boundary
        ),
        observation(item, "frequency_configuration", item["frequency_text"], "Hz", boundary),
        observation(item, "upm_count", item["upm_count"], "count", boundary),
        observation(
            item,
            "maximum_input_current",
            item["max_input_current_a"]
            if item["max_input_current_a"] is not None
            else "not stated",
            "A" if item["max_input_current_a"] is not None else None,
            boundary,
        ),
        observation(
            item,
            "nominal_output_current",
            item["output_current_a"] if item["output_current_a"] is not None else "not stated",
            "A" if item["output_current_a"] is not None else None,
            boundary,
        ),
        observation(item, "efficiency_profile", item["efficiency_profile"], "%", boundary),
        observation(item, "topology", FAMILY_NOTES[family]["topology"], None, boundary),
        observation(
            item,
            "battery_interface",
            FAMILY_NOTES[family]["battery"],
            None,
            "UPS battery-interface statement only; no battery model, energy or runtime "
            "record created",
        ),
        observation(item, "overload_tolerance", FAMILY_NOTES[family]["overload"], None, boundary),
        observation(
            item,
            "communications",
            FAMILY_NOTES[family]["protocols"],
            None,
            "Published family interface statement; optional interfaces are not selected",
        ),
        observation(
            item,
            "standards_and_claims",
            FAMILY_NOTES[family]["standards"],
            None,
            "OEM statement only; not normalized as an issuer-registry certification",
        ),
    ]
    fields = [
        "apparent_power_kva",
        "capacity_scope",
        "depth_mm",
        "equipment_category",
        "form_factor",
        "height_mm",
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
        "weight_kg",
        "width_mm",
    ]
    for field in (
        "communication_protocols",
        "efficiency_conditions",
        "efficiency_pct",
        "frequency_hz",
        "input_current_a",
        "input_voltage_v",
        "output_power_kw",
        "output_voltage_v",
        "thermal_output_kw",
    ):
        if item.get(field) is not None:
            fields.append(field)
    evidence: dict[str, dict[str, object]] = {}
    units = {
        "apparent_power_kva": "kVA",
        "depth_mm": "mm",
        "efficiency_pct": "%",
        "frequency_hz": "Hz",
        "height_mm": "mm",
        "input_current_a": "A",
        "input_voltage_v": "V",
        "output_power_kw": "kW",
        "output_voltage_v": "V",
        "thermal_output_kw": "kW",
        "weight_kg": "kg",
        "width_mm": "mm",
    }
    publication_date = item["publication_date"]
    for field in fields:
        source_id = (
            PORTFOLIO_ID if field == "product_status" and family != "UPS7500WX-T4" else exact_source
        )
        entry: dict[str, object] = {
            "confidence": "high",
            "locator": (
                f"current portfolio card / {family}"
                if source_id == PORTFOLIO_ID
                else item["locator"]
            ),
            "source_publication_dates": {source_id: publication_date},
        }
        if field in units:
            entry["unit"] = units[field]
        evidence[field] = entry
    field_sources = {
        field: [
            PORTFOLIO_ID if field == "product_status" and family != "UPS7500WX-T4" else exact_source
        ]
        for field in fields
    }
    record: dict[str, object] = {
        "apparent_power_kva": item["apparent_power_kva"],
        "capacity_scope": (
            f"Exact OEM {family} rating/configuration; apparent and active power remain "
            "source-reported only, and battery or optional-system combinations are excluded"
        ),
        "created_at": RETRIEVED_AT,
        "depth_mm": item["depth_mm"],
        "entity_type": "equipment",
        "equipment_category": "ups",
        "evidence_json": compact(evidence),
        "field_sources_json": compact(field_sources),
        "form_factor": "Floor-standing UPS system",
        "height_mm": item["height_mm"],
        "last_verified_at": RETRIEVED_AT,
        "manufacturer": "Fuji Electric",
        "model": family,
        "name": (
            f"Fuji Electric {family} {item['apparent_power_kva']:g} kVA {item['upm_count']} UPM"
        ),
        "notes": (
            "The exact published model/rating column is retained. Nominal and maximum input "
            "current, output current, efficiency modes/load points, battery interface and OEM "
            "standards statements remain distinct. No battery energy, runtime, installed "
            "deployment or optional topology is inferred."
        ),
        "observations_json": compact(observations),
        "official_url": item["source_url"],
        "power_conditions": (
            f"{item['voltage_text']}; {item['frequency_text']}; rated OEM UPS output; "
            "online/double-conversion conditions where stated in the exact source"
        ),
        "power_rating_kind": (
            "rated UPS output apparent and active power"
            if item["output_power_kw"] is not None
            else "rated UPS output apparent power; active kW not inferred"
        ),
        "product_status": "listed in the current Fuji Electric UPS portfolio",
        "quality_status": "source_backed",
        "record_id": stable_id("equipment", "Fuji Electric", family, str(item["variant"])),
        "record_scope": "configuration",
        "source_urls": sorted(source_urls),
        "sources": source_ids,
        "updated_at": RETRIEVED_AT,
        "variant": item["variant"],
        "weight_kg": item["weight_kg"],
        "width_mm": item["width_mm"],
    }
    for field in (
        "communication_protocols",
        "efficiency_conditions",
        "efficiency_pct",
        "frequency_hz",
        "input_current_a",
        "input_voltage_v",
        "output_power_kw",
        "output_voltage_v",
        "thermal_output_kw",
    ):
        if item.get(field) is not None:
            record[field] = item[field]
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    items = rows()
    parse_ups_rating_matrix(extracted_csv(items), source_url=PORTFOLIO_URL, expected_count=20)
    records = sorted(
        (build_record(item) for item in items),
        key=lambda record: (record["model"], record["apparent_power_kva"], record["variant"]),
    )
    if len(records) != 20 or len({record["record_id"] for record in records}) != 20:
        raise ValueError("Expected 20 unique Fuji Electric UPS configurations")
    args.output.write_text("".join(f"{compact(record)}\n" for record in records), encoding="utf-8")
    print("Wrote 20 reviewed Fuji Electric current UPS configurations")


if __name__ == "__main__":
    main()
