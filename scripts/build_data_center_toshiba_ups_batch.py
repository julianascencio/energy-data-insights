"""Build reviewed Toshiba current three-phase UPS rating configurations."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
from typing import Any

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.inventories import parse_ups_rating_matrix

RETRIEVED_AT = "2026-11-03T20:27:00Z"
AS_OF = "2026-11-03"
SOURCES = {
    "toshiba-g9400-current-20261103": {
        "url": "https://toshiba.com/tic/product/g9400-series-ups/",
        "family": "G9400 Series",
        "publication_date": None,
    },
    "toshiba-g9000-current-20261103": {
        "url": "https://toshiba.com/tic/product/g9000-series-100-1050kva/",
        "family": "G9000 Series",
        "publication_date": None,
    },
    "toshiba-4400-current-20261103": {
        "url": "https://toshiba.com/tic/product/4400-series-3-phase-ups/",
        "family": "4400 Series",
        "publication_date": None,
    },
    "toshiba-3000tp-current-20261103": {
        "url": "https://toshiba.com/tic/product/3000-tp-series-ups/",
        "family": "3000 TP Series",
        "publication_date": "2026-05-04",
    },
}


def row(
    source: str,
    kva: int,
    voltage: str,
    frequency: str,
    *,
    kw: int | None = None,
    market: str,
) -> dict[str, Any]:
    family = str(SOURCES[source]["family"])
    power = f"{kva} kVA/kW" if kw is not None else f"{kva} kVA"
    return {
        "source": source,
        "manufacturer": "Toshiba",
        "family": family,
        "variant": f"{power}; {voltage}; {frequency}",
        "apparent_power_kva": kva,
        "output_power_kw": kw,
        "voltage_text": voltage,
        "frequency_text": frequency,
        "market": market,
        "locator": f"current product page / {family} capacity list / {power}",
    }


ROWS: list[dict[str, Any]] = []
for kva in (1050, 1400, 1750):
    ROWS.append(
        row(
            "toshiba-g9400-current-20261103",
            kva,
            "380-415 V",
            "50/60 Hz",
            market="global voltage configuration",
        )
    )
for kva in (1200, 1600, 2000):
    ROWS.append(
        row(
            "toshiba-g9400-current-20261103",
            kva,
            "480 V",
            "60 Hz",
            market="480 V configuration",
        )
    )
for kva in (100, 160, 225, 300, 500, 750, 1050):
    ROWS.append(
        row(
            "toshiba-g9000-current-20261103",
            kva,
            "480 V, 3-wire plus ground",
            "not stated on current page",
            market="480 V monolithic configuration",
        )
    )
for kva in (15, 20, 25, 30, 50):
    ROWS.append(
        row(
            "toshiba-4400-current-20261103",
            kva,
            "208 V, 4-wire",
            "not stated on current page",
            market="208 V monolithic configuration",
        )
    )
for kva in (40, 80, 120, 160, 200):
    ROWS.append(
        row(
            "toshiba-3000tp-current-20261103",
            kva,
            "480 V",
            "60 Hz",
            kw=kva,
            market="480 V modular configuration",
        )
    )

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


def extracted_csv(rows: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for item in rows:
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
        "source_id": item["source"],
        "unit": unit,
        "value": value,
    }


def build_record(item: dict[str, Any]) -> dict[str, object]:
    source_id = str(item["source"])
    source_url = str(SOURCES[source_id]["url"])
    family = str(item["family"])
    locator = str(item["locator"])
    boundary = f"Exact published {family} {item['variant']} configuration"
    fields = [
        "apparent_power_kva",
        "capacity_scope",
        "equipment_category",
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
    if item["output_power_kw"] is not None:
        fields.append("output_power_kw")
    warranty = family in {"G9000 Series", "4400 Series", "3000 TP Series"}
    if warranty:
        fields.extend(["warranty_conditions", "warranty_years"])
    evidence: dict[str, dict[str, object]] = {
        field: {
            "confidence": "high",
            "locator": locator,
            "source_publication_dates": {source_id: SOURCES[source_id]["publication_date"]},
        }
        for field in fields
    }
    evidence["apparent_power_kva"]["unit"] = "kVA"
    if item["output_power_kw"] is not None:
        evidence["output_power_kw"]["unit"] = "kW"
    if warranty:
        evidence["warranty_years"]["unit"] = "years"
    observations = [
        observation(item, "voltage_configuration", item["voltage_text"], "V", boundary),
        observation(item, "market_configuration", item["market"], None, boundary),
    ]
    if not str(item["frequency_text"]).startswith("not stated"):
        observations.append(
            observation(item, "frequency_configuration", item["frequency_text"], "Hz", boundary)
        )
    family_observations: dict[str, list[tuple[str, object, str | None, str]]] = {
        "G9400 Series": [
            (
                "maximum_online_efficiency",
                97,
                "%",
                "family claim across various loads; not normalized at rating-row level",
            ),
            ("parallel_units", 6, None, "family maximum"),
        ],
        "G9000 Series": [
            (
                "maximum_efficiency",
                97,
                "%",
                "family claim at 50-100% load; not normalized at rating-row level",
            ),
            (
                "minimum_efficiency_at_20pct_load",
                94,
                "%",
                "family claim expressed as greater than 94%",
            ),
            (
                "supported_battery_technologies",
                "VRLA; NiCad; Toshiba SCiB lithium-titanium-oxide",
                None,
                "compatibility choices only; no battery configuration duplicated",
            ),
        ],
        "4400 Series": [
            ("output_power_factor", 0.9, None, "family statement; no active kW derived"),
            (
                "battery_link_voltage",
                288,
                "VDC",
                "external battery-link option; no energy or runtime inferred",
            ),
        ],
        "3000 TP Series": [
            (
                "maximum_ac_ac_efficiency",
                96.5,
                "%",
                "family claim without a stated load point; not normalized",
            ),
            ("power_module_rating", 40, "kW", "hot-swappable module nameplate"),
            ("cabinet_height", 42, "U", "six-shelf architecture"),
        ],
    }
    for field, value, unit, scope in family_observations[family]:
        observations.append(observation(item, field, value, unit, f"{family}; {scope}"))
    record: dict[str, object] = {
        "apparent_power_kva": item["apparent_power_kva"],
        "capacity_scope": (
            f"Exact current OEM {family} rating configuration; optional batteries, "
            "bypass cabinets, transformers and parallel combinations excluded"
        ),
        "created_at": RETRIEVED_AT,
        "entity_type": "equipment",
        "equipment_category": "ups",
        "evidence_json": compact(evidence),
        "field_sources_json": compact({field: [source_id] for field in fields}),
        "form_factor": "three-phase UPS",
        "last_verified_at": RETRIEVED_AT,
        "manufacturer": "Toshiba",
        "model": family,
        "name": f"Toshiba {family} {item['apparent_power_kva']} kVA",
        "notes": (
            "kVA and active kW remain separate. Voltage/frequency market variants and "
            "family efficiency claims remain observations; no optional cabinet, battery, "
            "runtime or parallel-system combination is synthesized."
        ),
        "observations_json": compact(observations),
        "official_url": source_url,
        "power_conditions": (
            f"OEM current product-page rating for {item['market']}; active output is "
            "normalized only when the page explicitly states kVA/kW"
        ),
        "power_rating_kind": "rated UPS output apparent power",
        "product_status": "listed on current Toshiba three-phase UPS product page",
        "quality_status": "source_backed",
        "record_id": stable_id("equipment", "Toshiba", family, str(item["variant"])),
        "record_scope": "configuration",
        "source_urls": [source_url],
        "sources": [source_id],
        "updated_at": RETRIEVED_AT,
        "variant": item["variant"],
    }
    if item["output_power_kw"] is not None:
        record["output_power_kw"] = item["output_power_kw"]
    if warranty:
        record["warranty_conditions"] = "Three-year onsite warranty; OEM family statement"
        record["warranty_years"] = 3
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    for source_id, source in SOURCES.items():
        selected = [item for item in ROWS if item["source"] == source_id]
        parse_ups_rating_matrix(
            extracted_csv(selected),
            source_url=str(source["url"]),
            expected_count=len(selected),
        )
    records = sorted(
        (build_record(item) for item in ROWS),
        key=lambda record: (record["model"], record["variant"]),
    )
    if len(records) != 23 or len({record["record_id"] for record in records}) != 23:
        raise ValueError("Expected 23 unique Toshiba UPS rating configurations")
    args.output.write_text("".join(f"{compact(record)}\n" for record in records), encoding="utf-8")
    print("Wrote 23 reviewed Toshiba current UPS rating configurations")


if __name__ == "__main__":
    main()
