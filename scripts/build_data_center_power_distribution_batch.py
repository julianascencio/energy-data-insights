"""Build reviewed Eaton transformer and Siemens switchgear catalogue records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id

RETRIEVED_AT = "2026-11-03T11:19:28Z"
AS_OF = "2026-11-03"
EATON_SOURCE = "eaton-dry-transformer-tables-20261103"
EATON_URL = (
    "https://www.eaton.com/dk/da-dk/catalog/medium-voltage-power-distribution-"
    "control-systems/dry-type-transformer.html"
)
SIEMENS_SOURCE = "siemens-nxair-portfolio-20261103"
SIEMENS_URL = "https://www.siemens.com/en-us/products/energy-systems/nxair/"

# Standard, kVA, no-load W, load W, short-circuit %, dB, L, W, H, D, E, F, kg.
EATON_ROWS = (
    ("EU No. 548/2014 Tier 1", 250, 520, 3800, 6, 59, 1260, 750, 1260, 520, 125, 40, 1090),
    ("EU No. 548/2014 Tier 1", 400, 750, 5500, 6, 61, 1370, 950, 1360, 670, 160, 50, 1370),
    ("EU No. 548/2014 Tier 1", 630, 1100, 7600, 6, 63, 1440, 1100, 1540, 670, 160, 50, 1790),
    ("EU No. 548/2014 Tier 1", 800, 1300, 8000, 6, 64, 1530, 1100, 1620, 670, 160, 50, 2200),
    ("EU No. 548/2014 Tier 1", 1000, 1550, 9000, 6, 65, 1610, 1100, 1640, 820, 160, 50, 2550),
    ("EU No. 548/2014 Tier 1", 1250, 1800, 11000, 6, 67, 1650, 1100, 1740, 820, 160, 50, 2950),
    ("EU No. 548/2014 Tier 1", 1600, 2200, 13000, 6, 68, 1760, 1100, 1850, 820, 160, 50, 3560),
    ("EU No. 548/2014 Tier 1", 2000, 2600, 16000, 6, 72, 1820, 1200, 2190, 1070, 200, 70, 4360),
    ("BS EN 50541-1:2011", 250, 820, 3500, 6, 65, 1280, 750, 1160, 520, 125, 40, 990),
    ("BS EN 50541-1:2011", 400, 1150, 4900, 6, 68, 1380, 950, 1310, 670, 160, 50, 1330),
    ("BS EN 50541-1:2011", 630, 1500, 7300, 6, 70, 1440, 1100, 1450, 670, 160, 50, 1720),
    ("BS EN 50541-1:2011", 800, 1800, 9000, 6, 71, 1530, 1100, 1550, 670, 160, 50, 2120),
    ("BS EN 50541-1:2011", 1000, 2100, 10000, 6, 73, 1600, 1100, 1620, 820, 160, 50, 2470),
    ("BS EN 50541-1:2011", 1250, 2500, 12000, 6, 75, 1650, 1100, 1700, 820, 160, 50, 2770),
    ("BS EN 50541-1:2011", 1600, 2800, 14500, 6, 76, 1760, 1100, 1790, 820, 160, 50, 3380),
    ("BS EN 50541-1:2011", 2000, 3600, 18000, 6, 78, 1810, 1200, 2060, 1070, 200, 70, 4010),
)

# Model, portfolio variant, maximum voltage kV, maximum short-circuit kA,
# maximum continuous current A (null where the current page does not state it).
SIEMENS_ROWS = (
    ("NXAIR", "17.5 kV / 40 kA portfolio rating", 17.5, 40, 4000),
    ("NXAIR 50 kA", "17.5 kV / 50 kA portfolio rating", 17.5, 50, 4000),
    ("NXAIR M", "24 kV / 25 kA portfolio rating", 24, 25, None),
    ("NXAIR C", "24 kV / 25 kA / 2000 A portfolio rating", 24, 25, 2000),
    ("NXAIR H", "36 kV / 31.5 kA / 2900 A portfolio rating", 36, 31.5, 2900),
)


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def evidence(fields: list[str], source_id: str, locator: str) -> str:
    units = {
        "apparent_power_kva": "kVA",
        "depth_mm": "mm",
        "height_mm": "mm",
        "weight_kg": "kg",
        "width_mm": "mm",
    }
    payload: dict[str, dict[str, Any]] = {}
    for field in fields:
        payload[field] = {
            "confidence": "high",
            "locator": locator,
            "source_publication_dates": {source_id: None},
        }
        if field in units:
            payload[field]["unit"] = units[field]
    return compact(payload)


def observation(
    *, field: str, value: object, unit: str | None, source_id: str, locator: str, boundary: str
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


def build_eaton(row: tuple[object, ...]) -> dict[str, object]:
    standard, kva, no_load, load, short_pct, noise, length, width, height, d, e, f, weight = row
    standard = str(standard)
    locator = f"{standard} / Voltage 7.2 kV - 12 kV table / {kva} kVA row"
    boundary = f"Eaton dry-type transformer; {standard}; 7.2-12 kV voltage class; {kva} kVA"
    fields = [
        "apparent_power_kva",
        "capacity_scope",
        "depth_mm",
        "equipment_category",
        "evidence_json",
        "form_factor",
        "height_mm",
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
        "weight_kg",
        "width_mm",
    ]
    observations = [
        observation(
            field="voltage_class",
            value="7.2-12",
            unit="kV",
            source_id=EATON_SOURCE,
            locator=locator,
            boundary=boundary,
        ),
        observation(
            field="no_load_loss",
            value=no_load,
            unit="W",
            source_id=EATON_SOURCE,
            locator=locator,
            boundary=boundary,
        ),
        observation(
            field="load_loss",
            value=load,
            unit="W",
            source_id=EATON_SOURCE,
            locator=locator,
            boundary=boundary,
        ),
        observation(
            field="short_circuit_impedance",
            value=short_pct,
            unit="%",
            source_id=EATON_SOURCE,
            locator=locator,
            boundary=boundary,
        ),
        observation(
            field="noise_level",
            value=noise,
            unit="dB",
            source_id=EATON_SOURCE,
            locator=locator,
            boundary=boundary,
        ),
        observation(
            field="dimension_D",
            value=d,
            unit="mm",
            source_id=EATON_SOURCE,
            locator=locator,
            boundary=boundary,
        ),
        observation(
            field="dimension_E",
            value=e,
            unit="mm",
            source_id=EATON_SOURCE,
            locator=locator,
            boundary=boundary,
        ),
        observation(
            field="dimension_F",
            value=f,
            unit="mm",
            source_id=EATON_SOURCE,
            locator=locator,
            boundary=boundary,
        ),
    ]
    variant = f"{standard}; 7.2-12 kV class; {kva} kVA"
    return {
        "apparent_power_kva": kva,
        "capacity_scope": (
            f"Exact Eaton published {standard} {kva} kVA table configuration; "
            "apparent power is not converted to active kW"
        ),
        "created_at": RETRIEVED_AT,
        "depth_mm": length,
        "entity_type": "equipment",
        "equipment_category": "transformer",
        "evidence_json": evidence(fields, EATON_SOURCE, locator),
        "field_sources_json": compact({field: [EATON_SOURCE] for field in fields}),
        "form_factor": "dry-type medium-voltage transformer",
        "height_mm": height,
        "last_verified_at": RETRIEVED_AT,
        "manufacturer": "Eaton",
        "model": "Dry type transformer",
        "name": f"Eaton dry type transformer {standard} {kva} kVA",
        "notes": (
            "The OEM table supplies a voltage class rather than one nominal winding "
            "voltage. Input/output voltage, active kW and efficiency remain null; "
            "losses and short-circuit impedance are retained as observations."
        ),
        "observations_json": compact(observations),
        "official_url": EATON_URL,
        "power_conditions": (
            f"OEM rated apparent power for the {standard} table row in the 7.2-12 kV voltage class"
        ),
        "power_rating_kind": "rated transformer apparent power",
        "product_status": "listed on current Eaton dry-type transformer product page",
        "quality_status": "source_backed",
        "record_id": stable_id(
            "equipment", "Eaton", "Dry type transformer", standard, "7.2-12 kV", f"{kva} kVA"
        ),
        "record_scope": "configuration",
        "source_urls": [EATON_URL],
        "sources": [EATON_SOURCE],
        "updated_at": RETRIEVED_AT,
        "variant": variant,
        "weight_kg": weight,
        "width_mm": width,
    }


def build_siemens(row: tuple[object, ...]) -> dict[str, object]:
    model, variant, max_voltage, max_short, max_current = row
    locator = f"NXAIR product portfolio card: {model}"
    boundary = f"Siemens {model} portfolio maximum; not an ordered panel configuration"
    observations = [
        observation(
            field="maximum_rated_voltage",
            value=max_voltage,
            unit="kV",
            source_id=SIEMENS_SOURCE,
            locator=locator,
            boundary=boundary,
        ),
        observation(
            field="maximum_short_circuit_current",
            value=max_short,
            unit="kA",
            source_id=SIEMENS_SOURCE,
            locator=locator,
            boundary=boundary,
        ),
        observation(
            field="insulation_medium",
            value="natural air",
            unit=None,
            source_id=SIEMENS_SOURCE,
            locator="NXAIR portfolio overview",
            boundary=f"Siemens {model} family",
        ),
        observation(
            field="standard_claim",
            value="IEC 62271-200",
            unit=None,
            source_id=SIEMENS_SOURCE,
            locator="NXAIR portfolio overview",
            boundary="OEM family claim; no issuer certificate identifier normalized",
        ),
    ]
    if max_current is not None:
        observations.append(
            observation(
                field="maximum_rated_continuous_current",
                value=max_current,
                unit="A",
                source_id=SIEMENS_SOURCE,
                locator=locator,
                boundary=boundary,
            )
        )
    fields = [
        "capacity_scope",
        "equipment_category",
        "evidence_json",
        "form_factor",
        "manufacturer",
        "model",
        "name",
        "observations_json",
        "official_url",
        "product_status",
        "record_scope",
        "variant",
    ]
    return {
        "capacity_scope": (
            f"Exact Siemens {model} current portfolio variant; voltage, fault-current "
            "and continuous-current values are stated maxima, not nominal inputs"
        ),
        "created_at": RETRIEVED_AT,
        "entity_type": "equipment",
        "equipment_category": "switchgear",
        "evidence_json": evidence(fields, SIEMENS_SOURCE, locator),
        "field_sources_json": compact({field: [SIEMENS_SOURCE] for field in fields}),
        "form_factor": "air-insulated medium-voltage switchgear",
        "last_verified_at": RETRIEVED_AT,
        "manufacturer": "Siemens",
        "model": model,
        "name": f"Siemens {model} {variant}",
        "notes": (
            "Maximum portfolio ratings are retained as observations. No nominal "
            "voltage/current, panel width, breaker configuration, remote-monitoring "
            "protocol or EcoTech certification is inferred for an ordered panel."
        ),
        "observations_json": compact(observations),
        "official_url": SIEMENS_URL,
        "product_status": "listed in current Siemens NXAIR portfolio",
        "quality_status": "source_backed",
        "record_id": stable_id("equipment", "Siemens", str(model), str(variant)),
        "record_scope": "model",
        "source_urls": [SIEMENS_URL],
        "sources": [SIEMENS_SOURCE],
        "updated_at": RETRIEVED_AT,
        "variant": variant,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = [
        *(build_eaton(row) for row in EATON_ROWS),
        *(build_siemens(row) for row in SIEMENS_ROWS),
    ]
    if len(rows) != 21 or len({row["record_id"] for row in rows}) != 21:
        raise ValueError("Expected 21 unique power-distribution records")
    rows.sort(key=lambda item: str(item["record_id"]))
    args.output.write_text("".join(f"{compact(row)}\n" for row in rows), encoding="utf-8")
    print(f"Wrote {len(rows)} reviewed transformer/switchgear records to {args.output}")


if __name__ == "__main__":
    main()
