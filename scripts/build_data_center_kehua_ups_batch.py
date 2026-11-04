"""Build reviewed Kehua Tech current UPS model configurations."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
from typing import Any

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.inventories import parse_ups_rating_matrix

RETRIEVED_AT = "2026-11-04T01:34:00Z"
AS_OF = "2026-11-04"
PORTFOLIO_ID = "kehua-critical-power-portfolio-20261104"
PORTFOLIO_URL = "https://www.kehua.com/critical-power.html"

SOURCES = {
    "KR11-RM": (
        "kehua-kr11-rm-current-20261104",
        "https://www.kehua.com/critical-power/kr11-rm-series-1-10kva",
    ),
    "KR-RM": (
        "kehua-kr-rm-current-20261104",
        "https://www.kehua.com/critical-power/kr-rm-series-10-40kva.html",
    ),
    "Eon": (
        "kehua-eon-current-20261104",
        "https://www.kehua.com/critical-power/eon-series-10-30kw.html",
    ),
    "MY": (
        "kehua-my-current-20261104",
        "https://www.kehua.com/critical-power/my-series-60-200kw",
    ),
    "KR33": (
        "kehua-kr33-en-current-20261104",
        "https://www.kehua.com/critical-power/kr33-series-300-1200kva",
    ),
}
KR33_ES_ID = "kehua-kr33-es-current-20261104"
KR33_ES_URL = "https://www.kehua.com/es/critical-power/kr33-series-300-1200kva.html"

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
        source_id, source_url = SOURCES[family]
        values.update(
            family=family,
            manufacturer="Kehua Tech",
            source_id=source_id,
            source_url=source_url,
        )
        result.append(values)

    for model, kva, efficiency, depth, height, weight, ebm_depth, ebm_height, ebm_weight in (
        ("KR1000-RM", 1, 92.5, 420, 87, 14, 420, 87, 20),
        ("KR2000-RM", 2, 93.5, 570, 87, 20, 420, 87, 29),
        ("KR3000-RM", 3, 93.8, 570, 87, 26, 420, 87, 40),
        ("KR6000-RM", 6, 95.5, 660, 174, 55.6, 500, 130, 45),
        ("KR1110-RM", 10, 95.5, 660, 174, 64, 500, 130, 48),
    ):
        high_power = kva >= 6
        add(
            "KR11-RM",
            model=model,
            apparent_power_kva=kva,
            output_power_kw=None,
            input_text=(
                "L-N 80-275 V; source also prints 176-295 V at full load"
                if high_power
                else "L-N 120-295 V; 176-295 V at full load"
            ),
            output_text="L-N 208/220/230/240 V +/-1% selectable",
            frequency_text="50/60 Hz self-adapting; frequency-converter mode",
            efficiency=efficiency,
            width=438,
            depth=depth,
            height=height,
            weight=weight,
            form_factor="rack/tower UPS; 4U" if high_power else "rack/tower UPS; 2U",
            extra_observations=[
                (
                    "external_battery_module_dimensions",
                    f"438 x {ebm_depth} x {ebm_height} mm",
                    "mm",
                ),
                ("external_battery_module_weight", ebm_weight, "kg"),
                (
                    "battery_interface",
                    "Internal/external hot-swappable modules; selectable battery count and "
                    "charger options; no battery model or runtime selected",
                    None,
                ),
            ],
            locator=f"KR11-RM technical specification / {model} column",
        )

    for model, kva, input_text, output_text, depth, weight in (
        ("KR10KVA-RM", 10, "L-L 138-485 V; 305-485 V at full load", "L-L 380/400/415 V", 535, 17.5),
        (
            "KR20KVA-RM",
            20,
            "L-L 121-268 V or 138-485 V; full-load ranges 155-268 V or 305-485 V",
            "L-L 190/200/208/220/380/400/415 V",
            535,
            17.5,
        ),
        ("KR30KVA-RM", 30, "L-L 138-485 V; 305-485 V at full load", "L-L 380/400/415 V", 720, 34.5),
        (
            "KR40KVA-RM",
            40,
            "L-L 121-268 V or 138-485 V; full-load ranges 155-268 V or 305-485 V",
            "L-L 190/200/208/220/380/400/415 V",
            720,
            34.5,
        ),
    ):
        distribution_weight = 8 if kva <= 20 else 14
        ebm_weight = 45 if kva <= 20 else 56
        add(
            "KR-RM",
            model=model,
            apparent_power_kva=kva,
            output_power_kw=None,
            input_text=input_text,
            output_text=output_text,
            frequency_text="40-70 Hz input range; 50/60 Hz frequency-converter choices",
            efficiency=96.0,
            width=438,
            depth=depth,
            height=130,
            weight=weight,
            form_factor="3U rack/tower UPS",
            extra_observations=[
                ("distribution_box_dimensions", f"438 x {depth} x 130 mm", "mm"),
                ("distribution_box_weight", distribution_weight, "kg"),
                ("battery_pack_dimensions", f"438 x {depth} x 130 mm", "mm"),
                ("battery_pack_weight", ebm_weight, "kg"),
                (
                    "battery_compatibility",
                    "VRLA or lithium; no battery model, energy or runtime selected",
                    None,
                ),
            ],
            locator=f"KR-RM technical specification / {model} column",
        )

    for model, kw, weight in (("Eon10", 10, 211), ("Eon20", 20, 276), ("Eon30", 30, 340)):
        add(
            "Eon",
            model=model,
            apparent_power_kva=None,
            output_power_kw=kw,
            input_text="L-L 120-268 V; 156-268 V at full load",
            output_text="L-L 190/200/208/220 V +/-1%; default 208 V",
            frequency_text="Not stated in the reviewed exact table",
            efficiency=94.0,
            width=378,
            depth=993,
            height=1250,
            weight=weight,
            form_factor="floor-standing UPS with hot-swappable battery modules",
            extra_observations=[
                ("eco_efficiency", 99, "%"),
                ("output_power_factor", 1.0, "ratio"),
                ("maximum_ambient_temperature", 50, "degC"),
            ],
            locator=f"Eon technical specification / {model} column",
        )

    for model, kw, width, depth, height, weight in (
        ("MY60", 60, 400, 960, 1200, 153),
        ("MY80", 80, 400, 960, 1200, 163),
        ("MY100", 100, 400, 960, 1200, 165),
        ("MY120", 120, 400, 960, 1200, 161),
        ("MY160", 160, 600, 1000, 1600, 294),
        ("MY200", 200, 600, 1000, 1600, 296),
    ):
        add(
            "MY",
            model=model,
            apparent_power_kva=None,
            output_power_kw=kw,
            input_text="L-L 138-485 V; 324-485 V at full load",
            output_text="L-L 380/400/415 V +/-1% selectable",
            frequency_text="Not stated in the reviewed exact table",
            efficiency=96.5,
            width=width,
            depth=depth,
            height=height,
            weight=weight,
            form_factor="floor-standing UPS",
            extra_observations=[
                ("efficiency_at_30_pct_load", 95, "%"),
                ("short_circuit_duration_range", "20-200 ms settable", "ms"),
                (
                    "battery_parallel_mode",
                    "Common battery bank supported; no battery configuration selected",
                    None,
                ),
            ],
            locator=f"MY technical specification / {model} column",
        )

    english_weights = (700, 700, 1050, 1050, 1400, 2350, 2350)
    spanish_weights = (750, 750, 1100, 1100, 1450, 2400, 2400)
    for model, kva, width, en_weight, es_weight in zip(
        ("KR33300", "KR33400", "KR33500", "KR33600", "KR33800", "KR331000", "KR331200"),
        (300, 400, 500, 600, 800, 1000, 1200),
        (1000, 1000, 1400, 1400, 1900, 3000, 3000),
        english_weights,
        spanish_weights,
        strict=True,
    ):
        add(
            "KR33",
            model=model,
            apparent_power_kva=kva,
            output_power_kw=None,
            input_text=(
                "English page prints an input range; Spanish page prints 380/400/415 V rated input"
            ),
            output_text="L-L 380/400/415 V +/-1% selectable",
            frequency_text="Not stated in the reviewed exact tables",
            efficiency=None,
            width=width,
            depth=900,
            height=1950,
            weight=None,
            form_factor="floor-standing large UPS",
            extra_observations=[
                ("english_page_maximum_efficiency", 96.5, "%"),
                ("spanish_page_maximum_efficiency", 97.0, "%"),
                ("english_page_weight", en_weight, "kg"),
                ("spanish_page_weight", es_weight, "kg"),
                ("parallel_portfolio_limit", "up to eight units / 9.6 MVA", None),
            ],
            locator=f"KR33 technical specification / {model} column",
            conflicting_source_id=KR33_ES_ID,
            conflicting_source_url=KR33_ES_URL,
        )
    return result


def extracted_csv(items: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for item in items:
        writer.writerow(
            {
                "manufacturer": item["manufacturer"],
                "family": item["family"],
                "variant": variant(item),
                "apparent_power_kva": item["apparent_power_kva"] or "",
                "output_power_kw": item["output_power_kw"] or "",
                "voltage_text": f"input {item['input_text']}; output {item['output_text']}",
                "frequency_text": item["frequency_text"],
                "locator": item["locator"],
            }
        )
    return stream.getvalue().encode()


def variant(item: dict[str, Any]) -> str:
    if item["apparent_power_kva"] is not None:
        return f"{item['apparent_power_kva']} kVA published configuration"
    return f"{item['output_power_kw']} kW published configuration"


def observation(
    item: dict[str, Any], field: str, value: object, unit: str | None
) -> dict[str, object]:
    return {
        "as_of": AS_OF,
        "boundary": f"Exact {item['model']} published model column",
        "field": field,
        "kind": "reported",
        "locator": item["locator"],
        "source_id": item["source_id"],
        "unit": unit,
        "value": value,
    }


def build_record(item: dict[str, Any]) -> dict[str, object]:
    fields = [
        "capacity_scope",
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
        "power_conditions",
        "power_rating_kind",
        "product_status",
        "record_scope",
        "variant",
        "weight_kg",
        "width_mm",
    ]
    if item["apparent_power_kva"] is not None:
        fields.append("apparent_power_kva")
    if item["output_power_kw"] is not None:
        fields.append("output_power_kw")
    if item["efficiency"] is None:
        fields.remove("efficiency_pct")
        fields.remove("efficiency_conditions")
    if item["weight"] is None:
        fields.remove("weight_kg")
    source_ids = [item["source_id"], PORTFOLIO_ID]
    source_urls = [item["source_url"], PORTFOLIO_URL]
    if item.get("conflicting_source_id"):
        source_ids.append(item["conflicting_source_id"])
        source_urls.append(item["conflicting_source_url"])
    evidence: dict[str, dict[str, object]] = {}
    units = {
        "apparent_power_kva": "kVA",
        "output_power_kw": "kW",
        "efficiency_pct": "%",
        "width_mm": "mm",
        "depth_mm": "mm",
        "height_mm": "mm",
        "weight_kg": "kg",
    }
    for field in fields:
        evidence[field] = {
            "confidence": "high",
            "locator": item["locator"],
            "source_publication_dates": {source_id: None for source_id in source_ids},
        }
        if field in units:
            evidence[field]["unit"] = units[field]
    observations = [
        observation(item, "input_voltage_range_or_choices", item["input_text"], "V"),
        observation(item, "output_voltage_choices", item["output_text"], "V"),
        observation(item, "frequency_behavior", item["frequency_text"], "Hz"),
    ]
    observations.extend(
        observation(item, field, value, unit) for field, value, unit in item["extra_observations"]
    )
    model = str(item["model"])
    rating = variant(item)
    record: dict[str, object] = {
        "capacity_scope": (
            f"Exact OEM {model} model column; alternative voltage, frequency, battery, "
            "parallel and accessory choices are observations, not selected configurations"
        ),
        "created_at": RETRIEVED_AT,
        "depth_mm": item["depth"],
        "entity_type": "equipment",
        "equipment_category": "ups",
        "evidence_json": compact(evidence),
        "field_sources_json": compact({field: source_ids for field in fields}),
        "form_factor": item["form_factor"],
        "height_mm": item["height"],
        "last_verified_at": RETRIEVED_AT,
        "manufacturer": "Kehua Tech",
        "model": model,
        "name": f"Kehua Tech {model}",
        "notes": (
            "The exact current OEM model column is retained. Input/output voltage ranges "
            "and choices remain observations because no ordered voltage is selected. "
            "No battery energy, usable energy, runtime, deployment or option combination "
            "is inferred. KR33 efficiency and weight remain null because the current "
            "English and Spanish official pages conflict."
        ),
        "observations_json": compact(observations),
        "official_url": item["source_url"],
        "power_conditions": (
            "OEM published model rating; maximum efficiency has no stated load point; "
            "voltage and frequency options remain unselected"
        ),
        "power_rating_kind": (
            "rated UPS apparent power"
            if item["apparent_power_kva"] is not None
            else "rated UPS active output"
        ),
        "product_status": "listed in current Kehua Critical Power portfolio",
        "quality_status": "needs_review"
        if item["family"] == "KR33" or model in {"KR6000-RM", "KR1110-RM"}
        else "source_backed",
        "record_id": stable_id("equipment", "Kehua Tech", model, rating),
        "record_scope": "configuration",
        "source_urls": sorted(set(source_urls)),
        "sources": source_ids,
        "updated_at": RETRIEVED_AT,
        "variant": rating,
        "width_mm": item["width"],
    }
    if item["apparent_power_kva"] is not None:
        record["apparent_power_kva"] = item["apparent_power_kva"]
    if item["output_power_kw"] is not None:
        record["output_power_kw"] = item["output_power_kw"]
    if item["efficiency"] is not None:
        record["efficiency_pct"] = item["efficiency"]
        record["efficiency_conditions"] = "Maximum AC/AC efficiency; load point not stated"
    if item["weight"] is not None:
        record["weight_kg"] = item["weight"]
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    items = rows()
    parse_ups_rating_matrix(extracted_csv(items), source_url=PORTFOLIO_URL, expected_count=25)
    records = sorted(
        (build_record(item) for item in items),
        key=lambda record: (record["model"], record["variant"]),
    )
    if len(records) != 25 or len({record["record_id"] for record in records}) != 25:
        raise ValueError("Expected 25 unique Kehua Tech UPS configurations")
    args.output.write_text("".join(f"{compact(record)}\n" for record in records), encoding="utf-8")
    print("Wrote 25 reviewed Kehua Tech UPS configurations")


if __name__ == "__main__":
    main()
